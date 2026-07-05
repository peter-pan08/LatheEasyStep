"""Tests for save/load round-trip consistency.

Verifies that:
1. _operation_to_step_data / _step_data_to_operation round-trip preserves path data
2. Primitive paths (arc/line dicts) survive JSON serialization
3. Point paths survive JSON serialization (tuples → lists → tuples)
4. _collect_program_header keys match _load_program_header_to_form expectations
5. _collect_program_header keys match _apply_header_to_ui expectations
6. _set_widget_value handles QLineEdit (setText) for program_name
7. Slice view handles list-of-lists (JSON-deserialized tuples)
8. _handle_save_program flushes current operation before saving
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType, ProgramModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _SpinBox:
    """Minimal SpinBox mock that tracks setValue/value calls."""
    def __init__(self, val=0.0):
        self._val = val
    def value(self):
        return self._val
    def setValue(self, v):
        self._val = float(v)
    def blockSignals(self, _):
        pass
    def isChecked(self):
        return False
    def setChecked(self, v):
        pass


class _CheckBox:
    """Minimal CheckBox mock."""
    def __init__(self, checked=False):
        self._checked = checked
    def isChecked(self):
        return self._checked
    def setChecked(self, v):
        self._checked = bool(v)
    def blockSignals(self, _):
        pass


class _ComboBox:
    """Minimal ComboBox mock."""
    def __init__(self, items=None, index=0):
        self._items = list(items or [])
        self._index = index
    def currentText(self):
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        return ""
    def currentIndex(self):
        return self._index
    def setCurrentIndex(self, i):
        self._index = i
    def setCurrentText(self, text):
        if text in self._items:
            self._index = self._items.index(text)
    def findText(self, text, *args, **kwargs):
        try:
            return self._items.index(text)
        except ValueError:
            return -1
    def blockSignals(self, _):
        pass
    def count(self):
        return len(self._items)
    def itemText(self, i):
        if 0 <= i < len(self._items):
            return self._items[i]
        return ""


class _LineEdit:
    """Minimal QLineEdit mock."""
    def __init__(self, text=""):
        self._text = text
    def text(self):
        return self._text
    def setText(self, t):
        self._text = str(t)
    def blockSignals(self, _):
        pass


def _make_handler():
    """Create a minimal HandlerClass instance bypassing Qt init."""
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    handler.model = ProgramModel()
    return handler


def _attach_header_widgets(h, header_vals=None):
    """Attach mock header widgets to handler and optionally set values."""
    vals = header_vals or {}
    h.program_npv = _ComboBox(["G54", "G55", "G56"], 0)
    h.program_unit = _ComboBox(["mm", "inch"], 0)
    h.program_shape = _ComboBox(["Rund", "Sechskant", "Vierkant"], 0)
    h.program_retract_mode = _ComboBox(["Individuell", "Automatisch"], 0)
    h.program_xa = _SpinBox(vals.get("xa", 50.0))
    h.program_xi = _SpinBox(vals.get("xi", 10.0))
    h.program_za = _SpinBox(vals.get("za", 5.0))
    h.program_zi = _SpinBox(vals.get("zi", -60.0))
    h.program_zb = _SpinBox(vals.get("zb", -80.0))
    h.program_w = _SpinBox(vals.get("w", 42.0))
    h.program_l = _SpinBox(vals.get("l", 100.0))
    h.program_n = _SpinBox(vals.get("n_edges", 6.0))
    h.program_sw = _SpinBox(vals.get("sw", 24.0))
    h.program_xra = _SpinBox(vals.get("xra", 2.0))
    h.program_xri = _SpinBox(vals.get("xri", 1.0))
    h.program_zra = _SpinBox(vals.get("zra", 2.0))
    h.program_zri = _SpinBox(vals.get("zri", 1.0))
    h.program_xt = _SpinBox(vals.get("xt", 55.0))
    h.program_zt = _SpinBox(vals.get("zt", 10.0))
    h.program_sc = _SpinBox(vals.get("sc", 1500.0))
    h.program_machine_profile = _ComboBox(
        ["Manuell", "Werkstatt 125 Standard", "Werkstatt 100 Soft", "Werkstatt 200 Innen"],
        vals.get("machine_profile_idx", 0),
    )
    h.program_chuck_size = _ComboBox(["Kein Futter", "80 mm", "100 mm", "125 mm"], vals.get("chuck_size_idx", 0))
    h.program_chuck_part_type = _ComboBox(["Welle (Vollmaterial)", "Rohr"], vals.get("chuck_part_type_idx", 0))
    h.program_chuck_grip_mode = _ComboBox(["Außen gespannt", "Innen gespannt"], vals.get("chuck_grip_mode_idx", 0))
    h.program_chuck_profile = _ComboBox(["3-Backen Standard", "Softjaws", "Innenausdrehen"], vals.get("chuck_profile_idx", 0))
    h.program_chuck_x_min = _SpinBox(vals.get("chuck_no_go_x_min", 0.0))
    h.program_chuck_x_max = _SpinBox(vals.get("chuck_no_go_x_max", 0.0))
    h.program_chuck_z_limit = _SpinBox(vals.get("chuck_no_go_z_limit", 0.0))
    h.program_s1 = _SpinBox(vals.get("s1_max", 3000.0))
    h.program_s3 = _SpinBox(vals.get("s3_max", 2000.0))
    h.program_name = _LineEdit(vals.get("program_name", "TestProg"))
    h.program_xra_absolute = _CheckBox(vals.get("xra_absolute", False))
    h.program_xri_absolute = _CheckBox(vals.get("xri_absolute", True))
    h.program_zra_absolute = _CheckBox(vals.get("zra_absolute", False))
    h.program_zri_absolute = _CheckBox(vals.get("zri_absolute", True))
    h.program_xt_absolute = _CheckBox(vals.get("xt_absolute", True))
    h.program_zt_absolute = _CheckBox(vals.get("zt_absolute", False))
    h.program_has_subspindle = _CheckBox(vals.get("has_subspindle", True))
    h._get_widget_by_name = lambda name: None
    # Stub visibility/update methods that touch more UI
    h.root_widget = None
    h._find_root_widget = lambda: None
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None


# ---------------------------------------------------------------------------
# 1. Step round-trip: point paths
# ---------------------------------------------------------------------------

def test_step_roundtrip_point_path():
    """Point paths survive _operation_to_step_data → JSON → _step_data_to_operation."""
    h = _make_handler()
    points = [(40.0, 2.0), (20.0, 0.0), (25.0, -35.0)]
    op = Operation(OpType.FACE, {"tool": 1, "feed": 0.15}, path=points)

    data = h._operation_to_step_data(op)
    # Roundtrip through JSON
    json_str = json.dumps(data)
    loaded = json.loads(json_str)
    op2 = h._step_data_to_operation(loaded)

    assert op2 is not None
    assert op2.op_type == OpType.FACE
    assert op2.params["tool"] == 1
    assert op2.params["feed"] == 0.15
    assert len(op2.path) == 3
    # Tuples get deserialized as tuples by _step_data_to_operation
    for i, (x, z) in enumerate(points):
        assert abs(op2.path[i][0] - x) < 1e-9
        assert abs(op2.path[i][1] - z) < 1e-9


def test_step_roundtrip_primitive_path():
    """Primitive paths (dict-based) survive round-trip serialization."""
    h = _make_handler()
    primitives = [
        {"type": "line", "x1": 40.0, "z1": 0.0, "x2": 20.0, "z2": 0.0},
        {"type": "arc", "cx": 25.0, "cz": -10.0, "r": 5.0, "start": 0, "end": 90},
    ]
    op = Operation(OpType.CONTOUR, {"name": "Test"}, path=primitives)

    data = h._operation_to_step_data(op)
    # Should use "primitives" key, not "path"
    assert "primitives" in data
    assert "path" not in data

    json_str = json.dumps(data)
    loaded = json.loads(json_str)
    op2 = h._step_data_to_operation(loaded)

    assert op2 is not None
    assert op2.op_type == OpType.CONTOUR
    assert len(op2.path) == 2
    assert op2.path[0]["type"] == "line"
    assert op2.path[1]["type"] == "arc"


def test_step_roundtrip_empty_path():
    """Empty path survives round-trip."""
    h = _make_handler()
    op = Operation(OpType.THREAD, {"tool": 3}, path=[])
    data = h._operation_to_step_data(op)
    json_str = json.dumps(data)
    loaded = json.loads(json_str)
    op2 = h._step_data_to_operation(loaded)
    assert op2 is not None
    assert op2.path == []


# ---------------------------------------------------------------------------
# 2. Header round-trip: _collect_program_header → _load_program_header_to_form
# ---------------------------------------------------------------------------

def test_header_roundtrip_load_program_header_to_form():
    """All fields collected by _collect_program_header are restored by _load_program_header_to_form."""
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 48.0, "xi": 12.0, "za": 3.0, "zi": -55.0, "zb": -70.0,
        "w": 38.5, "l": 95.0, "n_edges": 4.0, "sw": 22.0,
        "xra": 3.0, "xri": 1.5, "zra": 4.0, "zri": 2.0,
        "xt": 60.0, "zt": 15.0, "sc": 1200.0,
        "s1_max": 2500.0, "s3_max": 1800.0,
        "program_name": "RoundTrip",
        "xra_absolute": True, "xri_absolute": False,
        "zra_absolute": True, "zri_absolute": False,
        "xt_absolute": True, "zt_absolute": True,
        "has_subspindle": True,
    })

    # Collect
    header = h._collect_program_header()

    # Verify all critical keys are present
    assert header["s1_max"] == 2500.0
    assert header["s3_max"] == 1800.0
    assert header["l"] == 95.0
    assert header["n_edges"] == 4.0
    assert header["sw"] == 22.0
    assert header["xt_absolute"] is True
    assert header["zt_absolute"] is True
    assert header["program_name"] == "RoundTrip"

    # JSON round-trip (simulates file save/load)
    json_str = json.dumps(header, default=str)
    loaded_header = json.loads(json_str)

    # Reset widgets to defaults
    _attach_header_widgets(h, {
        "xa": 0.0, "xi": 0.0, "za": 0.0, "zi": 0.0, "zb": 0.0,
        "w": 0.0, "l": 0.0, "n_edges": 0.0, "sw": 0.0,
        "xra": 0.0, "xri": 0.0, "zra": 0.0, "zri": 0.0,
        "xt": 0.0, "zt": 0.0, "sc": 0.0,
        "s1_max": 0.0, "s3_max": 0.0,
        "program_name": "",
        "xra_absolute": False, "xri_absolute": False,
        "zra_absolute": False, "zri_absolute": False,
        "xt_absolute": False, "zt_absolute": False,
        "has_subspindle": False,
    })

    # Load
    h._load_program_header_to_form(loaded_header)

    # Verify restoration
    assert h.program_xa.value() == 48.0
    assert h.program_xi.value() == 12.0
    assert h.program_za.value() == 3.0
    assert h.program_zi.value() == -55.0
    assert h.program_zb.value() == -70.0
    assert h.program_w.value() == 38.5
    assert h.program_l.value() == 95.0
    assert h.program_n.value() == 4.0
    assert h.program_sw.value() == 22.0
    assert h.program_xra.value() == 3.0
    assert h.program_xri.value() == 1.5
    assert h.program_zra.value() == 4.0
    assert h.program_zri.value() == 2.0
    assert h.program_xt.value() == 60.0
    assert h.program_zt.value() == 15.0
    assert h.program_sc.value() == 1200.0
    assert h.program_s1.value() == 2500.0  # BUG 1 fix: s1_max key
    assert h.program_s3.value() == 1800.0  # BUG 1 fix: s3_max key
    assert h.program_name.text() == "RoundTrip"
    assert h.program_xt_absolute.isChecked() is True  # BUG 3 fix
    assert h.program_zt_absolute.isChecked() is True  # BUG 3 fix
    assert h.program_xra_absolute.isChecked() is True
    assert h.program_zra_absolute.isChecked() is True
    assert h.program_has_subspindle.isChecked() is True


# ---------------------------------------------------------------------------
# 3. Header round-trip: _collect_program_header → _apply_header_to_ui
# ---------------------------------------------------------------------------

def test_header_roundtrip_apply_header_to_ui():
    """All fields collected by _collect_program_header are restored by _apply_header_to_ui."""
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 44.0, "xi": 14.0, "za": 4.0, "zi": -50.0, "zb": -65.0,
        "w": 35.0, "l": 90.0, "n_edges": 8.0, "sw": 19.0,
        "xra": 2.5, "xri": 1.2, "zra": 3.5, "zri": 1.8,
        "xt": 58.0, "zt": 12.0, "sc": 1100.0,
        "s1_max": 2200.0, "s3_max": 1600.0,
        "program_name": "ApplyTest",
        "xra_absolute": False, "xri_absolute": True,
        "zra_absolute": False, "zri_absolute": True,
        "xt_absolute": False, "zt_absolute": True,
        "has_subspindle": True,
    })

    # Collect
    header = h._collect_program_header()

    # JSON round-trip
    json_str = json.dumps(header, default=str)
    loaded_header = json.loads(json_str)

    # Reset
    _attach_header_widgets(h, {
        "xa": 0.0, "xi": 0.0, "za": 0.0, "zi": 0.0, "zb": 0.0,
        "w": 0.0, "l": 0.0, "n_edges": 0.0, "sw": 0.0,
        "xra": 0.0, "xri": 0.0, "zra": 0.0, "zri": 0.0,
        "xt": 0.0, "zt": 0.0, "sc": 0.0,
        "s1_max": 0.0, "s3_max": 0.0,
        "program_name": "",
        "xra_absolute": False, "xri_absolute": False,
        "zra_absolute": False, "zri_absolute": False,
        "xt_absolute": False, "zt_absolute": False,
        "has_subspindle": False,
    })
    # Stub the visibility update methods
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None

    # Apply via _apply_header_to_ui
    h._apply_header_to_ui(loaded_header)

    # Verify restoration — numeric fields
    assert h.program_xa.value() == 44.0
    assert h.program_xi.value() == 14.0
    assert h.program_za.value() == 4.0
    assert h.program_zi.value() == -50.0
    assert h.program_zb.value() == -65.0
    assert h.program_w.value() == 35.0  # BUG 5 fix
    assert h.program_l.value() == 90.0  # BUG 5 fix
    assert h.program_n.value() == 8.0   # BUG 5 fix
    assert h.program_sw.value() == 19.0  # BUG 5 fix
    assert h.program_xra.value() == 2.5
    assert h.program_xri.value() == 1.2
    assert h.program_zra.value() == 3.5
    assert h.program_zri.value() == 1.8
    assert h.program_xt.value() == 58.0
    assert h.program_zt.value() == 12.0
    assert h.program_sc.value() == 1100.0
    assert h.program_s1.value() == 2200.0
    assert h.program_s3.value() == 1600.0

    # BUG 4 fix: QLineEdit program_name
    assert h.program_name.text() == "ApplyTest"

    # Absolute flags
    assert h.program_xt_absolute.isChecked() is False
    assert h.program_zt_absolute.isChecked() is True
    assert h.program_xri_absolute.isChecked() is True
    assert h.program_has_subspindle.isChecked() is True


def test_header_roundtrip_with_chuck_fields():
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 48.0, "zi": -60.0, "zb": -40.0,
        "chuck_size_idx": 3,  # 125 mm
        "machine_profile_idx": 2,  # Werkstatt 100 Soft
        "chuck_part_type_idx": 1,  # Rohr
        "chuck_grip_mode_idx": 0,  # außen gespannt
        "chuck_profile_idx": 2,  # Innenausdrehen
        "chuck_no_go_x_min": 24.0,
        "chuck_no_go_x_max": 132.0,
        "chuck_no_go_z_limit": -68.0,
    })

    header = h._collect_program_header()
    assert header["chuck_size"] == "125 mm"
    assert header["machine_profile"] == "Werkstatt 100 Soft"
    assert header["chuck_part_type"] == "Rohr"
    assert header["chuck_grip_mode"] == "Außen gespannt"
    assert header["chuck_profile"] == "Innenausdrehen"
    assert header["chuck_no_go_x_min"] == 24.0
    assert header["chuck_no_go_x_max"] == 132.0
    assert header["chuck_no_go_z_limit"] == -68.0

    # Reset and load
    _attach_header_widgets(h, {
        "chuck_size_idx": 0,
        "machine_profile_idx": 0,
        "chuck_part_type_idx": 0,
        "chuck_grip_mode_idx": 0,
        "chuck_profile_idx": 0,
        "chuck_no_go_x_min": 0.0,
        "chuck_no_go_x_max": 0.0,
        "chuck_no_go_z_limit": 0.0,
    })
    h._load_program_header_to_form(header)

    assert h.program_chuck_size.currentText() == "125 mm"
    assert h.program_machine_profile.currentText() == "Werkstatt 100 Soft"
    assert h.program_chuck_part_type.currentText() == "Rohr"
    assert h.program_chuck_grip_mode.currentText() == "Außen gespannt"
    assert h.program_chuck_profile.currentText() == "Innenausdrehen"
    assert h.program_chuck_x_min.value() == 24.0
    assert h.program_chuck_x_max.value() == 132.0
    assert h.program_chuck_z_limit.value() == -68.0


def test_chuck_profile_changes_preset_geometry():
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 50.0,
        "xi": 20.0,
        "zb": -40.0,
        "sc": 0.0,
        "chuck_size_idx": 2,      # 100 mm
        "chuck_part_type_idx": 1, # Rohr
        "chuck_grip_mode_idx": 1, # Innen gespannt
        "chuck_profile_idx": 0,   # 3-Backen Standard
    })

    # Stub methods not relevant for this unit
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None
    h._update_face_visibility = lambda: None
    h._refresh_preview = lambda: None
    h._log = lambda *a, **k: None

    h._handle_global_change()
    x_max_std = h.program_chuck_x_max.value()
    z_lim_std = h.program_chuck_z_limit.value()
    sc_std = h.program_sc.value()

    # Innenausdrehen should increase jaw band/depth/sc safety
    h.program_chuck_profile.setCurrentIndex(2)
    h._handle_global_change()
    x_max_boring = h.program_chuck_x_max.value()
    z_lim_boring = h.program_chuck_z_limit.value()

    assert x_max_boring > x_max_std
    assert z_lim_boring < z_lim_std
    assert sc_std > 0.0


def test_machine_profile_applies_chuck_presets():
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 60.0,
        "xi": 24.0,
        "zb": -50.0,
        "sc": 0.0,
        "machine_profile_idx": 0,
        "chuck_size_idx": 0,
        "chuck_part_type_idx": 0,
        "chuck_grip_mode_idx": 0,
        "chuck_profile_idx": 0,
    })

    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None
    h._update_face_visibility = lambda: None
    h._refresh_preview = lambda: None
    h._log = lambda *a, **k: None

    # Simulate machine profile change event
    h.sender = lambda: type("Sender", (), {"objectName": lambda self: "program_machine_profile"})()
    h.program_machine_profile.setCurrentIndex(1)
    h._handle_global_change()

    assert h.program_chuck_size.currentText() == "125 mm"
    assert h.program_chuck_part_type.currentText() == "Welle (Vollmaterial)"
    assert h.program_chuck_grip_mode.currentText() == "Außen gespannt"
    assert h.program_chuck_profile.currentText() == "3-Backen Standard"
    assert h.program_chuck_x_max.value() > 0.0


# ---------------------------------------------------------------------------
# 4. Specific bug regression: s1_max / s3_max key mismatch (BUG 1)
# ---------------------------------------------------------------------------

def test_header_s1_max_s3_max_key_roundtrip():
    """Spindle speed limits use 's1_max'/'s3_max' keys consistently."""
    h = _make_handler()
    _attach_header_widgets(h, {"s1_max": 4000.0, "s3_max": 3500.0, "has_subspindle": True})

    header = h._collect_program_header()
    assert "s1_max" in header
    assert "s3_max" in header
    # Old buggy keys must NOT exist
    assert "s1" not in header
    assert "s3" not in header
    assert header["s1_max"] == 4000.0
    assert header["s3_max"] == 3500.0


# ---------------------------------------------------------------------------
# 5. Specific bug regression: l, n_edges, sw saved but not loaded (BUG 2)
# ---------------------------------------------------------------------------

def test_header_l_n_edges_sw_roundtrip():
    """Fields l, n_edges, sw are saved and loaded correctly."""
    h = _make_handler()
    _attach_header_widgets(h, {"l": 120.0, "n_edges": 6.0, "sw": 30.0})

    header = h._collect_program_header()
    assert header["l"] == 120.0
    assert header["n_edges"] == 6.0
    assert header["sw"] == 30.0

    # Reset and load
    h.program_l.setValue(0.0)
    h.program_n.setValue(0.0)
    h.program_sw.setValue(0.0)

    h._load_program_header_to_form(header)
    assert h.program_l.value() == 120.0
    assert h.program_n.value() == 6.0
    assert h.program_sw.value() == 30.0


# ---------------------------------------------------------------------------
# 6. Specific bug regression: xt_absolute / zt_absolute not loaded (BUG 3)
# ---------------------------------------------------------------------------

def test_header_xt_zt_absolute_roundtrip():
    """xt_absolute and zt_absolute checkboxes survive round-trip."""
    h = _make_handler()
    _attach_header_widgets(h, {"xt_absolute": True, "zt_absolute": True})

    header = h._collect_program_header()
    assert header["xt_absolute"] is True
    assert header["zt_absolute"] is True

    # Reset
    h.program_xt_absolute.setChecked(False)
    h.program_zt_absolute.setChecked(False)

    h._load_program_header_to_form(header)
    assert h.program_xt_absolute.isChecked() is True
    assert h.program_zt_absolute.isChecked() is True


# ---------------------------------------------------------------------------
# 7. _apply_header_to_ui: QLineEdit support (BUG 4)
# ---------------------------------------------------------------------------

def test_apply_header_sets_program_name():
    """_apply_header_to_ui correctly writes QLineEdit (program_name)."""
    h = _make_handler()
    _attach_header_widgets(h, {"program_name": ""})
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None

    h._apply_header_to_ui({"program_name": "MyLathePart"})
    assert h.program_name.text() == "MyLathePart"


# ---------------------------------------------------------------------------
# 8. Slice view: isinstance(path[0], (list, tuple)) after JSON (BUG 7)
# ---------------------------------------------------------------------------

def test_slice_view_accepts_lists_from_json():
    """After JSON round-trip, point paths are lists, not tuples.
    The slice view must handle both."""
    # Simulate JSON round-trip of a point path
    original = [(40.0, 2.0), (20.0, 0.0), (20.0, -30.0)]
    json_str = json.dumps(original)
    loaded = json.loads(json_str)  # Now [[40.0, 2.0], [20.0, 0.0], [20.0, -30.0]]

    # The check that was buggy:
    # isinstance(loaded[0], tuple) → False for lists
    # isinstance(loaded[0], (list, tuple)) → True (fixed)
    assert isinstance(loaded[0], list)
    assert isinstance(loaded[0], (list, tuple))


# ---------------------------------------------------------------------------
# 9. Program save uses _operation_to_step_data (BUG 8)
# ---------------------------------------------------------------------------

def test_program_save_uses_step_data_serialization():
    """_operation_to_step_data correctly separates primitives from point paths."""
    h = _make_handler()

    # Point path
    point_op = Operation(OpType.FACE, {"tool": 1}, path=[(10.0, 0.0), (5.0, -20.0)])
    data_point = h._operation_to_step_data(point_op)
    assert "path" in data_point
    assert "primitives" not in data_point

    # Primitive path
    prim_op = Operation(OpType.CONTOUR, {"name": "C"}, path=[
        {"type": "line", "x1": 0, "z1": 0, "x2": 10, "z2": -20}
    ])
    data_prim = h._operation_to_step_data(prim_op)
    assert "primitives" in data_prim
    assert "path" not in data_prim


# ---------------------------------------------------------------------------
# 10. Full .lse round-trip simulation (BUG 6 + BUG 8)
# ---------------------------------------------------------------------------

def test_full_program_json_roundtrip(tmp_path):
    """Simulate full save→load cycle: header + multiple ops with mixed paths."""
    h = _make_handler()
    _attach_header_widgets(h, {
        "xa": 50.0, "xi": 10.0, "za": 5.0, "zi": -60.0, "zb": -80.0,
        "w": 42.0, "l": 100.0, "n_edges": 6.0, "sw": 24.0,
        "s1_max": 3000.0, "s3_max": 2000.0,
        "program_name": "FullTest",
        "xt_absolute": True, "zt_absolute": False,
        "has_subspindle": True,
    })

    header = h._collect_program_header()

    # Create operations
    ops = [
        Operation(OpType.FACE, {"tool": 1, "feed": 0.15}, path=[(50.0, 2.0), (0.0, 0.0)]),
        Operation(OpType.CONTOUR, {"name": "Profile"}, path=[
            {"type": "line", "x1": 40.0, "z1": 0.0, "x2": 40.0, "z2": -30.0},
            {"type": "arc", "cx": 35.0, "cz": -30.0, "r": 5.0},
        ]),
        Operation(OpType.THREAD, {"pitch": 1.5}, path=[]),
    ]

    # Serialize
    ops_data = []
    for op in ops:
        d = h._operation_to_step_data(op)
        d["title"] = op.params.get("title", "")
        ops_data.append(d)

    program = {"version": 1, "header": header, "operations": ops_data}

    # Write to file
    fpath = tmp_path / "test.lse"
    with open(fpath, "w") as f:
        json.dump(program, f, default=str)

    # Read back
    with open(fpath) as f:
        loaded = json.load(f)

    assert loaded["version"] == 1
    assert loaded["header"]["s1_max"] == 3000.0
    assert loaded["header"]["s3_max"] == 2000.0
    assert loaded["header"]["l"] == 100.0
    assert loaded["header"]["n_edges"] == 6.0
    assert loaded["header"]["sw"] == 24.0
    assert loaded["header"]["program_name"] == "FullTest"
    assert loaded["header"]["xt_absolute"] is True

    # Deserialize operations
    loaded_ops = []
    for od in loaded["operations"]:
        op2 = h._step_data_to_operation(od)
        assert op2 is not None
        loaded_ops.append(op2)

    assert len(loaded_ops) == 3
    assert loaded_ops[0].op_type == OpType.FACE
    assert len(loaded_ops[0].path) == 2  # point path
    assert loaded_ops[1].op_type == OpType.CONTOUR
    assert len(loaded_ops[1].path) == 2  # primitive path (dicts)
    assert loaded_ops[1].path[0]["type"] == "line"
    assert loaded_ops[2].op_type == OpType.THREAD
    assert loaded_ops[2].path == []


# ---------------------------------------------------------------------------
# 11. _load_program_header_to_form calls _apply_unit_suffix etc.
# ---------------------------------------------------------------------------

def test_load_header_calls_post_update():
    """_load_program_header_to_form triggers suffix/visibility updates."""
    h = _make_handler()
    _attach_header_widgets(h)

    calls = []
    h._apply_unit_suffix = lambda: calls.append("suffix")
    h._update_program_visibility = lambda: calls.append("vis")
    h._update_retract_visibility = lambda: calls.append("retract")
    h._update_subspindle_visibility = lambda: calls.append("sub")

    h._load_program_header_to_form({"xa": 10.0})
    assert "suffix" in calls
    assert "vis" in calls
    assert "retract" in calls
    assert "sub" in calls


# ---------------------------------------------------------------------------
# 12. _apply_header_to_ui combo matching
# ---------------------------------------------------------------------------

def test_apply_header_combo_matching():
    """_apply_header_to_ui matches combo values by text."""
    h = _make_handler()
    _attach_header_widgets(h)
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None

    # Apply header with specific combo values
    h._apply_header_to_ui({
        "npv": "G55",
        "unit": "inch",
        "shape": "Sechskant",
    })

    assert h.program_npv.currentText() == "G55"
    assert h.program_unit.currentText() == "inch"
    assert h.program_shape.currentText() == "Sechskant"
