"""
The welcome message. This is displayed when the editor opens without any files.
"""
from __future__ import unicode_literals
from pygments.token import Token
from prompt_toolkit.layout.utils import token_list_len

import pyvim
import platform
import sys
version = sys.version_info
pyvim_version = pyvim.__version__

__all__ = (
    'WELCOME_MESSAGE_TOKENS',
    'WELCOME_MESSAGE_WIDTH',
    'WELCOME_MESSAGE_HEIGHT',
)

WELCOME_MESSAGE_WIDTH = 34


def _t(token_list):
    """
    Center tokens on this line.
    """
    length = token_list_len(token_list)

    return [(Token.Welcome, ' ' * int((WELCOME_MESSAGE_WIDTH - length) / 2))] \
        + token_list + [(Token.Welcome, '\n')]


WELCOME_MESSAGE_TOKENS = (
    _t([(Token.Welcome.Title, 'PyVim - Pure Python Vi clone')]) +
    _t([(Token.Welcome.Body, 'Still experimental')]) +
    _t([(Token.Welcome.Body, '')]) +
    _t([(Token.Welcome.Body, 'version %s' % pyvim_version)]) +
    _t([(Token.Welcome.Body, 'by Jonathan Slenders')]) +
    _t([(Token.Welcome.Body, '')]) +
    _t([(Token.Welcome.Body, 'type :q'),
        (Token.Welcome.Body.Key, '<Enter>'),
        (Token.Welcome.Body, '            to exit')]) +
    _t([(Token.Welcome.Body, 'type :help'),
        (Token.Welcome.Body.Key, '<Enter>'),
        (Token.Welcome.Body, ' or '),
        (Token.Welcome.Body.Key, '<F1>'),
        (Token.Welcome.Body, ' for help')]) +
    _t([(Token.Welcome.Body, '')]) +
    _t([(Token.Welcome.Body, 'All feedback is appreciated.')]) +
    _t([(Token.Welcome.Body, '')]) +
    _t([(Token.Welcome.Body, '')]) +

    _t([(Token.Welcome.PythonVersion, ' %s %i.%i.%i ' % (
        platform.python_implementation(),
        version[0], version[1], version[2]))])
)

WELCOME_MESSAGE_HEIGHT = ''.join(t[1] for t in WELCOME_MESSAGE_TOKENS).count('\n')
