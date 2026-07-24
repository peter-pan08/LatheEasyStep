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
    "lathe_easystep.ui_static",
):
    sys.modules.pop(_mod, None)

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.translations import TRANSLATIONS  # noqa: E402
from lathe_easystep.ui_split import load_split_tab_uis  # noqa: E402
from lathe_easystep.ui_static import apply_ui_static_translations, load_ui_static_map  # noqa: E402


def _load_full_root():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _split_tabs_loaded=False, _log=lambda *_args, **_kwargs: None)
    load_split_tab_uis(handler)
    return root


def test_ui_static_map_covers_widgets_from_split_tab_files():
    """LES-021: bis zur UI-Teilung lagen alle Reiter in der einen
    lathe_easystep.ui, die load_ui_static_map() komplett scannte. Nach dem
    Split in lathe_easystep/ui_parts/*.ui blieb load_ui_static_map() auf die
    Shell-Datei beschraenkt - Labels/Tooltips/Combo-Eintraege der acht
    Reiter-Dateien wurden dadurch nie mehr automatisch uebersetzt, obwohl
    fuer alle bereits vollstaendige de/en/es-Schluessel im .lng-Katalog
    vorhanden waren (z. B. ui.label_drill_dwell.text)."""
    static_map = load_ui_static_map()
    assert "label_drill_dwell" in static_map
    assert static_map["label_drill_dwell"]["text"] == "Verweilzeit (G82)"
    assert "groove_lage" in static_map
    assert static_map["groove_lage"]["items"][1] == "Mantel – Innen (ID)"


def test_language_switch_translates_split_tab_labels_and_tooltips():
    root = _load_full_root()

    label = root.findChild(QtWidgets.QLabel, "label_drill_dwell")
    combo = root.findChild(QtWidgets.QComboBox, "groove_lage")
    btn = root.findChild(QtWidgets.QToolButton, "btn_slice_view")
    assert label is not None and combo is not None and btn is not None

    apply_ui_static_translations(root, TRANSLATIONS.tr, "de")
    assert label.text() == "Verweilzeit (G82)"
    assert combo.itemText(1) == "Mantel – Innen (ID)"

    apply_ui_static_translations(root, TRANSLATIONS.tr, "en")
    assert label.text() == "Dwell Time (G82)"
    assert combo.itemText(1) == "Cylindrical - Inside (ID)"
    assert btn.toolTip() == (
        "Shows an additional section view. Move the cutting line with the mouse in the side view."
    )

    apply_ui_static_translations(root, TRANSLATIONS.tr, "es")
    assert label.text() != "Dwell Time (G82)"
    assert label.text() != "Verweilzeit (G82)"
