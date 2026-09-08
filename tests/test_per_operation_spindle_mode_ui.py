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

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtWidgets, uic  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

import lathe_easystep_handler  # noqa: E402,F401
from lathe_easystep.model import OpType, Operation  # noqa: E402
from lathe_easystep.translations import TRANSLATIONS  # noqa: E402
from lathe_easystep.ui_operations import load_operation_params_to_form  # noqa: E402
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


@pytest.mark.parametrize("prefix", ["face", "parting", "groove", "thread"])
def test_freshly_created_widgets_are_both_visible_until_visibility_update_runs(prefix):
    """Realer Bugreport: 'es darf nur einer der beiden Werte sichtbar sein,
    niemals beide gleichzeitig'. Dokumentiert die Ursache: ensure_advanced_
    widgets() legt die Felder dynamisch an, Qt-Widgets sind direkt nach dem
    Erzeugen standardmaessig sichtbar - ohne einen expliziten Aufruf von
    update_spindle_mode_visibility() DANACH sind Drehzahl- UND
    Schnittgeschwindigkeitsfeld gleichzeitig sichtbar (siehe Fix in
    ui_lifecycle.py::_finalize_ui_ready, direkt nach ensure_advanced_widgets)."""
    handler = _load_handler_with_widgets()
    rpm_field = handler._get_widget_by_name(f"{prefix}_spindle")
    vc_field = getattr(handler, f"{prefix}_cutting_speed")
    assert not rpm_field.isHidden()
    assert not vc_field.isHidden()

    update_spindle_mode_visibility(handler)
    assert not rpm_field.isHidden()
    assert vc_field.isHidden()


@pytest.mark.parametrize("prefix", ["face", "parting", "groove", "thread"])
def test_missing_spindle_mode_resets_to_fixed_instead_of_keeping_stale_value(prefix):
    """Realer Bugreport: 'die Umschaltung der Anzeige funktioniert nicht
    zuverlaessig'. Eine Operation ohne gespeicherten spindle_mode (z. B. aus
    einer alten Datei) liess die Combo bisher auf dem Wert der zuvor
    angezeigten Operation stehen - schaltet man von einer CSS-Operation auf
    eine Operation ohne spindle_mode um, blieb faelschlich "CSS" (und damit
    das Schnittgeschwindigkeitsfeld statt des Drehzahlfelds) sichtbar."""
    handler = _load_handler_with_widgets()
    handler.param_widgets = {
        OpType.FACE: {"spindle_mode": handler.face_spindle_mode},
        OpType.ABSPANEN: {"spindle_mode": handler.parting_spindle_mode},
        OpType.GROOVE: {"spindle_mode": handler.groove_spindle_mode},
        OpType.THREAD: {"spindle_mode": handler.thread_spindle_mode},
    }
    handler._setup_param_maps = lambda: None
    op_type = {"face": OpType.FACE, "parting": OpType.ABSPANEN, "groove": OpType.GROOVE, "thread": OpType.THREAD}[prefix]
    combo = getattr(handler, f"{prefix}_spindle_mode")

    combo.setCurrentIndex(1)  # simuliert vorherige CSS-Operation
    assert combo.currentData() == "css"

    load_operation_params_to_form(handler, Operation(op_type, {}))
    assert combo.currentData() == "fixed"


@pytest.mark.parametrize("selected", ["off", "suggest_din_relief"])
def test_thread_relief_norm_visibility_survives_roundtrip_and_translation(selected):
    from lathe_easystep.persistence import operation_to_step_data, step_data_to_operation
    from lathe_easystep.ui_visibility import update_thread_relief_visibility
    from lathe_easystep.ui_static import apply_ui_static_translations
    handler = _load_handler_with_widgets()
    mode = handler.thread_relief_mode
    norm = handler.thread_relief_norm
    handler._setup_param_maps = lambda: None
    handler.param_widgets = {OpType.THREAD: {"relief_mode": mode, "relief_norm": norm}}
    op = Operation(OpType.THREAD, {"relief_mode": selected, "relief_norm": "din76_b"})
    restored = step_data_to_operation(operation_to_step_data(op))
    load_operation_params_to_form(handler, restored)
    assert mode.currentData() == selected
    assert norm.currentData() == "din76_b"
    assert norm.isHidden() == (selected == "off")
    for lang in ("de", "en", "es"):
        apply_ui_static_translations(handler.root_widget, TRANSLATIONS.tr, lang)
        update_thread_relief_visibility(handler)
        assert mode.currentData() == selected
        assert norm.currentData() == "din76_b"
        assert norm.isHidden() == (selected == "off")
    mode.setCurrentIndex(mode.findData("off" if selected == "suggest_din_relief" else "suggest_din_relief"))
    assert norm.isHidden() == (selected == "suggest_din_relief")


def test_legacy_thread_relief_ids_load_into_current_combos():
    handler = _load_handler_with_widgets()
    handler._setup_param_maps = lambda: None
    handler.param_widgets = {OpType.THREAD: {"relief_mode": handler.thread_relief_mode,
                                             "relief_norm": handler.thread_relief_norm}}
    load_operation_params_to_form(handler, Operation(OpType.THREAD, {"relief_mode": "suggest", "relief_norm": "DIN 76-B"}))
    assert handler.thread_relief_mode.currentData() == "suggest_din_relief"
    assert handler.thread_relief_norm.currentData() == "din76_b"
    assert not handler.thread_relief_norm.isHidden()
