import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Diese Tests pruefen den echten Combo-ItemData-Rundlauf (isinstance
# QComboBox), den der projektweite qtpy-Stub (conftest.py) nicht abbilden
# kann, da dort alle Widget-Typen dieselbe Dummy-Klasse sind. Ohne echtes
# PyQt5 (venv hat keins) werden diese Tests uebersprungen - ausfuehren mit:
# /usr/bin/python3 -m pytest tests/test_tool_combo_selection.py
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtCore, QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep_handler import HandlerClass  # noqa: E402
from lathe_easystep.model import OpType, Operation  # noqa: E402
from lathe_easystep import ui_operations  # noqa: E402


def _make_tool_combo(with_tools=(1, 7, 11)):
    combo = QtWidgets.QComboBox()
    combo.addItem("Bitte waehlen", 0)
    for t in with_tools:
        combo.addItem(f"T{t:02d}", t)
    return combo


def _bare_handler():
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    return handler


def test_tool_combo_selects_matching_tool_when_present():
    combo = _make_tool_combo()
    handler = _bare_handler()
    handler.param_widgets = {OpType.FACE: {"tool": combo}}
    handler._setup_param_maps = lambda: None

    op = Operation(OpType.FACE, {"tool": 7})
    ui_operations.load_operation_params_to_form(handler, op)

    assert combo.currentData() == 7


def test_tool_combo_falls_back_to_placeholder_when_tool_not_in_table():
    """Realer Bugreport: nach 'Programm laden' fehlte das Werkzeug bei
    einigen Operationen. Ursache: wenn die Werkzeug-Combo (noch) nicht die
    passende Werkzeugnummer als itemData enthaelt (z. B. andere/leere
    Werkzeugtabelle oder noch nicht befuellter Reiter), interpretierte der
    generische QComboBox-Fallback den rohen Zahlenwert als Positions-Index
    und waehlte damit ein voellig anderes (oder gar kein) Werkzeug aus, ohne
    dass das im UI auffiel."""
    combo = _make_tool_combo(with_tools=(1, 2))
    handler = _bare_handler()
    handler.param_widgets = {OpType.FACE: {"tool": combo}}
    handler._setup_param_maps = lambda: None

    # Werkzeug 11 existiert nicht in dieser (kleineren) Combo - Position 11
    # gaebe es aber, wenn die Combo zufaellig genug Eintraege haette; hier
    # gibt es nur 3 Eintraege (Platzhalter + 2 Werkzeuge).
    op = Operation(OpType.FACE, {"tool": 11})
    ui_operations.load_operation_params_to_form(handler, op)

    assert combo.currentIndex() == 0
    assert combo.currentData() == 0


def test_tool_combo_position_index_bug_would_pick_wrong_tool():
    """Kontrollfall: mit genuegend Eintraegen in der Combo wuerde der alte
    Positions-Index-Fallback (setCurrentIndex(int(val)) statt findData(val))
    ein voellig falsches Werkzeug auswaehlen - dieser Test dokumentiert,
    wovor der Fix in load_operation_params_to_form() schuetzt. Werkzeuge sind
    nach Werkzeugnummer sortiert, aber nicht fortlaufend (Luecken moeglich) -
    Position in der Combo und Werkzeugnummer sind zwei verschiedene Dinge."""
    combo = _make_tool_combo(with_tools=(5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60))
    assert combo.count() > 11
    # Simuliert den ALTEN Fallback direkt, um zu zeigen, was er tut, wenn man
    # versucht, Werkzeug 11 auszuwaehlen (das es in dieser Tabelle gar nicht gibt):
    combo.setCurrentIndex(11)
    # Position 11 zeigt Werkzeug 55, nicht Werkzeug 11 - genau die stille
    # Fehlauswahl, die der neue tool-spezifische Zweig verhindert.
    assert combo.currentData() == 55
    assert combo.currentData() != 11
