import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.ui_split import load_step_management_uis  # noqa: E402
from lathe_easystep.ui_advanced import _ensure_status_widgets  # noqa: E402

# LES-050 Regressionsfund: stepActionsPanel.ui wechselte von QHBoxLayout auf
# QGridLayout (zweispaltig, damit die sieben Buttons nicht unter ihre
# Textbreite gequetscht werden). _ensure_status_widgets() rief bisher
# layout.insertWidget() auf, um das "Keine offenen Aenderungen"-Label neben
# btnSaveChanges einzufuegen - eine QBoxLayout-Methode, die QGridLayout nicht
# hat. Beim ersten Start des Panels ausserhalb der Test-Stubs (Standalone-
# `qtvcp -c easystep ...`) brach das real mit
# "AttributeError: 'QGridLayout' object has no attribute 'insertWidget'".
# Kein bestehender Test deckte das ab: die Stub-Suite nutzt keine echten
# Qt-Layouts, und der einzige Real-Qt-Test fuer label_dirty_status setzte es
# direkt als Fake statt _ensure_status_widgets() echt aufzurufen.


def _load_root_with_step_management():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _step_management_ui_loaded=False, _log=lambda *_a, **_k: None)
    load_step_management_uis(handler)
    return root, handler


def test_ensure_status_widgets_does_not_crash_against_the_real_grid_layout():
    root, handler = _load_root_with_step_management()
    _ensure_status_widgets(handler, root)  # darf nicht mit AttributeError abbrechen
    assert getattr(handler, "label_dirty_status", None) is not None


def test_dirty_status_label_is_placed_in_the_same_grid_as_save_changes_button():
    root, handler = _load_root_with_step_management()
    _ensure_status_widgets(handler, root)

    button = root.findChild(QtWidgets.QPushButton, "btnSaveChanges")
    label = handler.label_dirty_status
    layout = button.parentWidget().layout()
    assert isinstance(layout, QtWidgets.QGridLayout)
    assert layout.indexOf(label) >= 0

    button_row, _col, _row_span, _col_span = layout.getItemPosition(layout.indexOf(button))
    label_row, label_col, _label_row_span, label_col_span = layout.getItemPosition(layout.indexOf(label))
    assert label_row == button_row + 1
    assert label_col == 0
    assert label_col_span >= layout.columnCount()


def test_ensure_status_widgets_is_idempotent():
    """Wird u. a. bei jedem erneuten Durchlauf von ensure_advanced_widgets()
    aufgerufen - ein zweiter Aufruf darf kein zweites Label einfuegen."""
    root, handler = _load_root_with_step_management()
    _ensure_status_widgets(handler, root)
    first_label = handler.label_dirty_status
    _ensure_status_widgets(handler, root)
    assert handler.label_dirty_status is first_label
    assert len(root.findChildren(QtWidgets.QLabel, "label_dirty_status")) == 1
