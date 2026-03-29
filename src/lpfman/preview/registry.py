from __future__ import annotations
from typing import List, Optional
from .base import Previewer, PreviewState


class PreviewRegistry:
    """Ordered list of Previewer instances. Returns first match for a path/mime pair."""

    def __init__(self, previewers: List[Previewer]) -> None:
        self._previewers = previewers

    def find(self, path: str, mime_type: str) -> Optional[Previewer]:
        for p in self._previewers:
            if p.can_preview(path, mime_type):
                return p
        return None


from .directory_previewer import DirectoryPreviewerImpl
from .image_previewer     import ImagePreviewerImpl
from .video_previewer     import VideoPreviewerImpl
from .audio_previewer     import AudioPreviewerImpl
from .pdf_previewer       import PdfPreviewerImpl
from .ebook_previewer     import EbookPreviewerImpl
from .archive_previewer   import ArchivePreviewerImpl
from .text_previewer      import TextPreviewerImpl

DEFAULT_REGISTRY: PreviewRegistry = PreviewRegistry([
    DirectoryPreviewerImpl(),
    PdfPreviewerImpl(),
    EbookPreviewerImpl(),
    ArchivePreviewerImpl(),
    ImagePreviewerImpl(),
    VideoPreviewerImpl(),
    AudioPreviewerImpl(),
    TextPreviewerImpl(),
])
