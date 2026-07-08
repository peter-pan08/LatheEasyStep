"""Tests for double-click on step and delete step in operation list.

Verifies that:
1. Double-clicking a step saves current changes (flush)
2. Switches to the correct tab
3. Loads the operation's params into the form widgets
4. Works for all operation types
5. Delete removes the selected step, not the last one
6. _handle_selection_change always resets _ui_loading (no leak)
"""
import os
import sys
from weakref import WeakSet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType, ProgramModel


# ---------------------------------------------------------------------------
# Minimal mocks
# ---------------------------------------------------------------------------

class _Signal:
    def __init__(self):
        self.calls = []

    def connect(self, fn, *args, **kwargs):
        self.calls.append(fn)


class _SpinBox:
    def __init__(self, val=0.0):
        self._val = val
        self.valueChanged = _Signal()
    def value(self):
        return self._val
    def setValue(self, v):
        self._val = float(v)
    def blockSignals(self, _):
        pass

class _CheckBox:
    def __init__(self, checked=False):
        self._checked = checked
        self.toggled = _Signal()
    def isChecked(self):
        return self._checked
    def setChecked(self, v):
        self._checked = bool(v)
    def blockSignals(self, _):
        pass

class _ComboBox:
    def __init__(self, items=None, index=0):
        self._items = list(items or [])
        self._index = index
        self.currentIndexChanged = _Signal()
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
        return self._items[i] if 0 <= i < len(self._items) else ""

class _LineEdit:
    def __init__(self, text=""):
        self._text = text
    def text(self):
        return self._text
    def setText(self, t):
        self._text = str(t)
    def blockSignals(self, _):
        pass

class _ListItem:
    def __init__(self, text=""):
        self._text = text
    def text(self):
        return self._text
    def setText(self, t):
        self._text = str(t)

class _ListWidget:
    """Minimal mock of QListWidget."""
    def __init__(self):
        self._items = []
        self._current_row = -1
    def addItem(self, text):
        self._items.append(_ListItem(text))
    def count(self):
        return len(self._items)
    def currentRow(self):
        return self._current_row
    def setCurrentRow(self, i):
        self._current_row = i
    def row(self, item):
        try:
            return self._items.index(item)
        except ValueError:
            return -1
    def item(self, i):
        if 0 <= i < len(self._items):
            return self._items[i]
        return None
    def hasFocus(self):
        return True
    def blockSignals(self, _):
        pass
    def clear(self):
        self._items.clear()
        self._current_row = -1
    def objectName(self):
        return "listOperations"
    def scrollToItem(self, item):
        pass

class _TabWidget:
    def __init__(self, n=8):
        self._index = 0
        self._n = n
    def count(self):
        return self._n
    def setCurrentIndex(self, i):
        self._index = i
    def currentIndex(self):
        return self._index
    def widget(self, i):
        return None


def _make_handler():
    """Create a minimal HandlerClass bypassing Qt init."""
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    h = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    h.model = ProgramModel()
    h.root_widget = None
    h._find_root_widget = lambda: None
    h._ui_loading = False
    h._op_row_user_selected = False
    h.list_ops = _ListWidget()
    h.tab_params = _TabWidget()
    h.param_widgets = {}
    h._connected_param_widgets = WeakSet()
    h._connected_global_widgets = WeakSet()
    # Stub methods that touch deeper UI
    h._refresh_preview = lambda: None
    h._update_face_visibility = lambda: None
    h._update_retract_visibility = lambda: None
    h._apply_unit_suffix = lambda: None
    h._update_program_visibility = lambda: None
    h._update_subspindle_visibility = lambda: None
    h._update_parting_contour_choices = lambda: None
    h._update_parting_ready_state = lambda: None
    h._log = lambda *a, **kw: None
    h._deleting = False
    h._describe_operation = lambda op, num: f"{num}: {op.op_type}"
    return h


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_double_click_switches_tab_face():
    """Double-clicking a FACE step switches to tab index 1."""
    h = _make_handler()
    op = Operation(OpType.FACE, {"tool": 1, "feed": 0.15}, path=[])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Planen")
    h.list_ops.setCurrentRow(0)

    # Simulate double-click on item 0
    item = h.list_ops.item(0)
    h._on_step_double_clicked(item)

    assert h.tab_params.currentIndex() == 1  # FACE tab


