from __future__ import annotations
import os
import threading
from dataclasses import dataclass, field
from typing import Optional

from pdf2image import convert_from_path

from lpfman.preview.base import PreviewState
from lpfman.preview._thumbnail import thumbnail_path
from lpfman.preview._image_backend import show_image, clear_image, ImagePreviewState


@dataclass
class PdfPreviewState(PreviewState):
    tmp_path: str = ""
    pending: bool = False        # True while background thread is generating the thumbnail
    image_state: Optional[ImagePreviewState] = None


class PdfPreviewerImpl:
    def can_preview(self, path: str, mime_type: str) -> bool:
        return path.endswith(".pdf")

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
        full_path = os.path.realpath(path)
        tmp = thumbnail_path(full_path, w - 5, h - 7, ext="png")

        # Re-entry on same file while thread is running — thumbnail not ready yet
        if (
            isinstance(prev_state, PdfPreviewState)
            and prev_state.pending
            and prev_state.tmp_path == tmp
            and not os.path.exists(tmp)
        ):
            return prev_state  # still generating — nothing to show yet

        if not os.path.exists(tmp):
            def _generate(src_path: str, dest_path: str) -> None:
                try:
                    images = convert_from_path(src_path, first_page=1, last_page=1, dpi=72)
                    if images:
                        images[0].save(dest_path, "PNG")
                except Exception:
                    pass

            t = threading.Thread(target=_generate, args=(path, tmp), daemon=True)
            t.start()
            return PdfPreviewState(tmp_path=tmp, pending=True)

        # Thumbnail exists — render it
        image_state = show_image(
            tmp, x=x, y=y, w=w, h=h,
            prev_state=prev_state.image_state if isinstance(prev_state, PdfPreviewState) else None,
        )
        return PdfPreviewState(tmp_path=tmp, pending=False, image_state=image_state)

    def clear(self, state: Optional[PreviewState]) -> None:
        if isinstance(state, PdfPreviewState) and state.image_state:
            clear_image(state.image_state)
