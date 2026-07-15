from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .contour_features import normalize_relief_mode, primitive_to_points
from .contour_logic import build_contour_variants
from .gcode_safety import append_tool_and_spindle, emit_approach, get_safe_position, nose_compensation_command
from .gcode_utils import (
    Point,
    get_tool_number,
    is_internal_side,
    is_monotonic_x,
    is_monotonic_x_decreasing,
    is_monotonic_z_decreasing,
    require,
    require_positive,
    require_tool,
    resolve_enum_index,
    resolve_internal_safe_x,
    validate_internal_x_limit,
)

PARTING_MODE_INDEX = {"rough": 0, "finish": 1}


@dataclass(frozen=True)
class RetractCfg:
    x_value: Optional[float]
    z_value: Optional[float]
    x_absolute: bool
    z_absolute: bool


@dataclass
class Segment:
    x0: float
    z0: float
    x1: float
    z1: float


LEADOUT_LENGTH_DEFAULT = 2.0


def _normalize_output_preference(value: object | None) -> str:
    text = str(value or "").strip().lower()
    if text in ("cycle", "prefer_cycle", "standardzyklus", "1"):
        return "prefer_cycle"
    if text in ("explicit", "prefer_explicit", "ausgeschrieben", "2"):
        return "prefer_explicit"
    return "auto"


def _resolve_roughing_stock_x(
    settings: Dict[str, object],
    rough_path: List[Point],
    *,
    external: bool,
) -> float:
    contour_max_x = max(point[0] for point in rough_path)
    contour_min_x = min(point[0] for point in rough_path)
    stock_key = "xa" if external else "xi"
    fallback = contour_max_x
    try:
        stock_x = float(settings.get(stock_key))
    except Exception:
        return fallback
    if external:
        return max(stock_x, contour_max_x)
    if stock_x <= 0.0 or stock_x < contour_min_x - 1e-9:
        return contour_min_x
    return max(stock_x, contour_max_x)


def _finish_entry_point(
    finish_points: List[Point],
    safe_z: float,
    *,
    lead_length: float = LEADOUT_LENGTH_DEFAULT,
) -> Point:
    start_x, start_z = finish_points[0]
    if safe_z > start_z + 1e-9:
        return (start_x, safe_z)
    return (start_x, start_z + max(lead_length, 0.5))


def _emit_finish_primitives(lines: List[str], primitives: List[Dict[str, object]], *, feed: float) -> None:
    cur_x: Optional[float] = None
    cur_z: Optional[float] = None

    def _ensure_linear_at(x: float, z: float) -> None:
        nonlocal cur_x, cur_z
        if cur_x is None or cur_z is None or abs(cur_x - x) > 1e-9 or abs(cur_z - z) > 1e-9:
            lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            cur_x, cur_z = x, z

    for pr in primitives or []:
        typ = pr.get("type")
        if typ == "line":
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            if p1 is None or p2 is None:
                continue
            x1, z1 = float(p1[0]), float(p1[1])
            x2, z2 = float(p2[0]), float(p2[1])
            _ensure_linear_at(x1, z1)
            _ensure_linear_at(x2, z2)
        elif typ == "arc":
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            c = pr.get("c") or pr.get("center")
            if p1 is None or p2 is None or c is None:
                continue
            x1, z1 = float(p1[0]), float(p1[1])
            x2, z2 = float(p2[0]), float(p2[1])
            cx, cz = float(c[0]), float(c[1])
            _ensure_linear_at(x1, z1)
            i = cx - (cur_x if cur_x is not None else x1)
            k = cz - (cur_z if cur_z is not None else z1)
            g = "G3" if pr.get("ccw") else "G2"
            lines.append(f"{g} X{x2:.3f} Z{z2:.3f} I{i:.3f} K{k:.3f} F{feed:.3f}")
            cur_x, cur_z = x2, z2


