from __future__ import unicode_literals

from prompt_toolkit.contrib.regular_languages.compiler import compile

from .commands import get_commands_taking_filenames


#: The compiled grammar for the Vim command line.
COMMAND_GRAMMAR = compile(r"""
    # Allow leading colons and whitespace. (They are ignored.)
    :*
    \s*
    (
        # Commands accepting a filename.
        (?P<command>%(commands_taking_filenames)s)  \s+   (?P<filename>[^\s]+)   |

        # Commands accepting a buffer.
        (?P<command>b|buffer)  \s+   (?P<buffer_name>[^\s]+)    |

        # Jump to line numbers.
        (?P<go_to_line>\d+)                                     |

        # Set operation
        (?P<command>set) \s+ (?P<set_option>[^\s=]+)
                             (=(?P<set_value>[^\s]+))?           |

        # Colorscheme command
        (?P<command>colorscheme) \s+ (?P<colorscheme>[^\s]+)    |

        # Shell command
        !(?P<shell_command>.*)                                  |

        # Any command. (For command completions.)
        (?P<command>[^\s]+)                                     |

        # Accept the empty input as well. (Ignores everything.)

        #(?P<command>colorscheme.+)    (?P<colorscheme>[^\s]+)  |
    )

    # Allow trailing space.
    \s*
""" % {
    'commands_taking_filenames': '|'.join(get_commands_taking_filenames()),
})
