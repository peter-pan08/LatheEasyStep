from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Tuple

from .contour_features import _tessellate_arc, primitive_to_points
from .contour_logic import build_contour_path as build_contour_primitives
from .gcode_utils import is_internal_side, is_left_hand
from .model import OpType, Operation
from .face_geometry import face_primitives

_LOGGER = logging.getLogger(__name__)

Point = Tuple[float, float]


def sample_preview_arc(p1: Point, p2: Point, center: Point, ccw: bool) -> List[Point]:
    """Tessellate an X-diameter/Z arc after validating it in radius space."""
    x1, z1 = p1[0] / 2.0, p1[1]
    x2, z2 = p2[0] / 2.0, p2[1]
    xc, zc = center[0] / 2.0, center[1]
    r1 = math.hypot(x1 - xc, z1 - zc)
    r2 = math.hypot(x2 - xc, z2 - zc)
    if r1 <= 1e-9 or abs(r1 - r2) > 1e-3:
        return [p1, p2]
    return [p1, *_tessellate_arc(p1, p2, center, ccw)]


def preview_primitives_to_points(primitives) -> List[Point]:
    """Flatten legacy line/arc primitives for interpolation compatibility."""
    points: List[Point] = []
    last = None
    for primitive in primitives or []:
        if isinstance(primitive, (list, tuple)) and len(primitive) >= 2:
            try:
                point = (float(primitive[0]), float(primitive[1]))
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "preview_primitives_to_points", exc)
                continue
            points.append(point)
            last = point
            continue
        if not isinstance(primitive, dict):
            continue
        primitive_type = (primitive.get("type") or "").lower()
        if primitive_type == "line":
            p1 = tuple(primitive.get("p1", (0.0, 0.0)))
            p2 = tuple(primitive.get("p2", (0.0, 0.0)))
            if last is None or math.hypot(p1[0] - last[0], p1[1] - last[1]) > 1e-6:
                points.append(p1)
            points.append(p2)
            last = p2
        elif primitive_type == "arc":
            p1 = tuple(primitive.get("p1", (0.0, 0.0)))
            p2 = tuple(primitive.get("p2", (0.0, 0.0)))
            center = tuple(primitive.get("c", (0.0, 0.0)))
            arc_points = sample_preview_arc(p1, p2, center, bool(primitive.get("ccw", True)))
            if last is None:
                points.extend(arc_points)
            else:
                if math.hypot(arc_points[0][0] - last[0], arc_points[0][1] - last[1]) > 1e-6:
                    points.append(arc_points[0])
                points.extend(arc_points[1:])
            last = arc_points[-1]
    return points


def compute_side_viewport(
    paths,
    width: float,
    height: float,
    *,
    x_is_diameter: bool = True,
    base_span: float = 10.0,
    padding: float = 0.05,
) -> Dict[str, float]:
    """Return padded side-view bounds and scale without any Qt dependency."""
    min_x = min_z = float("inf")
    max_x = max_z = float("-inf")

    for path in paths or []:
        if not path:
            continue
        try:
            points = preview_primitives_to_points(path) if isinstance(path[0], dict) else path
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "compute_side_viewport", exc)
            points = []
        for x_value, z_value in points:
            x_display = float(x_value) * (0.5 if x_is_diameter else 1.0)
            z_number = float(z_value)
            min_x = min(min_x, x_display)
            max_x = max(max_x, x_display)
            min_z = min(min_z, z_number)
            max_z = max(max_z, z_number)

    if min_x == float("inf") or min_z == float("inf"):
        min_x = max_x = min_z = max_z = 0.0

    span_floor = max(0.0, float(base_span))
    half_span = span_floor / 2.0
    min_x, max_x = min(min_x, -half_span, 0.0), max(max_x, half_span, 0.0)
    min_z, max_z = min(min_z, -half_span, 0.0), max(max_z, half_span, 0.0)

    def ensure_span(minimum: float, maximum: float) -> tuple[float, float]:
        missing = span_floor - (maximum - minimum)
        if missing > 0.0:
            return minimum - missing / 2.0, maximum + missing / 2.0
        return minimum, maximum

    min_x, max_x = ensure_span(min_x, max_x)
    min_z, max_z = ensure_span(min_z, max_z)
    x_span = max(max_x - min_x, 1e-3)
    z_span = max(max_z - min_z, 1e-3)
    pad = max(0.0, float(padding))
    min_x, max_x = min_x - x_span * pad, max_x + x_span * pad
    min_z, max_z = min_z - z_span * pad, max_z + z_span * pad
    scale = min(
        float(width) / max(max_z - min_z, 1e-6),
        float(height) / max(max_x - min_x, 1e-6),
    )
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_z": min_z,
        "max_z": max_z,
        "scale": scale,
    }


def navigated_center_scale(
    center: Point, scale: float, zoom: float, pan: Point
) -> Tuple[Point, float]:
    """Apply display-only pan/zoom to a fitted circular/front viewport."""
    safe_zoom = max(float(zoom), 1e-9)
    return (
        (float(center[0]) + float(pan[0]), float(center[1]) + float(pan[1])),
        float(scale) * safe_zoom,
    )


