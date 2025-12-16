"""Slicing helpers for roughing (parallel X / parallel Z)"""
from dataclasses import dataclass
from typing import List, Tuple, Optional

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
            x_cut = xa if external else xb
            # skip undercutting if not allowed
            if not allow_undercut and min_x is not None and max_x is not None:
                eps = 1e-6
                if x_cut < min_x - eps or x_cut > max_x + eps:
                    continue
            lines.append(f"G0 Z{safe_z:.3f}")
            lines.append(f"G0 X{x_cut:.3f}")
            lines.append(f"G0 Z{band_lo:.3f}")
            lines.append(f"G1 Z{band_hi:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

    return lines
