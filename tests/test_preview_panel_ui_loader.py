import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtCore, QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.ui_split import (  # noqa: E402
    load_preview_uis,
    load_split_tab_uis,
    load_step_management_uis,
)
from lathe_easystep.ui_lifecycle import (  # noqa: E402
    _dock_preview_above_scroll,
    _install_workspace_splitter,
)

# LES-024: Vorschau/Schnittansicht (previewWidget, previewSliceWidget,
# btn_slice_view) wurden aus dem Geruest (lathe_easystep.ui) in ein eigenes
# .ui-Fragment ausgelagert (ui_parts/previewPanel.ui). Beim ersten Umbau
# stellte sich real per Screenshot-Vergleich heraus, dass die leer
# zurueckbleibende Huelle nach dem Docking (_dock_preview_above_scroll())
# unentdeckt Layout-Platz beanspruchte und die angedockte Vorschau dadurch
# sichtbar zu gross wurde (previewWidget 220px statt 140px hoch) - seitdem
# entfernt _dock_preview_above_scroll() die leere Huelle vollstaendig aus
# ihrem Elternlayout. Dieser Test deckt beide Aspekte ab: Laden UND das
# korrekte, unveraenderte Docking-Ergebnis danach.


def _load_root_without_preview():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(
        root_widget=root,
        _split_tabs_loaded=False,
        _step_management_ui_loaded=False,
        _preview_ui_loaded=False,
        _preview_docked=False,
        _log=lambda *_a, **_k: None,
        _find_root_widget=lambda: root,
    )
    return root, handler


def _load_full_root():
    """Realistisches Gesamt-Panel wie beim echten Start (alle drei Lader) -
    previewWidget bekommt seine endgueltige Groesse erst im Zusammenspiel
    mit den echten Reiterinhalten (tabParams-sizeHint beeinflusst, wie viel
    Platz rightLayout der angedockten Vorschau zuteilt)."""
    root, handler = _load_root_without_preview()
    load_split_tab_uis(handler)
    load_step_management_uis(handler)
    return root, handler


def test_preview_widgets_missing_before_load_present_after():
    root, handler = _load_root_without_preview()

    for name in ("previewWidget", "previewSliceWidget", "btn_slice_view"):
        assert root.findChild(QtWidgets.QWidget, name) is None, f"{name} sollte vor dem Laden fehlen"

    load_preview_uis(handler)

    for name in ("previewWidget", "previewSliceWidget", "btn_slice_view"):
        assert root.findChild(QtWidgets.QWidget, name) is not None, f"{name} sollte nach dem Laden vorhanden sein"


def test_preview_load_is_idempotent():
    root, handler = _load_root_without_preview()
    load_preview_uis(handler)
    load_preview_uis(handler)
    assert len(root.findChildren(QtWidgets.QWidget, "previewWidget")) == 1


def test_docking_removes_empty_shell_and_adds_resizable_preview_splitter():
    """Die Vorschau bleibt oben, behaelt eine brauchbare Mindesthoehe und
    laesst sich ab LES-050 bewusst gegen den Parameterbereich vergroessern."""
    root, handler = _load_full_root()
    load_preview_uis(handler)
    _dock_preview_above_scroll(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    preview = root.findChild(QtWidgets.QWidget, "previewWidget")
    assert preview.height() >= 140

    empty_shell = root.findChild(QtWidgets.QWidget, "previewPanel")
    assert empty_shell is None, "die leere Huelle muss nach dem Docking aus dem Baum entfernt sein"

    scroll = root.findChild(QtWidgets.QScrollArea, "scrollParams")
    container = root.findChild(QtWidgets.QWidget, "previewDockContainer")
    splitter = root.findChild(QtWidgets.QSplitter, "previewParamsSplitter")
    assert splitter is not None
    assert splitter.orientation() == QtCore.Qt.Vertical
    assert splitter.widget(0) is container
    assert splitter.widget(1) is scroll
    assert splitter.childrenCollapsible() is False

    initial_height = preview.height()
    splitter.setSizes([320, 180])
    _app.processEvents()
    assert preview.height() > initial_height


def test_workspace_splitter_resizes_step_column_against_editor():
    root, handler = _load_full_root()
    _install_workspace_splitter(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    step_panel = root.findChild(QtWidgets.QWidget, "stepListPanel")
    right_panel = root.findChild(QtWidgets.QWidget, "rightWorkspacePanel")
    assert splitter is not None
    assert splitter.orientation() == QtCore.Qt.Horizontal
    assert splitter.widget(0) is step_panel
    assert splitter.widget(1) is right_panel
    assert splitter.childrenCollapsible() is False

    splitter.setSizes([380, 560])
    _app.processEvents()
    wide_step = step_panel.width()
    splitter.setSizes([210, 730])
    _app.processEvents()
    assert step_panel.width() < wide_step
    assert step_panel.width() >= 190
    assert right_panel.width() >= 360
