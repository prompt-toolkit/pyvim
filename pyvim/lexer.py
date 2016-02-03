from __future__ import unicode_literals

from prompt_toolkit.layout.lexers import Lexer, SimpleLexer, PygmentsLexer

__all__ = (
    'DocumentLexer',
)


class DocumentLexer(Lexer):
    """
    Lexer that depending on the filetype, uses another pygments lexer.
    """
    def __init__(self, editor_buffer):
        self.editor_buffer = editor_buffer

    def lex_document(self, cli, document):
        """
        Call the lexer and return a get_tokens_for_line function.
        """
        location = self.editor_buffer.location

        if location:
            return PygmentsLexer.from_filename(location, sync_from_start=False).lex_document(cli, document)

        return SimpleLexer().lex_document(cli, document)
