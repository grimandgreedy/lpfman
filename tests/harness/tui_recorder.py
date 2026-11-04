"""
Run a curses program in a pseudo-terminal and record every frame it draws.

The program's output is fed into a pyte terminal emulator. After each chunk
of output is read, a timestamped snapshot of the emulated screen is stored,
so tests can see exactly what the user would have seen and for how long.
"""

from __future__ import annotations

import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import pyte


@dataclass
class Frame:
    t: float                 # seconds since the program started
    lines: list[str]
    raw: bytes               # the output chunk that produced this frame

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    def is_blank(self) -> bool:
        return all(not line.strip() for line in self.lines)

    def contains(self, s: str) -> bool:
        return any(s in line for line in self.lines)


@dataclass
class TuiRecorder:
    argv: list[str]
    cwd: str
    env: dict
    cols: int = 160
    rows: int = 45
    frames: list[Frame] = field(default_factory=list)
    marks: list[tuple[float, str]] = field(default_factory=list)
    stack_file: Optional[str] = None   # set by for_python_module()

    @classmethod
    def for_python_module(cls, module: str, cwd: str, env: dict, stack_file: str, **kw) -> "TuiRecorder":
        """
        Run `python -m module` with faulthandler listening on SIGUSR1, so
        dump_stacks() can show where every thread is when the program seems stuck.
        """
        launcher = (
            "import faulthandler, runpy, signal\n"
            "if __name__ == '__main__':\n"
            f"    faulthandler.register(signal.SIGUSR1, file=open({stack_file!r}, 'w'), all_threads=True)\n"
            f"    runpy.run_module({module!r}, run_name='__main__')\n"
        )
        return cls([sys.executable, "-c", launcher], cwd, env, stack_file=stack_file, **kw)

    def start(self) -> "TuiRecorder":
        self._screen = pyte.Screen(self.cols, self.rows)
        self._stream = pyte.ByteStream(self._screen)
        self._lock = threading.Lock()
        self._t0 = time.monotonic()

        pid, fd = pty.fork()
        if pid == 0:  # child
            try:
                os.chdir(self.cwd)
                os.execvpe(self.argv[0], self.argv, self.env)
            finally:
                os._exit(127)

        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", self.rows, self.cols, 0, 0))
        self._stop = threading.Event()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        return self

    def _read_loop(self) -> None:
        while not self._stop.is_set():
            try:
                r, _, _ = select.select([self.fd], [], [], 0.05)
            except (OSError, ValueError):
                break
            if not r:
                continue
            try:
                chunk = os.read(self.fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            with self._lock:
                self._stream.feed(chunk)
                self.frames.append(
                    Frame(time.monotonic() - self._t0, list(self._screen.display), chunk)
                )

    # -- interaction -------------------------------------------------------

    def now(self) -> float:
        return time.monotonic() - self._t0

    def mark(self, label: str) -> float:
        """Record a labelled point in time, e.g. just before sending a key."""
        t = self.now()
        self.marks.append((t, label))
        return t

    def send(self, keys: str | bytes, label: Optional[str] = None) -> float:
        t = self.mark(label or f"send {keys!r}")
        os.write(self.fd, keys.encode() if isinstance(keys, str) else keys)
        return t

    def wait_for(self, pred: Callable[[Frame], bool], timeout: float = 5.0, after: float = 0.0) -> Frame:
        """Wait for the first frame recorded after `after` for which pred(frame) is true."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                for f in self.frames:
                    if f.t >= after and pred(f):
                        return f
            time.sleep(0.01)
        raise TimeoutError(f"no matching frame within {timeout}s; last screen:\n{self.screen_text()}")

    def wait_for_text(self, s: str, timeout: float = 5.0, after: float = 0.0) -> Frame:
        return self.wait_for(lambda f: f.contains(s), timeout, after)

    def settle(self, quiet: float = 0.5, timeout: float = 10.0) -> None:
        """Wait until no output has arrived for `quiet` seconds."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            last = self.frames[-1].t if self.frames else 0.0
            if self.now() - last >= quiet:
                return
            time.sleep(0.02)

    def screen_text(self) -> str:
        with self._lock:
            return "\n".join(self._screen.display)

    def frames_since(self, t: float) -> list[Frame]:
        with self._lock:
            return [f for f in self.frames if f.t >= t]

    def dump_stacks(self, wait: float = 0.5) -> str:
        """
        Return a traceback of every thread in the child (needs for_python_module).

        For debugging hangs only: faulthandler walks other threads' stacks while
        they keep running, which can crash the child (SIGSEGV). Don't call it in
        the middle of a test that goes on using the program afterwards.
        """
        if not self.stack_file:
            raise RuntimeError("dump_stacks() needs a recorder created with for_python_module()")
        os.kill(self.pid, signal.SIGUSR1)
        time.sleep(wait)
        with open(self.stack_file) as f:
            return f.read()

    def close(self) -> None:
        self._stop.set()
        for sig, grace in ((signal.SIGTERM, 1.0), (signal.SIGKILL, 5.0)):
            try:
                os.kill(self.pid, sig)
            except ProcessLookupError:
                break
            deadline = time.monotonic() + grace
            done = False
            while time.monotonic() < deadline:
                try:
                    if os.waitpid(self.pid, os.WNOHANG) != (0, 0):
                        done = True
                        break
                except ChildProcessError:
                    done = True
                    break
                time.sleep(0.02)
            if done:
                break
        self._reader.join(timeout=1)
        try:
            os.close(self.fd)
        except OSError:
            pass

    def __enter__(self) -> "TuiRecorder":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.close()


def blank_spans(frames: list[Frame], end: Optional[float] = None) -> list[tuple[float, float]]:
    """
    Return (start, duration) for each stretch of time the screen was blank.

    A frame stays on screen until the next frame arrives (or until `end`).
    """
    spans = []
    for i, f in enumerate(frames):
        if not f.is_blank():
            continue
        if i + 1 < len(frames):
            nxt = frames[i + 1].t
        else:
            nxt = end if end is not None else f.t
        if spans and abs(spans[-1][0] + spans[-1][1] - f.t) < 1e-9:
            s, _ = spans[-1]
            spans[-1] = (s, nxt - s)
        else:
            spans.append((f.t, nxt - f.t))
    return spans


def timeline(frames: list[Frame], marks: Optional[list[tuple[float, str]]] = None, since: float = 0.0, width: int = 60) -> str:
    """Human-readable list of frames and marks: time, blank or not, and the first non-empty line."""
    events: list[tuple[float, str]] = []
    for t, label in marks or []:
        if t >= since:
            events.append((t, f"{t:8.3f}s  >>> {label}"))
    for f in frames:
        if f.t < since:
            continue
        first = next((l.strip() for l in f.lines if l.strip()), "")
        state = "BLANK" if f.is_blank() else f"{sum(1 for l in f.lines if l.strip()):2d} lines"
        events.append((f.t, f"{f.t:8.3f}s  {state:9s} {len(f.raw):6d}B  {first[:width]}"))
    events.sort(key=lambda e: e[0])
    return "\n".join(line for _, line in events)
