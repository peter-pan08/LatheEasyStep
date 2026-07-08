from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .model import Operation


THREAD_ORIENTATION_LABELS: Tuple[str, str] = ("Aussen", "Innen")


def generate_thread_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require_tool: Callable[[Dict[str, object], str], int],
    get_tool_number: Callable[[Dict[str, object]], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
    emit_approach: Callable[[List[str], float, float, Dict[str, object] | None], None],
    sanitize_comment_text: Callable[[object], str],
) -> List[str]:
    settings = settings or {}
    require_tool(op.params, "THREAD")
    safe_z = float(op.params.get("safe_z", 2.0))
    major_diameter = float(op.params.get("major_diameter", 0.0))
    pitch = float(op.params.get("pitch", 1.5))
    pitch_warning: str | None = None
    if pitch <= 0.0:
        pitch_warning = "(WARN: Ungueltige Steigung; P=1.0 fallback)"
        pitch = 1.0
    length = float(op.params.get("length", 0.0))

    raw_thread_depth = op.params.get("thread_depth")
    if isinstance(raw_thread_depth, (int, float)) and raw_thread_depth > 0:
        thread_depth = float(raw_thread_depth)
    else:
        thread_depth = pitch * 0.6134

    raw_first_depth = op.params.get("first_depth")
    if isinstance(raw_first_depth, (int, float)) and raw_first_depth > 0:
        first_depth = float(raw_first_depth)
    else:
        first_depth = max(thread_depth * 0.1, pitch * 0.05)

    raw_peak_offset = op.params.get("peak_offset")
    if isinstance(raw_peak_offset, (int, float)) and raw_peak_offset != 0:
        peak_offset = float(raw_peak_offset)
    else:
        peak_offset = -max(thread_depth * 0.5, pitch * 0.25)

    retract_r = float(op.params.get("retract_r", 1.5))
    infeed_q = float(op.params.get("infeed_q", 29.5))
    spring_passes_raw = op.params.get("spring_passes")
    if isinstance(spring_passes_raw, (int, float)) and spring_passes_raw > 0:
        spring_passes = max(0, int(spring_passes_raw))
    else:
        spring_passes = max(0, int(op.params.get("passes", 1)))
    e_val = float(op.params.get("e", 0.0))
    l_val = int(float(op.params.get("l", 0)))

    orientation_raw = op.params.get("orientation", 0)
    orientation_idx = 0
    if isinstance(orientation_raw, (int, float)):
        orientation_idx = max(0, min(int(orientation_raw), len(THREAD_ORIENTATION_LABELS) - 1))
    internal = orientation_idx == 1
    orientation_label = THREAD_ORIENTATION_LABELS[orientation_idx]
    standard_data = op.params.get("standard")
    standard_label = ""
    if isinstance(standard_data, dict):
        std_label_tmp = standard_data.get("label")
        if isinstance(std_label_tmp, str):
            standard_label = std_label_tmp

    if internal:
        peak_offset = abs(peak_offset)
        approach_x = major_diameter - 2.0 * thread_depth
    else:
        peak_offset = -abs(peak_offset)
        approach_x = major_diameter

    comments: List[str] = []
    if standard_label and standard_label != "Benutzerdefiniert":
        comments.append(f"(Normgewinde: {sanitize_comment_text(standard_label)})")
    comments.append(f"(Gewindetyp: {orientation_label})")
    if pitch_warning:
        comments.append(pitch_warning)

    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    lines.extend(comments)

    lines.append("(Anfahren vor Gewinde)")
    emit_approach(lines, approach_x, safe_z, settings)
    lines.append(
        (
            "G76 "
            f"P{pitch:.4f} "
            f"Z{-abs(length):.3f} "
            f"I{peak_offset:.4f} "
            f"J{first_depth:.4f} "
            f"R{retract_r:.4f} "
            f"K{thread_depth:.4f} "
            f"Q{infeed_q:.4f} "
            f"H{spring_passes:d} "
            f"E{e_val:.4f} "
            f"L{l_val:d}"
        )
    )
    return lines
