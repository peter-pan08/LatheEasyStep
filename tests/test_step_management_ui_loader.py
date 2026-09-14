import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.ui_split import load_step_management_uis  # noqa: E402

# LES-024: Step-Liste (listOperations + Step/Programm speichern/laden) und
# Aktionsleiste (Schritt hinzufuegen/loeschen/verschieben/Programm erzeugen/
# Aenderungen speichern) wurden aus dem Geruest (lathe_easystep.ui) in
# eigene .ui-Fragmente ausgelagert (ui_parts/stepListPanel.ui,
# ui_parts/stepActionsPanel.ui), analog zum bestehenden Reiter-Split.
# Alle objectNames blieben identisch - dieser Test stellt sicher, dass sie
# nach dem Laden weiterhin auffindbar sind (sonst wuerde jeder Widget-
# Lookup im Handler leer laufen, ohne dass das automatisierte Stub-Tests
# aufgefallen waere, da die dort verwendeten Handler-Fixtures Widgets
# direkt als Python-Attribute setzen statt sie ueber echtes uic.loadUi zu
# suchen).


def _load_root_without_step_management():
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _step_management_ui_loaded=False, _log=lambda *_a, **_k: None)
    return root, handler


def test_step_management_widgets_missing_before_load_present_after():
    root, handler = _load_root_without_step_management()

    for name in ("listOperations", "btn_save_step", "btn_load_step", "btn_save_program",
                 "btn_load_program", "btnAdd", "btnDelete", "btnMoveUp", "btnMoveDown",
                 "btnNewProgram", "btnGenerate", "btnSaveChanges"):
        assert root.findChild(QtWidgets.QWidget, name) is None, f"{name} sollte vor dem Laden fehlen"

    load_step_management_uis(handler)

    for name in ("listOperations", "btn_save_step", "btn_load_step", "btn_save_program",
                 "btn_load_program", "btnAdd", "btnDelete", "btnMoveUp", "btnMoveDown",
                 "btnNewProgram", "btnGenerate", "btnSaveChanges"):
        widget = root.findChild(QtWidgets.QWidget, name)
        assert widget is not None, f"{name} sollte nach dem Laden vorhanden sein"

    assert handler.list_ops is root.findChild(QtWidgets.QListWidget, "listOperations")
    assert handler.list_ops.count() == 0


def test_step_management_load_is_idempotent():
    """Zweiter Aufruf (z.B. durch mehrfach getriggertes _finalize_ui_ready)
    darf den Inhalt nicht duplizieren."""
    root, handler = _load_root_without_step_management()
    load_step_management_uis(handler)
    load_step_management_uis(handler)

    assert len(root.findChildren(QtWidgets.QListWidget, "listOperations")) == 1
    assert len(root.findChildren(QtWidgets.QPushButton, "btnAdd")) == 1


def test_step_management_buttons_keep_expected_german_labels():
    root, handler = _load_root_without_step_management()
    load_step_management_uis(handler)

    btn_add = root.findChild(QtWidgets.QPushButton, "btnAdd")
    btn_save_changes = root.findChild(QtWidgets.QPushButton, "btnSaveChanges")
    assert btn_add.text() == "Schritt hinzufügen"
    assert btn_save_changes.text() == "Änderungen speichern"
