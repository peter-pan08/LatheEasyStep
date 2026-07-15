from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .gcode_utils import float_or_none, get_tool_number, sanitize_comment_text
from .model import OpType, Operation


def _safe_axis_value(
    settings: Dict[str, object] | None,
    *,
    axis: str,
    internal: bool,
) -> Optional[float]:
    if not settings:
        return None
    base_key = f"{axis}{'ri' if internal else 'ra'}"
    base_value = float_or_none(settings.get(base_key))
    if base_value is None:
        return None
    absolute = bool(settings.get(f"{base_key}_absolute", False))
    if absolute:
        return base_value
    # X: "innen" heisst radial zur Bohrungswand hin (xi = vorhandener Innen-
    # durchmesser), das kehrt sich zwischen aussen/innen tatsaechlich um.
    # Z: die Werkzeugfreifahrt erfolgt bei Innen- UND Aussenbearbeitung immer
    # zur vorderen, zugaenglichen Seite (za = "Vorderes Anfangsmass"), niemals
    # zum hinteren Ende (zi = "Hinteres Endmass"), das beim Innenbohren naeher
    # am Futter liegt und keine sichere Rueckzugsrichtung ist. zi + zri wuerde
    # hier eine Rueckzugsebene mitten im bzw. jenseits des Rohteils erzeugen
    # (siehe get_approach_warnings: "Rueckzugsebene schneidet den Futterbereich").
    stock_key = "xi" if internal and axis == "x" else "xa" if axis == "x" else "za"
    stock_value = float_or_none(settings.get(stock_key))
    if stock_value is None:
        return None
    return stock_value + base_value


def get_safe_position(settings: Dict[str, object] | None) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    internal = str(settings.get("_active_retract_mode", "") or "").strip().lower() == "internal"
    x_safe = _safe_axis_value(settings, axis="x", internal=internal)
    z_safe = _safe_axis_value(settings, axis="z", internal=internal)
    if x_safe is None or z_safe is None:
        if internal:
            x_safe = _safe_axis_value(settings, axis="x", internal=False)
            z_safe = _safe_axis_value(settings, axis="z", internal=False)
        if x_safe is None or z_safe is None:
            return None
    return (x_safe, z_safe)


def get_safe_position_for_mode(
    settings: Dict[str, object] | None,
    *,
    internal: bool,
) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    saved = settings.get("_active_retract_mode")
    try:
        settings["_active_retract_mode"] = "internal" if internal else "external"
        return get_safe_position(settings)
    finally:
        if saved is None:
            settings.pop("_active_retract_mode", None)
        else:
            settings["_active_retract_mode"] = saved


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
    for warning in get_approach_warnings(settings, (start_x, start_z)):
        lines.append(f"(WARN: {sanitize_comment_text(warning)})")
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


def append_tool_and_spindle(
    lines: List[str],
    tool_value: object | None,
    spindle_value: object | None,
    settings: Dict[str, object] | None = None,
    *,
    spindle_mode: object | None = None,
    spindle_max_rpm: object | None = None,
):
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
                safe = get_safe_position_for_mode(settings, internal=False)
                if safe:
                    x_safe, z_safe = safe
                    lines.append(f"G0 Z{z_safe:.3f}")
                    lines.append(f"G0 X{x_safe:.3f}")
                    settings["_is_at_safe"] = True
                if last_tool > 0 and bool(settings.get("optional_stop_toolchange", False)):
                    lines.append("M1")
                lines.append("M5")
                lines.append("M9")
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
            # Op-spezifischer Drehzahlmodus hat Vorrang; ohne Angabe gilt weiterhin
            # der globale Programmkopf-Wert (Rueckwaertskompatibilitaet).
            if spindle_mode is not None:
                effective_mode = str(spindle_mode or "fixed").strip().lower()
            else:
                effective_mode = str((settings or {}).get("spindle_mode", "fixed") or "fixed").strip().lower()
            if spindle_max_rpm is not None:
                max_rpm = float_or_none(spindle_max_rpm)
            else:
                max_rpm = float_or_none((settings or {}).get("spindle_max_rpm"))
            if effective_mode in ("css", "g96"):
                if max_rpm and max_rpm > 0:
                    lines.append(f"G96 D{int(round(max_rpm))} S{rpm_value} M3")
                else:
                    lines.append("(WARN: CSS angefordert, aber spindle_max_rpm fehlt - nutze G97)")
                    lines.append(f"G97 S{rpm_value} M3")
            else:
                lines.append(f"G97 S{rpm_value} M3")


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