def _emit_relief_pass(
    lines: List[str],
    feature_points: List[Point],
    feed: float,
    safe_z: float,
    settings: Dict[str, object],
    tool_num: int,
    spindle: float,
    op_params: Dict[str, object],
) -> None:
    if len(feature_points) < 2:
        return
    relief_tool = int(float(op_params.get("undercut_tool", tool_num) or tool_num))
    relief_spindle = float(op_params.get("undercut_spindle", spindle) or spindle)
    relief_feed = float(op_params.get("undercut_feed", feed) or feed)
    if bool(op_params.get("optional_stop_before_undercut", settings.get("optional_stop_before_undercut", False))):
        lines.append("M1")
    append_tool_and_spindle(
        lines, relief_tool, relief_spindle, settings,
        spindle_mode=op_params.get("spindle_mode"), spindle_max_rpm=op_params.get("spindle_max_rpm"),
    )
    lines.append("(Hinterschnitt separat)")
    emit_approach(lines, feature_points[0][0], safe_z, settings)
    for idx, (x, z) in enumerate(feature_points):
        code = "G1"
        if idx == 0:
            lines.append(f"{code} X{x:.3f} Z{z:.3f} F{relief_feed:.3f}")
        else:
            lines.append(f"{code} X{x:.3f} Z{z:.3f} F{relief_feed:.3f}")
    lines.append(f"G0 Z{safe_z:.3f}")


def segments_from_polyline(path: List[Point]) -> List[Segment]:
    segs: List[Segment] = []
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        if abs(x1 - x0) < 1e-12 and abs(z1 - z0) < 1e-12:
            continue
        segs.append(Segment(x0, z0, x1, z1))
    return segs


def intersect_segment_with_x_band(seg: Segment, x_lo: float, x_hi: float) -> Optional[Tuple[float, float]]:
    x0, z0, x1, z1 = seg.x0, seg.z0, seg.x1, seg.z1
    dx = x1 - x0
    if abs(dx) < 1e-12:
        if x_lo - 1e-12 <= x0 <= x_hi + 1e-12:
            return (min(z0, z1), max(z0, z1))
        return None
    t_lo = (x_lo - x0) / dx
    t_hi = (x_hi - x0) / dx
    t_enter = min(t_lo, t_hi)
    t_exit = max(t_lo, t_hi)
    a = max(0.0, t_enter)
    b = min(1.0, t_exit)
    if b <= a:
        return None

    def z_at(t: float) -> float:
        return z0 + (z1 - z0) * t

    za, zb = z_at(a), z_at(b)
    return (min(za, zb), max(za, zb))


def merge_intervals(intervals: List[Tuple[float, float]], gap: float = 1e-6) -> List[Tuple[float, float]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda it: it[0])
    merged: List[Tuple[float, float]] = []
    cur_a, cur_b = intervals[0]
    for a, b in intervals[1:]:
        if a <= cur_b + gap:
            cur_b = max(cur_b, b)
        else:
            merged.append((cur_a, cur_b))
            cur_a, cur_b = a, b
    merged.append((cur_a, cur_b))
    return merged


def compute_pass_x_levels(x_start: float, x_target: float, step: float, external: bool) -> List[Tuple[float, float]]:
    if step <= 0:
        return []
    passes: List[Tuple[float, float]] = []
    if external:
        x = x_start
        while x > x_target + 1e-9:
            x_hi = x
            x_lo = max(x_target, x - step)
            passes.append((x_hi, x_lo))
            x = x_lo
    else:
        x = x_start
        while x < x_target - 1e-9:
            x_lo = x
            x_hi = min(x_target, x + step)
            passes.append((x_hi, x_lo))
            x = x_hi
    return passes


def resolve_retract_targets(cfg: RetractCfg, *, external: bool, current_x: float, current_z: float, safe_z: float) -> Tuple[Optional[float], Optional[float]]:
    rx = cfg.x_value
    if rx is not None and not cfg.x_absolute:
        rx = current_x + (rx if external else -rx)
    rz = cfg.z_value
    if rz is not None and not cfg.z_absolute:
        rz = current_z + rz
    return rx, rz


