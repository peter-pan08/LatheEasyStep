import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LES-013: G96/G97 ist jetzt pro Operation waehlbar (Planen/Abspanen/
# Einstich/Gewinde). Diese Tests pruefen die echte Widget-Erzeugung
# (ensure_advanced_widgets) und Sprachumschaltung mit echtem PyQt5 - ohne
# PyQt5 (venv hat keins) werden sie uebersprungen, ausfuehren mit:
# /usr/bin/python3 -m pytest tests/test_per_operation_spindle_mode_ui.py
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

for _mod in (
    "qtpy",
    "qtpy.QtCore",
    "qtpy.QtGui",
    "qtpy.QtWidgets",
    "qtvcp",
    "qtvcp.core",
    "lathe_easystep_handler",
    "lathe_easystep.ui_advanced",
    "lathe_easystep.ui_split",
    "lathe_easystep.ui_visibility",
):
    sys.modules.pop(_mod, None)

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401
from lathe_easystep.translations import TRANSLATIONS  # noqa: E402
from lathe_easystep.ui_split import load_split_tab_uis  # noqa: E402
from lathe_easystep.ui_advanced import ensure_advanced_widgets  # noqa: E402
from lathe_easystep.ui_visibility import update_spindle_mode_visibility  # noqa: E402


def _load_handler_with_widgets():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(
        root_widget=root,
        w=root,
        _split_tabs_loaded=False,
        _log=lambda *_args, **_kwargs: None,
        _get_widget_by_name=lambda name: root.findChild(QtWidgets.QWidget, name),
    )
    load_split_tab_uis(handler)
    ensure_advanced_widgets(handler)
    return handler


@pytest.mark.parametrize("prefix", ["face", "parting", "groove", "thread"])
def test_spindle_mode_and_cutting_speed_widgets_are_created(prefix):
    handler = _load_handler_with_widgets()
    combo = getattr(handler, f"{prefix}_spindle_mode")
    cutting_speed = getattr(handler, f"{prefix}_cutting_speed")
    assert isinstance(combo, QtWidgets.QComboBox)
    assert isinstance(cutting_speed, QtWidgets.QDoubleSpinBox)
    assert combo.count() == 2
    assert combo.itemData(0) == "fixed"
    assert combo.itemData(1) == "css"


def test_program_tab_no_longer_has_global_spindle_mode_combo():
    """LES-013: die Modus-Wahl ist jetzt pro Operation, nicht mehr im
    Programmkopf - die globale Combo darf nicht mehr existieren."""
    handler = _load_handler_with_widgets()
    assert getattr(handler, "program_spindle_mode", None) is None
    assert handler.root_widget.findChild(QtWidgets.QComboBox, "program_spindle_mode") is None


def test_program_tab_still_has_max_rpm_field():
    handler = _load_handler_with_widgets()
    assert isinstance(handler.program_spindle_max_rpm, QtWidgets.QDoubleSpinBox)


@pytest.mark.parametrize("prefix", ["face", "parting", "groove", "thread"])
def test_new_spindle_mode_combos_share_translation_keys_with_program_combo(prefix):
    """Neue Reiter-Combos verwenden dieselben Uebersetzungsschluessel wie die
    bisherige globale program_spindle_mode-Combo (kein Duplikat noetig, da
    der Anzeigetext ueberall identisch ist: "Festdrehzahl (G97)"/"CSS (G96)")."""
    handler = _load_handler_with_widgets()
    combo = getattr(handler, f"{prefix}_spindle_mode")
    assert combo.itemText(0) == "combo.program_spindle_mode.fixed"
    assert combo.itemText(1) == "combo.program_spindle_mode.css"
    assert TRANSLATIONS.tr(combo.itemText(1), "de") == "CSS (G96)"
    assert TRANSLATIONS.tr(combo.itemText(1), "en") == "CSS (G96)"


@pytest.mark.parametrize("prefix", ["face", "parting", "groove", "thread"])
def test_spindle_mode_visibility_toggles_rpm_vs_cutting_speed_fields(prefix):
    handler = _load_handler_with_widgets()
    combo = getattr(handler, f"{prefix}_spindle_mode")
    rpm_field = handler._get_widget_by_name(f"{prefix}_spindle")
    vc_field = getattr(handler, f"{prefix}_cutting_speed")

    combo.setCurrentIndex(0)  # fixed / G97
    update_spindle_mode_visibility(handler)
    assert not rpm_field.isHidden()
    assert vc_field.isHidden()

    combo.setCurrentIndex(1)  # css / G96
    update_spindle_mode_visibility(handler)
    assert rpm_field.isHidden()
    assert not vc_field.isHidden()
