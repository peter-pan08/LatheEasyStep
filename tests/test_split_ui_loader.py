import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    "lathe_easystep.ui_split",
):
    sys.modules.pop(_mod, None)

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.ui_split import load_split_tab_uis  # noqa: E402


def test_split_shell_ui_loads_all_tab_widgets():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _split_tabs_loaded=False, _log=lambda *_args, **_kwargs: None)

    assert root.findChild(QtWidgets.QWidget, "program_language") is None
    assert root.findChild(QtWidgets.QWidget, "face_mode") is None
    assert root.findChild(QtWidgets.QWidget, "thread_pitch") is None

    load_split_tab_uis(handler)

    assert root.findChild(QtWidgets.QWidget, "program_language") is not None
    assert root.findChild(QtWidgets.QWidget, "face_mode") is not None
    assert root.findChild(QtWidgets.QWidget, "contour_segments") is not None
    assert root.findChild(QtWidgets.QWidget, "parting_mode") is not None
    assert root.findChild(QtWidgets.QWidget, "thread_pitch") is not None
    assert root.findChild(QtWidgets.QWidget, "groove_tool") is not None
    assert root.findChild(QtWidgets.QWidget, "drill_mode") is not None
    assert root.findChild(QtWidgets.QWidget, "key_slot_start_angle") is not None


def test_parting_mode_combo_offers_rough_finish_like_face_mode():
    """Realtest-Antwort Q14 ('drittes Combo-Item Schruppen + Schlichten? -
    ja'): Registry/Uebersetzungen/PARTING_MODE_INDEX kannten "rough_finish"
    bereits, aber die .ui hatte fuer parting_mode nur zwei <item>-Eintraege
    (Schruppen/Schlichten) - im echten Panel liess sich die dritte Option gar
    nicht auswaehlen, obwohl der Generator sie bereits unterstuetzt (siehe
    face_mode, das bereits drei Eintraege hatte)."""
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _split_tabs_loaded=False, _log=lambda *_args, **_kwargs: None)
    load_split_tab_uis(handler)

    face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
    parting_mode = root.findChild(QtWidgets.QComboBox, "parting_mode")
    assert face_mode.count() == 3
    assert parting_mode.count() == 3
    assert parting_mode.itemText(2) == "Schruppen + Schlichten"
