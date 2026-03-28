from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

from .base import PreviewState
from ._thumbnail import thumbnail_path
from ._image_backend import show_image, clear_image, ImagePreviewState
from .previewers import extract_album_art


@dataclass
class AudioPreviewState(PreviewState):
    image_state: Optional[ImagePreviewState] = None
    path: str = ""


class AudioPreviewerImpl:
    def can_preview(self, path: str, mime_type: str) -> bool:
        return mime_type.startswith("audio/")

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
        tmp = thumbnail_path(full_path, w - 5, h - 7, ext="jpg")
        if not os.path.exists(tmp):
            try:
                # FIX: existing code called extract_album_art(cell, True, tmp_full_path)
                # which passes True as output_image_path (a bug). Correct form uses keyword arg:
                extract_album_art(path, output_image_path=tmp)
            except Exception:
                return AudioPreviewState(path=path)
        image_state = show_image(
            tmp, x=x, y=y, w=w, h=h,
            prev_state=prev_state.image_state if isinstance(prev_state, AudioPreviewState) else None,
        )
        return AudioPreviewState(image_state=image_state, path=path)

    def clear(self, state: Optional[PreviewState]) -> None:
        if isinstance(state, AudioPreviewState) and state.image_state:
            clear_image(state.image_state)
