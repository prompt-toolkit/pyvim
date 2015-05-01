from __future__ import unicode_literals

import pytest

from prompt_toolkit.buffer import Buffer
from pyvim.window_arrangement import TabPage, EditorBuffer, Window


@pytest.fixture
def prompt_buffer():
    return Buffer()


@pytest.fixture
def editor_buffer(prompt_buffer):
    return EditorBuffer(prompt_buffer, 'b1')


@pytest.fixture
def window(editor_buffer):
    return Window(editor_buffer)


@pytest.fixture
def tab_page(window):
    return TabPage(window)
