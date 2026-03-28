from __future__ import annotations
import curses
import os
from typing import Optional
from lpfman.preview.base import PreviewState

# NOTE: text_preview.py was deleted in Phase 2 as part of the curses_syntax_highlighting
# migration. file_info_pane.py line 17 imports from it and will fail at startup until
# Phase 4 rewires the dispatcher. text_previewer.py (Phase 3 Plan 01) is the replacement.


class DirectoryPreviewerImpl:
    def can_preview(self, path: str, _mime_type: str) -> bool:
        return os.path.isdir(path)

    def render(
        self,
        stdscr: "curses.window",
        path: str,
        x: int,
        y: int,
        w: int,
        h: int,
        _prev_state: Optional[PreviewState],
    ) -> PreviewState:
        try:
            fs = sorted(os.listdir(path), key=lambda f: (f.startswith("."), f))
        except PermissionError:
            return PreviewState()

        for i, f in enumerate(fs):
            if y + 1 + i >= h:
                break
            isdir = os.path.isdir(f"{path}/{f}")
            color = curses.color_pair(9)
            if isdir:
                color = curses.color_pair(11)
            try:
                stdscr.addstr(y + 1 + i, x + 3, f[:w - 5], color)
            except curses.error:
                pass

        return PreviewState()

    def clear(self, _state: Optional[PreviewState]) -> None:
        pass  # text rendering — no subprocess or artifact to clean up
