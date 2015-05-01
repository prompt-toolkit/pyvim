from __future__ import unicode_literals, print_function
import six
import os

__all__ = (
    'has_command_handler',
    'call_command_handler',
)


COMMANDS_TO_HANDLERS = {}  # Global mapping Vi commands to their handler.
COMMANDS_TAKING_LOCATIONS = set()  # Name of commands that accept locations.
SET_COMMANDS = {}  # Mapping ':set'-commands to their handler.
SET_COMMANDS_TAKING_VALUE = set()


_NO_WRITE_SINCE_LAST_CHANGE_TEXT = 'No write since last change (add ! to override)'
_NO_FILE_NAME = 'No file name'


def has_command_handler(command):
    return command in COMMANDS_TO_HANDLERS


def call_command_handler(command, editor, variables):
    """
    Execute command.
    """
    COMMANDS_TO_HANDLERS[command](editor, variables)


def get_commands():
    return COMMANDS_TO_HANDLERS.keys()


def get_commands_taking_locations():
    return COMMANDS_TAKING_LOCATIONS


# Decorators

def _cmd(name):
    """
    Base decorator for registering commands in this namespace.
    """
    def decorator(func):
        COMMANDS_TO_HANDLERS[name] = func
        return func
    return decorator


def location_cmd(name, accepts_force=False):
    """
    Decorator that registers a command that takes a location as (optional)
    parameter.
    """
    COMMANDS_TAKING_LOCATIONS.add(name)

    def decorator(func):
        @_cmd(name)
        def command_wrapper(editor, variables):
            location = variables.get('location')
            force = bool(variables['force'])

            if force and not accepts_force:
                editor.show_message('No ! allowed')
            elif accepts_force:
                func(editor, location, force=force)
            else:
                func(editor, location)
        return func
    return decorator


def cmd(name, accepts_force=False):
    """
    Decarator that registers a command that doesn't take any parameters.
    """
    def decorator(func):
        @_cmd(name)
        def command_wrapper(editor, variables):
            force = bool(variables['force'])

            if force and not accepts_force:
                editor.show_message('No ! allowed')
            elif accepts_force:
                func(editor, force=force)
            else:
                func(editor)
        return func
    return decorator


def set_cmd(name, accepts_value=False):
    """
    Docorator that registers a ':set'-command.
    """
    def decorator(func):
        SET_COMMANDS[name] = func
        if accepts_value:
            SET_COMMANDS_TAKING_VALUE.add(name)
        return func
    return decorator


# Actual command implementations

@_cmd('set')
def _(editor, variables):
    """
    Execute a ':set' command.
    """
    option = variables.get('set_option')
    value = variables.get('set_value')

    if option in SET_COMMANDS:
        # Call the correct handler.
        if option in SET_COMMANDS_TAKING_VALUE:
            SET_COMMANDS[option](editor, value)
        else:
            SET_COMMANDS[option](editor)
    else:
        editor.show_message('Unknown option: %s' % option)


@cmd('bn', accepts_force=True)
def _bn(editor, force=False):
    """
    Go to next buffer.
    """
    eb = editor.window_arrangement.active_editor_buffer

    if not force and eb.has_unsaved_changes:
        editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)
    else:
        editor.window_arrangement.go_to_next_buffer()


@cmd('bp', accepts_force=True)
def _bp(editor, force=False):
    """
    Go to previous buffer.
    """
    eb = editor.window_arrangement.active_editor_buffer

    if not force and eb.has_unsaved_changes:
        editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)
    else:
        editor.window_arrangement.go_to_previous_buffer()


@cmd('only')
def _(editor):
    """
    Keep only the current window.
    """
    editor.window_arrangement.keep_only_current_window()


@cmd('hide')
def _(editor):
    """
    Hide the current window.
    """
    editor.window_arrangement.close_window()


@location_cmd('sp')
@location_cmd('split')
def _(editor, location):
    """
    Split window horizontally.
    """
    editor.window_arrangement.hsplit(location or None)


@location_cmd('vsp')
@location_cmd('vsplit')
def _(editor, location):
    """
    Split window vertically.
    """
    editor.window_arrangement.vsplit(location or None)


@cmd('new')
def _(editor):
    """
    Create new buffer.
    """
    editor.window_arrangement.hsplit(new=True)


