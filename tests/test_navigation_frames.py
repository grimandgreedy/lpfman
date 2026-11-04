"""
What the user sees while navigating, frame by frame.

The screen should never go blank between two frames that have rows: moving
into or out of a directory should replace the old listing with the new one,
the same way moving the cursor does.
"""

import time

import pytest

from harness.tui_recorder import blank_spans

# Longest the screen may stay blank. Anything above roughly one frame at 60Hz
# is visible.
MAX_BLANK = 0.016

# How long to watch the screen after each action. lpfman keeps redrawing while
# column data loads, so waiting for output to stop would wait for the whole load.
WINDOW = 1.0


def enter(rec, name, expect, timeout=30):
    t = rec.send("\n", f"enter {name}/")
    rec.wait_for_text(expect, timeout=timeout, after=t)
    time.sleep(WINDOW)
    return t


def go_up(rec, expect, timeout=10):
    t = rec.send("h", "up")
    rec.wait_for_text(expect, timeout=timeout, after=t)
    time.sleep(WINDOW)
    return t


def visible_blanks(rec, since):
    """Blank stretches longer than MAX_BLANK in the WINDOW after `since`, as (start, duration)."""
    frames = [f for f in rec.frames_since(since) if f.t <= since + WINDOW]
    spans = blank_spans(frames, end=since + WINDOW)
    return [(round(s - since, 3), round(d, 3)) for s, d in spans if d > MAX_BLANK]


@pytest.fixture
def lpfman_in_tree(run_lpfman, tree):
    rec = run_lpfman(tree)
    rec.wait_for_text("big", timeout=15)
    time.sleep(0.5)
    return rec


def warm_up(rec):
    """Enter and leave big/ once, so one-off costs (imports, caches) are paid."""
    enter(rec, "big", "file_00000", timeout=60)
    go_up(rec, "small")


def test_cursor_down_never_blanks(lpfman_in_tree):
    rec = lpfman_in_tree
    warm_up(rec)
    t = rec.send("j", "cursor down")
    time.sleep(WINDOW)
    assert visible_blanks(rec, t) == []


def test_entering_directory_never_blanks(lpfman_in_tree):
    rec = lpfman_in_tree
    warm_up(rec)
    t = enter(rec, "big", "file_00000")
    assert visible_blanks(rec, t) == [], "screen went blank after entering big/ (start s, duration s)"


def test_leaving_directory_never_blanks(lpfman_in_tree):
    rec = lpfman_in_tree
    warm_up(rec)
    enter(rec, "big", "file_00000")
    t = go_up(rec, "small")
    assert visible_blanks(rec, t) == [], "screen went blank after leaving big/ (start s, duration s)"


def test_entering_directory_shows_rows_quickly(lpfman_in_tree):
    rec = lpfman_in_tree
    warm_up(rec)
    t = rec.send("\n", "enter big/")
    f = rec.wait_for_text("file_00000", timeout=30, after=t)
    assert f.t - t < 0.1, f"first frame with rows took {f.t - t:.3f}s"


def test_first_entry_shows_rows_quickly(lpfman_in_tree):
    """The first time a text file is previewed must not stall the whole screen."""
    rec = lpfman_in_tree
    t = rec.send("\n", "enter big/ (cold)")
    f = rec.wait_for_text("file_00000", timeout=60, after=t)
    assert f.t - t < 0.5, f"first frame with rows took {f.t - t:.3f}s"
