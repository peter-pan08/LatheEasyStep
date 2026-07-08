from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def normalize_arc_side(value: object | None) -> str:
    text = str(value or "").strip().lower()
    if text in ("innen", "inner", "inside"):
        return "inner"
    if text in ("aussen", "außen", "outer", "outside"):
        return "outer"
    return "auto"


def build_contour_path(params) -> list:
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

        if s.get("x_empty"):
            x = last_x
        else:
            xv = float(s.get("x", 0.0) or 0.0) if not x_is_abs else float(s.get("x", last_x) or last_x)
            x = xv if x_is_abs else (last_x + xv)

        if s.get("z_empty"):
            z = last_z
        else:
            zv = float(s.get("z", 0.0) or 0.0) if not z_is_abs else float(s.get("z", last_z) or last_z)
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
    cur = pts[0]

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
                    continue

        _emit_line(cur, p_next)
        cur = p_next

    return prim


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
            x = float(seg.get("x", x))
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