def apply_side_navigation(
    viewport: Dict[str, float],
    *,
    left: float,
    bottom: float,
    center: Point,
    zoom: float,
    pan: Point,
) -> Dict[str, float]:
    """Apply display-only pan/zoom while preserving the fitted model bounds."""
    safe_zoom = max(float(zoom), 1e-9)
    base_scale = max(float(viewport["scale"]), 1e-9)
    scale = base_scale * safe_zoom
    min_z = float(viewport["min_z"]) + (float(center[0]) - float(left)) * (
        1.0 - 1.0 / safe_zoom
    ) / base_scale
    min_x = float(viewport["min_x"]) + (float(bottom) - float(center[1])) * (
        1.0 - 1.0 / safe_zoom
    ) / base_scale
    min_z -= float(pan[0]) / scale
    min_x += float(pan[1]) / scale
    z_span = (float(viewport["max_z"]) - float(viewport["min_z"])) / safe_zoom
    x_span = (float(viewport["max_x"]) - float(viewport["min_x"])) / safe_zoom
    return {
        "min_x": min_x,
        "max_x": min_x + x_span,
        "min_z": min_z,
        "max_z": min_z + z_span,
        "scale": scale,
    }


def zoom_navigation_state(
    old_zoom: float,
    pan: Point,
    pointer: Point,
    center: Point,
    wheel_steps: float,
    *,
    minimum: float = 0.2,
    maximum: float = 20.0,
) -> Tuple[float, Point]:
    """Return bounded zoom and compensating pan keeping the pointer anchored."""
    current = max(float(old_zoom), 1e-9)
    new_zoom = max(float(minimum), min(float(maximum), current * (1.2 ** float(wheel_steps))))
    ratio = new_zoom / current
    anchor_x = float(pointer[0]) - float(center[0])
    anchor_y = float(pointer[1]) - float(center[1])
    return new_zoom, (
        anchor_x - (anchor_x - float(pan[0])) * ratio,
        anchor_y - (anchor_y - float(pan[1])) * ratio,
    )


def nice_tick_step(span: float) -> float:
    """Choose a 1/2/5-based tick distance yielding at most eight intervals."""
    if span <= 0.0:
        return 1.0
    raw = span / 5.0
    power = 10 ** int(math.floor(math.log10(raw)))
    for multiplier in (1, 2, 5, 10):
        step = multiplier * power
        if span / step <= 8:
            return step
    return raw


def front_view_scale(max_diameter: float, width: float, height: float) -> float:
    """Pixels per mm for the front (cross-section) view, fitting the largest
    diameter into the available rect with a small margin."""
    return min(float(width), float(height)) / max(float(max_diameter) * 1.15, 1e-6)


def circular_view_layout(
    diameter: float,
    bounds: Tuple[float, float, float, float],
    *,
    zoom: float = 1.0,
    pan: Point = (0.0, 0.0),
    fit_factor: float = 1.15,
) -> Dict[str, object]:
    """Build Qt-free screen geometry for slice/front circular views."""
    left, top, right, bottom = (float(value) for value in bounds)
    width = max(right - left, 0.0)
    height = max(bottom - top, 0.0)
    base_center = ((left + right) * 0.5, (top + bottom) * 0.5)
    base_scale = min(width, height) / max(abs(float(diameter)) * float(fit_factor), 1e-6)
    center, scale = navigated_center_scale(base_center, base_scale, zoom, pan)
    return {
        "center": center,
        "scale": scale,
        "radius": abs(float(diameter)) * 0.5 * scale,
        "horizontal_axis": ((left, center[1]), (right, center[1])),
        "vertical_axis": ((center[0], top), (center[0], bottom)),
    }


def offset_polygons_to_screen(
    polygons: List[List[Point]], center: Point, scale: float
) -> List[List[Point]]:
    """Map model-space polygons expressed as center offsets to screen space."""
    cx, cy = float(center[0]), float(center[1])
    factor = float(scale)
    return [
        [(cx + float(x) * factor, cy + float(y) * factor) for x, y in polygon]
        for polygon in polygons
    ]


def legend_layout(
    item_count: int,
    *,
    collapsed: bool = False,
    margin: float = 6.0,
    header_height: float = 18.0,
    row_height: float = 16.0,
    box_width: float = 175.0,
    line_length: float = 26.0,
) -> Dict[str, object]:
    """Pure geometry for the side-view legend box: outer rect, header click
    target, header text rect and each row's line/label positions - no
    QPainter dependency. The legend labels/colours themselves stay in the
    widget since they are Qt style constants, not layout."""
    x0 = margin
    y0 = margin - 2.0
    box_height = (
        margin * 2.0 + header_height
        if collapsed
        else margin * 2.0 + header_height + row_height * item_count
    )
    rows: List[Dict[str, tuple]] = []
    if not collapsed:
        for index in range(item_count):
            y = y0 + margin + header_height + index * row_height + 10.0
            rows.append({
                "line": ((x0 + margin, y), (x0 + margin + line_length, y)),
                "label_pos": (x0 + margin + line_length + 6.0, y + 4.0),
            })
    return {
        "box_rect": (x0, y0, box_width, box_height),
        "click_rect": (x0, y0, box_width, header_height + margin),
        "header_text_rect": (x0 + margin, y0 + 2.0, box_width - 2.0 * margin, header_height),
        "rows": rows,
    }


