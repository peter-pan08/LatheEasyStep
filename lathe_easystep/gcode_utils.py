from __future__ import annotations

from typing import Dict, List, Tuple

from .model import OpType

Point = Tuple[float, float]


def require(params: Dict[str, object], keys: List[str], op_label: str) -> None:
    for key in keys:
        if key not in params:
            raise ValueError(f"Fehler in Operation {op_label}: Pflicht-Parameter fehlt: '{key}'. Bitte im Handler/UI bei dieser Operation nachtragen.")
        v = params[key]
        if v is None or v == "":
            raise ValueError(f"Fehler in Operation {op_label}: Pflicht-Parameter ist leer: '{key}'. Bitte im Handler/UI bei dieser Operation nachtragen.")


def require_positive(params: Dict[str, object], keys: List[str], op_label: str) -> None:
    for key in keys:
        try:
            val = float(params.get(key, 0))
            if val <= 0:
                raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' muss > 0 sein (aktuell: {val}). Bitte im Handler/UI bei dieser Operation nachtragen.")
        except (ValueError, TypeError):
            raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' ist keine gültige positive Zahl. Bitte im Handler/UI bei dieser Operation nachtragen.")


def get_tool_number(params: Dict[str, object]) -> int:
    for key in ("tool", "toolno", "tool_number"):
        if key in params and params.get(key) not in (None, ""):
            try:
                return int(float(params.get(key, 0)))
            except Exception:
                return 0
    return 0


def require_tool(params: Dict[str, object], op_label: str) -> int:
    tool_num = get_tool_number(params)
    if tool_num <= 0:
        raise ValueError(f"Fehler in Operation {op_label}: Werkzeug fehlt/ungueltig (tool). Bitte im Handler/UI nachtragen.")
    return tool_num


def is_monotonic_z_decreasing(path: List[Point]) -> bool:
    if len(path) < 2:
        return True
    return all(z1 >= z2 for (_, z1), (_, z2) in zip(path, path[1:]))


def is_monotonic_x_decreasing(path: List[Point]) -> bool:
    if len(path) < 2:
        return True
    return all(x1 >= x2 for (x1, _), (x2, _) in zip(path, path[1:]))


def is_monotonic_x_increasing(path: List[Point]) -> bool:
    if len(path) < 2:
        return True
    return all(x1 <= x2 for (x1, _), (x2, _) in zip(path, path[1:]))


def is_monotonic_x(path: List[Point]) -> bool:
    return is_monotonic_x_decreasing(path) or is_monotonic_x_increasing(path)


def primitives_to_points(primitives: List[Dict[str, object]]) -> List[Point]:
    points = []
    for pr in primitives:
        if pr.get("type") in ("line", "arc"):
            p1 = pr.get("p1")
            p2 = pr.get("p2")
            if p1 and p2:
                points.append(tuple(p1))
                points.append(tuple(p2))
    return points


REQUIRED_KEYS = {
    OpType.FACE: ["depth_max", "feed", "spindle", "tool"],
    OpType.CONTOUR: [],
    OpType.TURN: ["feed", "safe_z", "tool"],
    OpType.BORE: ["feed", "safe_z", "tool"],
    OpType.THREAD: ["pitch", "length", "major_diameter", "spindle", "tool"],
    OpType.GROOVE: ["feed", "safe_z", "tool"],
    OpType.DRILL: ["feed", "safe_z", "tool"],
    OpType.KEYWAY: ["depth_per_pass", "feed", "safe_z", "tool"],
    OpType.ABSPANEN: ["depth_per_pass", "tool"],
}


def sanitize_gcode_text(text: str) -> str:
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


def sanitize_comment_text(text: object) -> str:
    raw = str(text or "")
    raw = raw.replace("(", " ").replace(")", " ")
    raw = " ".join(raw.split())
    return sanitize_gcode_text(raw)


def emit_coolant(lines: List[str], mode: object) -> None:
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
    lines.append("M9")


def float_or_none(value: object | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_path(path: List[Point]) -> List[Point]:
    if not path:
        return path
    cleaned = [path[0]]
    for p in path[1:]:
        if p != cleaned[-1]:
            cleaned.append(p)
    return cleaned


__all__ = [
    "Point",
    "REQUIRED_KEYS",
    "clean_path",
    "emit_coolant",
    "float_or_none",
    "get_tool_number",
    "is_monotonic_x",
    "is_monotonic_x_decreasing",
    "is_monotonic_x_increasing",
    "is_monotonic_z_decreasing",
    "primitives_to_points",
    "require",
    "require_positive",
    "require_tool",
    "sanitize_comment_text",
    "sanitize_gcode_text",
]
