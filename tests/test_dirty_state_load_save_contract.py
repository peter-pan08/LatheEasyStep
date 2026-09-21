"""LES-052 Abnahme: Dirty-State nach Laden/Speichern - dedizierter Nachweis.

Bisherige Abdeckung (siehe test_dirty_state.py fuer die reine `DirtyState`-
Arithmetik und test_step_path_persistence.py fuer Step-bezogene Save/Load-
Mechanik) prueft nirgends END-ZU-ENDE, mit einem REALEN `handler._dirty`
(kein Stub von `_clear_dirty_state()`/`_clear_program_dirty()` selbst), was
ein erfolgreicher bzw. fehlgeschlagener "Programm laden"/"Programm
speichern"-Aufruf tatsaechlich mit dem Dirty-State macht. Diese Datei
schliesst genau diese Luecke.

Tatsaechlich vorgesehenes Verhalten (aus Code-Audit, nicht angenommen):
- "Programm laden" (`handle_load_program`) ERSETZT `model.operations`
  vollstaendig durch das geladene Programm. Jeder vorherige Dirty-Zustand
  (Programm- UND Step-Ebene) bezog sich auf das ALTE, jetzt verworfene
  Programm und wird deshalb bei Erfolg vollstaendig geleert
  (`_clear_dirty_state()`) - bereits so dokumentiert in CHANGELOG.md
  (LES-025-Audit 2026-09-xx zu `_mark_dirty`-Aufrufstellen).
- "Programm speichern" (`handle_save_program`) schreibt den AKTUELLEN
  Operationszustand vollstaendig in die .lse-Datei und muss danach
  mindestens extern sichtbar "sauber" sein (`has_unsaved_changes() is
  False`).
- Ein fehlgeschlagenes Laden/Speichern (Exception vor dem jeweiligen
  Clear-Aufruf) darf den Dirty-State nicht anfassen - insbesondere darf
  ein vorher bestehender "dirty"-Zustand NICHT stillschweigend auf
  "sauber" fallen, nur weil der Vorgang fehlgeschlagen ist.

Bewusst NICHT hier getestet (bereits andernorts abgedeckt):
- Die reine `DirtyState`-Indexarithmetik: test_dirty_state.py.
- "Step speichern" raeumt die unlinked-structure-dirty-Sonderregel auf:
  test_step_path_persistence.py::
  test_save_step_clears_unlinked_structure_dirty_after_new_step_save.
- Ungueltige Step-/Programmversionen zeigen eine Warnung statt einer
  unbehandelten Exception: test_format_versioning.py.

Echter Fund beim Audit 2026-09-20 (siehe Tests am Ende dieser Datei,
`test_load_step_into_*`): "Step laden" (`handle_load_step()`/
`_insert_loaded_operation()`, `lathe_easystep/ui_persistence.py`) rief nach
erfolgreichem Einfuegen `handler._clear_dirty_state()` auf und loeschte
damit faelschlich JEDEN bestehenden Dirty-Zustand - nicht nur den des neu
eingefuegten Steps. Das Laden eines Steps in ein bereits offenes Programm
ist eine Strukturaenderung DIESES Programms, genau wie "Operation
hinzufuegen" (`handle_add_operation()`), das korrekt nur
`_mark_program_structure_dirty()` aufruft, ohne bestehenden Dirty-Zustand
zu beruehren. Fix: `handle_load_step()` markiert jetzt ebenso nur die
Strukturaenderung, statt den gesamten Zustand zu leeren."""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.model import Operation, OpType
from lathe_easystep.persistence import step_data_to_operation
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep_handler import HandlerClass


class _DummySettings:
    def __init__(self):
        self._store = {}

    def value(self, key, default=None, type=None):
        return self._store.get(key, default)

    def setValue(self, key, value):
        self._store[key] = value


def _make_bare_handler():
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    handler._runtime = RuntimeState()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._dialog_start_dir = lambda *a, **k: ""
    handler._remember_dialog_path = lambda *a, **k: None
    sys.modules["qtpy.QtCore"].QSettings = lambda: _DummySettings()
    return handler