def test_double_click_switches_tab_thread():
    """Double-clicking a THREAD step switches to tab index 4."""
    h = _make_handler()
    op = Operation(OpType.THREAD, {"pitch": 1.5}, path=[])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Gewinde")
    h.list_ops.setCurrentRow(0)

    item = h.list_ops.item(0)
    h._on_step_double_clicked(item)

    assert h.tab_params.currentIndex() == 4  # THREAD tab


def test_double_click_switches_tab_drill():
    """Double-clicking a DRILL step switches to tab index 6."""
    h = _make_handler()
    op = Operation(OpType.DRILL, {"mode": 0.0}, path=[])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Bohren")

    item = h.list_ops.item(0)
    h._on_step_double_clicked(item)

    assert h.tab_params.currentIndex() == 6  # DRILL tab


def test_double_click_loads_params_into_widgets():
    """Double-clicking a step loads its params into the corresponding form widgets."""
    h = _make_handler()

    # Set up a FACE spinbox widget for 'tool'
    tool_spin = _SpinBox(0.0)
    feed_spin = _SpinBox(0.0)
    widget_map = {"face_tool": tool_spin, "face_feed": feed_spin}
    h._get_widget_by_name = lambda name: widget_map.get(name)
    h._setup_param_maps()

    op = Operation(OpType.FACE, {"tool": 5.0, "feed": 0.22}, path=[])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Planen")

    # Double-click
    item = h.list_ops.item(0)
    h._on_step_double_clicked(item)

    assert tool_spin.value() == 5.0
    assert feed_spin.value() == 0.22


def test_keyway_param_map_prefers_bound_widgets_over_name_lookup():
    """KEYWAY param mapping must use bound widgets even when generic name lookup is unavailable."""
    h = _make_handler()

    h.key_mode = _ComboBox(["Axial (Z)", "Face (X)"], 1)
    h.key_radial_side = _ComboBox(["Außen (Welle)", "Innen (Bohrung)"], 0)
    h.key_coolant = _ComboBox(["Aus", "Ein"], 0)
    h.key_slot_count = _SpinBox(0.0)
    h.key_slot_start_angle = _SpinBox(0.0)
    h.key_slot_angle_step = _SpinBox(0.0)
    h.key_start_diameter = _SpinBox(0.0)
    h.key_start_z = _SpinBox(0.0)
    h.key_nut_length = _SpinBox(0.0)
    h.key_nut_depth = _SpinBox(0.0)
    h.key_slot_width = _SpinBox(0.0)
    h.key_cutting_width = _SpinBox(0.0)
    h.key_top_clearance = _SpinBox(0.0)
    h.key_depth_per_pass = _SpinBox(0.0)
    h.key_plunge_feed = _SpinBox(0.0)
    h.key_use_c_axis = _CheckBox(False)
    h.key_use_c_axis_switch = _CheckBox(False)
    h.key_c_axis_switch_p = _SpinBox(0.0)
    h.key_tool = _ComboBox(["T0", "T1", "T2", "T3"], 0)
    h._get_widget_by_name = lambda name: None

    h._setup_param_maps()

    params = h.param_widgets[OpType.KEYWAY]

    assert params["tool"] is h.key_tool
    assert params["mode"] is h.key_mode
    assert params["radial_side"] is h.key_radial_side
    assert params["coolant"] is h.key_coolant
    assert params["slot_count"] is h.key_slot_count
    assert params["slot_start_angle"] is h.key_slot_start_angle
    assert params["slot_angle_step"] is h.key_slot_angle_step
    assert params["start_x_dia"] is h.key_start_diameter
    assert params["start_z"] is h.key_start_z
    assert params["nut_length"] is h.key_nut_length
    assert params["nut_depth"] is h.key_nut_depth
    assert params["slot_width"] is h.key_slot_width
    assert params["cutting_width"] is h.key_cutting_width
    assert params["top_clearance"] is h.key_top_clearance
    assert params["depth_per_pass"] is h.key_depth_per_pass
    assert params["plunge_feed"] is h.key_plunge_feed
    assert params["use_c_axis"] is h.key_use_c_axis
    assert params["use_c_axis_switch"] is h.key_use_c_axis_switch
    assert params["c_axis_switch_p"] is h.key_c_axis_switch_p


