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

def right_split_file_attributes(stdscr, x, y, w, h, state, row, cell, data: list = [], test: bool = False):
    """
    Display file attributes in right pane.
    """
    if test: return True

    # Title
    title = "File attributes"
    if len(title) < w: title = f"{title:^{w}}"
    stdscr.addstr(y, x,title[:w], curses.color_pair(state["colours_start"]+4) | curses.A_BOLD)

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
        data[:] = ["", False]
        return []

    cell = state["indexed_items"][state["cursor_pos"]][1][0]
    # Filename/cursor cell value
    stdscr.addstr(y+2, x+2, cell[:w-3])


    attributes = get_file_attributes(cell)
    for i, attr in enumerate(attributes):
        stdscr.addstr(y+3+i, x+4, attr[:w-5])


    displaying_image = False
    proc = None
    if len(attributes) == 3 and attributes[1].startswith("Filetype: image/"):
        if is_kitty_graphics_supported():
            # display_image_with_icat(cell, clear=False)
            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                cell,
                x=x+3,
                y=y+7,
                width=w-5,
                height=h-8,
                clear=clear,
            )
            displaying_image = True
        else:
            # display_image("/home/noah/Pictures/paintings/Botticelli_La_nascita_di_Venere.jpg", width=20)
            #
            # from term_image.image import from_file
            #
            # image = from_file(cell)
            #
            # image.width = w-5
            # image.draw()
            if len(data) and data[0] != cell:
                # if len(data) > 2 and data[2] != None:
                #     os.system("notify-send hi")
                #     # import pyperclip
                #     # pyperclip.copy(data)
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
                    y=y+7,
                    width=w-5,
                    height=h-8,
                )
            displaying_image = True

    elif len(attributes) == 3 and attributes[1].startswith("Filetype: video/"):
        full_path = os.path.realpath(cell)
        hash = generate_hash(full_path)

        tmp_fname = f"{hash}_{w-5}x{h-8}.jpg"
        tmp_full_path = f"/tmp/{tmp_fname}"
        if not os.path.exists(tmp_full_path):
            command = f"ffmpegthumbnailer -i {shlex.quote(cell)} -o {tmp_full_path} -s {720}"
            # command = [
            #     "ffmpegthumbnailer",
            #     "-i", cell,
            #     "-o", tmp_full_path,
            #     "-s", "720",
            # ]
            subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if is_kitty_graphics_supported():

            clear = False if len(data) and cell == data[0] else True
            display_image_with_icat(
                tmp_full_path,
                x=x+3,
                y=y+7,
                width=w-5,
                height=h-8,
                clear=clear,
            )
            displaying_image = True



    elif displaying_image:
        if is_kitty_graphics_supported():
            clear_kitty_image()
        elif len(data) > 2 and data[2] != None:
            old_proc = data[2]
            os.killpg(os.getpgid(old_proc.pid), signal.SIGTERM)
    # else:
    #     if is_kitty_graphics_supported():
    #         clear_kitty_image()

    elif len(attributes) == 3 and attributes[1].startswith("Filetype: text/"):
        lines = []
        with open(shlex.quote(cell), "r") as f:
            try:
                for _ in range(h):
                    line = next(f).strip()
                    lines.append(line)
            except:
                pass

        for i in range(min(h-8, len(lines))):
            stdscr.addstr(y+8+i, x+2, lines[i][:w-3])






    data[:] = [cell, displaying_image, proc]

    return []
