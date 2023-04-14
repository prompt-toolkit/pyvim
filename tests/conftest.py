from __future__ import unicode_literals

import pytest

from prompt_toolkit.output import DummyOutput
from prompt_toolkit.input import DummyInput
from pyvim.editor import Editor
from pyvim.window_arrangement import TabPage, EditorBuffer, Window, WindowArrangement


@pytest.fixture
def editor():
    return Editor(output=DummyOutput(), input=DummyInput())


@pytest.fixture
def editor_buffer(editor):
    return EditorBuffer(editor)


@pytest.fixture
def window(editor_buffer):
    return Window(editor_buffer)


@pytest.fixture
def tab_page(window):
    return TabPage(window)


@pytest.fixture
def tab_page_with_splits(editor_buffer, window):
    editor_buffer2 = EditorBuffer(editor)

    tab_page = TabPage(Window(editor_buffer))
    tab_page.vsplit(editor_buffer)
    tab_page.vsplit(editor_buffer2)
    tab_page.hsplit(editor_buffer)
    return tab_page


@pytest.fixture
def window_arrangement(editor):
    return WindowArrangement(editor)
