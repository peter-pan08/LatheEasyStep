import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.presets import validate_thread_preset_data
from lathe_easystep.preview_geometry import build_chuck_nogo_primitives
from lathe_easystep.ui_signals import connect_language_signal
from lathe_easystep.ui_signals import connect_global_form_signals
from lathe_easystep.ui_visibility import handle_global_change
from lathe_easystep.translations import TRANSLATIONS
from lathe_easystep_handler import (
    GENERAL_TOOLTIP_TRANSLATIONS,
    HandlerClass,
    LathePreviewWidget,
    build_retract_primitives,
)


def test_retract_preview_helper_accepts_absolute_xri_even_when_xi_is_zero():
    primitives = build_retract_primitives(
        {
            "xa": 50.0,
            "xi": 0.0,
            "za": 1.0,
            "zi": -100.0,
            "xri": 9.0,
            "xri_absolute": True,
        }
    )
    xs = sorted(
        {
            round(float(pr["p1"][0]), 6)
            for pr in primitives
            if isinstance(pr, dict) and pr.get("role") == "retract" and pr.get("type") == "line" and pr["p1"][0] == pr["p2"][0]
        }
    )
    assert 9.0 in xs


def test_retract_preview_uses_same_incremental_xri_semantics_as_generator():
    primitives = build_retract_primitives(
        {
            "xa": 50.0,
            "xi": 6.0,
            "za": 1.0,
            "zi": -100.0,
            "xri": 3.0,
            "xri_absolute": False,
        }
    )
    xs = sorted(
        {
            round(float(pr["p1"][0]), 6)
            for pr in primitives
            if isinstance(pr, dict) and pr.get("role") == "retract" and pr.get("type") == "line" and pr["p1"][0] == pr["p2"][0]
        }
    )
    assert 9.0 in xs


def test_display_x_to_label_reports_diameter_values():
    preview = object.__new__(LathePreviewWidget)
    preview.x_is_diameter = True
    assert preview._display_x_to_label(12.5) == 25.0


def test_language_change_does_not_mark_program_dirty():
    class _Sender:
        def objectName(self):
            return "program_language"

    class _Handler:
        def __init__(self):
            self.marked = False
            self._ui_loading = False
            self._startup_complete = False

        def sender(self):
            return _Sender()

        def _apply_machine_profile_preset(self):
            pass

        def _apply_unit_suffix(self):
            pass

        def _apply_chuck_safety_preset(self):
            pass

        def _update_program_visibility(self):
            pass

        def _update_retract_visibility(self):
            pass

        def _update_subspindle_visibility(self):
            pass

        def _update_face_visibility(self):
            pass

        def _update_spindle_mode_visibility(self):
            pass

        def _mark_dirty(self, program=False):
            self.marked = bool(program)

    handler = _Handler()
    handle_global_change(handler)
    assert handler.marked is False


def test_thread_preset_validation_rejects_incomplete_custom_payload():
    errors = validate_thread_preset_data({"label": "Benutzerdefiniert"})
    assert "major diameter must be > 0" in errors
    assert "pitch must be > 0" in errors


def test_apply_thread_preset_skips_custom_entry_without_changing_values():
    class _Spin:
        def __init__(self, value):
            self._value = float(value)

        def value(self):
            return self._value

        def setValue(self, value):
            self._value = float(value)

    class _Combo:
        def currentData(self):
            return {"label": "Benutzerdefiniert"}

    handler = object.__new__(HandlerClass)
    handler._thread_applying_standard = False
    handler.thread_standard = _Combo()
    handler.thread_depth = _Spin(0.0)
    handler.thread_first_depth = _Spin(0.0)
    handler.thread_peak_offset = _Spin(0.0)
    handler.thread_retract_r = _Spin(0.0)
    handler.thread_infeed_q = _Spin(0.0)
    handler.thread_spring_passes = _Spin(0.0)
    handler.thread_e = _Spin(0.0)
    handler.thread_l = _Spin(0.0)
    handler.thread_major_diameter = _Spin(0.0)
    handler.thread_pitch = _Spin(0.0)
    handler._log_messages = []
    handler._log = lambda message, level="info": handler._log_messages.append((level, message))
    handler._set_if_zero = types.MethodType(HandlerClass._set_if_zero, handler)

    HandlerClass._apply_thread_preset(handler, force=False)

    assert handler.thread_depth.value() == 0.0
    assert handler.thread_pitch.value() == 0.0
    assert handler._log_messages


