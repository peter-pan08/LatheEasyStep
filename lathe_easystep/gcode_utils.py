from __future__ import annotations

from typing import Dict, List, Tuple

from .model import OpType
from .numeric import finite_float, whole_number

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
            val = finite_float(params.get(key, 0), key)
            if val <= 0:
                raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' muss > 0 sein (aktuell: {val}). Bitte im Handler/UI bei dieser Operation nachtragen.")
        except (ValueError, TypeError):
            raise ValueError(f"Fehler in Operation {op_label}: Parameter '{key}' ist keine gültige positive Zahl. Bitte im Handler/UI bei dieser Operation nachtragen.")


def get_tool_number(params: Dict[str, object]) -> int:
    for key in ("tool", "toolno", "tool_number"):
        if params.get(key) not in (None, ""):
            number = whole_number(params[key], "Werkzeug")
            if number < 0:
                raise ValueError("Werkzeugnummer darf nicht negativ sein.")
            return number
    return 0


def get_param_float(params: Dict[str, object], keys: List[str], default: float | None = None) -> float | None:
    for key in keys:
        if key in params and params.get(key) not in (None, ""):
            return finite_float(params[key], key)
    return default


def get_param_int(params: Dict[str, object], keys: List[str], default: int | None = None) -> int | None:
    for key in keys:
        if key in params and params.get(key) not in (None, ""):
            return whole_number(params[key], key)
    return default


_INTERNAL_SIDE_TOKENS = {"internal", "inside", "innen", "in", "id"}
_EXTERNAL_SIDE_TOKENS = {"external", "outside", "aussen", "außen", "out", "od"}


def is_internal_side(value: object, default: bool = False) -> bool:
    """Interpretiert Seiten-/Orientierungswerte robust.

    Combos wie ``thread_orientation``, ``parting_side`` oder ``groove_lage``
    liefern seit der ID-only-Umstellung ueber ``currentData()`` String-IDs
    (z. B. ``"internal"``/``"external"``, ``"inside"``/``"outside"``) statt
    des frueheren numerischen Index (0/1). Diese Funktion versteht beide
    Formen, damit Alt-Daten (Save/Load, Tests mit rohen int-Werten) und neue
    UI-Werte gleichermassen korrekt als innen/aussen erkannt werden.
    """
    if value is None:
        return default
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _INTERNAL_SIDE_TOKENS:
            return True
        if token in _EXTERNAL_SIDE_TOKENS:
            return False
        try:
            return int(float(token)) == 1
        except (TypeError, ValueError):
            return default
    try:
        return int(float(value)) == 1
    except (TypeError, ValueError):
        return default


_LEFT_HAND_TOKENS = {"left", "links", "l"}
_RIGHT_HAND_TOKENS = {"right", "rechts", "r"}


def is_left_hand(value: object, default: bool = False) -> bool:
    """Analog zu is_internal_side(), aber fuer die Gewinderichtung
    (thread_hand: 'right'/'left' seit der ID-only-Umstellung statt 0/1)."""
    if value is None:
        return default
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _LEFT_HAND_TOKENS:
            return True
        if token in _RIGHT_HAND_TOKENS:
            return False
        try:
            return int(float(token)) == 1
        except (TypeError, ValueError):
            return default
    try:
        return int(float(value)) == 1
    except (TypeError, ValueError):
        return default


