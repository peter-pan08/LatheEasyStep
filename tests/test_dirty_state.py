"""Direct unit coverage for DirtyState (LES-052), independent of the handler
integration exercised in test_dirty_and_messages.py/test_step_double_click.py.
Qt-free - the whole point of extracting this out of the handler."""

from lathe_easystep.dirty_state import DirtyState


def test_mark_program_sets_program_and_header_flags():
    state = DirtyState()
    state.mark(program=True)
    assert state.program_dirty is True
    assert state.program_header_dirty is True
    assert state.program_structure_dirty is False
    assert state.operation_indices == set()


def test_mark_operation_index_only_touches_indices():
    state = DirtyState()
    state.mark(operation_index=2)
    assert state.operation_indices == {2}
    assert state.program_dirty is False


def test_mark_negative_operation_index_is_ignored():
    state = DirtyState()
    state.mark(operation_index=-1)
    assert state.operation_indices == set()


def test_mark_program_structure_sets_structure_and_optional_indices():
    state = DirtyState()
    state.mark_program_structure({1, 3})
    assert state.program_dirty is True
    assert state.program_structure_dirty is True
    assert state.program_header_dirty is False
    assert state.operation_indices == {1, 3}


def test_clear_resets_everything():
    state = DirtyState(operation_indices={1, 2}, program_dirty=True,
                        program_header_dirty=True, program_structure_dirty=True)
    state.clear()
    assert state.operation_indices == set()
    assert state.program_dirty is False
    assert state.program_header_dirty is False
    assert state.program_structure_dirty is False


def test_clear_program_structure_only_recomputes_program_dirty():
    """program_dirty ist abgeleitet: bleibt True, solange header ODER
    structure noch dirty sind, faellt erst auf False, wenn beide es nicht
    mehr sind."""
    state = DirtyState(program_dirty=True, program_header_dirty=True, program_structure_dirty=True)
    state.clear_program(structure=True)
    assert state.program_structure_dirty is False
    assert state.program_header_dirty is True
    assert state.program_dirty is True  # header noch dirty

    state.clear_program(header=True)
    assert state.program_dirty is False


def test_clear_operation_discards_a_single_index_without_touching_others():
    state = DirtyState(operation_indices={1, 2, 3})
    state.clear_operation(2)
    assert state.operation_indices == {1, 3}
    # Ein nicht vorhandener Index darf keinen Fehler ausloesen.
    state.clear_operation(99)
    assert state.operation_indices == {1, 3}


def test_reindex_after_removal_shifts_only_indices_above_the_removed_one():
    """SICHERHEITSFUND 2026-09-13 (siehe dirty_state.py-Docstring): Loeschen
    von Index 1 darf einen dirty markierten Index 2 nicht bei 2 belassen -
    er muss auf 1 nachruecken, um weiterhin auf dieselbe Operation zu zeigen."""
    state = DirtyState(operation_indices={0, 2, 3})
    state.reindex_after_removal(1)
    assert state.operation_indices == {0, 1, 2}


def test_reindex_after_removal_drops_the_removed_index_itself():
    state = DirtyState(operation_indices={1, 2})
    state.reindex_after_removal(1)
    assert state.operation_indices == {1}


def test_reindex_after_insert_shifts_indices_at_or_after_the_insert_point():
    state = DirtyState(operation_indices={0, 2})
    state.reindex_after_insert(0)
    assert state.operation_indices == {1, 3}


def test_swap_indices_exchanges_only_the_two_given_positions():
    state = DirtyState(operation_indices={1, 4})
    state.swap_indices(1, 2)
    assert state.operation_indices == {2, 4}


def test_swap_indices_is_a_no_op_when_neither_side_is_dirty():
    state = DirtyState(operation_indices={5})
    state.swap_indices(1, 2)
    assert state.operation_indices == {5}


def test_mark_all_operations_replaces_the_whole_set_and_marks_structure():
    state = DirtyState(operation_indices={9})
    state.mark_all_operations({1, 2, 3})
    assert state.operation_indices == {1, 2, 3}
    assert state.program_dirty is True
    assert state.program_structure_dirty is True


def test_has_unsaved_changes_true_for_either_program_or_operations():
    assert DirtyState().has_unsaved_changes() is False
    assert DirtyState(program_dirty=True).has_unsaved_changes() is True
    assert DirtyState(operation_indices={0}).has_unsaved_changes() is True
