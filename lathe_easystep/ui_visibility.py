from __future__ import annotations

import re

from qtpy import QtCore, QtWidgets

def handle_global_change(handler, *args, **kwargs):
    sender_name = ""
    try:
        sender_fn = getattr(handler, "sender", None)
        sender = sender_fn() if callable(sender_fn) else None
        sender_name = sender.objectName() if sender is not None and hasattr(sender, "objectName") else ""
    except Exception:
        sender_name = ""
    if sender_name == "program_machine_profile":
        handler._apply_machine_profile_preset()
    handler._apply_unit_suffix()
    handler._apply_chuck_safety_preset()
    handler._update_program_visibility()
    handler._update_retract_visibility()
    handler._update_subspindle_visibility()
    handler._update_face_visibility()
    if sender_name and sender_name != "program_language" and not getattr(handler, "_ui_loading", False):
        try:
            handler._mark_dirty(program=True)
        except Exception:
            pass
    if getattr(handler, "_startup_complete", False):
        handler._refresh_preview()


def apply_machine_profile_preset(handler) -> None:
    if getattr(handler, "_applying_machine_profile", False):
        return
    profile_combo = getattr(handler, "program_machine_profile", None)
    if profile_combo is None:
        return
    try:
        profile_idx = int(profile_combo.currentIndex())
    except Exception:
        profile_idx = 0
    if profile_idx <= 0:
        return
    preset = handler.MACHINE_CHUCK_PROFILE_PRESETS.get(profile_idx)
    if not preset:
        return
    handler._applying_machine_profile = True
    try:
        mappings = (
            (getattr(handler, "program_chuck_size", None), int(preset.get("chuck_size_idx", 0))),
            (getattr(handler, "program_chuck_part_type", None), int(preset.get("part_type_idx", 0))),
            (getattr(handler, "program_chuck_grip_mode", None), int(preset.get("grip_mode_idx", 0))),
            (getattr(handler, "program_chuck_profile", None), int(preset.get("chuck_profile_idx", 0))),
        )
        for combo, idx in mappings:
            if combo is None:
                continue
            try:
                if 0 <= idx < int(combo.count()) and int(combo.currentIndex()) != idx:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
            except Exception:
                pass
            finally:
                try:
                    combo.blockSignals(False)
                except Exception:
                    pass
    finally:
        handler._applying_machine_profile = False


