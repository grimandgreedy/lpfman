from __future__ import annotations
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional

from .base import PreviewState
from ._thumbnail import thumbnail_path
from ._image_backend import show_image, clear_image, ImagePreviewState


@dataclass
class VideoPreviewState(PreviewState):
    image_state: Optional[ImagePreviewState] = None
    path: str = ""


class VideoPreviewerImpl:
    def can_preview(self, path: str, mime_type: str) -> bool:
        return mime_type.startswith("video/")

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
        # Pass adjusted dimensions to thumbnail_path to match the existing cache key
        # (file_info_pane.py line 152 uses w-5, h-7 as the dimension key)
        tmp = thumbnail_path(full_path, w - 5, h - 7, ext="jpg")
        if not os.path.exists(tmp):
            command = f"ffmpegthumbnailer -i {shlex.quote(path)} -o {tmp} -s 720"
            subprocess.run(
                command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        image_state = show_image(
            tmp, x=x, y=y, w=w, h=h,
            prev_state=prev_state.image_state if isinstance(prev_state, VideoPreviewState) else None,
        )
        return VideoPreviewState(image_state=image_state, path=path)

    def clear(self, state: Optional[PreviewState]) -> None:
        if isinstance(state, VideoPreviewState) and state.image_state:
            clear_image(state.image_state)
