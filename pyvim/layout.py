"""
The actual layout for the renderer.
"""
from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import has_focus, is_searching, Condition, has_arg
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout import HSplit, VSplit, FloatContainer, Float, Layout
from prompt_toolkit.layout.containers import Window, ConditionalContainer, ColorColumn, WindowAlign, ScrollOffsets
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import Processor, ConditionalProcessor, BeforeInput, ShowTrailingWhiteSpaceProcessor, Transformation, HighlightSelectionProcessor, HighlightSearchProcessor, HighlightIncrementalSearchProcessor, HighlightMatchingBracketProcessor, TabsProcessor, DisplayMultipleCursors
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.widgets.toolbars import FormattedTextToolbar, SystemToolbar, SearchToolbar, ValidationToolbar, CompletionsToolbar

from .commands.lexer import create_command_lexer
from .lexer import DocumentLexer
from .welcome_message import WELCOME_MESSAGE_TOKENS, WELCOME_MESSAGE_HEIGHT, WELCOME_MESSAGE_WIDTH

import pyvim.window_arrangement as window_arrangement
from functools import partial

import re
import sys

__all__ = (
    'EditorLayout',
    'get_terminal_title',
)

def _try_char(character, backup, encoding=sys.stdout.encoding):
    """
    Return `character` if it can be encoded using sys.stdout, else return the
    backup character.
    """
    if character.encode(encoding, 'replace') == b'?':
        return backup
    else:
        return character


TABSTOP_DOT = _try_char('\u2508', '.')


