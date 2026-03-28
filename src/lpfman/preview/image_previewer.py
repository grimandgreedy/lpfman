from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from lpfman.preview.base import Previewer, PreviewState
from lpfman.preview._image_backend import show_image, clear_image, ImagePreviewState


@dataclass
class _ImageWrapperState(PreviewState):
    """Wraps ImagePreviewState in the PreviewState hierarchy.

    Stored only in the return value of render() — never on self — because
    ImagePreviewerImpl is used as a singleton and must not carry per-file state
    between calls from different files.
    """
    image_state: Optional[ImagePreviewState] = field(default=None)


class ImagePreviewerImpl:
    """Previewer for image files via _image_backend.py (kitty icat / ueberzugpp)."""

    def can_preview(self, path: str, mime_type: str) -> bool:
        """Return True for image/* MIME types.

        Parameters:
            path (str): File path (unused; detection is MIME-based).
            mime_type (str): MIME type string, e.g. 'image/jpeg'.

        Returns:
            bool: True if this previewer can render the file.
        """
        return mime_type.startswith("image/")

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
        """Display the image using the appropriate backend (kitty or ueberzugpp).

        Backend selection and kitty graphics detection are handled inside
        _image_backend.py (_KITTY_SUPPORTED is cached at import time), so this
        method never calls is_kitty_graphics_supported() directly.

        Parameters:
            stdscr: curses window (unused by image backends; required by Protocol).
            path (str): Absolute path to the image file.
            x (int): Left edge of the display region.
            y (int): Top edge of the display region.
            w (int): Width of the display region.
            h (int): Height of the display region.
            prev_state: Previous state from the last render call, if any.

        Returns:
            _ImageWrapperState: State carrying the ImagePreviewState for clear().
        """
        prev_image_state: Optional[ImagePreviewState] = None
        if prev_state is not None and isinstance(prev_state, _ImageWrapperState):
            prev_image_state = prev_state.image_state

        image_state = show_image(
            path,
            x=x,
            y=y,
            w=w,
            h=h,
            prev_state=prev_image_state,
        )
        return _ImageWrapperState(image_state=image_state)

    def clear(self, state: Optional[PreviewState]) -> None:
        """Tear down the image display owned by state.

        Parameters:
            state: State returned by render(); may be None or wrong type if
                   the previewer was never successfully rendered.
        """
        if state is None or not isinstance(state, _ImageWrapperState):
            return
        clear_image(state.image_state)
