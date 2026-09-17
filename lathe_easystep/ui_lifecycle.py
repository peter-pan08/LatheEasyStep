from __future__ import annotations

from qtpy import QtCore, QtWidgets


def bootstrap_widget_refs(handler) -> None:
    """Initialize widget reference attributes early so startup code can safely probe them."""
    panel_root = getattr(handler.w, "easystep", None) or handler.w

    def find(name, cls=None):
        widget = getattr(handler.w, name, None)
        if widget is not None:
            return widget
        try:
            if cls is None:
                return panel_root.findChild(QtCore.QObject, name)
            return panel_root.findChild(cls, name)
        except Exception:
            return None

    handler.preview_slice = find("previewSliceWidget", QtWidgets.QWidget)
    handler.btn_slice_view = find("btn_slice_view", QtWidgets.QAbstractButton)
    if handler.btn_slice_view is None:
        try:
            for button in panel_root.findChildren(QtWidgets.QAbstractButton):
                text = (button.text() or "").lower()
                if getattr(button, "isCheckable", lambda: False)() and ("schnitt" in text or "seiten" in text):
                    handler.btn_slice_view = button
                    break
        except Exception:
            pass
    handler.contour_preview = getattr(handler.w, "contourPreview", None)
    handler.list_ops = getattr(handler.w, "listOperations", None)
    handler.tab_params = getattr(handler.w, "tabParams", None)
    if handler.tab_params is not None:
        try:
            handler.tab_params.setCurrentIndex(1)
        except Exception:
            pass

    def resolve_widget(name: str):
        widget = getattr(handler.w, name, None)
        if widget is not None:
            return widget
        widget = handler._find_any_widget(name)
        if widget is not None:
            handler._log(f"[LatheEasyStep] resolved '{name}' via global search", level="info")
        return widget

    def resolve_or_defer_local(attr_name: str, name: str, cls=None, debug_context: bool = False):
        try:
            ui_ready = getattr(handler.w, "ui_ready", False)
        except Exception:
            ui_ready = False
        if not ui_ready:
            handler._deferred_lookup_queue.append((attr_name, name, cls, debug_context))
            return None
        widget = getattr(handler.w, name, None)
        if widget is not None:
            setattr(handler, attr_name, widget)
            return widget
        try:
            widget = handler._find_any_widget(name)
        except Exception:
            widget = None
        if widget is not None and debug_context:
            handler._log(f"[LatheEasyStep] resolved '{name}' via global search", level="info")
        setattr(handler, attr_name, widget)
        return widget

    handler.btn_add = resolve_or_defer_local("btn_add", "btnAdd")
    handler.btn_delete = resolve_or_defer_local("btn_delete", "btnDelete")
    handler.btn_move_up = resolve_or_defer_local("btn_move_up", "btnMoveUp")
    handler.btn_move_down = resolve_or_defer_local("btn_move_down", "btnMoveDown")
    handler.btn_new_program = resolve_or_defer_local("btn_new_program", "btnNewProgram")
    handler.btn_generate = resolve_or_defer_local("btn_generate", "btnGenerate")
    handler.btn_save_changes = resolve_or_defer_local("btn_save_changes", "btnSaveChanges")

    handler.tab_program = resolve_widget("tabProgram")
    handler.program_unit = resolve_widget("program_unit")
    handler.program_shape = resolve_widget("program_shape")
    handler.program_retract_mode = resolve_widget("program_retract_mode")
    handler.program_has_subspindle = resolve_widget("program_has_subspindle")

    for attr_name in (
        "program_xa", "program_xi", "label_prog_xi", "program_za", "program_zi", "program_zb",
        "program_w", "label_prog_w", "program_l", "label_prog_l", "program_n", "label_prog_n",
        "program_sw", "label_prog_sw", "program_xt", "program_zt", "program_sc",
        "program_machine_profile", "program_chuck_size", "program_chuck_part_type",
        "program_chuck_grip_mode", "program_chuck_profile", "program_chuck_x_min",
        "program_chuck_x_max", "program_chuck_z_limit", "program_name", "program_xra",
        "label_prog_xra", "program_xri", "label_prog_xri", "program_zra", "label_prog_zra",
        "program_zri", "label_prog_zri", "program_xra_absolute", "program_xri_absolute",
        "program_zra_absolute", "program_zri_absolute", "program_xt_absolute",
        "program_zt_absolute", "program_s1", "label_prog_s1", "program_s3", "label_prog_s3",
        "program_spindle", "program_tool", "program_npv", "face_mode", "face_edge_type",
        "label_face_edge_size", "face_edge_size", "label_face_finish_allow_x",
        "face_finish_allow_x", "label_face_finish_allow_z", "face_finish_allow_z",
        "label_face_depth_max", "face_depth_max", "label_face_pause", "face_pause_enabled",
        "label_face_pause_distance", "face_pause_distance", "contour_start_x",
        "contour_start_z", "contour_name", "contour_segments", "contour_add_segment",
        "contour_delete_segment", "contour_move_up", "contour_move_down", "contour_edge_type",
        "label_contour_edge_size", "contour_edge_size", "parting_contour", "parting_side",
        "parting_tool", "parting_spindle", "parting_feed", "parting_depth_per_pass",
        "parting_mode", "parting_pause_enabled", "parting_pause_distance",
        "label_parting_slice_strategy", "parting_slice_strategy", "label_parting_slice_step",
        "parting_slice_step", "label_parting_allow_undercut", "parting_allow_undercut",
        "label_parting_depth", "label_parting_pause", "label_parting_pause_distance",
        "thread_standard", "thread_orientation", "thread_tool", "thread_spindle",
        "thread_major_diameter", "thread_pitch", "thread_length", "thread_passes",
        "thread_safe_z", "thread_depth", "thread_peak_offset", "thread_first_depth",
        "thread_retract_r", "thread_infeed_q", "thread_spring_passes", "thread_e",
        "thread_l", "btn_thread_preset", "tool_table_path", "lbl_tool_table_path",
        "key_mode", "key_radial_side", "key_tool", "key_coolant", "key_slot_count",
        "key_slot_start_angle", "key_slot_angle_step", "key_start_diameter", "key_start_z",
        "key_nut_length", "key_nut_depth", "key_cutting_width", "key_top_clearance",
        "key_depth_per_pass", "key_plunge_feed", "key_use_c_axis", "key_use_c_axis_switch",
        "key_c_axis_switch_p",
    ):
        setattr(handler, attr_name, getattr(handler.w, attr_name, None))

    handler._contour_edge_template_text = "Keine"
    handler._contour_edge_template_size = 0.0
    handler._contour_arc_template_text = "Auto"
    handler._contour_row_user_selected = False
    handler._op_row_user_selected = False
    handler._setup_parting_slice_strategy_items()
    if handler.label_parting_slice_step is not None:
        try:
            handler.label_parting_slice_step.setVisible(False)
        except Exception:
            pass
    if handler.parting_slice_step is not None:
        try:
            handler.parting_slice_step.setVisible(False)
        except Exception:
            pass

    handler.root_widget = handler._find_root_widget()
    handler._setup_resolver()
    handler._unit_last_index = -1


