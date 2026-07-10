from __future__ import annotations

from qtpy import QtWidgets


def prepare_signal_connection_context(handler) -> None:
    handler._ensure_core_widgets()
    if handler.tab_params is None:
        handler.tab_params = handler._get_widget_by_name("tabParams")
    handler._ensure_list_ops_type()
    if not hasattr(handler, "_resolver"):
        handler._setup_resolver()


def connect_resolver_fallbacks(handler) -> None:
    if handler.list_ops is not None:
        return

    def on_list_ops_ready(widget, err):
        if err is not None:
            try:
                handler.LOG.error(f"listOperations resolve failed: {err}")
            except Exception:
                handler._log(err, level="info")
            return
        if not isinstance(widget, QtWidgets.QListWidget):
            return
        handler.list_ops = widget
        connect_list_ops_signals(handler)

    handler._resolver.resolve_later(
        QtWidgets.QListWidget,
        "listOperations",
        on_list_ops_ready,
        timeout_ms=5000,
        interval_ms=150,
        debug_context=True,
    )


def connect_tool_preview_signals(handler) -> None:
    for combo_name in ["face_tool", "drill_tool", "groove_tool", "thread_tool", "parting_tool", "key_tool"]:
        combo = getattr(handler, combo_name, None)
        if combo and not getattr(handler, f"_{combo_name}_connected", False):
            combo.currentIndexChanged.connect(handler._update_tool_previews)
            setattr(handler, f"_{combo_name}_connected", True)


def connect_param_change_signals(handler) -> None:
    handler._setup_param_maps()
    for widgets in handler.param_widgets.values():
        for widget in widgets.values():
            if widget is None:
                continue
            if widget in handler._connected_param_widgets:
                continue
            if hasattr(widget, "set_paths") or hasattr(widget, "set_primitives"):
                continue
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(handler._handle_param_change)
            elif isinstance(widget, QtWidgets.QAbstractButton):
                widget.toggled.connect(handler._handle_param_change)
            elif hasattr(widget, "valueChanged"):
                widget.valueChanged.connect(handler._handle_param_change)
            handler._connected_param_widgets.add(widget)


def connect_global_form_signals(handler) -> None:
    for widget in (
        getattr(handler, "program_npv", None),
        getattr(handler, "program_shape", None),
        getattr(handler, "program_retract_mode", None),
        getattr(handler, "program_machine_profile", None),
        getattr(handler, "program_chuck_size", None),
        getattr(handler, "program_chuck_part_type", None),
        getattr(handler, "program_chuck_grip_mode", None),
        getattr(handler, "program_chuck_profile", None),
        getattr(handler, "program_spindle_mode", None),
        getattr(handler, "program_toolchange_coords", None),
        getattr(handler, "program_park_mode", None),
        getattr(handler, "program_park_coords", None),
    ):
        if widget and widget not in handler._connected_global_widgets:
            widget.currentIndexChanged.connect(handler._handle_global_change)
            handler._connected_global_widgets.add(widget)
    for widget in (
        getattr(handler, "program_xa", None),
        getattr(handler, "program_xi", None),
        getattr(handler, "program_za", None),
        getattr(handler, "program_zi", None),
        getattr(handler, "program_zb", None),
        getattr(handler, "program_xra", None),
        getattr(handler, "program_xri", None),
        getattr(handler, "program_zra", None),
        getattr(handler, "program_zri", None),
        getattr(handler, "program_w", None),
        getattr(handler, "program_l", None),
        getattr(handler, "program_n", None),
        getattr(handler, "program_sw", None),
        getattr(handler, "program_xt", None),
        getattr(handler, "program_zt", None),
        getattr(handler, "program_sc", None),
        getattr(handler, "program_chuck_x_min", None),
        getattr(handler, "program_chuck_x_max", None),
        getattr(handler, "program_chuck_z_limit", None),
        getattr(handler, "program_spindle_max_rpm", None),
        getattr(handler, "program_park_x", None),
        getattr(handler, "program_park_z", None),
        getattr(handler, "program_s1", None),
        getattr(handler, "program_s3", None),
    ):
        if widget and widget not in handler._connected_global_widgets and hasattr(widget, "valueChanged"):
            widget.valueChanged.connect(handler._handle_global_change)
            handler._connected_global_widgets.add(widget)
    for widget in (
        getattr(handler, "program_xra_absolute", None),
        getattr(handler, "program_xri_absolute", None),
        getattr(handler, "program_zra_absolute", None),
        getattr(handler, "program_zri_absolute", None),
        getattr(handler, "program_xt_absolute", None),
        getattr(handler, "program_zt_absolute", None),
        getattr(handler, "program_has_subspindle", None),
        getattr(handler, "program_park_sequential", None),
        getattr(handler, "program_optional_stop_toolchange", None),
        getattr(handler, "program_preview_warnings", None),
    ):
        if widget and widget not in handler._connected_global_widgets and hasattr(widget, "toggled"):
            widget.toggled.connect(handler._handle_global_change)
            handler._connected_global_widgets.add(widget)
    line_edit = getattr(handler, "program_name", None)
    if line_edit and line_edit not in handler._connected_global_widgets and hasattr(line_edit, "textChanged"):
        line_edit.textChanged.connect(handler._handle_global_change)
        handler._connected_global_widgets.add(line_edit)
    if handler.program_unit and handler.program_unit not in handler._connected_global_widgets:
        handler.program_unit.currentIndexChanged.connect(handler._handle_global_change)
        handler._connected_global_widgets.add(handler.program_unit)
    if (
        handler.program_has_subspindle
        and hasattr(handler.program_has_subspindle, "toggled")
        and not getattr(handler, "_program_has_subspindle_visibility_connected", False)
    ):
        handler.program_has_subspindle.toggled.connect(handler._update_subspindle_visibility)
        handler._program_has_subspindle_visibility_connected = True


