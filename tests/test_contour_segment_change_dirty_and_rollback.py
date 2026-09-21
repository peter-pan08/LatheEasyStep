"""Real-Qt-Tests fuer LES-052 Abschnitt 3 (Audit/Fix 2026-09-20): den
bestaetigten Kontur-Fund und den dabei mitgefundenen Dirty-State-Fehler.

`tests/test_contour_table_interaction.py` stubbt `_update_selected_
operation()` bewusst als No-Op, um isoliert nur den Weg Tabelle ->
`collect_contour_segments()` zu pruefen. Diese Datei geht einen Schritt
weiter und ruft die ECHTE Kette mit einem bereits bestehenden, in der
Step-Liste ausgewaehlten CONTOUR-Step auf:

    QTableWidget -> handle_contour_*() -> _update_selected_operation()
    -> sync_form_to_operation() -> model.update_geometry()
    -> contour_logic.build_contour_path()/build_contour_variants()

Bestaetigter Fund vor dem Fix: Loeschen der letzten verbleibenden
Segmentzeile eines bestehenden Kontur-Steps liess `update_geometry()` mit
einem unbehandelten `TypeError` scheitern (build_contour_variants() gab
bei `len(pts) < 2` eine blanke Liste statt des sonst ueblichen Dicts
zurueck). `op.params` wurde von `sync_form_to_operation()` zwar bereits
korrekt zurueckgerollt, die sichtbare Tabelle blieb aber auf dem
abgelehnten (leeren) Zustand stehen - Modell und Tabelle zeigten danach
unterschiedliche Konturen, ohne dass irgendwas dirty markiert wurde.

Zusaetzlich bestaetigt: `add`/`delete`/`move up`/`move down` sowie
Aenderungen an `contour_start_x`/`contour_start_z` markierten einen
bestehenden, ausgewaehlten Kontur-Step bei Erfolg nie dirty.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.dirty_state import DirtyState  # noqa: E402
from lathe_easystep.model import Operation, OpType, ProgramModel  # noqa: E402
from lathe_easystep.runtime_state import RuntimeState  # noqa: E402
from lathe_easystep_handler import HandlerClass  # noqa: E402


def _segment(x, z, edge="none", edge_size=0.0):
    return {
        "mode": "xz", "x": x, "z": z, "x_empty": False, "z_empty": False,
        "edge": edge, "edge_size": edge_size, "arc_side": "auto", "arc_side_raw": "",
    }


def _make_handler_with_existing_contour(segments):
    """Bare HandlerClass mit einer ECHTEN QTableWidget/QListWidget und
    einem bereits bestehenden, in der Step-Liste ausgewaehlten CONTOUR-Step
    (`_op_row_user_selected=True`, wie nach einem normalen Klick auf den
    Step in der Liste, siehe `ui_selection.py`). Die Tabelle wird ueber die
    bestehende `_load_params_to_form()` (dispatcht fuer CONTOUR an
    `_load_contour_operation_to_form()`) aus `op.params` aufgebaut - exakt
    der Weg, den das echte Panel beim Auswaehlen eines Steps nutzt."""
    h = object.__new__(HandlerClass)
    h._runtime = RuntimeState()
    h.contour_segments = QtWidgets.QTableWidget()
    h.contour_start_x = QtWidgets.QDoubleSpinBox()
    h.contour_start_x.setRange(-1000.0, 1000.0)
    h.contour_start_z = QtWidgets.QDoubleSpinBox()
    h.contour_start_z.setRange(-1000.0, 1000.0)
    h.contour_coord_mode = QtWidgets.QComboBox()
    h.contour_coord_mode.addItem("Absolut", 0)
    h.contour_coord_mode.addItem("Inkrementell", 1)
    h.contour_name = None
    h.contour_edge_type = None
    h.contour_edge_size = None
    h.label_contour_edge_size = None
    h._contour_edge_template_data = "none"
    h._contour_edge_template_size = 0.0
    h._contour_arc_template_data = "auto"
    h._contour_row_user_selected = False
    h._ensure_contour_widgets = lambda: None
    h._update_contour_preview_temp = lambda: None
    h._sync_contour_edge_controls = lambda: None
    h._refresh_preview = lambda: None
    h._update_parting_contour_choices = lambda: None
    h.btn_add = None
    h._log = lambda *a, **kw: None
    h._describe_operation = lambda op, i: f"{i}. Kontur"

    op = Operation(OpType.CONTOUR, {
        "name": "K1", "start_x": 0.0, "start_z": 0.0, "coord_mode": 0,
        "segments": segments,
    })
    model = ProgramModel()
    model.update_geometry(op)
    model.operations = [op]
    h.model = model

    h.list_ops = QtWidgets.QListWidget()
    h.list_ops.addItem("1. Kontur")
    h.list_ops.setCurrentRow(0)
    h.param_widgets = {
        OpType.CONTOUR: {
            "start_x": h.contour_start_x, "start_z": h.contour_start_z,
            "coord_mode": h.contour_coord_mode,
        },
    }
    h._dirty = DirtyState()
    h._op_row_user_selected = True

    h._load_params_to_form(op)
    return h, op


# ---------------------------------------------------------------------------
# Bestaetigter Fund: letzte Segmentzeile loeschen.
# ---------------------------------------------------------------------------

def test_delete_last_segment_does_not_raise_and_restores_table_from_model():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    table = h.contour_segments
    original_path = list(op.path)
    assert table.rowCount() == 1

    table.setCurrentCell(0, 0)
    h._handle_contour_delete_segment()  # darf NICHT werfen

    assert table.rowCount() == 1  # aus dem unveraenderten op.params wiederhergestellt
    assert table.item(0, 1).text() == "10.000"
    assert table.item(0, 2).text() == "-5.000"
    assert op.params["segments"] == [_segment(10.0, -5.0)]
    assert op.path == original_path


def test_delete_last_segment_does_not_change_existing_dirty_state():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    h._dirty = DirtyState(operation_indices={5}, program_dirty=True, program_header_dirty=True)
    table = h.contour_segments
    table.setCurrentCell(0, 0)

    h._handle_contour_delete_segment()

    assert h._dirty.operation_indices == {5}
    assert h._dirty.program_dirty is True
    assert h._dirty.program_header_dirty is True


def test_delete_segment_marks_dirty_when_a_segment_remains():
    h, op = _make_handler_with_existing_contour([_segment(1.0, -1.0), _segment(2.0, -2.0)])
    table = h.contour_segments
    table.setCurrentCell(0, 0)

    h._handle_contour_delete_segment()

    assert table.rowCount() == 1
    assert len(op.params["segments"]) == 1
    assert op.params["segments"][0]["x"] == 2.0
    assert op.params["segments"][0]["z"] == -2.0
    assert h._dirty.operation_indices == {0}


# ---------------------------------------------------------------------------
# Erfolgreiche Aenderungen markieren den bestehenden Step dirty.
# ---------------------------------------------------------------------------

def test_add_segment_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])

    h._handle_contour_add_segment()

    assert h.contour_segments.rowCount() == 2
    assert h._dirty.operation_indices == {0}


def test_move_up_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(1.0, -1.0), _segment(2.0, -2.0)])
    h.contour_segments.setCurrentCell(1, 0)

    h._handle_contour_move_up()

    assert op.params["segments"][0]["x"] == 2.0
    assert h._dirty.operation_indices == {0}


def test_move_down_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(1.0, -1.0), _segment(2.0, -2.0)])
    h.contour_segments.setCurrentCell(0, 0)

    h._handle_contour_move_down()

    assert op.params["segments"][0]["x"] == 2.0
    assert h._dirty.operation_indices == {0}


# ---------------------------------------------------------------------------
# contour_start_x/contour_start_z: fachliche Parameter, mussten bisher nur
# die Live-Vorschau aktualisieren, nie zuverlaessig Modell/Dirty-State.
# ---------------------------------------------------------------------------

def test_contour_start_x_change_updates_model_and_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    h.contour_start_x.setValue(3.5)

    h._handle_contour_start_change()

    assert op.params["start_x"] == 3.5
    assert h._dirty.operation_indices == {0}


def test_contour_start_z_change_updates_model_and_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    h.contour_start_z.setValue(-7.25)

    h._handle_contour_start_change()

    assert op.params["start_z"] == -7.25
    assert h._dirty.operation_indices == {0}


# ---------------------------------------------------------------------------
# handle_contour_table_change(): direkter Zellen-Text-Edit. Bestaetigter
# Fund (Audit 2026-09-21): nicht-numerischer Text laesst finite_float() ueber
# _collect_contour_segments() mit einem ValueError scheitern - vorher
# unbehandelt (Tabelle blieb auf dem abgelehnten Text stehen, nie dirty auch
# im Erfolgsfall).
# ---------------------------------------------------------------------------

def test_table_change_with_valid_edit_updates_model_and_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    table = h.contour_segments
    table.item(0, 1).setText("12.500")

    h._handle_contour_table_change()

    assert op.params["segments"][0]["x"] == 12.5
    assert h._dirty.operation_indices == {0}


def test_table_change_with_invalid_text_does_not_raise_and_restores_table():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    table = h.contour_segments
    original_path = list(op.path)
    table.item(0, 1).setText("abc")  # nicht-numerischer Text

    h._handle_contour_table_change()  # darf NICHT werfen

    assert table.item(0, 1).text() == "10.000"  # aus op.params wiederhergestellt
    assert op.params["segments"][0]["x"] == 10.0
    assert op.path == original_path


def test_table_change_with_invalid_text_does_not_change_existing_dirty_state():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    h._dirty = DirtyState(operation_indices={5}, program_dirty=True, program_header_dirty=True)
    table = h.contour_segments
    table.item(0, 1).setText("abc")

    h._handle_contour_table_change()

    assert h._dirty.operation_indices == {5}
    assert h._dirty.program_dirty is True
    assert h._dirty.program_header_dirty is True


# ---------------------------------------------------------------------------
# _write_contour_row(): schreibt Kante/Mass PROGRAMMGESTEUERT in eine
# Tabellenzeile (aufgerufen von handle_contour_edge_change()). Bestaetigter
# Reentranz-Fund (Audit 2026-09-21): der Kantentyp-Combo einer Zeile ist an
# handle_contour_table_change() angebunden; setCurrentIndex() auf diesem
# bereits verbundenen Combo loeste dieses Signal REENTRANT aus, WAEHREND
# _write_contour_row() noch lief - eine rein programmatische Zeilen-
# Befuellung loeste dadurch denselben Sync-/Dirty-Pfad aus wie eine echte
# Benutzeraenderung, mit einem zeitpunktabhaengigen (nicht deterministischen)
# Endergebnis. Enthielt eine ANDERE Zeile zu diesem Zeitpunkt bereits
# ungueltigen Text, fuehrte das sogar zu einem *nativen Prozessabsturz*
# (Fatal Python error: Aborted). Fix: die zwei setCurrentIndex()-Aufrufe in
# _write_contour_row() blocken jetzt kurzzeitig nur das Signal des
# betroffenen Combo-Widgets selbst (dieselbe bereits im Projekt etablierte
# Technik wie in _load_contour_operation_to_form()/sync_contour_edge_
# controls() - keine neue Architektur, keine globale Signalsperre).
# ---------------------------------------------------------------------------

def test_write_contour_row_alone_does_not_sync_or_mark_dirty():
    """Ein rein programmatischer Aufruf von _write_contour_row() (ohne den
    umgebenden handle_contour_edge_change()-Sync) darf keine fachliche
    Aenderung und kein Dirty erzeugen - das war vor dem Blocksignals-Fix
    NICHT der Fall, weil der reentrante Combo-Signal-Aufruf selbstaendig
    _handle_contour_table_change() (inkl. Dirty-Markierung) ausloeste."""
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    original_params = dict(op.params)

    h._write_contour_row(0, edge_text="radius", edge_size=2.0)

    assert op.params == original_params
    assert h._dirty.operation_indices == set()
    assert h._dirty.program_dirty is False


def test_edge_change_with_valid_state_updates_model_and_marks_dirty():
    """Eine echte Benutzeraenderung (ueber handle_contour_edge_change(),
    dem einzigen vorgesehenen Ausloeser) funktioniert weiterhin und
    markiert den bestehenden Kontur-Step dirty."""
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    table = h.contour_segments
    table.setCurrentCell(0, 0)
    edge_combo = QtWidgets.QComboBox()
    edge_combo.addItem("Radius", "radius")
    h.contour_edge_type = edge_combo
    edge_size = QtWidgets.QDoubleSpinBox()
    edge_size.setValue(2.0)
    h.contour_edge_size = edge_size

    h._handle_contour_edge_change()

    assert op.params["segments"][0]["edge"] == "radius"
    assert op.params["segments"][0]["edge_size"] == 2.0
    assert h._dirty.operation_indices == {0}


def _trigger_edge_change_with_other_row_invalid(h):
    table = h.contour_segments
    # Zeile 1 (nicht die gerade bearbeitete Zeile 0) enthaelt bereits
    # ungueltigen Text.
    table.item(1, 1).setText("xyz")
    table.setCurrentCell(0, 0)
    edge_combo = QtWidgets.QComboBox()
    edge_combo.addItem("Radius", "radius")
    h.contour_edge_type = edge_combo
    edge_size = QtWidgets.QDoubleSpinBox()
    edge_size.setValue(2.0)
    h.contour_edge_size = edge_size
    h._handle_contour_edge_change()  # darf NICHT werfen und NICHT abstuerzen


def test_edge_change_restore_after_invalid_change_ends_deterministically_with_table_matching_model():
    """Mit der Reentranz behoben laeuft der Sync jetzt genau EINMAL, zum
    richtigen Zeitpunkt (nach vollstaendigem _write_contour_row()) - das
    Ergebnis ist deshalb nicht mehr zeitpunktabhaengig: Zeile 1 wird ueber
    _load_params_to_form() exakt aus dem unveraenderten op.params
    wiederhergestellt, Zeile 0s versuchte Kantenaenderung wird NICHT
    uebernommen (der Sync scheiterte insgesamt), Tabelle == Modell."""
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0), _segment(20.0, -8.0)])
    table = h.contour_segments
    original_segments = [dict(s) for s in op.params["segments"]]
    original_path = list(op.path)

    _trigger_edge_change_with_other_row_invalid(h)

    assert op.params["segments"] == original_segments
    assert op.path == original_path
    assert table.rowCount() == 2
    assert table.item(0, 1).text() == "10.000"
    assert table.item(0, 2).text() == "-5.000"
    assert table.cellWidget(0, 3).currentData() == "none"  # Kantenaenderung NICHT uebernommen
    assert table.item(1, 1).text() == "20.000"
    assert table.item(1, 2).text() == "-8.000"
    assert h._dirty.operation_indices == set()


def test_edge_change_restore_after_invalid_change_does_not_alter_existing_dirty_state():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0), _segment(20.0, -8.0)])
    h._dirty = DirtyState(operation_indices={5}, program_dirty=True, program_header_dirty=True)

    _trigger_edge_change_with_other_row_invalid(h)

    assert h._dirty.operation_indices == {5}
    assert h._dirty.program_dirty is True
    assert h._dirty.program_header_dirty is True


# ---------------------------------------------------------------------------
# contour_name: fachlicher Bestandteil des Steps (op.params["name"]),
# referenziert von ABSPANEN ueber contour_name - keine reine Anzeige-
# /Metadatenangabe. Bestaetigter Fund: war nur an Vorschau/Auswahlliste
# angebunden, nie zuverlaessig an Modell/Dirty-State.
# ---------------------------------------------------------------------------

def test_contour_name_change_updates_model_and_marks_dirty():
    h, op = _make_handler_with_existing_contour([_segment(10.0, -5.0)])
    h.contour_name = QtWidgets.QLineEdit()
    h.contour_name.setText("K1")

    h.contour_name.setText("Aussenkontur")
    h._handle_contour_name_change()

    assert op.params["name"] == "Aussenkontur"
    assert h._dirty.operation_indices == {0}
