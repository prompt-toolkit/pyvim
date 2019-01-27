from __future__ import unicode_literals

from prompt_toolkit.lexers import Lexer, SimpleLexer, PygmentsLexer
from pygments.lexer import RegexLexer
from pygments.token import Token

__all__ = (
    'DocumentLexer',
)


class DocumentLexer(Lexer):
    """
    Lexer that depending on the filetype, uses another pygments lexer.
    """
    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def lex_document(self, document):
        """
        Call the lexer and return a get_tokens_for_line function.
        """
        location = self.editor_buffer.location

        if location:
            if self.editor_buffer.in_file_explorer_mode:
                return PygmentsLexer(DirectoryListingLexer, sync_from_start=False).lex_document(document)

            return PygmentsLexer.from_filename(location, sync_from_start=False).lex_document(document)

        return SimpleLexer().lex_document(document)


_DirectoryListing = Token.DirectoryListing

class DirectoryListingLexer(RegexLexer):
    """
    Highlighting of directory listings.
    """
    name = 'directory-listing'
    tokens = {
        str('root'): [  # Conversion to `str` because of Pygments on Python 2.
            (r'^".*', _DirectoryListing.Header),

            (r'^\.\./$', _DirectoryListing.ParentDirectory),
            (r'^\./$', _DirectoryListing.CurrentDirectory),

            (r'^[^"].*/$', _DirectoryListing.Directory),
            (r'^[^"].*\.(txt|rst|md)$', _DirectoryListing.Textfile),
            (r'^[^"].*\.(py)$', _DirectoryListing.PythonFile),

            (r'^[^"].*\.(pyc|pyd)$', _DirectoryListing.Tempfile),
            (r'^\..*$', _DirectoryListing.Dotfile),
        ]
    }
