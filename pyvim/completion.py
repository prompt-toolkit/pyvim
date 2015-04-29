from __future__ import unicode_literals
from prompt_toolkit.completion import Completer, Completion
from ptpython.completer import PythonCompleter

import re
import weakref

__all__ = (
    'DocumentCompleter',
)


class DocumentWordsCompleter(Completer):
    """
    Completer that completes on words that appear already in the open document.
    """
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()

        # Create a set of words that could be a possible completion.
        words = set()

        for w in re.split(r'\W', document.text):
            if len(w) > 1:
                if w.startswith(word_before_cursor) and w != word_before_cursor:
                    words.add(w)

        # Yield Completion instances.
        for w in sorted(words):
            yield Completion(w, start_position=-len(word_before_cursor))


class DocumentCompleter(Completer):
    """
    This is the general completer for EditorBuffer completions.
    Depending on the file type and settings, it selects another completer to
    call.
    """
    def __init__(self, editor, editor_buffer):
        # (Weakrefs, they are already pointing to us.)
        self._editor_ref = weakref.ref(editor)
        self._editor_buffer_ref = weakref.ref(editor_buffer)

    def get_completions(self, document, complete_event):
        editor = self._editor_ref()
        location = self._editor_buffer_ref().location or '.txt'

        # Select completer.
        if location.endswith('.py') and editor.enable_jedi:
            completer = PythonCompleter(lambda: globals(), lambda: {})
        else:
            completer = DocumentWordsCompleter()

        # Call completer.
        return completer.get_completions(document, complete_event)
