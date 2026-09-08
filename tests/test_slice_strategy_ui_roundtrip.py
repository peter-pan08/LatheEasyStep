import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Diese Tests pruefen den echten Combo-ItemData-Rundlauf (isinstance
# QComboBox vs. QSpinBox etc.), den der projektweite qtpy-Stub (conftest.py)
# nicht abbilden kann, da dort alle Widget-Typen dieselbe Dummy-Klasse sind.
# Ohne echtes PyQt5 (venv hat keins) werden diese Tests uebersprungen -
# ausfuehren mit: /usr/bin/python3 -m pytest tests/test_slice_strategy_ui_roundtrip.py
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# conftest.py's pytest_configure() unconditionally installs a fake qtpy/qtvcp
# stub into sys.modules before any test module is imported (the venv used for
# the rest of the suite has no real Qt bindings). Since real PyQt5/qtpy/qtvcp
# ARE available under this interpreter, evict the stub so the production
# modules below bind to the real classes - otherwise isinstance(widget,
# QtWidgets.QComboBox) checks in the production code compare a real QComboBox
# against the fake stub class and silently never match.
# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtCore, QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep_handler import HandlerClass  # noqa: E402
from lathe_easystep.model import OpType, Operation  # noqa: E402
from lathe_easystep import ui_operations, ui_params  # noqa: E402


def _make_combo():
    combo = QtWidgets.QComboBox()
    combo.addItem("Parallel X")
    combo.addItem("Parallel Z")
    combo.setItemData(0, "parallel_x", QtCore.Qt.UserRole)
    combo.setItemData(1, "parallel_z", QtCore.Qt.UserRole)
    return combo


def test_select_slice_strategy_index_maps_legacy_numeric_codes():
    """Realer Bug: findData() wurde mit einem int aufgerufen, obwohl itemData
    immer Strings ("parallel_x"/"parallel_z") enthaelt - der Treffer konnte nie
    gelingen. Dadurch wurden gueltige, gespeicherte Werte (1/2) beim Laden
    nie korrekt auf die Combo angewandt (bzw. bildeten ueber den generischen
    Fallback faelschlich auf den falschen Eintrag ab)."""
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    h.parting_slice_strategy = combo

    assert h._select_slice_strategy_index(combo, 1) is True
    assert combo.itemData(combo.currentIndex()) == "parallel_x"

    assert h._select_slice_strategy_index(combo, 2) is True
    assert combo.itemData(combo.currentIndex()) == "parallel_z"


def test_select_slice_strategy_index_rejects_invalid_code():
    """Ein gespeicherter Wert von 0 (oder jeder andere Wert ausserhalb 1/2)
    darf NICHT stillschweigend auf eine Auswahl abgebildet werden - sonst
    zeigt die Combo eine Strategie an, die nie gewaehlt wurde."""
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    assert h._select_slice_strategy_index(combo, 0) is False


def test_load_operation_params_to_form_shows_unset_for_stale_zero():
    """Realer Bug (Test.lse, Innen-Schruppen-Step 9): gespeicherter Wert
    slice_strategy=0 fuehrte dazu, dass die Combo faelschlich 'Parallel X'
    anzeigte (ueber den generischen setCurrentIndex(int(val))-Fallback),
    obwohl die G-Code-Erzeugung denselben Wert als 'keine Strategie gewaehlt'
    interpretiert (gcode_roughing.py) und nur eine WARN-Zeile ohne Schnitt
    ausgibt. UI und Generator widersprachen sich damit. Nach dem Fix muss die
    Combo ehrlich 'keine Auswahl' (currentIndex == -1) zeigen."""
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    combo.setCurrentIndex(0)
    h.parting_slice_strategy = combo
    h.param_widgets = {OpType.ABSPANEN: {"slice_strategy": combo}}
    h._setup_param_maps = lambda: None

    op = Operation(OpType.ABSPANEN, {"slice_strategy": 0})
    ui_operations.load_operation_params_to_form(h, op)
    assert combo.currentIndex() == -1


def test_load_operation_params_to_form_selects_valid_stored_strategy():
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    h.parting_slice_strategy = combo
    h.param_widgets = {OpType.ABSPANEN: {"slice_strategy": combo}}
    h._setup_param_maps = lambda: None

    op = Operation(OpType.ABSPANEN, {"slice_strategy": "parallel_z"})
    ui_operations.load_operation_params_to_form(h, op)
    assert combo.itemData(combo.currentIndex()) == "parallel_z"


def test_collect_params_does_not_fabricate_zero_for_unselected_combo():
    """Realer Bug: collect_params() setzte fuer eine Combo ohne Auswahl
    (currentIndex == -1, kein itemData) den Fallback idx + 1, was fuer
    idx == -1 den ungueltigen Wert 0 ergab - exakt der Wert, der spaeter das
    Innen-Schruppen ohne jede Warnung im UI stillschweigend deaktivierte."""
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    combo.setCurrentIndex(-1)
    h.param_widgets = {OpType.ABSPANEN: {"slice_strategy": combo}}
    h._setup_param_maps = lambda: None
    h._current_parting_contour_name = lambda: "dummy"
    h._resolve_contour_path = lambda name: []

    params = ui_params.collect_params(h, OpType.ABSPANEN)
    assert params.get("slice_strategy") != 0
    assert params.get("slice_strategy") is None


def test_collect_params_reads_valid_selection_from_itemdata():
    h = object.__new__(HandlerClass)
    combo = _make_combo()
    combo.setCurrentIndex(1)
    h.param_widgets = {OpType.ABSPANEN: {"slice_strategy": combo}}
    h._setup_param_maps = lambda: None
    h._current_parting_contour_name = lambda: "dummy"
    h._resolve_contour_path = lambda name: []

    params = ui_params.collect_params(h, OpType.ABSPANEN)
    assert params["slice_strategy"] == "parallel_z"
