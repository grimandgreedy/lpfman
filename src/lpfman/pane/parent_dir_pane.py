import curses
import os

def parent_dir_pane(stdscr, x, y, w, h, state, row, cell, data: list = [], test: bool = False):
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
        stdscr.addstr(j+y, x+w-1, '│', curses.color_pair(state["colours_start"]+16) | curses.A_REVERSE)

    # # Display pane count
    # pane_count = len(state["right_panes"])
    # pane_index = state["right_pane_index"]
    # if pane_count > 1:
    #     s = f" {pane_index+1}/{pane_count} "
    #     stdscr.addstr(y+h-1, x+w-len(s)-1, s, curses.color_pair(state["colours_start"]+20))

    if len(state["indexed_items"]) == 0:
        data[:] = ["", False, None]
        return None
    if os.getcwd() == "/":
        return None
    
    fs = sorted(os.listdir(".."), key=lambda x: (x.startswith('.'), x))
    for i, f in enumerate(fs):
        if y+1+i >= h: break
        isdir = os.path.isdir(f"{cell}/{f}")
        isdir = os.path.isdir(f"../{f}")
        if isdir:
            color = curses.color_pair(11)
        else:
            color = curses.color_pair(9)
        try:
            stdscr.addstr(y+1+i, x+2, f[:w-5], color)
        except:
            pass
    data[:] = [cell, False, None]
