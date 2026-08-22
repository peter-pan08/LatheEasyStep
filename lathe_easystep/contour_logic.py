from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .contour_features import primitive_to_points, segment_feature
from .presets import get_din_relief_preset


def _is_internal(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "inside", "internal", "innen", "id")


def _is_left_hand(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "left", "links", "lh")


def thread_relief_spec(thread_params: Dict[str, object]) -> Dict[str, object] | None:
    """Return the contour feature derived from an automatic DIN-76 thread relief.

    ``thread_overlap`` deliberately positions the G76 endpoint *inside* the
    relief.  The geometry is therefore tied to the thread, never to the end
    of an arbitrary contour segment.
    """
    mode = str(thread_params.get("relief_mode", "off") or "off").strip().lower()
    if mode not in ("suggest", "suggest_din_relief", "automatic", "auto"):
        return None
    try:
        diameter = float(thread_params.get("major_diameter", 0.0) or 0.0)
        length = abs(float(thread_params.get("length", 0.0) or 0.0))
        start_z = float(thread_params.get("thread_start_z", 0.0) or 0.0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Automatischer DIN-Freistich: Gewindedaten sind ungueltig.") from exc
    size = f"M{diameter:g}"
    internal = _is_internal(thread_params.get("orientation", 0))
    preset = get_din_relief_preset(size, internal=internal)
    if preset is None:
        raise ValueError(f"Automatischer DIN-Freistich: kein DIN-76-Datensatz fuer {size} vorhanden.")
    overlap = float(preset.get("thread_overlap", 0.0) or 0.0)
    width = float(preset.get("width", 0.0) or 0.0)
    depth = float(preset.get("depth", 0.0) or 0.0)
    if overlap <= 0.0 or width <= 0.0 or depth <= 0.0:
        raise ValueError(f"Automatischer DIN-Freistich: unvollstaendige DIN-76-Daten fuer {size}.")
    if overlap > length + 1e-9:
        raise ValueError(
            f"Freistich DIN 76 {size}: Gewindeueberdeckung f={overlap:.3f}mm "
            f"ist laenger als die Gewindelaenge {length:.3f}mm."
        )
    z_dir = 1.0 if _is_left_hand(thread_params.get("hand", 0)) else -1.0
    end_z = start_z + z_dir * length
    entry_z = end_z - z_dir * overlap
    exit_z = entry_z + z_dir * width
    return {
        "feature_type": "din_relief",
        "source": "thread_auto",
        "thread_size": size,
        "norm": str(thread_params.get("relief_norm", "DIN 76-A") or "DIN 76-A"),
        "internal": internal,
        "diameter": diameter,
        "width": width,
        "bottom_width": float(preset.get("bottom_width", 0.0) or 0.0),
        "short_width": float(preset.get("short_width", 0.0) or 0.0),
        "short_bottom_width": float(preset.get("short_bottom_width", 0.0) or 0.0),
        "variant": "standard",
        "depth": depth,
        "radius": float(preset.get("radius", 0.0) or 0.0),
        "thread_overlap": overlap,
        "entry_z": entry_z,
        "exit_z": exit_z,
    }


def normalize_arc_side(value: object | None) -> str:
    text = str(value or "").strip().lower()
    if text in ("innen", "inner", "inside"):
        return "inner"
    if text in ("aussen", "außen", "outer", "outside"):
        return "outer"
    return "auto"


def build_contour_path(params) -> list:
    variants = build_contour_variants(params)
    return variants["finish_primitives"]


def contour_supports_thread_relief(params: Dict[str, object], feature: Dict[str, object]) -> bool:
    """Whether a contour has the complete cylindrical span required by feature."""
    probe = dict(params or {})
    probe["auto_thread_reliefs"] = [dict(feature)]
    variants = build_contour_variants(probe)
    return any(item.get("source") == "thread_auto" for item in variants["feature_primitives"])


def select_thread_relief_for_contour(params: Dict[str, object], feature: Dict[str, object]) -> Dict[str, object] | None:
    """Select the DIN long form, or its valid short form, for this contour."""
    if contour_supports_thread_relief(params, feature):
        return feature
    try:
        short_width = float(feature.get("short_width", 0.0) or 0.0)
        width = float(feature["width"])
        entry_z = float(feature["entry_z"])
        exit_z = float(feature["exit_z"])
    except (KeyError, TypeError, ValueError):
        return None
    if short_width <= 0.0 or short_width >= width - 1e-9:
        return None
    short_feature = dict(feature)
    short_feature["_source_feature_id"] = id(feature)
    short_feature["width"] = short_width
    short_feature["bottom_width"] = float(feature.get("short_bottom_width", 0.0) or 0.0)
    short_feature["exit_z"] = entry_z + (1.0 if exit_z >= entry_z else -1.0) * short_width
    short_feature["variant"] = "short"
    return short_feature if contour_supports_thread_relief(params, short_feature) else None


def build_contour_variants(params) -> Dict[str, List[Dict[str, object]]]:
    if isinstance(params, dict):
        segments = params.get("segments") or []
    else:
        segments = params or []

    start_x = 0.0
    start_z = 0.0
    if isinstance(params, dict):
        start_x = float(params.get("start_x", 0.0) or 0.0)
        start_z = float(params.get("start_z", 0.0) or 0.0)

    pts = [(start_x, start_z)]
    last_x = start_x
    last_z = start_z

    coord_mode = 0
    if isinstance(params, dict):
        try:
            coord_mode = int(params.get("coord_mode", 0) or 0)
        except Exception:
            coord_mode = 0

    incremental = coord_mode == 1

    for s in segments:
        if not isinstance(s, dict):
            continue

        def _axis_is_abs(axis: str) -> Optional[bool]:
            k_abs = f"{axis}_abs"
            if k_abs in s:
                try:
                    return bool(s.get(k_abs))
                except Exception:
                    pass
            k_inc = f"{axis}_incremental"
            if k_inc in s:
                try:
                    return not bool(s.get(k_inc))
                except Exception:
                    pass
            k_mode = f"{axis}_mode"
            if k_mode in s:
                v = str(s.get(k_mode) or "").strip().lower()
                if v in ("abs", "absolute"):
                    return True
                if v in ("ink", "inc", "incremental"):
                    return False
            return None

        x_is_abs = _axis_is_abs("x")
        z_is_abs = _axis_is_abs("z")
        if x_is_abs is None:
            x_is_abs = not incremental
        if z_is_abs is None:
            z_is_abs = not incremental

        def _raw_axis(key: str, fallback: float) -> float:
            # Nicht "s.get(key, fallback) or fallback" verwenden: ein
            # gueltiges, bewusst gesetztes Ziel von exakt 0.0 ist in Python
            # falsy und wuerde damit stillschweigend durch den vorherigen
            # Punkt ersetzt (X=0/Z=0 sind z. B. bei Plan-/Zentrierpunkten
            # voellig normale, haeufige Zielwerte).
            raw = s.get(key)
            return float(raw) if raw is not None else float(fallback)

        if s.get("x_empty"):
            x = last_x
        else:
            xv = _raw_axis("x", 0.0 if not x_is_abs else last_x)
            x = xv if x_is_abs else (last_x + xv)

        if s.get("z_empty"):
            z = last_z
        else:
            zv = _raw_axis("z", 0.0 if not z_is_abs else last_z)
            z = zv if z_is_abs else (last_z + zv)

        pts.append((x, z))
        last_x, last_z = x, z

    if len(pts) < 2:
        return []

    def _v(a, b):
        return (b[0] - a[0], b[1] - a[1])

    def _norm(v):
        l = math.hypot(v[0], v[1])
        if l <= 1e-12:
            return (0.0, 0.0), 0.0
        return (v[0] / l, v[1] / l), l

    def _perp_ccw(u):
        return (-u[1], u[0])

    def _dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    def _cross(a, b):
        return a[0] * b[1] - a[1] * b[0]

    prim = []
    reliefs: List[List[Dict[str, object]]] = []
    cur = pts[0]
    # Primitive-Indexbereich [start, end) je Segment - wird gebraucht, um
    # einen Freistich (din_relief) spaeter an der RICHTIGEN Stelle in `prim`
    # einzufuegen, statt ihn immer nur vor/nach der GESAMTEN Kontur anzuhaengen.
    segment_prim_bounds: List[Tuple[int, int]] = []

    def _emit_line(p1, p2):
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) <= 1e-9:
            return
        prim.append({"type": "line", "p1": [float(p1[0]), float(p1[1])], "p2": [float(p2[0]), float(p2[1])]})

    def _emit_arc(p1, p2, c, ccw):
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) <= 1e-9:
            return
        prim.append({
            "type": "arc",
            "p1": [float(p1[0]), float(p1[1])],
            "p2": [float(p2[0]), float(p2[1])],
            "c": [float(c[0]), float(c[1])],
            "ccw": bool(ccw),
        })

    for i in range(1, len(pts)):
        p_next = pts[i]
        seg_prim_start = len(prim)
        if 1 <= i < len(pts) - 1:
            seg = segments[i - 1] if (i - 1) < len(segments) else {}
            edge_kind = (seg.get("edge") or "none").strip().lower()
            edge_size = float(seg.get("edge_size") or 0.0)

            if edge_kind in ("radius", "fillet") and edge_size > 1e-9:
                p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
                p0_r = (p0[0] / 2.0, p0[1])
                p1_r = (p1[0] / 2.0, p1[1])
                p2_r = (p2[0] / 2.0, p2[1])
                u1, l1 = _norm(_v(p1_r, p0_r))
                u2, l2 = _norm(_v(p1_r, p2_r))
                if l1 > 1e-9 and l2 > 1e-9:
                    cosang = max(-1.0, min(1.0, _dot(u1, u2)))
                    ang = math.acos(cosang)
                    if ang > 1e-6 and abs(math.pi - ang) > 1e-6:
                        r = edge_size
                        tan_half = math.tan(ang / 2.0)
                        if tan_half <= 1e-9:
                            r = 0.0
                        t = r * tan_half if r > 0.0 else 0.0
                        max_t = min(l1, l2) * 0.999
                        if t > max_t and tan_half > 1e-9:
                            r = max_t / tan_half
                            t = max_t

                        if r > 1e-9 and t > 1e-9:
                            pt1_r = (p1_r[0] + u1[0] * t, p1_r[1] + u1[1] * t)
                            pt2_r = (p1_r[0] + u2[0] * t, p1_r[1] + u2[1] * t)
                            n1 = _perp_ccw(u1)
                            n2 = _perp_ccw(u2)
                            tol = max(0.01, r * 0.01)
                            candidates = []
                            for s1 in (1.0, -1.0):
                                c1 = (pt1_r[0] + n1[0] * r * s1, pt1_r[1] + n1[1] * r * s1)
                                for s2 in (1.0, -1.0):
                                    c2 = (pt2_r[0] + n2[0] * r * s2, pt2_r[1] + n2[1] * r * s2)
                                    if math.hypot(c1[0] - c2[0], c1[1] - c2[1]) <= tol:
                                        candidates.append(((c1[0] + c2[0]) * 0.5, (c1[1] + c2[1]) * 0.5))
                            if candidates:
                                arc_side = normalize_arc_side(seg.get("arc_side"))
                                bx = u1[0] + u2[0]
                                bz = u1[1] + u2[1]
                                bl = math.hypot(bx, bz)
                                if bl > 1e-9:
                                    bx /= bl
                                    bz /= bl
                                best_r = None
                                best_score = -1e9
                                for c in candidates:
                                    dx = c[0] - p1_r[0]
                                    dz = c[1] - p1_r[1]
                                    score = dx * bx + dz * bz
                                    if arc_side == "inner" and score < 0:
                                        continue
                                    if arc_side == "outer" and score > 0:
                                        continue
                                    if abs(score) > best_score:
                                        best_score = abs(score)
                                        best_r = c
                                if best_r is None:
                                    best_r = candidates[0]
                                pt1_d = (pt1_r[0] * 2.0, pt1_r[1])
                                pt2_d = (pt2_r[0] * 2.0, pt2_r[1])
                                best_d = (best_r[0] * 2.0, best_r[1])
                                _emit_line(cur, pt1_d)
                                v1 = (pt1_r[0] - best_r[0], pt1_r[1] - best_r[1])
                                v2 = (pt2_r[0] - best_r[0], pt2_r[1] - best_r[1])
                                ccw = _cross(v1, v2) < 0.0
                                _emit_arc(pt1_d, pt2_d, best_d, ccw)
                                cur = pt2_d
                                segment_prim_bounds.append((seg_prim_start, len(prim)))
                                continue

            elif edge_kind in ("chamfer", "fase") and edge_size > 1e-9:
                p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
                u1, l1 = _norm(_v(p0, p1))
                u2, l2 = _norm(_v(p1, p2))
                if l1 > 1e-9 and l2 > 1e-9:
                    d = min(edge_size, l1 * 0.999, l2 * 0.999)
                    pc1 = (p1[0] - u1[0] * d, p1[1] - u1[1] * d)
                    pc2 = (p1[0] + u2[0] * d, p1[1] + u2[1] * d)
                    _emit_line(cur, pc1)
                    _emit_line(pc1, pc2)
                    cur = pc2
                    segment_prim_bounds.append((seg_prim_start, len(prim)))
                    continue

        _emit_line(cur, p_next)
        cur = p_next
        segment_prim_bounds.append((seg_prim_start, len(prim)))

    # Freistiche (din_relief) duerfen an JEDEM Segment sitzen, nicht nur am
    # allerersten/-letzten der GESAMTEN Kontur - die Geometrieformel selbst
    # war bereits generisch (sie hing nur vom Segment-Punktpaar pts[idx]/
    # pts[idx+1] ab); die frueher harte idx==0/idx==len(segments)-1-Schranke
    # war eine rein kuenstliche Einschraenkung. Verarbeitung in ABSTEIGENDER
    # Segmentreihenfolge, damit ein Einfuegen bei hoeherem idx die bereits
    # ermittelten `segment_prim_bounds` fuer NIEDRIGERE idx nicht verschiebt.
    relief_specs: List[Tuple[int, str, Dict[str, object]]] = []
    for idx, seg in enumerate(segments):
        feature = segment_feature(seg if isinstance(seg, dict) else {})
        if feature.get("feature_type") != "din_relief":
            continue
        if idx >= len(segment_prim_bounds):
            continue
        anchor_mode = str(feature.get("orientation") or "end").strip().lower()
        if anchor_mode not in ("start", "end"):
            anchor_mode = "end"
        relief_specs.append((idx, anchor_mode, feature))

    for idx, anchor_mode, feature in sorted(relief_specs, key=lambda item: item[0], reverse=True):
        p_prev = pts[idx]
        p_anchor = pts[idx + 1] if idx + 1 < len(pts) else pts[idx]
        relief = _build_relief_primitives(p_prev, p_anchor, feature, prepend=(anchor_mode == "start"))
        if not relief:
            continue
        splice_at = segment_prim_bounds[idx][0] if anchor_mode == "start" else segment_prim_bounds[idx][1]
        prim[splice_at:splice_at] = relief
        reliefs.append(relief)

    # Automatische DIN-76-Freistiche kommen von einer Gewindeoperation. Sie
    # werden nur in eine passende zylindrische Gewindestrecke eingespleisst;
    # ein beliebiges Konturende ist bewusst kein zulassiger Ersatzanker.
    auto_reliefs = []
    if isinstance(params, dict):
        auto_reliefs = params.get("auto_thread_reliefs") or []
    for feature in auto_reliefs:
        if not isinstance(feature, dict):
            continue
        relief = _splice_thread_relief(prim, feature)
        if relief:
            reliefs.append(relief)

    feature_primitives = [item for relief in reliefs for item in relief]
    return {
        "finish_primitives": prim,
        "rough_primitives": _primitives_without_relief(prim),
        "feature_primitives": feature_primitives,
        "finish_points": primitive_to_points(prim),
        "rough_points": primitive_to_points(_primitives_without_relief(prim)),
        "feature_points": primitive_to_points(feature_primitives),
    }


