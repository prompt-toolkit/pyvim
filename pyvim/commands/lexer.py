from __future__ import unicode_literals

from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.layout.lexers import PygmentsLexer, SimpleLexer

from pygments.token import Token
from pygments.lexers import BashLexer
from .grammar import COMMAND_GRAMMAR

__all__ = (
    'create_command_lexer',
)


def create_command_lexer():
    """
    Lexer for highlighting of the command line.
    """
    return GrammarLexer(COMMAND_GRAMMAR, lexers={
        'command': SimpleLexer(Token.CommandLine.Command),
        'location': SimpleLexer(Token.CommandLine.Location),
        'shell_command': PygmentsLexer(BashLexer),
    })
