"""Real-Qt-Tests fuer den Datenweg Kontur-Tabelle -> collect_contour_segments().

LES-052-Testaudit 2026-09-18: build_contour_path()/generate_program_gcode()
und Co. sind gut mit vorgegebenen Operation.params["segments"] getestet -
aber niemand rief bislang collect_contour_segments() oder die
Add/Delete/Move/Edge-Change-Handler (ui_contour.py/ui_contour_input.py) mit
einer echten QTableWidget auf. Genau dieser Weg (Tabellen-Widgets -> die
tatsaechlich vom Anwender eingegebenen Segmentdaten) blieb dadurch
ungetestet - der Stub-Qt-Modus kann das nicht abdecken, da QTableWidget dort
eine wirkungslose Dummy-Klasse ist (rowCount()==0, setItem() no-op, ...).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep_handler import HandlerClass  # noqa: E402
from lathe_easystep.ui_contour_input import collect_contour_segments  # noqa: E402


class _Value:
    """Minimal SpinBox-Ersatz: nur .value() wird von den Handlern gelesen."""
    def __init__(self, v=0.0):
        self._v = v
    def value(self):
        return self._v


def _make_contour_handler():
    """Bare HandlerClass-Instanz mit einer ECHTEN QTableWidget als
    contour_segments - alles andere, was die Handler sonst noch anfassen
    (Modell-Update, Vorschau, Bootstrap-Widget-Suche), ist fuer diesen Test
    irrelevant und wird als No-Op gestubt (deckt sich mit der in TODO.md
    dokumentierten, bewussten Entscheidung, reinen Bootstrap-Code nicht
    unit-testbar zu machen)."""
    h = object.__new__(HandlerClass)
    h.contour_segments = QtWidgets.QTableWidget()
    h.contour_start_x = _Value(0.0)
    h.contour_start_z = _Value(0.0)
    h.contour_coord_mode = None
    h.contour_edge_type = None
    h.contour_edge_size = None
    h.label_contour_edge_size = None
    h._contour_edge_template_data = "none"
    h._contour_edge_template_size = 0.0
    h._contour_arc_template_data = "auto"
    h._contour_row_user_selected = False
    # LES-052 Abschnitt 3 (2026-09-20): die Add/Delete/Move-Handler markieren
    # einen bestehenden Kontur-Step jetzt dirty, dafuer wird ueber
    # _selected_operation_index() auf handler.list_ops zugegriffen. Diese
    # Tests pruefen bewusst nur den Tabellen-Datenweg (kein Step in der
    # Step-Liste ausgewaehlt), list_ops bleibt entsprechend ungebunden.
    h.list_ops = None
    h._op_row_user_selected = False
    h._ensure_contour_widgets = lambda: None
    h._update_selected_operation = lambda *a, **kw: None
    h._update_contour_preview_temp = lambda: None
    h._sync_contour_edge_controls = lambda: None
    h._log = lambda *a, **kw: None
    return h


def _set_row_xz(table, row, x, z):
    table.item(row, 1).setText(f"{x:.3f}")
    table.item(row, 2).setText(f"{z:.3f}")


def test_add_segment_creates_a_real_row_that_collect_reads_back():
    """_handle_contour_add_segment() legt eine echte Tabellenzeile mit
    Default-Werten an; collect_contour_segments() muss exakt das lesen, was
    add_segment tatsaechlich in die Zellen/ComboBoxen geschrieben hat."""
    h = _make_contour_handler()
    h.contour_start_x = _Value(12.5)
    h.contour_start_z = _Value(-3.0)

    h._handle_contour_add_segment()

    assert h.contour_segments.rowCount() == 1
    segments = collect_contour_segments(h)
    assert len(segments) == 1
    seg = segments[0]
    assert seg["mode"] == "xz"
    assert seg["x"] == 12.5
    assert seg["z"] == -3.0
    assert seg["edge"] == "none"
    assert seg["arc_side"] == "auto"


def test_add_segment_defaults_next_row_to_the_previous_rows_position():
    """Eine zweite hinzugefuegte Zeile ohne Bearbeitung durch den Anwender
    muss als Default die Position der letzten vorhandenen Zeile uebernehmen
    (echter Aufruf von collect_contour_segments() innerhalb von
    handle_contour_add_segment, nicht nur der Konturstart)."""
    h = _make_contour_handler()
    h.contour_start_x = _Value(20.0)
    h.contour_start_z = _Value(0.0)

    h._handle_contour_add_segment()
    _set_row_xz(h.contour_segments, 0, 15.0, -5.0)

    h._handle_contour_add_segment()

    assert h.contour_segments.rowCount() == 2
    segments = collect_contour_segments(h)
    assert segments[0]["x"] == 15.0 and segments[0]["z"] == -5.0
    # Zeile 2 ohne eigene Bearbeitung -> Default = Position von Zeile 1
    assert segments[1]["x"] == 15.0 and segments[1]["z"] == -5.0


def test_edge_change_writes_radius_to_the_selected_row_and_enables_arc_side():
    """_handle_contour_edge_change() liest den Vorlage-Kantentyp/-mass aus
    contour_edge_type/contour_edge_size und schreibt ihn ueber
    _write_contour_row() in die aktuell ausgewaehlte Tabellenzeile -
    collect_contour_segments() muss den geaenderten Wert sehen, und die
    Bogen-Seite-ComboBox (nur bei Radius sinnvoll) muss aktiviert werden."""
    h = _make_contour_handler()
    h._handle_contour_add_segment()
    table = h.contour_segments
    table.setCurrentCell(0, 0)

    edge_combo = QtWidgets.QComboBox()
    edge_combo.addItem("Radius", "radius")
    h.contour_edge_type = edge_combo
    edge_size = QtWidgets.QDoubleSpinBox()
    edge_size.setValue(7.5)
    h.contour_edge_size = edge_size

    assert table.cellWidget(0, 5).isEnabled() is False  # vorher: edge=none

    h._handle_contour_edge_change()

    segments = collect_contour_segments(h)
    assert segments[0]["edge"] == "radius"
    assert segments[0]["edge_size"] == 7.5
    assert table.cellWidget(0, 5).isEnabled() is True


def test_delete_segment_removes_only_the_selected_row():
    """_handle_contour_delete_segment() darf ausschliesslich die aktuell
    ausgewaehlte Zeile entfernen; die Daten der uebrigen Zeilen (inkl. ihrer
    ComboBox-Widgets) muessen unveraendert und in Reihenfolge erhalten
    bleiben."""
    h = _make_contour_handler()
    table = h.contour_segments
    for _ in range(3):
        h._handle_contour_add_segment()
    _set_row_xz(table, 0, 1.0, -1.0)
    _set_row_xz(table, 1, 2.0, -2.0)
    _set_row_xz(table, 2, 3.0, -3.0)

    table.setCurrentCell(1, 0)
    h._handle_contour_delete_segment()

    assert table.rowCount() == 2
    segments = collect_contour_segments(h)
    assert [s["x"] for s in segments] == [1.0, 3.0]
    assert [s["z"] for s in segments] == [-1.0, -3.0]


def test_move_up_and_move_down_swap_rows_without_losing_widget_state():
    """_handle_contour_move_up()/_handle_contour_move_down() verschieben
    Items UND ComboBox-Cellwidgets zwischen Zeilen (table.cellWidget()/
    removeCellWidget()/setCellWidget()) - ein reales Risiko, dass dabei ein
    Widget (z.B. ein zuvor auf 'radius' gesetzter Kantentyp) verloren geht
    oder an der falschen Zeile landet, statt nur die reinen Textwerte."""
    h = _make_contour_handler()
    table = h.contour_segments
    h._handle_contour_add_segment()
    h._handle_contour_add_segment()
    _set_row_xz(table, 0, 1.0, -1.0)
    _set_row_xz(table, 1, 2.0, -2.0)
    # Zeile 1 (Index 1) bekommt einen echten Kantentyp, der beim Verschieben
    # nicht verloren gehen darf.
    table.cellWidget(1, 3).setCurrentIndex(table.cellWidget(1, 3).findData("radius"))

    table.setCurrentCell(1, 0)
    h._handle_contour_move_up()

    assert table.currentRow() == 0
    segments = collect_contour_segments(h)
    assert segments[0]["x"] == 2.0 and segments[0]["z"] == -2.0
    assert segments[0]["edge"] == "radius"
    assert segments[1]["x"] == 1.0 and segments[1]["z"] == -1.0
    assert segments[1]["edge"] == "none"

    h._handle_contour_move_down()

    assert table.currentRow() == 1
    segments = collect_contour_segments(h)
    assert segments[0]["x"] == 1.0 and segments[0]["z"] == -1.0
    assert segments[1]["x"] == 2.0 and segments[1]["z"] == -2.0
    assert segments[1]["edge"] == "radius"
