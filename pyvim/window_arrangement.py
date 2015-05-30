"""
Window arrangement.

This contains the data structure for the tab pages with their windows and
buffers. It's not the same as a `prompt-toolkit` layout. The latter directly
represents the rendering, while this is more specific for the editor itself.
"""
from __future__ import unicode_literals
from six import string_types
import weakref

from .editor_buffer import EditorBuffer

__all__ = (
    'WindowArrangement',
)


class HSplit(list):
    """ Horizontal split. (This is a higher level split than
    prompt_toolkit.layout.HSplit.) """


class VSplit(list):
    """ Horizontal split. """


class Window(object):
    """
    Editor window: a window can show any open buffer.
    """
    def __init__(self, editor_buffer):
        assert isinstance(editor_buffer, EditorBuffer)
        self.editor_buffer = editor_buffer

    def __repr__(self):
        return '%s(editor_buffer=%r)' % (self.__class__.__name__, self.editor_buffer)


class TabPage(object):
    """
    Tab page. Container for windows.
    """
    def __init__(self, window):
        assert isinstance(window, Window)
        self.root = VSplit([window])

        # Keep track of which window is focusesd in this tab.
        self.active_window = window

    def windows(self):
        """ Return a list of all windows in this tab page. """
        return [window for _, window in self._walk_through_windows()]

    def window_count(self):
        """ The amount of windows in this tab. """
        return len(self.windows())

    def visible_editor_buffers(self):
        """
        Return a list of visible `EditorBuffer` instances.
        """
        return [w.editor_buffer for w in self.windows()]

    def _walk_through_windows(self):
        """
        Yields (Split, Window) tuples.
        """
        def walk(split):
            for c in split:
                if isinstance(c, (HSplit, VSplit)):
                    for i in walk(c):
                        yield i
                elif isinstance(c, Window):
                    yield split, c

        return walk(self.root)

    def _walk_through_splits(self):
        """
        Yields (parent_split, child_plit) tuples.
        """
        def walk(split):
            for c in split:
                if isinstance(c, (HSplit, VSplit)):
                    yield split, c
                    for i in walk(c):
                        yield i

        return walk(self.root)

    def _get_active_split(self):
        for split, window in self._walk_through_windows():
            if window == self.active_window:
                return split
        raise Exception('active_window not found. Something is wrong.')

    def _get_split_parent(self, split):
        for parent, child in self._walk_through_splits():
            if child == split:
                return parent

    def _split(self, split_cls, editor_buffer=None):
        """
        Split horizontal or vertical.
        (when editor_buffer is None, show the current buffer there as well.)
        """
        if editor_buffer is None:
            editor_buffer = self.active_window.editor_buffer

        active_split = self._get_active_split()
        index = active_split.index(self.active_window)
        new_window = Window(editor_buffer)

        if isinstance(active_split, split_cls):
            # Add new window to active split.
            active_split.insert(index, new_window)
        else:
            # Split in the other direction.
            active_split[index] = split_cls([active_split[index], new_window])

        # Focus new window.
        self.active_window = new_window

    def hsplit(self, editor_buffer=None):
        """
        Split active window horizontally.
        """
        self._split(HSplit, editor_buffer)

    def vsplit(self, editor_buffer=None):
        """
        Split active window vertically.
        """
        self._split(VSplit, editor_buffer)

    def show_editor_buffer(self, editor_buffer):
        """
        Open this `EditorBuffer` in the active window.
        """
        assert isinstance(editor_buffer, EditorBuffer)
        self.active_window.editor_buffer = editor_buffer

    def close_editor_buffer(self, editor_buffer):
        """
        Close all the windows that have this editor buffer open.
        """
        for split, window in self._walk_through_windows():
            if window.editor_buffer == editor_buffer:
                self._close_window(window)

    def _close_window(self, window):
        """
        Close this window.
        """
        if window == self.active_window:
            self.close_active_window()
        else:
            original_active_window = self.active_window
            self.close_active_window()
            self.active_window = original_active_window

    def close_active_window(self):
        """
        Close active window.
        """
        active_split = self._get_active_split()

        # First remove the active window from its split.
        index = active_split.index(self.active_window)
        del active_split[index]

        # Move focus.
        if len(active_split):
            new_active_window = active_split[max(0, index - 1)]
            while isinstance(new_active_window, (HSplit, VSplit)):
                new_active_window = new_active_window[0]
            self.active_window = new_active_window
        else:
            self.active_window = None  # No windows left.

        # When there is exactly on item left, move this back into the parent
        # split. (We don't want to keep a split with one item around -- exept
        # for the root.)
        if len(active_split) == 1 and active_split != self.root:
            parent = self._get_split_parent(active_split)
            index = parent.index(active_split)
            parent[index] = active_split[0]

    def cycle_focus(self):
        """
        Cycle through all windows.
        """
        windows = self.windows()
        new_index = (windows.index(self.active_window) + 1) % len(windows)
        self.active_window = windows[new_index]

    @property
    def has_unsaved_changes(self):
        """
        True when any of the visible buffers in this tab has unsaved changes.
        """
        for w in self.windows():
            if w.editor_buffer.has_unsaved_changes:
                return True
        return False


