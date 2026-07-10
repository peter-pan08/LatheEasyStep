from __future__ import annotations

from typing import Dict, List, Tuple

from .presets import DIN_RELIEF_TABLE, get_din_relief_preset


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
    for primitive in primitives or []:
        if not isinstance(primitive, dict):
            continue
        for key in ("p1", "p2"):
            p = primitive.get(key)
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                continue
            point = (float(p[0]), float(p[1]))
            if point != last:
                points.append(point)
                last = point
    return points
