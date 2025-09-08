import os
import json
import time
import subprocess
from lpfman.utils.lpfman_utils import *

UEBERZUGPP_CMD = ["ueberzugpp", "layer", "--parser", "json"]

def start_ueberzugpp():
    proc = subprocess.Popen(
        UEBERZUGPP_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,  # Keep stderr open to inspect later
        text=True  # So we can write strings instead of bytes
    )
    return proc

def send_command(proc, command: dict):
    try:
        proc.stdin.write(json.dumps(command) + '\n')
        proc.stdin.flush()
    except Exception as e:
        pass

def display_image(proc, path, x=0, y=0, width=40, height=20):
    id = generate_hash(path)
    send_command(proc, {
        "action": "add",
        "identifier": id,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "path": path,
        "scaler": "contain",
        "layer": "above",
        "visibility": True
    })

def remove_image(proc, identifier="demo"):
    id = generate_hash(identifier)
    send_command(proc, {
        "action": "remove",
        "identifier": id,
    })

if __name__ == "__main__":
    image_path = "~/Pictures/paintings/Botticelli_La_nascita_di_Venere.jpg"  # <-- Replace this with a valid absolute path
    image_path = os.path.expanduser(image_path)

    # print(f"[DEBUG] Checking image path: {image_path}")
    if not os.path.isfile(image_path):
        # print(f"[ERROR] Image file does not exist: {image_path}")
        exit(1)

    proc = start_ueberzugpp()
    time.sleep(0.2)  # Let it warm up

    display_image(proc, image_path, x=5, y=2)
    time.sleep(5)

    remove_image(proc)
    time.sleep(1)

    # print("[DEBUG] Shutting down ueberzugpp...")
    proc.stdin.close()
    proc.terminate()
    proc.wait(timeout=1)

    # Dump any stderr output for debugging
    stderr = proc.stderr.read()
    # if stderr:
        # print("[DEBUG] ueberzugpp stderr:")
        # print(stderr.strip())

    # print("[DEBUG] Done.")
