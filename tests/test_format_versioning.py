"""Tests fuer LES-053 (Programm-/Step-Dateiformat-Versionierung) und die
LES-032-Integration (Werkzeug-Snapshot) als erster realer v1->v2-Anwendungsfall.

Verifiziert:
1. Format v2 ist die aktuelle, zentrale Version (storage.CURRENT_FORMAT_VERSION).
2. v1-Programmdateien laden weiterhin (Migration nach v2), ohne dass die
   Quelldaten dabei veraendert werden.
3. Fehlende Version in einer Programmdatei wird abgelehnt (Programmdateien
   hatten immer schon eine Version - keine Formaterkennung).
4. Unbekannte neuere Version / ungueltiger Versionstyp werden mit
   verstaendlicher eigener Meldung abgelehnt, sowohl fuer Programm- als
   auch fuer Step-Dateien.
5. Eine fehlende Version in einer Step-Datei wird dagegen ausdruecklich als
   historisches Step-v1 behandelt (das einzige je geschriebene Step-Format).
6. Die Migrationskette wendet mehrere Schritte sequenziell an.
7. Laden einer alten Datei schreibt nichts auf die Platte zurueck.
8. Der beim LES-053-Audit gefundene Fehlerpfad in handle_load_step() ist
   behoben: ungueltige/nicht mehr unterstuetzte Step-Daten erzeugen einen
   Warnungsdialog statt einer unbehandelten Exception.
9. Save -> Load -> Save fuer Format v2 ist stabil.
"""
import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep import storage
from lathe_easystep.storage import CURRENT_FORMAT_VERSION, parse_program_payload, parse_step_payload
from lathe_easystep.persistence import build_program_data, operation_to_step_data, step_data_to_operation
from lathe_easystep.model import Operation, OpType
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep_handler import HandlerClass


# ---------------------------------------------------------------------------
# Grundlagen: zentrale Version, v1 laedt weiter, Nicht-Mutation
# ---------------------------------------------------------------------------

def test_build_program_data_writes_the_current_format_version():
    payload = build_program_data([], {}, {})
    assert payload["version"] == CURRENT_FORMAT_VERSION == 2


def test_v1_program_payload_still_loads_and_migrates_to_current_version():
    payload = {
        "version": 1,
        "header": {"program_name": "Alt"},
        "operations": [
            {"op_type": "face", "params": {"tool": 1}, "path": [[10.0, 0.0]], "title": ""},
        ],
        "meta": {},
    }
    header, operations, _program_path, _gcode_path = parse_program_payload(payload, "alt.lse")
    assert header == {"program_name": "Alt"}
    assert len(operations) == 1
    op = step_data_to_operation(operations[0])
    # Migration v1->v2 darf keinen Snapshot nachtraeglich erfinden.
    assert "tool_snapshot" not in op.params


def test_migration_does_not_mutate_the_source_payload():
    original = {"version": 1, "header": {"x": 1.0}, "operations": [{"op_type": "face", "params": {}}], "meta": {}}
    before = copy.deepcopy(original)
    parse_program_payload(original, "x.lse")
    assert original == before


def test_migration_chain_applies_multiple_sequential_steps(monkeypatch):
    """Nur v1->v2 existiert real - hier wird mit einer temporaeren
    zusaetzlichen Fake-Migration v2->v3 bewiesen, dass _migrate_to_current()
    mehrere Schritte NACHEINANDER anwendet statt nur den ersten."""
    monkeypatch.setattr(storage, "CURRENT_FORMAT_VERSION", 3)

    def _fake_v2_to_v3(payload):
        migrated = copy.deepcopy(payload)
        migrated["version"] = 3
        migrated["header"] = dict(migrated.get("header") or {})
        migrated["header"]["_migrated_via_fake_v3"] = True
        return migrated

    monkeypatch.setitem(storage._MIGRATIONS, 2, _fake_v2_to_v3)
    header, _ops, _p, _g = parse_program_payload(
        {"version": 1, "header": {}, "operations": [], "meta": {}}, "x.lse"
    )
    assert header.get("_migrated_via_fake_v3") is True


# ---------------------------------------------------------------------------
# Programmdateien: fehlende/ungueltige/zu neue Version wird abgelehnt
# ---------------------------------------------------------------------------

def test_program_payload_missing_version_is_rejected():
    """Gueltige .lse-Programme hatten schon vor Format v2 immer eine
    Version - anders als bei Step-Dateien wird eine fehlende Version hier
    NICHT stillschweigend angenommen."""
    with pytest.raises(ValueError, match="Formatversion"):
        parse_program_payload({"header": {}, "operations": []}, "no_version.lse")


def test_program_payload_rejects_unknown_newer_version():
    with pytest.raises(ValueError, match="neuer als die unterstützte"):
        parse_program_payload({"version": 99, "header": {}, "operations": []}, "future.lse")


@pytest.mark.parametrize("bad_version", ["2", 1.5, True, None, [2]])
def test_program_payload_rejects_invalid_version_types(bad_version):
    with pytest.raises(ValueError, match="Formatversion"):
        parse_program_payload({"version": bad_version, "header": {}, "operations": []}, "bad.lse")