def test_selection_change_flushes_previous_keyway_form_values():
    """Switching away from KEYWAY writes the current form values back into the model first."""
    h = _make_handler()

    keyway = Operation(
        OpType.KEYWAY,
        {"slot_count": 1.0, "slot_start_angle": 0.0, "slot_angle_step": 0.0},
        path=[],
    )
    face = Operation(OpType.FACE, {"tool": 1.0}, path=[])
    h.model.add_operation(keyway)
    h.model.add_operation(face)
    h.list_ops.addItem("1: Keilnut")
    h.list_ops.addItem("2: Planen")
    h._active_form_operation_index = 0
    h._collect_params = lambda op_type: {
        "slot_count": 5.0,
        "slot_start_angle": 0.0,
        "slot_angle_step": 35.0,
    } if op_type == OpType.KEYWAY else {}

    h._handle_selection_change(1)

    assert keyway.params["slot_count"] == 5.0
    assert keyway.params["slot_start_angle"] == 0.0
    assert keyway.params["slot_angle_step"] == 35.0


def test_connect_param_change_signals_connects_keyway_widgets():
    h = _make_handler()
    widget_map = {
        "key_slot_count": _SpinBox(3.0),
        "key_slot_start_angle": _SpinBox(10.0),
        "key_slot_angle_step": _SpinBox(35.0),
    }
    h._get_widget_by_name = lambda name: widget_map.get(name)

    h._connect_param_change_signals()

    assert h.param_widgets[OpType.KEYWAY]["slot_count"] is widget_map["key_slot_count"]
    assert h.param_widgets[OpType.KEYWAY]["slot_start_angle"] is widget_map["key_slot_start_angle"]
    assert h.param_widgets[OpType.KEYWAY]["slot_angle_step"] is widget_map["key_slot_angle_step"]
    assert h._handle_param_change in widget_map["key_slot_count"].valueChanged.calls
    assert h._handle_param_change in widget_map["key_slot_start_angle"].valueChanged.calls
    assert h._handle_param_change in widget_map["key_slot_angle_step"].valueChanged.calls


def test_tab_change_selects_matching_keyway_operation():
    h = _make_handler()
    tool_spin = _SpinBox(0.0)
    count_spin = _SpinBox(0.0)
    angle_spin = _SpinBox(0.0)
    widget_map = {
        "key_tool": tool_spin,
        "key_slot_count": count_spin,
        "key_slot_angle_step": angle_spin,
    }
    h._get_widget_by_name = lambda name: widget_map.get(name)
    h._setup_param_maps()

    h.model.add_operation(Operation(OpType.FACE, {"tool": 1.0}, path=[]))
    h.model.add_operation(Operation(OpType.KEYWAY, {"tool": 9.0, "slot_count": 6.0, "slot_angle_step": 35.0}, path=[]))
    h.list_ops.addItem("1: Planen")
    h.list_ops.addItem("2: Keilnut")
    h.list_ops.setCurrentRow(0)
    h.tab_params.setCurrentIndex(7)

    h._handle_tab_changed()

    assert h.list_ops.currentRow() == 1
    assert tool_spin.value() == 9.0
    assert count_spin.value() == 6.0
    assert angle_spin.value() == 35.0


def test_sync_form_to_operation_preserves_unmapped_keyway_values():
    """Transiently missing Keyway widgets must not wipe loaded geometry values."""
    h = _make_handler()

    keyway = Operation(
        OpType.KEYWAY,
        {
            "slot_count": 4.0,
            "slot_start_angle": 15.0,
            "slot_angle_step": 45.0,
            "start_x_dia": 30.0,
            "nut_length": 20.0,
        },
        path=[],
    )
    h.model.add_operation(keyway)
    h.list_ops.addItem("1: Keilnut")
    h.list_ops.setCurrentRow(0)

    h._collect_params = lambda op_type: {"slot_count": 6.0} if op_type == OpType.KEYWAY else {}
    h._describe_operation = lambda op, idx: f"{idx}: Keilnut"

    h._sync_form_to_operation(0)

    assert keyway.params["slot_count"] == 6.0
    assert keyway.params["slot_start_angle"] == 15.0
    assert keyway.params["slot_angle_step"] == 45.0
    assert keyway.params["start_x_dia"] == 30.0


