"""
Reporting.

This is a way to highlight syntax errors in an open files.
Reporters are run in an executor (in a thread) to ensure not blocking the
input.

Usage::

    errors = report('location.py', Document('file content'))
"""
from __future__ import unicode_literals
import pyflakes.api
import string
import six

from pygments.token import Token

__all__ = (
    'report',
)


class ReporterError(object):
    """
    Error found by a reporter.
    """
    def __init__(self, lineno, start_column, end_column, message_token_list):
        self.lineno = lineno  # Zero based line number.
        self.start_column = start_column
        self.end_column = end_column
        self.message_token_list = message_token_list


def report(location, document):
    """
    Run reporter on document and return list of ReporterError instances.
    (Depending on the location it will or won't run anything.)

    Returns a list of `ReporterError`.
    """
    assert isinstance(location, six.string_types)

    if location.endswith('.py'):
        return report_pyflakes(document)
    else:
        return []


WORD_CHARACTERS = string.ascii_letters + '0123456789_'


def report_pyflakes(document):
    """
    Run pyflakes on document and return list of ReporterError instances.
    """
    # Run pyflakes on input.
    reporter = _FlakesReporter()
    pyflakes.api.check(document.text, '', reporter=reporter)

    def format_flake_message(message):
        return [
            (Token.FlakeMessage.Prefix, 'pyflakes:'),
            (Token, ' '),
            (Token.FlakeMessage, message.message % message.message_args)
        ]

    def message_to_reporter_error(message):
        """ Turn pyflakes message into ReporterError. """
        start_index = document.translate_row_col_to_index(message.lineno - 1, message.col)
        end_index = start_index
        while end_index < len(document.text) and document.text[end_index] in WORD_CHARACTERS:
            end_index += 1

        return ReporterError(lineno=message.lineno - 1,
                             start_column=message.col,
                             end_column=message.col + end_index - start_index,
                             message_token_list=format_flake_message(message))

    # Construct list of ReporterError instances.
    return [message_to_reporter_error(m) for m in reporter.messages]


class _FlakesReporter(object):
    """
    Reporter class to be passed to pyflakes.api.check.
    """
    def __init__(self):
        self.messages = []

    def unexpectedError(self, location, msg):
        pass

    def syntaxError(self, location, msg, lineno, offset, text):
        pass

    def flake(self, message):
        self.messages.append(message)
