from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .contour_logic import build_contour_path as build_contour_primitives
from .model import OpType, Operation

Point = Tuple[float, float]


def build_face_path(params: Dict[str, float]) -> List[Point]:
    if "path" in params and params["path"]:
        path_data = params["path"]
        if isinstance(path_data, list) and path_data:
            path = []
            for point in path_data:
                if isinstance(point, dict):
                    x = point.get("x", 0.0)
                    z = point.get("z", 0.0)
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    x, z = point[0], point[1]
                else:
                    continue
                path.append((float(x), float(z)))
            return path

    x_outer = params.get("outer_diameter", None)
    x_inner = params.get("inner_diameter", None)
    sx = params.get("start_x", None)
    ex = params.get("end_x", None)
    sd = params.get("start_diameter", None)
    ed = params.get("end_diameter", None)

    candidates = [v for v in (sx, ex, sd, ed) if isinstance(v, (int, float))]
    if x_outer is None:
        x_outer = max(candidates) if candidates else 0.0
    if x_inner is None:
        x_inner = min(candidates) if candidates else 0.0

    x_outer = float(x_outer or 0.0)
    x_inner = float(x_inner or 0.0)
    z_start = float(params.get("start_z", params.get("z_start", 0.0)) or 0.0)
    z_end = float(params.get("end_z", z_start))
    edge_type = int(params.get("edge_type", 0))
    edge_size = float(params.get("edge_size", 0.0) or 0.0)

    if x_inner > x_outer:
        x_inner, x_outer = x_outer, x_inner

    path: List[Point] = [(x_inner, z_end)]
    if edge_type == 1 and edge_size > 0.0:
        path.append((max(x_inner, x_outer - 2.0 * edge_size), z_end))
        path.append((x_outer, z_end - edge_size))
    elif edge_type == 2 and edge_size > 0.0:
        x_outer_r = x_outer / 2.0
        x_inner_r = x_inner / 2.0
        x0_r = max(x_inner_r, x_outer_r - edge_size)
        path.append((x0_r * 2.0, z_end))
        cx_r = x_outer_r - edge_size
        cz = z_end - edge_size
        segments = 10
        for i in range(1, segments + 1):
            a = (math.pi / 2.0) * (1.0 - (i / segments))
            x_r = cx_r + edge_size * math.cos(a)
            z = cz + edge_size * math.sin(a)
            path.append((x_r * 2.0, z))
    else:
        path.append((x_outer, z_end))
    return path


def build_turn_path(params: Dict[str, float]) -> List[Point]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    length = params.get("length", 0.0)
    safe_z = params.get("safe_z", 2.0)
    return [(x_start, safe_z), (x_start, 0.0), (x_end, -abs(length))]


def build_bore_path(params: Dict[str, float]) -> List[Point]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    depth = -abs(params.get("depth", 0.0))
    safe_z = params.get("safe_z", 2.0)
    return [(x_start, safe_z), (x_start, 0.0), (x_end, depth)]


def build_thread_path(params: Dict[str, float]) -> List[Point]:
    major = float(params.get("major_diameter", 0.0) or 0.0)
    pitch = max(0.1, float(params.get("pitch", 1.5) or 1.5))
    length = abs(float(params.get("length", 0.0) or 0.0))
    orientation = int(params.get("orientation", 0))
    internal = orientation == 1
    raw_td = params.get("thread_depth")
    if isinstance(raw_td, (int, float)) and raw_td > 0:
        thread_depth = float(raw_td)
    else:
        thread_depth = pitch * 0.6134

    if length <= 1e-9:
        return []

    if internal:
        bore_dia = major - 2.0 * thread_depth
        root_dia = max(bore_dia, major)
        crest_dia = min(bore_dia, major)
    else:
        crest_dia = max(0.0, major)
        root_dia = max(0.0, major - 2.0 * thread_depth)

    if abs(root_dia - crest_dia) <= 1e-9:
        return [(crest_dia, 0.0), (crest_dia, -length)]

    path: List[Point] = [(crest_dia, 0.0)]
    teeth = max(1, int(math.ceil(length / pitch)))
    z = 0.0
    for _ in range(teeth):
        z_mid = max(-length, z - (pitch * 0.5))
        z_next = max(-length, z - pitch)
        path.append((root_dia, z_mid))
        path.append((crest_dia, z_next))
        z = z_next
        if z <= -length + 1e-9:
            break
    if path[-1][1] > -length:
        path.append((root_dia, -length))
    return path


def build_groove_path(params: Dict[str, float]) -> List[Point]:
    diameter = float(params.get("diameter", 0.0) or 0.0)
    width = abs(float(params.get("width", 0.0) or 0.0))
    depth = abs(float(params.get("depth", 0.0) or 0.0))
    z0 = float(params.get("z", 0.0) or 0.0)
    ref = int(params.get("ref", 0) or 0)
    if ref == 1:
        z_left = z0
        z_right = z0 + width
    elif ref == 2:
        z_right = z0
        z_left = z0 - width
    else:
        z_left = z0 - (width / 2.0)
        z_right = z0 + (width / 2.0)
    lage = int(params.get("lage", 0) or 0)
    x_bottom = diameter + depth if lage == 1 else diameter - depth
    return [(diameter, z_left), (x_bottom, z_left), (x_bottom, z_right), (diameter, z_right)]


