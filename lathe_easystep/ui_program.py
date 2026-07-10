from __future__ import annotations

from typing import Dict

from qtpy import QtWidgets

from .model import OpType


def apply_program_header_to_handler(
    handler,
    header: Dict[str, object],
    *,
    apply_chuck_preset_if_missing: bool,
) -> None:
    if not isinstance(header, dict):
        return

    def set_combo(widget, value):
        if widget is None or value is None:
            return
        idx = -1
        try:
            idx = widget.findData(value)
        except Exception:
            idx = -1
        if idx < 0:
            try:
                idx = widget.findText(str(value))
            except Exception:
                return
        if idx >= 0:
            widget.blockSignals(True)
            widget.setCurrentIndex(idx)
            widget.blockSignals(False)

    def set_value(widget, value):
        if widget is None or value is None:
            return
        widget.blockSignals(True)
        try:
            if isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(int(float(value)))
            else:
                widget.setValue(float(value))
        except Exception:
            try:
                widget.setValue(float(value))
            except Exception:
                pass
        finally:
            widget.blockSignals(False)

    def set_checked(widget, value):
        if widget is None:
            return
        widget.blockSignals(True)
        widget.setChecked(bool(value))
        widget.blockSignals(False)

    set_combo(handler.program_npv, header.get("npv"))
    set_combo(handler.program_unit, header.get("unit"))
    set_combo(handler.program_shape, header.get("shape"))
    set_combo(handler.program_retract_mode, header.get("retract_mode"))
    set_combo(getattr(handler, "program_machine_profile", None), header.get("machine_profile"))
    set_combo(getattr(handler, "program_chuck_size", None), header.get("chuck_size"))
    set_combo(getattr(handler, "program_chuck_part_type", None), header.get("chuck_part_type"))
    set_combo(getattr(handler, "program_chuck_grip_mode", None), header.get("chuck_grip_mode"))
    set_combo(getattr(handler, "program_chuck_profile", None), header.get("chuck_profile"))
    set_combo(getattr(handler, "program_spindle_mode", None), header.get("spindle_mode"))
    set_combo(getattr(handler, "program_park_mode", None), header.get("park_mode"))
    toolchange_coords = header.get("toolchange_coords")
    if toolchange_coords is None:
        toolchange_coords = "work" if bool(header.get("xt_absolute", True)) and bool(header.get("zt_absolute", True)) else "machine"
    set_combo(getattr(handler, "program_toolchange_coords", None), toolchange_coords)
    park_coords = header.get("park_coords")
    if park_coords is None:
        park_coords = toolchange_coords
    set_combo(getattr(handler, "program_park_coords", None), park_coords)

    set_value(handler.program_xa, header.get("xa"))
    set_value(handler.program_xi, header.get("xi"))
    set_value(handler.program_za, header.get("za"))
    set_value(handler.program_zi, header.get("zi"))
    set_value(handler.program_zb, header.get("zb"))
    set_value(handler.program_xra, header.get("xra"))
    set_value(handler.program_xri, header.get("xri"))
    set_value(handler.program_zra, header.get("zra"))
    set_value(handler.program_zri, header.get("zri"))
    set_value(handler.program_w, header.get("w"))
    set_value(handler.program_l, header.get("l"))
    set_value(handler.program_n, header.get("n_edges"))
    set_value(handler.program_sw, header.get("sw"))
    set_value(handler.program_xt, header.get("xt"))
    set_value(handler.program_zt, header.get("zt"))
    set_value(handler.program_sc, header.get("sc"))
    set_value(getattr(handler, "program_chuck_x_min", None), header.get("chuck_no_go_x_min"))
    set_value(getattr(handler, "program_chuck_x_max", None), header.get("chuck_no_go_x_max"))
    set_value(getattr(handler, "program_chuck_z_limit", None), header.get("chuck_no_go_z_limit"))
    set_value(getattr(handler, "program_spindle_max_rpm", None), header.get("spindle_max_rpm"))
    set_value(getattr(handler, "program_park_x", None), header.get("park_x"))
    set_value(getattr(handler, "program_park_z", None), header.get("park_z"))
    set_value(handler.program_s1, header.get("s1_max"))
    set_value(handler.program_s3, header.get("s3_max"))

    set_checked(handler.program_xra_absolute, header.get("xra_absolute"))
    set_checked(handler.program_xri_absolute, header.get("xri_absolute"))
    set_checked(handler.program_zra_absolute, header.get("zra_absolute"))
    set_checked(handler.program_zri_absolute, header.get("zri_absolute"))
    set_checked(handler.program_xt_absolute, header.get("xt_absolute"))
    set_checked(handler.program_zt_absolute, header.get("zt_absolute"))
    set_checked(handler.program_has_subspindle, header.get("has_subspindle"))
    set_checked(getattr(handler, "program_park_sequential", None), header.get("park_sequential"))
    set_checked(getattr(handler, "program_optional_stop_toolchange", None), header.get("optional_stop_toolchange"))
    set_checked(getattr(handler, "program_preview_warnings", None), header.get("preview_warnings"))

    if handler.program_name is not None:
        handler.program_name.blockSignals(True)
        handler.program_name.setText(str(header.get("program_name") or ""))
        handler.program_name.blockSignals(False)

    handler._apply_unit_suffix()
    if apply_chuck_preset_if_missing and (
        header.get("chuck_no_go_x_min") is None
        or header.get("chuck_no_go_x_max") is None
        or header.get("chuck_no_go_z_limit") is None
    ):
        handler._apply_chuck_safety_preset()
    handler._update_program_visibility()
    handler._update_retract_visibility()
    handler._update_subspindle_visibility()


def sync_form_to_operation(handler, idx: int) -> None:
    if idx < 0 or idx >= len(handler.model.operations):
        return
    op = handler.model.operations[idx]
    previous_params = dict(op.params or {})
    if op.op_type == OpType.PROGRAM_HEADER:
        op.params = handler._collect_program_header()
    else:
        collected_params = handler._collect_params(op.op_type)
        op.params = dict(previous_params)
        op.params.update(collected_params)
    for key, value in previous_params.items():
        if isinstance(key, str) and key.startswith("__") and key not in op.params:
            op.params[key] = value
    handler.model.update_geometry(op)
    description = handler._describe_operation(op, idx + 1)
    if handler.list_ops:
        item = handler.list_ops.item(idx)
        if item:
            item.setText(description)
    op.params["comment"] = description