def get_retract_cfg(settings: Dict[str, object], side_idx: int) -> RetractCfg:
    if side_idx == 0:
        x = settings.get("xra")
        z = settings.get("zra")
        x_abs = bool(settings.get("xra_absolute", False))
        z_abs = bool(settings.get("zra_absolute", False))
    else:
        x = settings.get("xri")
        z = settings.get("zri")
        x_abs = bool(settings.get("xri_absolute", False))
        z_abs = bool(settings.get("zri_absolute", False))
    try:
        x = None if x is None else float(x)
    except Exception:
        x = None
    try:
        z = None if z is None else float(z)
    except Exception:
        z = None
    return RetractCfg(x, z, x_abs, z_abs)


def contour_sub_from_points(points: List[Point], sub_num: int) -> List[str]:
    lines: List[str] = [f"o{sub_num} sub"]
    prev: Optional[Point] = None
    for x, z in points or []:
        if prev is None or (abs(prev[0] - x) > 1e-9 or abs(prev[1] - z) > 1e-9):
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            prev = (x, z)
    lines.append(f"o{sub_num} endsub")
    return lines


def contour_sub_from_primitives(primitives: List[Dict[str, object]], sub_num: int) -> List[str]:
    lines: List[str] = [f"o{sub_num} sub"]
    cur_x: Optional[float] = None
    cur_z: Optional[float] = None

    def _ensure_at(x: float, z: float) -> None:
        nonlocal cur_x, cur_z
        if cur_x is None or cur_z is None or abs(cur_x - x) > 1e-9 or abs(cur_z - z) > 1e-9:
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            cur_x, cur_z = x, z

    for pr in primitives or []:
        typ = pr.get("type")
        if typ == "line":
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            if p1 is None or p2 is None:
                continue
            x1, z1 = float(p1[0]), float(p1[1])
            x2, z2 = float(p2[0]), float(p2[1])
            _ensure_at(x1, z1)
            _ensure_at(x2, z2)
        elif typ == "arc":
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            c = pr.get("c") or pr.get("center")
            if p1 is None or p2 is None or c is None:
                continue
            x1, z1 = float(p1[0]), float(p1[1])
            x2, z2 = float(p2[0]), float(p2[1])
            cx, cz = float(c[0]), float(c[1])
            _ensure_at(x1, z1)
            i = cx - (cur_x if cur_x is not None else x1)
            k = cz - (cur_z if cur_z is not None else z1)
            g = "G3" if pr.get("ccw") else "G2"
            lines.append(f"{g} X{x2:.3f} Z{z2:.3f} I{i:.3f} K{k:.3f}")
            cur_x, cur_z = x2, z2

    lines.append(f"o{sub_num} endsub")
    return lines


def _emit_segment_with_pauses(lines: List[str], start: Point, end: Point, feed: float, pause_enabled: bool, pause_distance: float, pause_duration: float, state: Dict[str, object] | None = None):
    x0, z0 = start
    x1, z1 = end
    single_axis_segment = abs(x1 - x0) < 1e-9 or abs(z1 - z0) < 1e-9
    long_enough = max(abs(x1 - x0), abs(z1 - z0)) > pause_distance
    if pause_enabled and pause_distance > 0 and single_axis_segment and long_enough:
        if state is not None:
            state["needs_step_line_pause_sub"] = True
        lines.append(
            "o<step_line_pause> call "
            f"[{x0:.3f}] [{z0:.3f}] [{x1:.3f}] [{z1:.3f}] "
            f"[{pause_distance:.3f}] [{feed:.3f}] [{pause_duration:.3f}]"
        )
        return
    lines.append(f"G1 X{x1:.3f} Z{z1:.3f} F{feed:.3f}")