def resolve_enum_index(value: object, mapping: Dict[str, int], default: int = 0) -> int:
    """Loest einen Enum-Parameter zu seinem legacy-numerischen Index auf.

    Combos wie ``face_mode`` (rough/finish/rough_finish) oder ``parting_mode``
    (rough/finish) liefern seit der ID-only-Umstellung String-IDs ueber
    ``currentData()`` statt des frueheren numerischen Combo-Index. Bestehende
    Generatorlogik vergleicht weiterhin gegen den Index (0/1/2); diese Funktion
    versteht beide Formen, damit alte Zahlenwerte (Tests, Altdaten) und neue
    String-IDs gleichermassen korrekt aufgeloest werden.
    """
    if isinstance(value, str):
        token = value.strip().lower()
        if token in mapping:
            return mapping[token]
        try:
            return int(float(token))
        except (TypeError, ValueError):
            return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def resolve_internal_safe_x(settings: Dict[str, object]) -> float | None:
    xri = float_or_none(settings.get("xri"))
    if xri is None:
        return None
    if bool(settings.get("xri_absolute", False)):
        return xri
    xi = float_or_none(settings.get("xi"))
    if xi is None:
        return None
    return xi + xri


def validate_internal_x_limit(settings: Dict[str, object], x_values: List[object], *, op_label: str) -> float:
    safe_x = resolve_internal_safe_x(settings)
    if safe_x is None or safe_x <= 0.0:
        raise ValueError(f"{op_label} erfordert ein gueltiges XRI im Programmkopf.")
    numeric_values: List[float] = []
    for value in x_values:
        numeric_values.append(finite_float(value, op_label))
    if not numeric_values:
        return safe_x
    min_x = min(numeric_values)
    if min_x < safe_x - 1e-9:
        raise ValueError(
            f"XRI={safe_x:.3f} ist fuer {op_label} unplausibel. "
            f"Der kleinste angeforderte X-Wert waere {min_x:.3f}; XRI ist eine harte Sicherheitsgrenze und darf nicht unterschritten werden."
        )
    return safe_x


def validate_internal_material_clearance(
    settings: Dict[str, object], safe_x: float, z_values: List[float], *, op_label: str
) -> None:
    """Sicherstellen, dass die axiale Eilgangebene (XRI) nachweislich in
    bereits offenem Material liegt - nicht nur innerhalb der Fertigkontur
    (siehe `validate_internal_x_limit`), sondern auch innerhalb dessen, was
    laut Programmkopf (XI, vorgebohrtes/Rohr-Rohteil) oder einer
    vorangehenden Bohren-Operation tatsaechlich schon frei ist. XI deckt die
    gesamte Werkstuecklaenge ab; eine Bohrung nur bis zu ihrer Tiefe.
    Blockiert nur bei nachgewiesenem Widerspruch zu bekannten Werten - bei
    fehlender Angabe (weder XI noch vorangehende Bohrung) bleibt dies
    bewusst fehlerfrei, dafuer existiert die separate Reihenfolge-Warnung in
    `checks.py::validate_program_setup`."""
    xi = float_or_none(settings.get("xi"))
    drilled_diameter = float_or_none(settings.get("_last_drill_diameter"))
    drilled_depth = float_or_none(settings.get("_last_drill_depth"))
    deepest_z = min(z_values) if z_values else None

    if xi is not None and xi > 1e-9 and safe_x <= xi + 1e-6:
        return  # XI deckt die gesamte Werkstuecklaenge ab.

    if drilled_diameter is not None and drilled_diameter > 1e-9 and safe_x <= drilled_diameter + 1e-6:
        if drilled_depth is None or deepest_z is None or deepest_z >= drilled_depth - 1e-6:
            return
        raise ValueError(
            f"{op_label}: XRI={safe_x:.3f} ist nur bis Z{drilled_depth:.3f} (Bohrtiefe) "
            f"nachweislich frei, die Bearbeitung erreicht aber Z{deepest_z:.3f}. Bohrung "
            "vertiefen oder Z-Bereich der Operation pruefen."
        )

    have_xi = xi is not None and xi > 1e-9
    have_drill = drilled_diameter is not None and drilled_diameter > 1e-9
    if have_xi or have_drill:
        known = xi if have_xi else drilled_diameter
        source = "das im Programmkopf gesetzte XI" if have_xi else "die vorangehende Bohrung"
        raise ValueError(
            f"{op_label}: XRI={safe_x:.3f} ist groesser als der durch {source} "
            f"nachgewiesene offene Innendurchmesser (Ø{known:.3f}). Die axiale "
            "Eilgangebene waere nicht nachweislich frei von Material."
        )
    # Weder XI noch eine vorangehende Bohrung bekannt - keine gesicherte
    # Aussage moeglich, bewusst kein Fehler.