def _coord_mode(settings: Dict[str, object] | None, primary_key: str, *, legacy_x_key: str | None = None, legacy_z_key: str | None = None, default: str = "work") -> str:
    if settings is None:
        return default
    mode = str(settings.get(primary_key, "") or "").strip().lower()
    if mode in ("machine", "g53"):
        return "machine"
    if mode in ("work", "wcs", "g54"):
        return "work"
    if legacy_x_key and legacy_z_key:
        x_abs = bool(settings.get(legacy_x_key, True))
        z_abs = bool(settings.get(legacy_z_key, True))
        if x_abs != z_abs:
            return "mixed"
        return "work" if x_abs and z_abs else "machine"
    return default


def move_to_toolchange_pos(settings: Dict[str, object], label: str | None = None) -> List[str]:
    xt = float_or_none(settings.get("xt"))
    zt = float_or_none(settings.get("zt"))
    prefix = f"({label})" if label else "(Toolchange move)"
    lines: List[str] = [prefix]
    if xt is None or zt is None:
        lines.append("(WARN: Toolchange position XT/ ZT nicht gesetzt)")
        return lines
    mode = _coord_mode(settings, "toolchange_coords", legacy_x_key="xt_absolute", legacy_z_key="zt_absolute")
    if mode == "machine":
        lines.append(f"G53 G0 X{xt:.3f} Z{zt:.3f}")
    elif mode == "mixed":
        if not bool(settings.get("xt_absolute", True)):
            lines.append(f"G53 G0 X{xt:.3f}")
        if not bool(settings.get("zt_absolute", True)):
            lines.append(f"G53 G0 Z{zt:.3f}")
        if bool(settings.get("xt_absolute", True)) and bool(settings.get("zt_absolute", True)):
            lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
        else:
            work_parts = []
            if bool(settings.get("xt_absolute", True)):
                work_parts.append(f"X{xt:.3f}")
            if bool(settings.get("zt_absolute", True)):
                work_parts.append(f"Z{zt:.3f}")
            if work_parts:
                lines.append(f"G0 {' '.join(work_parts)}")
    else:
        lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
    return lines


def get_approach_warnings(settings: Dict[str, object] | None, start_pos: Tuple[float, float] | None) -> List[str]:
    warnings: List[str] = []
    if settings is None or start_pos is None:
        return warnings
    x, z = start_pos
    xa = float_or_none(settings.get("xa"))
    xi = float_or_none(settings.get("xi"))
    za = float_or_none(settings.get("za"))
    zi = float_or_none(settings.get("zi"))
    if xa is not None and za is not None and zi is not None:
        x_min = min(xi if xi is not None else 0.0, xa)
        x_max = max(xi if xi is not None else 0.0, xa)
        z_min = min(zi, za)
        z_max = max(zi, za)
        if x_min - 1e-6 <= x <= x_max + 1e-6 and z_min - 1e-6 <= z <= z_max + 1e-6:
            warnings.append(f"Startpunkt X{x:.3f} Z{z:.3f} liegt im Rohteil")
    x_min = float_or_none(settings.get("chuck_no_go_x_min"))
    x_max = float_or_none(settings.get("chuck_no_go_x_max"))
    z_lim = float_or_none(settings.get("chuck_no_go_z_limit"))
    if x_min is not None and x_max is not None and z_lim is not None:
        if min(x_min, x_max) - 1e-6 <= x <= max(x_min, x_max) + 1e-6:
            if z <= z_lim + 1e-6:
                warnings.append(f"Startpunkt X{x:.3f} Z{z:.3f} liegt in der Futter-Sperrzone")
        safe = get_safe_position(settings)
        if safe is not None:
            _, safe_z = safe
            if safe_z <= z_lim + 1e-6:
                warnings.append(f"Rueckzugsebene Z{safe_z:.3f} schneidet den Futterbereich")
    return warnings