def test_chuck_nogo_zone_starts_at_zb_and_extends_toward_chuck():
    """Realer Bug: Die Futter-Sperrzone wurde bisher komplett aus
    chuck_no_go_z_limit plus einem geschaetzten Abstand ('span') konstruiert
    und ignorierte ZB (Bearbeitungsmass) - die tatsaechliche Grenze, ab der
    das Rohteil aus dem Futter herausschaut. Die Zone muss bei ZB beginnen
    und von dort Richtung Futter (weiter negativ) reichen, nicht umgekehrt."""
    program = {
        "za": 1.0, "zi": -80.0, "zb": -60.0,
        "chuck_no_go_x_min": 0.0, "chuck_no_go_x_max": 50.0,
        "chuck_no_go_z_limit": -71.0,
    }
    prims = build_chuck_nogo_primitives(program)
    z_values = [p["p1"][1] for p in prims] + [p["p2"][1] for p in prims]
    assert -60.0 in z_values, "Sperrzone muss bei ZB (-60) beginnen"
    assert max(z_values) == -60.0, "ZB muss die naehere (weniger negative) Grenze sein"
    assert min(z_values) < -71.0, "Sperrzone muss ueber chuck_no_go_z_limit hinaus Richtung Futter reichen"


def test_apply_thread_preset_applies_real_metric_preset():
    """Regression: _populate_thread_standard_options() baute das Combo-itemData
    bisher ohne 'label' (nur 'label_key'), waehrend validate_thread_preset_data()
    zwingend ein nicht-leeres 'label' verlangt. Dadurch scheiterte JEDE
    Preset-Anwendung mit 'missing label' und Major/Pitch wurden nie
    uebernommen - real am Panel beobachtet ('thread preset skipped: missing
    label' bei jedem Klick auf 'Preset uebernehmen')."""
    class _Spin:
        def __init__(self, value):
            self._value = float(value)

        def value(self):
            return self._value

        def setValue(self, value):
            self._value = float(value)

    class _Combo:
        def currentData(self):
            # Exakt die Form, die _populate_thread_standard_options() heute baut.
            return {"label": "M10", "label_key": "thread.standard.metric.m10x1_5", "major": 10.0, "pitch": 1.5, "profile": "metric"}

    handler = object.__new__(HandlerClass)
    handler._thread_applying_standard = False
    handler.thread_standard = _Combo()
    handler.thread_depth = _Spin(0.0)
    handler.thread_first_depth = _Spin(0.0)
    handler.thread_peak_offset = _Spin(0.0)
    handler.thread_retract_r = _Spin(0.0)
    handler.thread_infeed_q = _Spin(0.0)
    handler.thread_spring_passes = _Spin(0.0)
    handler.thread_e = _Spin(0.0)
    handler.thread_l = _Spin(0.0)
    handler.thread_major_diameter = _Spin(0.0)
    handler.thread_pitch = _Spin(0.0)
    handler._log_messages = []
    handler._log = lambda message, level="info": handler._log_messages.append((level, message))
    handler._set_if_zero = types.MethodType(HandlerClass._set_if_zero, handler)

    HandlerClass._apply_thread_preset(handler, force=False)

    assert handler.thread_major_diameter.value() == 10.0
    assert handler.thread_pitch.value() == 1.5
    assert not any("skipped" in msg for _level, msg in handler._log_messages)


def test_apply_combo_translations_preserves_item_data():
    class _Combo:
        def __init__(self):
            self.items = [("Festdrehzahl (G97)", "fixed"), ("CSS (G96)", "css")]
            self._index = 1
            self._blocked = False

        def currentIndex(self):
            return self._index

        def currentData(self):
            return self.items[self._index][1]

        def count(self):
            return len(self.items)

        def itemData(self, idx, _role=None):
            return self.items[idx][1]

        def blockSignals(self, value):
            self._blocked = bool(value)

        def clear(self):
            self.items = []

        def addItem(self, text, data=None):
            self.items.append((text, data))

        def findData(self, data, _role=None):
            for idx, (_text, item_data) in enumerate(self.items):
                if item_data == data:
                    return idx
            return -1

        def setCurrentIndex(self, idx):
            self._index = idx

    combo = _Combo()
    handler = object.__new__(HandlerClass)
    handler._get_widget_by_name = lambda name: combo if name == "program_spindle_mode" else None
    handler._setup_parting_slice_strategy_items = lambda: None

    HandlerClass._apply_combo_translations(handler, "en")

    assert combo.items == [("Fixed RPM (G97)", "fixed"), ("CSS (G96)", "css")]
    assert combo.currentData() == "css"


