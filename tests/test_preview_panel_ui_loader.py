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
from lathe_easystep import ui_lifecycle  # noqa: E402
from lathe_easystep.ui_split import (  # noqa: E402
    load_preview_uis,
    load_split_tab_uis,
    load_step_management_uis,
)
from lathe_easystep.ui_lifecycle import (  # noqa: E402
    _dock_preview_above_scroll,
    _install_workspace_splitter,
)


class _FakeSettings:
    """Teilt sich einen Speicher ueber alle QSettings()-Aufrufe hinweg (wie
    das echte Backend), damit ein Speichern-dann-Wiederherstellen-Zyklus
    innerhalb eines Tests sinnvoll geprueft werden kann."""

    def __init__(self):
        self._values = {}

    def value(self, key, default=None, type=None):
        value = self._values.get(key, default)
        return type(value) if type is not None and value is not None else value

    def setValue(self, key, value):
        self._values[key] = value

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
    laesst sich ab LES-050 bewusst gegen den Parameterbereich vergroessern.

    Ruft `_install_workspace_splitter()` vor dem Preview-Docking auf, exakt
    wie der echte Start (`ui_lifecycle.py`) es tut - ohne den Splitter teilen
    sich Step-Spalte und rechte Spalte noch dieselbe Zeile im urspruenglichen
    Geruest-Layout, wodurch die (seit LES-050 zweizeilige) Button-Gruppe der
    Step-Spalte der Vorschau faelschlich Hoehe wegnehmen wuerde - ein reines
    Testaufbau-Artefakt, das im echten Start nicht auftritt."""
    root, handler = _load_full_root()
    _install_workspace_splitter(handler)
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


def test_docking_moves_reset_view_button_too_so_the_shell_stays_removable():
    """LES-050 Regressionsfund: `_dock_preview_above_scroll()` reparentete
    urspruenglich nur `btn_slice_view` in den neuen Controls-Bereich. Der
    neue `btn_reset_view` (Ansicht zuruecksetzen) blieb dadurch als letztes
    Kind im alten `previewPanel`-Geruest zurueck, wodurch dessen
    `findChildren()` nicht mehr leer war und die 'leere Huelle entfernen'-
    Pruefung (`not old_parent.findChildren(QtWidgets.QWidget)`) fehlschlug -
    die leere Huelle blieb sichtbar im Baum und beanspruchte wieder Platz."""
    root, handler = _load_full_root()
    _install_workspace_splitter(handler)
    load_preview_uis(handler)
    _dock_preview_above_scroll(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    reset_button = root.findChild(QtWidgets.QAbstractButton, "btn_reset_view")
    assert reset_button is not None
    container = root.findChild(QtWidgets.QWidget, "previewDockContainer")
    assert reset_button.parentWidget() is not None
    # Muss im Baum unterhalb des Dock-Containers haengen, nicht mehr im alten
    # (inzwischen entfernten) previewPanel-Geruest.
    parent = reset_button.parentWidget()
    while parent is not None and parent is not container:
        parent = parent.parentWidget()
    assert parent is container

    empty_shell = root.findChild(QtWidgets.QWidget, "previewPanel")
    assert empty_shell is None


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
    # LES-050 Regressionsfund: 190/360 lagen unter dem tatsaechlichen
    # minimumSizeHint der zweispaltigen Button-Grids (stepListPanel/
    # stepActionsPanel) und quetschten deren Buttons unter die Textbreite.
    assert step_panel.width() >= 330
    assert right_panel.width() >= 380


def test_workspace_splitter_restores_saved_sizes_from_settings(monkeypatch):
    """LES-050 letzter offener Punkt: eine aus einer frueheren Sitzung
    gemerkte Aufteilung muss beim naechsten Start wieder angewendet werden
    statt stets bei der festen Standardaufteilung (340/700) zu bleiben."""
    settings = _FakeSettings()
    settings.setValue(ui_lifecycle._WORKSPACE_SPLITTER_SETTINGS_KEY, "500,600")
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    root, handler = _load_full_root()
    _install_workspace_splitter(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    # stepListPanel hat den Stretchfaktor 0 (behaelt seine angeforderte
    # Groesse), rightWorkspacePanel Faktor 1 (nimmt den Rest) - die
    # gemerkte 500 muss deshalb exakt ankommen, unabhaengig von der
    # tatsaechlichen Fensterbreite.
    assert splitter.sizes()[0] == 500


def test_workspace_splitter_ignores_saved_sizes_below_minimum(monkeypatch):
    """Eine zu schmale gemerkte Aufteilung (z. B. von einem inzwischen
    entfernten Feature oder einem anderen Bildschirm) darf die Buttons nicht
    wieder unter ihre Textbreite quetschen - siehe REGRESSIONSFUND oben."""
    settings = _FakeSettings()
    settings.setValue(ui_lifecycle._WORKSPACE_SPLITTER_SETTINGS_KEY, "50,50")
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    root, handler = _load_full_root()
    _install_workspace_splitter(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    step_panel = root.findChild(QtWidgets.QWidget, "stepListPanel")
    right_panel = root.findChild(QtWidgets.QWidget, "rightWorkspacePanel")
    assert step_panel.width() >= 330
    assert right_panel.width() >= 380


def test_workspace_splitter_persists_sizes_when_dragged(monkeypatch):
    settings = _FakeSettings()
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    root, handler = _load_full_root()
    _install_workspace_splitter(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    splitter = root.findChild(QtWidgets.QSplitter, "workspaceSplitter")
    # moveSplitter() simuliert das Ziehen am Splitter-Griff per Hand - anders
    # als setSizes() loest es zuverlaessig das splitterMoved-Signal aus, an
    # das die Persistenz gebunden ist (empirisch geprueft).
    splitter.moveSplitter(450, 1)
    _app.processEvents()

    expected = ",".join(str(size) for size in splitter.sizes())
    assert settings.value(ui_lifecycle._WORKSPACE_SPLITTER_SETTINGS_KEY, "", type=str) == expected


def test_preview_params_splitter_restores_saved_sizes_from_settings(monkeypatch):
    """Wie test_workspace_splitter_restores_saved_sizes_from_settings, aber
    fuer den vertikalen Vorschau-/Parameter-Splitter. Da beide Seiten hier
    unterschiedliche Stretchfaktoren/Mindesthoehen als beim horizontalen
    Splitter haben, wird nicht auf einen fixen Pixelwert geprueft, sondern
    gegen denselben Aufbau ohne gemerkte Werte verglichen - eine wirkungslose
    _restore_splitter_sizes()-Anbindung wuerde in beiden Faellen zum
    identischen Ergebnis fuehren."""

    def build(saved_value):
        settings = _FakeSettings()
        if saved_value is not None:
            settings.setValue(ui_lifecycle._PREVIEW_PARAMS_SPLITTER_SETTINGS_KEY, saved_value)
        monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

        root, handler = _load_full_root()
        _install_workspace_splitter(handler)
        load_preview_uis(handler)
        _dock_preview_above_scroll(handler)

        root.resize(1000, 700)
        root.show()
        _app.processEvents()

        splitter = root.findChild(QtWidgets.QSplitter, "previewParamsSplitter")
        return tuple(splitter.sizes())

    baseline = build(None)
    restored = build("500,300")
    assert restored != baseline


def test_preview_params_splitter_persists_sizes_when_dragged(monkeypatch):
    settings = _FakeSettings()
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    root, handler = _load_full_root()
    _install_workspace_splitter(handler)
    load_preview_uis(handler)
    _dock_preview_above_scroll(handler)

    root.resize(1000, 700)
    root.show()
    _app.processEvents()

    splitter = root.findChild(QtWidgets.QSplitter, "previewParamsSplitter")
    splitter.moveSplitter(250, 1)
    _app.processEvents()

    expected = ",".join(str(size) for size in splitter.sizes())
    assert settings.value(ui_lifecycle._PREVIEW_PARAMS_SPLITTER_SETTINGS_KEY, "", type=str) == expected