class TabsControl(FormattedTextControl):
    """
    Displays the tabs at the top of the screen, when there is more than one
    open tab.
    """
    def __init__(self, editor):
        def location_for_tab(tab):
            return tab.active_window.editor_buffer.get_display_name(short=True)

        def create_tab_handler(index):
            " Return a mouse handler for this tab. Select the tab on click. "
            def handler(app, mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                    editor.window_arrangement.active_tab_index = index
                    editor.sync_with_prompt_toolkit()
                else:
                    return NotImplemented
            return handler

        def get_tokens():
            selected_tab_index = editor.window_arrangement.active_tab_index

            result = []
            append = result.append

            for i, tab in enumerate(editor.window_arrangement.tab_pages):
                caption = location_for_tab(tab)
                if tab.has_unsaved_changes:
                    caption = ' + ' + caption

                handler = create_tab_handler(i)

                if i == selected_tab_index:
                    append(('class:tabbar.tab.active', ' %s ' % caption, handler))
                else:
                    append(('class:tabbar.tab', ' %s ' % caption, handler))
                append(('class:tabbar', ' '))

            return result

        super(TabsControl, self).__init__(get_tokens, style='class:tabbar')


class TabsToolbar(ConditionalContainer):
    def __init__(self, editor):
        super(TabsToolbar, self).__init__(
            Window(TabsControl(editor), height=1),
            filter=Condition(lambda: len(editor.window_arrangement.tab_pages) > 1))


class CommandLine(ConditionalContainer):
    """
    The editor command line. (For at the bottom of the screen.)
    """
    def __init__(self, editor):
        super(CommandLine, self).__init__(
            Window(
                BufferControl(
                    buffer=editor.command_buffer,
                    input_processors=[BeforeInput(':')],
                    lexer=create_command_lexer()),
                height=1),
            filter=has_focus(editor.command_buffer))


class WelcomeMessageWindow(ConditionalContainer):
    """
    Welcome message pop-up, which is shown during start-up when no other files
    were opened.
    """
    def __init__(self, editor):
        once_hidden = [False]  # Nonlocal

        def condition():
            # Get editor buffers
            buffers = editor.window_arrangement.editor_buffers

            # Only show when there is only one empty buffer, but once the
            # welcome message has been hidden, don't show it again.
            result = (len(buffers) == 1 and buffers[0].buffer.text == '' and
                      buffers[0].location is None and not once_hidden[0])
            if not result:
                once_hidden[0] = True
            return result

        super(WelcomeMessageWindow, self).__init__(
            Window(
                FormattedTextControl(lambda: WELCOME_MESSAGE_TOKENS),
                align=WindowAlign.CENTER,
                style="class:welcome"),
            filter=Condition(condition))


def _bufferlist_overlay_visible(editor):
    """
    True when the buffer list overlay should be displayed.
    (This is when someone starts typing ':b' or ':buffer' in the command line.)
    """
    @Condition
    def overlay_is_visible():
        app = get_app()

        text = editor.command_buffer.text.lstrip()
        return app.layout.has_focus(editor.command_buffer) and (
                any(text.startswith(p) for p in ['b ', 'b! ', 'buffer', 'buffer!']))
    return overlay_is_visible


class BufferListOverlay(ConditionalContainer):
    """
    Floating window that shows the list of buffers when we are typing ':b'
    inside the vim command line.
    """
    def __init__(self, editor):
        def highlight_location(location, search_string, default_token):
            """
            Return a tokenlist with the `search_string` highlighted.
            """
            result = [(default_token, c) for c in location]

            # Replace token of matching positions.
            for m in re.finditer(re.escape(search_string), location):
                for i in range(m.start(), m.end()):
                    result[i] = ('class:searchmatch', result[i][1])

            if location == search_string:
                result[0] = (result[0][0] + ' [SetCursorPosition]', result[0][1])

            return result

        def get_tokens():
            wa = editor.window_arrangement
            buffer_infos = wa.list_open_buffers()

            # Filter infos according to typed text.
            input_params = editor.command_buffer.text.lstrip().split(None, 1)
            search_string = input_params[1] if len(input_params) > 1 else ''

            if search_string:
                def matches(info):
                    """
                    True when we should show this entry.
                    """
                    # When the input appears in the location.
                    if input_params[1] in (info.editor_buffer.location or ''):
                        return True

                    # When the input matches this buffer his index number.
                    if input_params[1] in str(info.index):
                        return True

                    # When this entry is part of the current completions list.
                    b = editor.command_buffer

                    if b.complete_state and any(info.editor_buffer.location in c.display
                                                for c in b.complete_state.completions
                                                if info.editor_buffer.location is not None):
                        return True

                    return False

                buffer_infos = [info for info in buffer_infos if matches(info)]

            # Render output.
            if len(buffer_infos) == 0:
                return [('', ' No match found. ')]
            else:
                result = []

                # Create title.
                result.append(('', '  '))
                result.append(('class:title', 'Open buffers\n'))

                # Get length of longest location
                max_location_len = max(len(info.editor_buffer.get_display_name()) for info in buffer_infos)

                # Show info for each buffer.
                for info in buffer_infos:
                    eb = info.editor_buffer
                    char = '%' if info.is_active else ' '
                    char2 = 'a' if info.is_visible else ' '
                    char3 = ' + ' if info.editor_buffer.has_unsaved_changes else '   '
                    t = 'class:active' if info.is_active else ''

                    result.extend([
                        ('', ' '),
                        (t, '%3i ' % info.index),
                        (t, '%s' % char),
                        (t, '%s ' % char2),
                        (t, '%s ' % char3),
                    ])
                    result.extend(highlight_location(eb.get_display_name(), search_string, t))
                    result.extend([
                        (t, ' ' * (max_location_len - len(eb.get_display_name()))),
                        (t + ' class:lineno', '  line %i' % (eb.buffer.document.cursor_position_row + 1)),
                        (t, ' \n')
                    ])
                return result

        super(BufferListOverlay, self).__init__(
            Window(FormattedTextControl(get_tokens),
                   style='class:bufferlist',
                   scroll_offsets=ScrollOffsets(top=1, bottom=1)),
            filter=_bufferlist_overlay_visible(editor))


class MessageToolbarBar(ConditionalContainer):
    """
    Pop-up (at the bottom) for showing error/status messages.
    """
    def __init__(self, editor):
        def get_tokens():
            if editor.message:
                return [('class:message', editor.message)]
            else:
                return []

        super(MessageToolbarBar, self).__init__(
            FormattedTextToolbar(get_tokens),
            filter=Condition(lambda: editor.message is not None))


class ReportMessageToolbar(ConditionalContainer):
    """
    Toolbar that shows the messages, given by the reporter.
    (It shows the error message, related to the current line.)
    """
    def __init__(self, editor):
        def get_formatted_text():
            eb = editor.window_arrangement.active_editor_buffer

            lineno = eb.buffer.document.cursor_position_row
            errors = eb.report_errors

            for e in errors:
                if e.lineno == lineno:
                    return e.formatted_text

            return []

        super(ReportMessageToolbar, self).__init__(
                FormattedTextToolbar(get_formatted_text),
                filter=~has_focus(editor.command_buffer) & ~is_searching & ~has_focus('system'))


class WindowStatusBar(FormattedTextToolbar):
    """
    The status bar, which is shown below each window in a tab page.
    """
    def __init__(self, editor, editor_buffer):
        def get_text():
            app = get_app()

            insert_mode = app.vi_state.input_mode in (InputMode.INSERT, InputMode.INSERT_MULTIPLE)
            replace_mode = app.vi_state.input_mode == InputMode.REPLACE
            sel = editor_buffer.buffer.selection_state
            temp_navigation = app.vi_state.temporary_navigation_mode
            visual_line = sel is not None and sel.type == SelectionType.LINES
            visual_block = sel is not None and sel.type == SelectionType.BLOCK
            visual_char = sel is not None and sel.type == SelectionType.CHARACTERS

            def mode():
                if get_app().layout.has_focus(editor_buffer.buffer):
                    if insert_mode:
                        if temp_navigation:
                            return ' -- (insert) --'
                        elif editor.paste_mode:
                            return ' -- INSERT (paste)--'
                        else:
                            return ' -- INSERT --'
                    elif replace_mode:
                        if temp_navigation:
                            return ' -- (replace) --'
                        else:
                            return ' -- REPLACE --'
                    elif visual_block:
                        return ' -- VISUAL BLOCK --'
                    elif visual_line:
                        return ' -- VISUAL LINE --'
                    elif visual_char:
                        return ' -- VISUAL --'
                return '                     '

            def recording():
                if app.vi_state.recording_register:
                    return 'recording '
                else:
                    return ''

            return ''.join([
                ' ',
                recording(),
                (editor_buffer.location or ''),
                (' [New File]' if editor_buffer.is_new else ''),
                ('*' if editor_buffer.has_unsaved_changes else ''),
                (' '),
                mode(),
            ])
        super(WindowStatusBar, self).__init__(
            get_text,
            style='class:toolbar.status')


class WindowStatusBarRuler(ConditionalContainer):
    """
    The right side of the Vim toolbar, showing the location of the cursor in
    the file, and the vectical scroll percentage.
    """
    def __init__(self, editor, buffer_window, buffer):
        def get_scroll_text():
            info = buffer_window.render_info

            if info:
                if info.full_height_visible:
                    return 'All'
                elif info.top_visible:
                    return 'Top'
                elif info.bottom_visible:
                    return 'Bot'
                else:
                    percentage = info.vertical_scroll_percentage
                    return '%2i%%' % percentage

            return ''

        def get_tokens():
            main_document = buffer.document

            return [
                ('class:cursorposition', '(%i,%i)' % (main_document.cursor_position_row + 1,
                                                      main_document.cursor_position_col + 1)),
                ('', ' - '),
                ('class:percentage', get_scroll_text()),
                ('', ' '),
            ]

        super(WindowStatusBarRuler, self).__init__(
            Window(
                FormattedTextControl(get_tokens),
                char=' ',
                align=WindowAlign.RIGHT,
                style='class:toolbar.status',
                height=1,
            ),
            filter=Condition(lambda: editor.show_ruler))


class SimpleArgToolbar(ConditionalContainer):
    """
    Simple control showing the Vi repeat arg.
    """
    def __init__(self):
        def get_tokens():
            arg = get_app().key_processor.arg
            if arg is not None:
                return [('class:arg', ' %s ' % arg)]
            else:
                return []

        super(SimpleArgToolbar, self).__init__(
            Window(FormattedTextControl(get_tokens), align=WindowAlign.RIGHT),
            filter=has_arg),


class PyvimScrollOffsets(ScrollOffsets):
    def __init__(self, editor):
        self.editor = editor
        self.left = 0
        self.right = 0

    @property
    def top(self):
        return self.editor.scroll_offset

    @property
    def bottom(self):
        return self.editor.scroll_offset


class EditorLayout(object):
    """
    The main layout class.
    """
    def __init__(self, editor, window_arrangement):
        self.editor = editor  # Back reference to editor.
        self.window_arrangement = window_arrangement

        # Mapping from (`window_arrangement.Window`, `EditorBuffer`) to a frame
        # (Layout instance).
        # We keep this as a cache in order to easily reuse the same frames when
        # the layout is updated. (We don't want to create new frames on every
        # update call, because that way, we would loose some state, like the
        # vertical scroll offset.)
        self._frames = {}

        self._fc = FloatContainer(
            content=VSplit([
                Window(BufferControl())  # Dummy window
            ]),
            floats=[
                Float(xcursor=True, ycursor=True,
                      content=CompletionsMenu(max_height=12,
                                              scroll_offset=2,
                                              extra_filter=~has_focus(editor.command_buffer))),
                Float(content=BufferListOverlay(editor), bottom=1, left=0),
                Float(bottom=1, left=0, right=0, height=1,
                      content=ConditionalContainer(
                          CompletionsToolbar(),
                          filter=has_focus(editor.command_buffer) &
                                       ~_bufferlist_overlay_visible(editor) &
                                       Condition(lambda: editor.show_wildmenu))),
                Float(bottom=1, left=0, right=0, height=1,
                      content=ValidationToolbar()),
                Float(bottom=1, left=0, right=0, height=1,
                      content=MessageToolbarBar(editor)),
                Float(content=WelcomeMessageWindow(editor),
                      height=WELCOME_MESSAGE_HEIGHT,
                      width=WELCOME_MESSAGE_WIDTH),
            ]
        )

        search_toolbar = SearchToolbar(vi_mode=True, search_buffer=editor.search_buffer)
        self.search_control = search_toolbar.control

        self.layout = Layout(FloatContainer(
            content=HSplit([
                TabsToolbar(editor),
                self._fc,
                CommandLine(editor),
                ReportMessageToolbar(editor),
                SystemToolbar(),
                search_toolbar,
            ]),
            floats=[
                Float(right=0, height=1, bottom=0, width=5,
                      content=SimpleArgToolbar()),
            ]
        ))

    def get_vertical_border_char(self):
        " Return the character to be used for the vertical border. "
        return _try_char('\u2502', '|', get_app().output.encoding())

    def update(self):
        """
        Update layout to match the layout as described in the
        WindowArrangement.
        """
        # Start with an empty frames list everytime, to avoid memory leaks.
        existing_frames = self._frames
        self._frames = {}

        def create_layout_from_node(node):
            if isinstance(node, window_arrangement.Window):
                # Create frame for Window, or reuse it, if we had one already.
                key = (node, node.editor_buffer)
                frame = existing_frames.get(key)
                if frame is None:
                    frame, pt_window = self._create_window_frame(node.editor_buffer)

                    # Link layout Window to arrangement.
                    node.pt_window = pt_window

                self._frames[key] = frame
                return frame

            elif isinstance(node, window_arrangement.VSplit):
                return VSplit(
                    [create_layout_from_node(n) for n in node],
                    padding=1,
                    padding_char=self.get_vertical_border_char(),
                    padding_style='class:frameborder')

            if isinstance(node, window_arrangement.HSplit):
                return HSplit([create_layout_from_node(n) for n in node])

        layout = create_layout_from_node(self.window_arrangement.active_tab.root)
        self._fc.content = layout

    def _create_window_frame(self, editor_buffer):
        """
        Create a Window for the buffer, with underneat a status bar.
        """
        @Condition
        def wrap_lines():
            return self.editor.wrap_lines

        window = Window(
            self._create_buffer_control(editor_buffer),
            allow_scroll_beyond_bottom=True,
            scroll_offsets=ScrollOffsets(
                left=0, right=0,
                top=(lambda: self.editor.scroll_offset),
                bottom=(lambda: self.editor.scroll_offset)),
            wrap_lines=wrap_lines,
            left_margins=[ConditionalMargin(
                    margin=NumberedMargin(
                        display_tildes=True,
                        relative=Condition(lambda: self.editor.relative_number)),
                    filter=Condition(lambda: self.editor.show_line_numbers))],
            cursorline=Condition(lambda: self.editor.cursorline),
            cursorcolumn=Condition(lambda: self.editor.cursorcolumn),
            colorcolumns=(
                lambda: [ColorColumn(pos) for pos in self.editor.colorcolumn]),
            ignore_content_width=True,
            ignore_content_height=True,
            get_line_prefix=partial(self._get_line_prefix, editor_buffer.buffer))

        return HSplit([
            window,
            VSplit([
                WindowStatusBar(self.editor, editor_buffer),
                WindowStatusBarRuler(self.editor, window, editor_buffer.buffer),
            ], width=Dimension()),  # Ignore actual status bar width.
        ]), window

    def _create_buffer_control(self, editor_buffer):
        """
        Create a new BufferControl for a given location.
        """
        @Condition
        def preview_search():
            return self.editor.incsearch

        input_processors = [
            # Processor for visualising spaces. (should come before the
            # selection processor, otherwise, we won't see these spaces
            # selected.)
            ConditionalProcessor(
                ShowTrailingWhiteSpaceProcessor(),
                Condition(lambda: self.editor.display_unprintable_characters)),

            # Replace tabs by spaces.
            TabsProcessor(
                tabstop=(lambda: self.editor.tabstop),
                char1=(lambda: '|' if self.editor.display_unprintable_characters else ' '),
                char2=(lambda: _try_char('\u2508', '.', get_app().output.encoding())
                                       if self.editor.display_unprintable_characters else ' '),
            ),

            # Reporting of errors, for Pyflakes.
            ReportingProcessor(editor_buffer),
            HighlightSelectionProcessor(),
            ConditionalProcessor(
                HighlightSearchProcessor(),
                Condition(lambda: self.editor.highlight_search)),
            ConditionalProcessor(
                HighlightIncrementalSearchProcessor(),
                Condition(lambda: self.editor.highlight_search) & preview_search),
            HighlightMatchingBracketProcessor(),
            DisplayMultipleCursors(),
        ]

        return BufferControl(
            lexer=DocumentLexer(editor_buffer),
            include_default_input_processors=False,
            input_processors=input_processors,
            buffer=editor_buffer.buffer,
            preview_search=preview_search,
            search_buffer_control=self.search_control,
            focus_on_click=True)

    def _get_line_prefix(self, buffer, line_number, wrap_count):
        if wrap_count > 0:
            result = []

            # Add 'breakindent' prefix.
            if self.editor.break_indent:
                line = buffer.document.lines[line_number]
                prefix = line[:len(line) - len(line.lstrip())]
                result.append(('', prefix))

            # Add softwrap mark.
            result.append(('class:soft-wrap', '...'))
            return result
        return ''

class ReportingProcessor(Processor):
    """
    Highlight all pyflakes errors on the input.
    """
    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def apply_transformation(self, transformation_input): 
        fragments = transformation_input.fragments

        if self.editor_buffer.report_errors:
            for error in self.editor_buffer.report_errors:
                if error.lineno == transformation_input.lineno:
                    fragments = explode_text_fragments(fragments)
                    for i in range(error.start_column, error.end_column):
                        if i < len(fragments):
                            fragments[i] = ('class:flakeserror', fragments[i][1])

        return Transformation(fragments)



def get_terminal_title(editor):
    """
    Return the terminal title,
    e.g.: "filename.py (/directory) - Pyvim"
    """
    eb = editor.current_editor_buffer
    if eb is not None:
        return '%s - Pyvim' % (eb.location or '[New file]', )
    else:
        return 'Pyvim'
