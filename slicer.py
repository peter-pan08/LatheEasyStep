"""Helpers for parting roughing (parallel X / parallel Z)"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import math

Point = Tuple[float, float]  # (x, z)


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


def _norm(vx: float, vz: float) -> Tuple[float, float]:
    length = math.hypot(vx, vz)
    if length < 1e-12:
        return 0.0, 0.0
    return vx / length, vz / length


def _dot(ax: float, az: float, bx: float, bz: float) -> float:
    return ax * bx + az * bz


def _cross(ax: float, az: float, bx: float, bz: float) -> float:
    return ax * bz - az * bx


def _line_intersection(
    P: Tuple[float, float],
    v: Tuple[float, float],
    Q: Tuple[float, float],
    w: Tuple[float, float],
) -> Optional[Tuple[float, float]]:
    px, pz = P
    vx, vz = v
    qx, qz = Q
    wx, wz = w
    denom = _cross(vx, vz, wx, wz)
    if abs(denom) < 1e-12:
        return None
    dx = qx - px
    dz = qz - pz
    t = _cross(dx, dz, wx, wz) / denom
    return (px + vx * t, pz + vz * t)


def fillet_arc(
    p_prev: Point,
    p_curr: Point,
    p_next: Point,
    radius: float,
    *,
    side: str = "auto",
    chord: float = 0.2,
) -> Optional[Dict[str, object]]:
    """Return a fillet arc passing through p_curr with tangency to the two segments."""
    if radius <= 0.0 or chord <= 0.0:
        return None
    x0, z0 = p_prev
    x1, z1 = p_curr
    x2, z2 = p_next

    d1x, d1z = _norm(x0 - x1, z0 - z1)
    d2x, d2z = _norm(x2 - x1, z2 - z1)
    if abs(d1x) < 1e-12 and abs(d1z) < 1e-12:
        return None
    if abs(d2x) < 1e-12 and abs(d2z) < 1e-12:
        return None

    a1x, a1z = -d1x, -d1z
    a2x, a2z = d2x, d2z
    cos_theta = max(-1.0, min(1.0, _dot(a1x, a1z, a2x, a2z)))
    theta = math.acos(cos_theta)
    if theta <= 1e-6 or abs(math.pi - theta) < 1e-6:
        return None

    tan_half = math.tan(theta * 0.5)
    if tan_half <= 0.0:
        return None
    tangential = radius * tan_half

    T1 = (x1 + a1x * tangential, z1 + a1z * tangential)
    T2 = (x1 + a2x * tangential, z1 + a2z * tangential)

    turn = _cross(a1x, a1z, a2x, a2z)
    if abs(turn) < 1e-9:
        return None

    n1L = (-a1z, a1x)
    n1R = (a1z, -a1x)
    n2L = (-a2z, a2x)
    n2R = (a2z, -a2x)

    candidates: List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]] = []
    for n1 in (n1L, n1R):
        for n2 in (n2L, n2R):
            P = (T1[0] + n1[0] * radius, T1[1] + n1[1] * radius)
            Q = (T2[0] + n2[0] * radius, T2[1] + n2[1] * radius)
            center = _line_intersection(P, (a1x, a1z), Q, (a2x, a2z))
            if center is None:
                continue
            candidates.append((center, n1, n2))
    if not candidates:
        return None

    def score_center(center: Tuple[float, float]) -> float:
        cx, cz = center
        vx, vz = cx - x1, cz - z1
        return turn * _cross(a1x, a1z, vx, vz)

    side_lower = str(side or "auto").lower()
    if side_lower == "outer":
        chosen = min(candidates, key=lambda tup: score_center(tup[0]))
    else:
        chosen = max(candidates, key=lambda tup: score_center(tup[0]))

    center = chosen[0]
    cx, cz = center
    vec_start = (T1[0] - cx, T1[1] - cz)
    vec_end = (T2[0] - cx, T2[1] - cz)
    angle_start = math.atan2(vec_start[1], vec_start[0])
    angle_end = math.atan2(vec_end[1], vec_end[0])
    ccw = turn > 0

    def unwrap(a_start: float, a_end: float, ccw_dir: bool) -> Tuple[float, float]:
        while ccw_dir and a_end < a_start:
            a_end += 2.0 * math.pi
        while not ccw_dir and a_end > a_start:
            a_end -= 2.0 * math.pi
        return a_start, a_end

    a0, a1 = unwrap(angle_start, angle_end, ccw)
    arc_length = abs(a1 - a0) * radius
    chords = max(chord, 1e-6)
    steps = max(4, int(math.ceil(arc_length / chords)))
    points: List[Point] = []
    delta = a1 - a0
    for idx in range(steps + 1):
        fraction = idx / steps
        angle = a0 + delta * fraction
        points.append((cx + radius * math.cos(angle), cz + radius * math.sin(angle)))

    return {
        "T1": T1,
        "T2": T2,
        "C": center,
        "ccw": ccw,
        "points": points,
    }


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


def _point_at(seg: Segment, t: float) -> Point:
    return (seg.x0 + (seg.x1 - seg.x0) * t, seg.z0 + (seg.z1 - seg.z0) * t)


def _parameter_on_segment(seg: Segment, point: Point, eps: float = 1e-6) -> Optional[float]:
    dx = seg.x1 - seg.x0
    dz = seg.z1 - seg.z0
    seg_len_sq = dx * dx + dz * dz
    if seg_len_sq < 1e-18:
        return None
    px = point[0] - seg.x0
    pz = point[1] - seg.z0
    t = (px * dx + pz * dz) / seg_len_sq
    if t < -eps or t > 1.0 + eps:
        return None
    proj_x = seg.x0 + dx * t
    proj_z = seg.z0 + dz * t
    if abs(point[0] - proj_x) > eps or abs(point[1] - proj_z) > eps:
        return None
    return max(0.0, min(1.0, t))


def infer_z_dir_from_path(path: List[Point]) -> int:
    if not path:
        return -1
    zs = [p[1] for p in path]
    z_min = min(zs)
    z_max = max(zs)
    if abs(z_min) > abs(z_max):
        return -1
    return +1


def _find_contour_at_z_in_band(
    segs: List[Segment],
    z: float,
    x_lo: float,
    x_hi: float,
    prefer_high_x: bool,
    eps: float = 1e-6,
) -> Optional[Tuple[Point, int, float]]:
    best: Optional[Tuple[Point, int, float, float]] = None
    for idx, seg in enumerate(segs):
        dz = seg.z1 - seg.z0
        if abs(dz) < 1e-12:
            continue
        t = (z - seg.z0) / dz
        if t < -eps or t > 1.0 + eps:
            continue
        x = seg.x0 + (seg.x1 - seg.x0) * t
        if x < x_lo - eps or x > x_hi + eps:
            continue
        clamp_t = max(0.0, min(1.0, t))
        pt = (x, z)
        candidate = (pt, idx, clamp_t, x)
        if best is None:
            best = candidate
            continue
        _, _, _, best_x = best
        if prefer_high_x:
            if x > best_x:
                best = candidate
        else:
            if x < best_x:
                best = candidate
    if best is None:
        return None
    pt, idx, t, _ = best
    return (pt, idx, t)


def pick_entry_exit(z_low: float, z_high: float, z_dir: int) -> Tuple[float, float]:
    if z_dir < 0:
        return (z_high, z_low)
    return (z_low, z_high)


def pick_leadout_step_direction(seg_dx: float, seg_dz: float, z_dir: int, external: bool) -> int:
    if abs(seg_dz) < 1e-12:
        direction = +1 if seg_dx >= 0 else -1
    else:
        direction = +1 if (seg_dz * z_dir) > 0 else -1
    if external and seg_dx * direction < 0:
        direction *= -1
    return direction


def _advance_along_polyline(
    segs: List[Segment],
    seg_idx: int,
    t: float,
    length: float,
    direction: int,
    eps: float = 1e-6,
) -> Point:
    if not segs:
        return (0.0, 0.0)
    dir_sign = 1 if direction >= 0 else -1
    current_idx = seg_idx
    current_t = t
    remaining = max(length, 0.0)
    while remaining > eps:
        seg = segs[current_idx]
        seg_dx = seg.x1 - seg.x0
        seg_dz = seg.z1 - seg.z0
        seg_len = math.hypot(seg_dx, seg_dz)
        if seg_len < 1e-12:
            next_idx = current_idx + dir_sign
            if not (0 <= next_idx < len(segs)):
                return _point_at(seg, current_t)
            current_idx = next_idx
            current_t = 0.0 if dir_sign == 1 else 1.0
            continue
        remaining_on_seg = seg_len * ((1.0 - current_t) if dir_sign == 1 else current_t)
        target_t = 1.0 if dir_sign == 1 else 0.0
        if remaining_on_seg >= remaining - eps:
            delta_t = remaining / seg_len
            new_t = current_t + dir_sign * delta_t
            return _point_at(seg, max(0.0, min(1.0, new_t)))
        remaining -= remaining_on_seg
        next_idx = current_idx + dir_sign
        if not (0 <= next_idx < len(segs)):
            return _point_at(seg, target_t)
        current_idx = next_idx
        current_t = 0.0 if direction == 1 else 1.0
    return _point_at(segs[current_idx], current_t)


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


def emit_g0(lines: List[str], *, x: Optional[float] = None, z: Optional[float] = None) -> None:
    """Emit a single G0 with both axes so retracts happen simultaneously."""
    if x is None and z is None:
        return
    cmd = ["G0"]
    if x is not None:
        cmd.append(f"X{x:.3f}")
    if z is not None:
        cmd.append(f"Z{z:.3f}")
    lines.append(" ".join(cmd))


def resolve_retract_targets(
    cfg: RetractCfg,
    *,
    external: bool,
    current_x: float,
    current_z: float,
    safe_z: float,
) -> Tuple[Optional[float], Optional[float]]:
    """Return the effective X/Z retract targets based on the config."""
    rx = cfg.x_value
    if rx is not None and not cfg.x_absolute:
        rx = current_x + (rx if external else -rx)

    rz = cfg.z_value
    if rz is not None:
        if not cfg.z_absolute:
            rz = current_z + rz

    return rx, rz


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
    retract_cfg: Optional[RetractCfg] = None,
    leadout_length: float = LEADOUT_LENGTH_DEFAULT,
) -> List[str]:
    segs = segments_from_polyline(path)
    passes = compute_pass_x_levels(x_stock, x_target, step_x, external)

    lines: List[str] = []
    lines.append("(ABSPANEN Rough - parallel Z)")

    # bounding X of contour path (used to limit undercuts)
    xs = [p[0] for p in path] if path else []
    min_x = min(xs) if xs else None
    max_x = max(xs) if xs else None

    cfg = retract_cfg or RetractCfg(None, None, True, True)
    current_x: Optional[float] = None
    current_z: Optional[float] = None
    start_rx, start_rz = resolve_retract_targets(
        cfg,
        external=external,
        current_x=x_stock,
        current_z=safe_z,
        safe_z=safe_z,
    )
    if start_rz is not None:
        lines.append(f"G0 Z{start_rz:.3f}")
        current_z = start_rz
    if start_rx is not None:
        lines.append(f"G0 X{start_rx:.3f}")
        current_x = start_rx

    z_dir = infer_z_dir_from_path(path)
    for pass_i, (x_hi, x_lo) in enumerate(passes, 1):
        band_lo, band_hi = (x_lo, x_hi) if x_lo <= x_hi else (x_hi, x_lo)
        x_cut = x_lo if external else x_hi
        eps_band = 1e-3
        z_intervals: List[Tuple[float, float, Segment]] = []
        for s in segs:
            hit = intersect_segment_with_x_band(s, x_cut - eps_band, x_cut + eps_band)
            if hit:
                z_intervals.append((hit[0], hit[1], s))
        if not z_intervals:
            lines.append(f"(Pass {pass_i}: no cut region in band X[{band_lo:.3f},{band_hi:.3f}])")
            continue

        lines.append(f"(Pass {pass_i}: X-band [{band_lo:.3f},{band_hi:.3f}])")

        for (za, zb, seg) in z_intervals:
            if abs(zb - za) < 1e-9:
                # Degeneriertes Intervall -> kein Schnitt notwendig
                continue
            x_cut = x_lo if external else x_hi
            if not allow_undercut and min_x is not None and max_x is not None:
                eps = 1e-6
                if external and x_cut < min_x - eps:
                    continue
                if (not external) and x_cut > max_x + eps:
                    continue

            emit_g0(lines, x=x_cut, z=safe_z)
            current_x = x_cut
            current_z = safe_z

            z_low = min(za, zb)
            z_high = max(za, zb)
            z_entry, z_exit = pick_entry_exit(z_low, z_high, z_dir)
            if abs(current_z - z_entry) > 1e-9:
                lines.append(f"G1 Z{z_entry:.3f} F{feed:.3f}")
                current_z = z_entry

            if pause_enabled and pause_distance > 0 and abs(z_entry - z_exit) > pause_distance:
                lines.append(
                    "o<step_line_pause> call "
                    f"[{x_cut:.3f}] [{z_entry:.3f}] [{x_cut:.3f}] [{z_exit:.3f}] "
                    f"[{pause_distance:.3f}] [{feed:.3f}] [{pause_duration:.3f}]"
                )
            else:
                if abs(current_z - z_exit) > 1e-9:
                    lines.append(f"G1 Z{z_exit:.3f} F{feed:.3f}")
                    current_z = z_exit
            current_z = z_exit

            found = _find_contour_at_z_in_band(
                segs,
                z_exit,
                x_lo=band_lo,
                x_hi=band_hi,
                prefer_high_x=external,
            )
            leadout_len = max(leadout_length, 0.0)
            if found:
                contour_pt, seg_idx, t0 = found
                x_c, z_c = contour_pt
                if external and x_c < x_cut - 1e-6:
                    found = None
                if (not external) and x_c > x_cut + 1e-6:
                    found = None
            if found:
                contour_pt, seg_idx, t0 = found
                x_c, z_c = contour_pt
                if abs(x_c - current_x) > 1e-9:
                    lines.append(f"G1 X{x_c:.3f} F{feed:.3f}")
                    current_x = x_c
                current_z = z_exit
                if leadout_len > 1e-9:
                    seg = segs[seg_idx]
                    direction = pick_leadout_step_direction(seg.x1 - seg.x0, seg.z1 - seg.z0, z_dir, external)
                    leadout_point = _advance_along_polyline(segs, seg_idx, t0, leadout_len, direction)
                    if abs(leadout_point[0] - current_x) > 1e-9 or abs(leadout_point[1] - current_z) > 1e-9:
                        lines.append(f"G1 X{leadout_point[0]:.3f} Z{leadout_point[1]:.3f} F{feed:.3f}")
                        current_x, current_z = leadout_point
            else:
                current_x = x_cut
                current_z = z_exit

            rx_eff, rz_eff = resolve_retract_targets(
                cfg,
                external=external,
                current_x=current_x,
                current_z=current_z,
                safe_z=safe_z,
            )
            emit_g0(lines, x=rx_eff, z=rz_eff)
            if rx_eff is not None:
                current_x = rx_eff
            if rz_eff is not None:
                current_z = rz_eff

    return lines


def rough_turn_parallel_z(
    path: List[Point],
    external: bool,
    z_stock: float,
    z_target: float,
    step_z: float,
    safe_z: float,
    feed: float,
    start_x: float,
    allow_undercut: bool = False,
    pause_enabled: bool = False,
    pause_distance: float = 0.0,
    pause_duration: float = 0.5,
    leadout_length: float = LEADOUT_LENGTH_DEFAULT,
    retract_cfg: Optional[RetractCfg] = None,
) -> List[str]:
    """Parallel to X (horizontal bands)."""
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
    lines.append("(ABSPANEN Rough - parallel X)")
    if not passes:
        return lines

    cfg = retract_cfg or RetractCfg(None, None, True, True)

    current_x = start_x
    current_z = safe_z
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append(f"G0 X{start_x:.3f}")
    had_pass = False

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
        pass_cut = False
        for (xa, xb) in x_work:
            if not allow_undercut and min_x is not None and max_x is not None:
                eps = 1e-6
                if xb < min_x - eps or xa > max_x + eps:
                    continue

            if not pass_cut:
                pass_cut = True
                had_pass = True
                # Reposition to the band's start X without climbing all the way up
                # to the absolute safe Z; incremental offsets keep the travel short.
                if current_x != start_x:
                    lines.append(f"G0 X{start_x:.3f}")
                    current_x = start_x

            lines.append(f"G1 Z{band_lo:.3f} F{feed:.3f}")
            current_z = band_lo
            # For external stock we must cut toward the center (decreasing X):
            # choose the interval endpoint that is closer to the center (smaller X).
            # For internal stock the opposite applies (choose larger X).
            cut_target = min(xa, xb) if external else max(xa, xb)
            _emit_segment_with_pauses(
                lines,
                (current_x, current_z),
                (cut_target, band_lo),
                feed,
                pause_enabled=pause_enabled,
                pause_distance=pause_distance,
                pause_duration=pause_duration,
            )
            current_x = cut_target

            rx_eff, rz_eff = resolve_retract_targets(
                cfg,
                external=external,
                current_x=current_x,
                current_z=band_lo,
                safe_z=safe_z,
            )
            emit_g0(lines, x=rx_eff, z=rz_eff)
            if rz_eff is not None:
                current_z = rz_eff
            if rx_eff is not None:
                current_x = rx_eff

    if had_pass and (current_x != start_x or current_z != safe_z):
        if current_z != safe_z:
            lines.append(f"G0 Z{safe_z:.3f}")
        if current_x != start_x:
            lines.append(f"G0 X{start_x:.3f}")
    return lines

# ----------------------------------------------------------------------
# Abspanen (Parting) generator helpers
# ----------------------------------------------------------------------

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



def gcode_from_primitives(
    primitives: List[Dict[str, object]],
    *,
    start: Tuple[float, float],
    feed: float,
    safe_z: float,
) -> List[str]:
    """
    Generate G-Code from a primitive list:
      - {"type":"line","end":(x,z)}
      - {"type":"arc","end":(x,z),"center":(cx,cz),"ccw":bool}
    Uses I/K center offsets (LinuxCNC-friendly).
    """
    lines: List[str] = []
    if not primitives:
        return lines

    x0, z0 = float(start[0]), float(start[1])
    lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
    lines.append(f"G1 Z{z0:.3f} F{feed:.3f}")

    cur_x, cur_z = x0, z0
    for pr in primitives:
        typ = pr.get("type")
        if typ == "line":
            x, z = pr.get("end", (cur_x, cur_z))
            x, z = float(x), float(z)
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            cur_x, cur_z = x, z
            continue

        if typ == "arc":
            x, z = pr.get("end", (cur_x, cur_z))
            cx, cz = pr.get("center", (cur_x, cur_z))
            x, z, cx, cz = float(x), float(z), float(cx), float(cz)

            i = cx - cur_x
            k = cz - cur_z
            g = "G3" if pr.get("ccw") else "G2"
            lines.append(f"{g} X{x:.3f} Z{z:.3f} I{i:.3f} K{k:.3f}")
            cur_x, cur_z = x, z
            continue

        # unknown primitive → treat as line to "end" if present
        end = pr.get("end")
        if end and isinstance(end, (tuple, list)) and len(end) >= 2:
            x, z = float(end[0]), float(end[1])
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            cur_x, cur_z = x, z

    return lines


def _contour_retract_positions(
    settings: Dict[str, object],
    side_idx: int,
    fallback_x: Optional[float],
    fallback_z: Optional[float],
) -> Tuple[Optional[float], Optional[float]]:
    """Return (retract_x, retract_z) using settings or fallbacks.

    This mirrors the logic previously in the handler and is useful for CAM
    operations that need to pick a safe retract point based on program
    settings.
    """
    def _pick(candidate: object, default: Optional[float]) -> Optional[float]:
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


def get_retract_cfg(settings: Dict[str, object], side_idx: int) -> RetractCfg:
    x, z = _contour_retract_positions(settings, side_idx, None, None)
    if side_idx == 0:
        x_abs = bool(settings.get("xra_absolute", False))
        z_abs = bool(settings.get("zra_absolute", False))
    else:
        x_abs = bool(settings.get("xri_absolute", False))
        z_abs = bool(settings.get("zri_absolute", False))
    return RetractCfg(x_value=x, z_value=z, x_absolute=x_abs, z_absolute=z_abs)


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

    This consolidates the previous handler behavior and uses the band helpers
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

    stock_hint = settings.get("xa") if side_idx == 0 else settings.get("xi")
    stock_from_settings = stock_hint is not None
    try:
        stock_x = float(stock_hint) if stock_hint is not None else None
    except Exception:
        stock_x = None
    path_xs = [point[0] for point in path] if path else []
    if stock_x is None:
        stock_x = max(path_xs) if path_xs else 0.0

    # band arguments
    cfg = get_retract_cfg(settings, side_idx)
    if cfg.x_value is None or float(cfg.x_value) == 0.0:
        raise ValueError("XRA/XRI ist nicht gesetzt (oder 0). Bitte im Programm-Tab eintragen.")
    if cfg.z_value is None or float(cfg.z_value) == 0.0:
        raise ValueError("ZRA/ZRI ist nicht gesetzt (oder 0). Bitte im Programm-Tab eintragen.")
    safe_z = float(cfg.z_value)

    offsets = _abspanen_offsets(stock_x, path, depth_per_pass)

    slice_strategy = p.get("slice_strategy")
    slice_step = depth_per_pass if depth_per_pass > 0.0 else 1.0
    allow_undercut = bool(p.get("allow_undercut", False))
    external = side_idx == 0
    leadout_length = max(float(p.get("leadout_length", LEADOUT_LENGTH_DEFAULT)), 0.0)

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
            start_x=stock_x if external else (min(path_xs) if path_xs and not stock_from_settings else stock_x),
            allow_undercut=allow_undercut,
            pause_enabled=pause_enabled,
            pause_distance=pause_distance,
            pause_duration=pause_duration,
            retract_cfg=cfg,
            leadout_length=leadout_length,
        )
        # sicherstellen, dass der Header den gewählten Richtungsmodus widerspiegelt
        if rough_lines:
            rough_lines[0] = "(ABSPANEN Rough - parallel X)"
        lines.extend(rough_lines)
        # document effective slice step in output for traceability
        lines.insert(1, f"#<_depth_per_pass> = {depth_per_pass:.3f}")
        lines.insert(2, f"#<_slice_step> = {slice_step:.3f}")

        # Finish optional (Kontur 1x)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            for (x, z) in path:
                lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

        return lines

    if strategy_code == "parallel_z":
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
            retract_cfg=cfg,
            leadout_length=leadout_length,
        )
        if rough_lines:
            rough_lines[0] = "(ABSPANEN Rough - parallel Z)"
        lines.extend(rough_lines)
        # document effective slice step in output for traceability
        lines.insert(1, f"#<_depth_per_pass> = {depth_per_pass:.3f}")
        lines.insert(2, f"#<_slice_step> = {slice_step:.3f}")

        # Finish optional (Kontur 1x)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            for (x, z) in path:
                lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

        return lines

    # No direction selected
    if mode_idx == 0:
        lines.append("(WARN: Abspanen-Schruppen ohne Bearbeitungsrichtung ist deaktiviert)")
        lines.append("(      Bitte in 'Abspanen -> Bearbeitungsrichtung' Parallel X oder Parallel Z wählen.)")
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
