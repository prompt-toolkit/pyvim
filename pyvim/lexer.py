from __future__ import unicode_literals

from prompt_toolkit.layout.lexers import Lexer
from pygments.lexers import get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound

__all__ = (
    'DocumentLexer',
)


class DocumentLexer(Lexer):
    """
    Lexer that depending on the filetype, uses another pygments lexer.
    """
    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def get_tokens(self, cli, text):
        """
        Call the lexer and return the tokens.
        """
        location = self.editor_buffer.location

        if location:
            # Create an instance of the correct lexer class.
            try:
                lexer = get_lexer_for_filename(location, stripnl=False, stripall=False, ensurenl=False)
            except ClassNotFound:
                pass
            else:
                return lexer.get_tokens(text)

        return [(Token, text)]
