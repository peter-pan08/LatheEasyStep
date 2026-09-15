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
from lathe_easystep.ui_split import load_split_tab_uis, load_step_management_uis  # noqa: E402
from lathe_easystep.ui_lifecycle import _install_workspace_splitter  # noqa: E402

# LES-050 REGRESSIONSFUND (2026-09-14, echtes praktisches Testen): die
# Step-Listen-Buttons (stepListPanel.ui: Step/Programm speichern/laden) und
# die Aktionsleiste (stepActionsPanel.ui: hinzufuegen/loeschen/verschieben/
# Programm erzeugen/Aenderungen speichern) standen alle in je einer einzigen
# QHBoxLayout-Reihe (4 bzw. 7 Buttons) ohne Mindestbreiten-Absicherung -
# bei schmaler Splitterstellung wurden die Buttons unter ihre Textbreite
# gequetscht, nur noch Fragmente lesbar. Fix: beide Reihen sind jetzt
# QGridLayout mit zwei Spalten (stepListPanel: 2x2, stepActionsPanel: 2x4),
# die Splitter-Mindestbreiten (`_install_workspace_splitter`) wurden an das
# tatsaechliche minimumSizeHint der Grids angepasst (330/380 statt 190/360).
# Diese Tests sichern, dass kein Button-Text unter jeder unterstuetzten
# Fenstergroesse/Splitterstellung unter seine sizeHint()-Breite faellt.


def _load_workspace():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(
        root_widget=root,
        _split_tabs_loaded=False,
        _step_management_ui_loaded=False,
        _log=lambda *_a, **_k: None,
    )
    load_split_tab_uis(handler)
    load_step_management_uis(handler)
    _install_workspace_splitter(handler)
    return root, handler


def _step_list_buttons(root):
    return [
        root.findChild(QtWidgets.QPushButton, name)
        for name in ("btn_save_step", "btn_load_step", "btn_save_program", "btn_load_program")
    ]


def _step_action_buttons(root):
    return [
        root.findChild(QtWidgets.QPushButton, name)
        for name in ("btnAdd", "btnDelete", "btnMoveUp", "btnMoveDown", "btnNewProgram", "btnGenerate", "btnSaveChanges")
    ]


def _assert_no_button_is_squeezed_below_its_text(buttons):
    for button in buttons:
        assert button is not None
        # +1px Toleranz fuer Rundungsdifferenzen zwischen sizeHint() und der
        # tatsaechlichen Layout-Zuteilung im Offscreen-Backend.
        assert button.width() + 1 >= button.sizeHint().width(), (
            f"{button.objectName()!r}: width={button.width()} < sizeHint={button.sizeHint().width()}"
        )


@pytest.mark.parametrize("window_width", [700, 1000, 1600], ids=["minimal", "normal", "wide"])
def test_step_list_buttons_stay_full_width_at_every_window_size(window_width):
    root, handler = _load_workspace()
    root.resize(window_width, 700)
    root.show()
    _app.processEvents()
    _assert_no_button_is_squeezed_below_its_text(_step_list_buttons(root))


@pytest.mark.parametrize("window_width", [700, 1000, 1600], ids=["minimal", "normal", "wide"])
def test_step_action_buttons_stay_full_width_at_every_window_size(window_width):
    root, handler = _load_workspace()
    root.resize(window_width, 700)
    root.show()
    _app.processEvents()
    _assert_no_button_is_squeezed_below_its_text(_step_action_buttons(root))


def test_buttons_stay_readable_at_the_narrow_splitter_extreme():
    root, handler = _load_workspace()
    root.resize(1000, 700)
    root.show()
    _app.processEvents()
    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    splitter.setSizes([330, 670])  # step_panel an seinem eigenen Minimum
    _app.processEvents()
    _assert_no_button_is_squeezed_below_its_text(_step_list_buttons(root))


def test_buttons_stay_readable_at_the_wide_splitter_extreme():
    root, handler = _load_workspace()
    root.resize(1600, 700)
    root.show()
    _app.processEvents()
    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    splitter.setSizes([380, 1000])  # rechte Spalte an ihrem eigenen Minimum
    _app.processEvents()
    _assert_no_button_is_squeezed_below_its_text(_step_action_buttons(root))


def test_step_panel_and_right_panel_never_shrink_below_their_minimum_width():
    root, handler = _load_workspace()
    root.resize(1000, 700)
    root.show()
    _app.processEvents()
    step_panel = root.findChild(QtWidgets.QWidget, "stepListPanel")
    right_panel = root.findChild(QtWidgets.QWidget, "rightWorkspacePanel")
    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    # Absichtlich unrealistisch schmale Vorgaben anfordern - der Splitter
    # (childrenCollapsible=False + minimumWidth) muss trotzdem die echten
    # Mindestbreiten durchsetzen statt die Panels zu unterschreiten.
    splitter.setSizes([1, 1])
    _app.processEvents()
    assert step_panel.width() >= 330
    assert right_panel.width() >= 380
