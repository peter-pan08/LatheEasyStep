from __future__ import annotations

from .model import OpType
from .ui_step_list_view import StepListView


def update_operation_action_button_states(handler) -> None:
    """Enable delete/reorder actions only when the selected step permits them."""
    buttons = {
        "delete": getattr(handler, "btn_delete", None),
        "up": getattr(handler, "btn_move_up", None),
        "down": getattr(handler, "btn_move_down", None),
    }
    states = {"delete": False, "up": False, "down": False}
    try:
        operations = handler.model.operations
        index = handler._selected_operation_index()
        if 0 <= index < len(operations):
            operation = operations[index]
            movable = getattr(operation, "op_type", None) != OpType.PROGRAM_HEADER
            states["delete"] = movable
            states["up"] = (
                movable
                and index > 0
                and getattr(operations[index - 1], "op_type", None) != OpType.PROGRAM_HEADER
            )
            states["down"] = movable and index < len(operations) - 1
    except Exception:
        pass
    for name, button in buttons.items():
        if button is not None:
            try:
                button.setEnabled(states[name])
            except Exception:
                pass


def handle_tab_changed(handler, *_args, **_kwargs) -> None:
    """Keep list selection and tab-specific helpers in sync."""
    if (
        not handler._runtime.ui_loading
        and not handler._dirty.warning_suppressed
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
        step_list = StepListView(handler)
        if not step_list.is_bound():
            return
        index = step_list.row_of(item)
        if index < 0 or index >= len(handler.model.operations):
            return

        handler._log(
            f"[LatheEasyStep] double-click: row={index}, "
            f"op_type={handler.model.operations[index].op_type}",
            level="info",
        )

        prev_idx = step_list.selected_row()
        if 0 <= prev_idx < len(handler.model.operations) and prev_idx != index:
            handler._op_row_user_selected = True
            handler._update_selected_operation(force=True)

        step_list.select_row(index, block_signals=True)

        handler._op_row_user_selected = True
        handler._handle_selection_change(index)
    except Exception as exc:
        handler._log(f"[LatheEasyStep] _on_step_double_clicked error: {exc}", level="info")


def handle_selection_change(handler, row: int) -> None:
    previous_row = getattr(handler, "_active_form_operation_index", -1)
    if (
        not handler._runtime.ui_loading
        and previous_row != row
        and 0 <= previous_row < len(handler.model.operations)
        and not handler._dirty.warning_suppressed
        and getattr(handler, "_startup_complete", False)
    ):
        try:
            handler._warn_if_dirty("Stepwechsel", row=previous_row)
        except Exception:
            pass
    if (
        not handler._runtime.ui_loading
        and previous_row != row
        and 0 <= previous_row < len(handler.model.operations)
    ):
        try:
            handler._sync_form_to_operation(previous_row)
        except Exception as exc:
            handler._log(f"[LatheEasyStep] sync previous operation failed: {exc}", level="warning")

    handler._runtime.ui_loading = True
    try:
        step_list = StepListView(handler)
        handler._op_row_user_selected = bool(
            step_list.is_bound()
            and (step_list.has_focus() or handler._op_row_user_selected)
        )
        try:
            handler._update_save_step_button_state()
        except Exception:
            pass
        try:
            handler._update_operation_action_button_states()
        except Exception:
            pass
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
            handler._dirty.warning_suppressed = True
            try:
                handler.tab_params.setCurrentIndex(type_to_tab.get(op.op_type, 1))
            finally:
                handler._dirty.warning_suppressed = False
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
        try:
            handler._update_spindle_mode_visibility()
        except Exception:
            pass
        handler._refresh_preview()
        handler._active_form_operation_index = row
    finally:
        handler._runtime.ui_loading = False
