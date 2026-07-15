from __future__ import annotations

from typing import Callable, Dict, List

from .gcode_safety import get_approach_warnings, get_safe_position
from .gcode_utils import sanitize_comment_text
from .model import Operation


# Mapping: combo index (float from _collect_params) -> G-code mode string
DRILL_MODE_MAP: Dict[int, str] = {
    0: "G81",  # Normal drilling
    1: "G82",  # Drilling with dwell
    2: "G83",  # Peck drilling (full retract)
    3: "G73",  # Chip breaking drilling (partial retract)
    4: "G84",  # Tapping
}


def generate_drill_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require: Callable[[Dict[str, object], List[str], str], None],
    require_tool: Callable[[Dict[str, object], str], int],
    get_tool_number: Callable[[Dict[str, object]], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
    emit_approach: Callable[[List[str], float, float, Dict[str, object] | None], None],
) -> List[str]:
    def emit_drill_approach(lines: List[str], start_x: float, start_z: float) -> None:
        for warning in get_approach_warnings(settings, (start_x, start_z)):
            lines.append(f"(WARN: {sanitize_comment_text(warning)})")
        safe = get_safe_position(settings)
        if safe and settings is not None:
            x_safe, z_safe = safe
            eps = 1e-9
            if not settings.get("_is_at_safe"):
                lines.append(f"G0 Z{z_safe:.3f}")
                lines.append(f"G0 X{x_safe:.3f}")
            if abs(start_z - z_safe) > eps:
                lines.append(f"G0 Z{start_z:.3f}")
            lines.append(f"G0 X{start_x:.3f}")
            settings["_is_at_safe"] = False
            return
        emit_approach(lines, start_x, start_z, settings)

    settings = settings or {}
    path = op.path or []
    if not path:
        return []
    p = op.params
    require_tool(p, "DRILL")

    mode_raw_value = p.get("mode", "G81")
    if isinstance(mode_raw_value, str) and mode_raw_value.strip().upper() in DRILL_MODE_MAP.values():
        # ID-only-Combo liefert die G-Code-ID direkt (z. B. 'g83'), unabhaengig von Gross-/Kleinschreibung.
        mode = mode_raw_value.strip().upper()
    else:
        try:
            mode_idx = int(float(mode_raw_value))
            mode = DRILL_MODE_MAP.get(mode_idx, "G81")
        except (TypeError, ValueError):
            mode = "G81"

    if mode == "G82":
        require(p, ["dwell"], "DRILL G82")
    elif mode in ["G83", "G73"]:
        require(p, ["peck_depth"], "DRILL " + mode)

    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
        spindle_mode=op.params.get("spindle_mode"),
        spindle_max_rpm=op.params.get("spindle_max_rpm"),
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    safe_z = float(op.params.get("safe_z", 2.0))
    feed = float(op.params.get("feed", 0.12))
    depth_z = path[-1][1]
    x_start = path[0][0]
    retract = float(op.params.get("retract", safe_z))
    if retract < safe_z:
        lines.append(f"(WARN: retract ({retract:.3f}) < safe_z ({safe_z:.3f}); verwende safe_z)")
        retract = safe_z

    lines.append("(Anfahren vor Zyklus)")
    emit_drill_approach(lines, x_start, safe_z)
    lines.append("(G17 nur fuer Bohrzyklus - LinuxCNC Besonderheit)")
    lines.append("G17")
    lines.append(f"F{feed:.3f}")
    if mode == "G81":
        lines.append(f"G81 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    elif mode == "G82":
        dwell = float(p.get("dwell", 0.0))
        lines.append(f"G82 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} P{dwell:.3f} F{feed:.3f}")
    elif mode == "G83":
        peck_depth = float(p.get("peck_depth", 1.0))
        lines.append(f"G83 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} Q{peck_depth:.3f} F{feed:.3f}")
    elif mode == "G73":
        peck_depth = float(p.get("peck_depth", 1.0))
        lines.append(f"G73 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} Q{peck_depth:.3f} F{feed:.3f}")
    elif mode == "G84":
        lines.append(f"G84 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    else:
        lines.append(f"G81 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    lines.append("G80")
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append("G18")
    return lines