def test_apply_language_texts_updates_all_widgets_with_same_object_name():
    class _Widget:
        def __init__(self, name):
            self._name = name
            self.text_value = None

        def objectName(self):
            return self._name

        def setText(self, text):
            self.text_value = text

    widgets = [_Widget("label_prog_npv"), _Widget("label_prog_npv")]
    handler = object.__new__(HandlerClass)
    handler._current_language_code = lambda: "en"
    handler._widgets_by_name = lambda name: widgets if name == "label_prog_npv" else []
    handler._apply_combo_translations = lambda lang: None
    handler._handle_global_change = lambda: None
    handler._apply_tab_titles = lambda lang: None
    handler._apply_button_translations = lambda lang: None
    handler._apply_general_tooltips = lambda lang: None
    handler._apply_thread_tooltips = lambda lang: None
    handler._apply_parting_tooltips = lambda lang: None
    handler._apply_groove_tooltips = lambda lang: None
    handler._apply_tooltip_fallbacks = lambda: None
    handler._update_dirty_status = lambda: None

    HandlerClass._apply_language_texts(handler)

    assert widgets[0].text_value == "Work Offset"
    assert widgets[1].text_value == "Work Offset"


def test_connect_language_signal_connects_all_language_widgets():
    class _Signal:
        def __init__(self):
            self.calls = []

        def connect(self, fn):
            self.calls.append(fn)

    class _Combo:
        def __init__(self):
            self.currentIndexChanged = _Signal()

    combos = [_Combo(), _Combo()]
    handler = types.SimpleNamespace(
        _widgets_by_name=lambda name: combos if name == "program_language" else [],
        _get_widget_by_name=lambda name: None,
        _handle_language_change=lambda *args: None,
    )

    connect_language_signal(handler)

    assert len(combos[0].currentIndexChanged.calls) == 1
    assert len(combos[1].currentIndexChanged.calls) == 1
    assert handler._language_connected is True


def test_connect_global_form_signals_ignores_non_toggle_widgets():
    class _Signal:
        def __init__(self):
            self.calls = []

        def connect(self, fn):
            self.calls.append(fn)

    class _PreviewLike:
        pass

    handler = types.SimpleNamespace(
        _connected_global_widgets=set(),
        _handle_global_change=lambda *args: None,
        _update_subspindle_visibility=lambda *args: None,
        program_npv=None,
        program_shape=None,
        program_retract_mode=None,
        program_machine_profile=None,
        program_chuck_size=None,
        program_chuck_part_type=None,
        program_chuck_grip_mode=None,
        program_chuck_profile=None,
        program_spindle_mode=None,
        program_toolchange_coords=None,
        program_park_mode=None,
        program_park_coords=None,
        program_xa=None,
        program_xi=None,
        program_za=None,
        program_zi=None,
        program_zb=None,
        program_xra=None,
        program_xri=None,
        program_zra=None,
        program_zri=None,
        program_w=None,
        program_l=None,
        program_n=None,
        program_sw=None,
        program_xt=None,
        program_zt=None,
        program_sc=None,
        program_chuck_x_min=None,
        program_chuck_x_max=None,
        program_chuck_z_limit=None,
        program_spindle_max_rpm=None,
        program_park_x=None,
        program_park_z=None,
        program_s1=None,
        program_s3=None,
        program_xra_absolute=_PreviewLike(),
        program_xri_absolute=None,
        program_zra_absolute=None,
        program_zri_absolute=None,
        program_xt_absolute=None,
        program_zt_absolute=None,
        program_has_subspindle=_PreviewLike(),
        program_park_sequential=None,
        program_optional_stop_toolchange=None,
        program_preview_warnings=None,
        program_name=None,
        program_unit=None,
    )

    connect_global_form_signals(handler)

    assert not hasattr(handler, "_program_has_subspindle_visibility_connected")


