from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .gcode_utils import float_or_none, get_tool_number
from .model import OpType, Operation


def get_safe_position(settings: Dict[str, object] | None) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    xra = float_or_none(settings.get("xra"))
    zra = float_or_none(settings.get("zra"))
    if xra is None or zra is None:
        return None
    xra_absolute = bool(settings.get("xra_absolute", False))
    zra_absolute = bool(settings.get("zra_absolute", False))
    if xra_absolute:
        x_safe = xra
    else:
        xa = float_or_none(settings.get("xa"))
        if xa is None:
            return None
        x_safe = xa + xra
    if zra_absolute:
        z_safe = zra
    else:
        za = float_or_none(settings.get("za"))
        if za is None:
            return None
        z_safe = za + zra
    return (x_safe, z_safe)


def emit_safe_retract(lines: List[str], settings: Dict[str, object] | None) -> None:
    emit_safe_retract_for_op(lines, settings, None)


def emit_safe_retract_for_op(
    lines: List[str],
    settings: Dict[str, object] | None,
    op_type: Optional[str],
    current_pos: Optional[Tuple[float, float]] = None,
) -> None:
    safe = get_safe_position(settings)
    if not safe:
        return
    x_safe, z_safe = safe

    def _inside_stock_envelope(pos: Optional[Tuple[float, float]]) -> bool:
        if pos is None or settings is None:
            return False
        xa = float_or_none(settings.get("xa"))
        za = float_or_none(settings.get("za"))
        zi = float_or_none(settings.get("zi"))
        if xa is None or za is None or zi is None:
            return False
        xi = float_or_none(settings.get("xi"))
        if xi is None:
            xi = 0.0
        x, z = pos
        x_min = min(xi, xa)
        x_max = max(xi, xa)
        z_min = min(zi, za)
        z_max = max(zi, za)
        eps = 1e-6
        return (x_min - eps) <= x <= (x_max + eps) and (z_min - eps) <= z <= (z_max + eps)

    def _inside_chuck_nogo(pos: Optional[Tuple[float, float]]) -> bool:
        if pos is None or settings is None:
            return False
        x_min = float_or_none(settings.get("chuck_no_go_x_min"))
        x_max = float_or_none(settings.get("chuck_no_go_x_max"))
        z_lim = float_or_none(settings.get("chuck_no_go_z_limit"))
        if x_min is None or x_max is None or z_lim is None:
            return False
        x, z = pos
        lo = min(x_min, x_max)
        hi = max(x_min, x_max)
        eps = 1e-6
        if x < lo - eps or x > hi + eps:
            return False
        za = float_or_none(settings.get("za"))
        if za is None:
            return z <= z_lim + eps
        if z_lim <= za:
            return z <= z_lim + eps
        return z >= z_lim - eps

    inside_stock = _inside_stock_envelope(current_pos)
    inside_chuck_nogo = _inside_chuck_nogo(current_pos)

    if op_type in (OpType.GROOVE, OpType.KEYWAY):
        lines.append(f"G0 X{x_safe:.3f}")
        lines.append(f"G0 Z{z_safe:.3f}")
    elif op_type in (OpType.DRILL, OpType.THREAD):
        lines.append(f"G0 Z{z_safe:.3f}")
        lines.append(f"G0 X{x_safe:.3f}")
    elif inside_stock or inside_chuck_nogo:
        lines.append(f"G0 X{x_safe:.3f}")
        lines.append(f"G0 Z{z_safe:.3f}")
    else:
        lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")
    if settings is not None:
        settings["_is_at_safe"] = True


def estimate_operation_end_pos(op: Operation) -> Optional[Tuple[float, float]]:
    path = op.path or []
    if path:
        last = path[-1]
        if isinstance(last, (tuple, list)) and len(last) >= 2:
            try:
                return (float(last[0]), float(last[1]))
            except Exception:
                pass
    p = op.params or {}
    if op.op_type in (OpType.GROOVE, OpType.KEYWAY):
        a_end = float_or_none(p.get("A_end"))
        mode = int(float_or_none(p.get("mode")) or 0)
        c_val = float_or_none(p.get("C"))
        if a_end is not None and c_val is not None:
            return (a_end, c_val) if mode == 0 else (c_val, a_end)
    if op.op_type == OpType.FACE:
        x = float_or_none(p.get("end_x"))
        z = float_or_none(p.get("end_z"))
        if x is not None and z is not None:
            return (x, z)
    return None