def chuck_size_mm(handler) -> int:
    combo = getattr(handler, "program_chuck_size", None)
    if combo is None:
        return 0
    try:
        data = combo.currentData()
    except Exception:
        data = None
    if isinstance(data, str):
        token = data.strip().lower()
        if token in {"", "none"}:
            return 0
        if token.isdigit():
            return int(token)
    try:
        idx = int(combo.currentIndex())
        item_data = combo.itemData(idx, QtCore.Qt.UserRole)
        if isinstance(item_data, str):
            token = item_data.strip().lower()
            if token in {"", "none"}:
                return 0
            if token.isdigit():
                return int(token)
    except Exception:
        pass
    try:
        txt = str(combo.currentText() or "").lower().strip()
    except Exception:
        return 0
    match = re.search(r"(\d+)", txt)
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def apply_chuck_safety_preset(handler) -> None:
    if getattr(handler, "_applying_chuck_preset", False):
        return
    size_mm = handler._chuck_size_mm()
    x_min_w = getattr(handler, "program_chuck_x_min", None)
    x_max_w = getattr(handler, "program_chuck_x_max", None)
    z_lim_w = getattr(handler, "program_chuck_z_limit", None)
    sc_w = getattr(handler, "program_sc", None)
    if x_min_w is None or x_max_w is None or z_lim_w is None or size_mm <= 0:
        return
    preset = handler.CHUCK_PRESETS.get(size_mm)
    if not preset:
        return
    xa = handler._widget_get_value(getattr(handler, "program_xa", None)) or 0.0
    xi = handler._widget_get_value(getattr(handler, "program_xi", None)) or 0.0
    zb = handler._widget_get_value(getattr(handler, "program_zb", None)) or 0.0
    part_type_idx = 0
    grip_idx = 0
    profile_idx = 0
    try:
        if getattr(handler, "program_chuck_part_type", None) is not None:
            part_type_idx = int(handler.program_chuck_part_type.currentIndex())
    except Exception:
        part_type_idx = 0
    try:
        if getattr(handler, "program_chuck_grip_mode", None) is not None:
            grip_idx = int(handler.program_chuck_grip_mode.currentIndex())
    except Exception:
        grip_idx = 0
    try:
        if getattr(handler, "program_chuck_profile", None) is not None:
            profile_idx = int(handler.program_chuck_profile.currentIndex())
    except Exception:
        profile_idx = 0
    profile_mod = handler.CHUCK_PROFILE_MODIFIERS.get(profile_idx, handler.CHUCK_PROFILE_MODIFIERS[0])
    jaw_band = float(preset["jaw_band"]) * float(profile_mod.get("jaw_band_mul", 1.0))
    sc_default = max(0.2, float(preset["sc"]) + float(profile_mod.get("sc_add", 0.0)))
    jaw_depth_z = float(preset["jaw_depth_z"]) * float(profile_mod.get("jaw_depth_mul", 1.0))
    if grip_idx == 0:
        x_min = max(float(xa) - 2.0 * jaw_band, 0.0)
        x_max = float(size_mm) + 2.0 * sc_default
    else:
        if part_type_idx == 1 and float(xi) > 0.0:
            x_min = 0.0
            x_max = max(float(xi) + 2.0 * jaw_band + 2.0 * sc_default, 2.0 * sc_default)
        else:
            x_min = 0.0
            x_max = max(float(size_mm) * 0.6, 2.0 * sc_default)
    z_limit = float(zb) - jaw_depth_z - sc_default
    handler._applying_chuck_preset = True
    try:
        for w, val in ((x_min_w, x_min), (x_max_w, x_max), (z_lim_w, z_limit)):
            try:
                w.blockSignals(True)
                w.setValue(float(val))
            finally:
                w.blockSignals(False)
        if sc_w is not None:
            try:
                curr_sc = float(sc_w.value())
            except Exception:
                curr_sc = 0.0
            if curr_sc <= 0.0:
                try:
                    sc_w.blockSignals(True)
                    sc_w.setValue(sc_default)
                finally:
                    sc_w.blockSignals(False)
    finally:
        handler._applying_chuck_preset = False


def apply_unit_suffix(handler):
    if handler.program_unit is None:
        handler.program_unit = handler._find_unit_combo()
        if handler.program_unit is None:
            handler._log("[LatheEasyStep] _apply_unit_suffix: no unit combo, abort", level="info")
            return
    idx = handler.program_unit.currentIndex()
    unit = "mm" if idx == 0 else "inch"
    unit_suffix = f" {unit}"
    feed_suffix = f" {unit}/U"
    root = handler.root_widget or handler.program_unit.window()
    if root is None:
        return
    for sb in root.findChildren(QtWidgets.QDoubleSpinBox):
        name = sb.objectName()
        angle_fields = {"thread_infeed_q", "key_slot_start_angle", "key_slot_angle_step"}
        if name in angle_fields:
            sb.setSuffix(" °")
            continue
        if name in ("program_s1", "program_s3") or "spindle" in name.lower():
            sb.setSuffix("")
            continue
        sb.setSuffix(feed_suffix if "feed" in name.lower() else unit_suffix)
    if not hasattr(handler, "_labels_cleaned") or not handler._labels_cleaned:
        for lbl in root.findChildren(QtWidgets.QLabel):
            text = lbl.text()
            if "(" in text and ")" in text and any(u in text for u in ("mm", "inch", "/U")):
                prefix = text.split("(", 1)[0].rstrip()
                lbl.setText(prefix)
        handler._labels_cleaned = True
    try:
        win = root.window()
        old_title = win.windowTitle()
        win.setWindowTitle(f"{old_title.split('[')[0].strip()} [{unit}]")
    except Exception:
        pass