def status_message_layout(messages, *, widget_width: float) -> Dict[str, object] | None:
    """Pure geometry+truncation for the status/warning box in the top-right
    corner - no QPainter dependency. Returns None when there is nothing to
    show, matching the widget's "skip the whole block" behaviour."""
    truncated = [str(message)[:80] for message in list(messages or [])[:4]]
    if not truncated:
        return None
    box_h = 12.0 + (len(truncated) * 16.0)
    box_w = min(float(widget_width) - 20.0, 540.0)
    x0 = float(widget_width) - box_w - 8.0
    y0 = 8.0
    return {
        "messages": truncated,
        "box_rect": (x0, y0, box_w, box_h),
        "header_pos": (x0 + 8.0, y0 + 14.0),
        "line_positions": [(x0 + 8.0, y0 + 30.0 + index * 15.0) for index in range(len(truncated))],
    }


def side_view_to_screen(
    x_value: float,
    z_value: float,
    viewport: Dict[str, float],
    *,
    left: float,
    bottom: float,
    x_is_diameter: bool = True,
    x_is_display: bool = False,
) -> Point:
    """Map lathe coordinates to screen coordinates (Z right, X up)."""
    x_display = float(x_value)
    if x_is_diameter and not x_is_display:
        x_display *= 0.5
    scale = float(viewport["scale"])
    screen_x = float(left) + (float(z_value) - float(viewport["min_z"])) * scale
    screen_y = float(bottom) - (x_display - float(viewport["min_x"])) * scale
    return (screen_x, screen_y)


def side_view_axis_lines(
    viewport: Dict[str, float], *, left: float, bottom: float
) -> Dict[str, object]:
    """Return screen-space X/Z axes and their display-coordinate positions."""
    min_x, max_x = float(viewport["min_x"]), float(viewport["max_x"])
    min_z, max_z = float(viewport["min_z"]), float(viewport["max_z"])
    axis_x = 0.0 if min_x <= 0.0 <= max_x else min_x
    axis_z = 0.0 if min_z <= 0.0 <= max_z else min_z

    def display_point(x_display: float, z_value: float) -> Point:
        return side_view_to_screen(
            x_display,
            z_value,
            viewport,
            left=left,
            bottom=bottom,
            x_is_display=True,
        )

    return {
        "axis_x": axis_x,
        "axis_z": axis_z,
        "x_line": (display_point(axis_x, min_z), display_point(axis_x, max_z)),
        "z_line": (display_point(min_x, axis_z), display_point(max_x, axis_z)),
    }


def side_view_slice_line(
    viewport: Dict[str, float], slice_z: float, *, left: float, bottom: float
) -> tuple[Point, Point]:
    """Return the vertical screen-space line for a selected axial slice."""
    return (
        side_view_to_screen(
            viewport["min_x"], slice_z, viewport,
            left=left, bottom=bottom, x_is_display=True,
        ),
        side_view_to_screen(
            viewport["max_x"], slice_z, viewport,
            left=left, bottom=bottom, x_is_display=True,
        ),
    )