# ---------------------------------------------------------------------------
# "Programm laden" - Erfolg raeumt den kompletten (Programm- UND Step-)
# Dirty-Zustand auf, weil das gesamte Modell ersetzt wird.
# ---------------------------------------------------------------------------

def test_load_program_success_leaves_dirty_state_fully_clean(tmp_path):
    from lathe_easystep import ui_persistence

    sample = tmp_path / "example.lse"
    sample.write_text(json.dumps({
        "version": 2,
        "header": {"program_name": "Demo"},
        "meta": {},
        "operations": [
            {"op_type": "program_header", "version": 2, "params": {"program_name": "Demo"}, "path": []},
            {"op_type": "face", "version": 2, "params": {"tool": 1}, "path": []},
        ],
    }))

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(sample), None))}
    )
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(lambda *a: None)
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"critical must not fire: {a}"))
    )

    handler = _make_bare_handler()
    handler.model = type("M", (), {"operations": []})()
    handler.model.operations = []
    handler.model.add_operation = lambda op: handler.model.operations.append(op)
    handler._op_row_user_selected = False
    handler._active_form_operation_index = -1
    handler._load_program_header_to_form = lambda header: None
    handler._current_program_path = None
    handler._current_gcode_path = None
    handler._step_data_to_operation = lambda data: step_data_to_operation(data)
    handler._rebuild_all_operation_geometry = lambda: None
    handler._tool_table = type("T", (), {"tools": {}})()
    handler._populate_tool_combos = lambda tools: None
    handler._auto_load_tool_table = lambda: None
    handler._refresh_operation_list = lambda select_index=0: None
    handler._refresh_preview = lambda: None
    handler._handle_selection_change = lambda idx: None
    handler.list_ops = None

    # Das vorher geoeffnete (jetzt zu ersetzende) Programm hatte ungespeicherte
    # Aenderungen auf Programm- UND Step-Ebene.
    handler._dirty = DirtyState(operation_indices={0}, program_dirty=True, program_header_dirty=True)

    handler._handle_load_program()

    assert handler._dirty.operation_indices == set()
    assert handler._has_unsaved_changes() is False


def test_load_program_failure_does_not_clear_preexisting_dirty_state(tmp_path):
    """Ungueltiges Programm (hier: fehlende Version, siehe
    test_format_versioning.py Punkt 3) muss ueber den vorhandenen
    Warnungs-Dialog abgelehnt werden, OHNE den Dirty-Zustand des noch
    offenen, tatsaechlich ungespeicherten Programms zu beruehren."""
    from lathe_easystep import ui_persistence

    broken = tmp_path / "broken.lse"
    broken.write_text(json.dumps({"header": {}, "operations": [], "meta": {}}))

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(broken), None))}
    )
    warnings = []
    sys.modules["qtpy.QtWidgets"].QMessageBox.warning = staticmethod(lambda *a: warnings.append(a))
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"critical must not fire: {a}"))
    )

    handler = _make_bare_handler()
    handler.model = type("M", (), {"operations": []})()
    handler.model.operations = []

    handler._dirty = DirtyState(operation_indices={2}, program_dirty=True, program_header_dirty=True)

    handler._handle_load_program()

    assert len(warnings) == 1
    assert handler._dirty.operation_indices == {2}
    assert handler._dirty.program_dirty is True
    assert handler._has_unsaved_changes() is True


# ---------------------------------------------------------------------------
# LES-052 Abschnitt 3 Fund 1 (Audit 2026-09-20): "Programm laden" muss
# atomar sein. Vorher wurde `handler.model.operations` schon geleert/neu
# befuellt, WAEHREND die einzelnen Operationen noch geparst wurden - ein
# Fehler in einer SPAETEREN Operation (`_step_data_to_operation()` wirft
# z. B. bei einem strukturell ungueltigen `path`-Eintrag, was
# `parse_program_payload()`s reine Zahlen-Endlichkeitspruefung nicht
# abdeckt) liess das vorherige, ggf. ungespeicherte Programm durch einen
# kaputten Teilimport ersetzt zurueck. Diese Tests bauen genau dieses
# Szenario nach: ein gueltiges Programm ist offen (einmal sauber, einmal
# mit echten ungespeicherten Aenderungen), das zu ladende Programm hat eine
# gueltige erste und eine STRUKTURELL ungueltige dritte Operation.
# ---------------------------------------------------------------------------