@cmd('vnew')
def _(editor):
    """
    Create new buffer, splitting vertically.
    """
    editor.window_arrangement.vsplit(new=True)


@location_cmd('badd')
def _(editor, location):
    """
    Add a new buffer.
    """
    editor.window_arrangement.open_buffer(location)


@cmd('buffers')
def _(editor):
    """
    List all buffers.
    """
    def handler():
        wa = editor.window_arrangement
        for info in wa.list_open_buffers():
            char = '%' if info.is_active else ''
            eb = info.editor_buffer
            print(' %3i %-2s %-20s  line %i' % (
                  info.index, char, eb.location, (eb.buffer.document.cursor_position_row + 1)))
        (input() if six.PY3 else raw_input)('\nPress ENTER to continue...')
    editor.cli.run_in_terminal(handler)


@_cmd('b')
@_cmd('buffer')
def _buffer(editor, variables, force=False):
    """
    Go to one of the open buffers.
    """
    eb = editor.window_arrangement.active_editor_buffer
    force = bool(variables['force'])

    buffer_name = variables.get('buffer_name')
    if buffer_name:
        if not force and eb.has_unsaved_changes:
            editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)
        else:
            editor.window_arrangement.go_to_buffer(buffer_name)


@cmd('bw')
@cmd('bd')
def _(editor):
    """
    Wipe buffer.
    """
    eb = editor.window_arrangement.active_editor_buffer
    if eb.has_unsaved_changes:
        editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)
    else:
        editor.window_arrangement.close_buffer()


@cmd('bw!')
@cmd('bd!')
def _(editor):
    """
    Force wipe buffer.
    """
    editor.window_arrangement.close_buffer()


@location_cmd('o', accepts_force=True)
@location_cmd('open', accepts_force=True)
@location_cmd('e', accepts_force=True)
@location_cmd('edit', accepts_force=True)
def _(editor, location, force=False):
    """
    Edit new buffer.
    """
    if location is None:
        # Edit/open without a location will reload the current file, if there are
        # no changes.
        eb = editor.window_arrangement.active_editor_buffer
        if eb.location is None:
            editor.show_message(_NO_FILE_NAME)
        elif not force and eb.has_unsaved_changes:
            editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)
        else:
            eb.reload()
    else:
        editor.window_arrangement.open_buffer(location, show_in_current_window=True)


@cmd('q', accepts_force=True)
@cmd('quit', accepts_force=True)
def quit(editor, all_=False, force=False):
    """
    Quit.
    """
    ebs = editor.window_arrangement.editor_buffers

    # When there are buffers that have unsaved changes, show balloon.
    if not force and any(eb.has_unsaved_changes for eb in ebs):
        editor.show_message(_NO_WRITE_SINCE_LAST_CHANGE_TEXT)

    # When there is more than one buffer open.
    elif not all_ and len(ebs) > 1:
        editor.show_message('%i more files to edit' % (len(ebs) - 1))

    else:
        editor.cli.set_return_value('')


@cmd('qa', accepts_force=True)
@cmd('qall', accepts_force=True)
def _(editor, force=False):
    """
    Quit all.
    """
    quit(editor, all_=True, force=force)


@location_cmd('w', accepts_force=True)
@location_cmd('write', accepts_force=True)
def write(editor, location, force=False):
    """
    Write file.
    """
    if location and not force and os.path.exists(location):
        editor.show_message('File exists (add ! to overriwe)')
    else:
        eb = editor.window_arrangement.active_editor_buffer
        if location is None and eb.location is None:
            editor.show_message(_NO_FILE_NAME)
        else:
            eb.write(location)


@location_cmd('wq', accepts_force=True)
def _(editor, location, force=False):
    """
    Write file and quit.
    """
    write(editor, location, force=force)
    editor.cli.set_return_value('')


@cmd('wqa')
def _(editor):
    """
    Write current buffer and quit all.
    """
    eb = editor.window_arrangement.active_editor_buffer
    if eb.location is None:
        editor.show_message(_NO_FILE_NAME)
    else:
        eb.write()
        quit(editor, all_=True, force=False)


@cmd('h')
@cmd('help')
def _(editor):
    """
    Show help.
    """
    editor.show_help()