def connect_language_signal(handler) -> None:
    if not hasattr(handler, "_language_connected_widgets"):
        handler._language_connected_widgets = set()
    widgets = []
    try:
        widgets = list(handler._widgets_by_name("program_language"))
    except Exception:
        combo = handler._get_widget_by_name("program_language")
        if combo is not None:
            widgets = [combo]
    for lang_combo in widgets:
        if lang_combo is None:
            continue
        key = id(lang_combo)
        if key in handler._language_connected_widgets:
            continue
        try:
            lang_combo.currentIndexChanged.connect(handler._handle_language_change)
            handler._language_connected_widgets.add(key)
        except Exception:
            continue
    handler._language_connected = bool(handler._language_connected_widgets)


def connect_mode_visibility_signals(handler) -> None:
    try:
        if getattr(handler, "face_mode", None):
            handler.face_mode.currentIndexChanged.connect(lambda *_: handler._update_face_visibility())
        if getattr(handler, "face_edge_type", None):
            handler.face_edge_type.currentIndexChanged.connect(lambda *_: handler._update_face_visibility())
    except Exception:
        pass
    try:
        if getattr(handler, "drill_mode", None):
            handler.drill_mode.currentIndexChanged.connect(lambda *_: handler._update_drill_visibility())
    except Exception:
        pass


def connect_list_ops_signals(handler) -> None:
    widget = getattr(handler, "list_ops", None)
    if widget is None:
        return

    if getattr(handler, "_list_ops_signal_widget", None) is not widget:
        handler._list_ops_connected = False
        handler._list_ops_double_click_connected = False
        handler._list_ops_click_connected = False
        handler._list_ops_activate_connected = False
        handler._list_ops_signal_widget = widget

    if not getattr(handler, "_list_ops_connected", False):
        try:
            widget.currentRowChanged.connect(handler._handle_selection_change)
        except Exception:
            pass
        handler._list_ops_connected = True
    if not getattr(handler, "_list_ops_double_click_connected", False):
        try:
            widget.itemDoubleClicked.connect(handler._on_step_double_clicked)
        except Exception:
            pass
        handler._list_ops_double_click_connected = True
    if not getattr(handler, "_list_ops_click_connected", False):
        try:
            widget.clicked.connect(handler._mark_operation_user_selected)
        except Exception:
            pass
        handler._list_ops_click_connected = True
    if not getattr(handler, "_list_ops_activate_connected", False):
        try:
            widget.itemActivated.connect(handler._on_step_double_clicked)
        except Exception:
            pass
        handler._list_ops_activate_connected = True


def connect_core_signals(handler) -> None:
    handler._ensure_core_widgets()
    if handler.tab_params is None:
        handler.tab_params = handler._get_widget_by_name("tabParams")
    handler._ensure_list_ops_type()

    handler._connect_button_once(handler.btn_add, handler._handle_add_operation, "_btn_add_connected")
    handler._connect_button_once(handler.btn_delete, handler._handle_delete_operation, "_btn_delete_connected")
    handler._connect_button_once(handler.btn_move_up, handler._handle_move_up, "_btn_move_up_connected")
    handler._connect_button_once(handler.btn_move_down, handler._handle_move_down, "_btn_move_down_connected")
    handler._connect_button_once(handler.btn_new_program, handler._handle_new_program, "_btn_new_program_connected")
    handler._connect_button_once(handler.btn_generate, handler._handle_generate_gcode, "_btn_generate_connected")
    handler._connect_button_once(handler.btn_save_changes, handler._handle_save_changes, "_btn_save_changes_connected")
    handler._connect_button_once(handler.btn_load_tool_table, handler._handle_load_tool_table, "_btn_load_tool_table_connected")
    handler._connect_button_once(handler.btn_save_program, handler._handle_save_program, "_btn_save_program_connected")
    handler._connect_button_once(handler.btn_load_program, handler._handle_load_program, "_btn_load_program_connected")
    connect_list_ops_signals(handler)
    if handler.tab_params and not getattr(handler, "_tab_params_connected", False):
        handler.tab_params.currentChanged.connect(handler._handle_tab_changed)
        handler._tab_params_connected = True
    if (
        handler.parting_mode
        and hasattr(handler.parting_mode, "currentIndexChanged")
        and not getattr(handler, "_parting_mode_connected", False)
    ):
        handler.parting_mode.currentIndexChanged.connect(handler._update_parting_mode_visibility)
        handler._parting_mode_connected = True
    if (
        getattr(handler, "parting_undercut_mode", None)
        and hasattr(handler.parting_undercut_mode, "currentIndexChanged")
        and not getattr(handler, "_parting_undercut_mode_connected", False)
    ):
        handler.parting_undercut_mode.currentIndexChanged.connect(handler._update_parting_mode_visibility)
        handler._parting_undercut_mode_connected = True
    if (
        getattr(handler, "groove_process_type", None)
        and hasattr(handler.groove_process_type, "currentIndexChanged")
        and not getattr(handler, "_groove_process_type_connected", False)
    ):
        handler.groove_process_type.currentIndexChanged.connect(handler._update_groove_tab_ui)
        handler._groove_process_type_connected = True
