#!/bin/python

import os
import sys
import curses
from datetime import datetime
import shlex


# os.chdir(os.path.dirname(os.path.realpath(__file__)))

from listpick.utils.utils import *
from listpick.listpick_app import Picker, start_curses, close_curses
from listpick.ui.picker_colours import get_colours
from listpick.utils.table_to_list_of_lists import *
from listpick.utils.options_selectors import default_option_selector
from listpick.ui.keys import menu_keys
from file_info_pane import right_split_file_attributes
from listpick.utils.generate_data_multithreaded import generate_picker_data, command_to_func
from lpfman_utils import get_filetype, get_size, get_mtime


class FileManager:
    def __init__(
        self,
        stdscr: curses.window,
        show_hidden_files: bool = False,
    ):

        self.stdscr = stdscr
        self.show_hidden_files = show_hidden_files

        header = ["Fname", "type", "st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime"]

        self.column_names = ["Filename", "Size", "Filetype", "Modified Time"]

        # commands_list = [
        #     "du -hs {} | awk '{{print $1 }}'",
        # ]
        # column_functions = [command_to_func(command) for command in commands_list]

        self.column_functions = [get_size, get_filetype, get_mtime]

        self.fman_data = {
            "colour_theme_number": 3,
            "cell_cursor": True,
            "split_right": True,
            "header": self.column_names,
            "cell_cursor": False,
        }

        self.fman_data["items"] = [[]]
        self.fman_data["header"] = header
        self.fman_data["right_panes"] = [
            # File attribures
            {
                "proportion": 2/3,
                "auto_refresh": False,
                "get_data": lambda data, state: [],
                "display": right_split_file_attributes,
                "data": ["Files", [str(x) for x in range(100)]],
                "refresh_time": 1.0,
            },
        ]

        self.UI = Picker(self.stdscr, **self.fman_data)

    def run(self):
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


            if not self.show_hidden_files:
                visible_dirs = [dir.name for dir in dirs if not dir.name.startswith(".")]
                visible_files = [file.name for file in files if not file.name.startswith(".")]
            else:
                visible_dirs = [dir.name for dir in dirs]
                visible_files = [file.name for file in files]


            filenames = [".."] + visible_dirs + visible_files

            highlights = [ ]
            for i in range(len(visible_dirs)+1):
                highlight = {
                    "row" : i, 
                    "field" : 0,
                    "match" : ".*",
                    "color" : 11,
                }
                highlights.append(highlight)
            self.UI.highlights = highlights


            def generate_data(items, header, visible_rows_indices, getting_data):
                generate_picker_data(
                    filenames,
                    self.column_functions,
                    self.column_names,
                    items,
                    header,
                    visible_rows_indices,
                    getting_data,
                )

            self.UI.refresh_function = generate_data
            self.UI.get_data_startup = True
            self.UI.get_new_data = True

            cwd = os.getcwd()
            cwd = cwd.replace("/home/" + os.getlogin(), "~")
            self.UI.footer_string = cwd

            selected_entries, opts, fman_data = self.UI.run()

            if not selected_entries: break
            list_entries = fman_data["items"]

            # print(selected_entries)
            if len(selected_entries) == 1:
                target = self.UI.items[selected_entries[0]][0]
                if target == "..":
                    os.chdir("..")
                    continue
                elif os.path.isdir(target):
                    try:
                        os.chdir(target)
                    except Exception as e:
                        self.UI.startup_notification = f"Error: {e}"
                    self.UI.filter_query = ""
                    self.UI.cursor_pos = 0

                    continue

            targets = [shlex.quote(self.UI.items[i][0]) for i in selected_entries]

            openFiles(targets)

def main():
    stdscr = start_curses()
    app = FileManager(stdscr)
    app.run()
    close_curses(stdscr)

if __name__ == "__main__":
    main()
