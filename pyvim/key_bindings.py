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


def _current_window_for_event(event):
    """
    Return the `Window` for the currently focussed Buffer.
    """
    return find_window_for_buffer_name(event.cli.layout, event.cli.current_buffer_name)


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
    def scroll_forward(event, half=False):
        """
        Scroll window down.
        """
        w = _current_window_for_event(event)
        b = event.cli.current_buffer

        if w and w.render_info:
            # Determine height to move.
            shift = w.render_info.rendered_height
            if half:
                shift = int(shift / 2)

            # Scroll.
            new_document_line = min(
                b.document.line_count - 1,
                b.document.cursor_position_row + int(shift))
            b.cursor_position = b.document.translate_row_col_to_index(new_document_line, 0)
            w.vertical_scroll = w.render_info.input_line_to_screen_line(new_document_line)

    @handle(Keys.ControlB)
    def scroll_backward(event, half=False):
        """
        Scroll window up.
        """
        w = _current_window_for_event(event)
        b = event.cli.current_buffer

        if w and w.render_info:
            # Determine height to move.
            shift = w.render_info.rendered_height
            if half:
                shift = int(shift / 2)

            # Scroll.
            new_document_line = max(0, b.document.cursor_position_row - int(shift))
            b.cursor_position = b.document.translate_row_col_to_index(new_document_line, 0)
            w.vertical_scroll = w.render_info.input_line_to_screen_line(new_document_line)

    @handle(Keys.ControlD)
    def scroll_half_page_down(event):
        """
        Same as ControlF, but only scroll half a page.
        """
        scroll_forward(event, half=True)

    @handle(Keys.ControlU)
    def scroll_half_page_up(event):
        """
        Same as ControlB, but only scroll half a page.
        """
        scroll_backward(event, half=True)

    @handle(Keys.ControlE)
    def scroll_one_line_down(event):
        """
        scroll_offset += 1
        """
        w = find_window_for_buffer_name(event.cli.layout, event.cli.current_buffer_name)
        b = event.cli.current_buffer

        if w:
            # When the cursor is at the top, move to the next line. (Otherwise, only scroll.)
            if w.render_info:
                info = w.render_info
                if info.cursor_position.y <= info.configured_scroll_offset:
                    b.cursor_position += b.document.get_cursor_down_position()

            w.vertical_scroll += 1

    @handle(Keys.ControlY)
    def scroll_one_line_up(event):
        """
        scroll_offset -= 1
        """
        w = find_window_for_buffer_name(event.cli.layout, event.cli.current_buffer_name)
        b = event.cli.current_buffer

        if w:
            # When the cursor is at the bottom, move to the previous line. (Otherwise, only scroll.)
            if w.render_info:
                info = w.render_info

                if info.cursor_position.y >= info.rendered_height - 1 - info.configured_scroll_offset:
                    b.cursor_position += b.document.get_cursor_up_position()

            # Scroll window
            w.vertical_scroll -= 1

    @handle(Keys.PageDown)
    def scroll_page_down(event):
        """
        Scroll page down. (Prefer the cursor at the top of the page, after scrolling.)
        """
        w = _current_window_for_event(event)
        b = event.cli.current_buffer

        if w and w.render_info:
            # Scroll down one page.
            w.vertical_scroll += w.render_info.rendered_height

            # Put cursor at the top of the visible region.
            try:
                new_document_line = w.render_info.screen_line_to_input_line[w.vertical_scroll]
            except KeyError:
                new_document_line = b.document.line_count - 1

            b.cursor_position = b.document.translate_row_col_to_index(new_document_line, 0)
            b.cursor_position += b.document.get_start_of_line_position(after_whitespace=True)

    @handle(Keys.PageUp)
    def scroll_page_up(event):
        """
        Scroll page up. (Prefer the cursor at the bottom of the page, after scrolling.)
        """
        w = _current_window_for_event(event)
        b = event.cli.current_buffer

        if w and w.render_info:
            # Scroll down one page.
            w.vertical_scroll = max(0, w.vertical_scroll - w.render_info.rendered_height)

            # Put cursor at the bottom of the visible region.
            try:
                new_document_line = w.render_info.screen_line_to_input_line[
                    w.vertical_scroll + w.render_info.rendered_height - 1]
            except KeyError:
                new_document_line = 0

            b.cursor_position = min(b.cursor_position,
                                    b.document.translate_row_col_to_index(new_document_line, 0))
            b.cursor_position += b.document.get_start_of_line_position(after_whitespace=True)

    @handle(Keys.ControlT)
    def _(event):
        """
        Override default behaviour of prompt-toolkit.
        (Control-T will swap the last two characters before the cursor, because
        that's what readline does.)
        """
        pass

    @handle(Keys.ControlT, filter=in_insert_mode)
    def indent_line(event):
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

    @handle(Keys.ControlR, filter=in_navigation_mode, save_before=False)
    def redo(event):
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
    def autocomplete_or_indent(event):
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

    @handle(Keys.ControlW, 'n', filter=in_navigation_mode)
    def horizontal_split(event):
        """
        Split horizontally.
        """
        editor.window_arrangement.hsplit(None)
        editor.sync_with_prompt_toolkit()

    @handle(Keys.ControlW, 'v', filter=in_navigation_mode)
    def vertical_split(event):
        """
        Split vertically.
        """
        editor.window_arrangement.vsplit(None)
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
    def goto_line_beginning(event):
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
