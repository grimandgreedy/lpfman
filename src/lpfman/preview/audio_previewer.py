from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

from mutagen import File  # type: ignore[attr-defined]
from mutagen.id3 import ID3, APIC  # type: ignore[attr-defined]

from .base import PreviewState
from ._thumbnail import thumbnail_path
from ._image_backend import show_image, clear_image, ImagePreviewState


def extract_album_art(audio_path, output_image_path="/tmp/albart.png"):
    """
    Extract album art using mutagen (MP3, FLAC, M4A).
    Returns:
        - Path to saved image if saved,
        - Bytes if not saved,
        - None if not found.
    """
    audio = File(audio_path)
    if audio is None:
        print("Unsupported or invalid audio file.")
        return None

    image_data = None
    image_ext = "jpg"  # default

    # MP3
    if isinstance(audio.tags, ID3):
        # Find any APIC (Attached Picture) tag
        for key in audio.tags.keys():
            if key.startswith("APIC"):
                apic = audio.tags.getall(key)[0]
                image_data = apic.data
                image_ext = apic.mime.split("/")[-1]
                break

    # FLAC
    elif hasattr(audio, "pictures") and audio.pictures:
        pic = audio.pictures[0]
        image_data = pic.data
        image_ext = pic.mime.split("/")[-1]

    # MP4/M4A
    elif audio.mime and "mp4" in audio.mime[0]:
        covers = audio.tags.get("covr")
        if covers:
            cover = covers[0]
            image_data = cover if isinstance(cover, bytes) else cover.data
            # 13 = jpg, 14 = png
            image_ext = "jpg" if getattr(cover, "imageformat", 13) == 13 else "png"
    if image_data:
        if not output_image_path:
            base = os.path.splitext(os.path.basename(audio_path))[0]
            output_image_path = f"{base}_cover.{image_ext}"
        with open(output_image_path, "wb") as f:
            f.write(image_data)
        return output_image_path

    return None


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
