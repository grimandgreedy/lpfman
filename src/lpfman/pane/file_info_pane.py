import curses
import os
import signal
import random
import string
import subprocess
import shlex
import re
import threading
from pdf2image import convert_from_path

from listpick.pane.pane_utils import get_file_attributes

from lpfman.utils.lpfman_utils import *
from lpfman.preview.previewers import extract_album_art
from lpfman.pane.ueberzug_pane import display_image, start_ueberzugpp, remove_image
from lpfman.preview.text_previewer import preview_text
from lpfman.preview._image_backend import clear_image, ImagePreviewState, show_image as backend_show_image

def right_split_file_attributes(stdscr, x, y, w, h, state, row, cell, data: list = [], test: bool = False):
    """
    Display file attributes in right pane.
    """
    if test: return True

    # Title
    # title = "File attributes"
    # if len(title) < w: title = f"{title:^{w}}"
    # stdscr.addstr(y, x,title[:w], curses.color_pair(state["colours_start"]+4) | curses.A_BOLD)

    # Separator
    for j in range(h):
        # stdscr.addstr(j+y, x, ' ', curses.color_pair(state["colours_start"]+16))
        stdscr.addstr(j+y, x, '│', curses.color_pair(state["colours_start"]+16) | curses.A_REVERSE)

    # Display pane count
    pane_count = len(state["right_panes"])
    pane_index = state["right_pane_index"]
    if pane_count > 1:
        s = f" {pane_index+1}/{pane_count} "
        stdscr.addstr(y+h-1, x+w-len(s)-1, s, curses.color_pair(state["colours_start"]+20))

    if len(state["indexed_items"]) == 0:
        data[:] = ["", False, None]
        return None

    cell = state["indexed_items"][state["cursor_pos"]][1][0]

    # Clear previous image display when navigating to a different file
    if len(data) == 3 and cell != data[0] and isinstance(data[1], ImagePreviewState):
        clear_image(data[1])

    if os.path.isdir(cell):
        fs = sorted(os.listdir(cell), key=lambda x: (x.startswith('.'), x))
        for i, f in enumerate(fs):
            if y+1+i >= h: break
            isdir = os.path.isdir(f"{cell}/{f}")
            color = curses.color_pair(9)
            if isdir:
                color = curses.color_pair(11)
            try:
                stdscr.addstr(y+1+i, x+3, f[:w-5], color)
            except:
                pass
        data[:] = [cell, False, None]
        return None



    # Filename/cursor cell value
    stdscr.addstr(y+1, x+2, cell[:w-3])

    # Horizontal separator
    # stdscr.addstr(y+6, x+1, '─'*(w-1), curses.color_pair(state["colours_start"]+16) | curses.A_REVERSE)

    displaying_image = False
    image_state = None
    proc = None
    code_file_extensions = [".sh", ".srt", ".rs", ".toml"]




    # Display file attributes
    attributes = get_file_attributes(cell)
    if len(attributes) != 3: return None
    for i, attr in enumerate(attributes):
        stdscr.addstr(y+2+i, x+4, attr[:w-5])


    def show_image(path):
        prev_state = data[1] if len(data) == 3 and isinstance(data[1], ImagePreviewState) else None
        return backend_show_image(path, x=x+3, y=y+6, w=w-5, h=h-7, prev_state=prev_state)


    if attributes[1].startswith("Filetype: image/"):
        image_state = show_image(cell)
        displaying_image = True


    elif attributes[1].startswith("Filetype: video/"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/lpfman/{tmp_fname}"
        os.makedirs(os.path.dirname(tmp_full_path), exist_ok=True)
        if not os.path.exists(tmp_full_path):
            command = f"ffmpegthumbnailer -i {shlex.quote(cell)} -o {tmp_full_path} -s {720}"
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data[:] = [cell, False, None]
            return None

        image_state = show_image(tmp_full_path)
        displaying_image = True

    elif attributes[1].startswith("Filetype: audio/"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/lpfman/{tmp_fname}"
        os.makedirs(os.path.dirname(tmp_full_path), exist_ok=True)
        if not os.path.exists(tmp_full_path):
            def _extract_art(src, dest):
                try:
                    extract_album_art(src, output_image_path=dest)
                except Exception:
                    pass
            t = threading.Thread(target=_extract_art, args=(cell, tmp_full_path), daemon=True)
            t.start()
            data[:] = [cell, False, None]
            return None

        image_state = show_image(tmp_full_path)
        displaying_image = True

    elif cell.endswith(".epub"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/lpfman/{tmp_fname}"
        os.makedirs(os.path.dirname(tmp_full_path), exist_ok=True)
        if not os.path.exists(tmp_full_path):
            command = f"gnome-epub-thumbnailer {shlex.quote(cell)} {tmp_full_path} -s {512}"
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data[:] = [cell, False, None]
            return None

        image_state = show_image(tmp_full_path)
        displaying_image = True

    elif cell.endswith(".mobi"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/lpfman/{tmp_fname}"
        os.makedirs(os.path.dirname(tmp_full_path), exist_ok=True)
        if not os.path.exists(tmp_full_path):
            command = f"gnome-mobi-thumbnailer {shlex.quote(cell)} {tmp_full_path} -s {512}"
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data[:] = [cell, False, None]
            return None

        image_state = show_image(tmp_full_path)
        displaying_image = True

    elif cell.endswith(".torrent"):
        command = f"transmission-show {shlex.quote(cell)}"
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = proc.stdout.decode("utf-8").strip().split("\n")
        for i in range(min(len(lines), h-7)):
            stdscr.addstr(y+6+i, x+4, lines[i][:w-5])

    elif cell.endswith(".zip"):
        command = f"unzip -l {shlex.quote(cell)}"
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = proc.stdout.decode("utf-8").strip().split("\n")
        for i in range(min(len(lines), h-7)):
            stdscr.addstr(y+6+i, x+4, lines[i][:w-5])

    elif cell.endswith(".pdf"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}.png"
        tmp_full_path = f"/tmp/lpfman/{tmp_fname}"
        os.makedirs(os.path.dirname(tmp_full_path), exist_ok=True)
        if not os.path.exists(tmp_full_path):
            tmp_fname = f"{hash}.png"
            tmp_full_path = f"/tmp/{tmp_fname}"
            def pdf_thumb(cell):
                images = convert_from_path(cell, first_page=1, last_page=1, dpi=72)
                if images:
                    images[0].save(tmp_full_path, 'PNG')

            im_thread = threading.Thread(target=pdf_thumb, args=(cell,))
            im_thread.daemon = True
            im_thread.start()

        image_state = show_image(tmp_full_path)
        displaying_image = True

    elif re.match(r".*tar\...$", cell):
        command = f"tar tf {shlex.quote(cell)}"
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = proc.stdout.decode("utf-8").strip().split("\n")
        for i in range(min(len(lines), h-7)):
            stdscr.addstr(y+6+i, x+4, lines[i][:w-5])

    elif attributes[1].startswith("Filetype: text/") or cell.endswith(tuple(code_file_extensions)):
        preview_text(
            stdscr,
            filepath=cell,
            code_x=x+3,
            code_y=y+6,
            code_w=w-3,
            code_h=h-7,
            show_line_numbers=False,
            indent_guides=True,
            theme="dark"
        )

    data[:] = [cell, image_state if displaying_image else False, None]

    return []
