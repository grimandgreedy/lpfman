#!/bin/python

import os
import sys
import curses

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.expanduser("../list_picker/"))

from list_picker.utils.utils import *
from list_picker.list_picker_app import *
from list_picker.ui.list_picker_colours import get_colours
from list_picker.utils.table_to_list_of_lists import *
from list_picker.utils.options_selectors import default_option_selector
from list_picker.ui.keys import menu_keys


def begin(stdscr: curses.window):
    """ Main loop for lpfman. """
    fman_data = {
            "colour_theme_number": 0,
    }
    while True:
        ## Get files and folders in directory
        sc = os.scandir(".")
        files, dirs, symlinks = [], [], []

        for ob in sc:
            if ob.is_file(): files.append(ob)
            elif ob.is_dir(): dirs.append(ob)
            if ob.is_symlink(): symlinks.append(ob)
        dirs.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: x.name.lower())
        

        print("Files****")
        for file in files:
            print(file)
        print("DIRs****")
        for dir in dirs:
            print(dir)

        header = ["Fname", "type", "st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime"]
        list_entries = []
        list_entries += [[dir.name, 0, *list(dir.stat())] for dir in dirs]
        list_entries += [[f.name, 1, *list(f.stat())] for f in files]
        list_entries += [[s.name, 2] + ["" for _ in range(len(header)-2)] for s in symlinks]
        list_entries.insert(0, ["..", 0,] + list(os.stat("..")))
        print(list_entries)

        for entry in list_entries: 
            # convert unix time to readable format
            try: 
                entry[-1] = datetime.fromtimestamp(entry[-1]).strftime('%y-%m-%d %H:%M')
                entry[-2] = datetime.fromtimestamp(entry[-2]).strftime('%y-%m-%d %H:%M')
                entry[-3] = datetime.fromtimestamp(entry[-3]).strftime('%y-%m-%d %H:%M')
            except:
                pass
        for l in list_entries:
            print("\t" + str(l))
        
        fman_data["items"] = list_entries
        fman_data["header"] = header
        selected_entries, opts, fman_data = picker(
            stdscr,
            **fman_data,
        )
        if not selected_entries: break
        list_entries = fman_data["items"]
        # print(selected_entries)
        if len(selected_entries) == 1:
            if selected_entries[0] == 0:
                os.chdir("..")
                continue
            if os.path.isdir(list_entries[selected_entries[0]][0]):
                os.chdir(list_entries[selected_entries[0]][0])
                continue

        file_and_dir_open_list = [list_entries[i][0] for i in selected_entries]
        openFiles(file_and_dir_open_list)

def main():
    ## Run curses
    stdscr = curses.initscr()
    stdscr.keypad(True)
    curses.start_color()
    curses.noecho()  # Turn off automatic echoing of keys to the screen
    curses.cbreak()  # Interpret keystrokes immediately (without requiring Enter)
    error = ""
    try:
        begin(stdscr)
    except Exception as e:
        error = str(e)
        pass


    ## Clean up curses and clear terminal
    stdscr.clear()
    stdscr.refresh()
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    os.system('cls' if os.name == 'nt' else 'clear')

    if error: print(error)
