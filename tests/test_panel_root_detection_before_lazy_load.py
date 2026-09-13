import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401  # re-exported custom widgets for uic
from lathe_easystep.ui_registry import _looks_like_panel_widget  # noqa: E402

# SICHERHEITSFUND 2026-09-13 (LES-024-Nachuntersuchung "Embedded-/
# Standalone-Laden testen"): `_looks_like_panel_widget()` entscheidet u. a.
# in eingebetteten Betrieb (Panel unter einem generisch benannten Host wie
# "MainWindow"/"VCPWindow"), OB ein Kandidat-Widget ueberhaupt die echte
# LatheEasyStep-Panel-Wurzel ist (widget_resolver.py::_pick_best_root(),
# lathe_easystep_handler.py an mehreren Stellen fuer die Embedded-Root-
# Suche). Dieser Check laeuft bereits SYNCHRON in bootstrap_widget_refs()
# (__init__), also BEVOR load_split_tab_uis()/load_step_management_uis()/
# load_preview_uis() in finalize_ui_ready() (per QTimer.singleShot(0, ...)
# erst auf dem naechsten Event-Loop-Durchlauf) das Panel vollstaendig
# nachladen. Vor der LES-024-Auslagerung war `listOperations` direkt
# statisch im Geruest vorhanden - seit dem Auslagern in
# ui_parts/stepListPanel.ui existiert es in diesem fruehen Zeitfenster
# noch NICHT. Ohne Gegenmassnahme haette das die Panel-Erkennung in genau
# dem Embedded-Szenario, fuer das dieser Mechanismus gebaut wurde,
# faelschlich verfehlt.


def test_raw_shell_without_any_lazy_loading_is_still_recognized_as_panel():
    """Reproduziert exakt das fruehe Zeitfenster: nur uic.loadUi(), noch
    KEIN load_split_tab_uis()/load_step_management_uis()/load_preview_uis()."""
    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    assert root.findChild(QtWidgets.QWidget, "listOperations") is None, (
        "Testannahme verletzt: listOperations sollte vor dem Nachladen fehlen"
    )
    assert _looks_like_panel_widget(root) is True


def test_shell_after_full_lazy_loading_is_still_recognized_as_panel():
    from lathe_easystep.ui_split import load_split_tab_uis, load_step_management_uis, load_preview_uis
    from types import SimpleNamespace

    root = uic.loadUi(os.path.join(os.path.dirname(__file__), "..", "lathe_easystep.ui"))
    handler = SimpleNamespace(
        root_widget=root,
        _split_tabs_loaded=False,
        _step_management_ui_loaded=False,
        _preview_ui_loaded=False,
        _log=lambda *_a, **_k: None,
    )
    load_split_tab_uis(handler)
    load_step_management_uis(handler)
    load_preview_uis(handler)
    assert root.findChild(QtWidgets.QWidget, "listOperations") is not None
    assert _looks_like_panel_widget(root) is True


def test_unrelated_widget_is_not_recognized_as_panel():
    unrelated = QtWidgets.QWidget()
    unrelated.setObjectName("SomeOtherHostWindow")
    assert _looks_like_panel_widget(unrelated) is False