def _splice_thread_relief(primitives: List[Dict[str, object]], feature: Dict[str, object]) -> List[Dict[str, object]]:
    """Replace a cylindrical contour span by the derived DIN-76 relief.

    ``g2`` is the full axial span and ``g1`` the lower span.  The two
    transitions are straight flanks followed by tangential arcs of the DIN
    radius.  Coordinates remain diameter-programmed externally, while all
    radius calculations use physical X radii.
    """
    try:
        diameter = float(feature["diameter"])
        entry_z = float(feature["entry_z"])
        exit_z = float(feature["exit_z"])
        depth = abs(float(feature["depth"]))
        bottom_width = float(feature.get("bottom_width", 0.0) or 0.0)
        relief_radius = float(feature.get("radius", 0.0) or 0.0)
    except (KeyError, TypeError, ValueError):
        return []
    lo, hi = sorted((entry_z, exit_z))
    eps = 1e-6
    for index, primitive in enumerate(primitives):
        if primitive.get("type") != "line" or primitive.get("feature_type") == "din_relief":
            continue
        p1 = primitive.get("p1") or ()
        p2 = primitive.get("p2") or ()
        if len(p1) < 2 or len(p2) < 2:
            continue
        x1, z1 = float(p1[0]), float(p1[1])
        x2, z2 = float(p2[0]), float(p2[1])
        if abs(x1 - x2) > eps or abs(x1 - diameter) > 0.05:
            continue
        if min(z1, z2) > lo + eps or max(z1, z2) < hi - eps:
            continue
        travel = 1.0 if z2 >= z1 else -1.0
        first_z, second_z = (entry_z, exit_z) if (exit_z - entry_z) * travel >= 0 else (exit_z, entry_z)
        width = abs(second_z - first_z)
        if bottom_width <= eps:
            # Compatibility for old manually stored features.  Automatic DIN
            # data always supplies g1 explicitly.
            bottom_width = width * 0.5
        if bottom_width >= width - eps:
            return []
        x_relief = diameter + (2.0 * depth if bool(feature.get("internal")) else -2.0 * depth)
        # DIN 76 defines g1 and g2 from the shoulder, not a symmetric
        # trapezoid.  The thread-side transition is the 30 degree flank with
        # axial width g2-g1; g1 is the straight relief-ground distance to the
        # rounded shoulder.
        flank_width = width - bottom_width
        if flank_width <= eps:
            return []
        # Profile orientation comes from the thread travel, never from
        # internal/external.  The 30 degree flank is always where the thread
        # enters the relief; contour segments may be stored in either travel
        # direction and are reversed only after this geometry is built.
        thread_z_dir = 1.0 if exit_z >= entry_z else -1.0
        surface_r, relief_r = diameter / 2.0, x_relief / 2.0
        radial_dir = 1.0 if surface_r > relief_r else -1.0
        # The shoulder radius cannot exceed the available radial depth.  This
        # matters for the very shallow DIN inside forms (dg = D + 0.5).
        shoulder_radius = min(relief_radius, abs(surface_r - relief_r) * 0.999, bottom_width * 0.999)
        if shoulder_radius <= eps:
            return []
        flank_end = (relief_r, entry_z + thread_z_dir * flank_width)
        arc_start = (relief_r, exit_z - thread_z_dir * shoulder_radius)
        arc_end = (relief_r + radial_dir * shoulder_radius, exit_z)
        arc_center = (relief_r + radial_dir * shoulder_radius, exit_z - thread_z_dir * shoulder_radius)
        forward_items: List[Dict[str, object]] = []
        for a, b in (((surface_r, entry_z), flank_end), (flank_end, arc_start)):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > eps:
                forward_items.append({"type": "line", "p1": [a[0] * 2.0, a[1]], "p2": [b[0] * 2.0, b[1]]})
        v1 = (arc_start[0] - arc_center[0], arc_start[1] - arc_center[1])
        v2 = (arc_end[0] - arc_center[0], arc_end[1] - arc_center[1])
        forward_items.append({
            "type": "arc", "p1": [arc_start[0] * 2.0, arc_start[1]],
            "p2": [arc_end[0] * 2.0, arc_end[1]],
            "c": [arc_center[0] * 2.0, arc_center[1]],
            "ccw": (v1[0] * v2[1] - v1[1] * v2[0]) < 0.0,
        })
        if math.hypot(surface_r - arc_end[0], exit_z - arc_end[1]) > eps:
            forward_items.append({"type": "line", "p1": [arc_end[0] * 2.0, arc_end[1]], "p2": [surface_r * 2.0, exit_z]})

        forward_travel = (first_z - entry_z) * thread_z_dir >= -eps
        if forward_travel:
            profile_items = forward_items
        else:
            profile_items = []
            for item in reversed(forward_items):
                reversed_item = dict(item)
                reversed_item["p1"], reversed_item["p2"] = list(item["p2"]), list(item["p1"])
                if reversed_item.get("type") == "arc":
                    reversed_item["ccw"] = not bool(item.get("ccw"))
                profile_items.append(reversed_item)

        feature_data = {"role": "feature", "feature_type": "din_relief", "source": "thread_auto"}
        relief = [{**item, **feature_data} for item in profile_items]
        replacement: List[Dict[str, object]] = []
        for a, b in (((x1, z1), (diameter, first_z)), ((diameter, second_z), (x2, z2))):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > eps:
                replacement.append({"type": "line", "p1": [a[0], a[1]], "p2": [b[0], b[1]]})
            if a == (x1, z1):
                replacement.extend(relief)
        primitives[index:index + 1] = replacement
        return relief
    return []


