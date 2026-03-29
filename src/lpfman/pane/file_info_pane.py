import curses
import os

from listpick.pane.pane_utils import get_file_attributes
from lpfman.preview.registry import DEFAULT_REGISTRY
from lpfman.preview.base import PreviewState


def right_split_file_attributes(stdscr, x, y, w, h, state, row, cell, data: list = [], test: bool = False):
    """
    Display file attributes in right pane.
    """
    if test: return True

    # Separator
    for j in range(h):
        stdscr.addstr(j+y, x, '│', curses.color_pair(state["colours_start"]+16) | curses.A_REVERSE)

    # Display pane count
    pane_count = len(state["right_panes"])
    pane_index = state["right_pane_index"]
    if pane_count > 1:
        s = f" {pane_index+1}/{pane_count} "
        stdscr.addstr(y+h-1, x+w-len(s)-1, s, curses.color_pair(state["colours_start"]+20))

    if len(state["indexed_items"]) == 0:
        data[:] = ["", None, None]
        return None

    cell = state["indexed_items"][state["cursor_pos"]][1][0]

    # Clear previous preview on file change
    if len(data) == 3 and cell != data[0] and data[2] is not None:
        data[2].clear(data[1])

    # Directory special case — show listing without filename/attributes chrome
    if os.path.isdir(cell):
        previewer = DEFAULT_REGISTRY.find(cell, "")
        if previewer:
            new_state = previewer.render(stdscr, cell, x, y, w, h, data[1] if len(data) == 3 and data[0] == cell else None)
            data[:] = [cell, new_state, previewer]
        else:
            data[:] = [cell, None, None]
        return None

    # Filename/cursor cell value
    stdscr.addstr(y+1, x+2, cell[:w-3])

    # Display file attributes
    attributes = get_file_attributes(cell)
    if len(attributes) != 3:
        data[:] = [cell, None, None]
        return None
    for i, attr in enumerate(attributes):
        stdscr.addstr(y+2+i, x+4, attr[:w-5])

    # Extract MIME type
    mime_type = attributes[1][len("Filetype: "):]

    # Registry dispatch
    prev_state = data[1] if len(data) == 3 and data[0] == cell else None
    previewer = DEFAULT_REGISTRY.find(cell, mime_type)
    if previewer is None:
        data[:] = [cell, None, None]
        return []

    new_state = previewer.render(stdscr, cell, x+3, y+6, w-5, h-7, prev_state)
    data[:] = [cell, new_state, previewer]
    return []
