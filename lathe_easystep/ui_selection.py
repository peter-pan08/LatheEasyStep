from __future__ import annotations

from .model import OpType


def handle_tab_changed(handler, *_args, **_kwargs) -> None:
    """Keep list selection and tab-specific helpers in sync."""
    if (
        not getattr(handler, "_ui_loading", False)
        and not getattr(handler, "_dirty_warning_suppressed", False)
        and getattr(handler, "_startup_complete", False)
    ):
        try:
            handler._warn_if_dirty("Tabwechsel")
        except Exception:
            pass
    current_type = handler._current_op_type()
    if current_type != OpType.PROGRAM_HEADER:
        try:
            handler._select_operation_for_current_tab(current_type)
        except Exception as exc:
            handler._log(f"[LatheEasyStep] tab-to-operation sync failed: {exc}", level="warning")
    if current_type == OpType.PROGRAM_HEADER:
        try:
            header = handler._collect_program_header()
            handler._load_program_header_to_form(header)
        except Exception:
            pass
    if current_type == OpType.THREAD and not getattr(handler, "_thread_standard_populated", False):
        try:
            handler._setup_thread_helpers()
        except Exception:
            pass
    if current_type == OpType.ABSPANEN:
        handler._update_parting_contour_choices()
    handler._update_parting_ready_state()


def on_step_double_clicked(handler, item) -> None:
    """Flush current form values, select the clicked step, then load its tab/form."""
    try:
        if handler.list_ops is None:
            return
        index = handler.list_ops.row(item)
        if index < 0 or index >= len(handler.model.operations):
            return

        handler._log(
            f"[LatheEasyStep] double-click: row={index}, "
            f"op_type={handler.model.operations[index].op_type}",
            level="info",
        )

        prev_idx = handler.list_ops.currentRow()
        if 0 <= prev_idx < len(handler.model.operations) and prev_idx != index:
            handler._op_row_user_selected = True
            handler._update_selected_operation(force=True)

        handler.list_ops.blockSignals(True)
        handler.list_ops.setCurrentRow(index)
        handler.list_ops.blockSignals(False)

        handler._op_row_user_selected = True
        handler._handle_selection_change(index)
    except Exception as exc:
        handler._log(f"[LatheEasyStep] _on_step_double_clicked error: {exc}", level="info")


def handle_selection_change(handler, row: int) -> None:
    previous_row = getattr(handler, "_active_form_operation_index", -1)
    if (
        not getattr(handler, "_ui_loading", False)
        and previous_row != row
        and 0 <= previous_row < len(handler.model.operations)
        and not getattr(handler, "_dirty_warning_suppressed", False)
        and getattr(handler, "_startup_complete", False)
    ):
        try:
            handler._warn_if_dirty("Stepwechsel", row=previous_row)
        except Exception:
            pass
    if (
        not getattr(handler, "_ui_loading", False)
        and previous_row != row
        and 0 <= previous_row < len(handler.model.operations)
    ):
        try:
            handler._sync_form_to_operation(previous_row)
        except Exception as exc:
            handler._log(f"[LatheEasyStep] sync previous operation failed: {exc}", level="warning")

    handler._ui_loading = True
    try:
        handler._op_row_user_selected = bool(
            handler.list_ops
            and (handler.list_ops.hasFocus() or handler._op_row_user_selected)
        )
        if row < 0 or row >= len(handler.model.operations):
            return
        op = handler.model.operations[row]
        if handler.tab_params:
            type_to_tab = {
                OpType.PROGRAM_HEADER: 0,
                OpType.FACE: 1,
                OpType.CONTOUR: 2,
                OpType.ABSPANEN: 3,
                OpType.THREAD: 4,
                OpType.GROOVE: 5,
                OpType.DRILL: 6,
                OpType.KEYWAY: 7,
            }
            handler._dirty_warning_suppressed = True
            try:
                handler.tab_params.setCurrentIndex(type_to_tab.get(op.op_type, 1))
            finally:
                handler._dirty_warning_suppressed = False
        handler._load_params_to_form(op)
        try:
            if op.op_type == OpType.FACE:
                handler._update_face_visibility()
        except Exception:
            pass
        try:
            handler._update_retract_visibility()
        except Exception:
            pass
        handler._refresh_preview()
        handler._active_form_operation_index = row
    finally:
        handler._ui_loading = False
