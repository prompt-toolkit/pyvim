from __future__ import unicode_literals

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.contrib.completers.base import WordCompleter
from prompt_toolkit.contrib.completers.filesystem import PathCompleter
from prompt_toolkit.contrib.completers.system import SystemCompleter
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter

from .grammar import COMMAND_GRAMMAR
from .commands import get_commands, SET_COMMANDS

__all__ = (
    'create_command_completer',
)


def create_command_completer(editor):
    commands = [c + ' ' for c in get_commands()]

    return GrammarCompleter(COMMAND_GRAMMAR, {
        'command': WordCompleter(commands),
        'location': PathCompleter(expanduser=True),
        'set_option': WordCompleter(sorted(SET_COMMANDS)),
        'buffer_name': BufferNameCompleter(editor),
        'colorscheme': ColorSchemeCompleter(editor),
        'shell_command': SystemCompleter(),
    })


class BufferNameCompleter(Completer):
    """
    Complete on buffer names.
    It is sufficient when the input appears anywhere in the buffer name, to
    trigger a completion.
    """
    def __init__(self, editor):
        self.editor = editor

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        for eb in self.editor.window_arrangement.editor_buffers:
            location = eb.location

            if location is not None and text in location:
                yield Completion(location, start_position=-len(text), display=location)


class ColorSchemeCompleter(Completer):
    """
    Complete on the names of the color schemes that are currently known to the
    Editor instance.
    """
    def __init__(self, editor):
        self.editor = editor

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        for style_name in self.editor.styles:
            if style_name.startswith(text):
                yield Completion(style_name[len(text):], display=style_name)