def side_view_ticks(
    viewport: Dict[str, float], *, left: float, bottom: float,
    x_is_diameter: bool = True,
) -> Dict[str, list]:
    """Return tick values, label values and screen positions for both axes."""
    axes = side_view_axis_lines(viewport, left=left, bottom=bottom)

    def values(minimum: float, maximum: float) -> List[float]:
        step = nice_tick_step(maximum - minimum)
        value = (minimum // step) * step
        result = []
        while value <= maximum:
            result.append(value)
            value += step
        return result

    x_ticks = []
    for value in values(float(viewport["min_x"]), float(viewport["max_x"])):
        point = side_view_to_screen(
            value, axes["axis_z"], viewport,
            left=left, bottom=bottom, x_is_display=True,
        )
        label_value = value * 2.0 if x_is_diameter else value
        x_ticks.append((value, label_value, point))

    z_ticks = []
    for value in values(float(viewport["min_z"]), float(viewport["max_z"])):
        point = side_view_to_screen(
            axes["axis_x"], value, viewport,
            left=left, bottom=bottom, x_is_display=True,
        )
        z_ticks.append((value, value, point))
    return {"x": x_ticks, "z": z_ticks}


def side_view_grid_layout(
    viewport: Dict[str, float],
    *,
    left: float,
    top: float,
    right: float,
    bottom: float,
    x_is_diameter: bool = True,
    slice_z: float | None = None,
) -> Dict[str, object]:
    """Build the complete Qt-free axes/ticks/slice overlay draw geometry."""
    axes = side_view_axis_lines(viewport, left=left, bottom=bottom)
    ticks = side_view_ticks(
        viewport, left=left, bottom=bottom, x_is_diameter=x_is_diameter
    )
    z_ticks = []
    for value, label, point in ticks["z"]:
        px, py = point
        z_ticks.append({
            "value": value,
            "label": label,
            "mark_line": ((px, py - 4.0), (px, py + 2.0)),
            "label_pos": (px - 6.0, py + 14.0),
        })
    x_ticks = []
    for value, label, point in ticks["x"]:
        px, py = point
        x_ticks.append({
            "value": value,
            "label": label,
            "mark_line": ((px - 2.0, py), (px + 4.0, py)),
            "label_pos": (px - 28.0, py + 4.0),
        })
    result: Dict[str, object] = {
        "axes": axes,
        "z_ticks": z_ticks,
        "x_ticks": x_ticks,
        "z_label_pos": (float(right) - 20.0, float(axes["z_line"][0][1]) - 6.0),
        "x_label_pos": (float(axes["x_line"][0][0]) + 6.0, float(top) + 12.0),
        "slice": None,
    }
    if slice_z is not None:
        line = side_view_slice_line(
            viewport, float(slice_z), left=left, bottom=bottom
        )
        result["slice"] = {
            "line": line,
            "label_pos": (min(float(line[0][0]) + 8.0, float(right) - 90.0), float(top) + 16.0),
        }
    return result


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
    profile = face_primitives(x_outer, x_inner, z_end,
                              params.get("edge_type", 0), params.get("edge_size", 0.0))
    # Preserve the preview's inside-to-outside point order. Sample the shared
    # circular primitive in radial coordinates; G-code keeps the actual arc.
    path = []
    for primitive in profile:
        if not path:
            path.append(primitive["p1"])
        if primitive["type"] == "arc":
            cx, cz = primitive["c"]
            radius = (primitive["p1"][0] - cx) / 2.0
            for i in range(1, 17):
                angle = math.pi * i / 32.0
                path.append((cx + 2 * radius * math.cos(angle), cz + radius * math.sin(angle)))
            path[-1] = primitive["p2"]
        else:
            path.append(primitive["p2"])
    return list(reversed(path))


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
    internal = is_internal_side(params.get("orientation", 0))
    left_hand = is_left_hand(params.get("hand", 0))
    start_z = float(params.get("thread_start_z", 0.0) or 0.0)
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

    z_dir = 1.0 if left_hand else -1.0
    end_z = start_z + (z_dir * length)
    lead_in = abs(float(params.get("lead_in", 0.0) or 0.0))
    lead_out = abs(float(params.get("lead_out", 0.0) or 0.0))

    if abs(root_dia - crest_dia) <= 1e-9:
        return [(crest_dia, start_z), (crest_dia, end_z)]

    path: List[Point] = []
    if lead_in > 1e-9:
        path.extend([(crest_dia, start_z - z_dir * lead_in), (root_dia, start_z)])
    path.append((crest_dia, start_z))
    teeth = max(1, int(math.ceil(length / pitch)))
    z = start_z
    for _ in range(teeth):
        z_mid = z + (z_dir * pitch * 0.5)
        z_next = z + (z_dir * pitch)
        if z_dir < 0.0:
            z_mid = max(end_z, z_mid)
            z_next = max(end_z, z_next)
        else:
            z_mid = min(end_z, z_mid)
            z_next = min(end_z, z_next)
        path.append((root_dia, z_mid))
        path.append((crest_dia, z_next))
        z = z_next
        if (z_dir < 0.0 and z <= end_z + 1e-9) or (z_dir > 0.0 and z >= end_z - 1e-9):
            break
    if (z_dir < 0.0 and path[-1][1] > end_z) or (z_dir > 0.0 and path[-1][1] < end_z):
        path.append((root_dia, end_z))
    if lead_out > 1e-9:
        if path[-1] != (root_dia, end_z):
            path.append((root_dia, end_z))
        path.append((crest_dia, end_z + z_dir * lead_out))
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
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_drill_path", exc)
        diameter = 0.0
    try:
        depth = float(params.get("depth", 0.0) or 0.0)
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_drill_path", exc)
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


def keyway_radial_slot_radii(params: Dict[str, object]) -> tuple[float, float]:
    """Return (inner_radius, outer_radius) of the radial keyway slot (mode 0)
    for the Schnittansicht-Overlay. Must stay consistent with the final
    diameter `build_keyway_path()` computes for the Seitenansicht, since both
    describe the same cut depth from the same params - just as radius vs.
    diameter and at a specific Z vs. along the whole slot length.
    """
    try:
        start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "keyway_radial_slot_radii", exc)
        start_dia = 0.0
    try:
        nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "keyway_radial_slot_radii", exc)
        nut_depth = 0.0
    try:
        radial_side = int(float(params.get("radial_side", 0) or 0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "keyway_radial_slot_radii", exc)
        radial_side = 0

    base_radius = start_dia * 0.5
    if radial_side == 0:
        return max(0.0, base_radius - nut_depth), base_radius
    return base_radius, base_radius + nut_depth


def build_keyway_slot_angles(params: Dict[str, object]) -> List[float]:
    try:
        slot_count = max(1, int(float(params.get("slot_count", 1) or 1)))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_keyway_slot_angles", exc)
        slot_count = 1
    try:
        start_angle_deg = float(params.get("slot_start_angle", 0.0) or 0.0)
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_keyway_slot_angles", exc)
        start_angle_deg = 0.0
    try:
        step_deg = float(params.get("slot_angle_step", 0.0) or 0.0)
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_keyway_slot_angles", exc)
        step_deg = 0.0
    if abs(step_deg) <= 1e-9:
        step_deg = 360.0 / float(slot_count)
    return [math.radians(start_angle_deg + (slot_idx * step_deg)) for slot_idx in range(slot_count)]


def front_view_polar_to_cartesian(angle_rad: float, radius: float) -> tuple[float, float]:
    return (math.sin(angle_rad) * radius, -math.cos(angle_rad) * radius)


def keyway_slice_bounds(params: Dict[str, object]) -> tuple[float, float] | None:
    try:
        mode = int(float(params.get("mode", 0) or 0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "keyway_slice_bounds", exc)
        mode = 0
    if mode != 0:
        return None
    try:
        z_start = float(params.get("start_z", 0.0) or 0.0)
        nut_length = abs(float(params.get("nut_length", 0.0) or 0.0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "keyway_slice_bounds", exc)
        return None
    z_min = min(z_start, z_start - nut_length)
    z_max = max(z_start, z_start - nut_length)
    return (z_min, z_max)


def build_keyway_front_polygons(
    params: Dict[str, object], slice_z: float, samples: int = 14
) -> List[List[Point]]:
    """Build radial-keyway overlay polygons in unscaled front-view space."""
    try:
        mode = int(float(params.get("mode", 0) or 0))
        start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
        slot_width = abs(
            float(params.get("slot_width", params.get("cutting_width", 0.0)) or 0.0)
        )
        slice_value = float(slice_z)
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_keyway_front_polygons", exc)
        return []
    if mode != 0 or start_dia <= 0.0:
        return []

    bounds = keyway_slice_bounds(params)
    if bounds is None:
        return []
    z_min, z_max = bounds
    if slice_value < z_min - 1e-6 or slice_value > z_max + 1e-6:
        return []

    inner_radius, outer_radius = keyway_radial_slot_radii(params)
    if outer_radius <= 1e-9:
        return []
    if slot_width > 0.0:
        half_opening = max(
            math.radians(2.0),
            min(math.radians(40.0), slot_width / max(outer_radius, 1e-6)),
        )
    else:
        half_opening = math.radians(6.0)

    sample_count = max(1, int(samples))
    polygons: List[List[Point]] = []
    for middle_angle in build_keyway_slot_angles(params):
        start_angle = middle_angle - half_opening
        end_angle = middle_angle + half_opening
        polygon = [
            front_view_polar_to_cartesian(
                start_angle + ((end_angle - start_angle) * index / sample_count),
                outer_radius,
            )
            for index in range(sample_count + 1)
        ]
        polygon.extend(
            front_view_polar_to_cartesian(
                start_angle + ((end_angle - start_angle) * index / sample_count),
                inner_radius,
            )
            for index in range(sample_count, -1, -1)
        )
        polygons.append(polygon)
    return polygons


def default_slice_z_for_operation(op: Operation | None) -> float | None:
    if op is None:
        return None
    if getattr(op, "op_type", None) == OpType.KEYWAY:
        bounds = keyway_slice_bounds(getattr(op, "params", {}) or {})
        if bounds is not None:
            return (bounds[0] + bounds[1]) * 0.5
        try:
            return float((getattr(op, "params", {}) or {}).get("start_z", 0.0) or 0.0)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "default_slice_z_for_operation", exc)
            return 0.0
    path = getattr(op, "path", None) or []
    if path and isinstance(path[0], tuple):
        try:
            z_vals = [float(z) for _, z in path]
            return (min(z_vals) + max(z_vals)) * 0.5
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "default_slice_z_for_operation", exc)
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
    try:
        # source_path kommt aus der referenzierten Kontur-Operation
        # (resolve_contour_path()); deren eigenes op.path ist immer
        # primitiven-foermig ({"type": "line"/"arc", "p1": ..., "p2": ...}),
        # nie eine flache Liste aus (x, z)-Punkten. Der reine Tupel-Zweig
        # unten griff deshalb faktisch nie und lieferte fuer jede reale
        # Abspanen-Operation einen leeren Vorschaupfad.
        if source_path and isinstance(source_path[0], dict):
            return primitive_to_points(source_path)
        points: List[Point] = []
        for point in source_path:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            points.append((float(point[0]), float(point[1])))
        return points
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_abspanen_path", exc)
        return []


def build_contour_path(params) -> list:
    return build_contour_primitives(params)


def build_stock_outline(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a thin reference outline of the raw stock in XZ (diameter X).

    Output format matches the preview widget's 'primitives' list of dicts.
    Uses role='stock' so the widget can draw it in a neutral thin dashed style.
    """
    shape = str(program.get("shape", "")).lower().strip()

    def _sf(v: Any, default: float = 0.0) -> float:
        try:
            if v is None:
                return float(default)
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else float(default)
            return float(v)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "_sf", exc)
            return float(default)

    xa = _sf(program.get("xa", 0.0), 0.0)  # outer diameter
    xi = _sf(program.get("xi", 0.0), 0.0)  # inner diameter (for tube)
    za = _sf(program.get("za", 0.0), 0.0)  # front face Z
    zi = float(program.get("zi", 0.0) or 0.0)  # back face Z (often negative length)

    if xa <= 0.0:
        return []

    # Normalize Z: ensure za is the front (greater) and zi is the back (smaller) for drawing
    z_front = max(za, zi)
    z_back = min(za, zi)

    primitives: List[Dict[str, Any]] = []

    def add_line(z1: float, x1: float, z2: float, x2: float) -> None:
        primitives.append({"role": "stock", "type": "line", "p1": (x1, z1), "p2": (x2, z2)})

    # Outer contour (L-shape: face + OD + back face + centerline return)
    add_line(z_front, 0.0, z_front, xa)     # front face
    add_line(z_front, xa, z_back, xa)       # OD along Z
    add_line(z_back, xa, z_back, 0.0)       # back face
    # centerline is optional; keep it minimal (no line back to front)

    if shape in ("rohr", "tube") and xi > 0.0 and xi < xa:
        # Inner bore contour as reference (also L-shape)
        add_line(z_front, xi, z_back, xi)
        # (front/back inner face lines are usually not needed for reference)

    return primitives


def build_retract_primitives(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return retract plane lines (XRA/XRI/ZRA/ZRI) as preview primitives.

    Supports absolute/incremental flags:
      - xra_absolute / xri_absolute / zra_absolute / zri_absolute

    Interpretation (matching current program header semantics):
      - XRA (outer retract): always available; if incremental -> XA + XRA, else -> XRA
      - XRI (inner retract): only relevant in retract mode `erweitert`/`alle`;
        if incremental -> XI + XRI, else -> XRI
      - ZRA (front retract): always available; if incremental -> ZA + ZRA, else -> ZRA
      - ZRI (back retract): only relevant in retract mode `alle`;
        if incremental -> ZI - ZRI, else -> ZRI

    Output format:
      {"role":"retract","type":"line","p1":(x,z),"p2":(x,z)}
    """
    def _sf(v: Any, default: float = 0.0) -> float:
        try:
            if v is None:
                return float(default)
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else float(default)
            return float(v)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "_sf", exc)
            return float(default)

    xa = _sf(program.get("xa", 0.0), 0.0)
    xi = _sf(program.get("xi", 0.0), 0.0)
    za = _sf(program.get("za", 0.0), 0.0)
    zi = _sf(program.get("zi", 0.0), 0.0)

    # drawing span for the helper lines
    z_front = max(za, zi)
    z_back = min(za, zi)

    prim: List[Dict[str, Any]] = []

    def add_line(p1: tuple[float, float], p2: tuple[float, float]) -> None:
        prim.append({"role": "retract", "type": "line", "p1": p1, "p2": p2})

    def vline(x: float) -> None:
        add_line((x, z_front), (x, z_back))

    def hline(z: float) -> None:
        # use XA as max extents (fallback: 0..10mm)
        x_max = xa if xa > 0.0 else 10.0
        add_line((0.0, z), (x_max, z))

    def _is_true(key: str) -> bool:
        try:
            return bool(program.get(key, False))
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "_is_true", exc)
            return False

    # XRA (outer)
    xra = program.get("xra", None)
    if xra is not None:
        try:
            xra_f = _sf(xra)
            if abs(xra_f) > 1e-12:
                x = xra_f if _is_true("xra_absolute") else (xa + xra_f)
                vline(x)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_retract_primitives", exc)
            pass

    # XRI (inner)
    xri = program.get("xri", None)
    if xri is not None:
        try:
            xri_f = _sf(xri)
            if abs(xri_f) > 1e-12:
                x = xri_f if _is_true("xri_absolute") else (xi + xri_f)
                vline(x)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_retract_primitives", exc)
            pass

    # ZRA (front)
    zra = program.get("zra", None)
    if zra is not None:
        try:
            zra_f = _sf(zra)
            if abs(zra_f) > 1e-12:
                z = zra_f if _is_true("zra_absolute") else (za + zra_f)
                hline(z)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_retract_primitives", exc)
            pass

    # ZRI (back)
    zri = program.get("zri", None)
    if zri is not None:
        try:
            zri_f = _sf(zri)
            if abs(zri_f) > 1e-12:
                # If absolute flag is set, interpret value as absolute Z; otherwise incremental from ZI.
                z = zri_f if _is_true("zri_absolute") else (zi - zri_f)
                hline(z)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_retract_primitives", exc)
            pass

    return prim


