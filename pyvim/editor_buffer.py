from __future__ import unicode_literals
from prompt_toolkit.document import Document

from prompt_toolkit.buffer import Buffer, AcceptAction
from prompt_toolkit.filters import Always
from pyvim.completion import DocumentCompleter

from six import string_types

import codecs
import os

__all__ = (
    'EditorBuffer',
)


class EditorBuffer(object):
    """
    Wrapper aronud a `prompt-toolkit` buffer.

    A 'prompt-toolkit' `Buffer` doesn't know anything about files, changes,
    etc... This wrapper contains the necessary data for the editor.
    """
    def __init__(self, editor, buffer_name, filename=None, text=None):
        assert isinstance(buffer_name, string_types)
        assert filename is None or isinstance(filename, string_types)
        assert text is None or isinstance(text, string_types)
        assert not (filename and text)

        self.buffer_name = buffer_name
        self.filename = filename
        self.encoding = 'utf-8'
        self.is_directory = False

        # Create buffer
        if filename:
            self.is_directory, text = self._read(filename)
        else:
            text = text or ''

        self._file_content = text

        # Append slash to directory names.
        if self.is_directory:
            self.filename += '/'

        # Create Buffer.
        self.buffer = Buffer(
            is_multiline=Always(),
            completer=DocumentCompleter(editor, self),
            initial_document=Document(text, 0),
            accept_action=AcceptAction.IGNORE)

        # List of reporting errors.
        self.report_errors = []

    @property
    def has_unsaved_changes(self):
        """
        True when some changes are not yet written to file.
        """
        return self._file_content != self.buffer.text

    @property
    def is_new_file(self):
        """ True when this file does not exist on the disk yet. """
        return self.filename is None

    def _read(self, filename):
        """
        Read file content.
        """
        # Expand tilde.
        filename = os.path.expanduser(filename)

        if os.path.isfile(filename):
            # Try to open this file, using different encodings.
            encodings = ['utf-8', 'latin-1']
            for e in encodings:
                try:
                    with codecs.open(filename, 'r', e) as f:
                        self.encoding = e
                        return False, f.read()
                except UnicodeDecodeError:
                    pass  # Try next codec.

            # Unable to open. TODO: make read only.
            self.encoding = None
            return False, 'Unable to open file...'

        # Handle directory listing.
        elif os.path.isdir(filename):
            return True, self._create_directory_listing(filename)

        else:
            return False, ''

    def write(self, filename=None):
        """
        Save this file to disk.
        """
        # Take filename and expand tilde.
        if filename is not None:
            self.filename = filename
        assert self.filename
        filename = os.path.expanduser(self.filename)

        # Write it.
        with codecs.open(filename, 'w', self.encoding) as f:
            f.write(self.buffer.text)

        self._file_content = self.buffer.text

    @staticmethod
    def _create_directory_listing(directory):
        """
        Create a textual listing of the directory content.
        """
        # Read content.
        content = sorted(os.listdir(directory))
        directories = []
        files = []

        for f in content:
            if os.path.isdir(os.path.join(directory, f)):
                directories.append(f)
            else:
                files.append(f)

        # Construct output.
        result = []
        result.append('" ==================================\n')
        result.append('" Directory Listing\n')
        result.append('"    %s\n' % os.path.abspath(directory))
        result.append('" ==================================\n')

        for d in directories:
            result.append('%s/\n' % d)

        for f in files:
            result.append('%s\n' % f)

        return ''.join(result)

    def get_display_name(self, short=False):
        """
        Return name as displayed.
        """
        if self.filename is None:
            return '[New file]'
        elif short:
            return os.path.basename(self.filename)
        else:
            return self.filename

    def __repr__(self):
        return '%s(buffer_name=%r, buffer=%r)' % (
            self.__class__.__name__,
            self.buffer_name, self.buffer)