def emit_approach(lines: List[str], start_x: float, start_z: float, settings: Dict[str, object] | None) -> None:
    safe = get_safe_position(settings)
    if safe and settings is not None:
        x_safe, z_safe = safe
        if settings.get("_is_at_safe"):
            lines.append(f"G0 X{start_x:.3f} Z{start_z:.3f}")
        else:
            lines.append(f"G0 Z{z_safe:.3f}")
            lines.append(f"G0 X{x_safe:.3f}")
            lines.append(f"G0 X{start_x:.3f} Z{start_z:.3f}")
        settings["_is_at_safe"] = False
        return
    lines.append(f"G0 Z{start_z:.3f}")
    lines.append(f"G0 X{start_x:.3f}")


def append_tool_and_spindle(lines: List[str], tool_value: object | None, spindle_value: object | None, settings: Dict[str, object] | None = None):
    if tool_value is None and settings is not None:
        tool_num = get_tool_number(settings)
    else:
        try:
            tool_num = int(float(tool_value))
        except Exception:
            tool_num = 0

    if tool_num > 0:
        last_tool = int(float(settings.get("_current_tool", 0))) if settings else 0
        if tool_num != last_tool:
            lines.append(f"(Werkzeug T{tool_num:02d})")
            if settings is not None:
                skip_tool_move = bool(settings.pop("_skip_tool_move", False))
                safe = get_safe_position(settings)
                if safe and not settings.get("_is_at_safe"):
                    x_safe, z_safe = safe
                    lines.append(f"G0 Z{z_safe:.3f}")
                    lines.append(f"G0 X{x_safe:.3f}")
                    settings["_is_at_safe"] = True
                lines.append("M9")
                if not skip_tool_move:
                    lines.extend(move_to_toolchange_pos(settings))
            lines.append(f"T{tool_num:02d} M6")
            if settings is not None:
                settings["_current_tool"] = tool_num
                safe = get_safe_position(settings)
                if safe:
                    x_safe, z_safe = safe
                    lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")
                    settings["_is_at_safe"] = True
    rpm = float_or_none(spindle_value)
    if rpm and rpm > 0:
        rpm_value = int(round(rpm))
        if rpm_value > 0:
            lines.append(f"S{rpm_value} M3")


def nose_compensation_command(tool_info: Dict[str, object] | None, external: bool) -> Optional[str]:
    if not tool_info:
        return None
    radius = float_or_none(tool_info.get("radius_mm"))
    if radius is None or radius <= 0:
        return None
    orientation_raw = tool_info.get("q")
    if orientation_raw is None:
        return None
    try:
        orientation_idx = int(float(orientation_raw))
    except Exception:
        return None
    comp_code = "G42.1" if external else "G41.1"
    return f"{comp_code} D{(radius * 2):.4f} L{orientation_idx}"


def move_to_toolchange_pos(settings: Dict[str, object], label: str | None = None) -> List[str]:
    xt = float_or_none(settings.get("xt"))
    zt = float_or_none(settings.get("zt"))
    prefix = f"({label})" if label else "(Toolchange move)"
    lines: List[str] = [prefix]
    if xt is None or zt is None:
        lines.append("(WARN: Toolchange position XT/ ZT nicht gesetzt)")
        return lines
    lines.append(f"G53 G0 X{xt:.3f} Z{zt:.3f}")
    return lines


__all__ = [
    "append_tool_and_spindle",
    "emit_approach",
    "emit_safe_retract",
    "emit_safe_retract_for_op",
    "estimate_operation_end_pos",
    "get_safe_position",
    "move_to_toolchange_pos",
    "nose_compensation_command",
]
