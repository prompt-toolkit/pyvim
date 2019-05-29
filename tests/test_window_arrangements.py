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


def test_tab_page_get_windows_for_buffer(editor):
    # Create new buffer.
    eb1 = EditorBuffer(editor)
    eb2 = EditorBuffer(editor)

    # Insert in tab, by splitting.
    tab_page1 = TabPage(Window(eb1))
    tab_page1.vsplit(eb1)
    tab_page1.vsplit(eb2)
    tab_page1.hsplit(eb1)

    windows = list(tab_page1.get_windows_for_buffer(eb1))
    assert all(w.editor_buffer == eb1 for w in windows)
    assert len(windows) == 3

def test_window_arrangement_get_windows_for_buffer(editor, window_arrangement):
    # Create new buffer.
    eb1 = EditorBuffer(editor)
    eb2 = EditorBuffer(editor)

    # Insert in tab, by splitting.
    tab_page1 = TabPage(Window(eb1))
    tab_page1.vsplit(eb1)
    tab_page1.vsplit(eb2)
    tab_page1.hsplit(eb1)
    tab_page2 = TabPage(Window(eb1))

    window_arrangement.tab_pages[:] = [tab_page1, tab_page2]
    windows = list(window_arrangement.get_windows_for_buffer(eb1))
    assert all(w.editor_buffer == eb1 for w in windows)
    assert len(windows) == 4