def _broken_program_payload():
    return {
        "version": 2,
        "header": {"program_name": "Kaputt"},
        "meta": {},
        "operations": [
            {"op_type": "program_header", "version": 2, "params": {"program_name": "Kaputt"}, "path": []},
            {"op_type": "face", "version": 2, "params": {"tool": 1}, "path": []},
            # strukturell ungueltig: path-Eintrag ist kein X/Z-Punkt - wird
            # von parse_program_payload()s Zahlen-Endlichkeitspruefung NICHT
            # erkannt, sondern erst hier in _step_data_to_operation().
            {"op_type": "face", "version": 2, "params": {"tool": 2}, "path": [["oops"]]},
        ],
    }


def _make_load_program_failure_handler(tmp_path, *, existing_dirty):
    broken = tmp_path / "broken_later_op.lse"
    broken.write_text(json.dumps(_broken_program_payload()))

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(broken), None))}
    )
    criticals = []
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(lambda *a: criticals.append(a))
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"information must not fire: {a}"))
    )

    handler = _make_bare_handler()
    existing_op = Operation(OpType.FACE, params={"tool": 9, "comment": "WICHTIGE UNGESICHERTE AENDERUNG"}, path=[])
    handler.model = type("M", (), {"operations": [existing_op]})()
    handler.model.add_operation = lambda op: handler.model.operations.append(op)
    handler._op_row_user_selected = False
    handler._active_form_operation_index = -1
    handler._load_program_header_to_form = lambda header: None
    handler._current_program_path = "/tmp/still_the_old_program.lse"
    handler._current_gcode_path = None
    handler._step_data_to_operation = lambda data: step_data_to_operation(data)
    handler._rebuild_all_operation_geometry = lambda: None
    handler._tool_table = type("T", (), {"tools": {}})()
    handler._populate_tool_combos = lambda tools: None
    handler._auto_load_tool_table = lambda: None
    handler._refresh_operation_list = lambda select_index=0: None
    handler._refresh_preview = lambda: None
    handler._handle_selection_change = lambda idx: None
    handler.list_ops = None
    handler._dirty = existing_dirty
    return handler, existing_op, criticals


def test_load_program_failure_in_later_operation_leaves_clean_program_untouched(tmp_path):
    handler, existing_op, criticals = _make_load_program_failure_handler(
        tmp_path, existing_dirty=DirtyState()
    )

    handler._handle_load_program()

    assert len(criticals) == 1
    assert handler.model.operations == [existing_op]
    assert handler._current_program_path == "/tmp/still_the_old_program.lse"
    assert handler._has_unsaved_changes() is False


def test_load_program_failure_in_later_operation_leaves_dirty_program_untouched(tmp_path):
    original_dirty = DirtyState(operation_indices={0}, program_dirty=True, program_header_dirty=True)
    handler, existing_op, criticals = _make_load_program_failure_handler(
        tmp_path, existing_dirty=original_dirty
    )

    handler._handle_load_program()

    assert len(criticals) == 1
    assert handler.model.operations == [existing_op]
    assert handler.model.operations[0].params.get("comment") == "WICHTIGE UNGESICHERTE AENDERUNG"
    assert handler._current_program_path == "/tmp/still_the_old_program.lse"
    assert handler._dirty.operation_indices == {0}
    assert handler._dirty.program_dirty is True
    assert handler._dirty.program_header_dirty is True
    assert handler._has_unsaved_changes() is True


# ---------------------------------------------------------------------------
# "Programm speichern" - Erfolg macht den Programm-Dirty-Zustand extern
# sauber; ein Fehlschlag darf das nicht vortaeuschen.
# ---------------------------------------------------------------------------

