import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.ui_dirty import (
    clear_program_dirty,
    dirty_status_text,
    init_dirty_state,
    mark_dirty,
    mark_program_structure_dirty,
    warn_if_dirty,
)
from lathe_easystep.ui_flow import handle_move_down, handle_move_up, jump_to_error_location
from lathe_easystep.ui_messages import format_user_error, parse_error_location
from lathe_easystep.ui_groove import update_groove_tab_ui
import lathe_easystep.ui_dirty as ui_dirty


class _Label:
    def __init__(self):
        self.text = ""
        self.style = ""

    def setText(self, value):
        self.text = value

    def setStyleSheet(self, value):
        self.style = value


class _Button:
    def __init__(self):
        self.text = ""

    def setText(self, value):
        self.text = value


class _Visible:
    def __init__(self):
        self.visible = None

    def setVisible(self, value):
        self.visible = bool(value)


class _Check:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _List:
    def __init__(self, row=0):
        self._row = row

    def currentRow(self):
        return self._row


def _handler():
    handler = types.SimpleNamespace()
    handler.model = ProgramModel()
    handler.model.operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Demo"}),
        Operation(OpType.GROOVE, {"tool": 1}),
    ]
    handler.label_dirty_status = _Label()
    handler.btn_save_changes = _Button()
    handler.list_ops = _List(1)
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._current_language_code = lambda: "de"
    handler._update_dirty_status = lambda: None
    return handler


def test_dirty_status_text_tracks_program_and_steps():
    handler = _handler()
    init_dirty_state(handler)
    assert dirty_status_text(handler) == "Keine offenen Aenderungen"
    mark_dirty(handler, program=True)
    mark_dirty(handler, operation_index=1)
    assert "Programm" in dirty_status_text(handler)
    assert "1 Step" in dirty_status_text(handler)


def test_warn_if_dirty_uses_localized_unsaved_message(monkeypatch):
    handler = _handler()
    init_dirty_state(handler)
    mark_dirty(handler, operation_index=1)
    calls = []

    def _warn(_parent, title, text):
        calls.append((title, text))

    monkeypatch.setattr(ui_dirty.QtWidgets.QMessageBox, "warning", staticmethod(_warn))
    warn_if_dirty(handler, "Tabwechsel", row=1)
    assert calls
    assert "Ungespeicherte Aenderungen" in calls[0][0]
    assert "Einstich / Abstich" in calls[0][1]


def test_program_structure_dirty_marks_program_without_flagging_all_steps():
    handler = _handler()
    init_dirty_state(handler)
    mark_program_structure_dirty(handler, operation_indices={1})
    assert handler._program_dirty is True
    assert handler._dirty_operation_indices == {1}
    assert "Programm" in dirty_status_text(handler)
    assert "1 Step" in dirty_status_text(handler)


def test_clear_program_dirty_can_remove_structure_flag_only():
    handler = _handler()
    init_dirty_state(handler)
    mark_program_structure_dirty(handler, operation_indices={1})
    clear_program_dirty(handler, structure=True)
    assert handler._program_dirty is False
    assert handler._dirty_program_structure is False


def test_move_up_marks_program_structure_but_not_all_steps():
    class _Ops:
        def __init__(self):
            self._row = 1

        def currentRow(self):
            return self._row

    class _Model:
        def __init__(self):
            self.moved = None

        def move_up(self, idx):
            self.moved = idx

    handler = _handler()
    handler.list_ops = _Ops()
    handler.model = _Model()
    handler.structure_calls = 0
    handler.refresh_calls = []
    handler._moving_up = False
    handler._mark_program_structure_dirty = lambda operation_indices=None: setattr(handler, "structure_calls", handler.structure_calls + 1)
    handler._mark_all_operations_dirty = lambda: (_ for _ in ()).throw(AssertionError("must not mark all operations dirty"))
    handler._refresh_operation_list = lambda select_index=None: handler.refresh_calls.append(select_index)
    handler._renumber_operations = lambda: None
    handler._refresh_preview = lambda: None
    handle_move_up(handler)
    assert handler.model.moved == 1
    assert handler.structure_calls == 1
    assert handler.refresh_calls == [0]


def test_move_down_marks_program_structure_but_not_all_steps():
    class _Ops:
        def __init__(self):
            self._row = 0

        def currentRow(self):
            return self._row

        def count(self):
            return 2

    class _Model:
        def __init__(self):
            self.moved = None

        def move_down(self, idx):
            self.moved = idx

    handler = _handler()
    handler.list_ops = _Ops()
    handler.model = _Model()
    handler.structure_calls = 0
    handler.refresh_calls = []
    handler._moving_down = False
    handler._mark_program_structure_dirty = lambda operation_indices=None: setattr(handler, "structure_calls", handler.structure_calls + 1)
    handler._mark_all_operations_dirty = lambda: (_ for _ in ()).throw(AssertionError("must not mark all operations dirty"))
    handler._refresh_operation_list = lambda select_index=None: handler.refresh_calls.append(select_index)
    handler._renumber_operations = lambda: None
    handler._refresh_preview = lambda: None
    handle_move_down(handler)
    assert handler.model.moved == 0
    assert handler.structure_calls == 1
    assert handler.refresh_calls == [1]


def test_user_error_formatter_maps_required_field_to_tab_and_label():
    handler = _handler()
    text = format_user_error(
        handler,
        ValueError("Operation 2 (THREAD): Fehler in Operation THREAD: Pflicht-Parameter fehlt: 'safe_z'."),
        fallback_title="Fehler",
    )
    assert "Gewinde" in text
    assert "Sicherheitsabstand / Rueckzugsebene Z" in text


