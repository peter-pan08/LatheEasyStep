from __future__ import annotations

from typing import Dict

from qtpy import QtCore, QtWidgets

from .model import OpType


def setup_param_maps(handler) -> None:
    # Performance: setup_param_maps() wurde bisher bei JEDEM Feld-Edit, jedem
    # Stepwechsel und jedem Tabwechsel komplett neu aufgebaut - jedesmal ueber
    # 100 einzelne _get_widget_by_name()-Aufrufe mit eigener Baumsuche. Das war
    # die Hauptursache fuer traege Tab-/Stepwechsel und kurzzeitig blockierte
    # Panel-Reaktion. Widgets verschwinden nach dem UI-Aufbau nicht mehr, daher
    # reicht ein einmaliger Aufbau; nur falls beim ersten Versuch (z. B. sehr
    # frueh im Startup) noch Widgets fehlen, wird beim naechsten Aufruf erneut
    # versucht (selbstheilend), bis alle gefunden sind.
    existing = getattr(handler, "param_widgets", None)
    if isinstance(existing, dict) and existing and all(
        widget is not None
        for widgets in existing.values()
        for widget in widgets.values()
    ):
        return

    try:
        handler._log("[LatheEasyStep][debug] setup_param_maps: (re)building widget map", level="debug")
    except Exception:
        pass
    handler.param_widgets: Dict[str, Dict[str, QtWidgets.QWidget]] = {
        OpType.FACE: {
            "tool": handler._get_widget_by_name("face_tool"),
            "start_x": handler._get_widget_by_name("face_start_x"),
            "start_z": handler._get_widget_by_name("face_start_z"),
            "end_x": handler._get_widget_by_name("face_end_x"),
            "end_z": handler._get_widget_by_name("face_end_z"),
            "safe_z": handler._get_widget_by_name("face_safe_z"),
            "feed": handler._get_widget_by_name("face_feed"),
            "depth_per_pass": handler._get_widget_by_name("face_depth_per_pass"),
            "finish_allow_x": handler._get_widget_by_name("face_finish_allow_x"),
            "finish_allow_z": handler._get_widget_by_name("face_finish_allow_z"),
            "finish_direction": handler._get_widget_by_name("face_finish_direction"),
            "depth_max": handler._get_widget_by_name("face_depth_max"),
            "pause_enabled": handler._get_widget_by_name("face_pause_enabled"),
            "pause_distance": handler._get_widget_by_name("face_pause_distance"),
            "mode": handler._get_widget_by_name("face_mode"),
            "edge_type": handler._get_widget_by_name("face_edge_type"),
            "edge_size": handler._get_widget_by_name("face_edge_size"),
            "spindle": handler._get_widget_by_name("face_spindle"),
            "coolant": handler._get_widget_by_name("face_coolant"),
        },
        OpType.CONTOUR: {
            "start_x": handler._get_widget_by_name("contour_start_x"),
            "start_z": handler._get_widget_by_name("contour_start_z"),
            "coord_mode": handler._get_widget_by_name("contour_coord_mode"),
        },
        OpType.THREAD: {
            "tool": handler._get_widget_by_name("thread_tool"),
            "spindle": handler._get_widget_by_name("thread_spindle"),
            "coolant": handler._get_widget_by_name("thread_coolant"),
            "orientation": handler._get_widget_by_name("thread_orientation"),
            "hand": handler._get_widget_by_name("thread_hand"),
            "standard": handler._get_widget_by_name("thread_standard"),
            "major_diameter": handler._get_widget_by_name("thread_major_diameter"),
            "pitch": handler._get_widget_by_name("thread_pitch"),
            "length": handler._get_widget_by_name("thread_length"),
            "thread_start_z": handler._get_widget_by_name("thread_start_z"),
            "passes": handler._get_widget_by_name("thread_passes"),
            "safe_z": handler._get_widget_by_name("thread_safe_z"),
            "thread_depth": handler._get_widget_by_name("thread_depth"),
            "peak_offset": handler._get_widget_by_name("thread_peak_offset"),
            "first_depth": handler._get_widget_by_name("thread_first_depth"),
            "retract_r": handler._get_widget_by_name("thread_retract_r"),
            "infeed_q": handler._get_widget_by_name("thread_infeed_q"),
            "spring_passes": handler._get_widget_by_name("thread_spring_passes"),
            "e": handler._get_widget_by_name("thread_e"),
            "l": handler._get_widget_by_name("thread_l"),
            "relief_mode": handler._get_widget_by_name("thread_relief_mode"),
            "relief_norm": handler._get_widget_by_name("thread_relief_norm"),
            "optional_stop_before": handler._get_widget_by_name("thread_optional_stop_before"),
        },
        OpType.GROOVE: {
            "process_type": handler._get_widget_by_name("groove_process_type"),
            "tool": handler._get_widget_by_name("groove_tool"),
            "spindle": handler._get_widget_by_name("groove_spindle"),
            "coolant": handler._get_widget_by_name("groove_coolant"),
            "diameter": handler._get_widget_by_name("groove_diameter"),
            "width": handler._get_widget_by_name("groove_width"),
            "ref": handler._get_widget_by_name("groove_ref"),
            "lage": handler._get_widget_by_name("groove_lage"),
            "use_tool_width": handler._get_widget_by_name("groove_use_tool_width"),
            "cutting_width": handler._get_widget_by_name("groove_cutting_width"),
            "depth": handler._get_widget_by_name("groove_depth"),
            "z": handler._get_widget_by_name("groove_z"),
            "feed": handler._get_widget_by_name("groove_feed"),
            "stepA": handler._get_widget_by_name("groove_step_a"),
            "overlap": handler._get_widget_by_name("groove_overlap"),
            "retract": handler._get_widget_by_name("groove_retract"),
            "finish": handler._get_widget_by_name("groove_finish"),
            "sweep_feed": handler._get_widget_by_name("groove_sweep_feed"),
            "chip_amp": handler._get_widget_by_name("groove_chip_amp"),
            "chip_n": handler._get_widget_by_name("groove_chip_n"),
            "safe_z": handler._get_widget_by_name("groove_safe_z"),
            "reduced_feed_start_x": handler._get_widget_by_name("groove_reduced_feed_start_x"),
            "reduced_feed": handler._get_widget_by_name("groove_reduced_feed"),
            "reduced_rpm": handler._get_widget_by_name("groove_reduced_rpm"),
        },
        OpType.DRILL: {
            "tool": handler._get_widget_by_name("drill_tool"),
            "spindle": handler._get_widget_by_name("drill_spindle"),
            "coolant": handler._get_widget_by_name("drill_coolant"),
            "mode": handler._get_widget_by_name("drill_mode"),
            "diameter": handler._get_widget_by_name("drill_diameter"),
            "depth": handler._get_widget_by_name("drill_depth"),
            "feed": handler._get_widget_by_name("drill_feed"),
            "safe_z": handler._get_widget_by_name("drill_safe_z"),
            "dwell": handler._get_widget_by_name("drill_dwell"),
            "peck_depth": handler._get_widget_by_name("drill_peck_depth"),
        },
        OpType.KEYWAY: {
            "tool": getattr(handler, "key_tool", None) or handler._get_widget_by_name("key_tool"),
            "feed": getattr(handler, "key_plunge_feed", None) or handler._get_widget_by_name("key_plunge_feed"),
            "mode": getattr(handler, "key_mode", None) or handler._get_widget_by_name("key_mode"),
            "radial_side": getattr(handler, "key_radial_side", None) or handler._get_widget_by_name("key_radial_side"),
            "coolant": getattr(handler, "key_coolant", None) or handler._get_widget_by_name("key_coolant"),
            "slot_count": getattr(handler, "key_slot_count", None) or handler._get_widget_by_name("key_slot_count"),
            "slot_start_angle": getattr(handler, "key_slot_start_angle", None) or handler._get_widget_by_name("key_slot_start_angle"),
            "slot_angle_step": getattr(handler, "key_slot_angle_step", None) or handler._get_widget_by_name("key_slot_angle_step"),
            "start_x_dia": getattr(handler, "key_start_diameter", None) or handler._get_widget_by_name("key_start_diameter"),
            "start_z": getattr(handler, "key_start_z", None) or handler._get_widget_by_name("key_start_z"),
            "nut_length": getattr(handler, "key_nut_length", None) or handler._get_widget_by_name("key_nut_length"),
            "nut_depth": getattr(handler, "key_nut_depth", None) or handler._get_widget_by_name("key_nut_depth"),
            "slot_width": getattr(handler, "key_slot_width", None) or handler._get_widget_by_name("key_slot_width"),
            "cutting_width": getattr(handler, "key_cutting_width", None) or handler._get_widget_by_name("key_cutting_width"),
            "top_clearance": getattr(handler, "key_top_clearance", None) or handler._get_widget_by_name("key_top_clearance"),
            "depth_per_pass": getattr(handler, "key_depth_per_pass", None) or handler._get_widget_by_name("key_depth_per_pass"),
            "plunge_feed": getattr(handler, "key_plunge_feed", None) or handler._get_widget_by_name("key_plunge_feed"),
            "use_c_axis": getattr(handler, "key_use_c_axis", None) or handler._get_widget_by_name("key_use_c_axis"),
            "use_c_axis_switch": getattr(handler, "key_use_c_axis_switch", None) or handler._get_widget_by_name("key_use_c_axis_switch"),
            "c_axis_switch_p": getattr(handler, "key_c_axis_switch_p", None) or handler._get_widget_by_name("key_c_axis_switch_p"),
        },
        OpType.ABSPANEN: {
            "side": handler._get_widget_by_name("parting_side"),
            "tool": handler._get_widget_by_name("parting_tool"),
            "spindle": handler._get_widget_by_name("parting_spindle"),
            "coolant": handler._get_widget_by_name("parting_coolant"),
            "feed": handler._get_widget_by_name("parting_feed"),
            "depth_per_pass": handler._get_widget_by_name("parting_depth_per_pass"),
            "mode": handler._get_widget_by_name("parting_mode"),
            "pause_enabled": handler._get_widget_by_name("parting_pause_enabled"),
            "pause_distance": handler._get_widget_by_name("parting_pause_distance"),
            "slice_strategy": handler._get_widget_by_name("parting_slice_strategy"),
            "slice_step": handler._get_widget_by_name("parting_slice_step"),
            "allow_undercut": handler._get_widget_by_name("parting_allow_undercut"),
            "finish_allow_x": handler._get_widget_by_name("parting_finish_allow_x"),
            "finish_allow_z": handler._get_widget_by_name("parting_finish_allow_z"),
            "undercut_mode": handler._get_widget_by_name("parting_undercut_mode"),
            "output_preference": handler._get_widget_by_name("parting_output_preference"),
            "undercut_tool": handler._get_widget_by_name("parting_undercut_tool"),
            "undercut_spindle": handler._get_widget_by_name("parting_undercut_spindle"),
            "undercut_feed": handler._get_widget_by_name("parting_undercut_feed"),
            "optional_stop_before_undercut": handler._get_widget_by_name("parting_optional_stop_before_undercut"),
        },
    }


