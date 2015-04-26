from __future__ import unicode_literals

from prompt_toolkit.filters import Condition, HasFocus, Filter
from prompt_toolkit.key_binding.bindings.utils import create_handle_decorator
from prompt_toolkit.key_binding.bindings.vi import ViStateFilter
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.utils import find_window_for_buffer_name

from .enums import COMMAND_BUFFER

__all__ = (
    'create_key_bindings',
)


def create_key_bindings(editor):
    """
    Create custom key bindings.

    This starts with the key bindings, defined by `prompt-toolkit`, but adds
    the ones which are specific for the editor.
    """
    # Create new Key binding manager.
    manager = KeyBindingManager(enable_vi_mode=True, enable_system_prompt=True)
    manager.vi_state.input_mode = InputMode.NAVIGATION

    # Filters.
    vi_buffer_focussed = Condition(lambda cli: cli.current_buffer_name.startswith('buffer-'))

    in_insert_mode = (ViStateFilter(manager.vi_state, InputMode.INSERT) & vi_buffer_focussed)
    in_navigation_mode = (ViStateFilter(manager.vi_state, InputMode.NAVIGATION) &
                          vi_buffer_focussed)

    # Decorator.
    handle = create_handle_decorator(manager.registry)

    @handle(Keys.ControlF)
    def _(event):
        """
        Scroll window down.
        """
        w = find_window_for_buffer_name(event.cli.layout, event.cli.current_buffer_name)
        b = event.cli.current_buffer

        if w and w.render_info:
            new_document_line = min(
                b.document.line_count - 1,
                b.document.cursor_position_row + int(w.render_info.rendered_height / 2))
            b.cursor_position = b.document.translate_row_col_to_index(new_document_line, 0)
            w.vertical_scroll = w.render_info.input_line_to_screen_line(new_document_line)

    @handle(Keys.ControlT, filter=in_insert_mode)
    def _(event):
        """
        Indent current line.
        """
        b = event.cli.current_buffer

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

    @handle(Keys.ControlU)
    def _(event):
        """
        Scroll window up.
        """
        w = find_window_for_buffer_name(event.cli.layout, event.cli.current_buffer_name)
        b = event.cli.current_buffer

        if w and w.render_info:
            new_document_line = max(0, b.document.cursor_position_row -
                                    int(w.render_info.rendered_height / 2))
            b.cursor_position = b.document.translate_row_col_to_index(new_document_line, 0)
            w.vertical_scroll = w.render_info.input_line_to_screen_line(new_document_line)

    @handle(Keys.ControlR, filter=in_navigation_mode, save_before=False)
    def _(event):
        """
        Redo.
        """
        event.cli.current_buffer.redo()

    @handle(':', filter=in_navigation_mode)
    def enter_command_mode(event):
        """
        Entering command mode.
        """
        editor.enter_command_mode()

    @handle(Keys.Tab, filter=ViStateFilter(manager.vi_state, InputMode.INSERT) &
            ~HasFocus(COMMAND_BUFFER) & WhitespaceBeforeCursorOnLine())
    def _(event):
        """
        When the 'tab' key is pressed with only whitespace character before the
        cursor, do autocompletion. Otherwise, insert indentation.
        """
        b = event.cli.current_buffer
        if editor.expand_tab:
            b.insert_text('    ')
        else:
            b.insert_text('\t')

    @handle(Keys.Escape, filter=HasFocus(COMMAND_BUFFER))
    @handle(Keys.ControlC, filter=HasFocus(COMMAND_BUFFER))
    @handle(
        Keys.Backspace,
        filter=HasFocus(COMMAND_BUFFER) & Condition(lambda cli: cli.buffers[COMMAND_BUFFER].text == ''))
    def leave_command_mode(event):
        """
        Leaving command mode.
        """
        editor.leave_command_mode()

    @handle(Keys.ControlW, Keys.ControlW, filter=in_navigation_mode)
    def focus_next_window(event):
        editor.window_arrangement.cycle_focus()
        editor.sync_with_prompt_toolkit()

    @handle('g', 't', filter=in_navigation_mode)
    def focus_next_tab(event):
        editor.window_arrangement.go_to_next_tab()
        editor.sync_with_prompt_toolkit()

    @handle('g', 'T', filter=in_navigation_mode)
    def focus_previous_tab(event):
        editor.window_arrangement.go_to_previous_tab()
        editor.sync_with_prompt_toolkit()

    @handle(Keys.ControlJ, filter=in_navigation_mode)
    def _(event):
        """ Enter in navigation mode should move to the start of the next line. """
        b = event.current_buffer
        b.cursor_down(count=event.arg)
        b.cursor_position += b.document.get_start_of_line_position(after_whitespace=True)

    @handle(Keys.F1)
    def show_help(event):
        editor.show_help()

    return manager


class WhitespaceBeforeCursorOnLine(Filter):
    """
    Filter which evaluates to True when the characters before the cursor are
    whitespace, or we are at the start of te line.
    """
    def __call__(self, cli):
        b = cli.current_buffer
        before_cursor = b.document.current_line_before_cursor

        return bool(not before_cursor or before_cursor[-1].isspace())
