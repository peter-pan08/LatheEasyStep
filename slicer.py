"""Slicing helpers for roughing (parallel X / parallel Z)"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import math

Point = Tuple[float, float]  # (x, z)

@dataclass
class Segment:
    x0: float
    z0: float
    x1: float
    z1: float


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

    # vertical in X
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


def rough_turn_parallel_x(
    path: List[Point],
    external: bool,
    x_stock: float,
    x_target: float,
    step_x: float,
    safe_z: float,
    feed: float,
    allow_undercut: bool = False,
    pause_enabled: bool = False,
    pause_distance: float = 0.0,
    pause_duration: float = 0.5,
) -> List[str]:
    segs = segments_from_polyline(path)
    passes = compute_pass_x_levels(x_stock, x_target, step_x, external)

    lines: List[str] = []
    lines.append("(ABSPANEN Rough - parallel X slicing)")

    # bounding X of contour path (used to limit undercuts)
    xs = [p[0] for p in path] if path else []
    min_x = min(xs) if xs else None
    max_x = max(xs) if xs else None

    for pass_i, (x_hi, x_lo) in enumerate(passes, 1):
        band_lo, band_hi = (x_lo, x_hi) if x_lo <= x_hi else (x_hi, x_lo)
        z_intervals: List[Tuple[float, float]] = []
        for s in segs:
            hit = intersect_segment_with_x_band(s, band_lo, band_hi)
            if hit:
                z_intervals.append(hit)
        z_work = merge_intervals(z_intervals)

        if not z_work:
            lines.append(f"(Pass {pass_i}: no cut region in band X[{band_lo:.3f},{band_hi:.3f}])")
            continue

        lines.append(f"(Pass {pass_i}: X-band [{band_lo:.3f},{band_hi:.3f}])")

        for (za, zb) in z_work:
            x_cut = x_lo if external else x_hi
            # if undercuts are not allowed, skip cuts where the X cut position
            # lies clearly outside the contour X-range
            if not allow_undercut and min_x is not None and max_x is not None:
                eps = 1e-6
                if external and x_cut < min_x - eps:
                    # would undercut beyond contour's min X
                    continue
                if (not external) and x_cut > max_x + eps:
                    # internal undercut beyond contour's max X
                    continue
            lines.append(f"G0 Z{safe_z:.3f}")
            lines.append(f"G0 X{x_cut:.3f}")
            lines.append(f"G0 Z{za:.3f}")
            # Z movement is a segment from (x_cut, za) to (x_cut, zb)
            if pause_enabled and pause_distance > 0 and abs(zb - za) > pause_distance:
                # use the compact pause sub call
                lines.append(
                    "o<step_line_pause> call "
                    f"[{x_cut:.3f}] [{za:.3f}] [{x_cut:.3f}] [{zb:.3f}] "
                    f"[{pause_distance:.3f}] [{feed:.3f}] [{pause_duration:.3f}]"
                )
            else:
                lines.append(f"G1 Z{zb:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

    return lines


def rough_turn_parallel_z(
    path: List[Point],
    external: bool,
    z_stock: float,
    z_target: float,
    step_z: float,
    safe_z: float,
    feed: float,
    allow_undercut: bool = False,
    pause_enabled: bool = False,
    pause_distance: float = 0.0,
    pause_duration: float = 0.5,
) -> List[str]:
    """Slicing parallel to Z (horizontal bands)."""
    segs = segments_from_polyline(path)

    # compute Z passes from z_stock towards z_target
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

    lines: List[str] = []
    lines.append("(ABSPANEN Rough - parallel Z slicing)")

    for pass_i, (z_hi, z_lo) in enumerate(passes, 1):
        band_lo, band_hi = (z_lo, z_hi) if z_lo <= z_hi else (z_hi, z_lo)
        x_intervals: List[Tuple[float, float]] = []
        for s in segs:
            # reuse intersect logic by swapping coordinates
            # create a pseudo-segment in (z,x) space: treat z as 'x' and x as 'z'
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
            # treat interval [xa, xb] as the X-range to cut at this Z band
            x_start = xa
            x_end = xb
            # skip undercutting if not allowed (entire interval outside contour X range)
            if not allow_undercut and min_x is not None and max_x is not None:
                eps = 1e-6
                if x_end < min_x - eps or x_start > max_x + eps:
                    continue

            lines.append(f"G0 Z{safe_z:.3f}")
            lines.append(f"G0 X{x_start:.3f}")
            lines.append(f"G0 Z{band_lo:.3f}")
            # X movement is a segment from (x_start, band_lo) to (x_end, band_lo)
            if pause_enabled and pause_distance > 0 and abs(x_end - x_start) > pause_distance:
                # use the compact X-based step pause sub
                lines.append(
                    "o<step_x_pause> call "
                    f"[{x_start:.3f}] [{x_end:.3f}] [{pause_distance:.3f}] [{feed:.3f}] [{pause_duration:.3f}]"
                )
            else:
                lines.append(f"G1 X{x_end:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

    return lines


# ----------------------------------------------------------------------
# Abspanen (Parting) generator helpers
# ----------------------------------------------------------------------

def _abspanen_safe_z(settings: Dict[str, object], side_idx: int, path: List[Point]) -> float:
    if side_idx == 0:
        safe_candidates = [settings.get("zra"), settings.get("zri")]
    else:
        safe_candidates = [settings.get("zri"), settings.get("zra")]
    for candidate in safe_candidates:
        try:
            if candidate is not None and float(candidate) != 0.0:
                return float(candidate)
        except Exception:
            continue
    if path:
        return path[0][1] + 2.0
    return 2.0


def _offset_abspanen_path(path: List[Point], stock_x: float, offset: float) -> List[Point]:
    if offset <= 1e-6:
        return list(path)

    xs = [p[0] for p in path]
    min_x, max_x = min(xs), max(xs)
    adjusted: List[Point] = []

    if stock_x >= max_x:
        for x, z in path:
            adjusted.append((min(x + offset, stock_x), z))
    elif stock_x <= min_x:
        for x, z in path:
            adjusted.append((max(x - offset, stock_x), z))
    else:
        for x, z in path:
            adjusted.append((x + offset, z))

    return adjusted


def _abspanen_offsets(stock_x: float, path: List[Point], depth_per_pass: float) -> List[float]:
    if not path:
        return [0.0]

    xs = [p[0] for p in path]
    min_x, max_x = min(xs), max(xs)

    if stock_x >= max_x:
        start_offset = stock_x - min_x
    elif stock_x <= min_x:
        start_offset = max_x - stock_x
    else:
        start_offset = 0.0

    if start_offset <= 1e-6:
        return [0.0]

    if depth_per_pass <= 0:
        return [start_offset, 0.0]

    passes = math.ceil(start_offset / depth_per_pass)
    offsets: List[float] = []
    for i in range(0, passes + 1):
        current = max(round(start_offset - i * depth_per_pass, 6), 0.0)
        if offsets and abs(offsets[-1] - current) < 1e-6:
            continue
        offsets.append(current)
    if offsets[-1] != 0.0:
        offsets.append(0.0)
    return offsets


# ----------------------------------------------------------------------
# Generic helpers useful for CAM modules
# ----------------------------------------------------------------------

def gcode_from_path(path: List[Point], feed: float, safe_z: float) -> List[str]:
    """Generate simple G-Code from a polyline path (first point is start)."""
    lines: List[str] = []
    if not path:
        return lines
    x0, z0 = path[0]
    lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
    if len(path) > 1:
        lines.append(f"G1 Z{z0:.3f} F{feed:.3f}")
    for x, z in path[1:]:
        lines.append(f"G1 X{x:.3f} Z{z:.3f}")
    return lines


def _contour_retract_positions(settings: Dict[str, object], side_idx: int, fallback_x: float, fallback_z: float) -> Tuple[float, float]:
    """Return (retract_x, retract_z) using settings or fallbacks.

    This mirrors the logic previously in the handler and is useful for CAM
    operations that need to pick a safe retract point based on program
    settings.
    """
    def _pick(candidate: object, default: float) -> float:
        try:
            if candidate is not None and float(candidate) != 0.0:
                return float(candidate)
        except Exception:
            pass
        return default

    if side_idx == 0:
        retract_x = _pick(settings.get("xra"), fallback_x)
        retract_z = _pick(settings.get("zra"), fallback_z)
    else:
        retract_x = _pick(settings.get("xri"), fallback_x)
        retract_z = _pick(settings.get("zri"), fallback_z)

    return retract_x, retract_z


def _emit_segment_with_pauses(
    lines: List[str],
    start: Point,
    end: Point,
    feed: float,
    pause_enabled: bool,
    pause_distance: float,
    pause_duration: float,
):
    x0, z0 = start
    x1, z1 = end
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)

    if pause_enabled and pause_distance > 0.0 and length > pause_distance:
        lines.append(
            "o<step_line_pause> call "
            f"[{x0:.3f}] [{z0:.3f}] [{x1:.3f}] [{z1:.3f}] "
            f"[{pause_distance:.3f}] [{feed:.3f}] [{pause_duration:.3f}]"
        )
        return

    lines.append(f"G1 X{x1:.3f} Z{z1:.3f} F{feed:.3f}")


def _gcode_for_abspanen_pass(
    path: List[Point],
    feed: float,
    safe_z: float,
    pause_enabled: bool,
    pause_distance: float,
    pause_duration: float,
) -> List[str]:
    if not path:
        return []

    lines: List[str] = []
    x0, z0 = path[0]
    lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
    lines.append(f"G0 Z{z0:.3f}")
    lines.append(f"G1 X{x0:.3f} Z{z0:.3f} F{feed:.3f}")

    prev = path[0]
    for point in path[1:]:
        _emit_segment_with_pauses(
            lines, prev, point, feed, pause_enabled, pause_distance, pause_duration
        )
        prev = point

    lines.append(f"G0 Z{safe_z:.3f}")
    return lines


def generate_abspanen_gcode(p: Dict[str, object], path: List[Point], settings: Dict[str, object]) -> List[str]:
    """Generates G-code for an Abspanen operation.

    This consolidates the previous handler behavior and uses the slicing helpers
    when requested.
    """
    lines: List[str] = ["(ABSPANEN)"]

    if not path:
        return lines

    side_idx = int(p.get("side", 0))
    feed = float(p.get("feed", 0.15))
    depth_per_pass = max(float(p.get("depth_per_pass", 0.0)), 0.0)
    pause_enabled = bool(p.get("pause_enabled", False))
    pause_distance = max(float(p.get("pause_distance", 0.0)), 0.0)
    pause_duration = 0.5
    mode_idx = int(p.get("mode", 0))  # 0=Schruppen, 1=Schlichten

    # harte Sicherung: Unterbrechung nur beim Schruppen
    if mode_idx != 0:
        pause_enabled = False

    tool_num = int(p.get("tool", 0))
    spindle = float(p.get("spindle", 0.0))

    stock_x = settings.get("xa") if side_idx == 0 else settings.get("xi")
    try:
        stock_x = float(stock_x) if stock_x is not None else None
    except Exception:
        stock_x = None
    if stock_x is None:
        stock_x = max(point[0] for point in path)

    safe_z = _abspanen_safe_z(settings, side_idx, path)

    offsets = _abspanen_offsets(stock_x, path, depth_per_pass)

    # slicing arguments
    slice_strategy = p.get("slice_strategy")
    slice_step = float(p.get("slice_step", depth_per_pass or 1.0))
    allow_undercut = bool(p.get("allow_undercut", False))
    external = side_idx == 0

    # Accept either index or code
    strategy_code = None
    try:
        if isinstance(slice_strategy, (int, float)):
            idx = int(slice_strategy)
            if idx == 1:
                strategy_code = "parallel_x"
            elif idx == 2:
                strategy_code = "parallel_z"
            else:
                strategy_code = None
        elif isinstance(slice_strategy, str):
            strategy_code = slice_strategy
    except Exception:
        strategy_code = None

    if strategy_code == "parallel_x":
        xs = [pp[0] for pp in path] if path else [stock_x]
        x_target = min(xs) if external else max(xs)
        rough_lines = rough_turn_parallel_x(
            path,
            external=external,
            x_stock=stock_x,
            x_target=x_target,
            step_x=slice_step,
            safe_z=safe_z,
            feed=feed,
            allow_undercut=allow_undercut,
            pause_enabled=pause_enabled,
            pause_distance=pause_distance,
            pause_duration=pause_duration,
        )
        lines.extend(rough_lines)

        # Finish optional (Kontur 1x)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            for (x, z) in path:
                lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

        return lines

    if strategy_code == "parallel_z":
        z_vals = [pp[1] for pp in path] if path else [0.0]
        z_stock = max(z_vals) if external else min(z_vals)
        z_target = min(z_vals) if external else max(z_vals)
        rough_lines = rough_turn_parallel_z(
            path,
            external=external,
            z_stock=z_stock,
            z_target=z_target,
            step_z=slice_step,
            safe_z=safe_z,
            feed=feed,
            allow_undercut=allow_undercut,
            pause_enabled=pause_enabled,
            pause_distance=pause_distance,
            pause_duration=pause_duration,
        )
        lines.extend(rough_lines)

        # Finish optional (Kontur 1x)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            for (x, z) in path:
                lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

        return lines

    # No slicing selected
    if mode_idx == 0:
        lines.append("(WARN: Abspanen-Schruppen ohne Slicing ist deaktiviert)")
        lines.append("(      Bitte in 'Abspanen -> Slicing Strategy' Parallel X oder Parallel Z wählen.)")
        return lines

    # Finish-only (mode_idx == 1) without slicing: single contour pass
    # append tool and spindle
    try:
        tool_num = int(float(tool_num))
    except Exception:
        tool_num = 0
    if tool_num > 0:
        lines.append(f"(Werkzeug T{tool_num:02d})")
        lines.append(f"T{tool_num:02d} M6")
    try:
        rpm = float(spindle)
    except Exception:
        rpm = 0.0
    if rpm and rpm > 0:
        rpm_value = int(round(rpm))
        lines.append(f"S{rpm_value} M3")

    lines.append("(Schlichtschnitt Kontur)")
    lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
    for (x, z) in path:
        lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
    lines.append(f"G0 Z{safe_z:.3f}")
    return lines