def collect_params(handler, op_type: str) -> Dict[str, object]:
    handler._setup_param_maps()
    widgets = handler.param_widgets.get(op_type, {})
    params: Dict[str, object] = {}
    for key, widget in widgets.items():
        if widget is None:
            continue
        try:
            if isinstance(widget, QtWidgets.QSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QComboBox):
                if key == "slice_strategy":
                    idx = widget.currentIndex()
                    data = widget.itemData(idx, QtCore.Qt.UserRole) if idx >= 0 else None
                    if isinstance(data, str) and data:
                        params[key] = data
                    elif isinstance(data, (int, float)):
                        params[key] = int(float(data))
                    elif idx >= 0:
                        # itemData not yet populated but a real selection exists:
                        # fall back to the legacy 1-based numeric convention.
                        params[key] = idx + 1
                    # idx < 0 (no selection at all): leave slice_strategy unset
                    # instead of fabricating an invalid 0 - gcode_roughing.py
                    # cannot tell that apart from a real (but wrong) strategy
                    # code and would silently disable roughing.
                else:
                    data = widget.currentData()
                    if data is not None:
                        params[key] = data
                    else:
                        params[key] = float(widget.currentIndex())
            elif isinstance(widget, QtWidgets.QLineEdit):
                text = widget.text().strip()
                if text == "":
                    continue
                # try float, else keep as string
                try:
                    params[key] = float(text.replace(",", "."))
                except Exception:
                    params[key] = text
            elif isinstance(widget, QtWidgets.QAbstractButton):
                params[key] = float(widget.isChecked())
            else:
                # Fallback: only record if we can safely read something
                if hasattr(widget, "value"):
                    params[key] = float(widget.value())
                elif hasattr(widget, "text"):
                    text = str(widget.text()).strip()
                    if text != "":
                        params[key] = text
        except Exception:
            # Never let a broken widget mapping wipe the whole params dict
            continue
    # Kontur-Segmente separat aus Tabelle einsammeln
    if op_type == OpType.CONTOUR:
        params["segments"] = handler._collect_contour_segments()
        if getattr(handler, "contour_name", None):
            name = handler.contour_name.text().strip()
            if not name:
                name = handler._fallback_contour_name(handler._contour_count())
                # UI optional anreichern, damit Nutzer den vergebenen Namen sieht
                try:
                    handler.contour_name.setText(name)
                except Exception:
                    pass
            params["name"] = name
    elif op_type == OpType.ABSPANEN:
        contour_name = handler._current_parting_contour_name()
        params["contour_name"] = contour_name
        params["source_path"] = handler._resolve_contour_path(contour_name)
    elif op_type == OpType.FACE:
        # Defaults für FACE, da slicer.py keine harten Defaults hat
        defaults = {
            "retract": 0.5,
            "depth_max": 0.4,
            "feed": 0.2,
            "spindle": 1300.0,
            "tool": 1,
            "mode": 0,
            "edge_type": 0,
            "edge_size": 0.0,
            "finish_allow_z": 0.05,
            "start_x": 40.0,
            "start_z": 1.0,
            "end_x": -1.0,
            "end_z": 0.0,
            "coolant": False,
        }
        for key, default in defaults.items():
            if key not in params or params[key] is None or params[key] == "":
                params[key] = default
    elif op_type == OpType.KEYWAY:
        defaults = {
            "tool": 1,
            "feed": 200.0,
            "plunge_feed": 200.0,
            "slot_count": 1,
            "slot_start_angle": 0.0,
            "slot_angle_step": 0.0,
            "slot_width": 3.0,
            "cutting_width": 3.0,
            "top_clearance": 1.0,
            "depth_per_pass": 0.1,
            "mode": 0,
            "radial_side": 0,
            "coolant": 0,
        }
        for key, default in defaults.items():
            if key not in params or params[key] is None or params[key] == "":
                params[key] = default
    elif op_type == OpType.ABSPANEN:
        defaults = {
            "undercut_mode": "finish_only",
            "output_preference": "auto",
            "undercut_tool": 0,
            "undercut_spindle": 0.0,
            "undercut_feed": 0.0,
            "optional_stop_before_undercut": False,
        }
        for key, default in defaults.items():
            if key not in params or params[key] is None or params[key] == "":
                params[key] = default
    elif op_type == OpType.THREAD:
        defaults = {
            "relief_mode": "off",
            "relief_norm": "DIN 76-A",
            "optional_stop_before": False,
        }
        for key, default in defaults.items():
            if key not in params or params[key] is None or params[key] == "":
                params[key] = default
    return params
