from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .model import Operation


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
    lines: List[str] = []

    def req_float(key: str) -> float:
        if key not in p:
            raise ValueError(f"Missing parameter: '{key}'")
        v = p.get(key)
        if v is None or v == "":
            raise ValueError(f"Empty parameter: '{key}'")
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Invalid float for '{key}': {v!r}")

    def req_int(key: str) -> int:
        return int(req_float(key))

    def opt_bool(key: str) -> bool:
        return bool(p.get(key, False))

    mode = req_int("mode")
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

    edge_type = req_int("edge_type")
    edge_size = req_float("edge_size")

    coolant_enabled = opt_bool("coolant")
    pause_enabled = opt_bool("pause_enabled")
    pause_distance = max(float(p.get("pause_distance", 0.0)), 0.0)

    if depth_per_pass <= 0.0:
        raise ValueError("depth_max must be > 0")
    if retract < 0.0:
        raise ValueError("retract must be >= 0")
    if finish_allow_z < 0.0:
        raise ValueError("finish_allow_z must be >= 0")
    if feed <= 0.0:
        raise ValueError("feed must be > 0")
    if spindle < 0.0:
        raise ValueError("spindle must be >= 0")

    append_tool_and_spindle(lines, tool_num, spindle, settings)
    coolant_mode = p.get("coolant_mode", coolant_enabled)
    emit_coolant(lines, coolant_mode)
    lines.append(f"F{feed:.3f}")

    contour: List[Tuple[float, float]] = []
    if edge_type == 1:
        if edge_size <= 0.0:
            raise ValueError("edge_size must be > 0 when edge_type==1")
        contour.append((start_x, end_z - edge_size))
        contour.append((start_x - 2.0 * edge_size, end_z))
    else:
        contour.append((start_x, end_z))

    contour.append((end_x, end_z))
    cleaned = clean_path(contour)

    allocator = settings.get("sub_allocator")
    if allocator:
        sub_num = allocator.allocate()
    else:
        sub_num = 100
    lines.append(f"o{sub_num} sub")
    for x, z in cleaned:
        lines.append(f"G1 X{x:.3f} Z{z:.3f}")
    lines.append(f"o{sub_num} endsub")

    lines.append("(Anfahren vor Zyklus)")
    emit_approach(lines, start_x, start_z, settings)
    if mode in (0, 2):
        lines.append(
            f"G72 Q{sub_num} X{start_x:.3f} Z{start_z:.3f} D{finish_allow_z:.3f} "
            f"I{depth_per_pass:.3f} R{retract:.3f}"
        )
    if mode in (1, 2):
        lines.append(f"G70 Q{sub_num} X{start_x:.3f} Z{start_z:.3f}")

    if mode in (0, 2) and pause_enabled and pause_distance > 0.0:
        settings["needs_step_x_pause_sub"] = True
    return lines
