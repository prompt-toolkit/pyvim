pyvim
=====

*An implementation of Vim in Python*

::

    pip install pyvim

.. image :: https://github.com/jonathanslenders/pyvim/raw/master/docs/images/welcome-screen.png

Issues, questions, wishes, comments, feedback, remarks? Please create a GitHub
issue, I appreciate it.

|Build Status|


Installation
------------

Simply install ``pyvim`` using pip:

::

    pip install pyvim


It is a good idea to add the following to your ``~/.bashrc`` if you really
want to use it:

::

    alias vi=pyvim
    export EDITOR=pyvim


The good things
---------------

The editor is written completely in Python. (There are no C extensions). This
makes development a lot faster. It's easy to prototype and integrate new
features.

We have already many nice things, for instance:

- Syntax highlighting of files, using the Pygments lexers.

- Horizontal and vertical splits, as well as tab pages. (Similar to Vim.)

- All of the functionality of `prompt_toolkit
  <http://github.com/jonathanslenders/python-prompt-toolkit>`_. This includes a
  lot of Vi key bindings, it's platform independent and runs on every Python
  version from python 2.6 up to 3.4. It also runs on Pypy with a noticable
  performance boost.

- Several ``:set ...`` commands have been implemented, like ``incsearch``,
  ``number``, ``ignorecase``, ``wildmenu``, ``expandtab``, ``hlsearch``,
  ``ruler``, ``paste`` and ``tabstop``.

- Other working commands: ``vsplit``, ``tabnew``, ``only``, ``badd``, and many
  others.

- For Python source code, auto completion uses the amazing Jedi library, and
  code checking in done (asynchronously) through Pyflakes.

- Colorschemes can be changed at runtime.

Further, when the project develops, it should also become possible to write
extensions in Python, and use Python as a scripting language. (Instead of
vimscript, for instance.)

We can also do some cool stuff. Like for instance running the editor on the
Python asyncio event loop and having other coroutines interact with the editor.


Some more screenshots
---------------------

Editing its own source code:

.. image :: https://github.com/jonathanslenders/pyvim/raw/master/docs/images/editing-pyvim-source.png

Window layouts (horizontal and vertical splits + tab pages.)

.. image :: https://github.com/jonathanslenders/pyvim/raw/master/docs/images/window-layout.png

Pyflakes for Python code checking and Jedi for autocompletion:

.. image :: https://github.com/jonathanslenders/pyvim/raw/master/docs/images/pyflakes-and-jedi.png

Other colorschemes:

.. image :: https://github.com/jonathanslenders/pyvim/raw/master/docs/images/colorschemes.png

Chinese and Japanese input (double width characters):

.. image :: https://raw.githubusercontent.com/jonathanslenders/pyvim/master/docs/images/cjk.png?v2


Configuring pyvim
-----------------

It is possible to create a ``.pyvimrc`` file for a custom configuration.
Have a look at this example: `pyvimrc
<https://github.com/jonathanslenders/pyvim/blob/master/examples/config/pyvimrc>`_


Limitations
-----------

Compared to Vi Improved, Pyvim is still less powerful in many aspects.

- ``prompt_toolkit`` does not (or not yet) allow buffers to have an individual
  cursor when buffers are opened in several windows. Currently, this results in
  some unexpected behaviour, when a file is displayed in two windows at the
  same time. (The cursor could be displayed in the wrong window and other
  windows will sometimes scroll along when the cursor moves.) This has to be
  fixed in the future.
- The data structure for a buffer is extremely simple. (Right now, it's just a
  Python string, and an integer for the cursor position.) This works extremely
  well for development and quickly prototyping of new features, but it comes
  with a performance penalty. Depending on the system, when a file has above a
  thousand lines and syntax highlighting is enabled, editing will become
  noticable slower. (The bottleneck is probably the ``BufferControl`` code,
  which on every key press tries to reflow the text and calls pygments for
  highlighting. And this is Python code looping through single characters.)
- A lot of nice Vim features, like line folding, macros, etcetera are not yet
  implemented.
- Windows support is not that nice. It works, but could be improved. (I think
  most Windows users are not that interested in this project, but prove me
  wrong.)


Roadmap
-------

There is no roadmap. I mostly implement the stuff which I need or interests me,
or which gives me the opportunity to learn. But feel free to create a GitHub
issue to request a new feature. Pull requests are also welcome. (Maybe create
an issue first to discuss it, if you're unsure whether I'll merge it.)

Maybe some day we will have a better data structure (Rope), that makes it
possible to open really large files. (With good algorithms, Python does not have
to be slower than C code.)

Maybe we will also have line folding and probably block editing. Maybe some
day we will have a built-in Python debugger or mouse support. We'll see. :)


Testing
-------

To run all tests, install pytest:

    pip install pytest

And then run from root pyvim directory:

    py.test

To test pyvim against all supported python versions, install tox:

    pip install tox

And then run from root pyvim directory:

    tox

You need to have installed all the supported versions of python in order to run
tox command successfully.


Why did I create Pyvim?
-----------------------

There are several reasons.

The main reason is maybe because it was a small step after I created the Python
``prompt-toolkit`` library. That is a library which is actually only a simply
pure Python readline replacement, but with some nice additions like syntax
highlighting and multiline editing. It was never intended to be a toolkit for
full-screen terminal applications, but at some point I realised that everything
we need for an editor was in there and I liked to challenge its design. So, I
started an editor and the first proof of concept was literally just a few
hundred lines of code, but it was already a working editor.

The creation of ``pyvim`` will make sure that we have a solid architecture for
``prompt-toolkit``, but it also aims to demonstrate the flexibility of the
library. When it makes sense, features of ``pyvim`` will move back to
``prompt-toolkit``, which in turn also results in a better Python REPL.
(see `ptpython <https://github.com/jonathanslenders/ptpython>`_, an alternative
REPL.)

Above all, it is really fun to create an editor.


Alternatives
------------

Certainly have a look at the alternatives:

- Kaa: https://github.com/kaaedit/kaa by @atsuoishimoto
- Vai: https://github.com/stefanoborini/vai by @stefanoborini


Q & A:
------

Q
 Do you use curses?
A
 No, it uses only ``prompt-toolkit``.


Thanks
------

- To Vi Improved, by Bram Moolenaar. For the inspiration.
- To Jedi, pyflakes and the docopt Python libraries.
- To the Python wcwidth port of Jeff Quast for support of double width characters.
- To Guido van Rossum, for creating Python.


.. |Build Status| image:: https://api.travis-ci.org/jonathanslenders/pyvim.svg?branch=master
    :target: https://travis-ci.org/jonathanslenders/pyvim#
