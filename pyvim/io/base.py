from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import six

__all__ = (
    'EditorIO',
)


class EditorIO(six.with_metaclass(ABCMeta, object)):
    """
    The I/O interface for editor buffers.

    It is for instance possible to pass an FTP I/O backend to EditorBuffer, to
    read/write immediately from an FTP server. Or a GZIP backend for files
    ending with .gz.
    """
    @abstractmethod
    def can_open_location(cls, location):
        """
        Return True when this I/O implementation is able to handle this `location`.
        """
        return False

    @abstractmethod
    def exists(self, location):
        """
        Return whether this location exists in this storage..
        (If not, this is a new file.)
        """
        return True

    @abstractmethod
    def read(self, location):
        """
        Read file for storage. Returns (text, encoding tuple.)
        Can raise IOError.
        """

    @abstractmethod
    def write(self, location, data, encoding='utf-8'):
        """
        Write file to storage.
        Can raise IOError.
        """
