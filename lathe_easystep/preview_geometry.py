from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .contour_features import primitive_to_points
from .contour_logic import build_contour_path as build_contour_primitives
from .gcode_utils import is_internal_side, is_left_hand
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

    if abs(root_dia - crest_dia) <= 1e-9:
        return [(crest_dia, start_z), (crest_dia, end_z)]

    path: List[Point] = [(crest_dia, start_z)]
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
    except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
            return False

    # XRA (outer)
    xra = program.get("xra", None)
    if xra is not None:
        try:
            xra_f = _sf(xra)
            if abs(xra_f) > 1e-12:
                x = xra_f if _is_true("xra_absolute") else (xa + xra_f)
                vline(x)
        except Exception:
            pass

    # XRI (inner)
    xri = program.get("xri", None)
    if xri is not None:
        try:
            xri_f = _sf(xri)
            if abs(xri_f) > 1e-12:
                x = xri_f if _is_true("xri_absolute") else (xi + xri_f)
                vline(x)
        except Exception:
            pass

    # ZRA (front)
    zra = program.get("zra", None)
    if zra is not None:
        try:
            zra_f = _sf(zra)
            if abs(zra_f) > 1e-12:
                z = zra_f if _is_true("zra_absolute") else (za + zra_f)
                hline(z)
        except Exception:
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
        except Exception:
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
    except Exception:
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
                    except Exception:
                        pass
        elif isinstance(prim, dict) and prim.get("type") == "line":
            for pt in (prim.get("p1"), prim.get("p2")):
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    try:
                        x_vals.append(float(pt[0]))
                    except Exception:
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
        except Exception:
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
