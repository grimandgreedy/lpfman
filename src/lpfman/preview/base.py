from __future__ import annotations
import curses
from typing import Protocol, runtime_checkable


class PreviewState:
    """Opaque carrier for per-previewer inter-call state. Subclass to add fields."""
    pass


@runtime_checkable
class Previewer(Protocol):
    def can_preview(self, path: str, mime_type: str) -> bool:
        """Return True if this previewer handles the given file."""
        ...

    def render(
        self,
        stdscr: "curses._CursesWindow",
        path: str,
        x: int,
        y: int,
        w: int,
        h: int,
        prev_state: "PreviewState | None",
    ) -> "PreviewState":
        """Render preview into the terminal region. Return state for next call."""
        ...

    def clear(self, state: "PreviewState | None") -> None:
        """Tear down any subprocess or artifact owned by state."""
        ...
