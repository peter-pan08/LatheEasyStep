import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep.ui_persistence import update_save_step_button_state
from lathe_easystep.ui_selection import handle_selection_change

# LES-024 Entscheidung (2026-09-14): ungueltige Aktionen kuenftig per
# Buttonzustand verhindern statt nur beim Klick zu melden. Erster,
# klarster Fall: "Step speichern" ist nur aktiv, wenn eine Operation in
# der Step-Liste ausgewaehlt ist (vorher: Klick jederzeit moeglich, dann
# eine Warnung "message.step.select_operation_first").


class _FakeButton:
    def __init__(self):
        self.enabled = None

    def setEnabled(self, value):
        self.enabled = bool(value)


def test_button_disabled_without_a_selected_operation():
    handler = SimpleNamespace(btn_save_step=_FakeButton(), _selected_operation_index=lambda: -1)
    update_save_step_button_state(handler)
    assert handler.btn_save_step.enabled is False


def test_button_enabled_with_a_selected_operation():
    handler = SimpleNamespace(btn_save_step=_FakeButton(), _selected_operation_index=lambda: 0)
    update_save_step_button_state(handler)
    assert handler.btn_save_step.enabled is True


def test_missing_button_does_not_raise():
    handler = SimpleNamespace(btn_save_step=None, _selected_operation_index=lambda: 0)
    update_save_step_button_state(handler)  # darf nicht werfen


def test_exception_while_reading_selection_is_swallowed():
    def _raise():
        raise RuntimeError("boom")

    handler = SimpleNamespace(btn_save_step=_FakeButton(), _selected_operation_index=_raise)
    update_save_step_button_state(handler)  # darf nicht werfen
    assert handler.btn_save_step.enabled is None  # unveraendert, kein Absturz


def _selection_handler(*, row, operations, selected_index):
    calls = []
    handler = SimpleNamespace(
        model=SimpleNamespace(operations=operations),
        list_ops=None,
        tab_params=None,
        _runtime=RuntimeState(),
        _dirty=DirtyState(),
        _startup_complete=False,
        _op_row_user_selected=False,
        _active_form_operation_index=-1,
        _selected_operation_index=lambda: selected_index,
        _update_save_step_button_state=lambda: calls.append("called"),
        _load_params_to_form=lambda op: None,
        _refresh_preview=lambda: None,
    )
    handle_selection_change(handler, row)
    return calls


def test_handle_selection_change_updates_button_state_for_a_valid_row():
    calls = _selection_handler(row=0, operations=[object()], selected_index=0)
    assert calls == ["called"]


def test_handle_selection_change_updates_button_state_when_selection_becomes_invalid():
    """Der fruehe Rueckgabepfad (row ausserhalb der Operationsliste, z. B.
    nach dem Loeschen der letzten Operation) darf das Update nicht
    ueberspringen - genau dieser Fall soll den Button sperren."""
    calls = _selection_handler(row=-1, operations=[], selected_index=-1)
    assert calls == ["called"]