def update_program_visibility(handler, shape=None):
    shape_idx = None
    if hasattr(handler, "program_shape") and handler.program_shape is not None:
        try:
            data = handler.program_shape.currentData()
        except Exception:
            data = None
        if isinstance(data, str) and data:
            shape_idx = data
        else:
            try:
                shape_idx = int(handler.program_shape.currentIndex())
            except Exception:
                shape_idx = None
    if shape is None:
        if isinstance(shape_idx, str) and shape_idx:
            shape = shape_idx
        else:
            shape = shape_idx if shape_idx is not None and shape_idx >= 0 else None
    if shape is None or shape == "":
        return
    if isinstance(shape, int):
        shape_map = {0: "cylinder", 1: "tube", 2: "rectangle", 3: "polygon"}
        shape_norm = shape_map.get(shape, str(shape)).strip().lower()
    else:
        shape_norm = str(shape).strip().lower()
    root = handler.root_widget or handler._find_root_widget() or getattr(handler, "w", None)
    if root is None:
        return
    def _w(objname: str):
        if not getattr(handler, "widgets", None):
            handler.widgets = {}
        w = handler.widgets.get(objname)
        if w is None:
            try:
                w = handler._get_widget_by_name(objname)
            except Exception:
                w = None
            if w is not None:
                handler.widgets[objname] = w
        return w
    widgets = {
        "label_xa": _w("label_prog_xa"), "xa": _w("program_xa"),
        "label_xi": _w("label_prog_xi"), "xi": _w("program_xi"),
        "label_w": _w("label_prog_w"), "w": _w("program_w"),
        "label_l": _w("label_prog_l"), "l": _w("program_l"),
        "label_n": _w("label_prog_n"), "n": _w("program_n"),
        "label_sw": _w("label_prog_sw"), "sw": _w("program_sw"),
    }
    show_xa = shape_norm in ("cylinder", "tube")
    show_xi = shape_norm in ("tube",)
    show_w = shape_norm in ("rectangle",)
    show_l = shape_norm in ("rectangle",)
    show_n = shape_norm in ("polygon",)
    show_sw = show_n
    for key, visible in {
        "label_xa": show_xa, "xa": show_xa, "label_xi": show_xi, "xi": show_xi,
        "label_w": show_w, "w": show_w, "label_l": show_l, "l": show_l,
        "label_n": show_n, "n": show_n, "label_sw": show_sw, "sw": show_sw,
    }.items():
        w = widgets.get(key)
        if w is not None:
            w.setVisible(bool(visible))


def update_retract_visibility(handler, widget=None, mode_in=None):
    combo = handler.program_retract_mode if not isinstance(widget, QtWidgets.QComboBox) else widget
    if combo is None:
        return
    try:
        mode_code = combo.currentData()
    except Exception:
        mode_code = None
    idx = combo.currentIndex()
    if isinstance(mode_in, (int, float)):
        idx = int(mode_in)
        mode_code = None
    elif isinstance(mode_in, str) and mode_in:
        mode_code = mode_in
    root = handler.root_widget or handler._find_root_widget() or getattr(handler, "w", None)
    if root is None:
        return
    def show(name: str, visible: bool):
        w = None
        try:
            w = handler._get_widget_by_name(name)
        except Exception:
            w = None
        if w is None and root is not None:
            try:
                w = root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
            except Exception:
                w = None
        if w is not None:
            w.setVisible(visible)
    all_widgets = [
        "label_prog_xra", "program_xra", "program_xra_absolute",
        "label_prog_xri", "program_xri", "program_xri_absolute",
        "label_prog_zra", "program_zra", "program_zra_absolute",
        "label_prog_zri", "program_zri", "program_zri_absolute",
        "label_retract_hint",
    ]
    for name in all_widgets:
        show(name, False)
    mode_code = str(mode_code or "").strip().lower()
    if mode_code in ("simple", "") and idx == 0 or mode_code == "simple":
        for name in ("label_prog_xra", "program_xra", "program_xra_absolute", "label_prog_zra", "program_zra", "program_zra_absolute", "label_retract_hint"):
            show(name, True)
    elif mode_code == "extended" or (not mode_code and idx == 1):
        for name in ("label_prog_xra", "program_xra", "program_xra_absolute", "label_prog_zra", "program_zra", "program_zra_absolute", "label_prog_xri", "program_xri", "program_xri_absolute", "label_retract_hint"):
            show(name, True)
    else:
        for name in all_widgets:
            show(name, True)