def build_worklimit_primitives(program: Dict[str, Any], stock_prims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bearbeitungsmaß / Werkstück-Überstand (Chuck-Kollisionsgrenze) als Linie.

    program['zb'] = Z-Position der Grenze (wo das Material aus dem Futter herausragt).

    Die Linienlänge wird **aus der Rohteilkontur** abgeleitet, damit sie nicht mit
    Fantasie-Werten (±1000) gezeichnet wird.
    """
    try:
        z = float(program.get("zb", 0.0) or 0.0)
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_worklimit_primitives", exc)
        z = 0.0

    if abs(z) < 1e-9:
        return []

    # X-Ausdehnung aus Rohteil-Kontur (points sind (x, z))
    x_vals: List[float] = []
    for prim in stock_prims or []:
        if isinstance(prim, dict) and prim.get("type") == "polyline":
            pts = prim.get("points") or []
            for pt in pts:
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    try:
                        x_vals.append(float(pt[0]))
                    except Exception as exc:
                        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_worklimit_primitives", exc)
                        pass
        elif isinstance(prim, dict) and prim.get("type") == "line":
            for pt in (prim.get("p1"), prim.get("p2")):
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    try:
                        x_vals.append(float(pt[0]))
                    except Exception as exc:
                        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "build_worklimit_primitives", exc)
                        pass

    if x_vals:
        min_x = min(x_vals)
        max_x = max(x_vals)
        # kleine Sicherheitsmargen (typisch: min bei 0 -> Linie bis ca. -5mm)
        margin_neg = 5.0
        margin_pos = max(2.0, 0.02 * max(abs(max_x), 1.0))
        x_min = min(min_x - margin_neg, -margin_neg)
        x_max = max_x + margin_pos
    else:
        # Fallback, falls keine Rohteil-Kontur verfügbar ist
        x_min = -5.0
        x_max = 50.0

    return [{
        "type": "line",
        "p1": (x_min, z),
        "p2": (x_max, z),
        "role": "worklimit",
    }]


def build_chuck_nogo_primitives(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vorschau-Rechteck für die Futter-Sperrzone (No-Go-Bereich)."""
    def _sf(v: Any, default: float | None = None) -> float | None:
        try:
            if v is None:
                return default
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else default
            return float(v)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "_sf", exc)
            return default

    x_min = _sf(program.get("chuck_no_go_x_min"), None)
    x_max = _sf(program.get("chuck_no_go_x_max"), None)
    z_lim = _sf(program.get("chuck_no_go_z_limit"), None)
    if x_min is None or x_max is None or z_lim is None:
        return []

    lo = min(float(x_min), float(x_max))
    hi = max(float(x_min), float(x_max))
    if hi - lo <= 1e-6:
        return []

    za = _sf(program.get("za"), 0.0) or 0.0
    zi = _sf(program.get("zi"), 0.0) or 0.0
    zb = _sf(program.get("zb"), None)

    if zb is not None:
        # ZB (Bearbeitungsmass) markiert, wo das nutzbare Rohteil endet und das
        # futterseitig eingespannte Material beginnt - das ist die tatsaechliche
        # nahe Grenze der Sperrzone, nicht ein geschaetzter Abstand. Die Zone
        # beginnt dort und reicht bis zur (weiter negativen bzw. futterseitigen)
        # chuck_no_go_z_limit, plus einem kleinen Rand, damit sichtbar ist, dass
        # sie sich weiter ins Futter hinein fortsetzt statt dort hart aufzuhoeren.
        margin = max(2.0, 0.05 * max(abs(za - zi), 1.0))
        if float(z_lim) <= float(zb):
            z0 = float(zb)
            z1 = min(float(z_lim), float(zi)) - margin
        else:
            z0 = float(zb)
            z1 = max(float(z_lim), float(zi)) + margin
    else:
        # Rueckfallverhalten fuer aeltere Programme ohne ZB im Header.
        span = max(10.0, 0.20 * max(abs(za - zi), 1.0))
        if float(z_lim) <= float(za):
            z_far = min(float(zi), float(z_lim)) - span
            z0 = z_far
            z1 = float(z_lim)
        else:
            z_far = max(float(zi), float(z_lim)) + span
            z0 = float(z_lim)
            z1 = z_far

    return [
        {"type": "line", "p1": (lo, z0), "p2": (hi, z0), "role": "chuck_nogo"},
        {"type": "line", "p1": (hi, z0), "p2": (hi, z1), "role": "chuck_nogo"},
        {"type": "line", "p1": (hi, z1), "p2": (lo, z1), "role": "chuck_nogo"},
        {"type": "line", "p1": (lo, z1), "p2": (lo, z0), "role": "chuck_nogo"},
    ]


