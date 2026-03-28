from __future__ import annotations
import os
from lpfman.utils.lpfman_utils import generate_hash


def thumbnail_path(full_path: str, w: int, h: int, ext: str = "jpg") -> str:
    """
    Return the cache path for a thumbnail of full_path at dimensions w x h.

    Creates /tmp/lpfman/ if it does not exist. Callers must pass already-adjusted
    dimensions (e.g. w-5, h-7) — this function embeds w and h as-is.

    Returns /tmp/lpfman/{sha256_of_full_path}_{w}x{h}.{ext}
    """
    h_str = generate_hash(full_path)
    os.makedirs("/tmp/lpfman/", exist_ok=True)
    return f"/tmp/lpfman/{h_str}_{w}x{h}.{ext}"


# Re-export so callers can do: from lpfman.preview._thumbnail import generate_hash
__all__ = ["thumbnail_path", "generate_hash"]