def test_double_click_flushes_current_operation():
    """Double-clicking on a different step saves the current operation's changes first."""
    h = _make_handler()

    # Operation 0: FACE with tool=1
    op0 = Operation(OpType.FACE, {"tool": 1.0}, path=[])
    h.model.add_operation(op0)
    h.list_ops.addItem("1: Planen")

    # Operation 1: THREAD with pitch=2.0
    op1 = Operation(OpType.THREAD, {"pitch": 2.0}, path=[])
    h.model.add_operation(op1)
    h.list_ops.addItem("2: Gewinde")

    # Set up widgets for FACE
    tool_spin = _SpinBox(99.0)  # User changed tool to 99 in the UI
    h.param_widgets[OpType.FACE] = {"tool": tool_spin}

    # Currently viewing op0 (FACE)
    h.list_ops.setCurrentRow(0)
    h._op_row_user_selected = True

    # Track if _update_selected_operation was called
    flush_called = []
    orig_update = h._update_selected_operation

    def _mock_update(force=False):
        flush_called.append(force)
        # Actually flush the params
        idx = h.list_ops.currentRow()
        if 0 <= idx < len(h.model.operations):
            op = h.model.operations[idx]
            if op.op_type in h.param_widgets:
                for k, w in h.param_widgets[op.op_type].items():
                    op.params[k] = w.value()

    h._update_selected_operation = _mock_update

    # Double-click on op1 (THREAD)
    item = h.list_ops.item(1)
    h._on_step_double_clicked(item)

    # _update_selected_operation should have been called with force=True
    assert flush_called and flush_called[0] is True


def test_double_click_second_step_of_three():
    """With 3 operations, double-clicking #2 selects it and opens correct tab."""
    h = _make_handler()

    ops = [
        Operation(OpType.FACE, {"tool": 1}, []),
        Operation(OpType.GROOVE, {"width": 3.0}, []),
        Operation(OpType.DRILL, {"mode": 0.0}, []),
    ]
    for i, op in enumerate(ops):
        h.model.add_operation(op)
        h.list_ops.addItem(f"{i+1}: {op.op_type}")

    # Double-click on index 1 (GROOVE)
    item = h.list_ops.item(1)
    h._on_step_double_clicked(item)

    assert h.list_ops.currentRow() == 1
    assert h.tab_params.currentIndex() == 5  # GROOVE tab


def test_double_click_program_header():
    """Double-clicking the PROGRAM_HEADER step switches to tab 0."""
    h = _make_handler()
    # Supply header widgets so _load_program_header_to_form doesn't fail
    h.program_npv = _ComboBox(["G54"], 0)
    h.program_unit = _ComboBox(["mm"], 0)
    h.program_shape = _ComboBox(["Rund"], 0)
    h.program_retract_mode = _ComboBox(["Individuell"], 0)
    for attr in ["program_xa", "program_xi", "program_za", "program_zi",
                 "program_zb", "program_w", "program_l", "program_n",
                 "program_sw", "program_xra", "program_xri", "program_zra",
                 "program_zri", "program_xt", "program_zt", "program_sc",
                 "program_s1", "program_s3"]:
        setattr(h, attr, _SpinBox())
    h.program_name = _LineEdit()
    for attr in ["program_xra_absolute", "program_xri_absolute",
                 "program_zra_absolute", "program_zri_absolute",
                 "program_xt_absolute", "program_zt_absolute",
                 "program_has_subspindle"]:
        setattr(h, attr, _CheckBox())
    h._get_widget_by_name = lambda name: None

    op = Operation(OpType.PROGRAM_HEADER, {"program_name": "Welle", "xa": 50.0}, [])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Programmkopf")

    item = h.list_ops.item(0)
    h._on_step_double_clicked(item)

    assert h.tab_params.currentIndex() == 0  # PROGRAM_HEADER tab


def test_double_click_invalid_index_no_crash():
    """Double-clicking with an item not found in the list should not crash."""
    h = _make_handler()
    op = Operation(OpType.FACE, {}, [])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Planen")

    # Create an item that is NOT in the list
    fake_item = _ListItem("ghost")
    # Should not crash
    h._on_step_double_clicked(fake_item)
    # Tab should remain unchanged
    assert h.tab_params.currentIndex() == 0


# ---------------------------------------------------------------------------
# Delete Tests
# ---------------------------------------------------------------------------

