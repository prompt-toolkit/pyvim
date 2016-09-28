from __future__ import unicode_literals
from prompt_toolkit.completion import Completer, Completion

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
            completer = _PythonCompleter(location)
        else:
            completer = DocumentWordsCompleter()

        # Call completer.
        return completer.get_completions(document, complete_event)


class _PythonCompleter(Completer):
    """
    Wrapper around the Jedi completion engine.
    """
    def __init__(self, location):
        self.location = location

    def get_completions(self, document, complete_event):
        script = self._get_jedi_script_from_document(document)
        if script:
            try:
                completions = script.completions()
            except TypeError:
                # Issue #9: bad syntax causes completions() to fail in jedi.
                # https://github.com/jonathanslenders/python-prompt-toolkit/issues/9
                pass
            except UnicodeDecodeError:
                # Issue #43: UnicodeDecodeError on OpenBSD
                # https://github.com/jonathanslenders/python-prompt-toolkit/issues/43
                pass
            except AttributeError:
                # Jedi issue #513: https://github.com/davidhalter/jedi/issues/513
                pass
            except ValueError:
                # Jedi issue: "ValueError: invalid \x escape"
                pass
            except KeyError:
                # Jedi issue: "KeyError: u'a_lambda'."
                # https://github.com/jonathanslenders/ptpython/issues/89
                pass
            except IOError:
                # Jedi issue: "IOError: No such file or directory."
                # https://github.com/jonathanslenders/ptpython/issues/71
                pass
            else:
                for c in completions:
                    yield Completion(c.name_with_symbols, len(c.complete) - len(c.name_with_symbols),
                                     display=c.name_with_symbols)

    def _get_jedi_script_from_document(self, document):
        import jedi  # We keep this import in-line, to improve start-up time.
                     # Importing Jedi is 'slow'.

        try:
            return jedi.Script(
                document.text,
                column=document.cursor_position_col,
                line=document.cursor_position_row + 1,
                path=self.location)
        except ValueError:
            # Invalid cursor position.
            # ValueError('`column` parameter is not in a valid range.')
            return None
        except AttributeError:
            # Workaround for #65: https://github.com/jonathanslenders/python-prompt-toolkit/issues/65
            # See also: https://github.com/davidhalter/jedi/issues/508
            return None
        except IndexError:
            # Workaround Jedi issue #514: for https://github.com/davidhalter/jedi/issues/514
            return None
        except KeyError:
            # Workaroud for a crash when the input is "u'", the start of a unicode string.
            return None

