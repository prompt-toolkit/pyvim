from __future__ import unicode_literals

from .grammar import COMMAND_GRAMMAR
from .commands import call_command_handler, has_command_handler

__all__ = (
    'handle_command',
)


def handle_command(editor, input_string):
    """
    Handle commands entered on the Vi command line.
    """
    # Match with grammar and extract variables.
    m = COMMAND_GRAMMAR.match(input_string)
    if m is None:
        return

    variables = m.variables()
    command = variables.get('command')
    go_to_line = variables.get('go_to_line')
    shell_command = variables.get('shell_command')

    # Call command handler.

    if go_to_line is not None:
        # Handle go-to-line.
        _go_to_line(editor, go_to_line)

    elif shell_command is not None:
        # Handle shell commands.
        editor.cli.run_system_command(shell_command)

    elif has_command_handler(command):
        # Handle other 'normal' commands.
        call_command_handler(command, editor, variables)
    else:
        # For unknown commands, show error message.
        editor.show_message('Not an editor command: %s' % input_string)
        return

    # After execution of commands, make sure to update the layout and focus
    # stack.
    editor.sync_with_prompt_toolkit()


def _go_to_line(editor, line):
    """
    Move cursor to this line in the current buffer.
    """
    b = editor.cli.current_buffer
    b.cursor_position = b.document.translate_row_col_to_index(max(0, int(line) - 1), 0)
