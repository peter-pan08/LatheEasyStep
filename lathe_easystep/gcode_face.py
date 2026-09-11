from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .gcode_utils import resolve_enum_index
from .model import Operation
from .face_geometry import face_primitives
from .gcode_roughing import contour_sub_from_primitives
from .gcode_safety import _motion_state, activate_pending_css
from .numeric import finite_float, validate_finite_data

FACE_MODE_INDEX = {"rough": 0, "finish": 1, "rough_finish": 2}
FACE_EDGE_TYPE_INDEX = {"none": 0, "chamfer": 1, "radius": 2}


def generate_face_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require_tool: Callable[[Dict[str, object], str], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
    emit_approach: Callable[[List[str], float, float, Dict[str, object] | None], None],
    clean_path: Callable[[List[Tuple[float, float]]], List[Tuple[float, float]]],
) -> List[str]:
    settings = settings or {}
    p = op.params
    validate_finite_data(p, "Planen")
    lines: List[str] = []

    def req_float(key: str) -> float:
        if key not in p:
            raise ValueError(f"Missing parameter: '{key}'")
        v = p.get(key)
        if v is None or v == "":
            raise ValueError(f"Empty parameter: '{key}'")
        try:
            return finite_float(v, key)
        except Exception:
            raise ValueError(f"Invalid float for '{key}': {v!r}")

    def req_int(key: str) -> int:
        return int(req_float(key))

    def opt_bool(key: str) -> bool:
        return bool(p.get(key, False))

    if "mode" not in p:
        raise ValueError("Missing parameter: 'mode'")
    mode = resolve_enum_index(p.get("mode"), FACE_MODE_INDEX, default=0)
    start_x = req_float("start_x")
    start_z = req_float("start_z")
    end_x = req_float("end_x")
    end_z = req_float("end_z")

    finish_allow_z = req_float("finish_allow_z")
    depth_per_pass = req_float("depth_max")
    retract = req_float("retract")
    feed = req_float("feed")
    spindle = req_float("spindle")
    tool_num = require_tool(p, "FACE")

    if "edge_type" not in p:
        raise ValueError("Missing parameter: 'edge_type'")
    edge_type = resolve_enum_index(p.get("edge_type"), FACE_EDGE_TYPE_INDEX, default=-1)
    edge_size = req_float("edge_size")
    if edge_size < 0.0:
        raise ValueError("edge_size must be >= 0")

    coolant_enabled = opt_bool("coolant")
    pause_enabled = opt_bool("pause_enabled")
    pause_distance = finite_float(p.get("pause_distance", 0.0), "pause_distance")

    if depth_per_pass <= 0.0:
        raise ValueError("depth_max must be > 0")
    if float(f"{depth_per_pass:.3f}") <= 0.0:
        raise ValueError("depth_max muss auch nach Ausgaberundung > 0 sein")
    if retract < 0.0:
        raise ValueError("retract must be >= 0")
    if finish_allow_z < 0.0:
        raise ValueError("finish_allow_z must be >= 0")
    if feed <= 0.0 or float(f"{feed:.3f}") <= 0.0:
        raise ValueError("feed muss auch nach Ausgaberundung > 0 sein")
    if spindle < 0.0:
        raise ValueError("spindle must be >= 0")
    if pause_distance < 0.0:
        raise ValueError("pause_distance must be >= 0")

    append_tool_and_spindle(
        lines, tool_num, spindle, settings,
        spindle_mode=p.get("spindle_mode"), spindle_max_rpm=p.get("spindle_max_rpm"),
        cutting_speed=p.get("cutting_speed"), css_start_diameter=abs(start_x),
    )
    coolant_mode = p.get("coolant_mode", coolant_enabled)
    emit_coolant(lines, coolant_mode)
    lines.append(f"F{feed:.3f}")

    profile = face_primitives(start_x, end_x, end_z, edge_type, edge_size)

    allocator = settings.get("sub_allocator")
    if allocator:
        sub_num = allocator.allocate()
    else:
        sub_num = 100
    lines.extend(contour_sub_from_primitives(profile, sub_num))

    lines.append("(Anfahren vor Zyklus)")
    emit_approach(lines, start_x, start_z, settings)
    activate_pending_css(lines, settings)
    if mode in (0, 2):
        lines.append(
            f"G72 Q{sub_num} X{start_x:.3f} Z{start_z:.3f} D{finish_allow_z:.3f} "
            f"I{depth_per_pass:.3f} R{retract:.3f}"
        )
    if mode in (1, 2):
        lines.append(f"G70 Q{sub_num} X{start_x:.3f} Z{start_z:.3f}")

    # LES-022 (dritte Etappe): G70 endet nachweislich (rs274-Verifikation,
    # siehe gcode_roughing.py) immer exakt am letzten Punkt der referenzierten
    # Kontur - hier (end_x, end_z), das Ende von `profile`. Ohne folgendes
    # G70 (reines Schruppen, mode 0) bleibt die Endposition des G72-Zyklus
    # unbekannt (siehe gcode_roughing.py can_use_cycles-Kommentar) - dort
    # explizit ungueltig markieren statt die Anfahrposition stehen zu lassen.
    if settings is not None:
        if mode in (1, 2):
            _motion_state(settings).record(end_x, end_z)
        else:
            _motion_state(settings).clear()

    if mode in (0, 2) and pause_enabled and pause_distance > 0.0:
        settings["needs_step_x_pause_sub"] = True
    return lines
