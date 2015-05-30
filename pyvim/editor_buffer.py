from __future__ import unicode_literals
from prompt_toolkit.document import Document

from prompt_toolkit.buffer import Buffer, AcceptAction
from prompt_toolkit.filters import Always
from pyvim.completion import DocumentCompleter

from six import string_types

import os
import weakref

__all__ = (
    'EditorBuffer',
)


class EditorBuffer(object):
    """
    Wrapper around a `prompt-toolkit` buffer.

    A 'prompt-toolkit' `Buffer` doesn't know anything about files, changes,
    etc... This wrapper contains the necessary data for the editor.
    """
    def __init__(self, editor, buffer_name, location=None, text=None):
        assert isinstance(buffer_name, string_types)
        assert location is None or isinstance(location, string_types)
        assert text is None or isinstance(text, string_types)
        assert not (location and text)

        self._editor_ref = weakref.ref(editor)
        self.buffer_name = buffer_name
        self.location = location
        self.encoding = 'utf-8'

        #: is_new: True when this file does not yet exist in the storage.
        self.is_new = True

        # Read text.
        if location:
            text = self._read(location)
        else:
            text = text or ''

        self._file_content = text

        # Create Buffer.
        self.buffer = Buffer(
            is_multiline=Always(),
            completer=DocumentCompleter(editor, self),
            initial_document=Document(text, 0),
            accept_action=AcceptAction.IGNORE)

        # List of reporting errors.
        self.report_errors = []

    @property
    def editor(self):
        """ Back reference to the Editor. """
        return self._editor_ref()

    @property
    def has_unsaved_changes(self):
        """
        True when some changes are not yet written to file.
        """
        return self._file_content != self.buffer.text

    def _read(self, location):
        """
        Read file I/O backend.
        """
        for io in self.editor.io_backends:
            if io.can_open_location(location):
                # Found an I/O backend.
                exists = io.exists(location)
                if exists in (True, NotImplemented):
                    # File could exist. Read it.
                    self.is_new = False
                    try:
                        text, self.encoding = io.read(location)

                        # Replace \r\n by \n.
                        text = text.replace('\r\n', '\n')

                        # Drop trailing newline while editing.
                        # (prompt-toolkit doesn't enforce the trailing newline.)
                        if text.endswith('\n'):
                            text = text[:-1]
                    except Exception as e:
                        self.editor.show_message('Cannot read %r: %r' % (location, e))
                        return ''
                    else:
                        return text
                else:
                    # File doesn't exist.
                    self.is_new = True
                    return ''

        self.editor.show_message('Cannot read: %r' % location)
        return ''

    def reload(self):
        """
        Reload file again from storage.
        """
        text = self._read(self.location)
        cursor_position = min(self.buffer.cursor_position, len(text))

        self.buffer.document = Document(text, cursor_position)
        self._file_content = text

    def write(self, location=None):
        """
        Write file to I/O backend.
        """
        # Take location and expand tilde.
        if location is not None:
            self.location = location
        assert self.location

        # Find I/O backend that handles this location.
        for io in self.editor.io_backends:
            if io.can_open_location(self.location):
                break
        else:
            self.editor.show_message('Unknown location: %r' % location)

        # Write it.
        try:
            io.write(self.location, self.buffer.text + '\n', self.encoding)
            self.is_new = False
        except Exception as e:
            # E.g. "No such file or directory."
            self.editor.show_message('%s' % e)
        else:
            # When the save succeeds: update: _file_content.
            self._file_content = self.buffer.text

    def get_display_name(self, short=False):
        """
        Return name as displayed.
        """
        if self.location is None:
            return '[New file]'
        elif short:
            return os.path.basename(self.location)
        else:
            return self.location

    def __repr__(self):
        return '%s(buffer_name=%r, buffer=%r)' % (
            self.__class__.__name__,
            self.buffer_name, self.buffer)
