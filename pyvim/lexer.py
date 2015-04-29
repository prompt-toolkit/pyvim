from __future__ import unicode_literals

from pygments.lexers import get_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound

__all__ = (
    'DocumentLexer',
)


class DocumentLexer(object):
    """
    Lexer that depending on the filetype, uses another pygments lexer.
    """
    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def __call__(self, stripnl=False, stripall=False, ensurenl=False):
        """
        For compatibility with a Pygments lexer class. (We use an instance of
        this as if it were such a class.)
        """
        return self

    def get_tokens(self, text):
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
