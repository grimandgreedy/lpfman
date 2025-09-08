import curses
import os
import signal
import random
import string
import subprocess
import shlex

from listpick.pane.pane_utils import get_file_attributes

from lpfman.utils.lpfman_utils import *
from lpfman.preview.previewers import display_image_with_icat, clear_kitty_image, is_kitty_graphics_supported
from lpfman.pane.ueberzug_pane import display_image, start_ueberzugpp, remove_image
from lpfman.preview.text_preview import preview_text

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


    if os.path.isdir(cell):
        fs = sorted(os.listdir(cell), key=lambda x: (x.startswith('.'), x))
        for i, f in enumerate(fs):
            if y+1+i >= h: break
            isdir = os.path.isdir(f"{cell}/{f}")
            color = curses.color_pair(2)
            if isdir:
                color = curses.color_pair(11)
            try:
                stdscr.addstr(y+1+i, x+4, f[:w-5], color)
            except:
                pass
        data[:] = [cell, False, None]
        return None



    # Filename/cursor cell value
    stdscr.addstr(y+1, x+2, cell[:w-3])



    # Horizontal separator
    # stdscr.addstr(y+6, x+1, '─'*(w-1), curses.color_pair(state["colours_start"]+16) | curses.A_REVERSE)

    displaying_image = False
    proc = None
    code_file_extensions = [".sh"]



    # If we are on a different line and we are displaying an image then clear the image.
    if cell != data[0] and data[1]:
        if is_kitty_graphics_supported():
            clear_kitty_image()


    # Display file attributes
    attributes = get_file_attributes(cell)
    if len(attributes) != 3: return None
    for i, attr in enumerate(attributes):
        stdscr.addstr(y+2+i, x+4, attr[:w-5])




    if attributes[1].startswith("Filetype: image/"):
        if is_kitty_graphics_supported():
            # display_image_with_icat(cell, clear=False)
            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                cell,
                x=x+3,
                y=y+6,
                width=w-5,
                height=h-9,
                clear=clear,
            )
            displaying_image = True
        else:
            if len(data) and data[0] != cell:
                # if len(data) > 2 and data[2] != None:
                #     os.system("notify-send hi")
                #     old_proc = data[2]
                #     remove_image(old_proc, data[0])
                #     old_proc.stdin.close()
                #     old_proc.terminate()
                #     old_proc.wait(timeout=1)
                #     # os.killpg(os.getpgid(old_proc.pid), signal.SIGTERM)
                #
                proc = start_ueberzugpp()
                display_image(
                    proc,
                    cell,
                    x=x+3,
                    y=y+6,
                    width=w-5,
                    height=h-7,
                )
            displaying_image = True

    elif attributes[1].startswith("Filetype: video/"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/{tmp_fname}"
        if not os.path.exists(tmp_full_path):
            command = f"ffmpegthumbnailer -i {shlex.quote(cell)} -o {tmp_full_path} -s {720}"
            subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if is_kitty_graphics_supported():

            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                tmp_full_path,
                x=x+3,
                y=y+6,
                width=w-5,
                height=h-7,
                clear=clear,
            )
            displaying_image = True

    elif cell.endswith(".epub"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/{tmp_fname}"
        if not os.path.exists(tmp_full_path):
            command = f"gnome-epub-thumbnailer {shlex.quote(cell)} {tmp_full_path} -s {512}"
            subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if is_kitty_graphics_supported():

            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                tmp_full_path,
                x=x+3,
                y=y+6,
                width=w-5,
                height=h-7,
                clear=clear,
            )
            displaying_image = True

    elif cell.endswith(".mobi"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-7}.jpg"
        tmp_full_path = f"/tmp/{tmp_fname}"
        if not os.path.exists(tmp_full_path):
            command = f"gnome-mobi-thumbnailer {shlex.quote(cell)} {tmp_full_path} -s {512}"
            subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if is_kitty_graphics_supported():

            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                tmp_full_path,
                x=x+3,
                y=y+6,
                width=w-5,
                height=h-7,
                clear=clear,
            )
            displaying_image = True

    elif cell.endswith(".torrent"):
        command = f"transmission-show {cell}"
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = proc.stdout.decode("utf-8").strip().split("\n")
        for i in range(min(len(lines), h-7)):
            stdscr.addstr(y+6+i, x+4, lines[i][:w-5])


    elif (attributes[1].startswith("Filetype: text/") or cell[-3:] in code_file_extensions):
        preview_text(
            stdscr,
            filepath=shlex.quote(cell),
            code_x=x+3,
            code_y=y+6,
            code_w=w-3,
            code_h=h-7,
            show_line_numbers=False,
            indent_guides=True,
            theme="dark"

        )

    data[:] = [cell, displaying_image, proc]

    return []
