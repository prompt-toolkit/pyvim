from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer
from pyvim.window_arrangement import EditorBuffer, VSplit


def test_initial(window, tab_page):
    assert isinstance(tab_page.root, VSplit)
    assert tab_page.root == [window]


def test_vsplit(tab_page):
    # Create new buffer.
    b = Buffer()
    eb = EditorBuffer(b, 'b1')

    # Insert in tab, by splitting.
    tab_page.vsplit(eb)

    assert isinstance(tab_page.root, VSplit)
    assert len(tab_page.root) == 2
