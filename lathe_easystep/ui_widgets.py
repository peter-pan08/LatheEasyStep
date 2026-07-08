from __future__ import annotations

from qtpy import QtCore, QtWidgets


def ensure_core_widgets(handler) -> None:
    root = (
        handler.root_widget
        or handler._panel_from_widget(handler.list_ops)
        or handler._panel_from_widget(handler.contour_segments)
        or (handler.program_unit.window() if handler.program_unit else None)
        or (handler.preview.window() if handler.preview else None)
        or handler._find_root_widget()
    )
    if root is None:
        return
    handler.root_widget = handler.root_widget or root

    def find(name: str, cls):
        current = getattr(handler, name, None)
        if current:
            return current
        obj_name = (
            "listOperations" if name == "list_ops" else
            "tabParams" if name == "tab_params" else
            "btnAdd" if name == "btn_add" else
            "btnDelete" if name == "btn_delete" else
            "btnMoveUp" if name == "btn_move_up" else
            "btnMoveDown" if name == "btn_move_down" else
            "btnNewProgram" if name == "btn_new_program" else
            "btnSaveChanges" if name == "btn_save_changes" else
            "btnGenerate" if name == "btn_generate" else
            name
        )
        obj = root.findChild(cls, obj_name, QtCore.Qt.FindChildrenRecursively)
        if obj is None:
            obj = root.findChild(QtCore.QObject, obj_name, QtCore.Qt.FindChildrenRecursively)
        if obj is None:
            obj = root.findChild(QtWidgets.QWidget, obj_name, QtCore.Qt.FindChildrenRecursively)
        if obj:
            setattr(handler, name, obj)
        return getattr(handler, name, None)

    handler.list_ops = find("list_ops", QtWidgets.QListWidget)
    handler.tab_params = find("tab_params", QtWidgets.QTabWidget)
    handler.btn_add = find("btn_add", QtWidgets.QPushButton)
    handler.btn_delete = find("btn_delete", QtWidgets.QPushButton)
    handler.btn_move_up = find("btn_move_up", QtWidgets.QPushButton)
    handler.btn_move_down = find("btn_move_down", QtWidgets.QPushButton)
    handler.btn_new_program = find("btn_new_program", QtWidgets.QPushButton)
    handler.btn_generate = find("btn_generate", QtWidgets.QPushButton)
    handler.btn_save_changes = find("btn_save_changes", QtWidgets.QPushButton)
    handler.btn_save_step = find("btn_save_step", QtWidgets.QPushButton)
    handler.btn_load_step = find("btn_load_step", QtWidgets.QPushButton)
    handler.btn_save_program = find("btn_save_program", QtWidgets.QPushButton)
    handler.btn_load_program = find("btn_load_program", QtWidgets.QPushButton)
    handler.btn_load_tool_table = find("btn_load_tool_table", QtWidgets.QPushButton)
    handler.tool_table_path = find("tool_table_path", QtWidgets.QLineEdit)
    handler.lbl_tool_table_path = find("lbl_tool_table_path", QtWidgets.QLabel)

    handler.face_tool = find("face_tool", QtWidgets.QComboBox)
    handler.drill_tool = find("drill_tool", QtWidgets.QComboBox)
    handler.groove_tool = find("groove_tool", QtWidgets.QComboBox)
    handler.thread_tool = find("thread_tool", QtWidgets.QComboBox)
    handler.parting_tool = find("parting_tool", QtWidgets.QComboBox)
    handler.key_tool = find("key_tool", QtWidgets.QComboBox)
    handler.face_tool_img = find("face_tool_img", QtWidgets.QLabel)
    handler.drill_tool_img = find("drill_tool_img", QtWidgets.QLabel)
    handler.groove_tool_img = find("groove_tool_img", QtWidgets.QLabel)
    handler.thread_tool_img = find("thread_tool_img", QtWidgets.QLabel)
    handler.parting_tool_img = find("parting_tool_img", QtWidgets.QLabel)

    if handler.list_ops is None:
        explicit = root.findChild(QtWidgets.QListWidget, "list_ops", QtCore.Qt.FindChildrenRecursively)
        if explicit:
            handler.list_ops = explicit
    handler._ensure_list_ops_type()
    if handler.tab_params is None:
        candidates = root.findChildren(QtWidgets.QTabWidget)
        if candidates:
            handler.tab_params = candidates[0]
    handler._resolve_core_widgets_strict()

    handler._connect_button_once(handler.btn_add, handler._handle_add_operation, "_btn_add_connected")
    handler._connect_button_once(handler.btn_delete, handler._handle_delete_operation, "_btn_delete_connected")
    handler._connect_button_once(handler.btn_move_up, handler._handle_move_up, "_btn_move_up_connected")
    handler._connect_button_once(handler.btn_move_down, handler._handle_move_down, "_btn_move_down_connected")
    handler._connect_button_once(handler.btn_new_program, handler._handle_new_program, "_btn_new_program_connected")
    handler._connect_button_once(handler.btn_generate, handler._handle_generate_gcode, "_btn_generate_connected")
    handler._connect_button_once(handler.btn_save_changes, handler._handle_save_changes, "_btn_save_changes_connected")
    handler._connect_button_once(handler.btn_save_step, handler._handle_save_step, "_btn_save_step_connected")
    handler._connect_button_once(handler.btn_load_step, handler._handle_load_step, "_btn_load_step_connected")
    handler._connect_button_once(handler.btn_thread_preset, handler._apply_thread_preset_force, "_thread_preset_connected")
