"""
The main editor class.

Usage::

    files_to_edit = ['file1.txt', 'file2.py']
    e = Editor(files_to_edit)
    e.run()  # Runs the event loop, starts interaction.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer, AcceptAction
from prompt_toolkit.enums import SEARCH_BUFFER, EditingMode
from prompt_toolkit.filters import Always, Condition
from prompt_toolkit.history import FileHistory
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.styles import DynamicStyle

from .commands.completer import create_command_completer
from .commands.handler import handle_command
from .commands.preview import CommandPreviewer
from .editor_buffer import EditorBuffer
from .enums import COMMAND_BUFFER
from .help import HELP_TEXT
from .key_bindings import create_key_bindings
from .layout import EditorLayout, get_terminal_title
from .reporting import report
from .style import generate_built_in_styles, get_editor_style_by_name
from .window_arrangement import WindowArrangement
from .io import FileIO, DirectoryIO, HttpIO, GZipFileIO

import pygments
import os

__all__ = (
    'Editor',
)


class Editor(object):
    """
    The main class. Containing the whole editor.
    """
    def __init__(self, config_directory='~/.pyvim'):
        # Vi options.
        self.show_line_numbers = True
        self.highlight_search = True
        self.paste_mode = False
        self.show_ruler = True
        self.show_wildmenu = True
        self.expand_tab = True  # Insect spaces instead of tab characters.
        self.tabstop = 4  # Number of spaces that a tab character represents.
        self.incsearch = True  # Show matches while typing search string.
        self.ignore_case = False  # Ignore case while searching.
        self.enable_mouse_support = True
        self.display_unprintable_characters = True  # ':set list'
        self.enable_jedi = True  # ':set jedi', for Python Jedi completion.
        self.scroll_offset = 0  # ':set scrolloff'
        self.relative_number = False  # ':set relativenumber'
        self.wrap_lines = True  # ':set wrap'
        self.cursorline = False  # ':set cursorline'
        self.cursorcolumn = False  # ':set cursorcolumn'
        self.colorcolumn = []  # ':set colorcolumn'. List of integers.

        # Ensure config directory exists.
        self.config_directory = os.path.abspath(os.path.expanduser(config_directory))
        if not os.path.exists(self.config_directory):
            os.mkdir(self.config_directory)

        self._reporters_running_for_buffer_names = set()
        self.window_arrangement = WindowArrangement(self)
        self.message = None

        # Load styles. (Mapping from name to Style class.)
        self.styles = generate_built_in_styles()
        self.current_style = get_editor_style_by_name('default')

        # I/O backends.
        self.io_backends = [
            DirectoryIO(),
            HttpIO(),
            GZipFileIO(),  # Should come before FileIO.
            FileIO(),
        ]

        # Create eventloop.
        self.eventloop = create_eventloop()

        # Create key bindings manager
        self.key_bindings_manager = create_key_bindings(self)

        # Create layout and CommandLineInterface instance.
        self.editor_layout = EditorLayout(
            self, self.key_bindings_manager, self.window_arrangement)
        self.application = self._create_application()

        self.cli = CommandLineInterface(
            eventloop=self.eventloop,
            application=self.application)

        # Hide message when a key is pressed.
        def key_pressed(_):
            self.message = None
        self.cli.input_processor.beforeKeyPress += key_pressed

        # Command line previewer.
        self.previewer = CommandPreviewer(self)

    def load_initial_files(self, locations, in_tab_pages=False, hsplit=False, vsplit=False):
        """
        Load a list of files.
        """
        assert in_tab_pages + hsplit + vsplit <= 1  # Max one of these options.

        # When no files were given, open at least one empty buffer.
        locations2 = locations or [None]

        # First file
        self.window_arrangement.open_buffer(locations2[0])

        for f in locations2[1:]:
            if in_tab_pages:
                self.window_arrangement.create_tab(f)
            elif hsplit:
                self.window_arrangement.hsplit(location=f)
            elif vsplit:
                self.window_arrangement.vsplit(location=f)
            else:
                self.window_arrangement.open_buffer(f)

        self.window_arrangement.active_tab_index = 0

        if locations and len(locations) > 1:
            self.show_message('%i files loaded.' % len(locations))

    def _create_application(self):
        """
        Create CommandLineInterface instance.
        """
        # Create Vi command buffer.
        def handle_action(cli, buffer):
            ' When enter is pressed in the Vi command line. '
            text = buffer.text  # Remember: leave_command_mode resets the buffer.

            # First leave command mode. We want to make sure that the working
            # pane is focussed again before executing the command handlers.
            self.leave_command_mode(append_to_history=True)

            # Execute command.
            handle_command(self, text)

        # Create history and search buffers.
        commands_history = FileHistory(os.path.join(self.config_directory, 'commands_history'))
        command_buffer = Buffer(accept_action=AcceptAction(handler=handle_action),
                                enable_history_search=Always(),
                                completer=create_command_completer(self),
                                history=commands_history)

        search_buffer_history = FileHistory(os.path.join(self.config_directory, 'search_history'))
        search_buffer = Buffer(history=search_buffer_history,
                               enable_history_search=Always(),
                               accept_action=AcceptAction.IGNORE)

        # Create app.

        # Create CLI.
        application = Application(
            editing_mode=EditingMode.VI,
            layout=self.editor_layout.layout,
            key_bindings_registry=self.key_bindings_manager.registry,
            get_title=lambda: get_terminal_title(self),
            buffers={
                COMMAND_BUFFER: command_buffer,
                SEARCH_BUFFER: search_buffer,
            },
            style=DynamicStyle(lambda: self.current_style),
            paste_mode=Condition(lambda cli: self.paste_mode),
            ignore_case=Condition(lambda cli: self.ignore_case),
            mouse_support=Condition(lambda cli: self.enable_mouse_support),
            use_alternate_screen=True,
            on_buffer_changed=self._current_buffer_changed)

        # Handle command line previews.
        # (e.g. when typing ':colorscheme blue', it should already show the
        # preview before pressing enter.)
        def preview(_):
            if self.cli.current_buffer == command_buffer:
                self.previewer.preview(command_buffer.text)
        command_buffer.on_text_changed += preview

        return application

    @property
    def current_editor_buffer(self):
        """
        Return the `EditorBuffer` that is currently active.
        """
        # For each buffer name on the focus stack.
        for current_buffer_name in self.cli.buffers.focus_stack:
            if current_buffer_name is not None:
                # Find/return the EditorBuffer with this name.
                for b in self.window_arrangement.editor_buffers:
                    if b.buffer_name == current_buffer_name:
                        return b

    @property
    def add_key_binding(self):
        """
        Shortcut for adding new key bindings.
        (Mostly useful for a pyvimrc file, that receives this Editor instance
        as input.)
        """
        return self.key_bindings_manager.registry.add_binding

    def show_message(self, message):
        """
        Set a warning message. The layout will render it as a "pop-up" at the
        bottom.
        """
        self.message = message

    def use_colorscheme(self, name='default'):
        """
        Apply new colorscheme. (By name.)
        """
        try:
            self.current_style = get_editor_style_by_name(name)
        except pygments.util.ClassNotFound:
            pass

    def sync_with_prompt_toolkit(self):
        """
        Update the prompt-toolkit Layout and FocusStack.
        """
        # After executing a command, make sure that the layout of
        # prompt-toolkit matches our WindowArrangement.
        self.editor_layout.update()

        # Make sure that the focus stack of prompt-toolkit has the current
        # page.
        self.cli.focus(
            self.window_arrangement.active_editor_buffer.buffer_name)

    def _current_buffer_changed(self, cli):
        """
        Current buffer changed.
        """
        name = self.cli.current_buffer_name
        eb = self.window_arrangement.get_editor_buffer_for_buffer_name(name)

        if eb is not None:
            # Run reporter.
            self.run_reporter_for_editor_buffer(eb)

    def run_reporter_for_editor_buffer(self, editor_buffer):
        """
        Run reporter on input. (Asynchronously.)
        """
        assert isinstance(editor_buffer, EditorBuffer)
        eb = editor_buffer
        name = eb.buffer_name

        if name not in self._reporters_running_for_buffer_names:
            text = eb.buffer.text
            self._reporters_running_for_buffer_names.add(name)
            eb.report_errors = []

            # Don't run reporter when we don't have a location. (We need to
            # know the filetype, actually.)
            if eb.location is None:
                return

            # Better not to access the document in an executor.
            document = eb.buffer.document

            def in_executor():
                # Call reporter
                report_errors = report(eb.location, document)

                def ready():
                    self._reporters_running_for_buffer_names.remove(name)

                    # If the text has not been changed yet in the meantime, set
                    # reporter errors. (We were running in another thread.)
                    if text == eb.buffer.text:
                        eb.report_errors = report_errors
                        self.cli.invalidate()
                    else:
                        # Restart reporter when the text was changed.
                        self._current_buffer_changed(self.cli)

                self.cli.eventloop.call_from_executor(ready)
            self.cli.eventloop.run_in_executor(in_executor)

    def show_help(self):
        """
        Show help in new window.
        """
        self.window_arrangement.hsplit(text=HELP_TEXT)
        self.sync_with_prompt_toolkit()  # Show new window.

    def run(self):
        """
        Run the event loop for the interface.
        This starts the interaction.
        """
        # Make sure everything is in sync, before starting.
        self.sync_with_prompt_toolkit()

        def pre_run():
            # Start in navigation mode.
            self.cli.vi_state.input_mode = InputMode.NAVIGATION

        # Run eventloop of prompt_toolkit.
        self.cli.run(reset_current_buffer=False, pre_run=pre_run)

    def enter_command_mode(self):
        """
        Go into command mode.
        """
        self.cli.push_focus(COMMAND_BUFFER)
        self.cli.vi_state.input_mode = InputMode.INSERT

        self.previewer.save()

    def leave_command_mode(self, append_to_history=False):
        """
        Leave command mode. Focus document window again.
        """
        self.previewer.restore()

        self.cli.pop_focus()
        self.cli.vi_state.input_mode = InputMode.NAVIGATION

        self.cli.buffers[COMMAND_BUFFER].reset(append_to_history=append_to_history)