def require_tool(params: Dict[str, object], op_label: str) -> int:
    tool_num = get_tool_number(params)
    if tool_num <= 0:
        raise ValueError(f"Fehler in Operation {op_label}: Werkzeug fehlt/ungueltig (tool). Bitte im Handler/UI nachtragen.")
    return tool_num


def is_monotonic_z_decreasing(path: List[Point]) -> bool:
    if len(path) < 2:
        return True
    return all(z1 >= z2 for (_, z1), (_, z2) in zip(path, path[1:]))


def is_monotonic_z_increasing(path: List[Point]) -> bool:
    if len(path) < 2:
        return True
    return all(z1 <= z2 for (_, z1), (_, z2) in zip(path, path[1:]))


def is_monotonic_z(path: List[Point]) -> bool:
    """Wie is_monotonic_x(): eine Kontur ist G71-tauglich (parallel_z), wenn
    Z durchgehend faellt ODER durchgehend steigt - nicht nur fallend. Innen-
    konturen werden haeufig vom tiefsten Punkt zur Bohrungsoeffnung definiert
    (Z steigt monoton), was geometrisch genauso gueltig ist wie die bei
    Aussenkonturen uebliche Richtung (Z faellt monoton). Fehlte bisher als
    Gegenstueck zu is_monotonic_z_decreasing() und verwarf dadurch sonst
    zyklustaugliche Innenkonturen faelschlich als "nicht G71-tauglich"."""
    return is_monotonic_z_decreasing(path) or is_monotonic_z_increasing(path)


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
    OpType.KEYWAY: ["depth_per_pass"],
    OpType.ABSPANEN: ["depth_per_pass", "feed", "tool"],
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
        # Ohne diesen Eintrag griff der generische ASCII-Fallback unten
        # (encode("ascii", "replace")), der JEDES nicht-ASCII-Zeichen durch
        # ein bedeutungsloses "?" ersetzt - z. B. wurde ein gespeicherter
        # Planen-Kommentar "Z 0.0->0.0" (Pfeil) im G-Code zu "Z 0.0?0.0".
        "→": "->",
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
    if isinstance(mode, (int, float)):
        # Manche Operationen (Drill/Groove/Thread) reichen params["coolant"]
        # unveraendert durch, ohne vorher wie FACE (opt_bool()) nach bool zu
        # wandeln. Ein gespeicherter Zahlenwert 1.0 traf dadurch weder den
        # str- noch den bool-Zweig und fiel stillschweigend auf M9 (AUS)
        # zurueck - obwohl 1.0 "an" bedeuten sollte. Realer Fund: Innen-
        # Einstich/-Gewinde und Bohren mit coolant=1.0 blieben ohne Kuehlung.
        lines.append("M8" if float(mode) != 0.0 else "M9")
        return
    lines.append("M9")


def float_or_none(value: object | None) -> float | None:
    if value in (None, ""):
        return None
    return finite_float(value)


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
    "get_param_float",
    "get_param_int",
    "get_tool_number",
    "is_monotonic_x",
    "is_monotonic_x_decreasing",
    "is_monotonic_x_increasing",
    "is_monotonic_z",
    "is_monotonic_z_decreasing",
    "is_monotonic_z_increasing",
    "is_internal_side",
    "is_left_hand",
    "primitives_to_points",
    "resolve_enum_index",
    "require",
    "require_positive",
    "require_tool",
    "resolve_internal_safe_x",
    "validate_internal_x_limit",
    "sanitize_comment_text",
    "sanitize_gcode_text",
]
