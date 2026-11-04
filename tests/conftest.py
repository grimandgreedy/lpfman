import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from harness.tui_recorder import TuiRecorder, timeline  # noqa: E402


def make_tree(root: Path, big_files: int = 1000, small_files: int = 10) -> Path:
    """
    root/
      big/      <- `big_files` small text files
      small/    <- `small_files` small text files
      a.txt
    """
    root.mkdir(parents=True, exist_ok=True)
    for name, n in (("big", big_files), ("small", small_files)):
        d = root / name
        d.mkdir(exist_ok=True)
        for i in range(n):
            (d / f"file_{i:05d}.txt").write_text(f"file {i}\n")
    (root / "a.txt").write_text("hello\n")
    return root


@pytest.fixture
def tree(tmp_path):
    return make_tree(tmp_path / "tree")


@pytest.fixture
def lpfman_env(tmp_path):
    """Environment for running lpfman without touching the real home or terminal graphics."""
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("KITTY_WINDOW_ID", "WEZTERM_EXECUTABLE", "TMUX")}
    env.update(HOME=str(home), TERM="xterm-256color", LANG=env.get("LANG", "en_US.UTF-8"))
    return env


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def run_lpfman(request, lpfman_env, tmp_path):
    """
    Start lpfman in `cwd` under a TuiRecorder.

    If the test fails, the frame timeline and every thread's stack in lpfman
    are printed, so a hang or slow draw shows where it happened.
    """
    recorders: list[TuiRecorder] = []

    def _run(cwd, cols=160, rows=45) -> TuiRecorder:
        stack_file = str(tmp_path / f"stacks_{len(recorders)}.txt")
        rec = TuiRecorder.for_python_module("lpfman", str(cwd), lpfman_env, stack_file, cols=cols, rows=rows)
        rec.start()
        recorders.append(rec)
        return rec

    yield _run

    rep = getattr(request.node, "rep_call", None)
    for rec in recorders:
        if rep is not None and rep.failed:
            print("\n=== frame timeline ===")
            print(timeline(rec.frames, rec.marks))
            try:
                print("\n=== lpfman stacks ===")
                print(rec.dump_stacks())
            except (OSError, RuntimeError) as e:
                print(f"(could not dump stacks: {e})")
        rec.close()
