from __future__ import annotations
from typing import Optional
from curses_syntax_highlighting import preview_text  # type: ignore[import-untyped]
from .base import PreviewState


# Extensions treated as code/text regardless of MIME type, matching the set
# that file_info_pane.py uses plus a broader reasonable set for common formats.
_CODE_EXTENSIONS = (
    ".py", ".js", ".ts", ".rs", ".go",
    ".c", ".cpp", ".h", ".java",
    ".sh", ".md", ".toml", ".json",
    ".yaml", ".yml", ".xml", ".html",
    ".css", ".sql", ".srt",
)


class TextPreviewerImpl:
    """Previewer for text and code files using curses_syntax_highlighting."""

    def can_preview(self, path: str, mime_type: str) -> bool:
        """Return True for text/* MIME types or recognised code file extensions.

        Parameters:
            path (str): Absolute or relative path to the file.
            mime_type (str): MIME type string, e.g. 'text/x-python'.

        Returns:
            bool: True if this previewer can render the file.
        """
        if mime_type.startswith("text/"):
            return True
        return path.endswith(_CODE_EXTENSIONS)

    def render(
        self,
        stdscr,
        path: str,
        x: int,
        y: int,
        w: int,
        h: int,
        _prev_state: Optional[PreviewState],
    ) -> PreviewState:
        """Render syntax-highlighted text into the terminal region.

        Passes the raw path directly to preview_text — NOT shlex.quote(path),
        which wraps the path in shell quoting and breaks os.path.isfile checks
        inside the library (BUGS-01 fix).

        Parameters:
            stdscr: curses window.
            path (str): Raw file path.
            x (int): Left edge of the preview region.
            y (int): Top edge of the preview region.
            w (int): Width of the preview region.
            h (int): Height of the preview region.
            prev_state: Ignored — text rendering is stateless.

        Returns:
            PreviewState: Empty state carrier (text leaves no subprocess).
        """
        preview_text(
            stdscr,
            filepath=path,
            code_x=x + 3,
            code_y=y + 6,
            code_w=w - 3,
            code_h=h - 7,
            show_line_numbers=False,
            indent_guides=True,
            theme="dark",
        )
        return PreviewState()

    def clear(self, state: Optional[PreviewState]) -> None:
        """No-op — text rendering leaves no subprocess or artifact to clean up.

        Parameters:
            state: Ignored.
        """
        pass