def test_connect_global_form_signals_connects_subspindle_visibility_separately():
    class _Signal:
        def __init__(self):
            self.calls = []

        def connect(self, fn):
            self.calls.append(fn)

    class _Check:
        def __init__(self):
            self.toggled = _Signal()

    check = _Check()
    handler = types.SimpleNamespace(
        _connected_global_widgets=set(),
        _handle_global_change=lambda *args: None,
        _update_subspindle_visibility=lambda *args: None,
        program_npv=None,
        program_shape=None,
        program_retract_mode=None,
        program_machine_profile=None,
        program_chuck_size=None,
        program_chuck_part_type=None,
        program_chuck_grip_mode=None,
        program_chuck_profile=None,
        program_spindle_mode=None,
        program_toolchange_coords=None,
        program_park_mode=None,
        program_park_coords=None,
        program_xa=None,
        program_xi=None,
        program_za=None,
        program_zi=None,
        program_zb=None,
        program_xra=None,
        program_xri=None,
        program_zra=None,
        program_zri=None,
        program_w=None,
        program_l=None,
        program_n=None,
        program_sw=None,
        program_xt=None,
        program_zt=None,
        program_sc=None,
        program_chuck_x_min=None,
        program_chuck_x_max=None,
        program_chuck_z_limit=None,
        program_spindle_max_rpm=None,
        program_park_x=None,
        program_park_z=None,
        program_s1=None,
        program_s3=None,
        program_xra_absolute=None,
        program_xri_absolute=None,
        program_zra_absolute=None,
        program_zri_absolute=None,
        program_xt_absolute=None,
        program_zt_absolute=None,
        program_has_subspindle=check,
        program_park_sequential=None,
        program_optional_stop_toolchange=None,
        program_preview_warnings=None,
        program_name=None,
        program_unit=None,
    )

    connect_global_form_signals(handler)

    assert len(check.toggled.calls) == 2
    assert handler._program_has_subspindle_visibility_connected is True


def test_general_tooltips_cover_upper_program_tab_fields():
    for name in (
        "program_language",
        "program_npv",
        "program_unit",
        "program_shape",
        "program_xa",
        "program_xi",
        "program_za",
        "program_zi",
        "program_zb",
        "program_w",
        "program_l",
        "program_n",
        "program_sw",
        "program_retract_mode",
    ):
        assert name in GENERAL_TOOLTIP_TRANSLATIONS
        assert GENERAL_TOOLTIP_TRANSLATIONS[name].get("de")


def test_tooltip_fallback_uses_matching_label_name():
    class _Label:
        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

    class _Widget:
        def objectName(self):
            return "face_start_x"

    handler = object.__new__(HandlerClass)
    handler._get_widget_by_name = lambda name: _Label("Start-X (Roh-Ø)") if name == "label_face_start_x" else None
    handler._form_label_for_widget = lambda widget: None

    text = HandlerClass._fallback_tooltip_text(handler, _Widget())
    assert text == "Start-X (Roh-Ø)"


def test_apply_tooltip_fallbacks_is_disabled_in_strict_i18n_mode():
    class _Label:
        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

    class _Widget:
        def __init__(self, name, tooltip=""):
            self._name = name
            self._tooltip = tooltip

        def objectName(self):
            return self._name

        def toolTip(self):
            return self._tooltip

        def setToolTip(self, text):
            self._tooltip = text

    class _Root:
        def __init__(self, widgets):
            self._widgets = widgets

        def findChildren(self, _cls):
            return self._widgets

    widgets = [_Widget("drill_depth"), _Widget("thread_pitch", "already set")]
    labels = {
        "label_drill_depth": _Label("Tiefe"),
        "label_thread_pitch": _Label("Steigung (mm)"),
    }
    handler = object.__new__(HandlerClass)
    handler.root_widget = _Root(widgets)
    handler._find_root_widget = lambda: handler.root_widget
    handler._get_widget_by_name = lambda name: labels.get(name)
    calls = []
    handler._set_tooltip_deep = lambda widget, text: (calls.append((widget.objectName(), text)), widget.setToolTip(text))
    handler._form_label_for_widget = lambda widget: None

    HandlerClass._apply_tooltip_fallbacks(handler)

    assert calls == []
    assert widgets[0].toolTip() == ""
    assert widgets[1].toolTip() == "already set"