def test_delete_removes_selected_step_not_last():
    """Deleting with step #2 selected removes that step, not the last."""
    h = _make_handler()

    # Add 4 operations: header + 3 steps
    ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Test"}, []),
        Operation(OpType.FACE, {"tool": 1}, []),
        Operation(OpType.THREAD, {"pitch": 1.5}, []),
        Operation(OpType.DRILL, {"mode": 0.0}, []),
    ]
    for i, op in enumerate(ops):
        h.model.add_operation(op)
        h.list_ops.addItem(f"{i+1}: {op.op_type}")

    # Select step #2 (THREAD, index 2)
    h.list_ops.setCurrentRow(2)

    # Delete
    h._handle_delete_operation()

    # THREAD (index 2) should be gone
    assert len(h.model.operations) == 3
    remaining_types = [op.op_type for op in h.model.operations]
    assert OpType.THREAD not in remaining_types
    assert remaining_types == [OpType.PROGRAM_HEADER, OpType.FACE, OpType.DRILL]


def test_delete_middle_step_preserves_others():
    """With 5 ops, deleting #3 keeps all other 4 in correct order."""
    h = _make_handler()

    ops = [
        Operation(OpType.PROGRAM_HEADER, {}, []),
        Operation(OpType.FACE, {"tool": 1}, []),
        Operation(OpType.CONTOUR, {"name": "C1"}, []),
        Operation(OpType.GROOVE, {"width": 3.0}, []),
        Operation(OpType.DRILL, {"mode": 0.0}, []),
    ]
    for i, op in enumerate(ops):
        h.model.add_operation(op)
        h.list_ops.addItem(f"{i+1}: {op.op_type}")

    # Select step #3 (GROOVE, index 3)
    h.list_ops.setCurrentRow(3)
    h._handle_delete_operation()

    assert len(h.model.operations) == 4
    types = [op.op_type for op in h.model.operations]
    assert types == [OpType.PROGRAM_HEADER, OpType.FACE, OpType.CONTOUR, OpType.DRILL]


def test_delete_header_is_blocked():
    """Deleting the program header (index 0) should be blocked."""
    h = _make_handler()
    op = Operation(OpType.PROGRAM_HEADER, {}, [])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Programmkopf")
    h.list_ops.setCurrentRow(0)

    h._handle_delete_operation()
    # Header should still be there
    assert len(h.model.operations) == 1
    assert h.model.operations[0].op_type == OpType.PROGRAM_HEADER


def test_delete_last_step_selects_previous():
    """After deleting the last step, selection moves to the new last step."""
    h = _make_handler()

    ops = [
        Operation(OpType.PROGRAM_HEADER, {}, []),
        Operation(OpType.FACE, {"tool": 1}, []),
        Operation(OpType.THREAD, {"pitch": 1.5}, []),
    ]
    for i, op in enumerate(ops):
        h.model.add_operation(op)
        h.list_ops.addItem(f"{i+1}: {op.op_type}")

    # Select last step (THREAD, index 2)
    h.list_ops.setCurrentRow(2)
    h._handle_delete_operation()

    assert len(h.model.operations) == 2
    # Selection should be on the new last step (FACE, index 1)
    assert h.list_ops.currentRow() == 1


def test_delete_no_selection_does_nothing():
    """Delete with no selection (currentRow=-1) does nothing."""
    h = _make_handler()
    op = Operation(OpType.PROGRAM_HEADER, {}, [])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Programmkopf")
    # No selection
    h.list_ops.setCurrentRow(-1)

    h._handle_delete_operation()
    assert len(h.model.operations) == 1


# ---------------------------------------------------------------------------
# _ui_loading leak fix
# ---------------------------------------------------------------------------

def test_selection_change_resets_ui_loading_on_invalid_row():
    """_handle_selection_change must reset _ui_loading even for invalid rows."""
    h = _make_handler()
    h._ui_loading = False

    # Call with invalid row
    h._handle_selection_change(-1)

    # _ui_loading must be False again (was True during execution)
    assert h._ui_loading is False


def test_selection_change_resets_ui_loading_on_valid_row():
    """_handle_selection_change resets _ui_loading after loading a valid step."""
    h = _make_handler()
    op = Operation(OpType.FACE, {"tool": 1}, [])
    h.model.add_operation(op)
    h.list_ops.addItem("1: Planen")
    h.list_ops.setCurrentRow(0)
    h._ui_loading = False

    h._handle_selection_change(0)

    assert h._ui_loading is False
