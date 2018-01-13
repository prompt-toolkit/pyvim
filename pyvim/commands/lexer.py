from __future__ import unicode_literals

from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.lexers import PygmentsLexer, SimpleLexer

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
        'command': SimpleLexer('class:commandline.command'),
        'location': SimpleLexer('class:commandline.location'),
        'shell_command': PygmentsLexer(BashLexer),
    })
