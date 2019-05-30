from __future__ import unicode_literals

from pyvim.window_arrangement import EditorBuffer, VSplit, TabPage, Window


def test_initial(window, tab_page):
    assert isinstance(tab_page.root, VSplit)
    assert tab_page.root == [window]


def test_vsplit(editor, tab_page):
    # Create new buffer.
    eb = EditorBuffer(editor)

    # Insert in tab, by splitting.
    tab_page.vsplit(eb)

    assert isinstance(tab_page.root, VSplit)
    assert len(tab_page.root) == 2


def test_tab_page_get_windows_for_buffer(editor, editor_buffer, tab_page_with_splits):
    tab_page1 = tab_page_with_splits

    windows = list(tab_page1.get_windows_for_buffer(editor_buffer))
    assert all(w.editor_buffer == editor_buffer for w in windows)
    assert len(windows) == 3

def test_window_arrangement_get_windows_for_buffer(editor, editor_buffer, tab_page_with_splits, window_arrangement):
    tab_page1 = tab_page_with_splits
    tab_page2 = TabPage(Window(editor_buffer))

    window_arrangement.tab_pages[:] = [tab_page1, tab_page2]
    windows = list(window_arrangement.get_windows_for_buffer(editor_buffer))
    assert all(w.editor_buffer == editor_buffer for w in windows)
    assert len(windows) == 4
