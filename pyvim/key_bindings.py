from __future__ import unicode_literals

from prompt_toolkit.application import get_app
from prompt_toolkit.filters import Condition, has_focus, vi_insert_mode, vi_navigation_mode
from prompt_toolkit.key_binding import KeyBindings

import os

__all__ = (
    'create_key_bindings',
)


def _current_window_for_event(event):
    """
    Return the `Window` for the currently focussed Buffer.
    """
    return event.app.layout.current_window


def create_key_bindings(editor):
    """
    Create custom key bindings.

    This starts with the key bindings, defined by `prompt-toolkit`, but adds
    the ones which are specific for the editor.
    """
    kb = KeyBindings()

    # Filters.
    @Condition
    def vi_buffer_focussed():
        app = get_app()
        if app.layout.has_focus(editor.search_buffer) or app.layout.has_focus(editor.command_buffer):
            return False
        return True

    in_insert_mode = vi_insert_mode & vi_buffer_focussed
    in_navigation_mode = vi_navigation_mode & vi_buffer_focussed

    @kb.add('c-t')
    def _(event):
        """
        Override default behaviour of prompt-toolkit.
        (Control-T will swap the last two characters before the cursor, because
        that's what readline does.)
        """
        pass

    @kb.add('c-t', filter=in_insert_mode)
    def indent_line(event):
        """
        Indent current line.
        """
        b = event.application.current_buffer

        # Move to start of line.
        pos = b.document.get_start_of_line_position(after_whitespace=True)
        b.cursor_position += pos

        # Insert tab.
        if editor.expand_tab:
            b.insert_text('    ')
        else:
            b.insert_text('\t')

        # Restore cursor.
        b.cursor_position -= pos

    @kb.add('c-r', filter=in_navigation_mode, save_before=(lambda e: False))
    def redo(event):
        """
        Redo.
        """
        event.app.current_buffer.redo()

    @kb.add(':', filter=in_navigation_mode)
    def enter_command_mode(event):
        """
        Entering command mode.
        """
        editor.enter_command_mode()

    @kb.add('tab', filter=vi_insert_mode &
            ~has_focus(editor.command_buffer) & whitespace_before_cursor_on_line)
    def autocomplete_or_indent(event):
        """
        When the 'tab' key is pressed with only whitespace character before the
        cursor, do autocompletion. Otherwise, insert indentation.
        """
        b = event.app.current_buffer
        if editor.expand_tab:
            b.insert_text('    ')
        else:
            b.insert_text('\t')

    @kb.add('escape', filter=has_focus(editor.command_buffer))
    @kb.add('c-c', filter=has_focus(editor.command_buffer))
    @kb.add('backspace',
        filter=has_focus(editor.command_buffer) & Condition(lambda: editor.command_buffer.text == ''))
    def leave_command_mode(event):
        """
        Leaving command mode.
        """
        editor.leave_command_mode()

    @kb.add('c-w', 'c-w', filter=in_navigation_mode)
    def focus_next_window(event):
        editor.window_arrangement.cycle_focus()
        editor.sync_with_prompt_toolkit()

    @kb.add('c-w', 'n', filter=in_navigation_mode)
    def horizontal_split(event):
        """
        Split horizontally.
        """
        editor.window_arrangement.hsplit(None)
        editor.sync_with_prompt_toolkit()

    @kb.add('c-w', 'v', filter=in_navigation_mode)
    def vertical_split(event):
        """
        Split vertically.
        """
        editor.window_arrangement.vsplit(None)
        editor.sync_with_prompt_toolkit()

    @kb.add('g', 't', filter=in_navigation_mode)
    def focus_next_tab(event):
        editor.window_arrangement.go_to_next_tab()
        editor.sync_with_prompt_toolkit()

    @kb.add('g', 'T', filter=in_navigation_mode)
    def focus_previous_tab(event):
        editor.window_arrangement.go_to_previous_tab()
        editor.sync_with_prompt_toolkit()

    @kb.add('f1')
    def show_help(event):
        editor.show_help()

    @Condition
    def in_file_explorer_mode():
        return bool(editor.current_editor_buffer and
            editor.current_editor_buffer.in_file_explorer_mode)

    @kb.add('enter', filter=in_file_explorer_mode)
    def open_path(event):
        """
        Open file/directory in file explorer mode.
        """
        name_under_cursor = event.current_buffer.document.current_line
        new_path = os.path.normpath(os.path.join(
            editor.current_editor_buffer.location, name_under_cursor))

        editor.window_arrangement.open_buffer(
            new_path, show_in_current_window=True)
        editor.sync_with_prompt_toolkit()

    @kb.add('-', filter=in_file_explorer_mode)
    def to_parent_directory(event):
        new_path = os.path.normpath(os.path.join(
            editor.current_editor_buffer.location, '..'))

        editor.window_arrangement.open_buffer(
            new_path, show_in_current_window=True)
        editor.sync_with_prompt_toolkit()

    return kb


@Condition
def whitespace_before_cursor_on_line():
    """
    Filter which evaluates to True when the characters before the cursor are
    whitespace, or we are at the start of te line.
    """
    b = get_app().current_buffer
    before_cursor = b.document.current_line_before_cursor

    return bool(not before_cursor or before_cursor[-1].isspace())