def test_save_program_success_clears_program_dirty(tmp_path):
    handler = _make_bare_handler()
    program_path = tmp_path / "prog.lse"
    written = []
    handler._write_program_file = lambda path: written.append(path)
    handler._normalized_file_path = lambda path: str(path) if path else None

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getSaveFileName": staticmethod(lambda *a, **k: (str(program_path), None))}
    )
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(lambda *a: None)
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"critical must not fire: {a}"))
    )

    handler._dirty = DirtyState(program_dirty=True, program_header_dirty=True)
    handler.label_dirty_status = None
    handler.btn_save_changes = None

    handler._handle_save_program()

    assert written == [str(program_path)]
    assert handler._dirty.program_dirty is False
    assert handler._has_unsaved_changes() is False


def test_save_program_failure_does_not_clear_dirty_state(tmp_path):
    """Schlaegt das eigentliche Schreiben fehl (z. B. Datenträger/Rechte-
    Fehler), faengt `handle_save_program()` das ueber die aeussere
    Fehlerbehandlung ab und darf den Dirty-Zustand nicht anfassen - sonst
    wuerde ein fehlgeschlagenes Speichern faelschlich als erfolgreich
    (sauber) angezeigt."""
    handler = _make_bare_handler()
    program_path = tmp_path / "prog.lse"

    def _boom(path):
        raise OSError("disk full")

    handler._write_program_file = _boom
    handler._normalized_file_path = lambda path: str(path) if path else None

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getSaveFileName": staticmethod(lambda *a, **k: (str(program_path), None))}
    )
    criticals = []
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(lambda *a: criticals.append(a))
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"information must not fire: {a}"))
    )

    handler._dirty = DirtyState(program_dirty=True, program_header_dirty=True)
    handler.label_dirty_status = None
    handler.btn_save_changes = None

    handler._handle_save_program()

    assert len(criticals) == 1
    assert handler._dirty.program_dirty is True
    assert handler._has_unsaved_changes() is True


# ---------------------------------------------------------------------------
# "Step laden" (in ein bereits offenes Programm einfuegen) - Regression fuer
# den beim Audit 2026-09-20 gefundenen Fehler.
# ---------------------------------------------------------------------------

def _make_load_step_handler(tmp_path, *, existing_ops):
    step_path = tmp_path / "new.step.json"
    step_path.write_text(
        json.dumps({"version": 1, "op_type": "face", "params": {"tool": 1}, "path": []}),
        encoding="utf-8",
    )
    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(step_path), None))}
    )

    handler = _make_bare_handler()
    handler._step_data_to_operation = lambda data: step_data_to_operation(data)
    handler.model = type("M", (), {"operations": list(existing_ops)})()
    handler.model.update_geometry = lambda op: None
    handler.model.add_operation = lambda op: handler.model.operations.append(op)
    handler._refresh_operation_list = lambda select_index=None: None
    handler._refresh_preview = lambda: None
    handler._update_parting_contour_choices = lambda: None
    handler._update_parting_ready_state = lambda *a, **k: None
    handler._setup_groove_tab_ui = lambda: None
    handler._handle_selection_change = lambda idx: None
    handler.list_ops = None
    return handler


def test_load_step_into_dirty_program_preserves_preexisting_dirty_state(tmp_path):
    existing_op = Operation(OpType.FACE, params={"tool": 2}, path=[])
    handler = _make_load_step_handler(tmp_path, existing_ops=[existing_op])

    # Bereits vorhandene, mit "Step laden" nichts zu tun habende
    # ungespeicherte Aenderungen (Header + Step 0).
    handler._dirty = DirtyState(operation_indices={0}, program_dirty=True, program_header_dirty=True)

    handler._handle_load_step()

    assert 0 in handler._dirty.operation_indices
    assert handler._dirty.program_header_dirty is True
    assert handler._has_unsaved_changes() is True


def test_load_step_into_clean_program_marks_program_dirty(tmp_path):
    existing_op = Operation(OpType.FACE, params={"tool": 2}, path=[])
    handler = _make_load_step_handler(tmp_path, existing_ops=[existing_op])
    handler._dirty = DirtyState()

    handler._handle_load_step()

    assert len(handler.model.operations) == 2
    assert handler._has_unsaved_changes() is True
