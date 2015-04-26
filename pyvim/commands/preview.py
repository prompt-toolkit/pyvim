from __future__ import unicode_literals
from .grammar import COMMAND_GRAMMAR

__all__ = (
    'CommandPreviewer',
)


class CommandPreviewer(object):
    """
    Already show the effect of Vi commands before enter is pressed.
    """
    def __init__(self, editor):
        self.editor = editor

    def save(self):
        """
        Back up current editor state.
        """
        e = self.editor

        self._style = e.cli.style
        self._show_line_numbers = e.show_line_numbers
        self._highlight_search = e.highlight_search
        self._show_ruler = e.show_ruler

    def restore(self):
        """
        Focus of Vi command line lost, undo preview.
        """
        e = self.editor

        e.cli.style = self._style
        e.show_line_numbers = self._show_line_numbers
        e.highlight_search = self._highlight_search
        e.show_ruler = self._show_ruler

    def preview(self, input_string):
        """
        Show effect of current Vi command.
        """
        # First, the apply.
        self.restore()
        self._apply(input_string)

    def _apply(self, input_string):
        """ Apply command. """
        e = self.editor

        # Parse command.
        m = COMMAND_GRAMMAR.match(input_string)
        if m is None:
            return

        variables = m.variables()

        command = variables.get('command')
        set_option = variables.get('set_option')

        # Preview colorschemes.
        if command == 'colorscheme':
            colorscheme = variables.get('colorscheme')
            if colorscheme:
                e.use_colorscheme(colorscheme)

        # Preview some set commands.
        if command == 'set':
            if set_option == 'hlsearch':
                e.highlight_search = True
            elif set_option == 'nohlsearch':
                e.highlight_search = False
            elif set_option in ('nu', 'number'):
                e.show_line_numbers = True
            elif set_option in ('nonu', 'nonumber'):
                e.show_line_numbers = False
            elif set_option == 'ruler':
                e.show_ruler = True
            elif set_option == 'noruler':
                e.show_ruler = False