# LES-024/LES-034: reine Geometrieberechnung fuer die Schnittansicht, aus
# preview_widget.py (LathePreviewWidget) extrahiert - keine QPainter-Aufrufe,
# keine Widget-Seiteneffekte. Die Widget-Methoden bleiben als duenne
# Delegierungen bestehen, damit Seiten- und Schnittansicht weiterhin
# dieselbe Datenquelle (op.path) nutzen und nicht auseinanderlaufen koennen
# (siehe TODO.md/CHANGELOG.md LES-034 "komplexe Endgeometrien vergleichen").

def interp_x_hits_at_z(path: List[Point], z: float) -> List[float]:
    """Alle X-Treffer eines Punktpfads bei einem festen Z, aufsteigend und
    entdoppelt. Eine vertikale Flanke (z1 == z2 == z) liefert beide Enden,
    nicht nur eines - sonst wuerde eine Nutflanke in der Schnittansicht nur
    einen von zwei tatsaechlichen Durchmessern zeigen."""
    if not path or len(path) < 2:
        return []
    hits: List[float] = []
    for (x1, z1), (x2, z2) in zip(path[:-1], path[1:]):
        if abs(z2 - z1) < 1e-9:
            if abs(z - z1) < 1e-6:
                hits.append(x1)
                hits.append(x2)
            continue
        if (z1 <= z <= z2) or (z2 <= z <= z1):
            t = (z - z1) / (z2 - z1)
            hits.append(x1 + t * (x2 - x1))
    uniq: List[float] = []
    for val in sorted(float(h) for h in hits):
        if not uniq or abs(val - uniq[-1]) > 1e-6:
            uniq.append(val)
    return uniq