def _build_relief_primitives(
    p_prev: Tuple[float, float],
    p_anchor: Tuple[float, float],
    feature: Dict[str, object],
    *,
    prepend: bool,
) -> List[Dict[str, object]]:
    try:
        width = abs(float(feature.get("width", 0.0) or 0.0))
        depth = abs(float(feature.get("depth", 0.0) or 0.0))
    except Exception:
        return []
    if width <= 1e-9 or depth <= 1e-9:
        return []

    x_anchor, z_anchor = float(p_anchor[0]), float(p_anchor[1])
    dx = float(p_anchor[0]) - float(p_prev[0])
    dz = float(p_anchor[1]) - float(p_prev[1])
    if abs(dx) < 1e-9 and abs(dz) < 1e-9:
        dz = -1.0
    z_dir = -1.0 if dz <= 0.0 else 1.0
    if prepend:
        z_dir *= -1.0
    internal = bool(feature.get("internal"))
    x_relief = x_anchor + (2.0 * depth if internal else -2.0 * depth)
    z_far = z_anchor + (z_dir * width)
    transition = str(feature.get("transition") or "radius").strip().lower()
    transition_size = min(width * 0.5, abs(float(feature.get("transition_size", 0.0) or 0.0)))

    points: List[Tuple[float, float]] = [(x_anchor, z_anchor)]
    if transition == "chamfer" and transition_size > 1e-9:
        z_mid = z_anchor + (z_dir * transition_size)
        x_mid = x_anchor + ((x_relief - x_anchor) * 0.5)
        points.extend([(x_mid, z_mid), (x_relief, z_mid)])
    else:
        points.append((x_relief, z_anchor))
    points.extend([(x_relief, z_far), (x_anchor, z_far)])

    primitives: List[Dict[str, object]] = []
    for p1, p2 in zip(points, points[1:]):
        if abs(p2[0] - p1[0]) <= 1e-9 and abs(p2[1] - p1[1]) <= 1e-9:
            continue
        primitives.append(
            {
                "type": "line",
                "role": "feature",
                "feature_type": "din_relief",
                "p1": [float(p1[0]), float(p1[1])],
                "p2": [float(p2[0]), float(p2[1])],
            }
        )
    return primitives