def update_subspindle_visibility(handler, *args, **kwargs):
    if getattr(handler, "program_has_subspindle", None) is None:
        try:
            handler.program_has_subspindle = handler._get_widget_by_name("program_has_subspindle")
        except Exception:
            handler.program_has_subspindle = None
    if getattr(handler, "label_prog_s3", None) is None:
        try:
            handler.label_prog_s3 = handler._get_widget_by_name("label_prog_s3")
        except Exception:
            handler.label_prog_s3 = None
    if getattr(handler, "program_s3", None) is None:
        try:
            handler.program_s3 = handler._get_widget_by_name("program_s3")
        except Exception:
            handler.program_s3 = None
    has_sub = bool(handler.program_has_subspindle.isChecked()) if handler.program_has_subspindle else False
    root = handler.root_widget or handler._find_root_widget() or getattr(handler, "w", None)
    if handler.label_prog_s3 is None and root:
        handler.label_prog_s3 = root.findChild(QtWidgets.QWidget, "label_prog_s3")
    if handler.program_s3 is None and root:
        handler.program_s3 = root.findChild(QtWidgets.QWidget, "program_s3")
    if handler.label_prog_s3:
        handler.label_prog_s3.setVisible(has_sub)
    if handler.program_s3:
        handler.program_s3.setVisible(has_sub)