def test_get_widget_by_name_does_not_return_preview_for_non_preview_name():
    class _Meta:
        def className(self):
            return "LathePreviewWidget"

    class _Preview:
        def objectName(self):
            return "previewWidget"

        def metaObject(self):
            return _Meta()

        def parentWidget(self):
            return None

    class _Root:
        def findChild(self, _cls, _name, _options=None):
            return None

        def findChildren(self, _cls, options=None):
            return [_Preview()]

    handler = object.__new__(HandlerClass)
    handler.w = None
    handler.root_widget = _Root()
    handler.tab_params = None
    handler._widget_name_cache = {}
    handler._find_root_widget = lambda: handler.root_widget

    assert HandlerClass._get_widget_by_name(handler, "program_language") is None


def test_get_widget_by_name_can_still_resolve_preview_widgets():
    preview = object.__new__(LathePreviewWidget)
    preview.setObjectName("previewWidget")

    class _Root:
        def findChild(self, _cls, name, _options=None):
            return preview if name == "previewWidget" else None

        def findChildren(self, _cls, options=None):
            return [preview]

    handler = object.__new__(HandlerClass)
    handler.w = None
    handler.root_widget = _Root()
    handler.tab_params = None
    handler._widget_name_cache = {}
    handler._find_root_widget = lambda: handler.root_widget

    assert HandlerClass._get_widget_by_name(handler, "previewWidget") is preview


def test_collect_program_header_ignores_wrong_checkbox_widget_types():
    class _PreviewLike:
        pass

    handler = object.__new__(HandlerClass)
    handler.program_npv = None
    handler.program_unit = None
    handler.program_shape = None
    handler.program_retract_mode = None
    handler.program_s1 = None
    handler.program_s3 = None
    handler.program_has_subspindle = _PreviewLike()
    handler.program_xt = None
    handler.program_zt = None
    handler.program_sc = None
    handler.program_name = None
    handler.program_xa = None
    handler.program_xi = None
    handler.program_za = None
    handler.program_zi = None
    handler.program_zb = None
    handler.program_w = None
    handler.program_l = None
    handler.program_n = None
    handler.program_sw = None
    handler.program_xra = None
    handler.program_xri = None
    handler.program_zra = None
    handler.program_zri = None
    handler.program_xra_absolute = _PreviewLike()
    handler.program_xri_absolute = _PreviewLike()
    handler.program_zra_absolute = _PreviewLike()
    handler.program_zri_absolute = _PreviewLike()
    handler.program_xt_absolute = _PreviewLike()
    handler.program_zt_absolute = _PreviewLike()
    handler.program_park_sequential = _PreviewLike()
    handler.program_optional_stop_toolchange = _PreviewLike()
    handler.program_preview_warnings = _PreviewLike()
    handler.program_machine_profile = None
    handler.program_chuck_size = None
    handler.program_chuck_part_type = None
    handler.program_chuck_grip_mode = None
    handler.program_chuck_profile = None
    handler.program_chuck_x_min = None
    handler.program_chuck_x_max = None
    handler.program_chuck_z_limit = None
    handler.program_spindle_mode = None
    handler.program_spindle_max_rpm = None
    handler.program_park_mode = None
    handler.program_toolchange_coords = None
    handler.program_park_coords = None
    handler.program_park_x = None
    handler.program_park_z = None
    handler._get_widget_by_name = lambda name: None
    handler._find_unit_combo = lambda: None
    handler._find_shape_combo = lambda: None

    header = HandlerClass._collect_program_header(handler)

    assert header["preview_warnings"] is False
    assert header["optional_stop_toolchange"] is False
    assert header["park_sequential"] is False
    assert header["has_subspindle"] is False


def test_translation_store_returns_key_for_missing_entry():
    missing = TRANSLATIONS.tr("missing.example.key", "de")
    assert missing == "missing.example.key"


def test_translation_store_lists_spanish_language():
    assert "es" in TRANSLATIONS.available_languages()