def _primitives_without_relief(primitives: List[Dict[str, object]]) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    eps = 1e-9
    for primitive in primitives or []:
        if str(primitive.get("feature_type") or "").strip().lower() == "din_relief":
            continue
        item = dict(primitive)
        if item.get("type") != "line" or not result or result[-1].get("type") != "line":
            result.append(item)
            continue
        previous = result[-1]
        p0, p1 = previous.get("p1"), previous.get("p2")
        q0, q1 = item.get("p1"), item.get("p2")
        if not all(isinstance(point, (list, tuple)) and len(point) >= 2 for point in (p0, p1, q0, q1)):
            result.append(item)
            continue
        # Nach dem Ausblenden eines U-foermigen Freistichs liegen zwei
        # Teilstuecke derselben zylindrischen Linie mit einer Luecke dazwischen.
        # Fuer die Schruppkontur ist genau diese Luecke wieder die unveraenderte
        # Zylinderflaeche; verbinden und zusammenfassen, damit G71/G72 keine
        # parallelen Null-/Folgesegmente erhaelt.
        if abs(float(p1[0]) - float(q0[0])) <= eps and abs(float(p1[0]) - float(p0[0])) <= eps and abs(float(q1[0]) - float(q0[0])) <= eps:
            previous["p2"] = [float(q1[0]), float(q1[1])]
            continue
        result.append(item)
    return result


