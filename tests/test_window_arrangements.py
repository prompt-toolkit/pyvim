from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer
from pyvim.editor import Editor
from pyvim.window_arrangement import TabPage, EditorBuffer, Window, HSplit, VSplit

import unittest


class BufferTest(unittest.TestCase):
    def setUp(self):
        e = Editor()
        eb = EditorBuffer(e, 'b1')
        self.window = Window(eb)
        self.tabpage = TabPage(self.window)

    def test_initial(self):
        self.assertIsInstance(self.tabpage.root, VSplit)
        self.assertEqual(self.tabpage.root, [self.window])

    def test_vsplit(self):
        # Create new buffer.
        e = Editor()
        eb = EditorBuffer(e, 'b1')

        # Insert in tab, by splitting.
        self.tabpage.vsplit(eb)

        self.assertIsInstance(self.tabpage.root, VSplit)
        self.assertEqual(len(self.tabpage.root), 2)


if __name__ == '__main__':
    unittest.main()