def build_drill_path(params: Dict[str, float]) -> List[Point]:
    try:
        diameter = float(params.get("diameter", 0.0) or 0.0)
    except Exception:
        diameter = 0.0
    try:
        depth = float(params.get("depth", 0.0) or 0.0)
    except Exception:
        depth = 0.0
    diameter = max(0.0, diameter)
    if depth > 0:
        depth = -abs(depth)
    if diameter <= 1e-9:
        return [(0.0, 0.0), (0.0, depth)]

    half_angle = math.radians(59.0)
    tanv = math.tan(half_angle)
    tip_len = 0.0
    if abs(tanv) > 1e-12:
        tip_len = (diameter * 0.5) / tanv
    cone_start_z = depth + tip_len
    if cone_start_z > 0.0:
        cone_start_z = 0.0
    return [(0.0, 0.0), (diameter, 0.0), (diameter, cone_start_z), (0.0, depth)]


def build_keyway_path(params: Dict[str, float]) -> List[Point]:
    mode = int(params.get("mode", 0))
    nut_length = params.get("nut_length", 0.0)
    nut_depth = params.get("nut_depth", 0.0)
    start_dia = params.get("start_x_dia", 0.0)
    start_z = params.get("start_z", 0.0)
    if mode == 0:
        radial_side = int(params.get("radial_side", 0))
        rad_sign = -1 if radial_side == 0 else 1
        bottom_z = start_z - nut_length
        final_dia = start_dia + rad_sign * 2 * nut_depth
        return [(start_dia, start_z), (start_dia, bottom_z), (final_dia, bottom_z), (final_dia, start_z)]
    top_x = start_dia
    inner_x = start_dia - 2 * nut_length
    back_z = start_z - nut_depth
    return [(top_x, start_z), (inner_x, start_z), (inner_x, back_z), (top_x, back_z)]


def build_keyway_slot_angles(params: Dict[str, object]) -> List[float]:
    try:
        slot_count = max(1, int(float(params.get("slot_count", 1) or 1)))
    except Exception:
        slot_count = 1
    try:
        start_angle_deg = float(params.get("slot_start_angle", 0.0) or 0.0)
    except Exception:
        start_angle_deg = 0.0
    try:
        step_deg = float(params.get("slot_angle_step", 0.0) or 0.0)
    except Exception:
        step_deg = 0.0
    if abs(step_deg) <= 1e-9:
        step_deg = 360.0 / float(slot_count)
    return [math.radians(start_angle_deg + (slot_idx * step_deg)) for slot_idx in range(slot_count)]


def front_view_polar_to_cartesian(angle_rad: float, radius: float) -> tuple[float, float]:
    return (math.sin(angle_rad) * radius, -math.cos(angle_rad) * radius)


def keyway_slice_bounds(params: Dict[str, object]) -> tuple[float, float] | None:
    try:
        mode = int(float(params.get("mode", 0) or 0))
    except Exception:
        mode = 0
    if mode != 0:
        return None
    try:
        z_start = float(params.get("start_z", 0.0) or 0.0)
        nut_length = abs(float(params.get("nut_length", 0.0) or 0.0))
    except Exception:
        return None
    z_min = min(z_start, z_start - nut_length)
    z_max = max(z_start, z_start - nut_length)
    return (z_min, z_max)


def default_slice_z_for_operation(op: Operation | None) -> float | None:
    if op is None:
        return None
    if getattr(op, "op_type", None) == OpType.KEYWAY:
        bounds = keyway_slice_bounds(getattr(op, "params", {}) or {})
        if bounds is not None:
            return (bounds[0] + bounds[1]) * 0.5
        try:
            return float((getattr(op, "params", {}) or {}).get("start_z", 0.0) or 0.0)
        except Exception:
            return 0.0
    path = getattr(op, "path", None) or []
    if path and isinstance(path[0], tuple):
        try:
            z_vals = [float(z) for _, z in path]
            return (min(z_vals) + max(z_vals)) * 0.5
        except Exception:
            return None
    return None


def build_groove_preview_path(params: Dict[str, float]) -> List[Point]:
    diameter = float(params.get("diameter", 0.0) or 0.0)
    width = abs(float(params.get("width", 0.0) or 0.0))
    depth = abs(float(params.get("depth", 0.0) or 0.0))
    z0 = float(params.get("z", 0.0) or 0.0)
    mode = int(params.get("mode", params.get("groove_mode", -1)) or -1)
    ref = int(params.get("ref", 0) or 0)
    lage = int(params.get("lage", 0) or 0)
    if mode not in (0, 1):
        mode = 0 if lage in (0, 1) else 1

    if mode == 0:
        if ref == 1:
            z_left = z0
            z_right = z0 + width
        elif ref == 2:
            z_right = z0
            z_left = z0 - width
        else:
            z_left = z0 - (width / 2.0)
            z_right = z0 + (width / 2.0)
        diameter_delta = 2.0 * depth
        x_bottom = diameter + diameter_delta if lage == 1 else diameter - diameter_delta
        return [(diameter, z_left), (x_bottom, z_left), (x_bottom, z_right), (diameter, z_right)]

    if ref == 1:
        x_near = diameter
        x_far = diameter + width
    elif ref == 2:
        x_near = diameter - width
        x_far = diameter
    else:
        x_near = diameter - (width / 2.0)
        x_far = diameter + (width / 2.0)
    z_bottom = z0 + depth if lage == 3 else z0 - depth
    return [(x_near, z0), (x_near, z_bottom), (x_far, z_bottom), (x_far, z0)]


def build_abspanen_path(params: Dict[str, object]) -> List[Point]:
    source_path = params.get("source_path") or []
    points: List[Point] = []
    try:
        for point in source_path:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            points.append((float(point[0]), float(point[1])))
    except Exception:
        return []
    return points


def build_contour_path(params) -> list:
    return build_contour_primitives(params)
