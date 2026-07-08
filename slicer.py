"""Helpers for parting roughing (parallel X / parallel Z) and G-code generation."""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import math
import re
from lathe_easystep.gcode_drill import DRILL_MODE_MAP, generate_drill_gcode
from lathe_easystep.gcode_face import generate_face_gcode
from lathe_easystep.gcode_groove import generate_groove_gcode, groove_sub_definition
from lathe_easystep.gcode_keyway import generate_keyway_gcode
from lathe_easystep.gcode_thread import generate_thread_gcode
from lathe_easystep.model import OpType, Operation

Point = Tuple[float, float]  # (x, z)


def require(params: Dict[str, object], keys: List[str], op_label: str) -> None:
    """Validate that required parameters are present and valid."""
    for key in keys:
        if key not in params:
            raise ValueError(f"Fehler in Operation {op_label}: Pflicht-Parameter fehlt: '{key}'. Bitte im Handler/UI bei dieser Operation nachtragen.")
        v = params[key]
        if v is None or v == "":
            raise ValueError(f"Fehler in Operation {op_label}: Pflicht-Parameter ist leer: '{key}'. Bitte im Handler/UI bei dieser Operation nachtragen.")


def require_positive(params: Dict[str, object], keys: List[str], op_label: str) -> None:
    """Validate that parameters are positive numbers."""
    for key in keys:
        try:
            val = float(params.get(key, 0))
            if val <= 0:
                raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' muss > 0 sein (aktuell: {val}). Bitte im Handler/UI bei dieser Operation nachtragen.")
        except (ValueError, TypeError):
            raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' ist keine gültige positive Zahl. Bitte im Handler/UI bei dieser Operation nachtragen.")


def _get_tool_number(params: Dict[str, object]) -> int:
    """Extract tool number from params, supporting legacy keys."""
    for key in ("tool", "toolno", "tool_number"):
        if key in params and params.get(key) not in (None, ""):
            try:
                return int(float(params.get(key, 0)))
            except Exception:
                return 0
    return 0


def require_tool(params: Dict[str, object], op_label: str) -> int:
    """Validate that a tool number is present and > 0."""
    tool_num = _get_tool_number(params)
    if tool_num <= 0:
        raise ValueError(f"Fehler in Operation {op_label}: Werkzeug fehlt/ungueltig (tool). Bitte im Handler/UI nachtragen.")
    return tool_num


def is_monotonic_z_decreasing(path: List[Point]) -> bool:
    """Check if Z coordinates are monotonically decreasing (for G71)."""
    if len(path) < 2:
        return True
    return all(z1 >= z2 for (_, z1), (_, z2) in zip(path, path[1:]))


def is_monotonic_x_decreasing(path: List[Point]) -> bool:
    """Check if X coordinates are monotonically decreasing (for G72)."""
    if len(path) < 2:
        return True
    return all(x1 >= x2 for (x1, _), (x2, _) in zip(path, path[1:]))


def is_monotonic_x_increasing(path: List[Point]) -> bool:
    """Check if X coordinates are monotonically increasing."""
    if len(path) < 2:
        return True
    return all(x1 <= x2 for (x1, _), (x2, _) in zip(path, path[1:]))


def is_monotonic_x(path: List[Point]) -> bool:
    """Check if X coordinates are monotonic in either direction."""
    return is_monotonic_x_decreasing(path) or is_monotonic_x_increasing(path)


def primitives_to_points(primitives: List[Dict[str, object]]) -> List[Point]:
    """Convert contour primitives to a list of points."""
    points = []
    for pr in primitives:
        if pr.get("type") == "line":
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            if p1 and p2:
                points.append(tuple(p1))
                points.append(tuple(p2))
        elif pr.get("type") == "arc":
            # For arcs, add start and end points
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            if p1 and p2:
                points.append(tuple(p1))
                points.append(tuple(p2))
    return points


REQUIRED_KEYS = {
    OpType.FACE: ["depth_max", "feed", "spindle", "tool"],
    OpType.CONTOUR: [],  # Nur Geometrie, keine Bearbeitung
    OpType.TURN: ["feed", "safe_z", "tool"],
    OpType.BORE: ["feed", "safe_z", "tool"],
    OpType.THREAD: ["pitch", "length", "major_diameter", "spindle", "tool"],
    OpType.GROOVE: ["feed", "safe_z", "tool"],
    OpType.DRILL: ["feed", "safe_z", "tool"],
    OpType.KEYWAY: ["depth_per_pass", "feed", "safe_z", "tool"],
    OpType.ABSPANEN: ["depth_per_pass", "tool"],
}
STANDARD_METRIC_THREAD_SPECS: List[Tuple[str, float, float]] = [
    ("M2", 2.0, 0.4),
    ("M2.5", 2.5, 0.45),
    ("M3", 3.0, 0.5),
    ("M3.5", 3.5, 0.6),
    ("M4", 4.0, 0.7),
    ("M5", 5.0, 0.8),
    ("M6", 6.0, 1.0),
    ("M7", 7.0, 1.0),
    ("M8", 8.0, 1.25),
    ("M9", 9.0, 1.25),
    ("M10", 10.0, 1.5),
    ("M11", 11.0, 1.5),
    ("M12", 12.0, 1.75),
    ("M13", 13.0, 1.75),
    ("M14", 14.0, 2.0),
    ("M15", 15.0, 2.0),
    ("M16", 16.0, 2.0),
    ("M17", 17.0, 2.0),
    ("M18", 18.0, 2.5),
    ("M19", 19.0, 2.5),
    ("M20", 20.0, 2.5),
    ("M21", 21.0, 2.5),
    ("M22", 22.0, 2.5),
    ("M23", 23.0, 3.0),
    ("M24", 24.0, 3.0),
    ("M25", 25.0, 3.0),
]
STANDARD_TR_THREAD_SPECS: List[Tuple[str, float, float]] = [
    ("Tr 10", 10.0, 2.0),
    ("Tr 12", 12.0, 3.0),
    ("Tr 14", 14.0, 3.0),
    ("Tr 16", 16.0, 4.0),
    ("Tr 18", 18.0, 4.0),
    ("Tr 20", 20.0, 4.0),
    ("Tr 22", 22.0, 5.0),
    ("Tr 24", 24.0, 5.0),
    ("Tr 26", 26.0, 5.0),
    ("Tr 28", 28.0, 5.0),
    ("Tr 30", 30.0, 6.0),
    ("Tr 32", 32.0, 6.0),
    ("Tr 36", 36.0, 6.0),
    ("Tr 40", 40.0, 7.0),
    # Zusätzliche TR-Größen (erweiterte Auswahl)
    ("Tr 45", 45.0, 7.0),
    ("Tr 50", 50.0, 8.0),
    ("Tr 55", 55.0, 8.0),
    ("Tr 60", 60.0, 10.0),
]
THREAD_ORIENTATION_LABELS: Tuple[str, str] = ("Aussen", "Innen")
DRILL_MODE_LABELS: Tuple[str, str, str] = (
    "Normal",
    "Spanbruch",
    "Spanbruch + Rückzug",
)


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
    pause_state: Dict[str, object] | None = None,
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
    pause_state: Dict[str, object] | None = None,
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
                state=pause_state,
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


