from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .presets import get_din_relief_preset
from .model import Operation
from .gcode_utils import float_or_none


THREAD_ORIENTATION_LABELS: Tuple[str, str] = ("Aussen", "Innen")
THREAD_HAND_LABELS: Tuple[str, str] = ("Rechtsgewinde", "Linksgewinde")
THREAD_RELIEF_SIZE_BY_MAJOR = {
    3.0: "M3",
    4.0: "M4",
    5.0: "M5",
    6.0: "M6",
    8.0: "M8",
    10.0: "M10",
    12.0: "M12",
    14.0: "M14",
    16.0: "M16",
}


def _resolve_internal_safe_x(settings: Dict[str, object]) -> float | None:
    xri = float_or_none(settings.get("xri"))
    if xri is None:
        return None
    if bool(settings.get("xri_absolute", False)):
        return xri
    xi = float_or_none(settings.get("xi"))
    if xi is None:
        return None
    return xi + xri


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
    start_z = float(op.params.get("thread_start_z", 0.0) or 0.0)
    hand_raw = op.params.get("hand", 0)
    hand_idx = 0
    if isinstance(hand_raw, (int, float)):
        hand_idx = max(0, min(int(hand_raw), len(THREAD_HAND_LABELS) - 1))
    hand_label = THREAD_HAND_LABELS[hand_idx]
    z_dir = -1.0 if hand_idx == 0 else 1.0
    end_z = start_z + (z_dir * abs(length))

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
        peak_offset = abs(float(raw_peak_offset))
    else:
        peak_offset = max(first_depth, pitch * 0.05)

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

    minor_diameter = major_diameter - 2.0 * thread_depth
    full_thread_depth = abs(major_diameter - minor_diameter)
    first_cut_depth = max(first_depth * 2.0, 0.0001)

    if internal:
        peak_offset = abs(peak_offset)
        approach_x = minor_diameter - peak_offset
        safe_x = _resolve_internal_safe_x(settings)
        if safe_x is None or safe_x <= 0.0:
            raise ValueError("Innengewinde erfordert ein gueltiges XRI im Programmkopf.")
        if safe_x >= minor_diameter - 1e-9:
            raise ValueError(
                f"XRI={safe_x:.3f} ist fuer Innengewinde unplausibel. "
                f"XRI muss kleiner als der Kerndurchmesser ({minor_diameter:.3f}) sein."
            )
    else:
        peak_offset = -abs(peak_offset)
        approach_x = major_diameter - peak_offset

    comments: List[str] = []
    if standard_label and standard_label != "Benutzerdefiniert":
        comments.append(f"(Normgewinde: {sanitize_comment_text(standard_label)})")
    comments.append(f"(Gewindetyp: {orientation_label})")
    comments.append(f"(Gewinderichtung: {hand_label})")
    comments.append(f"(Gewindestart/-ende Z: {start_z:.3f} -> {end_z:.3f})")
    if pitch_warning:
        comments.append(pitch_warning)
    relief_mode = str(op.params.get("relief_mode", "off") or "off").strip().lower()
    relief_norm = str(op.params.get("relief_norm", "DIN 76-A") or "DIN 76-A").strip()
    if relief_mode == "suggest":
        relief_size = None
        for dia, size_name in THREAD_RELIEF_SIZE_BY_MAJOR.items():
            if abs(major_diameter - dia) <= 0.2:
                relief_size = size_name
                break
        if relief_size:
            side_key = "internal" if internal else "external"
            relief_data = get_din_relief_preset(relief_size, internal=(side_key == "internal")) or {}
            if relief_data:
                comments.append(
                    f"(Vorschlag Freistich: {relief_norm} {relief_size} {orientation_label} B={float(relief_data.get('width', 0.0)):.3f} T={float(relief_data.get('depth', 0.0)):.3f})"
                )
        else:
            comments.append("(Hinweis: Kein DIN-Freistich-Vorschlag fuer dieses Gewinde gefunden)")

    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    lines.extend(comments)

    if bool(op.params.get("optional_stop_before", False)):
        lines.append("M1")
    lines.append("(Anfahren vor Gewinde)")
    emit_approach(lines, approach_x, safe_z, settings)
    if abs(start_z - safe_z) > 1e-9:
        lines.append(f"G0 Z{start_z:.3f}")
    lines.append(
        (
            "G76 "
            f"P{pitch:.4f} "
            f"Z{end_z:.3f} "
            f"I{peak_offset:.4f} "
            f"J{first_cut_depth:.4f} "
            f"R{retract_r:.4f} "
            f"K{full_thread_depth:.4f} "
            f"Q{infeed_q:.4f} "
            f"H{spring_passes:d} "
            f"E{e_val:.4f} "
            f"L{l_val:d}"
        )
    )
    return lines