def rough_turn_parallel_x(path: List[Point], external: bool, x_stock: float, x_target: float, step_x: float, safe_z: float, feed: float, allow_undercut: bool = False, pause_enabled: bool = False, pause_distance: float = 0.0, pause_duration: float = 0.5, retract_cfg: Optional[RetractCfg] = None, leadout_length: float = LEADOUT_LENGTH_DEFAULT, pause_state: Dict[str, object] | None = None) -> List[str]:
    segs = segments_from_polyline(path)
    passes = compute_pass_x_levels(x_stock, x_target, step_x, external)
    lines: List[str] = ["(ABSPANEN Rough - parallel Z)"]
    xs = [p[0] for p in path] if path else []
    min_x = min(xs) if xs else None
    max_x = max(xs) if xs else None
    cfg = retract_cfg or RetractCfg(None, None, True, True)
    start_rx, start_rz = resolve_retract_targets(cfg, external=external, current_x=x_stock, current_z=safe_z, safe_z=safe_z)
    if start_rz is not None:
        lines.append(f"G0 Z{start_rz:.3f}")
    if start_rx is not None:
        lines.append(f"G0 X{start_rx:.3f}")
    z_dir = -1 if (min([p[1] for p in path]) if path else 0) < 0 else 1
    for pass_i, (x_hi, x_lo) in enumerate(passes, 1):
        band_lo, band_hi = (x_lo, x_hi) if x_lo <= x_hi else (x_hi, x_lo)
        x_cut = x_lo if external else x_hi
        z_intervals: List[Tuple[float, float, Segment]] = []
        for s in segs:
            hit = intersect_segment_with_x_band(s, x_cut - 1e-3, x_cut + 1e-3)
            if hit:
                z_intervals.append((hit[0], hit[1], s))
        if not z_intervals:
            lines.append(f"(Pass {pass_i}: no cut region in band X[{band_lo:.3f},{band_hi:.3f}])")
            continue
        lines.append(f"(Pass {pass_i}: X-band [{band_lo:.3f},{band_hi:.3f}])")
        for (za, zb, _seg) in z_intervals:
            if abs(zb - za) < 1e-9:
                continue
            if not allow_undercut and min_x is not None and max_x is not None:
                if external and x_cut < min_x - 1e-6:
                    continue
                if (not external) and x_cut > max_x + 1e-6:
                    continue
            lines.append(f"G0 X{x_cut:.3f} Z{safe_z:.3f}")
            z_low = min(za, zb)
            z_high = max(za, zb)
            z_entry, z_exit = (z_high, z_low) if z_dir < 0 else (z_low, z_high)
            lines.append(f"G1 Z{z_entry:.3f} F{feed:.3f}")
            _emit_segment_with_pauses(lines, (x_cut, z_entry), (x_cut, z_exit), feed, pause_enabled, pause_distance, pause_duration, state=pause_state)
            rx_eff, rz_eff = resolve_retract_targets(cfg, external=external, current_x=x_cut, current_z=z_exit, safe_z=safe_z)
            cmd = ["G0"]
            if rx_eff is not None:
                cmd.append(f"X{rx_eff:.3f}")
            if rz_eff is not None:
                cmd.append(f"Z{rz_eff:.3f}")
            if len(cmd) > 1:
                lines.append(" ".join(cmd))
    return lines


