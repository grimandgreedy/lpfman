import curses
import os
from pygments import lex
from pygments.lexers import guess_lexer_for_filename, TextLexer
from pygments.token import Token
from wcwidth import wcwidth

THEMES = {
    'dark': {
        Token.Keyword: (curses.COLOR_BLUE, 232),
        Token.Name: (curses.COLOR_WHITE, 232),
        Token.Comment: (curses.COLOR_GREEN, 232),
        Token.String: (curses.COLOR_YELLOW, 232),
        Token.Number: (curses.COLOR_MAGENTA, 232),
        Token.Operator: (curses.COLOR_CYAN, 232),
        Token.Punctuation: (curses.COLOR_WHITE, 232),
        Token.Generic: (curses.COLOR_WHITE, 232),
        Token.Name.Function: (curses.COLOR_CYAN, 232),
        Token.Name.Class: (curses.COLOR_BLUE, 232),
        Token.Name.Builtin: (curses.COLOR_MAGENTA, 232),
        Token.Literal: (curses.COLOR_RED, 232),
        Token.Generic.Heading: (curses.COLOR_CYAN, 232),
        Token.Generic.Subheading: (curses.COLOR_BLUE, 232),
        Token.Literal.String: (curses.COLOR_YELLOW, 232),
        "line_number": (curses.COLOR_BLACK, curses.COLOR_WHITE),
        "indent_guide": (curses.COLOR_BLACK, 232),
    },
    'light': {
        Token.Keyword: (curses.COLOR_BLUE, 255),
        Token.Name: (curses.COLOR_BLACK, 255),
        Token.Comment: (curses.COLOR_GREEN, 255),
        Token.String: (curses.COLOR_RED, 255),
        Token.Number: (curses.COLOR_MAGENTA, 255),
        Token.Operator: (curses.COLOR_CYAN, 255),
        Token.Punctuation: (curses.COLOR_BLACK, 255),
        Token.Generic: (curses.COLOR_BLACK, 255),
        Token.Name.Function: (curses.COLOR_CYAN, 255),
        Token.Name.Class: (curses.COLOR_BLUE, 255),
        Token.Name.Builtin: (curses.COLOR_MAGENTA, 255),
        Token.Literal: (curses.COLOR_RED, 255),
        Token.Generic.Heading: (curses.COLOR_CYAN, 255),
        Token.Generic.Subheading: (curses.COLOR_BLUE, 255),
        Token.Literal.String: (curses.COLOR_YELLOW, 255),
        "line_number": (curses.COLOR_BLACK, curses.COLOR_BLUE),
        "indent_guide": (curses.COLOR_WHITE, 255)
    }
}

def init_colors(theme_name):
    """ Initialise colours starting at 200. """
    curses.start_color()
    curses.use_default_colors()
    theme = THEMES.get(theme_name, THEMES['dark'])

    color_id = 200
    token_to_color = {}
    for token, (fg, bg) in theme.items():
        curses.init_pair(color_id, fg, bg)
        token_to_color[token] = curses.color_pair(color_id)
        color_id += 1

    return token_to_color

def get_color_for_token(token_type, token_to_color):
    """ Get colour pair from token. """
    while token_type not in token_to_color and token_type.parent:
        token_type = token_type.parent
    return token_to_color.get(token_type, curses.color_pair(0))

