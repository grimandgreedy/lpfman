from __future__ import annotations
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional

from lpfman.preview.base import PreviewState
from lpfman.preview._thumbnail import thumbnail_path
from lpfman.preview._image_backend import show_image, clear_image, ImagePreviewState


@dataclass
class EbookPreviewState(PreviewState):
    image_state: Optional[ImagePreviewState] = None
    path: str = ""


class EbookPreviewerImpl:
    def can_preview(self, path: str, mime_type: str) -> bool:
        return path.endswith(".epub") or path.endswith(".mobi")

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
            if path.endswith(".epub"):
                cmd = f"gnome-epub-thumbnailer {shlex.quote(path)} {tmp} -s 512"
            else:
                cmd = f"gnome-mobi-thumbnailer {shlex.quote(path)} {tmp} -s 512"
            subprocess.run(
                cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        image_state = show_image(
            tmp, x=x, y=y, w=w, h=h,
            prev_state=prev_state.image_state if isinstance(prev_state, EbookPreviewState) else None,
        )
        return EbookPreviewState(image_state=image_state, path=path)

    def clear(self, state: Optional[PreviewState]) -> None:
        if isinstance(state, EbookPreviewState) and state.image_state:
            clear_image(state.image_state)
