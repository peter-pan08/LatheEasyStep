from __future__ import annotations

from typing import Dict, List, Tuple


METRIC_THREAD_PRESETS: List[Tuple[str, float, float]] = [
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
    ("M26", 26.0, 3.0),
    ("M27", 27.0, 3.0),
    ("M28", 28.0, 3.0),
    ("M29", 29.0, 3.0),
    ("M30", 30.0, 3.5),
]

TRAPEZOIDAL_THREAD_PRESETS: List[Tuple[str, float, float]] = [
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
    ("Tr 45", 45.0, 7.0),
    ("Tr 50", 50.0, 8.0),
    ("Tr 55", 55.0, 8.0),
    ("Tr 60", 60.0, 10.0),
]


def _preset_dict(entries: List[Tuple[str, float, float]], profile: str) -> Dict[str, Dict[str, object]]:
    result: Dict[str, Dict[str, object]] = {}
    for label, diameter, pitch in entries:
        result[label.upper()] = {
            "label": label,
            "major": diameter,
            "pitch": pitch,
            "profile": profile,
        }
    return result


def validate_thread_preset_data(data: Dict[str, object] | None) -> List[str]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["preset is not a dictionary"]
    label = data.get("label")
    if not isinstance(label, str) or not label.strip():
        errors.append("missing label")
    major = data.get("major")
    if not isinstance(major, (int, float)) or float(major) <= 0.0:
        errors.append("major diameter must be > 0")
    pitch = data.get("pitch")
    if not isinstance(pitch, (int, float)) or float(pitch) <= 0.0:
        errors.append("pitch must be > 0")
    profile = data.get("profile")
    if str(profile or "").strip().lower() not in {"metric", "tr"}:
        errors.append("profile must be 'metric' or 'tr'")
    return errors


THREAD_PRESET_INDEX: Dict[str, Dict[str, object]] = {}
THREAD_PRESET_INDEX.update(_preset_dict(METRIC_THREAD_PRESETS, "metric"))
THREAD_PRESET_INDEX.update(_preset_dict(TRAPEZOIDAL_THREAD_PRESETS, "tr"))


def metric_thread_presets() -> List[Tuple[str, float, float]]:
    return list(METRIC_THREAD_PRESETS)


def trapezoidal_thread_presets() -> List[Tuple[str, float, float]]:
    return list(TRAPEZOIDAL_THREAD_PRESETS)


def get_thread_preset(name: str) -> Dict[str, object] | None:
    preset = THREAD_PRESET_INDEX.get(str(name or "").strip().upper())
    if preset is None:
        return None
    result = dict(preset)
    if validate_thread_preset_data(result):
        return None
    return result