def update_face_visibility(handler):
    try:
        root = handler.w.get("MainWindow", None)
    except Exception:
        root = None
    if root is not None:
        if getattr(handler, "label_face_mode", None) is None:
            handler.label_face_mode = root.findChild(QtWidgets.QLabel, "label_face_mode")
        if getattr(handler, "face_mode", None) is None:
            handler.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
        if getattr(handler, "label_face_finish_direction", None) is None:
            handler.label_face_finish_direction = root.findChild(QtWidgets.QLabel, "label_face_finish_direction")
        if getattr(handler, "face_finish_direction", None) is None:
            handler.face_finish_direction = root.findChild(QtWidgets.QComboBox, "face_finish_direction")
        if getattr(handler, "label_face_edge_type", None) is None:
            handler.label_face_edge_type = root.findChild(QtWidgets.QLabel, "label_face_edge_type")
        if getattr(handler, "face_edge_type", None) is None:
            handler.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")
        if getattr(handler, "label_face_edge_size", None) is None:
            handler.label_face_edge_size = root.findChild(QtWidgets.QLabel, "label_face_edge_size")
        if getattr(handler, "face_edge_size", None) is None:
            handler.face_edge_size = root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_size")
        if getattr(handler, "label_face_chamfer", None) is None:
            handler.label_face_chamfer = root.findChild(QtWidgets.QLabel, "label_face_chamfer") or root.findChild(QtWidgets.QLabel, "label_face_fase") or root.findChild(QtWidgets.QLabel, "label_face_edge_chamfer")
        if getattr(handler, "face_chamfer", None) is None:
            handler.face_chamfer = root.findChild(QtWidgets.QDoubleSpinBox, "face_chamfer") or root.findChild(QtWidgets.QDoubleSpinBox, "face_fase") or root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_chamfer")
        if getattr(handler, "label_face_radius", None) is None:
            handler.label_face_radius = root.findChild(QtWidgets.QLabel, "label_face_radius") or root.findChild(QtWidgets.QLabel, "label_face_edge_radius")
        if getattr(handler, "face_radius", None) is None:
            handler.face_radius = root.findChild(QtWidgets.QDoubleSpinBox, "face_radius") or root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_radius")
    if getattr(handler, "face_mode", None) is None or getattr(handler, "face_edge_type", None) is None:
        return
    try:
        mode_data = handler.face_mode.currentData()
    except Exception:
        mode_data = None
    finish_visible = str(mode_data or "").strip().lower() in {"finish", "rough_finish"}
    if getattr(handler, "label_face_finish_direction", None) is not None:
        handler.label_face_finish_direction.setVisible(finish_visible)
    if getattr(handler, "face_finish_direction", None) is not None:
        handler.face_finish_direction.setVisible(finish_visible)
    try:
        edge_data = handler.face_edge_type.currentData()
    except Exception:
        edge_data = None
    edge_mode = str(edge_data or "").strip().lower()
    is_chamfer = edge_mode == "chamfer"
    is_radius = edge_mode == "radius"
    edge_visible = is_chamfer or is_radius
    for w in (
        getattr(handler, "label_face_edge_size", None), getattr(handler, "face_edge_size", None),
        getattr(handler, "label_face_chamfer", None), getattr(handler, "face_chamfer", None),
        getattr(handler, "label_face_radius", None), getattr(handler, "face_radius", None),
    ):
        if w is not None:
            w.setVisible(False)
    if not edge_visible:
        return
    if is_chamfer and getattr(handler, "face_chamfer", None) is not None:
        if getattr(handler, "label_face_chamfer", None) is not None:
            handler.label_face_chamfer.setVisible(True)
        handler.face_chamfer.setVisible(True)
        return
    if is_radius and getattr(handler, "face_radius", None) is not None:
        if getattr(handler, "label_face_radius", None) is not None:
            handler.label_face_radius.setVisible(True)
        handler.face_radius.setVisible(True)
        return
    if getattr(handler, "label_face_edge_size", None) is not None:
        handler.label_face_edge_size.setVisible(True)
    if getattr(handler, "face_edge_size", None) is not None:
        handler.face_edge_size.setVisible(True)


def update_drill_visibility(handler):
    try:
        root = handler.w.get("MainWindow", None)
    except Exception:
        root = None
    if root is not None:
        if getattr(handler, "drill_mode", None) is None:
            handler.drill_mode = root.findChild(QtWidgets.QComboBox, "drill_mode")
        if getattr(handler, "label_drill_dwell", None) is None:
            handler.label_drill_dwell = root.findChild(QtWidgets.QLabel, "label_drill_dwell")
        if getattr(handler, "drill_dwell", None) is None:
            handler.drill_dwell = root.findChild(QtWidgets.QDoubleSpinBox, "drill_dwell")
        if getattr(handler, "label_drill_peck_depth", None) is None:
            handler.label_drill_peck_depth = root.findChild(QtWidgets.QLabel, "label_drill_peck_depth")
        if getattr(handler, "drill_peck_depth", None) is None:
            handler.drill_peck_depth = root.findChild(QtWidgets.QDoubleSpinBox, "drill_peck_depth")
    if getattr(handler, "drill_mode", None) is None:
        return
    mode_idx = handler.drill_mode.currentIndex()
    dwell_visible = mode_idx == 1
    peck_visible = mode_idx in (2, 3)
    if getattr(handler, "label_drill_dwell", None) is not None:
        handler.label_drill_dwell.setVisible(dwell_visible)
    if getattr(handler, "drill_dwell", None) is not None:
        handler.drill_dwell.setVisible(dwell_visible)
    if getattr(handler, "label_drill_peck_depth", None) is not None:
        handler.label_drill_peck_depth.setVisible(peck_visible)
    if getattr(handler, "drill_peck_depth", None) is not None:
        handler.drill_peck_depth.setVisible(peck_visible)