def gcode_for_turn(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    settings = settings or {}
    p = op.params
    require_tool(p, "TURN")
    path = op.path or []
    if not path:
        return []
    feed = float(p.get("feed", 0.2))
    safe_z = float(p.get("safe_z", 2.0))
    lines: List[str] = []
    _append_tool_and_spindle(lines, _get_tool_number(p), p.get("spindle"), settings)
    if bool(p.get("coolant", False)):
        lines.append("M8")
    lines.extend(gcode_from_path(path, feed, safe_z))
    return lines


def gcode_for_bore(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    settings = settings or {}
    p = op.params
    require_tool(p, "BORE")
    path = op.path or []
    if not path:
        return []
    feed = float(p.get("feed", 0.15))
    safe_z = float(p.get("safe_z", 2.0))
    lines: List[str] = []
    _append_tool_and_spindle(lines, _get_tool_number(p), p.get("spindle"), settings)
    if bool(p.get("coolant", False)):
        lines.append("M8")
    lines.extend(gcode_from_path(path, feed, safe_z))
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
            # builder primitives use 'p2' as the end point, legacy code used 'end'
            if "p2" in pr:
                x, z = pr["p2"]
            else:
                x, z = pr.get("end", (cur_x, cur_z))
            x, z = float(x), float(z)
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            cur_x, cur_z = x, z
            continue

        if typ == "arc":
            # end point may be stored in 'p2' or in legacy 'end'
            if "p2" in pr:
                x, z = pr["p2"]
            else:
                x, z = pr.get("end", (cur_x, cur_z))
            # primitives stored center as 'c' in build_contour_path; legacy code expected 'center'
            center = pr.get("center") if pr.get("center") is not None else pr.get("c")
            if center is None:
                center = (cur_x, cur_z)
            cx, cz = center
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


def contour_sub_from_points(points: List[Point], sub_num: int) -> List[str]:
    """Create a contour subroutine using G1-only line segments."""
    lines: List[str] = [f"o{sub_num} sub"]
    if not points:
        lines.append(f"o{sub_num} endsub")
        return lines
    prev: Optional[Point] = None
    for x, z in points:
        if prev is None or (abs(prev[0] - x) > 1e-9 or abs(prev[1] - z) > 1e-9):
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            prev = (x, z)
    lines.append(f"o{sub_num} endsub")
    return lines


def contour_sub_from_primitives(primitives: List[Dict[str, object]], sub_num: int) -> List[str]:
    """Create a contour subroutine using G1/G2/G3 only (XZ plane, I/K arcs)."""
    lines: List[str] = [f"o{sub_num} sub"]
    if not primitives:
        lines.append(f"o{sub_num} endsub")
        return lines
    cur_x: Optional[float] = None
    cur_z: Optional[float] = None

    def _ensure_at(x: float, z: float) -> None:
        nonlocal cur_x, cur_z
        if cur_x is None or cur_z is None or abs(cur_x - x) > 1e-9 or abs(cur_z - z) > 1e-9:
            lines.append(f"G1 X{x:.3f} Z{z:.3f}")
            cur_x, cur_z = x, z

    for pr in primitives:
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
            continue

        if typ == "arc":
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
            continue

    lines.append(f"o{sub_num} endsub")
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


def _mark_step_line_pause(state: Dict[str, object] | None) -> None:
    if state is not None:
        state["needs_step_line_pause_sub"] = True


def _step_line_pause_sub_definition() -> List[str]:
    return [
        "o<step_line_pause> sub",
        "(Step line pause helper)",
        "G4 P[#7]",
        "o<step_line_pause> endsub",
    ]


# --- PHASE A: G0-Sicherheit für Außen/Innendrehen ---
# Tracker für aktuellen Zustand des Werkzeugs relativ zum Werkstück
class SafetyContext:
    """Verfolgt, ob das Werkzeug sicher vom Material entfernt ist."""
    def __init__(self, side_idx: int = 0, safe_z: float = 2.0):
        """side_idx: 0=Außendrehen, 1=Innendrehen; safe_z: Sicherheitspositin in Z"""
        self.side_idx = side_idx
        self.safe_z = safe_z
        self.is_safe = False  # Initial: nicht sicher (bis erste Anfahrt)
        
    def mark_safe_z(self):
        """Markiere: Werkzeug ist bei safe_z (Z sicherheitsposition)"""
        self.is_safe = True
        
    def mark_unsafe(self):
        """Markiere: Werkzeug ist beim Werkstück (nicht sicher)"""
        self.is_safe = False
        
    def is_x_move_safe(self, current_x: float, target_x: float) -> bool:
        """Prüfe, ob G0 von current_x zu target_x sicher ist.
        
        Außendrehen (side_idx=0):
            Material bei großem X
            Sicher wenn: target_x >= current_x (weg vom Material)
            
        Innendrehen (side_idx=1):
            Material bei kleinem X
            Sicher wenn: target_x <= current_x (weg vom Material)
        """
        if not self.is_safe:
            # Wenn nicht bei safe_z, muss zuerst Z sicher sein
            return False
            
        if self.side_idx == 0:  # Außendrehen
            # Material bei großem X, sicher wenn target >= current (weg)
            return target_x >= current_x
        else:  # Innendrehen
            # Material bei kleinem X, sicher wenn target <= current (weg)
            return target_x <= current_x


def emit_g0_safe(
    x: Optional[float] = None,
    z: Optional[float] = None,
    safety: SafetyContext = None,
    current_x: float = 0.0,
    label: str = "(G0)"
) -> List[str]:
    """Emittiert sichere G0-Bewegungen mit Validierung für Außen/Innendrehen.
    
    Wenn nur Z bewegt wird → immer safe
    Wenn X bewegt wird → prüfe material-safety mit SafetyContext
    Falls unsicher → Fehler + Kommentar
    """
    lines: List[str] = []
    
    if safety is None:
        # Kein Safety-Context → einfach emit (Legacy-Mode)
        if z is not None:
            lines.append(f"G0 Z{z:.3f}  {label}")
            return lines
        if x is not None:
            lines.append(f"G0 X{x:.3f}  {label}")
            return lines
        return lines
    
    # Mit SafetyContext: prüfe X-Bewegungen
    if x is not None and z is None:
        # Nur X-Bewegung
        if not safety.is_x_move_safe(current_x, x):
            lines.append(f"(ERROR: G0 X{x:.3f} nicht sicher bei side={safety.side_idx})")
            lines.append(f"(       Aktuell X={current_x:.3f}, sicher zum Material weg)")
            return lines
        lines.append(f"G0 X{x:.3f}  {label}")
        safety.mark_unsafe()  # X-Bewegung → evtl. näher am Material
        return lines
    
    if z is not None and x is None:
        # Nur Z-Bewegung
        lines.append(f"G0 Z{z:.3f}  {label}")
        if abs(z - safety.safe_z) < 0.01:
            safety.mark_safe_z()  # Bei safe_z → markiere sicher
        else:
            safety.mark_unsafe()  # Nicht bei safe_z → unsicher
        return lines
    
    if x is not None and z is not None:
        # X und Z zusammen → Z hat Vorrang
        # Z zuerst emittieren, dann X
        lines.append(f"G0 Z{z:.3f}  {label}")
        safety.mark_safe_z()
        lines.append(f"G0 X{x:.3f}")
        if not safety.is_x_move_safe(current_x, x):
            lines[-1] = f"(ERROR: G0 X{x:.3f} nicht sicher) {lines[-1]}"
        else:
            safety.mark_unsafe()
        return lines
    
    return lines


def _step_x_pause_sub_definition() -> List[str]:
    return [
        "o<step_x_pause> sub",
        "(Step X pause helper)",
        "G4 P0.1",
        "o<step_x_pause> endsub",
    ]


def _emit_segment_with_pauses(
    lines: List[str],
    start: Point,
    end: Point,
    feed: float,
    pause_enabled: bool,
    pause_distance: float,
    pause_duration: float,
    state: Dict[str, object] | None = None,
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
        _mark_step_line_pause(state)
        return

    lines.append(f"G1 X{x1:.3f} Z{z1:.3f} F{feed:.3f}")


def _gcode_for_abspanen_pass(
    path: List[Point],
    feed: float,
    safe_z: float,
    pause_enabled: bool,
    pause_distance: float,
    pause_duration: float,
    state: Dict[str, object] | None = None,
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
            lines,
            prev,
            point,
            feed,
            pause_enabled,
            pause_distance,
            pause_duration,
            state=state,
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

    # Strenge Validierung: depth_per_pass ist Pflicht
    require(p, ["depth_per_pass"], "ABSPANEN")
    require_positive(p, ["depth_per_pass"], "ABSPANEN")

    side_idx = int(p.get("side", 0))
    feed = float(p.get("feed", 0.15))
    depth_per_pass = float(p["depth_per_pass"])  # Jetzt garantiert vorhanden und positiv
    pause_enabled = bool(p.get("pause_enabled", False))
    pause_distance = max(float(p.get("pause_distance", 0.0)), 0.0)
    pause_duration = 0.5
    mode_idx = int(p.get("mode", 0))  # 0=Schruppen, 1=Schlichten
    if pause_enabled and pause_distance > 0.0 and mode_idx in (0, 2):
        settings["needs_step_line_pause_sub"] = True

    # finish allowance values (used for comment and radial adjustment)
    finish_allow_x = max(float(p.get("finish_allow_x", 0.0)), 0.0)
    finish_allow_z = max(float(p.get("finish_allow_z", 0.0)), 0.0)
    if finish_allow_x > 0.0 or finish_allow_z > 0.0:
        lines.append(f"(Schlichtaufmaß X/Z: {finish_allow_x:.3f}/{finish_allow_z:.3f} mm)")

    # harte Sicherung: Unterbrechung nur beim Schruppen
    if mode_idx != 0:
        pause_enabled = False

    tool_num = require_tool(p, "ABSPANEN")
    spindle = float(p.get("spindle", 0.0))
    coolant_enabled = bool(p.get("coolant", False))

    # --- Tool/Spindle/Coolant/Feed Rahmen am Anfang ---
    _append_tool_and_spindle(lines, tool_num, spindle, settings)
    coolant_mode = p.get("coolant_mode", p.get("coolant", False))
    _emit_coolant(lines, coolant_mode)
    # Set feedrate (required for contour in sub)
    lines.append(f"F{feed:.3f}")

    stock_hint = settings.get("xa") if side_idx == 0 else settings.get("xi")
    stock_from_settings = stock_hint is not None
    try:
        stock_x = float(stock_hint) if stock_hint is not None else None
    except Exception:
        stock_x = None
    path_xs = [point[0] for point in path] if path else []
    if stock_x is None:
        stock_x = max(path_xs) if path_xs else 0.0

    # radial finish allowance modifies the effective stock diameter used by the
    # roughing cycle: start a little short so the final pass leaves the allowance.
    stock_x_adj = stock_x
    if mode_idx == 0 and finish_allow_x > 0.0:
        stock_x_adj = stock_x - finish_allow_x
        # ensure we don't go negative
        stock_x_adj = max(stock_x_adj, 0.0)

    # band arguments
    cfg = get_retract_cfg(settings, side_idx)
    if cfg.x_value is None or float(cfg.x_value) == 0.0:
        raise ValueError("XRA/XRI ist nicht gesetzt (oder 0). Bitte im Programm-Tab eintragen.")
    if cfg.z_value is None or float(cfg.z_value) == 0.0:
        raise ValueError("ZRA/ZRI ist nicht gesetzt (oder 0). Bitte im Programm-Tab eintragen.")
    safe_z = float(cfg.z_value)

    offsets = _abspanen_offsets(stock_x, path, depth_per_pass)

    slice_strategy = p.get("slice_strategy")
    slice_step = depth_per_pass  # Kein Fallback mehr, depth_per_pass ist garantiert > 0
    allow_undercut = bool(p.get("allow_undercut", False))
    external = side_idx == 0
    tool_info = (settings.get("tools", {}) or {}).get(tool_num)
    compensation_command = _nose_compensation_command(tool_info, external)
    nose_disabled = bool(p.get("nose_comp_disabled", False))
    nose_reason = str(p.get("nose_comp_reason", "") or "").strip()
    if nose_disabled:
        reason = nose_reason if nose_reason else "Benutzerentscheidung"
        lines.append(f"(Nose compensation deaktiviert: {_sanitize_comment_text(reason)})")
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

    contour_name = p.get("contour_name")
    contour_subs = settings.get("contour_subs", {}) if settings else {}
    contour_sub_num = contour_subs.get(contour_name) if contour_name else None
    # Primitives (with arcs) for cycle subroutines - prefer over points
    primitives = p.get("_primitives")

    def _build_cycle_sub(sub_num: int) -> List[str]:
        """Build a cycle subroutine from primitives (G1/G2/G3) or points (G1 only)."""
        if primitives:
            return contour_sub_from_primitives(primitives, sub_num)
        return contour_sub_from_points(path, sub_num)

    if strategy_code == "parallel_x":
        if is_monotonic_x_decreasing(path):
            allocator = settings.get("sub_allocator")
            sub_num = contour_sub_num if contour_sub_num is not None else (allocator.allocate() if allocator else 100)
            lines.append("(ABSPANEN Rough - parallel X)")
            if contour_sub_num is None:
                lines.extend(_build_cycle_sub(sub_num))
            lines.append("(Anfahren vor Zyklus)")
            # use adjusted stock for approach too so cycle begins inside allowance
            _emit_approach(lines, stock_x_adj, safe_z, settings)
            # use adjusted X value for rough cycle if mode is rough
            x_cycle = stock_x_adj if mode_idx == 0 else stock_x
            lines.append(f"G72 Q{sub_num} X{x_cycle:.3f} Z{safe_z:.3f} D{depth_per_pass:.3f}")
            if mode_idx in (1, 2):
                lines.append(f"G70 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f}")
            # global safe retract after step
            return lines
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
            pause_state=settings,
        )
        if rough_lines:
            rough_lines[0] = "(ABSPANEN Rough - parallel X - Move-based)"
        lines.extend(rough_lines)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            if compensation_command and not nose_disabled:
                lines.append(compensation_command)
            prev_point = None
            for (x, z) in path:
                current_point = (x, z)
                if current_point != prev_point:
                    lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
                    prev_point = current_point
            lines.append(f"G0 Z{safe_z:.3f}")
            if compensation_command and not nose_disabled:
                lines.append("G40")  # Cancel compensation
        return lines

    if strategy_code == "parallel_z":
        can_use_g71 = is_monotonic_z_decreasing(path) and is_monotonic_x(path)
        if can_use_g71:
            if external and any(float(x) > float(stock_x) + 1e-9 for x, _ in path):
                can_use_g71 = False

        if can_use_g71:
            allocator = settings.get("sub_allocator")
            sub_num = contour_sub_num if contour_sub_num is not None else (allocator.allocate() if allocator else 100)
            lines.append("(ABSPANEN Rough - parallel Z)")
            if contour_sub_num is None:
                lines.extend(_build_cycle_sub(sub_num))
            _emit_approach(lines, stock_x, safe_z, settings)
            lines.append(f"G71 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f} D{depth_per_pass:.3f}")
            if mode_idx in (1, 2):
                lines.append(f"G70 Q{sub_num} X{stock_x:.3f} Z{safe_z:.3f}")
            # global safe retract after step
            return lines

        lines.append("(Info: G71 deaktiviert - Kontur nicht zyklustauglich, nutze Move-based Roughing)")

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
            pause_state=settings,
        )
        if rough_lines:
            rough_lines[0] = "(ABSPANEN Rough - parallel Z - Move-based)"
        lines.extend(rough_lines)
        if mode_idx in (1, 2):
            lines.append("(Schlichtschnitt Kontur)")
            lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
            if compensation_command and not nose_disabled:
                lines.append(compensation_command)
            for (x, z) in path:
                lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")
            if compensation_command and not nose_disabled:
                lines.append("G40")  # Cancel compensation
        return lines

    # No direction selected
    if mode_idx == 0:
        lines.append("(WARN: Abspanen-Schruppen ohne Bearbeitungsrichtung ist deaktiviert)")
        lines.append("(      Bitte in 'Abspanen -> Bearbeitungsrichtung' Parallel X oder Parallel Z wählen.)")
        return lines

    # Finish-only (mode_idx == 1) without slicing: single contour pass
    _append_tool_and_spindle(lines, tool_num, spindle, settings)

    lines.append("(Schlichtschnitt Kontur)")
    lines.append(f"G0 X{path[0][0]:.3f} Z{safe_z:.3f}")
    if compensation_command and not nose_disabled:
        lines.append(compensation_command)
    for (x, z) in path:
        lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
    lines.append(f"G0 Z{safe_z:.3f}")
    if compensation_command and not nose_disabled:
        lines.append("G40")
    return lines


# ----------------------------------------------------------------------
# G-code generation functions
# ----------------------------------------------------------------------

def _sanitize_gcode_text(text: str) -> str:
    """Ersetzt Umlaute/Akzente durch ASCII, um falsche Zeichensätze zu vermeiden."""
    translit = {
        "ä": "ae",
        "Ä": "Ae",
        "ö": "oe",
        "Ö": "Oe",
        "ü": "ue",
        "Ü": "Ue",
        "ß": "ss",
    }

    for src, repl in translit.items():
        text = text.replace(src, repl)

    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "replace").decode("ascii")


def _sanitize_comment_text(text: object) -> str:
    """Strip parentheses from comment content and normalize to ASCII."""
    raw = str(text or "")
    # Remove nested comment markers
    raw = raw.replace("(", " ").replace(")", " ")
    raw = " ".join(raw.split())
    return _sanitize_gcode_text(raw)


def _emit_coolant(lines: List[str], mode: object) -> None:
    """Emit explicit coolant state (M7/M8/M9)."""
    if isinstance(mode, str):
        m = mode.strip().lower()
        if m in ("mist", "m7"):
            lines.append("M7")
            return
        if m in ("flood", "m8", "on", "ein"):
            lines.append("M8")
            return
        if m in ("off", "aus", "m9", "0"):
            lines.append("M9")
            return
    if isinstance(mode, bool):
        lines.append("M8" if mode else "M9")
        return
    # Fallback: be explicit and safe
    lines.append("M9")


def _get_safe_position(settings: Dict[str, object] | None) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    xra = _float_or_none(settings.get("xra"))
    zra = _float_or_none(settings.get("zra"))
    if xra is None or zra is None:
        return None

    xra_absolute = bool(settings.get("xra_absolute", False))
    zra_absolute = bool(settings.get("zra_absolute", False))

    if xra_absolute:
        x_safe = xra
    else:
        xa = _float_or_none(settings.get("xa"))
        if xa is None:
            return None
        x_safe = xa + xra

    if zra_absolute:
        z_safe = zra
    else:
        za = _float_or_none(settings.get("za"))
        if za is None:
            return None
        z_safe = za + zra

    return (x_safe, z_safe)


def _emit_safe_retract(lines: List[str], settings: Dict[str, object] | None) -> None:
    _emit_safe_retract_for_op(lines, settings, None)


def _emit_safe_retract_for_op(
    lines: List[str],
    settings: Dict[str, object] | None,
    op_type: Optional[str],
    current_pos: Optional[Tuple[float, float]] = None,
) -> None:
    safe = _get_safe_position(settings)
    if not safe:
        return
    x_safe, z_safe = safe

    # Lathe-specific free-travel policy:
    # - default: simultaneous X/Z (diagonal free travel) when possible
    # - groove/keyway (Einstich): first retract in X, then move Z
    # - drill/thread: first retract in Z, then move X
    # - if current point is still inside stock envelope: no diagonal free travel
    def _inside_stock_envelope(pos: Optional[Tuple[float, float]]) -> bool:
        if pos is None or settings is None:
            return False
        xa = _float_or_none(settings.get("xa"))
        za = _float_or_none(settings.get("za"))
        zi = _float_or_none(settings.get("zi"))
        if xa is None or za is None or zi is None:
            return False
        xi = _float_or_none(settings.get("xi"))
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
        x_min = _float_or_none(settings.get("chuck_no_go_x_min"))
        x_max = _float_or_none(settings.get("chuck_no_go_x_max"))
        z_lim = _float_or_none(settings.get("chuck_no_go_z_limit"))
        if x_min is None or x_max is None or z_lim is None:
            return False
        x, z = pos
        lo = min(x_min, x_max)
        hi = max(x_min, x_max)
        eps = 1e-6
        if x < lo - eps or x > hi + eps:
            return False

        za = _float_or_none(settings.get("za"))
        if za is None:
            # project default convention: negative Z goes towards chuck
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
        # Conservative fallback for turning-like ops while still in/at stock.
        lines.append(f"G0 X{x_safe:.3f}")
        lines.append(f"G0 Z{z_safe:.3f}")
    else:
        lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")

    if settings is not None:
        settings["_is_at_safe"] = True


def _estimate_operation_end_pos(op: Operation) -> Optional[Tuple[float, float]]:
    """Best-effort estimate of the operation's last material-near point (X,Z)."""
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
        a_end = _float_or_none(p.get("A_end"))
        mode = int(_float_or_none(p.get("mode")) or 0)
        c_val = _float_or_none(p.get("C"))
        if a_end is not None and c_val is not None:
            if mode == 0:
                return (a_end, c_val)
            return (c_val, a_end)

    if op.op_type == OpType.FACE:
        x = _float_or_none(p.get("end_x"))
        z = _float_or_none(p.get("end_z"))
        if x is not None and z is not None:
            return (x, z)

    return None


def _emit_approach(lines: List[str], start_x: float, start_z: float, settings: Dict[str, object] | None) -> None:
    safe = _get_safe_position(settings)
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


def _float_or_none(value: object | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _append_tool_and_spindle(lines: List[str], tool_value: object | None, spindle_value: object | None, settings: Dict[str, object] | None = None):
    """Append tool and spindle commands, tracking tool state to avoid redundant changes."""
    if tool_value is None and settings is not None:
        tool_num = _get_tool_number(settings)
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
                safe = _get_safe_position(settings)
                if safe and not settings.get("_is_at_safe"):
                    x_safe, z_safe = safe
                    lines.append(f"G0 Z{z_safe:.3f}")
                    lines.append(f"G0 X{x_safe:.3f}")
                    settings["_is_at_safe"] = True
                # Coolant off before toolchange
                lines.append("M9")
                if not skip_tool_move:
                    toolchange_lines = move_to_toolchange_pos(settings)
                    lines.extend(toolchange_lines)
            lines.append(f"T{tool_num:02d} M6")
            if settings is not None:
                settings["_current_tool"] = tool_num
                safe = _get_safe_position(settings)
                if safe:
                    x_safe, z_safe = safe
                    lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")
                    settings["_is_at_safe"] = True

    rpm = _float_or_none(spindle_value)
    if rpm and rpm > 0:
        rpm_value = int(round(rpm))
        if rpm_value > 0:
            lines.append(f"S{rpm_value} M3")


def _nose_compensation_command(tool_info: Dict[str, object] | None, external: bool) -> Optional[str]:
    if not tool_info:
        return None
    radius = _float_or_none(tool_info.get("radius_mm"))
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
    xt = _float_or_none(settings.get("xt"))
    zt = _float_or_none(settings.get("zt"))
    if label:
        prefix = f"({label})"
    else:
        prefix = "(Toolchange move)"
    lines: List[str] = [prefix]
    if xt is None or zt is None:
        lines.append("(WARN: Toolchange position XT/ ZT nicht gesetzt)")
        return lines
    coords = f"X{xt:.3f} Z{zt:.3f}"
    lines.append(f"G53 G0 {coords}")
    return lines


def gcode_for_drill(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_drill_gcode(
        op,
        settings,
        require=require,
        require_tool=require_tool,
        get_tool_number=_get_tool_number,
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
        emit_approach=_emit_approach,
    )
def _should_activate_abstech(
    start_x: float, threshold: float, current_x: float
) -> bool:
    if start_x >= threshold:
        return current_x <= threshold
    return current_x >= threshold


def gcode_for_groove(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_groove_gcode(
        op,
        settings,
        require_tool=require_tool,
        get_tool_number=_get_tool_number,
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
    )


def gcode_for_keyway(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_keyway_gcode(
        op,
        settings,
        require=require,
        require_positive=require_positive,
    )


def gcode_for_contour(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    """Erzeugt einen G71/G70-Workflow für LinuxCNC 2.10 (Fanuc-Style)."""

    p = op.params
    name = _sanitize_comment_text(p.get("name") or "").strip()
    side_idx = int(p.get("side", 0))

    path = op.path or []
    if len(path) < 2:
        # Fallback: nur Kommentare ausgeben, wenn keine Kontur vorhanden ist
        lines: List[str] = ["(KONTUR)"]
        if name:
            lines.append(f"(Name: {name})")
        lines.append("(Keine Konturpunkte definiert)")
        return lines

    # Standardwerte gemäß LinuxCNC-Handbuch (G71/G70), solange kein eigenes UI-Feld existiert
    rough_depth = max(float(p.get("rough_depth", 0.5)), 0.05)
    retract = max(float(p.get("retract", 1.0)), 0.1)
    finish_allow_x = max(float(p.get("finish_allow_x", 0.2)), 0.0)
    finish_allow_z = max(float(p.get("finish_allow_z", 0.1)), 0.0)
    rough_feed = max(float(p.get("rough_feed", 0.25)), 0.01)
    finish_feed = max(float(p.get("finish_feed", rough_feed)), 0.01)
    safe_z = float(p.get("safe_z", 2.0))
    settings = settings or {}

    lines: List[str] = ["(KONTUR)"]
    if name:
        lines.append(f"(Name: {name})")
    lines.append("(Seite: Außen)" if side_idx == 0 else "(Seite: Innen)")
    lines.append("(Rauhen: G71, Schlichten: G70)")
    lines.append(f"(Zustellung: {rough_depth:.3f} mm, Rückzug: {retract:.3f} mm)")
    lines.append(
        f"(Schlichtaufmaß X/Z: {finish_allow_x:.3f}/{finish_allow_z:.3f} mm,"
        f" Vorschub Schruppen/Schlichten: {rough_feed:.3f}/{finish_feed:.3f})"
    )

    # Konturblöcke nummerieren, damit P/Q klar referenzierbar sind
    block_start = 500
    block_step = 10
    block_numbers = [block_start + i * block_step for i in range(len(path))]
    block_end = block_numbers[-1]

    # Anfahrbewegung und Zyklen
    xs = [p[0] for p in path]
    start_x, start_z = path[0]
    entry_x = max(xs) if side_idx == 0 else min(xs)
    retract_x, retract_z = _contour_retract_positions(
        settings, side_idx, entry_x, safe_z
    )
    safe_z = retract_z
    # Aus Sicherheits‑/Dokumentationsgründen nur kommentierte Konturinformationen ausgeben.
    # Die Kontur wird nicht als ausführbare Bewegungsfolge in den Header geschrieben.
    lines.append(f"(Sicherheitsposition aus Programm: X{retract_x:.3f} Z{retract_z:.3f})")
    lines.append(f"(Kontur-Punkte: {len(path)})")
    lines.append(f"(Startpunkt: X{start_x:.3f} Z{start_z:.3f})")
    # Listen der ersten Punkte als Kommentar (kurz und lesbar)
    sample_points = path[:5]
    for (x, z) in sample_points:
        lines.append(f"( Konturpunkt: X{x:.3f} Z{z:.3f} )")
    if len(path) > len(sample_points):
        lines.append(f"( ... +{len(path)-len(sample_points)} weitere Punkte )")

    return lines


def _contour_retract_positions(
    settings: Dict[str, object],
    side_idx: int,
    fallback_x: Optional[float],
    fallback_z: Optional[float],
) -> Tuple[Optional[float], Optional[float]]:
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



def clean_path(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Remove consecutive duplicates and simplify the path."""
    if not path:
        return path
    cleaned = [path[0]]
    for p in path[1:]:
        if p != cleaned[-1]:
            cleaned.append(p)
    return cleaned


def gcode_for_face(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_face_gcode(
        op,
        settings,
        require_tool=require_tool,
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
        emit_approach=_emit_approach,
        clean_path=clean_path,
    )

def gcode_for_thread(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_thread_gcode(
        op,
        settings,
        require_tool=require_tool,
        get_tool_number=_get_tool_number,
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
        emit_approach=_emit_approach,
        sanitize_comment_text=_sanitize_comment_text,
    )


def gcode_for_operation(
    op: Operation, settings: Dict[str, object] | None = None
) -> List[str]:
    settings = settings or {}
    if op.op_type == OpType.PROGRAM_HEADER:
        result: List[str] = []
    elif op.op_type == OpType.FACE:
        result = gcode_for_face(op, settings)
    elif op.op_type == OpType.CONTOUR:
        result = []
    elif op.op_type == OpType.TURN:
        result = gcode_for_turn(op, settings)
    elif op.op_type == OpType.BORE:
        result = gcode_for_bore(op, settings)
    elif op.op_type == OpType.DRILL:
        result = gcode_for_drill(op, settings)
    elif op.op_type == OpType.GROOVE:
        result = gcode_for_groove(op, settings)
    elif op.op_type == OpType.ABSPANEN:
        result = generate_abspanen_gcode(op.params, op.path, settings)
    elif op.op_type == OpType.THREAD:
        result = gcode_for_thread(op, settings)
    elif op.op_type == OpType.KEYWAY:
        result = gcode_for_keyway(op, settings)
    else:
        result = []

    comment = _sanitize_comment_text(op.params.get("comment") or "").strip()
    if comment:
        result.insert(0, f"(STEP: {comment})")
    return result


def generate_program_gcode(operations: List[Operation], program_settings: Dict[str, object]) -> List[str]:
    """Builds a complete LinuxCNC .ngc program from ordered operations.

    Design rules for this project:
    - Handler collects/validates user parameters.
    - ALL G-code generation is here in slicer.py.
    - The panel's step list defines the operation order; we do not reorder operations.

    LinuxCNC rule that matters here:
    - `o#### sub` definitions MUST appear BEFORE M30 (program end).
    - Subroutines are extracted from operations and placed in a definition block before main steps.
    """

    # --- Pre-generate validation: Check all operations for required parameters ---
    settings = dict(program_settings or {})
    for i, op in enumerate(operations):
        if op.op_type in REQUIRED_KEYS:
            require(op.params, REQUIRED_KEYS[op.op_type], op.op_type)
            if op.op_type in [OpType.FACE, OpType.ABSPANEN, OpType.KEYWAY, OpType.DRILL]:
                require_positive(op.params, REQUIRED_KEYS[op.op_type], op.op_type)
        try:
            gcode_for_operation(op, settings)  # This will raise ValueError if params missing
        except ValueError as e:
            # Re-raise with operation index for better error message
            raise ValueError(f"Operation {i+1} ({op.op_type}): {str(e)}") from e

    handler_header_lines: List[str] = []

    # --- Subroutine ID allocator ---
    class SubAllocator:
        def __init__(self, start: int = 100):
            self.next_id = start
        def allocate(self) -> int:
            result = self.next_id
            self.next_id += 1
            return result
    
    sub_alloc = SubAllocator()
    settings["sub_allocator"] = sub_alloc  # Pass to operation generators

    # --- header ---
    program_name = _sanitize_comment_text(settings.get("program_name", "Program"))
    unit = _sanitize_comment_text(settings.get("unit", "mm"))

    header_lines: List[str] = []
    header_lines.append("%")
    def _cmt(text: object) -> str:
        return f"({_sanitize_comment_text(text)})"

    header_lines.append(_cmt("Programm automatisch erzeugt"))
    header_lines.append(_cmt(f"Programmname: {program_name}"))
    header_lines.append(_cmt(f"Maßeinheit: {unit}"))
    handler_header_lines = [str(x) for x in settings.get("header_lines", []) or []]
    footer_lines_from_settings = [str(x) for x in settings.get("footer_lines", []) or []]
    if handler_header_lines:
        settings["_skip_tool_move"] = True

    # Modes / safety
    # G18 XZ-plane, G7 diameter mode, G90 absolute, G40 cancel comp, G80 cancel canned
    # G7 ist erforderlich, da alle X-Werte und I-Offsets als Durchmesser erzeugt werden.
    header_lines.append("G18 G7 G90 G40 G80")
    unit_norm = str(unit).strip().lower()
    is_imperial = unit_norm in ("inch", "in", "zoll", "imperial")
    header_lines.append("G20" if is_imperial else "G21")
    header_lines.append("G95")
    header_lines.append("G54")
    header_lines.append("")

    # --- PHASE 1: Security header comments (lesbar, keine Logik) ---
    header_lines.append(_cmt("=== SICHERHEITSPARAMETER ==="))
    
    # Werkzeugwechselpunkt
    xt = settings.get("xt")
    zt = settings.get("zt")
    xt_abs = settings.get("xt_absolute", True)
    zt_abs = settings.get("zt_absolute", True)
    if xt is not None and zt is not None:
        try:
            xt_val = float(xt)
            zt_val = float(zt)
            coord_note = " Maschinenkoordinaten G53" if (not xt_abs or not zt_abs) else ""
            header_lines.append(_cmt(f"Werkzeugwechselpunkt: X{xt_val:.3f} Z{zt_val:.3f}{coord_note}"))
        except (TypeError, ValueError):
            pass
    
    # Rückzugsebenen
    xra = settings.get("xra")
    xri = settings.get("xri")
    zra = settings.get("zra")
    zri = settings.get("zri")
    xra_str = f"{float(xra):.3f}" if xra is not None else "n.def."
    xri_str = f"{float(xri):.3f}" if xri is not None else "n.def."
    zra_str = f"{float(zra):.3f}" if zra is not None else "n.def."
    zri_str = f"{float(zri):.3f}" if zri is not None else "n.def."
    header_lines.append(_cmt(f"Rueckzugsebenen: XRA={xra_str} XRI={xri_str}"))
    header_lines.append(_cmt(f"               ZRA={zra_str} ZRI={zri_str}"))
    
    # Stock info (Rohteil)
    xa = settings.get("xa")
    xi = settings.get("xi")
    za = settings.get("za")
    zi = settings.get("zi")
    if xa is not None:
        try:
            xa_val = float(xa)
            header_lines.append(_cmt(f"Rohteil Aussendurchmesser: {xa_val:.3f} mm"))
        except (TypeError, ValueError):
            pass
    if za is not None and zi is not None:
        try:
            za_val = float(za)
            zi_val = float(zi)
            header_lines.append(_cmt(f"Rohteil Z-Bereich: {za_val:.3f} bis {zi_val:.3f} mm"))
        except (TypeError, ValueError):
            pass
    
    header_lines.append(_cmt("=== END SICHERHEITSPARAMETER ==="))
    header_lines.append("")

    # --- Collect ALL subroutines BEFORE main program ---
    # LinuxCNC REQUIRES subroutine definitions to appear BEFORE M30 (program end)
    all_subs: List[List[str]] = []

    def _extract_sub_blocks(block_lines: List[str]) -> List[str]:
        """Extract sub definitions from block_lines, add to all_subs, return main lines."""
        out: List[str] = []
        i = 0
        while i < len(block_lines):
            line = block_lines[i].strip()
            m = re.match(r"^o\s*<?\s*(\d+)\s*>?\s+sub\b", line, flags=re.IGNORECASE)
            if m:
                sub_block = [block_lines[i]]
                i += 1
                # collect until matching endsub
                while i < len(block_lines):
                    sub_block.append(block_lines[i])
                    if re.match(rf"^o\s*<?\s*{re.escape(m.group(1))}\s*>?\s+endsub\b", block_lines[i].strip(), flags=re.IGNORECASE):
                        i += 1
                        break
                    i += 1
                all_subs.append(sub_block)  # <-- ADD to all_subs, not footer_subs
                continue
            out.append(block_lines[i])
            i += 1
        return out

    # contour subs from contour operations (reused across steps)
    contour_subs: Dict[str, int] = {}
    contour_geom_map: Dict[tuple, int] = {}

    def _round6(val: object) -> float:
        try:
            return round(float(val), 6)
        except Exception:
            return 0.0

    def _contour_key_from_primitives(prims: List[Dict[str, object]]) -> tuple:
        key_items: List[tuple] = []
        for pr in prims:
            typ = pr.get("type")
            if typ == "line":
                p1 = pr.get("p1") or (0.0, 0.0)
                p2 = pr.get("p2") or (0.0, 0.0)
                key_items.append(
                    ("l", _round6(p1[0]), _round6(p1[1]), _round6(p2[0]), _round6(p2[1]))
                )
            elif typ == "arc":
                p1 = pr.get("p1") or (0.0, 0.0)
                p2 = pr.get("p2") or (0.0, 0.0)
                c = pr.get("c") or pr.get("center") or (0.0, 0.0)
                ccw = bool(pr.get("ccw"))
                key_items.append(
                    (
                        "a",
                        _round6(p1[0]),
                        _round6(p1[1]),
                        _round6(p2[0]),
                        _round6(p2[1]),
                        _round6(c[0]),
                        _round6(c[1]),
                        ccw,
                    )
                )
        return tuple(key_items)

    def _contour_key_from_points(points: List[Point]) -> tuple:
        return tuple((_round6(x), _round6(z)) for x, z in points)

    for op in operations:
        if op.op_type != OpType.CONTOUR:
            continue
        name = str(op.params.get("name") or "").strip()
        if not name:
            continue
        path = op.path or []
        if not path:
            continue
        if isinstance(path[0], dict):
            key = ("prims", _contour_key_from_primitives(path))
            if key in contour_geom_map:
                sub_num = contour_geom_map[key]
            else:
                sub_num = sub_alloc.allocate()
                contour_geom_map[key] = sub_num
                all_subs.append(contour_sub_from_primitives(path, sub_num))
        else:
            key = ("pts", _contour_key_from_points(path))
            if key in contour_geom_map:
                sub_num = contour_geom_map[key]
            else:
                sub_num = sub_alloc.allocate()
                contour_geom_map[key] = sub_num
                all_subs.append(contour_sub_from_points(path, sub_num))
        contour_subs[name] = sub_num

    settings["contour_subs"] = contour_subs

    # helper subs defined by settings (optional)
    helper_subs = settings.get("helper_subs", None)
    if helper_subs:
        # handler may pass already-built sub blocks (list[list[str]])
        for sb in helper_subs:
            all_subs.append([str(x) for x in sb])

    if settings.get("needs_step_line_pause_sub"):
        all_subs.append(_step_line_pause_sub_definition())
    if settings.get("needs_step_x_pause_sub"):
        all_subs.append(_step_x_pause_sub_definition())
    if any(op.op_type == OpType.GROOVE for op in operations):
        all_subs.append(groove_sub_definition())

    main_flow_lines: List[str] = []

    # --- PHASE A (Regel 1): Werkzeugwechselpunkt am Programmanfang ---
    # Header lines (if any) are inserted once; toolchange will handle TC move.
    # Insert handler header lines only when no tool is used (avoid redundant TC move)
    if handler_header_lines:
        has_tool = False
        for op in operations:
            if op.op_type in (OpType.PROGRAM_HEADER, OpType.CONTOUR):
                continue
            if _get_tool_number(op.params) > 0:
                has_tool = True
                break
        if not has_tool:
            main_flow_lines.extend(handler_header_lines)
    
    # Ensure tool is loaded before first cutting step (even if a step forgets it).
    first_tool: int = 0
    for op in operations:
        if op.op_type in (OpType.PROGRAM_HEADER, OpType.CONTOUR):
            continue
        tval = _get_tool_number(op.params)
        if tval > 0:
            first_tool = tval
            break
    if first_tool > 0 and int(float(settings.get("_current_tool", 0))) == 0:
        pre_tool_lines: List[str] = []
        _append_tool_and_spindle(pre_tool_lines, first_tool, None, settings)
        if pre_tool_lines:
            main_flow_lines.extend(pre_tool_lines)

    main_flow_lines.append("")

    # --- operations in UI order ---
    step_num: int = 0
    for op in operations:
        # Skip program header operation
        if op.op_type == OpType.PROGRAM_HEADER:
            continue
        
        step_num += 1
        
        # Load tool before this step if needed
        op_tool = _get_tool_number(op.params)
        if op_tool > 0:
            tool_lines: List[str] = []
            _append_tool_and_spindle(tool_lines, op_tool, None, settings)
            if tool_lines:
                main_flow_lines.extend(tool_lines)
        
        # For ABSPANEN, resolve contour path
        if op.op_type == OpType.ABSPANEN:
            contour_name = op.params.get("contour_name")
            if contour_name:
                # Find contour operation
                contour_op = next((o for o in operations if o.op_type == OpType.CONTOUR and o.params.get("name") == contour_name), None)
                if contour_op and contour_op.path:
                    # Keep primitives for G71/G72 cycle subs (G2/G3 arcs)
                    if contour_op.path and isinstance(contour_op.path[0], dict):
                        op.params["_primitives"] = contour_op.path
                        op.path = primitives_to_points(contour_op.path)
                    else:
                        op.path = contour_op.path
                else:
                    op.path = []
        
        main_flow_lines.append("")
        
        # Add step comment with tool info
        op_title = _sanitize_comment_text(op.params.get("title", op.op_type))
        tool_val = _get_tool_number(op.params)
        
        # Build step comment
        tools = settings.get("tools", {})
        tool_desc = ""
        if tool_val > 0 and tool_val in tools:
            tool_comment = _sanitize_comment_text(tools[tool_val].get("comment", ""))
            tool_desc = f" | T{tool_val}: {tool_comment}"
        
        # Generate operation G-code
        op_lines = gcode_for_operation(op, settings)
        op_lines = _extract_sub_blocks(op_lines)
        
        # Only output step if there is actual G-code generated (not empty/comments-only)
        if op_lines and any(not line.startswith("(") for line in op_lines):
            main_flow_lines.append(f"(Step {step_num}: {op_title}{tool_desc})")
            main_flow_lines.extend(op_lines)
        elif op_lines and op.op_type != OpType.CONTOUR:
            # Keep non-CONTOUR operations even if only comments, but skip empty CONTOUR
            main_flow_lines.append(f"(Step {step_num}: {op_title}{tool_desc})")
            main_flow_lines.extend(op_lines)
        
        # global safe retract after each cutting step
        if op_lines and any(not line.startswith("(") for line in op_lines):
            if op.op_type not in (OpType.CONTOUR, OpType.PROGRAM_HEADER):
                current_pos = _estimate_operation_end_pos(op)
                _emit_safe_retract_for_op(main_flow_lines, settings, op.op_type, current_pos=current_pos)

    lines: List[str] = []
    lines.extend(header_lines)
    if all_subs:
        lines.append("")
        lines.append("(=== Subroutine Definitions ===)")
        for sb in all_subs:
            lines.extend(sb)
        lines.append("(=== End Subroutines ===)")
        lines.append("")

    lines.extend(main_flow_lines)

    # --- PHASE A (Regel 1): Werkzeugwechselpunkt am Programmende ---
    if not footer_lines_from_settings:
        lines.append("")
        xt_end = _float_or_none(settings.get("xt"))
        zt_end = _float_or_none(settings.get("zt"))
        if xt_end is not None and zt_end is not None:
            lines.append("(Werkzeugwechselpunkt am Ende)")
            xt_abs_end = bool(settings.get("xt_absolute", True))
            zt_abs_end = bool(settings.get("zt_absolute", True))
            if not xt_abs_end or not zt_abs_end:
                lines.append(f"G53 G0 X{xt_end:.3f} Z{zt_end:.3f}")
            else:
                lines.append(f"G0 X{xt_end:.3f} Z{zt_end:.3f}")

    # --- program end in main flow ---
    lines.append("")
    # Add footer lines (toolchange position + other cleanup)
    # NOTE: Only output once! Do not duplicate!
    for footer_line in footer_lines_from_settings:
        lines.append(footer_line)
    # Put any global stops here
    lines.append("M5")
    lines.append("M9")
    lines.append("M30")

    lines.append("%")
    return lines


from lathe_easystep.gcode_program import (  # noqa: E402
    gcode_for_operation as _gcode_for_operation_mod,
    generate_program_gcode as _generate_program_gcode_mod,
)
from lathe_easystep.gcode_roughing import (  # noqa: E402
    RetractCfg as _RetractCfg_mod,
    Segment as _Segment_mod,
    compute_pass_x_levels as _compute_pass_x_levels_mod,
    contour_sub_from_points as _contour_sub_from_points_mod,
    contour_sub_from_primitives as _contour_sub_from_primitives_mod,
    generate_abspanen_gcode as _generate_abspanen_gcode_mod,
    get_retract_cfg as _get_retract_cfg_mod,
    intersect_segment_with_x_band as _intersect_segment_with_x_band_mod,
    merge_intervals as _merge_intervals_mod,
    rough_turn_parallel_x as _rough_turn_parallel_x_mod,
    rough_turn_parallel_z as _rough_turn_parallel_z_mod,
    segments_from_polyline as _segments_from_polyline_mod,
    step_line_pause_sub_definition as _step_line_pause_sub_definition_mod,
    step_x_pause_sub_definition as _step_x_pause_sub_definition_mod,
)
from lathe_easystep.gcode_safety import (  # noqa: E402
    append_tool_and_spindle as _append_tool_and_spindle_mod,
    emit_approach as _emit_approach_mod,
    emit_safe_retract as _emit_safe_retract_mod,
    emit_safe_retract_for_op as _emit_safe_retract_for_op_mod,
    estimate_operation_end_pos as _estimate_operation_end_pos_mod,
    get_safe_position as _get_safe_position_mod,
    move_to_toolchange_pos as _move_to_toolchange_pos_mod,
    nose_compensation_command as _nose_compensation_command_mod,
)
from lathe_easystep.gcode_utils import (  # noqa: E402
    REQUIRED_KEYS as _REQUIRED_KEYS_mod,
    clean_path as _clean_path_mod,
    emit_coolant as _emit_coolant_mod,
    float_or_none as _float_or_none_mod,
    get_tool_number as _get_tool_number_mod,
    is_monotonic_x as _is_monotonic_x_mod,
    is_monotonic_x_decreasing as _is_monotonic_x_decreasing_mod,
    is_monotonic_x_increasing as _is_monotonic_x_increasing_mod,
    is_monotonic_z_decreasing as _is_monotonic_z_decreasing_mod,
    primitives_to_points as _primitives_to_points_mod,
    require as _require_mod,
    require_positive as _require_positive_mod,
    require_tool as _require_tool_mod,
    sanitize_comment_text as _sanitize_comment_text_mod,
    sanitize_gcode_text as _sanitize_gcode_text_mod,
)

RetractCfg = _RetractCfg_mod
Segment = _Segment_mod
REQUIRED_KEYS = _REQUIRED_KEYS_mod
require = _require_mod
require_positive = _require_positive_mod
_get_tool_number = get_tool_number = _get_tool_number_mod
require_tool = _require_tool_mod
is_monotonic_z_decreasing = _is_monotonic_z_decreasing_mod
is_monotonic_x_decreasing = _is_monotonic_x_decreasing_mod
is_monotonic_x_increasing = _is_monotonic_x_increasing_mod
is_monotonic_x = _is_monotonic_x_mod
primitives_to_points = _primitives_to_points_mod
segments_from_polyline = _segments_from_polyline_mod
intersect_segment_with_x_band = _intersect_segment_with_x_band_mod
merge_intervals = _merge_intervals_mod
compute_pass_x_levels = _compute_pass_x_levels_mod
rough_turn_parallel_x = _rough_turn_parallel_x_mod
rough_turn_parallel_z = _rough_turn_parallel_z_mod
generate_abspanen_gcode = _generate_abspanen_gcode_mod
contour_sub_from_points = _contour_sub_from_points_mod
contour_sub_from_primitives = _contour_sub_from_primitives_mod
get_retract_cfg = _get_retract_cfg_mod
_step_line_pause_sub_definition = _step_line_pause_sub_definition_mod
_step_x_pause_sub_definition = _step_x_pause_sub_definition_mod
_sanitize_gcode_text = _sanitize_gcode_text_mod
_sanitize_comment_text = _sanitize_comment_text_mod
_emit_coolant = _emit_coolant_mod
_float_or_none = _float_or_none_mod
_get_safe_position = _get_safe_position_mod
_emit_safe_retract = _emit_safe_retract_mod
_emit_safe_retract_for_op = _emit_safe_retract_for_op_mod
_estimate_operation_end_pos = _estimate_operation_end_pos_mod
_emit_approach = _emit_approach_mod
_append_tool_and_spindle = _append_tool_and_spindle_mod
_nose_compensation_command = _nose_compensation_command_mod
move_to_toolchange_pos = _move_to_toolchange_pos_mod
clean_path = _clean_path_mod
gcode_for_operation = _gcode_for_operation_mod
generate_program_gcode = _generate_program_gcode_mod
