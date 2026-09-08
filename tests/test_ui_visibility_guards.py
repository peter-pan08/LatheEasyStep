import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.ui_visibility import chuck_size_mm


class _BoolWidget:
    def __init__(self):
        self.visible = None

    def setVisible(self, value):
        self.visible = bool(value)


class _ComboByIndex:
    def __init__(self, idx=0, data=None):
        self._idx = idx
        self._data = data
        self.visible = None

    def currentIndex(self):
        return self._idx

    def currentData(self):
        return self._data

    def setVisible(self, value):
        self.visible = bool(value)


class _Check:
    def __init__(self, checked):
        self._checked = bool(checked)

    def isChecked(self):
        return self._checked


class _Root:
    def __init__(self, mapping):
        self._mapping = mapping

    def findChild(self, _cls, name, *_args, **_kwargs):
        return self._mapping.get(name)


class _ChuckCombo:
    def __init__(self, *, data=None, text="", idx=0, item_data=None):
        self._data = data
        self._text = text
        self._idx = idx
        self._item_data = item_data

    def currentData(self):
        return self._data

    def currentText(self):
        return self._text

    def currentIndex(self):
        return self._idx

    def itemData(self, _idx, _role=None):
        return self._item_data


def test_face_visibility_shows_finish_direction_for_finish_mode():
    handler = SimpleNamespace(
        w={},
        face_mode=_ComboByIndex(data="finish"),
        face_edge_type=_ComboByIndex(data="none"),
        label_face_finish_direction=_BoolWidget(),
        face_finish_direction=_BoolWidget(),
        label_face_edge_size=_BoolWidget(),
        face_edge_size=_BoolWidget(),
        label_face_chamfer=_BoolWidget(),
        face_chamfer=_BoolWidget(),
        label_face_radius=_BoolWidget(),
        face_radius=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_face_visibility

    update_face_visibility(handler)

    assert handler.label_face_finish_direction.visible is True
    assert handler.face_finish_direction.visible is True
    assert handler.face_edge_size.visible is False
    assert handler.face_chamfer.visible is False
    assert handler.face_radius.visible is False


def test_face_visibility_prefers_radius_widget_for_radius_edge():
    handler = SimpleNamespace(
        w={},
        face_mode=_ComboByIndex(data="rough"),
        face_edge_type=_ComboByIndex(data="radius"),
        label_face_finish_direction=_BoolWidget(),
        face_finish_direction=_BoolWidget(),
        label_face_edge_size=_BoolWidget(),
        face_edge_size=_BoolWidget(),
        label_face_chamfer=_BoolWidget(),
        face_chamfer=_BoolWidget(),
        label_face_radius=_BoolWidget(),
        face_radius=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_face_visibility

    update_face_visibility(handler)

    assert handler.label_face_finish_direction.visible is False
    assert handler.face_finish_direction.visible is False
    assert handler.label_face_radius.visible is True
    assert handler.face_radius.visible is True
    assert handler.face_edge_size.visible is False
    assert handler.face_chamfer.visible is False


def test_drill_visibility_shows_dwell_only_for_g82():
    handler = SimpleNamespace(
        w={},
        drill_mode=_ComboByIndex(idx=1),
        label_drill_dwell=_BoolWidget(),
        drill_dwell=_BoolWidget(),
        label_drill_peck_depth=_BoolWidget(),
        drill_peck_depth=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_drill_visibility

    update_drill_visibility(handler)

    assert handler.label_drill_dwell.visible is True
    assert handler.drill_dwell.visible is True
    assert handler.label_drill_peck_depth.visible is False
    assert handler.drill_peck_depth.visible is False


def test_drill_visibility_shows_peck_only_for_g83_g73():
    handler = SimpleNamespace(
        w={},
        drill_mode=_ComboByIndex(idx=2),
        label_drill_dwell=_BoolWidget(),
        drill_dwell=_BoolWidget(),
        label_drill_peck_depth=_BoolWidget(),
        drill_peck_depth=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_drill_visibility

    update_drill_visibility(handler)

    assert handler.label_drill_dwell.visible is False
    assert handler.drill_dwell.visible is False
    assert handler.label_drill_peck_depth.visible is True
    assert handler.drill_peck_depth.visible is True


def test_subspindle_visibility_uses_checkbox_state_not_label_text():
    handler = SimpleNamespace(
        program_has_subspindle=_Check(True),
        label_prog_s3=_BoolWidget(),
        program_s3=_BoolWidget(),
        root_widget=None,
        _find_root_widget=lambda: None,
    )

    from lathe_easystep.ui_visibility import update_subspindle_visibility

    update_subspindle_visibility(handler)

    assert handler.label_prog_s3.visible is True
    assert handler.program_s3.visible is True


def test_chuck_size_mm_prefers_internal_item_data_over_display_text():
    handler = SimpleNamespace(program_chuck_size=_ChuckCombo(data="125", text="irgendein Text", idx=0, item_data="80"))

    assert chuck_size_mm(handler) == 125


def test_program_visibility_for_tube_shows_xa_and_xi_only():
    widgets = {
        "label_prog_xa": _BoolWidget(),
        "program_xa": _BoolWidget(),
        "label_prog_xi": _BoolWidget(),
        "program_xi": _BoolWidget(),
        "label_prog_w": _BoolWidget(),
        "program_w": _BoolWidget(),
        "label_prog_l": _BoolWidget(),
        "program_l": _BoolWidget(),
        "label_prog_n": _BoolWidget(),
        "program_n": _BoolWidget(),
        "label_prog_sw": _BoolWidget(),
        "program_sw": _BoolWidget(),
    }
    handler = SimpleNamespace(
        widgets={},
        root_widget=_Root(widgets),
        _find_root_widget=lambda: None,
        _get_widget_by_name=lambda name: widgets.get(name),
        program_shape=_ComboByIndex(data="tube"),
    )

    from lathe_easystep.ui_visibility import update_program_visibility

    update_program_visibility(handler)

    assert widgets["program_xa"].visible is True
    assert widgets["program_xi"].visible is True
    assert widgets["program_w"].visible is False
    assert widgets["program_l"].visible is False
    assert widgets["program_n"].visible is False
    assert widgets["program_sw"].visible is False


def test_program_visibility_for_polygon_shows_n_and_sw_only():
    widgets = {
        "label_prog_xa": _BoolWidget(),
        "program_xa": _BoolWidget(),
        "label_prog_xi": _BoolWidget(),
        "program_xi": _BoolWidget(),
        "label_prog_w": _BoolWidget(),
        "program_w": _BoolWidget(),
        "label_prog_l": _BoolWidget(),
        "program_l": _BoolWidget(),
        "label_prog_n": _BoolWidget(),
        "program_n": _BoolWidget(),
        "label_prog_sw": _BoolWidget(),
        "program_sw": _BoolWidget(),
    }
    handler = SimpleNamespace(
        widgets={},
        root_widget=_Root(widgets),
        _find_root_widget=lambda: None,
        _get_widget_by_name=lambda name: widgets.get(name),
        program_shape=_ComboByIndex(data="polygon"),
    )

    from lathe_easystep.ui_visibility import update_program_visibility

    update_program_visibility(handler)

    assert widgets["program_xa"].visible is False
    assert widgets["program_xi"].visible is False
    assert widgets["program_w"].visible is False
    assert widgets["program_l"].visible is False
    assert widgets["program_n"].visible is True
    assert widgets["program_sw"].visible is True


def test_retract_visibility_simple_shows_only_outer_planes():
    widgets = {name: _BoolWidget() for name in (
        "label_prog_xra", "program_xra", "program_xra_absolute",
        "label_prog_xri", "program_xri", "program_xri_absolute",
        "label_prog_zra", "program_zra", "program_zra_absolute",
        "label_prog_zri", "program_zri", "program_zri_absolute",
        "label_retract_hint",
    )}
    handler = SimpleNamespace(
        program_retract_mode=_ComboByIndex(idx=0, data="simple"),
        root_widget=_Root(widgets),
        _find_root_widget=lambda: None,
        _get_widget_by_name=lambda name: widgets.get(name),
    )

    from lathe_easystep.ui_visibility import update_retract_visibility

    update_retract_visibility(handler)

    assert widgets["program_xra"].visible is True
    assert widgets["program_zra"].visible is True
    assert widgets["program_xri"].visible is False
    assert widgets["program_zri"].visible is False


def test_retract_visibility_all_shows_all_planes():
    widgets = {name: _BoolWidget() for name in (
        "label_prog_xra", "program_xra", "program_xra_absolute",
        "label_prog_xri", "program_xri", "program_xri_absolute",
        "label_prog_zra", "program_zra", "program_zra_absolute",
        "label_prog_zri", "program_zri", "program_zri_absolute",
        "label_retract_hint",
    )}
    handler = SimpleNamespace(
        program_retract_mode=_ComboByIndex(idx=2, data="all"),
        root_widget=_Root(widgets),
        _find_root_widget=lambda: None,
        _get_widget_by_name=lambda name: widgets.get(name),
    )

    from lathe_easystep.ui_visibility import update_retract_visibility

    update_retract_visibility(handler)

    assert widgets["program_xra"].visible is True
    assert widgets["program_zra"].visible is True
    assert widgets["program_xri"].visible is True
    assert widgets["program_zri"].visible is True


def test_parting_undercut_separate_shows_undercut_tool_widgets():
    """LES-016: die 'undercut_mode == separate' Teilregel von
    update_parting_mode_visibility() (Abspanen-Reiter) war bisher ungetestet."""
    handler = SimpleNamespace(
        w={},
        parting_mode=_ComboByIndex(idx=0, data="rough"),
        parting_undercut_mode=_ComboByIndex(idx=0, data="separate"),
        label_parting_depth=_BoolWidget(),
        parting_depth_per_pass=_BoolWidget(),
        label_parting_pause=_BoolWidget(),
        parting_pause_enabled=_BoolWidget(),
        label_parting_pause_distance=_BoolWidget(),
        parting_pause_distance=_BoolWidget(),
        label_parting_slice_strategy=_BoolWidget(),
        parting_slice_strategy=_BoolWidget(),
        parting_allow_undercut=_BoolWidget(),
        label_parting_undercut_tool=_BoolWidget(),
        parting_undercut_tool=_BoolWidget(),
        label_parting_undercut_spindle=_BoolWidget(),
        parting_undercut_spindle=_BoolWidget(),
        label_parting_undercut_feed=_BoolWidget(),
        parting_undercut_feed=_BoolWidget(),
        label_parting_optional_stop_before_undercut=_BoolWidget(),
        parting_optional_stop_before_undercut=_BoolWidget(),
    )

    from lathe_easystep.ui_contour import update_parting_mode_visibility

    update_parting_mode_visibility(handler)

    assert handler.parting_undercut_tool.visible is True
    assert handler.parting_undercut_spindle.visible is True
    assert handler.parting_undercut_feed.visible is True
    assert handler.parting_optional_stop_before_undercut.visible is True


def test_parting_undercut_combined_hides_undercut_tool_widgets():
    handler = SimpleNamespace(
        w={},
        parting_mode=_ComboByIndex(idx=0, data="rough"),
        parting_undercut_mode=_ComboByIndex(idx=0, data="combined"),
        label_parting_depth=_BoolWidget(),
        parting_depth_per_pass=_BoolWidget(),
        label_parting_pause=_BoolWidget(),
        parting_pause_enabled=_BoolWidget(),
        label_parting_pause_distance=_BoolWidget(),
        parting_pause_distance=_BoolWidget(),
        label_parting_slice_strategy=_BoolWidget(),
        parting_slice_strategy=_BoolWidget(),
        parting_allow_undercut=_BoolWidget(),
        label_parting_undercut_tool=_BoolWidget(),
        parting_undercut_tool=_BoolWidget(),
        label_parting_undercut_spindle=_BoolWidget(),
        parting_undercut_spindle=_BoolWidget(),
        label_parting_undercut_feed=_BoolWidget(),
        parting_undercut_feed=_BoolWidget(),
        label_parting_optional_stop_before_undercut=_BoolWidget(),
        parting_optional_stop_before_undercut=_BoolWidget(),
    )

    from lathe_easystep.ui_contour import update_parting_mode_visibility

    update_parting_mode_visibility(handler)

    assert handler.parting_undercut_tool.visible is False
    assert handler.parting_undercut_spindle.visible is False
    assert handler.parting_undercut_feed.visible is False
    assert handler.parting_optional_stop_before_undercut.visible is False


def test_spindle_mode_visibility_shows_rpm_field_for_fixed_mode():
    """LES-013: G96/G97 ist pro Operation waehlbar (Planen/Abspanen/
    Einstich/Gewinde). Bei Festdrehzahl (G97) zeigt die Combo das
    Drehzahlfeld, nicht das Schnittgeschwindigkeitsfeld."""
    handler = SimpleNamespace(
        w={},
        face_spindle_mode=_ComboByIndex(idx=0, data="fixed"),
        face_spindle=_BoolWidget(),
        label_face_spindle=_BoolWidget(),
        face_cutting_speed=_BoolWidget(),
        label_face_cutting_speed=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_spindle_mode_visibility

    update_spindle_mode_visibility(handler)

    assert handler.face_spindle.visible is True
    assert handler.label_face_spindle.visible is True
    assert handler.face_cutting_speed.visible is False
    assert handler.label_face_cutting_speed.visible is False


def test_spindle_mode_visibility_shows_cutting_speed_field_for_css_mode():
    handler = SimpleNamespace(
        w={},
        parting_spindle_mode=_ComboByIndex(idx=1, data="css"),
        parting_spindle=_BoolWidget(),
        label_parting_spindle=_BoolWidget(),
        parting_cutting_speed=_BoolWidget(),
        label_parting_cutting_speed=_BoolWidget(),
    )

    from lathe_easystep.ui_visibility import update_spindle_mode_visibility

    update_spindle_mode_visibility(handler)

    assert handler.parting_spindle.visible is False
    assert handler.label_parting_spindle.visible is False
    assert handler.parting_cutting_speed.visible is True
    assert handler.label_parting_cutting_speed.visible is True


def test_spindle_mode_visibility_skips_tabs_without_the_widget():
    """Fehlt eine Reiter-Combo (z. B. weil noch nicht angehaengt), darf das
    keine Exception werfen - nur die Reiter mit vorhandener Combo werden
    aktualisiert."""
    handler = SimpleNamespace(w={}, _get_widget_by_name=lambda name: None)

    from lathe_easystep.ui_visibility import update_spindle_mode_visibility

    update_spindle_mode_visibility(handler)


class _Sender:
    def __init__(self, name):
        self._name = name

    def objectName(self):
        return self._name


def _make_global_change_handler(sender_name, *, ui_loading=False):
    marks = []
    return SimpleNamespace(
        sender=lambda: _Sender(sender_name),
        _ui_loading=ui_loading,
        _apply_unit_suffix=lambda: None,
        _apply_chuck_safety_preset=lambda: None,
        _update_program_visibility=lambda: None,
        _update_retract_visibility=lambda: None,
        _update_subspindle_visibility=lambda: None,
        _update_face_visibility=lambda: None,
        _update_spindle_mode_visibility=lambda: None,
        _mark_dirty=lambda **kwargs: marks.append(kwargs),
        _marks=marks,
    )


def test_handle_global_change_does_not_mark_dirty_for_language_switch():
    """LES-025: eine Sprachumschaltung darf ein Programm nicht als
    ungespeichert markieren - program_language ist als Sender explizit
    ausgenommen."""
    from lathe_easystep.ui_visibility import handle_global_change

    handler = _make_global_change_handler("program_language")
    handle_global_change(handler)
    assert handler._marks == []


def test_handle_global_change_skips_mark_dirty_while_ui_loading():
    """LES-025: waehrend das Formular programmatisch befuellt wird (Step-
    oder Programmwechsel), darf handle_global_change() trotz eines
    'echten' Sendernamens nicht als Nutzeraenderung werten."""
    from lathe_easystep.ui_visibility import handle_global_change

    handler = _make_global_change_handler("program_shape", ui_loading=True)
    handle_global_change(handler)
    assert handler._marks == []


def test_handle_global_change_marks_dirty_for_real_user_change():
    from lathe_easystep.ui_visibility import handle_global_change

    handler = _make_global_change_handler("program_shape")
    handle_global_change(handler)
    assert handler._marks == [{"program": True}]


def test_current_text_occurrences_are_limited_to_audited_fallbacks():
    root = Path(__file__).resolve().parent.parent
    audited = {
        "lathe_easystep/ui_contour.py": {
            "return handler.parting_contour.currentText().strip()",
            "current = handler.parting_contour.currentText().strip()",
        },
        "lathe_easystep/ui_tools.py": {
            'txt = combo.currentText() or ""',
        },
        "lathe_easystep/ui_visibility.py": {
            'txt = str(combo.currentText() or "").lower().strip()',
        },
        "lathe_easystep/ui_header.py": {
            'token = str(widget.currentText() or "").strip().upper()',
        },
        "lathe_easystep_handler.py": {
            'f"current=\'{self.program_retract_mode.currentText()}\'", level="info")',
            "val = data if data is not None else w.currentText()",
            "val = w.currentText()",
        },
    }

    found = {}
    for rel_path in audited:
        lines = (root / rel_path).read_text(encoding="utf-8").splitlines()
        for line in lines:
            if "currentText(" not in line:
                continue
            found.setdefault(rel_path, set()).add(line.strip())

    assert found == audited
