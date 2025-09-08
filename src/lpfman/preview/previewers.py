import subprocess
import os
import os
import shutil
import subprocess
import time

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