@location_cmd('tabnew')
def _(editor, location):
    """
    Create new tab page.
    """
    editor.window_arrangement.create_tab(location or None)


@cmd('tabclose')
def _(editor):
    """
    Close tab page.
    """
    editor.window_arrangement.close_tab()


@cmd('tabnext')
def _(editor):
    """
    Go to next tab.
    """
    editor.window_arrangement.go_to_next_tab()


@cmd('tabprevious')
def _(editor):
    """
    Go to previous tab.
    """
    editor.window_arrangement.go_to_previous_tab()


@_cmd('colorscheme')
def _(editor, variables):
    """
    Go to one of the open buffers.
    """
    colorscheme = variables.get('colorscheme')
    if colorscheme:
        editor.use_colorscheme(colorscheme)


@set_cmd('nu')
@set_cmd('number')
def _(editor):
    """ Show line numbers.  """
    editor.show_line_numbers = True


@set_cmd('nonu')
@set_cmd('nonumber')
def _(editor):
    """ Hide line numbers. """
    editor.show_line_numbers = False


@set_cmd('hlsearch')
def _(editor):
    """ Highlight search matches. """
    editor.highlight_search = True


@set_cmd('nohlsearch')
def _(editor):
    """ Don't highlight search matches. """
    editor.highlight_search = False


@set_cmd('paste')
def _(editor):
    """ Enter paste mode. """
    editor.paste_mode = True


@set_cmd('nopaste')
def _(editor):
    """ Leave paste mode. """
    editor.paste_mode = False


@set_cmd('ruler')
def _(editor):
    """ Show ruler. """
    editor.show_ruler = True


@set_cmd('noruler')
def _(editor):
    """ Hide ruler. """
    editor.show_ruler = False


@set_cmd('wildmenu')
@set_cmd('wmnu')
def _(editor):
    """ Show wildmenu. """
    editor.show_wildmenu = True


@set_cmd('nowildmenu')
@set_cmd('nowmnu')
def _(editor):
    """ Hide wildmenu. """
    editor.show_wildmenu = False


@set_cmd('expandtab')
@set_cmd('et')
def _(editor):
    """ Enable tab expension. """
    editor.expand_tab = True


@set_cmd('noexpandtab')
@set_cmd('noet')
def _(editor):
    """ Disable tab expension. """
    editor.expand_tab = False


@set_cmd('tabstop', accepts_value=True)
@set_cmd('ts', accepts_value=True)
def _(editor, value):
    """
    Set tabstop.
    """
    if value is None:
        editor.show_message('tabstop=%i' % editor.tabstop)
    else:
        try:
            value = int(value)
            if value > 0:
                editor.tabstop = value
            else:
                editor.show_message('Argument must be positive')
        except ValueError:
            editor.show_message('Number required after =')


@set_cmd('scrolloff', accepts_value=True)
@set_cmd('so', accepts_value=True)
def _(editor, value):
    """
    Set scroll offset.
    """
    if value is None:
        editor.show_message('scrolloff=%i' % editor.scroll_offset)
    else:
        try:
            value = int(value)
            if value >= 0:
                editor.scroll_offset = value
            else:
                editor.show_message('Argument must be positive')
        except ValueError:
            editor.show_message('Number required after =')


@set_cmd('incsearch')
def _(editor):
    """ Enable incsearch. """
    editor.incsearch = True


@set_cmd('noincsearch')
def _(editor):
    """ Disable incsearch. """
    editor.incsearch = False


@set_cmd('ignorecase')
def _(editor):
    """ Enable case insensitive searching. """
    editor.ignore_case = True


@set_cmd('noignorecase')
def _(editor):
    """ Disable case insensitive searching. """
    editor.ignore_case = False


@set_cmd('list')
def _(editor):
    """ Display unprintable characters. """
    editor.display_unprintable_characters = True


@set_cmd('nolist')
def _(editor):
    """ Hide unprintable characters. """
    editor.display_unprintable_characters = False


@set_cmd('jedi')
def _(editor):
    """ Enable Jedi autocompletion for Python files. """
    editor.enable_jedi = True


@set_cmd('nojedi')
def _(editor):
    """ Disable Jedi autocompletion. """
    editor.enable_jedi = False
