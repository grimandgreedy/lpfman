from __future__ import annotations
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Literal, Optional

from lpfman.preview.base import PreviewState
from lpfman.utils.lpfman_utils import generate_hash


def display_image_with_icat(
    image_path: str,
    width: int = 40,
    height: int = 20,
    x: int = 10,
    y: int = 5,
    align: str = "center",
    clear: bool = True,
    background_colour: str = "white",
):
    """
    Display an image in the terminal using Kitty's icat protocol.

    Parameters:
        image_path (str): Path to the image file.
        width (int): Width in terminal cells.
        height (int): Height in terminal cells.
        x (int): X (column) position in terminal cells.
        y (int): Y (row) position in terminal cells.
        align (str): One of 'left', 'center', 'right'.
        clear (bool): Whether to clear previously displayed images.
    """
    if not os.path.exists(image_path):
        # print(f"[Error] Image not found: {image_path}")
        return None

    cmd = [
        "kitty", "+kitten", "icat",
        "--transfer-mode", "file",
        "--place", f"{width}x{height}@{x}x{y}",
        "--align", align,
        "--background", background_colour,
    ]

    if clear:
        cmd.append("--clear")

    cmd.append(image_path)

    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        time.sleep(0.01)
        return proc

    except subprocess.CalledProcessError as e:
        pass
        # print(f"[Error] Failed to display image: {e}")


def is_kitty_graphics_supported() -> bool:
    """
    Check whether the terminal supports the Kitty graphics protocol.

    Returns:
        bool: True if supported, False otherwise.
    """
    # Check if 'kitty +kitten icat' is available
    icat_exists = shutil.which("kitty")
    if not icat_exists:
        return False

    # Check if running inside a Kitty-compatible terminal
    term = os.environ.get("TERM", "")
    kitty_version = os.environ.get("KITTY_WINDOW_ID")
    wezterm_version = os.environ.get("WEZTERM_EXECUTABLE")

    # Kitty sets KITTY_WINDOW_ID; WezTerm supports Kitty graphics protocol too
    if kitty_version or wezterm_version:
        return True

    # Fallback: try running a dry-run icat command and see if it succeeds
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--check-support"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False


# Cached at import time. is_kitty_graphics_supported() spawns a subprocess to probe the
# terminal; calling it on every keypress (the current bug in file_info_pane.py lines 50
# and 112) adds ~10ms of subprocess overhead per navigation event.
_KITTY_SUPPORTED: bool = is_kitty_graphics_supported()


@dataclass
class ImagePreviewState(PreviewState):
    path: str = ""
    proc: Optional[subprocess.Popen] = None   # kitty icat process handle; None for ueberzugpp
    identifier: str = ""                       # ueberzugpp image identifier (hash); "" for kitty
    backend: Literal["kitty", "ueberzug", ""] = ""


class UeberzugppBackend:
    """Single persistent ueberzugpp process for the session.

    The original code called start_ueberzugpp() on every cell change, spawning a new
    process each time. This class keeps one process alive and reconnects only if it dies.
    """
    _proc: Optional[subprocess.Popen] = None  # class-level — shared across all instances

    def ensure_running(self) -> subprocess.Popen:
        proc = UeberzugppBackend._proc
        if proc is None or proc.poll() is not None:
            proc = subprocess.Popen(
                ["ueberzugpp", "layer", "--parser", "json"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            UeberzugppBackend._proc = proc
        return proc

    def show(self, path: str, identifier: str, x: int, y: int, w: int, h: int) -> None:
        proc = self.ensure_running()
        if proc.stdin is None:
            return
        try:
            proc.stdin.write(json.dumps({
                "action": "add",
                "identifier": identifier,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "path": path,
                "scaler": "contain",
                "layer": "above",
                "visibility": True,
            }) + "\n")
            proc.stdin.flush()
        except Exception:
            pass

    def hide(self, identifier: str) -> None:
        proc = self.ensure_running()
        if proc.stdin is None:
            return
        try:
            proc.stdin.write(json.dumps({
                "action": "remove",
                "identifier": identifier,
            }) + "\n")
            proc.stdin.flush()
        except Exception:
            pass


# Module-level singleton — one UeberzugppBackend per session, shared by all callers
_ueberzug = UeberzugppBackend()


def show_image(
    path: str,
    x: int,
    y: int,
    w: int,
    h: int,
    prev_state: Optional[ImagePreviewState] = None,
) -> ImagePreviewState:
    """Display image at path in terminal region (x, y, w, h).

    Reuses existing display if prev_state has the same path and backend,
    avoiding a subprocess restart when the user has not moved to a different file.
    """
    if not os.path.exists(path):
        return ImagePreviewState()

    if _KITTY_SUPPORTED:
        clear = not (prev_state and prev_state.path == path and prev_state.backend == "kitty")
        proc = display_image_with_icat(path, x=x, y=y, width=w, height=h, clear=clear)
        return ImagePreviewState(path=path, proc=proc, backend="kitty")
    else:
        # Reuse existing ueberzugpp display if same file
        if prev_state and prev_state.path == path and prev_state.backend == "ueberzug":
            return prev_state
        identifier = generate_hash(path)
        _ueberzug.show(path, identifier, x, y, w, h)
        return ImagePreviewState(path=path, identifier=identifier, backend="ueberzug")


def clear_image(state: Optional[ImagePreviewState]) -> None:
    """Tear down the image display owned by state."""
    if state is None or not state.backend:
        return
    if state.backend == "kitty":
        print("\033_Ga=d\033\\", end="", flush=True)
        if state.proc is not None:
            try:
                state.proc.terminate()
                state.proc.wait(timeout=1)
            except Exception:
                pass
    elif state.backend == "ueberzug" and state.identifier:
        _ueberzug.hide(state.identifier)
