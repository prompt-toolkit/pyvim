#!/usr/bin/env python
"""
ptvim: STILL EXPERIMENTAL (!) Pure Python Vim clone.
Usage:
    ptvim <filename>
"""
from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import AlwaysOff, AlwaysOn, HasFocus, Condition, HasSearch
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.bindings.vi import ViStateFilter
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.toolbars import TokenListToolbar, SystemToolbar, SearchToolbar
from prompt_toolkit.renderer import Renderer
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.keys import Keys
from prompt_toolkit.selection import SelectionType

from pygments.styles.default import DefaultStyle
from pygments.lexers import get_lexer_for_filename
from pygments.token import Token
from pygments.style import Style

import codecs
import sys
import docopt


class VimStyle(Style):
    background_color = None
    styles = {
        # Highlighting of select text in document.
        Token.SelectedText:                           '#ffffff bg:#6666aa',
        Token.Toolbar:                                '#ffffff bg:#444444',
        Token.LineNumber:                             '#ffffff bg:#aaaa00',
        Token.Header:                                 '#ffffff bg:#662222',
        Token.SearchMatch:                            '#000000 bg:#ffff00',
        Token.SearchMatch.Current:                    '#000000 bg:#aaff33',
    }
    styles.update(DefaultStyle.styles)


class VimInputBar(Window):
    def __init__(self):
        super(VimInputBar, self).__init__(
            BufferControl(buffer_name='vim-input'),
            height=LayoutDimension.exact(1),
            filter=~HasSearch() & ~HasFocus('system'))


class Header(TokenListToolbar):
    def __init__(self):
        def get_tokens(cli):
            return [
                (Token.Header, "    Experimental Pure Python Vim editor. Type ':q' to quit."),
            ]
        super(Header, self).__init__(get_tokens, default_char=Char(' ', Token.Header))


class VimToolbar(TokenListToolbar):
    def __init__(self, filename, manager):
        def get_tokens(cli):
            insert_mode = manager.vi_state.input_mode == InputMode.INSERT
            replace_mode = manager.vi_state.input_mode == InputMode.REPLACE
            sel = cli.buffers['default'].selection_state
            visual_line = sel is not None and sel.type == SelectionType.LINES
            visual_char = sel is not None and sel.type == SelectionType.CHARACTERS

            return [
                (Token.Toolbar, filename),
                (Token.Toolbar, ' '),
                (Token.Toolbar, ' --INSERTION-- ' if insert_mode else ''),
                (Token.Toolbar, ' --REPLACE -- ' if replace_mode else ''),
                (Token.Toolbar, ' --VISUAL LINE-- ' if visual_line else ''),
                (Token.Toolbar, ' --VISUAL-- ' if visual_char else ''),
            ]
        super(VimToolbar, self).__init__(get_tokens, default_char=Char(' ', Token.Toolbar))


def edit_file(filename):
    manager = KeyBindingManager(enable_vi_mode=True, enable_system_prompt=True)
    manager.vi_state.input_mode = InputMode.NAVIGATION

    layout = HSplit([
        Header(),
        Window(content=BufferControl(
            show_line_numbers=AlwaysOn(),
            lexer=get_lexer_for_filename(filename).__class__)),
        VimToolbar(filename, manager),
        VimInputBar(),
        SystemToolbar(),
        SearchToolbar(),
    ])

    with codecs.open(filename, 'r', 'utf-8') as f:
        text = f.read()

    @manager.registry.add_binding(':', filter=ViStateFilter(manager.vi_state, InputMode.NAVIGATION))
    def enter_command_mode(event):
        """
        Entering command mode.
        """
        event.cli.focus_stack.push('vim-input')
        manager.vi_state.input_mode = InputMode.INSERT

    @manager.registry.add_binding(Keys.Escape, filter=HasFocus('vim-input'))
    @manager.registry.add_binding(Keys.ControlC, filter=HasFocus('vim-input'))
    @manager.registry.add_binding(
        Keys.Backspace,
        filter=HasFocus('vim-input') & Condition(lambda cli: cli.buffers['vim-input'].text == ''))
    def leave_command_mode(event):
        """
        Leaving command mode.
        """
        event.cli.focus_stack.pop()
        manager.vi_state.input_mode = InputMode.NAVIGATION
        event.cli.buffers['vim-input'].document = Document()

    @manager.registry.add_binding(Keys.ControlJ, filter=HasFocus('vim-input'))
    def process_command(event):
        """
        Handling of commands.
        """
        text = event.current_buffer.text

        def save():
            with codecs.open(filename, 'w', 'utf-8') as f:
                f.write(event.cli.buffers['default'].text)

        def leave_command_mode():
            event.cli.focus_stack.pop()
            manager.vi_state.input_mode = InputMode.NAVIGATION
            event.cli.buffers['vim-input'].document = Document()

        if text == 'w':
            save()
            leave_command_mode()
        elif text in ('wq', 'wqa'):
            save()
            event.cli.set_return_value('')

        elif text in ('q', 'qa', 'q!', 'qa!'):
            event.cli.set_return_value('')

        else:
            leave_command_mode()

        # TODO: validation of other commands.

    cli = CommandLineInterface(
        layout=layout,
        renderer=Renderer(use_alternate_screen=True),
        key_bindings_registry=manager.registry,
        buffers={
            'default': Buffer(
                returnable=AlwaysOff(),
                is_multiline=True,
                initial_document=Document(text, 0)),
            'vim-input': Buffer(returnable=AlwaysOff()),
        },
        style=VimStyle,
    )

    # Run interface.
    cli.read_input()


def run():
    a = docopt.docopt(__doc__)
    filename = a['<filename>']
    edit_file(filename)


if __name__ == '__main__':
    run()
