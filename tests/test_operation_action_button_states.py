from types import SimpleNamespace

from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.model import Operation, OpType
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep.ui_flow import handle_move_down, handle_move_up
from lathe_easystep.ui_selection import (
    handle_selection_change,
    update_operation_action_button_states,
)


class _Button:
    def __init__(self):
        self.enabled = None

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


def _handler(operations, selected):
    return SimpleNamespace(
        model=SimpleNamespace(operations=operations),
        btn_delete=_Button(),
        btn_move_up=_Button(),
        btn_move_down=_Button(),
        _selected_operation_index=lambda: selected,
        _runtime=RuntimeState(),
    )


def _states(handler):
    return (
        handler.btn_delete.enabled,
        handler.btn_move_up.enabled,
        handler.btn_move_down.enabled,
    )


def test_no_selection_disables_all_operation_actions():
    handler = _handler([], -1)
    update_operation_action_button_states(handler)
    assert _states(handler) == (False, False, False)


def test_missing_action_buttons_are_supported_during_lazy_ui_loading():
    """During lazy UI loading, some action buttons may not exist yet
    (None) while others already do. Buttons that already exist must still
    receive the correct real state; missing ones must be skipped without
    raising - a mere "no crash" check would miss a bug where an existing
    button is silently left at the wrong state."""
    operations = [Operation(OpType.FACE, {}), Operation(OpType.FACE, {})]
    handler = SimpleNamespace(
        model=SimpleNamespace(operations=operations),
        btn_delete=_Button(),
        btn_move_up=None,
        btn_move_down=_Button(),
        _selected_operation_index=lambda: 0,
    )
    update_operation_action_button_states(handler)
    assert handler.btn_delete.enabled is True
    assert handler.btn_move_down.enabled is True
    assert handler.btn_move_up is None


def test_program_header_cannot_be_deleted_or_reordered():
    operations = [Operation(OpType.PROGRAM_HEADER, {})]
    handler = _handler(operations, 0)
    update_operation_action_button_states(handler)
    assert _states(handler) == (False, False, False)


def test_first_step_cannot_move_above_program_header():
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.FACE, {}),
        Operation(OpType.DRILL, {}),
    ]
    handler = _handler(operations, 1)
    update_operation_action_button_states(handler)
    assert _states(handler) == (True, False, True)


def test_middle_and_last_step_states_follow_list_boundaries():
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.FACE, {}),
        Operation(OpType.DRILL, {}),
        Operation(OpType.GROOVE, {}),
    ]
    middle = _handler(operations, 2)
    update_operation_action_button_states(middle)
    assert _states(middle) == (True, True, True)

    last = _handler(operations, 3)
    update_operation_action_button_states(last)
    assert _states(last) == (True, True, False)


class _StepList:
    def __init__(self, selected, count):
        self._selected = selected
        self._count = count

    def is_bound(self):
        return True

    def currentRow(self):
        return self._selected

    def count(self):
        return self._count


class _Model:
    def __init__(self, operations):
        self.operations = operations
        self.moves = []

    def move_up(self, index):
        self.moves.append(("up", index))

    def move_down(self, index):
        self.moves.append(("down", index))


def _move_handler(operations, selected):
    model = _Model(operations)
    return SimpleNamespace(
        model=model,
        list_ops=_StepList(selected, len(operations)),
        _runtime=RuntimeState(),
        _swap_dirty_operation_indices=lambda *args: None,
        _mark_program_structure_dirty=lambda: None,
        _refresh_operation_list=lambda **kwargs: None,
        _renumber_operations=lambda: None,
        _refresh_preview=lambda: None,
    )


def test_handler_guards_also_prevent_moving_across_program_header():
    operations = [Operation(OpType.PROGRAM_HEADER, {}), Operation(OpType.FACE, {})]
    handler = _move_handler(operations, 1)
    handle_move_up(handler)
    assert handler.model.moves == []

    handler = _move_handler(operations, 0)
    handle_move_down(handler)
    assert handler.model.moves == []


def test_selection_change_updates_action_buttons_on_invalid_row():
    calls = []
    handler = SimpleNamespace(
        model=SimpleNamespace(operations=[]),
        list_ops=None,
        tab_params=None,
        _runtime=RuntimeState(),
        _dirty=DirtyState(),
        _startup_complete=False,
        _op_row_user_selected=False,
        _active_form_operation_index=-1,
        _update_save_step_button_state=lambda: None,
        _update_operation_action_button_states=lambda: calls.append("updated"),
    )

    handle_selection_change(handler, -1)

    assert calls == ["updated"]
