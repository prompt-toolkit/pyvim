from __future__ import unicode_literals

from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer

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
    return GrammarLexer(COMMAND_GRAMMAR, tokens={
        'command': Token.CommandLine.Command,
        'location': Token.CommandLine.Location,
    }, lexers={
        'shell_command': BashLexer,
    })
