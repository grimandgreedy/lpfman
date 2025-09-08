import subprocess
import os
import os
import shutil
import subprocess
import time
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.flac import Picture

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


def clear_kitty_image():
    """
    Clear all images displayed via Kitty's icat protocol.
    """
    try:
        subprocess.run(
            ["kitty", "+kitten", "icat", "--clear"],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        pass
        # print(f"[Error] Failed to clear image: {e}")



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
            image_ext = "jpg" if cover.imageformat == 13 else "png"  
    if image_data:
        if not output_image_path:
            base = os.path.splitext(os.path.basename(audio_path))[0]
            output_image_path = f"{base}_cover.{image_ext}"
        with open(output_image_path, "wb") as f:
            f.write(image_data)
        return output_image_path

    return None
