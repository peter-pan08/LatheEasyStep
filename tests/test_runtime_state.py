"""Direct unit coverage for RuntimeState (LES-052). Qt-free.

Unlike DirtyState/ToolTableState, RuntimeState holds no logic of its own -
all nine fields are plain reentrancy-guard/loading flags whose check-set-
reset behaviour lives at each call site (ui_flow.py/ui_persistence.py/
ui_selection.py/ui_visibility.py/lathe_easystep_handler.py), unchanged by
this encapsulation. These tests exist to pin down the field set and default
values, not to exercise behaviour."""

from lathe_easystep.runtime_state import RuntimeState


def test_all_nine_fields_default_to_false():
    state = RuntimeState()
    assert state.loading_step is False
    assert state.deleting is False
    assert state.saving_step is False
    assert state.saving_changes is False
    assert state.moving_up is False
    assert state.moving_down is False
    assert state.generating_gcode is False
    assert state.creating_new_program is False
    assert state.ui_loading is False


def test_fields_are_independent():
    state = RuntimeState()
    state.deleting = True
    assert state.moving_up is False
    assert state.ui_loading is False


def test_constructor_accepts_keyword_overrides():
    state = RuntimeState(ui_loading=True, generating_gcode=True)
    assert state.ui_loading is True
    assert state.generating_gcode is True
    assert state.deleting is False
