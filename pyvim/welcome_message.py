"""
The welcome message. This is displayed when the editor opens without any files.
"""
from __future__ import unicode_literals
from prompt_toolkit.formatted_text.utils import fragment_list_len

import prompt_toolkit
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

WELCOME_MESSAGE_WIDTH = 36


WELCOME_MESSAGE_TOKENS = [
    ('class:title', 'PyVim - Pure Python Vi clone\n'),
    ('', 'Still experimental\n\n'),
    ('', 'version '), ('class:version', pyvim_version),
        ('', ', prompt_toolkit '), ('class:version', prompt_toolkit.__version__),
    ('', '\n'),
    ('', 'by Jonathan Slenders\n\n'),
    ('', 'type :q'),
    ('class:key', '<Enter>'),
    ('', '            to exit\n'),
    ('', 'type :help'),
    ('class:key', '<Enter>'),
    ('', ' or '),
    ('class:key', '<F1>'),
    ('', ' for help\n\n'),
    ('', 'All feedback is appreciated.\n\n'),
    ('class:pythonversion', ' %s %i.%i.%i ' % (
        platform.python_implementation(),
        version[0], version[1], version[2])),
]

WELCOME_MESSAGE_HEIGHT = ''.join(t[1] for t in WELCOME_MESSAGE_TOKENS).count('\n') + 1