def test_all_static_required_keys_present_in_every_language():
    """Regression fuer real am Panel beobachtete 'missing translation key'
    Warnungen (u.a. Groove-Diagramm-Labels, Kontur-Laufzeitwerte, Gewinde-
    Presets). Fehlende Keys duerfen nicht erst beim Start im Log auffallen,
    sondern muessen hier als Testfehler sichtbar werden."""
    for lang in ("de", "en", "es"):
        missing = sorted(k for k in TRANSLATIONS.required_keys() if not TRANSLATIONS.tr(k, lang) or TRANSLATIONS.tr(k, lang) == k)
        assert missing == [], f"{lang}: missing keys {missing}"


def test_dynamic_thread_standard_keys_present_in_every_language():
    """thread_standard wird nicht aus der .ui, sondern zur Laufzeit aus den
    Presets befuellt (_populate_thread_standard_options); die dabei erzeugten
    Schluessel sind daher nicht Teil von TRANSLATIONS.required_keys() und
    muessen hier separat geprueft werden."""
    from lathe_easystep.presets.thread_presets import metric_thread_presets, trapezoidal_thread_presets

    def _compact(value):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text if text else "0"

    keys = ["combo.thread_standard.custom"]
    for name, _diameter, pitch in metric_thread_presets():
        keys.append(f"thread.standard.metric.{name.lower()}x{_compact(pitch).replace('.', '_')}")
    for name, _diameter, pitch in trapezoidal_thread_presets():
        keys.append(f"thread.standard.tr.{name.lower()}x{_compact(pitch).replace('.', '_')}")

    for lang in ("de", "en", "es"):
        missing = [k for k in keys if TRANSLATIONS.tr(k, lang) == k]
        assert missing == [], f"{lang}: missing thread_standard keys {missing}"


def test_op_fields_have_translations_for_precise_error_messages():
    """Jedes in ui_messages.OP_FIELDS gelistete Feld muss ein field.<key>
    besitzen, sonst degradiert format_user_error() stillschweigend zur
    generischen ('irgendein Pflichtfeld fehlt') Meldung - genau das war die
    beobachtete Ursache fuer zu ungenaue Fehlermeldungen beim Generieren."""
    from lathe_easystep.ui_messages import OP_FIELDS

    all_field_keys = sorted({key for keys in OP_FIELDS.values() for key in keys})
    for lang in ("de", "en", "es"):
        missing = [k for k in all_field_keys if TRANSLATIONS.tr(f"field.{k}", lang) == f"field.{k}"]
        assert missing == [], f"{lang}: missing field translations {missing}"


def test_no_duplicate_translation_keys_in_language_files():
    """Doppelte Schluessel ueberschreiben sich stillschweigend gegenseitig
    (die letzte Zeile gewinnt) und werden nur als Log-Warnung sichtbar."""
    import pathlib

    base = pathlib.Path(__file__).resolve().parent.parent / "lathe_easystep" / "languages"
    for lang in ("de", "en", "es"):
        path = base / f"{lang}.lng"
        seen = set()
        dupes = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(";") or "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in seen:
                dupes.append(key)
            seen.add(key)
        assert dupes == [], f"{lang}.lng: duplicate keys {dupes}"


def test_apply_tooltip_fallbacks_does_not_refresh_existing_tooltips():
    class _Label:
        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

    class _Widget:
        def __init__(self, name, tooltip=""):
            self._name = name
            self._tooltip = tooltip
            self._props = {}

        def objectName(self):
            return self._name

        def toolTip(self):
            return self._tooltip

        def setToolTip(self, text):
            self._tooltip = text

        def setProperty(self, key, value):
            self._props[key] = value

        def property(self, key):
            return self._props.get(key)

    class _Root:
        def __init__(self, widgets):
            self._widgets = widgets

        def findChildren(self, _cls, options=None):
            return self._widgets

    widget = _Widget("thread_pitch", "Steigung (mm)")
    widget.setProperty("tooltip_fallback_auto", True)
    handler = object.__new__(HandlerClass)
    handler.root_widget = _Root([widget])
    handler._find_root_widget = lambda: handler.root_widget
    handler._get_widget_by_name = lambda name: _Label("Pitch (mm)") if name == "label_thread_pitch" else None
    handler._form_label_for_widget = lambda current: None
    handler._set_tooltip_deep = lambda current, text: current.setToolTip(text)

    HandlerClass._apply_tooltip_fallbacks(handler)

    assert widget.toolTip() == "Steigung (mm)"