def rough_turn_parallel_z(path: List[Point], external: bool, z_stock: float, z_target: float, step_z: float, safe_z: float, feed: float, start_x: float, allow_undercut: bool = False, pause_enabled: bool = False, pause_distance: float = 0.0, pause_duration: float = 0.5, leadout_length: float = LEADOUT_LENGTH_DEFAULT, retract_cfg: Optional[RetractCfg] = None, pause_state: Dict[str, object] | None = None) -> List[str]:
    segs = segments_from_polyline(path)
    passes: List[Tuple[float, float]] = []
    if step_z <= 0:
        return []
    if external:
        z = z_stock
        while z > z_target + 1e-9:
            z_hi = z
            z_lo = max(z_target, z - step_z)
            passes.append((z_hi, z_lo))
            z = z_lo
    else:
        z = z_stock
        while z < z_target - 1e-9:
            z_lo = z
            z_hi = min(z_target, z + step_z)
            passes.append((z_hi, z_lo))
            z = z_hi
    xs = [p[0] for p in path] if path else []
    min_x = min(xs) if xs else None
    max_x = max(xs) if xs else None
    lines: List[str] = ["(ABSPANEN Rough - parallel X)"]
    if not passes:
        return lines
    cfg = retract_cfg or RetractCfg(None, None, True, True)
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append(f"G0 X{start_x:.3f}")
    for pass_i, (z_hi, z_lo) in enumerate(passes, 1):
        band_lo, band_hi = (z_lo, z_hi) if z_lo <= z_hi else (z_hi, z_lo)
        x_intervals: List[Tuple[float, float]] = []
        for s in segs:
            pseudo = Segment(s.z0, s.x0, s.z1, s.x1)
            hit = intersect_segment_with_x_band(pseudo, band_lo, band_hi)
            if hit:
                x_intervals.append(hit)
        x_work = merge_intervals(x_intervals)
        if not x_work:
            lines.append(f"(Pass {pass_i}: no cut region in band Z[{band_lo:.3f},{band_hi:.3f}])")
            continue
        lines.append(f"(Pass {pass_i}: Z-band [{band_lo:.3f},{band_hi:.3f}])")
        for (xa, xb) in x_work:
            if not allow_undercut and min_x is not None and max_x is not None:
                if xb < min_x - 1e-6 or xa > max_x + 1e-6:
                    continue
            lines.append(f"G1 Z{band_lo:.3f} F{feed:.3f}")
            cut_target = min(xa, xb) if external else max(xa, xb)
            _emit_segment_with_pauses(lines, (start_x, band_lo), (cut_target, band_lo), feed, pause_enabled, pause_distance, pause_duration, state=pause_state)
            rx_eff, rz_eff = resolve_retract_targets(cfg, external=external, current_x=cut_target, current_z=band_lo, safe_z=safe_z)
            cmd = ["G0"]
            if rx_eff is not None:
                cmd.append(f"X{rx_eff:.3f}")
            if rz_eff is not None:
                cmd.append(f"Z{rz_eff:.3f}")
            if len(cmd) > 1:
                lines.append(" ".join(cmd))
    return lines


