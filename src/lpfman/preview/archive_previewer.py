from __future__ import annotations
import curses
import re
import shlex
import subprocess
from typing import Optional

from .base import PreviewState


class ArchivePreviewerImpl:
    def can_preview(self, path: str, mime_type: str) -> bool:
        # FIX: original regex r".*tar\...$" only matches single-char suffixes.
        # Use r".*\.tar\..+$" to match .tar.gz, .tar.bz2, .tar.zst, .tar.xz etc.
        return (
            path.endswith(".zip")
            or path.endswith(".torrent")
            or bool(re.match(r".*\.tar\..+$", path))
        )

    def render(
        self,
        stdscr,
        path: str,
        x: int,
        y: int,
        w: int,
        h: int,
        prev_state: Optional[PreviewState],
    ) -> PreviewState:
        if path.endswith(".torrent"):
            cmd = f"transmission-show {shlex.quote(path)}"
        elif path.endswith(".zip"):
            cmd = f"unzip -l {shlex.quote(path)}"
        else:
            cmd = f"tar tf {shlex.quote(path)}"

        try:
            result = subprocess.run(
                cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            lines = result.stdout.decode("utf-8", errors="replace").strip().split("\n")
        except Exception:
            return PreviewState()

        for i in range(min(len(lines), h - 7)):
            try:
                stdscr.addstr(y + 6 + i, x + 4, lines[i][:w - 5])
            except curses.error:
                pass  # out-of-bounds addstr — skip silently

        return PreviewState()  # text output: no persistent state

    def clear(self, _state: Optional[PreviewState]) -> None:
        pass  # text output leaves no artifact or subprocess