class WindowArrangement(object):
    def __init__(self, editor):
        self._editor_ref = weakref.ref(editor)

        self.tab_pages = []
        self.active_tab_index = None
        self.editor_buffers = []  # List of EditorBuffer

        self._buffer_index = 0  # Index for generating buffer names.

    @property
    def editor(self):
        """ The Editor instance. """
        return self._editor_ref()

    @property
    def active_tab(self):
        """ The active TabPage or None. """
        if self.active_tab_index is not None:
            return self.tab_pages[self.active_tab_index]

    @property
    def active_editor_buffer(self):
        """ The active EditorBuffer or None. """
        if self.active_tab and self.active_tab.active_window:
            return self.active_tab.active_window.editor_buffer

    def get_editor_buffer_for_location(self, location):
        """
        Return the `EditorBuffer` for this location.
        When this file was not yet loaded, return None
        """
        for eb in self.editor_buffers:
            if eb.location == location:
                return eb

    def get_editor_buffer_for_buffer_name(self, buffer_name):
        """
        Return the `EditorBuffer` for this buffer_name.
        When not found, return None
        """
        for eb in self.editor_buffers:
            if eb.buffer_name == buffer_name:
                return eb

    def close_window(self):
        """
        Close active window of active tab.
        """
        self.active_tab.close_active_window()

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def close_tab(self):
        """
        Close active tab.
        """
        if len(self.tab_pages) > 1:  # Cannot close last tab.
            del self.tab_pages[self.active_tab_index]
            self.active_tab_index = max(0, self.active_tab_index - 1)

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def hsplit(self, location=None, new=False, text=None):
        """ Split horizontally. """
        assert location is None or text is None or new is False  # Don't pass two of them.

        if location or text or new:
            editor_buffer = self._get_or_create_editor_buffer(location=location, text=text)
        else:
            editor_buffer = None
        self.active_tab.hsplit(editor_buffer)

    def vsplit(self, location=None, new=False, text=None):
        """ Split vertically. """
        assert location is None or text is None or new is False  # Don't pass two of them.

        if location or text or new:
            editor_buffer = self._get_or_create_editor_buffer(location=location, text=text)
        else:
            editor_buffer = None
        self.active_tab.vsplit(editor_buffer)

    def keep_only_current_window(self):
        """
        Close all other windows, except the current one.
        """
        self.tab_pages = [TabPage(self.active_tab.active_window)]
        self.active_tab_index = 0

    def cycle_focus(self):
        """ Focus next visible window. """
        self.active_tab.cycle_focus()

    def show_editor_buffer(self, editor_buffer):
        """
        Show this EditorBuffer in the current window.
        """
        self.active_tab.show_editor_buffer(editor_buffer)

        # Clean up buffers.
        self._auto_close_new_empty_buffers()

    def go_to_next_buffer(self, _previous=False):
        """
        Open next buffer in active window.
        """
        if self.active_editor_buffer:
            # Find the active opened buffer.
            index = self.editor_buffers.index(self.active_editor_buffer)

            # Get index of new buffer.
            if _previous:
                new_index = (len(self.editor_buffers) + index - 1) % len(self.editor_buffers)
            else:
                new_index = (index + 1) % len(self.editor_buffers)

            # Open new buffer in active tab.
            self.active_tab.show_editor_buffer(self.editor_buffers[new_index])

            # Clean up buffers.
            self._auto_close_new_empty_buffers()

    def go_to_previous_buffer(self):
        """
        Open the previous buffer in the active window.
        """
        self.go_to_next_buffer(_previous=True)

    def go_to_next_tab(self):
        """
        Focus the next tab.
        """
        self.active_tab_index = (self.active_tab_index + 1) % len(self.tab_pages)

    def go_to_previous_tab(self):
        """
        Focus the previous tab.
        """
        self.active_tab_index = (self.active_tab_index - 1 +
                                 len(self.tab_pages)) % len(self.tab_pages)

    def go_to_buffer(self, buffer_name):
        """
        Go to one of the open buffers.
        """
        assert isinstance(buffer_name, string_types)

        for i, eb in enumerate(self.editor_buffers):
            if (eb.location == buffer_name or
                    (buffer_name.isdigit() and int(buffer_name) == i)):
                self.show_editor_buffer(eb)
                break

    def _add_editor_buffer(self, editor_buffer, show_in_current_window=False):
        """
        Insert this new buffer in the list of buffers, right after the active
        one.
        """
        assert isinstance(editor_buffer, EditorBuffer) and editor_buffer not in self.editor_buffers

        # Add to list of EditorBuffers
        eb = self.active_editor_buffer
        if eb is None:
            self.editor_buffers.append(editor_buffer)
        else:
            # Append right after the currently active one.
            try:
                index = self.editor_buffers.index(self.active_editor_buffer)
            except ValueError:
                index = 0
            self.editor_buffers.insert(index, editor_buffer)

        # When there are no tabs/windows yet, create one for this buffer.
        if self.tab_pages == []:
            self.tab_pages.append(TabPage(Window(editor_buffer)))
            self.active_tab_index = 0

        # To be shown?
        if show_in_current_window and self.active_tab:
            self.active_tab.show_editor_buffer(editor_buffer)

        # Add buffer to CLI.
        self.editor.cli.add_buffer(editor_buffer.buffer_name, editor_buffer.buffer)

        # Start reporter.
        self.editor.run_reporter_for_editor_buffer(editor_buffer)

    def _get_or_create_editor_buffer(self, location=None, text=None):
        """
        Given a location, return the `EditorBuffer` instance that we have if
        the file is already open, or create a new one.

        When location is None, this creates a new buffer.
        """
        assert location is None or text is None  # Don't pass two of them.
        assert location is None or isinstance(location, string_types)

        def new_name():
            """ Generate name for new buffer. """
            self._buffer_index += 1
            return 'buffer-%i' % self._buffer_index

        if location is None:
            # Create and add an empty EditorBuffer
            eb = EditorBuffer(self.editor, new_name(), text=text)
            self._add_editor_buffer(eb)

            return eb
        else:
            # When a location is given, first look whether the file was already
            # opened.
            eb = self.get_editor_buffer_for_location(location)

            # Not found? Create one.
            if eb is None:
                # Create and add EditorBuffer
                eb = EditorBuffer(self.editor, new_name(), location)
                self._add_editor_buffer(eb)

                return eb
            else:
                # Found! Return it.
                return eb

    def open_buffer(self, location=None, show_in_current_window=False):
        """
        Open/create a file, load it, and show it in a new buffer.
        """
        eb = self._get_or_create_editor_buffer(location)

        if show_in_current_window:
            self.show_editor_buffer(eb)

    def _auto_close_new_empty_buffers(self):
        """
        When there are new, empty buffers open. (Like, created when the editor
        starts without any files.) These can be removed at the point when there
        is no more window showing them.

        This should be called every time when a window is closed, or when the
        content of a window is replcaed by something new.
        """
        # Get all visible EditorBuffers
        ebs = set()
        for t in self.tab_pages:
            ebs |= set(t.visible_editor_buffers())

        # Remove empty/new buffers that are hidden.
        for eb in self.editor_buffers[:]:
            if eb.is_new and not eb.location and eb not in ebs and eb.buffer.text == '':
                self.editor_buffers.remove(eb)

    def close_buffer(self):
        """
        Close current buffer. When there are other windows showing the same
        buffer, they are closed as well. When no windows are left, the previous
        buffer or an empty buffer is shown.
        """
        eb = self.active_editor_buffer

        # Remove this buffer.
        index = self.editor_buffers.index(eb)
        self.editor_buffers.remove(eb)

        # Close the active window.
        self.active_tab.close_active_window()

        # Close all the windows that still have this buffer open.
        for i, t in enumerate(self.tab_pages[:]):
            t.close_editor_buffer(eb)

            # Remove tab when there are no windows left.
            if t.window_count() == 0:
                self.tab_pages.remove(t)

                if i >= self.active_tab_index:
                    self.active_tab_index = max(0, self.active_tab_index - 1)

        # When there are no windows/tabs left, create a new tab.
        if len(self.tab_pages) == 0:
            self.active_tab_index = None

            if len(self.editor_buffers) > 0:
                # Open the previous buffer.
                new_index = (len(self.editor_buffers) + index - 1) % len(self.editor_buffers)
                eb = self.editor_buffers[new_index]

                # Create a window for this buffer.
                self.tab_pages.append(TabPage(Window(eb)))
                self.active_tab_index = 0
            else:
                # Create a new buffer. (This will also create the window
                # automatically.)
                eb = self._get_or_create_editor_buffer()

    def create_tab(self, location=None):
        """
        Create a new tab page.
        """
        eb = self._get_or_create_editor_buffer(location)

        self.tab_pages.insert(self.active_tab_index + 1, TabPage(Window(eb)))
        self.active_tab_index += 1

    def list_open_buffers(self):
        """
        Return a `OpenBufferInfo` list that gives information about the
        open buffers.
        """
        active_eb = self.active_editor_buffer
        visible_ebs = self.active_tab.visible_editor_buffers()

        def make_info(i, eb):
            return OpenBufferInfo(
                index=i,
                editor_buffer=eb,
                is_active=(eb == active_eb),
                is_visible=(eb in visible_ebs))

        return [make_info(i, eb) for i, eb in enumerate(self.editor_buffers)]


class OpenBufferInfo(object):
    """
    Information about an open buffer, returned by
    `WindowArrangement.list_open_buffers`.
    """
    def __init__(self, index, editor_buffer, is_active, is_visible):
        self.index = index
        self.editor_buffer = editor_buffer
        self.is_active = is_active
        self.is_visible = is_visible