def validate_contour_segments_for_profile(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    segs = params.get("contour_segments", params.get("segments", [])) or []

    if not isinstance(segs, list) or len(segs) < 2:
        errors.append("Kontur: mindestens 2 Segmente/Zeilen erforderlich.")
        return False, errors

    try:
        start_x = float(params.get("start_x", 0.0))
        start_z = float(params.get("start_z", 0.0))
    except Exception:
        errors.append("Kontur: ungültiger Startpunkt (start_x/start_z).")
        return False, errors

    pts: List[Tuple[float, float]] = [(start_x, start_z)]
    x, z = start_x, start_z
    for i, seg in enumerate(segs):
        try:
            # Segmente, die nur eine Achse aendern (mode='x'/'z'), tragen fuer
            # die jeweils andere Achse einen Platzhalterwert (haeufig 0.0) mit
            # x_empty/z_empty == True. Dieser Platzhalter darf hier NICHT als
            # echtes Ziel uebernommen werden, sonst entstehen falsche Punkte
            # (z. B. Sprung nach Z=0 statt Beibehalten der vorherigen Z) - das
            # fuehrte zu falschen "Radius zu gross"/"colinear"-Fehlern und
            # damit zu einer geleerten Kontur-Vorschau.
            if not seg.get("x_empty"):
                x = float(seg.get("x", x))
            if not seg.get("z_empty"):
                z = float(seg.get("z", z))
        except Exception:
            errors.append(f"Zeile {i+1}: X/Z ungültig.")
            continue
        pts.append((x, z))

    if len(pts) != len(segs) + 1:
        errors.append("Kontur: interne Punktliste inkonsistent.")
        return False, errors

    for i, seg in enumerate(segs):
        etype = (seg.get("edge_type", seg.get("edge")) or "none").strip().lower()
        if etype in ("none", "", "keine"):
            continue
        if i == len(segs) - 1:
            errors.append(f"Zeile {i+1}: {etype} am Ende ist geometrisch unmöglich (keine Folge-Kante).")
            continue
        try:
            ev = float(seg.get("edge_value", seg.get("edge_size", 0.0)) or 0.0)
        except Exception:
            errors.append(f"Zeile {i+1}: Kantenmaß ungültig.")
            continue
        if ev <= 0.0:
            errors.append(f"Zeile {i+1}: Kantenmaß muss > 0 sein.")
            continue

        p0 = pts[i]
        p1 = pts[i + 1]
        p2 = pts[i + 2]

        def vlen(v):
            return (v[0] * v[0] + v[1] * v[1]) ** 0.5

        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = vlen(v1)
        l2 = vlen(v2)
        if l1 < 1e-9 or l2 < 1e-9:
            errors.append(f"Zeile {i+1}: Segmentlänge zu klein für {etype}.")
            continue

        cross = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(cross) < 1e-9:
            errors.append(f"Zeile {i+1}: {etype} ist nur an einer Ecke möglich (Segmente sind colinear).")
            continue

        if etype in ("chamfer", "fase"):
            if ev >= min(l1, l2):
                errors.append(f"Zeile {i+1}: Fase ist zu groß für die angrenzenden Segmente.")
        elif etype in ("radius", "r", "fillet"):
            p0_r = (p0[0] / 2.0, p0[1])
            p1_r = (p1[0] / 2.0, p1[1])
            p2_r = (p2[0] / 2.0, p2[1])
            v1_r = (p0_r[0] - p1_r[0], p0_r[1] - p1_r[1])
            v2_r = (p2_r[0] - p1_r[0], p2_r[1] - p1_r[1])
            l1_r = vlen(v1_r)
            l2_r = vlen(v2_r)
            if l1_r < 1e-9 or l2_r < 1e-9:
                errors.append(f"Zeile {i+1}: Segmentlänge zu klein für Radius.")
                continue
            cosang = (v1_r[0] * v2_r[0] + v1_r[1] * v2_r[1]) / (l1_r * l2_r)
            cosang = max(-1.0, min(1.0, cosang))
            ang = math.acos(cosang)
            t = ev / math.tan(ang / 2.0)
            if t >= l1_r or t >= l2_r:
                errors.append(f"Zeile {i+1}: Radius ist zu groß für die angrenzenden Segmente.")
        else:
            errors.append(f"Zeile {i+1}: unbekannter Kantentyp '{etype}'.")

    return (len(errors) == 0), errors
