"""
The styles, for the colorschemes.
"""
from __future__ import unicode_literals
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls

from pygments.styles import get_all_styles, get_style_by_name

__all__ = (
    'generate_built_in_styles',
    'get_editor_style_by_name',
)


def get_editor_style_by_name(name):
    """
    Get Style class.
    This raises `pygments.util.ClassNotFound` when there is no style with this
    name.
    """
    if name == 'vim':
        vim_style = Style.from_dict(default_vim_style)
    else:
        vim_style = style_from_pygments_cls(get_style_by_name(name))

    return merge_styles([
        vim_style,
        Style.from_dict(style_extensions),
    ])


def generate_built_in_styles():
    """
    Return a mapping from style names to their classes.
    """
    return dict((name, get_editor_style_by_name(name)) for name in get_all_styles())


style_extensions = {
    # Toolbar colors.
    'toolbar.status':                '#ffffff bg:#444444',
    'toolbar.status.cursorposition': '#bbffbb bg:#444444',
    'toolbar.status.percentage':     '#ffbbbb bg:#444444',

    # Flakes color.
    'flakeserror':            'bg:#ff4444 #ffffff',

    # Flake messages
    'flakemessage.prefix':    'bg:#ff8800 #ffffff',
    'flakemessage':           '#886600',

    # Highlighting for the text in the command bar.
    'commandline.command':    'bold',
    'commandline.location':   'bg:#bbbbff #000000',

    # Frame borders (for between vertical splits.)
    'frameborder':            'bold', #bg:#88aa88 #ffffff',

    # Messages
    'message':                'bg:#bbee88 #222222',

    # Welcome message
    'welcome title':          'underline',
    'welcome version':        '#8800ff',
    'welcome key':            '#0000ff',
    'welcome pythonversion':  'bg:#888888 #ffffff',

    # Tabs
    'tabbar':                 'noinherit reverse',
    'tabbar.tab':             'underline',
    'tabbar.tab.active':      'bold noinherit',

    # Arg count.
    'arg':                    'bg:#cccc44 #000000',

    # Buffer list
    'bufferlist':               'bg:#aaddaa #000000',
    'bufferlist title':         'underline',
    'bufferlist lineno':        '#666666',
    'bufferlist active':        'bg:#ccffcc',
    'bufferlist active.lineno': '#666666',
    'bufferlist searchmatch':   'bg:#eeeeaa',

    # Completions toolbar.
    'completions-toolbar':                    'bg:#aaddaa #000000',
    'completions-toolbar.arrow':              'bg:#aaddaa #000000 bold',
    'completions-toolbar completion':         'bg:#aaddaa #000000',
    'completions-toolbar current-completion': 'bg:#444444 #ffffff',

    # Soft wrap.
    'soft-wrap':                          '#888888',

    # Directory listing style.
    'pygments.directorylisting.header':    '#4444ff',
    'pygments.directorylisting.directory': '#ff4444 bold',
    'pygments.directorylisting.currentdirectory': '#888888',
    'pygments.directorylisting.parentdirectory': '#888888',
    'pygments.directorylisting.tempfile':  '#888888',
    'pygments.directorylisting.dotfile':  '#888888',
    'pygments.directorylisting.pythonfile':  '#8800ff',
    'pygments.directorylisting.textfile':  '#aaaa00',
}


# Default 'vim' color scheme. Taken from the Pygments Vim colorscheme, but
# modified to use mainly ANSI colors.
default_vim_style = {
    'pygments':                           '',
    'pygments.whitespace':                '',
    'pygments.comment':                   'ansiblue',
    'pygments.comment.preproc':           'ansiyellow',
    'pygments.comment.special':           'bold',

    'pygments.keyword':                   '#999900',
    'pygments.keyword.declaration':       'ansigreen',
    'pygments.keyword.namespace':         'ansimagenta',
    'pygments.keyword.pseudo':            '',
    'pygments.keyword.type':              'ansigreen',

    'pygments.operator':                  '',
    'pygments.operator.word':             '',

    'pygments.name':                      '',
    'pygments.name.class':                'ansicyan',
    'pygments.name.builtin':              'ansicyan',
    'pygments.name.exception':            '',
    'pygments.name.variable':             'ansicyan',
    'pygments.name.function':             'ansicyan',

    'pygments.literal':                   'ansired',
    'pygments.string':                    'ansired',
    'pygments.string.doc':                '',
    'pygments.number':                    'ansimagenta',

    'pygments.generic.heading':           'bold ansiblue',
    'pygments.generic.subheading':        'bold ansimagenta',
    'pygments.generic.deleted':           'ansired',
    'pygments.generic.inserted':          'ansigreen',
    'pygments.generic.error':             'ansibrightred',
    'pygments.generic.emph':              'italic',
    'pygments.generic.strong':            'bold',
    'pygments.generic.prompt':            'bold ansiblue',
    'pygments.generic.output':            'ansigray',
    'pygments.generic.traceback':         '#04d',

    'pygments.error':                     'border:ansired'
}
