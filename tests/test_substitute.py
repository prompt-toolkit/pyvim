from pyvim.commands.handler import handle_command

sample_text = """
Roses are red,
    Violets are blue,
Sugar is sweet,
    And so are you.
""".lstrip()

def given_sample_text(editor_buffer, text=None):
    editor = editor_buffer.editor
    editor.window_arrangement._add_editor_buffer(editor_buffer)
    editor_buffer.buffer.text = text or sample_text
    editor.sync_with_prompt_toolkit()


def given_cursor_position(editor_buffer, line_number, column=0):
    editor_buffer.buffer.cursor_position = \
        editor_buffer.buffer.document.translate_row_col_to_index(line_number - 1, column)


def test_substitute_current_line(editor, editor_buffer):
    given_sample_text(editor_buffer)
    given_cursor_position(editor_buffer, 2)

    handle_command(editor, ':s/s are/ is')

    assert 'Roses are red,' in editor_buffer.buffer.text
    assert 'Violet is blue,' in editor_buffer.buffer.text
    assert 'And so are you.' in editor_buffer.buffer.text
    assert editor_buffer.buffer.cursor_position \
        == editor_buffer.buffer.text.index('Violet')


def test_substitute_single_line(editor, editor_buffer):
    given_sample_text(editor_buffer)
    given_cursor_position(editor_buffer, 1)

    handle_command(editor, ':2s/s are/ is')

    assert 'Roses are red,' in editor_buffer.buffer.text
    assert 'Violet is blue,' in editor_buffer.buffer.text
    assert 'And so are you.' in editor_buffer.buffer.text
    assert editor_buffer.buffer.cursor_position \
        == editor_buffer.buffer.text.index('Violet')


def test_substitute_range(editor, editor_buffer):
    given_sample_text(editor_buffer)
    given_cursor_position(editor_buffer, 1)

    handle_command(editor, ':1,3s/s are/ is')

    assert 'Rose is red,' in editor_buffer.buffer.text
    assert 'Violet is blue,' in editor_buffer.buffer.text
    assert 'And so are you.' in editor_buffer.buffer.text
    # FIXME: vim would have set the cursor position on last substituted line
    #        but we set the cursor position on the end_range even when there
    #        is not substitution there
    # assert editor_buffer.buffer.cursor_position \
    #    == editor_buffer.buffer.text.index('Violet')
    assert editor_buffer.buffer.cursor_position \
        == editor_buffer.buffer.text.index('Sugar')


def test_substitute_range_boundaries(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet\n' * 4)

    handle_command(editor, ':2,3s/Violet/Rose')

    assert 'Violet\nRose\nRose\nViolet\n' in editor_buffer.buffer.text


def test_substitute_from_search_history(editor, editor_buffer):
    given_sample_text(editor_buffer)
    editor.application.current_search_state.text = 'blue'

    handle_command(editor, ':1,3s//pretty')
    assert 'Violets are pretty,' in editor_buffer.buffer.text


def test_substitute_from_substitute_search_history(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet is Violet\n')

    handle_command(editor, ':s/Violet/Rose')
    assert 'Rose is Violet' in editor_buffer.buffer.text

    handle_command(editor, ':s//Lily')
    assert 'Rose is Lily' in editor_buffer.buffer.text


def test_substitute_with_repeat_last_substitution(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet is Violet\n')
    editor.application.current_search_state.text = 'Lily'

    handle_command(editor, ':s/Violet/Rose')
    assert 'Rose is Violet' in editor_buffer.buffer.text

    handle_command(editor, ':s')
    assert 'Rose is Rose' in editor_buffer.buffer.text


def test_substitute_without_replacement_text(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet Violet Violet \n')
    editor.application.current_search_state.text = 'Lily'

    handle_command(editor, ':s/Violet/')
    assert ' Violet Violet \n' in editor_buffer.buffer.text

    handle_command(editor, ':s/Violet')
    assert '  Violet \n' in editor_buffer.buffer.text

    handle_command(editor, ':s/')
    assert '   \n' in editor_buffer.buffer.text


def test_substitute_with_repeat_last_substitution_without_previous_substitution(editor, editor_buffer):
    original_text = 'Violet is blue\n'
    given_sample_text(editor_buffer, original_text)

    handle_command(editor, ':s')
    assert original_text in editor_buffer.buffer.text

    editor.application.current_search_state.text = 'blue'

    handle_command(editor, ':s')
    assert 'Violet is \n' in editor_buffer.buffer.text


def test_substitute_flags_empty_flags(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet is Violet\n')
    handle_command(editor, ':s/Violet/Rose/')
    assert 'Rose is Violet' in editor_buffer.buffer.text


def test_substitute_flags_g(editor, editor_buffer):
    given_sample_text(editor_buffer, 'Violet is Violet\n')
    handle_command(editor, ':s/Violet/Rose/g')
    assert 'Rose is Rose' in editor_buffer.buffer.text