def get_machine_limit_warnings(settings: Dict[str, object] | None) -> List[str]:
    if settings is None:
        return []
    warnings: List[str] = []
    xa = float_or_none(settings.get("xa"))
    xi = float_or_none(settings.get("xi"))
    za = float_or_none(settings.get("za"))
    zi = float_or_none(settings.get("zi"))
    bounds = {
        "xt": float_or_none(settings.get("xt")),
        "zt": float_or_none(settings.get("zt")),
        "xra": float_or_none(settings.get("xra")),
        "xri": float_or_none(settings.get("xri")),
        "zra": float_or_none(settings.get("zra")),
        "zri": float_or_none(settings.get("zri")),
    }
    if xa is not None and xi is not None:
        span = max(abs(xa - xi), 1.0)
        low = min(xi, xa) - span * 2.0
        high = max(xi, xa) + span * 10.0 + 50.0
        for key in ("xt", "xra", "xri"):
            val = bounds.get(key)
            if val is not None and not (low <= val <= high):
                warnings.append(f"{key.upper()}={val:.3f} liegt ausserhalb plausibler X-Grenzen")
    if za is not None and zi is not None:
        span = max(abs(za - zi), 1.0)
        low = min(zi, za) - span * 10.0 - 50.0
        high = max(zi, za) + span * 10.0 + 50.0
        for key in ("zt", "zra", "zri"):
            val = bounds.get(key)
            if val is not None and not (low <= val <= high):
                warnings.append(f"{key.upper()}={val:.3f} liegt ausserhalb plausibler Z-Grenzen")
    return warnings


def get_end_park_lines(settings: Dict[str, object] | None) -> List[str]:
    if settings is None:
        return []
    park_mode = str(settings.get("park_mode", "toolchange") or "toolchange").strip().lower()
    sequential = bool(settings.get("park_sequential", False))
    if park_mode in ("end_position", "park", "custom"):
        x_park = float_or_none(settings.get("park_x"))
        z_park = float_or_none(settings.get("park_z"))
        label = "(Parkposition am Ende)"
        if x_park is None or z_park is None:
            return [label, "(WARN: Parkposition aktiv, aber park_x/park_z fehlen)"]
        park_machine = _coord_mode(settings, "park_coords", default="work") == "machine"
        if sequential:
            return [label, f"{'G53 G0' if park_machine else 'G0'} X{x_park:.3f}", f"{'G53 G0' if park_machine else 'G0'} Z{z_park:.3f}"]
        return [label, f"{'G53 G0' if park_machine else 'G0'} X{x_park:.3f} Z{z_park:.3f}"]
    xt_end = float_or_none(settings.get("xt"))
    zt_end = float_or_none(settings.get("zt"))
    if xt_end is None or zt_end is None:
        return []
    mode = _coord_mode(settings, "toolchange_coords", legacy_x_key="xt_absolute", legacy_z_key="zt_absolute")
    if mode == "machine":
        return ["(Werkzeugwechselpunkt am Ende)", f"G53 G0 X{xt_end:.3f} Z{zt_end:.3f}"]
    if mode == "mixed":
        lines = ["(Werkzeugwechselpunkt am Ende)"]
        if not bool(settings.get("xt_absolute", True)):
            lines.append(f"G53 G0 X{xt_end:.3f}")
        if not bool(settings.get("zt_absolute", True)):
            lines.append(f"G53 G0 Z{zt_end:.3f}")
        work_parts = []
        if bool(settings.get("xt_absolute", True)):
            work_parts.append(f"X{xt_end:.3f}")
        if bool(settings.get("zt_absolute", True)):
            work_parts.append(f"Z{zt_end:.3f}")
        if work_parts:
            lines.append(f"G0 {' '.join(work_parts)}")
        return lines
    return ["(Werkzeugwechselpunkt am Ende)", f"G0 X{xt_end:.3f} Z{zt_end:.3f}"]


__all__ = [
    "append_tool_and_spindle",
    "emit_approach",
    "emit_safe_retract",
    "emit_safe_retract_for_op",
    "estimate_operation_end_pos",
    "get_safe_position",
    "get_safe_position_for_mode",
    "get_approach_warnings",
    "get_end_park_lines",
    "get_machine_limit_warnings",
    "move_to_toolchange_pos",
    "nose_compensation_command",
]