def interp_x_at_z(path: List[Point], z: float) -> float | None:
    hits = interp_x_hits_at_z(path, z)
    return min(hits) if hits else None


def path_hits_at_slice(path, z: float, to_points) -> List[float]:
    """Wie interp_x_hits_at_z(), akzeptiert aber auch einen Primitive-Pfad
    (Liste von line/arc-Dicts statt Punkten) via `to_points`."""
    if not path:
        return []
    if isinstance(path[0], dict):
        try:
            path = to_points(path)
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "path_hits_at_slice", exc)
            return []
    return interp_x_hits_at_z(path, z)


def front_operation_side(op: Operation) -> str | None:
    params = getattr(op, "params", {}) or {}
    if op.op_type in (OpType.DRILL, OpType.BORE):
        return "inside"
    if op.op_type == OpType.GROOVE:
        try:
            return "inside" if int(float(params.get("lage", 0) or 0)) == 1 else "outside"
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_operation_side", exc)
            return "outside"
    if op.op_type == OpType.THREAD:
        return "inside" if is_internal_side(params.get("orientation", 0)) else "outside"
    if op.op_type == OpType.ABSPANEN:
        return "inside" if is_internal_side(params.get("side", 0)) else "outside"
    if op.op_type == OpType.KEYWAY:
        return None
    return "outside"