def test_program_payload_rejects_version_below_one():
    with pytest.raises(ValueError, match="Formatversion"):
        parse_program_payload({"version": 0, "header": {}, "operations": []}, "zero.lse")


# ---------------------------------------------------------------------------
# Step-Dateien: eigener Versions-Envelope, aber Altdateien bleiben ladbar
# ---------------------------------------------------------------------------

def test_parse_step_payload_treats_missing_version_as_historical_step_v1():
    data = {"op_type": "face", "params": {"tool": 1}, "path": [[10.0, 0.0]]}
    migrated = parse_step_payload(data)
    assert migrated["version"] == CURRENT_FORMAT_VERSION
    assert migrated["op_type"] == "face"
    # Quelle unveraendert - insbesondere kein nachtraeglich eingefuegtes "version".
    assert "version" not in data


def test_parse_step_payload_accepts_explicit_current_version():
    data = {"version": CURRENT_FORMAT_VERSION, "op_type": "face", "params": {"tool": 1}, "path": []}
    migrated = parse_step_payload(data)
    assert migrated["version"] == CURRENT_FORMAT_VERSION


def test_parse_step_payload_rejects_unknown_newer_version():
    with pytest.raises(ValueError, match="neuer als die unterstützte"):
        parse_step_payload({"version": 99, "op_type": "face", "params": {}})


def test_parse_step_payload_rejects_invalid_version_type():
    with pytest.raises(ValueError, match="Formatversion"):
        parse_step_payload({"version": "2", "op_type": "face", "params": {}})


def test_parse_step_payload_does_not_mutate_source():
    original = {"op_type": "face", "params": {"tool": 1}, "path": []}
    before = copy.deepcopy(original)
    parse_step_payload(original)
    assert original == before


# ---------------------------------------------------------------------------
# Save -> Load -> Save fuer Format v2
# ---------------------------------------------------------------------------

def test_save_load_save_roundtrip_preserves_version_and_content():
    op = Operation(OpType.FACE, {"tool": 1, "feed": 0.2}, path=[(10.0, 0.0), (0.0, 0.0)])
    first = build_program_data([op], {"program_name": "RT"}, {})
    assert first["version"] == CURRENT_FORMAT_VERSION

    header, ops_data, _p, _g = parse_program_payload(first, "rt.lse")
    restored_ops = [step_data_to_operation(d) for d in ops_data]
    assert len(restored_ops) == 1
    assert restored_ops[0].params["tool"] == 1

    second = build_program_data(restored_ops, header, {})
    assert second["version"] == CURRENT_FORMAT_VERSION
    assert second["operations"][0]["params"]["tool"] == 1


# ---------------------------------------------------------------------------
# Laden schreibt nichts automatisch zurueck; Step-Fehlerdialog statt Crash
# ---------------------------------------------------------------------------

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
    return handler


def test_loading_an_old_v1_program_does_not_rewrite_the_source_file(tmp_path):
    from lathe_easystep import ui_persistence

    file_path = tmp_path / "old.lse"
    original_text = json.dumps({"version": 1, "header": {}, "operations": [], "meta": {}}, indent=2)
    file_path.write_text(original_text, encoding="utf-8")
    original_mtime_ns = file_path.stat().st_mtime_ns

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(file_path), None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: _DummySettings()
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(lambda *a: None)
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"critical must not fire: {a}"))
    )

    handler = _make_bare_handler()
    handler.model = type("M", (), {"operations": type("Ops", (list,), {"clear": list.clear})()})()
    handler.model.operations = []
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
    handler._clear_dirty_state = lambda: None
    handler._handle_selection_change = lambda idx: None
    handler._op_row_user_selected = False
    handler.list_ops = None

    ui_persistence.handle_load_program(handler)

    assert file_path.read_text(encoding="utf-8") == original_text
    assert file_path.stat().st_mtime_ns == original_mtime_ns


def test_handle_load_step_shows_warning_instead_of_unhandled_exception_for_future_version(tmp_path):
    """LES-053-Audit-Fund: vor der Behebung propagierte ein ValueError aus
    _step_data_to_operation()/parse_step_payload() hier ungefangen. Eine
    zu neue Version muss stattdessen ueber den vorhandenen UI-Fehlerpfad
    gemeldet werden."""
    from lathe_easystep import ui_persistence

    step_path = tmp_path / "future.step.json"
    step_path.write_text(
        json.dumps({"version": 99, "op_type": "face", "params": {"tool": 1}, "path": []}),
        encoding="utf-8",
    )

    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(step_path), None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: _DummySettings()
    warnings = []
    sys.modules["qtpy.QtWidgets"].QMessageBox.warning = staticmethod(lambda *a: warnings.append(a))
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(
        lambda *a: (_ for _ in ()).throw(AssertionError(f"critical must not fire: {a}"))
    )

    handler = _make_bare_handler()
    handler._step_data_to_operation = lambda data: step_data_to_operation(data)

    # Kein Aufrufer-Fehler mehr moeglich: darf keine Exception werfen.
    ui_persistence.handle_load_step(handler, step_file_filter="*.step.json")

    assert len(warnings) == 1
    assert "neuer als die unterstützte" in warnings[0][-1]
    assert handler._runtime.loading_step is False