def finalize_ui_ready(handler) -> None:
    """Run the late UI binding pass after the panel widget tree exists."""
    handler._startup_mark("_finalize_ui_ready enter")
    if not getattr(handler, "w", None):
        handler._log("[LatheEasyStep] _finalize_ui_ready: widgets not ready (no program_unit) - deferring", level="info")
        return

    if getattr(handler, "_ui_finalized", False):
        return
    handler._finalize_pass = getattr(handler, "_finalize_pass", 0) + 1
    handler._log(f"[LatheEasyStep] _finalize_ui_ready pass {handler._finalize_pass}", level="info")

    try:
        handler._register_known_widgets()
        handler._rebuild_widget_name_cache()
    except Exception:
        pass

    handler._ensure_core_widgets()
    if handler.tab_params is not None and handler.tab_params.currentIndex() == 0:
        try:
            handler.tab_params.setCurrentIndex(1)
        except Exception:
            pass
    handler._force_attach_core_widgets()
    handler.list_ops = handler.list_ops or handler._find_any_widget("listOperations")
    handler.tab_params = handler.tab_params or handler._find_any_widget("tabParams")
    handler.btn_add = handler.btn_add or handler._find_any_widget("id:34721") or handler._find_any_widget("btnAdd")
    handler.btn_delete = handler.btn_delete or handler._find_any_widget("btnDelete")
    handler.btn_move_up = handler.btn_move_up or handler._find_any_widget("btnMoveUp")
    handler.btn_move_down = handler.btn_move_down or handler._find_any_widget("btnMoveDown")
    handler.btn_new_program = handler.btn_new_program or handler._find_any_widget("btnNewProgram")
    handler.btn_generate = handler.btn_generate or handler._find_any_widget("id:34722") or handler._find_any_widget("btnGenerate")
    if handler.btn_add is None:
        handler.btn_add = handler._get_widget_by_name("btnAdd")
    if handler.btn_generate is None:
        handler.btn_generate = handler._get_widget_by_name("btnGenerate")
    if getattr(handler, "btn_save_program", None) is None:
        handler.btn_save_program = getattr(handler, "btn_save_program", None) or handler._find_any_widget("id:34724") or handler._find_any_widget("btnSaveProgram")
    if handler.btn_save_step is None:
        handler.btn_save_step = handler._get_widget_by_name("btn_save_step")
    if handler.btn_load_step is None:
        handler.btn_load_step = handler._get_widget_by_name("btn_load_step")
    handler.contour_add_segment = handler.contour_add_segment or handler._find_any_widget("contour_add_segment")
    handler.contour_delete_segment = handler.contour_delete_segment or handler._find_any_widget("contour_delete_segment")
    handler.contour_move_up = handler.contour_move_up or handler._find_any_widget("contour_move_up")
    handler.contour_move_down = handler.contour_move_down or handler._find_any_widget("contour_move_down")
    handler._ensure_contour_widgets()
    handler._init_contour_table()
    try:
        handler._log(f"[LatheEasyStep] core widgets FIX: add={handler.btn_add} del={handler.btn_delete} list={handler.list_ops}", level="info")
    except Exception:
        pass
    handler._ensure_preview_widgets()
    handler._connect_core_signals()
    try:
        handler._connect_param_change_signals()
        handler._connect_global_form_signals()
        handler._connect_tool_preview_signals()
        handler._connect_mode_visibility_signals()
    except Exception as exc:
        handler._log(f"[LatheEasyStep] finalize signal setup failed: {exc}", level="warning")
    handler._ensure_core_widgets()
    handler._update_parting_contour_choices()
    handler._update_parting_ready_state()
    try:
        handler._apply_tab_titles(handler._current_language_code())
        handler._handle_global_change()
    except Exception:
        pass
    try:
        if getattr(handler, "w", None) is not None:
            try:
                setattr(handler.w, "ui_ready", True)
            except Exception:
                try:
                    handler.w.setProperty("ui_ready", True)
                except Exception:
                    pass
    except Exception:
        pass

    critical_ok = all([
        handler.list_ops is not None,
        handler.btn_add is not None,
        handler.btn_generate is not None,
        handler.tab_params is not None,
    ])
    if critical_ok:
        handler._ui_finalized = True
        handler._startup_complete = True
        handler._startup_in_progress = False
        handler._log(
            f'[LatheEasyStep] _finalize_ui_ready DONE after pass {getattr(handler, "_finalize_pass", "?")} — '
            f'all critical widgets found, skipping further passes',
            level="info",
        )
        handler._startup_mark("_finalize_ui_ready critical done")
        handler._schedule_post_start_init()
    else:
        missing = [name for name, widget in [
            ("list_ops", handler.list_ops), ("btn_add", handler.btn_add),
            ("btn_generate", handler.btn_generate), ("tab_params", handler.tab_params),
        ] if widget is None]
        handler._log(
            f'[LatheEasyStep] _finalize_ui_ready pass {getattr(handler, "_finalize_pass", "?")} — '
            f'still missing: {missing}, will retry on next timer',
            level="info",
        )
