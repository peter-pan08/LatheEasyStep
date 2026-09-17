from __future__ import annotations

import math
from typing import Dict, List, Tuple

from .presets import DIN_RELIEF_TABLE, get_din_relief_preset

# Max. Sehnenabweichung (Sagitta) beim Abtasten eines Bogens in Radiusmass -
# deutlich unter der 0.001mm-Ausgaberundung, damit kein Rundungseffekt
# entsteht. Ohne Abtastung wuerde ein Bogen nur durch seine Sehne
# repraesentiert; bei konkaven Bogen (z. B. kleine Rundungen zwischen engerer
# Bohrung und Schulter) baucht die wahre Kontur gegenueber der Sehne nach
# INNEN aus - Schrupp-Zustellrechnungen (Materialreichweite je X-Band), die
# auf der Sehne basieren, wuerden dadurch zu tief zustellen und ins
# Schlichtaufmass bzw. sogar ins Fertigteil schneiden.
_ARC_SAGITTA_TOLERANCE_MM = 0.0005
_ARC_MIN_SEGMENTS = 4
_ARC_MAX_SEGMENTS = 96


def _tessellate_arc(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    center: Tuple[float, float],
    ccw: bool,
) -> List[Tuple[float, float]]:
    """Bogen (X in Durchmessermass, Z) in Zwischenpunkte entlang des wahren
    Kreises zerlegen. Rueckgabe ohne p1, inklusive p2."""
    # Der Bogen ist nur im Radiusmass ein echter Kreis (X-Achse bewegt sich
    # physisch im Radius, auch wenn G7 den X-Wert als Durchmesser ausgibt).
    # G18 G3 (ccw=True) laeuft im Uhrzeigersinn in der (Radius-X, Z)-Ebene -
    # dieselbe Konvention wie bereits verifiziert in
    # gcode_roughing.py:_cycle_extrema_points(). direction/sweep exakt
    # analog uebernommen, damit beide Stellen konsistent bleiben.
    cx_r, cz = center[0] / 2.0, center[1]
    radius = math.hypot((p1[0] - center[0]) / 2.0, p1[1] - cz)
    if radius <= 1e-9:
        return [p2]
    direction = -1 if ccw else 1
    start = math.atan2(p1[1] - cz, (p1[0] - center[0]) / 2.0)
    end = math.atan2(p2[1] - cz, (p2[0] - center[0]) / 2.0)
    sweep = ((end - start) * direction) % (2.0 * math.pi)
    if sweep < 1e-9:
        sweep = 2.0 * math.pi
    tol = min(_ARC_SAGITTA_TOLERANCE_MM, radius * 0.999)
    half_step = math.acos(max(-1.0, min(1.0, 1.0 - tol / radius)))
    if half_step <= 1e-9:
        segments = _ARC_MAX_SEGMENTS
    else:
        segments = math.ceil(sweep / (2.0 * half_step))
    segments = max(_ARC_MIN_SEGMENTS, min(_ARC_MAX_SEGMENTS, segments))
    points: List[Tuple[float, float]] = []
    for i in range(1, segments + 1):
        if i == segments:
            points.append(p2)
        else:
            angle = start + direction * sweep * (i / segments)
            x_r = cx_r + radius * math.cos(angle)
            z = cz + radius * math.sin(angle)
            points.append((x_r * 2.0, z))
    return points


def normalize_relief_mode(value: object | None) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "ignore": "ignore",
        "none": "ignore",
        "0": "ignore",
        "finish_only": "finish_only",
        "finish": "finish_only",
        "only_finish": "finish_only",
        "1": "finish_only",
        "separate": "separate",
        "rough_separate": "separate",
        "2": "separate",
        "full": "full",
        "in_contour": "full",
        "3": "full",
    }
    return mapping.get(text, "finish_only")


def normalize_feature_type(value: object | None) -> str:
    text = str(value or "").strip().lower()
    if text in ("din_relief", "freistich", "hinterschnitt", "din-freistich", "undercut"):
        return "din_relief"
    if text in ("chamfer", "fase"):
        return "chamfer"
    if text in ("radius", "fillet"):
        return "radius"
    return "none"


def resolve_din_relief(feature: Dict[str, object]) -> Dict[str, object]:
    feature = dict(feature or {})
    feature_type = normalize_feature_type(feature.get("feature_type") or feature.get("type"))
    if feature_type != "din_relief":
        return feature
    size = str(feature.get("thread_size") or feature.get("thread") or "").strip().upper()
    side = "internal" if bool(feature.get("internal")) or str(feature.get("side") or "").strip().lower() in ("innen", "internal", "inner") else "external"
    defaults = get_din_relief_preset(size, internal=(side == "internal")) or {}
    merged = dict(defaults)
    merged.update(feature)
    merged["feature_type"] = "din_relief"
    merged["thread_size"] = size
    merged["internal"] = side == "internal"
    merged["side"] = side
    merged["orientation"] = str(merged.get("orientation") or "end").strip().lower()
    return merged


def segment_feature(segment: Dict[str, object]) -> Dict[str, object]:
    if not isinstance(segment, dict):
        return {}
    feature = segment.get("feature")
    if isinstance(feature, dict):
        raw = dict(feature)
    else:
        raw = {}
    if "feature_type" in segment and "feature_type" not in raw:
        raw["feature_type"] = segment.get("feature_type")
    if "thread_size" in segment and "thread_size" not in raw:
        raw["thread_size"] = segment.get("thread_size")
    if "feature_orientation" in segment and "orientation" not in raw:
        raw["orientation"] = segment.get("feature_orientation")
    if "feature_internal" in segment and "internal" not in raw:
        raw["internal"] = segment.get("feature_internal")
    if not raw:
        return {}
    return resolve_din_relief(raw)


def primitive_to_points(primitives: List[Dict[str, object]]) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    last: Tuple[float, float] | None = None

    def _append(point: Tuple[float, float]) -> None:
        nonlocal last
        if point != last:
            points.append(point)
            last = point

    for primitive in primitives or []:
        if not isinstance(primitive, dict):
            continue
        p1_raw = primitive.get("p1")
        p2_raw = primitive.get("p2")
        if not isinstance(p1_raw, (list, tuple)) or len(p1_raw) < 2:
            p1 = None
        else:
            p1 = (float(p1_raw[0]), float(p1_raw[1]))
        if not isinstance(p2_raw, (list, tuple)) or len(p2_raw) < 2:
            p2 = None
        else:
            p2 = (float(p2_raw[0]), float(p2_raw[1]))

        c_raw = primitive.get("c")
        is_arc = (
            str(primitive.get("type") or "").strip().lower() == "arc"
            and p1 is not None
            and p2 is not None
            and isinstance(c_raw, (list, tuple))
            and len(c_raw) >= 2
        )
        if is_arc:
            if p1 is not None:
                _append(p1)
            center = (float(c_raw[0]), float(c_raw[1]))
            for point in _tessellate_arc(p1, p2, center, bool(primitive.get("ccw"))):
                _append(point)
            continue

        if p1 is not None:
            _append(p1)
        if p2 is not None:
            _append(p2)
    return points
