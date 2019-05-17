from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit import __version__ as ptk_version

from pyvim.completion import DocumentCompleter
from pyvim.reporting import report

from six import string_types

import os
import weakref

PTK3 = ptk_version.startswith('3.')

if PTK3:
    from asyncio import get_event_loop
else:
    from prompt_toolkit.eventloop import call_from_executor, run_in_executor

__all__ = (
    'EditorBuffer',
)


class EditorBuffer(object):
    """
    Wrapper around a `prompt-toolkit` buffer.

    A 'prompt-toolkit' `Buffer` doesn't know anything about files, changes,
    etc... This wrapper contains the necessary data for the editor.
    """
    def __init__(self, editor, location=None, text=None):
        assert location is None or isinstance(location, string_types)
        assert text is None or isinstance(text, string_types)
        assert not (location and text)

        self._editor_ref = weakref.ref(editor)
        self.location = location
        self.encoding = 'utf-8'

        #: is_new: True when this file does not yet exist in the storage.
        self.is_new = True

        # Empty if not in file explorer mode, directory path otherwise.
        self.isdir = False

        # Read text.
        if location:
            text = self._read(location)
        else:
            text = text or ''

        self._file_content = text

        # Create Buffer.
        self.buffer = Buffer(
            multiline=True,
            completer=DocumentCompleter(editor, self),
            document=Document(text, 0),
            on_text_changed=lambda _: self.run_reporter())

        # List of reporting errors.
        self.report_errors = []
        self._reporter_is_running = False

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

    @property
    def in_file_explorer_mode(self):
        """
        True when we are in file explorer mode (when this is a directory).
        """
        return self.isdir

    def _read(self, location):
        """
        Read file I/O backend.
        """
        for io in self.editor.io_backends:
            if io.can_open_location(location):
                # Found an I/O backend.
                exists = io.exists(location)
                self.isdir = io.isdir(location)

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
        return '%s(buffer=%r)' % (self.__class__.__name__, self.buffer)

    def run_reporter(self):
        " Buffer text changed. "
        if not self._reporter_is_running:
            self._reporter_is_running = True

            text = self.buffer.text
            self.report_errors = []

            # Don't run reporter when we don't have a location. (We need to
            # know the filetype, actually.)
            if self.location is None:
                return

            # Better not to access the document in an executor.
            document = self.buffer.document

            if PTK3:
                loop = get_event_loop()

            def in_executor():
                # Call reporter
                report_errors = report(self.location, document)

                def ready():
                    self._reporter_is_running = False

                    # If the text has not been changed yet in the meantime, set
                    # reporter errors. (We were running in another thread.)
                    if text == self.buffer.text:
                        self.report_errors = report_errors
                        get_app().invalidate()
                    else:
                        # Restart reporter when the text was changed.
                        self.run_reporter()

                if PTK3:
                    loop.call_soon_threadsafe(ready)
                else:
                    call_from_executor(ready)

            if PTK3:
                loop.run_in_executor(None, in_executor)
            else:
                run_in_executor(in_executor)