class LazyFileViewer:
    def __init__(self, filepath, lexer, block_size=50):
        self.filepath = filepath
        self.lexer = lexer
        self.block_size = block_size
        self.line_cache = {}  # line_number -> list[(char, token_type)]
        self.total_lines = self._count_lines()

    def _count_lines(self):
        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for _ in f)

    def get_lines(self, start_line, num_lines):
        lines = []
        needed_lines = range(start_line, start_line + num_lines)

        for line_num in needed_lines:
            if line_num >= self.total_lines:
                break
            if line_num not in self.line_cache:
                self._load_block_containing(line_num)
            lines.append(self.line_cache.get(line_num, []))

        return lines

    def _load_block_containing(self, line_number):
        block_start = (line_number // self.block_size) * self.block_size
        block_end = min(block_start + self.block_size, self.total_lines)

        # Read block of lines
        block_lines = []
        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if i < block_start:
                    continue
                if i >= block_end:
                    break
                block_lines.append(line)

        block_text = ''.join(block_lines)
        tokens = list(lex(block_text, self.lexer))

        # Split tokens into lines
        current_line = 0
        line_tokens = [[]]
        for ttype, value in tokens:
            for ch in value:
                if ch == '\n':
                    line_tokens.append([])
                    current_line += 1
                else:
                    if current_line >= len(line_tokens):
                        line_tokens.append([])
                    line_tokens[current_line].append((ch, ttype))

        # Store in cache
        for i, tok_line in enumerate(line_tokens):
            absolute_line = block_start + i
            if absolute_line < self.total_lines:
                self.line_cache[absolute_line] = tok_line

def display_code(
    stdscr,
    viewer,
    token_to_color,
    code_x,
    code_y,
    code_w,
    code_h,
    show_line_numbers,
    indent_guides
):
    curses.curs_set(0)

    def draw(scroll_offset = 0):
        max_y, max_x = stdscr.getmaxyx()
        for i in range(code_h):
            try:
                stdscr.addstr(code_y + i, code_x, ' '*code_w)
            except:
                pass
            # stdscr.move(code_y + i, code_x)
            # stdscr.clrtoeol()
        # stdscr.erase()

        visible = viewer.get_lines(scroll_offset, code_h)
        for idx, line in enumerate(visible):
            y = code_y + idx
            if y >= max_y:
                return None

            x = code_x
            if show_line_numbers:
                ln = str(scroll_offset + idx + 1).rjust(line_num_width - 1) + " "
                ln_color = token_to_color.get("line_number", curses.color_pair(0))
                try:
                    stdscr.addstr(y, x, ln[:max_x - x], ln_color)
                except curses.error:
                    pass
                x += line_num_width

            # Use wcwidth to prevent special chars overflowing screen width
            col = 0
            for ch, ttype in line:
                width = wcwidth(ch)
                if width < 0:
                    width = 0  # unprintable

                if x + col + width > max_x or y >= max_y:
                    break

                try:
                    if indent_guides and ch == ' ' and (col % 4 == 0):
                        guide = token_to_color.get("indent_guide", curses.color_pair(0))
                        stdscr.addstr(y, x + col, '│', guide)
                    else:
                        color = get_color_for_token(ttype, token_to_color)
                        stdscr.addstr(y, x + col, ch, color)
                except curses.error:
                    pass

                col += width

        stdscr.refresh()

    scroll_offset = 0
    num_lines = viewer.total_lines
    line_num_width = (len(str(num_lines)) + 2) if show_line_numbers else 0

    draw(scroll_offset)

def get_lexer(filepath):
    """ Guess the lexer to use for the file. """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            sample = f.read(2048)
        return guess_lexer_for_filename(filepath, sample)
    except Exception:
        return TextLexer()

def preview_text(
    stdscr, 
    filepath,
    code_x=0,
    code_y=0,
    code_w=None,
    code_h=None,
    show_line_numbers=False,
    indent_guides=False,
    theme="dark"
):
    """ Create code preview at code_x, code_y, of size (code_w, code_h)"""
    try:
        if not os.path.isfile(filepath):
            return None

        lexer = get_lexer(filepath)

        max_y, max_x = stdscr.getmaxyx()

        if code_w is None:
            code_w = max_x - code_x
        if code_h is None:
            code_h = max_y - code_y

        viewer = LazyFileViewer(filepath, lexer, block_size=code_h)

        token_to_color = init_colors(theme)

        display_code(
            stdscr=stdscr,
            viewer=viewer,
            token_to_color=token_to_color,
            code_x=code_x,
            code_y=code_y,
            code_w=code_w,
            code_h=code_h,
            show_line_numbers=show_line_numbers,
            indent_guides=indent_guides,
        )
    except Exception as e:
        return None
