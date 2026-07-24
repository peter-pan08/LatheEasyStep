import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep_handler import (
    HandlerClass,
    OpType,
    Operation,
    build_keyway_slot_angles,
    default_slice_z_for_operation,
    front_view_polar_to_cartesian,
)


def test_keyway_slot_angles_default_to_even_distribution():
    angles = build_keyway_slot_angles({
        "slot_count": 3,
        "slot_start_angle": 15.0,
        "slot_angle_step": 0.0,
    })

    deg = [round(math.degrees(a), 6) for a in angles]
    assert deg == [15.0, 135.0, 255.0]


def test_keyway_slot_angles_respect_explicit_angle_offset():
    angles = build_keyway_slot_angles({
        "slot_count": 4,
        "slot_start_angle": 10.0,
        "slot_angle_step": 65.0,
    })

    deg = [round(math.degrees(a), 6) for a in angles]
    assert deg == [10.0, 75.0, 140.0, 205.0]


def test_keyway_slot_angles_use_offset_between_each_repetition():
    angles = build_keyway_slot_angles({
        "slot_count": 3,
        "slot_start_angle": 0.0,
        "slot_angle_step": 30.0,
    })

    deg = [round(math.degrees(a), 6) for a in angles]
    assert deg == [0.0, 30.0, 60.0]


def test_front_view_angle_uses_clockface_orientation():
    assert tuple(round(v, 9) for v in front_view_polar_to_cartesian(math.radians(0.0), 2.0)) == (0.0, -2.0)
    assert tuple(round(v, 9) for v in front_view_polar_to_cartesian(math.radians(90.0), 2.0)) == (2.0, 0.0)
    assert tuple(round(v, 9) for v in front_view_polar_to_cartesian(math.radians(180.0), 2.0)) == (0.0, 2.0)


def test_default_slice_z_for_axial_keyway_uses_slot_center():
    op = Operation(
        OpType.KEYWAY,
        params={
            "mode": 0,
            "start_z": 12.0,
            "nut_length": 20.0,
        },
        path=[],
    )

    assert default_slice_z_for_operation(op) == 2.0


def test_collect_params_refreshes_keyway_widget_mapping():
    h = object.__new__(HandlerClass)
    h._get_widget_by_name = lambda name: None
    h._setup_param_maps()

    params = h.param_widgets[OpType.KEYWAY]

    assert "slot_width" in params
    assert "cutting_width" in params


class _FakeSpinBox:
    def __init__(self, name):
        self._name = name
        self.suffix = None

    def objectName(self):
        return self._name

    def setSuffix(self, suffix):
        self.suffix = suffix


class _FakeLabel:
    def text(self):
        return ""


class _FakeRoot:
    def __init__(self, spinboxes):
        self.spinboxes = spinboxes

    def findChildren(self, cls):
        return self.spinboxes

    def window(self):
        return self


class _FakeUnitCombo:
    def currentIndex(self):
        return 0


class _FakePreview:
    def __init__(self):
        self.view_mode = None
        self.slice_enabled = None
        self.slice_z = None

    def set_slice_enabled(self, enabled):
        self.slice_enabled = enabled

    def set_view_mode(self, mode):
        self.view_mode = mode

    def set_slice_z(self, value, emit=False):
        self.slice_z = value


class _FakeButton:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class _FakeVisible:
    def __init__(self):
        self.visible = None

    def setVisible(self, visible):
        self.visible = visible

    def isVisible(self):
        return bool(self.visible)


def test_apply_unit_suffix_keeps_angle_fields_in_degrees():
    h = object.__new__(HandlerClass)
    h.program_unit = _FakeUnitCombo()
    angle_a = _FakeSpinBox("key_slot_start_angle")
    angle_b = _FakeSpinBox("key_slot_angle_step")
    feed = _FakeSpinBox("key_plunge_feed")
    length = _FakeSpinBox("key_start_z")
    spindle = _FakeSpinBox("program_s1")
    h.root_widget = _FakeRoot([angle_a, angle_b, feed, length, spindle])
    h._verbose_widget_logs = False
    h._log = lambda *args, **kwargs: None
    h._labels_cleaned = True

    h._apply_unit_suffix()

    assert angle_a.suffix == " °"
    assert angle_b.suffix == " °"
    assert feed.suffix == " mm/U"
    assert length.suffix == " mm"
    assert spindle.suffix == ""


def test_toggle_slice_view_switches_main_preview_mode():
    h = object.__new__(HandlerClass)
    h.preview = _FakePreview()
    h.preview_slice = _FakeVisible()
    h.btn_slice_view = _FakeButton()
    h._sync_slice_widget = lambda: None
    h._suggest_slice_z_for_preview = lambda op=None: 5.0

    h._on_toggle_slice_view(True)
    assert h.preview.slice_enabled is True
    assert h.preview.view_mode == "side"
    assert h.preview.slice_z == 5.0
    assert h.preview_slice.visible is True
    assert h.btn_slice_view.text == "Schnittansicht aus"

    h._on_toggle_slice_view(False)
    assert h.preview.slice_enabled is False
    assert h.preview.view_mode == "side"
    assert h.preview_slice.visible is False
    assert h.btn_slice_view.text == "Schnittansicht"
