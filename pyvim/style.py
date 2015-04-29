"""
The styles, for the colorschemes.
"""
from __future__ import unicode_literals
from prompt_toolkit.styles import default_style_extensions

from pygments.styles import get_all_styles, get_style_by_name
from pygments.token import Token

__all__ = (
    'get_editor_style_by_name',
)


def get_editor_style_by_name(name):
    """
    Get Style class.
    This raises `pygments.util.ClassNotFound` when there is no style with this
    name.
    """
    style_cls = get_style_by_name(name)

    class EditorStyle(style_cls):
        styles = {}
        styles.update(style_cls.styles)
        styles.update(default_style_extensions)
        styles.update(style_extensions)
    EditorStyle.__name__ = str('PyvimStyle_%s' % style_cls.__name__)
    return EditorStyle


def generate_built_in_styles():
    """
    Return a mapping from style names to their classes.
    """
    return dict((name, get_editor_style_by_name(name)) for name in get_all_styles())


style_extensions = {
    # Toolbar colors.
    Token.Toolbar:                '#ffffff bg:#444444',
    Token.Toolbar.CursorPosition: '#bbffbb bg:#444444',
    Token.Toolbar.Percentage:     '#ffbbbb bg:#444444',
    Token.Header:                 '#ffffff bg:#662222',

    # Flakes color.
    Token.FlakesError:            'bg:#ff4444 #ffffff',

    # Flake messages
    Token.FlakeMessage.Prefix:    'bg:#ff8800 #ffffff',
    Token.FlakeMessage:           '#886600',

    # Highlighting for the text in the command bar.
    Token.CommandLine.Command:    'bold',
    Token.CommandLine.Location:   'bg:#bbbbff #000000',

    # Frame borders (for between vertical splits.)
    Token.FrameBorder:            'bold', #bg:#88aa88 #ffffff',

    # Messages
    Token.Message:                'bg:#bbee88 #222222',

    # Welcome message
    Token.Welcome.Title:          'underline',
    Token.Welcome.Body:           '',
    Token.Welcome.Body.Key:       '#0000ff',
    Token.Welcome.PythonVersion:  'bg:#888888 #ffffff',

    # Matching brace color
    Token.MatchingBracket:        'bg:#aaaaff #000000',

    # Tabs
    Token.TabBar:                 'bg:#000000',
    Token.TabBar.Tab:             'bg:#888888 underline',
    Token.TabBar.Tab.Active:      'bold noinherit',

    # Arg count.
    Token.Arg:                    'bg:#cccc44 #000000',

    # Buffer list
    Token.BufferList:               'bg:#aaddaa #000000',
    Token.BufferList.Title:         'underline',
    Token.BufferList.Lineno:        '#666666',
    Token.BufferList.Active:        'bg:#ccffcc',
    Token.BufferList.Active.Lineno: '#666666',
    Token.BufferList.SearchMatch:   'bg:#eeeeaa',

    # Completions toolbar.
    Token.Toolbar.Completions:                    'bg:#aaddaa #000000',
    Token.Toolbar.Completions.Arrow:              'bg:#aaddaa #000000 bold',
    Token.Toolbar.Completions.Completion:         'bg:#aaddaa #000000',
    Token.Toolbar.Completions.Completion.Current: 'bg:#444444 #ffffff',

    # Tabs
    Token.TrailingWhiteSpace:             '#999999',
    Token.Tab:                            '#999999',
}