def generate_abspanen_gcode(p: Dict[str, object], path: List[Point], settings: Dict[str, object]) -> List[str]:
    lines: List[str] = ["(ABSPANEN)"]
    require(p, ["depth_per_pass"], "ABSPANEN")
    require_positive(p, ["depth_per_pass"], "ABSPANEN")
    side_idx = 1 if is_internal_side(p.get("side", 0)) else 0
    feed = float(p.get("feed", 0.15))
    depth_per_pass = float(p["depth_per_pass"])
    pause_enabled = bool(p.get("pause_enabled", False))
    pause_distance = max(float(p.get("pause_distance", 0.0)), 0.0)
    pause_duration = 0.5
    mode_idx = resolve_enum_index(p.get("mode", 0), PARTING_MODE_INDEX, default=0)
    if pause_enabled and pause_distance > 0.0 and mode_idx in (0, 2):
        settings["needs_step_line_pause_sub"] = True
    finish_allow_x = max(float(p.get("finish_allow_x", 0.0)), 0.0)
    finish_allow_z = max(float(p.get("finish_allow_z", 0.0)), 0.0)
    if finish_allow_x > 0.0 or finish_allow_z > 0.0:
        lines.append(f"(Schlichtaufmaß X/Z: {finish_allow_x:.3f}/{finish_allow_z:.3f} mm)")
    tool_num = require_tool(p, "ABSPANEN")
    spindle = float(p.get("spindle", 0.0))
    append_tool_and_spindle(
        lines, tool_num, spindle, settings,
        spindle_mode=p.get("spindle_mode"), spindle_max_rpm=p.get("spindle_max_rpm"),
    )
    lines.append(f"F{feed:.3f}")
    contour_variants = None
    contour_params = p.get("_contour_params")
    if isinstance(contour_params, dict) and contour_params.get("segments"):
        contour_variants = build_contour_variants(contour_params)
    finish_path = path
    rough_path = path
    feature_path: List[Point] = []
    relief_mode = normalize_relief_mode(p.get("undercut_mode"))
    if contour_variants:
        finish_path = contour_variants["finish_points"] or finish_path
        rough_path = contour_variants["rough_points"] or finish_path
        feature_path = contour_variants["feature_points"] or []
    elif path and isinstance(path[0], dict):
        finish_path = primitive_to_points(path) or []
        rough_path = finish_path
    if not finish_path and not rough_path:
        return lines
    if not rough_path:
        rough_path = finish_path
    if not finish_path:
        finish_path = rough_path

    path = finish_path
    stock_x = _resolve_roughing_stock_x(settings, rough_path, external=side_idx == 0)
    cfg = get_retract_cfg(settings, side_idx)
    if cfg.z_value is None:
        raise ValueError("ZRA/ZRI ist nicht gesetzt (oder 0). Bitte im Programm-Tab eintragen.")
    safe_z = float(cfg.z_value)
    external = side_idx == 0
    if not external:
        validate_internal_x_limit(
            settings,
            [pt[0] for pt in finish_path] + [pt[0] for pt in rough_path],
            op_label="Innenbearbeitung",
        )
    tool_info = (settings.get("tools", {}) or {}).get(tool_num)
    compensation_command = nose_compensation_command(tool_info, external)
    nose_disabled = bool(p.get("nose_comp_disabled", False))
    slice_strategy = p.get("slice_strategy")
    output_preference = _normalize_output_preference(p.get("output_preference", settings.get("output_preference")))
    strategy_code = None
    if isinstance(slice_strategy, (int, float)):
        strategy_code = "parallel_x" if int(slice_strategy) == 1 else "parallel_z" if int(slice_strategy) == 2 else None
    elif isinstance(slice_strategy, str):
        strategy_code = slice_strategy
    contour_name = p.get("contour_name")
    contour_subs = settings.get("contour_subs", {}) if settings else {}
    contour_sub_num = contour_subs.get(contour_name) if contour_name else None
    primitives = p.get("_primitives")
    if contour_variants:
        primitives = contour_variants["finish_primitives"]

    lines.append(f"(Strategie: {strategy_code or 'manuell'})")
    lines.append(f"(Ausgabe bevorzugen: {output_preference})")
    lines.append(f"(Hinterschnitt-Modus: {relief_mode})")
    if finish_allow_x > 0.0 or finish_allow_z > 0.0:
        lines.append(f"(Aufmass X/Z: {finish_allow_x:.3f}/{finish_allow_z:.3f})")

    def _build_cycle_sub(sub_num: int) -> List[str]:
        active_primitives = primitives
        active_points = finish_path
        if relief_mode in ("ignore", "finish_only", "separate") and contour_variants:
            active_primitives = contour_variants["rough_primitives"]
            active_points = rough_path
        return contour_sub_from_primitives(active_primitives, sub_num) if active_primitives else contour_sub_from_points(active_points, sub_num)

    rough_cycle_path = finish_path if relief_mode == "full" else rough_path
    can_use_cycles = output_preference != "prefer_explicit"
    rough_done = False
    cycle_finish_done = False

    # mode_idx == 1 (reiner Schlichtstep) darf NIE einen G71/G72-Schruppzyklus
    # erzeugen - ein separater Schruppstep (typischerweise mit eigenem
    # Werkzeug) hat das Material bereits abgetragen. Ohne diese Schranke
    # wiederholte ein dedizierter Schlichtstep mit gueltiger Strategie
    # unbemerkt die komplette Schruppbearbeitung.
    if strategy_code == "parallel_x" and mode_idx in (0, 2):
        if can_use_cycles and is_monotonic_x_decreasing(rough_cycle_path):
            allocator = settings.get("sub_allocator")
            sub_num = contour_sub_num if contour_sub_num is not None else (allocator.allocate() if allocator else 100)
            lines.append("(ABSPANEN Rough - parallel X)")
            if contour_sub_num is None:
                lines.extend(_build_cycle_sub(sub_num))
            lines.append("(Anfahren vor Zyklus)")
            stock_x_adj = stock_x - finish_allow_x if mode_idx == 0 and finish_allow_x > 0.0 else stock_x
            stock_x_adj = max(stock_x_adj, 0.0)
            emit_approach(lines, stock_x_adj, safe_z, settings)
            lines.append(f"G72 Q{sub_num} X{stock_x_adj:.3f} Z{safe_z:.3f} D{depth_per_pass:.3f}")
            if mode_idx in (1, 2) and relief_mode == "full":
                lines.append(f"G70 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f}")
            rough_done = True
            cycle_finish_done = mode_idx in (1, 2) and relief_mode == "full"
        if not rough_done:
            if output_preference == "prefer_cycle":
                lines.append("(Fallback-Grund: Kontur nicht G72-zyklustauglich)")
            elif output_preference == "prefer_explicit":
                lines.append("(Fallback-Grund: expliziten Code bevorzugt)")
            z_vals = [pp[1] for pp in rough_path] if rough_path else [0.0]
            rough_lines = rough_turn_parallel_z(rough_path, external=external, z_stock=max(z_vals), z_target=min(z_vals), step_z=depth_per_pass, safe_z=safe_z, feed=feed, start_x=stock_x, pause_enabled=pause_enabled, pause_distance=pause_distance, pause_duration=pause_duration, retract_cfg=cfg, pause_state=settings)
            if rough_lines:
                rough_lines[0] = "(ABSPANEN Rough - parallel X - Move-based)"
            lines.extend(rough_lines)
    elif strategy_code == "parallel_z" and mode_idx in (0, 2):
        can_use_g71 = is_monotonic_z_decreasing(rough_cycle_path) and is_monotonic_x(rough_cycle_path)
        if can_use_cycles and can_use_g71:
            allocator = settings.get("sub_allocator")
            sub_num = contour_sub_num if contour_sub_num is not None else (allocator.allocate() if allocator else 100)
            lines.append("(ABSPANEN Rough - parallel Z)")
            if contour_sub_num is None:
                lines.extend(_build_cycle_sub(sub_num))
            emit_approach(lines, stock_x, safe_z, settings)
            lines.append(f"G71 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f} D{depth_per_pass:.3f}")
            if mode_idx in (1, 2) and relief_mode == "full":
                lines.append(f"G70 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f}")
            rough_done = True
            cycle_finish_done = mode_idx in (1, 2) and relief_mode == "full"
        if not rough_done:
            if output_preference == "prefer_cycle":
                lines.append("(Fallback-Grund: Kontur nicht G71-zyklustauglich)")
            elif relief_mode == "separate":
                lines.append("(Fallback-Grund: Hinterschnitt separat)")
            elif pause_enabled and pause_distance > 0.0:
                lines.append("(Fallback-Grund: Spanbruch/Pausen aktiv)")
            elif output_preference == "prefer_explicit":
                lines.append("(Fallback-Grund: expliziten Code bevorzugt)")
            else:
                lines.append("(Fallback-Grund: automatische Entscheidung -> Move-based)")
            xs = [pp[0] for pp in rough_path] if rough_path else [stock_x]
            rough_lines = rough_turn_parallel_x(rough_path, external=external, x_stock=stock_x, x_target=min(xs) if external else max(xs), step_x=depth_per_pass, safe_z=safe_z, feed=feed, pause_enabled=pause_enabled, pause_distance=pause_distance, pause_duration=pause_duration, retract_cfg=cfg, pause_state=settings)
            if rough_lines:
                rough_lines[0] = "(ABSPANEN Rough - parallel Z - Move-based)"
            lines.extend(rough_lines)
    if relief_mode == "separate" and feature_path:
        _emit_relief_pass(lines, feature_path, feed, safe_z, settings, tool_num, spindle, p)
    if mode_idx in (1, 2) and not cycle_finish_done:
        lines.append("(Schlichtschnitt Kontur)")
        finish_points = rough_path if relief_mode == "ignore" else finish_path
        entry_x, entry_z = _finish_entry_point(finish_points, safe_z)
        # War zuvor ein einzelner diagonaler G0 (X und Z gleichzeitig) direkt aus der
        # jeweils vorherigen Position - potenziell noch im/am Rohteil bzw. in der
        # Futter-Sperrzone. emit_approach() prueft das (WARN-Zeilen) und faehrt bei
        # Bedarf erst Z, dann X auf die sichere Ebene, bevor der eigentliche
        # Kontur-Einfahrpunkt angefahren wird - dieselbe Absicherung, die die
        # Schrupp-Zustellung oben bereits nutzt.
        emit_approach(lines, entry_x, entry_z, settings)
        if compensation_command and not nose_disabled:
            lines.append(compensation_command)
        prev_point = (entry_x, entry_z) if compensation_command and not nose_disabled else None
        if contour_variants and relief_mode != "ignore":
            finish_primitives = contour_variants["finish_primitives"] or []
            _emit_finish_primitives(lines, finish_primitives, feed=feed)
            if finish_points:
                prev_point = finish_points[-1]
        else:
            for idx, (x, z) in enumerate(finish_points):
                current_point = (x, z)
                if idx == 0 and compensation_command and not nose_disabled and abs(entry_z - z) <= 1e-9 and abs(entry_x - x) <= 1e-9:
                    continue
                if current_point != prev_point:
                    lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
                    prev_point = current_point
        # Nullbewegung vermeiden: wenn der letzte Konturpunkt bereits auf
        # safe_z liegt (z. B. Kontur endet an der Stirnflaeche bei Z0, safe_z
        # ebenfalls 0), ist der Rueckzug bereits erreicht - ein zusaetzliches
        # G0 auf dieselbe Position ist eine bedeutungslose Nullbewegung.
        if not (prev_point is not None and abs(prev_point[1] - safe_z) <= 1e-6):
            lines.append(f"G0 Z{safe_z:.3f}")
        if compensation_command and not nose_disabled:
            lines.append("G40")
    elif mode_idx == 0 and strategy_code is None:
        lines.append("(WARN: Abspanen-Schruppen ohne Bearbeitungsrichtung ist deaktiviert)")
        lines.append("(      Bitte in 'Abspanen -> Bearbeitungsrichtung' Parallel X oder Parallel Z wählen.)")
    return lines


def step_line_pause_sub_definition() -> List[str]:
    return ["o<step_line_pause> sub", "(Step line pause helper)", "G4 P[#7]", "o<step_line_pause> endsub"]


def step_x_pause_sub_definition() -> List[str]:
    return ["o<step_x_pause> sub", "(Step X pause helper)", "G4 P0.1", "o<step_x_pause> endsub"]


__all__ = [
    "LEADOUT_LENGTH_DEFAULT",
    "RetractCfg",
    "Segment",
    "compute_pass_x_levels",
    "contour_sub_from_points",
    "contour_sub_from_primitives",
    "generate_abspanen_gcode",
    "get_retract_cfg",
    "intersect_segment_with_x_band",
    "merge_intervals",
    "rough_turn_parallel_x",
    "rough_turn_parallel_z",
    "segments_from_polyline",
    "step_line_pause_sub_definition",
    "step_x_pause_sub_definition",
]
