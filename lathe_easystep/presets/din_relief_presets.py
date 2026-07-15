from __future__ import annotations

from typing import Dict, List


RELIEF_NORMS = ["DIN 76-A", "DIN 76-B", "DIN 76-C"]

DIN_RELIEF_TABLE: Dict[str, Dict[str, Dict[str, object]]] = {
    "M3": {"external": {"width": 0.8, "depth": 0.25, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 0.8, "depth": 0.20, "transition": "radius", "transition_size": 0.2}},
    "M4": {"external": {"width": 1.0, "depth": 0.30, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 1.0, "depth": 0.25, "transition": "radius", "transition_size": 0.2}},
    "M5": {"external": {"width": 1.2, "depth": 0.35, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 1.2, "depth": 0.30, "transition": "radius", "transition_size": 0.2}},
    "M6": {"external": {"width": 1.5, "depth": 0.40, "transition": "radius", "transition_size": 0.25}, "internal": {"width": 1.5, "depth": 0.35, "transition": "radius", "transition_size": 0.25}},
    "M7": {"external": {"width": 1.6, "depth": 0.45, "transition": "radius", "transition_size": 0.25}, "internal": {"width": 1.6, "depth": 0.40, "transition": "radius", "transition_size": 0.25}},
    "M8": {"external": {"width": 1.8, "depth": 0.50, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 1.8, "depth": 0.45, "transition": "radius", "transition_size": 0.3}},
    "M9": {"external": {"width": 1.9, "depth": 0.55, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 1.9, "depth": 0.50, "transition": "radius", "transition_size": 0.3}},
    "M10": {"external": {"width": 2.0, "depth": 0.60, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 2.0, "depth": 0.55, "transition": "radius", "transition_size": 0.3}},
    "M11": {"external": {"width": 2.1, "depth": 0.68, "transition": "radius", "transition_size": 0.35}, "internal": {"width": 2.1, "depth": 0.60, "transition": "radius", "transition_size": 0.35}},
    "M12": {"external": {"width": 2.3, "depth": 0.75, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.3, "depth": 0.65, "transition": "radius", "transition_size": 0.4}},
    "M13": {"external": {"width": 2.5, "depth": 0.80, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.5, "depth": 0.70, "transition": "radius", "transition_size": 0.4}},
    "M14": {"external": {"width": 2.6, "depth": 0.85, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.6, "depth": 0.75, "transition": "radius", "transition_size": 0.4}},
    "M15": {"external": {"width": 2.8, "depth": 0.92, "transition": "radius", "transition_size": 0.45}, "internal": {"width": 2.8, "depth": 0.82, "transition": "radius", "transition_size": 0.45}},
    "M16": {"external": {"width": 3.0, "depth": 1.00, "transition": "radius", "transition_size": 0.5}, "internal": {"width": 3.0, "depth": 0.90, "transition": "radius", "transition_size": 0.5}},
    "M17": {"external": {"width": 3.1, "depth": 1.05, "transition": "radius", "transition_size": 0.5}, "internal": {"width": 3.1, "depth": 0.95, "transition": "radius", "transition_size": 0.5}},
    "M18": {"external": {"width": 3.3, "depth": 1.12, "transition": "radius", "transition_size": 0.55}, "internal": {"width": 3.3, "depth": 1.00, "transition": "radius", "transition_size": 0.55}},
    "M19": {"external": {"width": 3.4, "depth": 1.18, "transition": "radius", "transition_size": 0.55}, "internal": {"width": 3.4, "depth": 1.05, "transition": "radius", "transition_size": 0.55}},
    "M20": {"external": {"width": 3.6, "depth": 1.25, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.6, "depth": 1.10, "transition": "radius", "transition_size": 0.6}},
    "M21": {"external": {"width": 3.7, "depth": 1.30, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.7, "depth": 1.15, "transition": "radius", "transition_size": 0.6}},
    "M22": {"external": {"width": 3.8, "depth": 1.35, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.8, "depth": 1.20, "transition": "radius", "transition_size": 0.6}},
    "M23": {"external": {"width": 4.0, "depth": 1.45, "transition": "radius", "transition_size": 0.65}, "internal": {"width": 4.0, "depth": 1.30, "transition": "radius", "transition_size": 0.65}},
    "M24": {"external": {"width": 4.2, "depth": 1.55, "transition": "radius", "transition_size": 0.65}, "internal": {"width": 4.2, "depth": 1.40, "transition": "radius", "transition_size": 0.65}},
    "M25": {"external": {"width": 4.3, "depth": 1.62, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.3, "depth": 1.46, "transition": "radius", "transition_size": 0.7}},
    "M26": {"external": {"width": 4.4, "depth": 1.68, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.4, "depth": 1.52, "transition": "radius", "transition_size": 0.7}},
    "M27": {"external": {"width": 4.5, "depth": 1.74, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.5, "depth": 1.58, "transition": "radius", "transition_size": 0.7}},
    "M28": {"external": {"width": 4.6, "depth": 1.80, "transition": "radius", "transition_size": 0.75}, "internal": {"width": 4.6, "depth": 1.64, "transition": "radius", "transition_size": 0.75}},
    "M29": {"external": {"width": 4.8, "depth": 1.88, "transition": "radius", "transition_size": 0.75}, "internal": {"width": 4.8, "depth": 1.72, "transition": "radius", "transition_size": 0.75}},
    "M30": {"external": {"width": 5.0, "depth": 2.00, "transition": "radius", "transition_size": 0.8}, "internal": {"width": 5.0, "depth": 1.84, "transition": "radius", "transition_size": 0.8}},
}


def relief_thread_sizes() -> list[str]:
    return sorted(DIN_RELIEF_TABLE.keys(), key=lambda item: float(item[1:]) if item[1:].replace(".", "", 1).isdigit() else 999.0)


def validate_din_relief_preset_data(data: Dict[str, object] | None) -> List[str]:
    """Plausibilitaetspruefung fuer einen einzelnen Freistich-Datensatz
    (Breite/Tiefe/Uebergang), analog zu validate_thread_preset_data."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["preset is not a dictionary"]
    width = data.get("width")
    if not isinstance(width, (int, float)) or float(width) <= 0.0:
        errors.append("width must be > 0")
    depth = data.get("depth")
    if not isinstance(depth, (int, float)) or float(depth) <= 0.0:
        errors.append("depth must be > 0")
    transition = str(data.get("transition") or "").strip().lower()
    if transition not in {"radius", "chamfer"}:
        errors.append("transition must be 'radius' or 'chamfer'")
    transition_size = data.get("transition_size")
    if not isinstance(transition_size, (int, float)) or float(transition_size) <= 0.0:
        errors.append("transition_size must be > 0")
    return errors


def get_din_relief_preset(thread_size: str, internal: bool = False) -> Dict[str, object] | None:
    side = "internal" if internal else "external"
    preset = DIN_RELIEF_TABLE.get(str(thread_size or "").strip().upper(), {}).get(side)
    if not preset or validate_din_relief_preset_data(preset):
        return None
    return dict(preset)


def get_thread_with_relief(thread_size: str, internal: bool = False) -> Dict[str, object] | None:
    preset = get_din_relief_preset(thread_size, internal=internal)
    if preset is None:
        return None
    preset["thread_size"] = str(thread_size or "").strip().upper()
    preset["internal"] = bool(internal)
    preset["side"] = "internal" if internal else "external"
    return preset