class _JumpWidget:
    def __init__(self):
        self.focused = False
        self.style = ""

    def setFocus(self):
        self.focused = True

    def styleSheet(self):
        return self.style

    def setStyleSheet(self, value):
        self.style = value


class _JumpList:
    def __init__(self, count):
        self._count = count
        self.current_row = None

    def count(self):
        return self._count

    def setCurrentRow(self, row):
        self.current_row = row


def test_parse_error_location_extracts_step_type_and_field():
    location = parse_error_location(
        ValueError("Operation 3 (face): Missing parameter: 'mode'")
    )
    assert location["op_number"] == 3
    assert location["op_type"] == "face"
    assert location["field_key"] == "mode"


def test_parse_error_location_handles_unwrapped_errors():
    location = parse_error_location(ValueError("something went wrong"))
    assert location["op_number"] is None
    assert location["op_type"] is None
    assert location["field_key"] is None


def test_jump_to_error_location_selects_step_and_focuses_field():
    """TODO-Feedback: bei Generierungsfehlern soll automatisch zum
    betroffenen Step/Reiter gesprungen und das Feld hervorgehoben werden."""
    handler = types.SimpleNamespace()
    handler.list_ops = _JumpList(3)
    selected_rows = []
    handler._handle_selection_change = lambda row: selected_rows.append(row)
    mode_widget = _JumpWidget()
    handler.param_widgets = {"face": {"mode": mode_widget}}

    jump_to_error_location(handler, ValueError("Operation 2 (face): Missing parameter: 'mode'"))

    assert handler.list_ops.current_row == 1
    assert selected_rows == [1]
    assert mode_widget.focused is True
    assert "border" in mode_widget.style


def test_jump_to_error_location_does_nothing_without_op_number():
    handler = types.SimpleNamespace()
    handler.list_ops = _JumpList(3)
    handler._handle_selection_change = lambda row: (_ for _ in ()).throw(AssertionError("should not be called"))
    jump_to_error_location(handler, ValueError("plain error without location"))
    assert handler.list_ops.current_row is None


def test_groove_parting_mode_shows_parting_specific_widgets():
    widgets = {
        "label_23": _Label(),
        "label_groove_reduced_feed_start_x": _Visible(),
        "groove_reduced_feed_start_x": _Visible(),
        "label_groove_reduced_feed": _Visible(),
        "groove_reduced_feed": _Visible(),
        "label_groove_reduced_rpm": _Visible(),
        "groove_reduced_rpm": _Visible(),
    }
    handler = types.SimpleNamespace(
        groove_process_type=types.SimpleNamespace(currentData=lambda: "parting"),
        groove_use_tool_width=_Check(),
        groove_cutting_width=_Visible(),
        groove_lage=types.SimpleNamespace(currentIndex=lambda: 0),
        _get_widget_by_name=lambda name: widgets.get(name),
        _render_groove_diagrams=lambda: None,
        _refresh_preview=lambda: None,
    )
    update_groove_tab_ui(handler)
    assert widgets["groove_reduced_feed"].visible is True
    assert "Abstichposition" in widgets["label_23"].text


def test_groove_process_type_groove_hides_parting_specific_widgets():
    """Kehrseite von test_groove_parting_mode_shows_parting_specific_widgets:
    fuer den regulaeren Einstich (process_type="groove", nicht "parting")
    muessen die reduzierten Vorschub-/Drehzahlfelder ausgeblendet bleiben."""
    widgets = {
        "label_23": _Label(),
        "label_groove_reduced_feed_start_x": _Visible(),
        "groove_reduced_feed_start_x": _Visible(),
        "label_groove_reduced_feed": _Visible(),
        "groove_reduced_feed": _Visible(),
        "label_groove_reduced_rpm": _Visible(),
        "groove_reduced_rpm": _Visible(),
    }
    handler = types.SimpleNamespace(
        groove_process_type=types.SimpleNamespace(currentData=lambda: "groove"),
        groove_use_tool_width=_Check(),
        groove_cutting_width=_Visible(),
        groove_lage=types.SimpleNamespace(currentIndex=lambda: 0),
        _get_widget_by_name=lambda name: widgets.get(name),
        _render_groove_diagrams=lambda: None,
        _refresh_preview=lambda: None,
    )
    update_groove_tab_ui(handler)
    assert widgets["groove_reduced_feed_start_x"].visible is False
    assert widgets["groove_reduced_feed"].visible is False
    assert widgets["groove_reduced_rpm"].visible is False


def test_groove_use_tool_width_toggles_cutting_width_visibility():
    widgets = {"label_23": _Label(), "label_groove_cutting_width": _Visible()}
    handler = types.SimpleNamespace(
        groove_process_type=types.SimpleNamespace(currentData=lambda: "groove"),
        groove_use_tool_width=_Check(checked=True),
        groove_cutting_width=_Visible(),
        groove_lage=types.SimpleNamespace(currentIndex=lambda: 0),
        _get_widget_by_name=lambda name: widgets.get(name),
        _render_groove_diagrams=lambda: None,
        _refresh_preview=lambda: None,
    )
    update_groove_tab_ui(handler)
    assert handler.groove_cutting_width.visible is True
    assert widgets["label_groove_cutting_width"].visible is True

    handler.groove_use_tool_width = _Check(checked=False)
    handler.groove_cutting_width = _Visible()
    update_groove_tab_ui(handler)
    assert handler.groove_cutting_width.visible is False
    assert widgets["label_groove_cutting_width"].visible is False
