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

        self._style = e.current_style
        self._show_line_numbers = e.show_line_numbers
        self._highlight_search = e.highlight_search
        self._show_ruler = e.show_ruler
        self._relative_number = e.relative_number
        self._cursorcolumn = e.cursorcolumn
        self._cursorline = e.cursorline
        self._colorcolumn = e.colorcolumn

    def restore(self):
        """
        Focus of Vi command line lost, undo preview.
        """
        e = self.editor

        e.current_style = self._style
        e.show_line_numbers = self._show_line_numbers
        e.highlight_search = self._highlight_search
        e.show_ruler = self._show_ruler
        e.relative_number = self._relative_number
        e.cursorcolumn = self._cursorcolumn
        e.cursorline = self._cursorline
        e.colorcolumn = self._colorcolumn

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
            if set_option in ('hlsearch', 'hls'):
                e.highlight_search = True
            elif set_option in ('nohlsearch', 'nohls'):
                e.highlight_search = False
            elif set_option in ('nu', 'number'):
                e.show_line_numbers = True
            elif set_option in ('nonu', 'nonumber'):
                e.show_line_numbers = False
            elif set_option in ('ruler', 'ru'):
                e.show_ruler = True
            elif set_option in ('noruler', 'noru'):
                e.show_ruler = False
            elif set_option in ('relativenumber', 'rnu'):
                e.relative_number = True
            elif set_option in ('norelativenumber', 'nornu'):
                e.relative_number = False
            elif set_option in ('cursorline', 'cul'):
                e.cursorline = True
            elif set_option in ('cursorcolumn', 'cuc'):
                e.cursorcolumn = True
            elif set_option in ('nocursorline', 'nocul'):
                e.cursorline = False
            elif set_option in ('nocursorcolumn', 'nocuc'):
                e.cursorcolumn = False
            elif set_option in ('colorcolumn', 'cc'):
                value = variables.get('set_value', '')
                if value:
                    e.colorcolumn = [
                        int(v) for v in value.split(',') if v.isdigit()]