def front_slice_profile(
    *,
    front_program: Dict[str, object],
    front_operations: List[Operation],
    paths: List[list],
    active_index: int | None,
    slice_z: float,
    to_points,
) -> Dict[str, List[float] | float | None]:
    try:
        stock_od = abs(float(front_program.get("xa", 0.0) or 0.0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_slice_profile", exc)
        stock_od = 0.0
    try:
        stock_id = abs(float(front_program.get("xi", 0.0) or 0.0))
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_slice_profile", exc)
        stock_id = 0.0

    outer_hits: List[float] = []
    inner_hits: List[float] = []
    neutral_hits: List[float] = []

    if not front_operations and paths:
        idx = active_index if active_index is not None else 0
        idx = max(0, min(idx, len(paths) - 1))
        raw_hits = [abs(d) for d in path_hits_at_slice(paths[idx], slice_z, to_points) if abs(d) > 1e-6]
        return {
            "outer_hits": sorted(raw_hits, reverse=True),
            "inner_hits": [],
            "neutral_hits": [],
            "all_hits": sorted(raw_hits, reverse=True),
            "outer_fill": max(raw_hits) if raw_hits else (stock_od if stock_od > 1e-6 else None),
            "inner_fill": stock_id if stock_id > 1e-6 else None,
        }

    for op in front_operations:
        if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
            continue
        if getattr(op, "op_type", None) == OpType.KEYWAY:
            continue
        hits = [abs(d) for d in path_hits_at_slice(getattr(op, "path", []) or [], slice_z, to_points) if abs(d) > 1e-6]
        if not hits:
            continue
        side = front_operation_side(op)
        if side == "inside":
            inner_hits.extend(hits)
        elif side == "outside":
            outer_hits.extend(hits)
        else:
            neutral_hits.extend(hits)

    def _uniq_desc(values: List[float]) -> List[float]:
        uniq: List[float] = []
        for val in sorted((abs(float(v)) for v in values if abs(float(v)) > 1e-6), reverse=True):
            if not uniq or abs(val - uniq[-1]) > 1e-6:
                uniq.append(val)
        return uniq

    outer_hits = _uniq_desc(outer_hits)
    inner_hits = _uniq_desc(inner_hits)
    neutral_hits = _uniq_desc(neutral_hits)
    all_hits = _uniq_desc(outer_hits + inner_hits + neutral_hits)

    outer_fill = outer_hits[0] if outer_hits else (stock_od if stock_od > 1e-6 else None)
    inner_fill = inner_hits[-1] if inner_hits else (stock_id if stock_id > 1e-6 else None)

    return {
        "outer_hits": outer_hits,
        "inner_hits": inner_hits,
        "neutral_hits": neutral_hits,
        "all_hits": all_hits,
        "outer_fill": outer_fill,
        "inner_fill": inner_fill,
    }


def front_reference_diameter(
    *,
    front_program: Dict[str, object],
    front_operations: List[Operation],
    to_points,
) -> float:
    candidates: List[float] = []

    for key in ("xa", "xi"):
        try:
            val = abs(float(front_program.get(key, 0.0) or 0.0))
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_reference_diameter", exc)
            val = 0.0
        if val > 1e-6:
            candidates.append(val)

    for op in front_operations:
        if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
            continue
        path = getattr(op, "path", None) or []
        if not path:
            continue
        if isinstance(path[0], dict):
            try:
                pts = to_points(path)
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_reference_diameter", exc)
                pts = []
        else:
            pts = path
        for pt in pts:
            try:
                dia = abs(float(pt[0]))
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_reference_diameter", exc)
                continue
            if dia > 1e-6:
                candidates.append(dia)

        if getattr(op, "op_type", None) == OpType.KEYWAY:
            params = getattr(op, "params", {}) or {}
            try:
                start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
                nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
                radial_side = int(float(params.get("radial_side", 0) or 0))
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "front_reference_diameter", exc)
                continue
            if start_dia > 1e-6:
                candidates.append(start_dia)
                if radial_side != 0 and nut_depth > 1e-6:
                    candidates.append(start_dia + (2.0 * nut_depth))

    return max(candidates, default=10.0)
