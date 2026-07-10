from __future__ import annotations

import re

from .model import OpType


FIELD_LABELS = {
    "xt": {"de": "Werkzeugwechsel XT", "en": "tool change XT"},
    "zt": {"de": "Werkzeugwechsel ZT", "en": "tool change ZT"},
    "safe_z": {"de": "Sicherheitsabstand / Rueckzugsebene Z", "en": "safe Z / retract plane"},
    "feed": {"de": "Vorschub", "en": "feed"},
    "tool": {"de": "Werkzeug", "en": "tool"},
    "pitch": {"de": "Steigung", "en": "pitch"},
    "thread_start_z": {"de": "Gewindestart Z", "en": "thread start Z"},
    "major_diameter": {"de": "Major-Durchmesser", "en": "major diameter"},
    "depth_per_pass": {"de": "Zustellung pro Pass", "en": "depth per pass"},
    "zra": {"de": "ZRA aeussere Rueckzugsebene", "en": "ZRA outer retract plane"},
    "zri": {"de": "ZRI innere Rueckzugsebene", "en": "ZRI inner retract plane"},
    "undercut_tool": {"de": "Hinterschnitt-Werkzeug", "en": "undercut tool"},
}

TAB_LABELS = {
    OpType.PROGRAM_HEADER: {"de": "Programm", "en": "Program"},
    OpType.FACE: {"de": "Planen", "en": "Facing"},
    OpType.CONTOUR: {"de": "Kontur", "en": "Contour"},
    OpType.ABSPANEN: {"de": "Abspanen", "en": "Parting"},
    OpType.THREAD: {"de": "Gewinde", "en": "Thread"},
    OpType.GROOVE: {"de": "Einstich / Abstich", "en": "Groove / Parting"},
    OpType.DRILL: {"de": "Bohren", "en": "Drilling"},
    OpType.KEYWAY: {"de": "Keilnut", "en": "Keyway"},
}

OP_FIELDS = {
    OpType.FACE: {"depth_max", "feed", "spindle", "tool", "safe_z"},
    OpType.THREAD: {"pitch", "length", "major_diameter", "spindle", "tool", "safe_z", "thread_start_z"},
    OpType.GROOVE: {"feed", "safe_z", "tool", "width", "depth"},
    OpType.DRILL: {"feed", "safe_z", "tool", "depth"},
    OpType.KEYWAY: {"depth_per_pass", "tool", "feed"},
    OpType.ABSPANEN: {"depth_per_pass", "tool", "undercut_tool"},
}


def _lang(handler) -> str:
    try:
        return handler._current_language_code()
    except Exception:
        return "de"


def _tab(handler, op_type: str | None) -> str:
    if isinstance(op_type, str):
        op_type = _normalize_op_type(op_type)
    entry = TAB_LABELS.get(op_type, TAB_LABELS[OpType.PROGRAM_HEADER])
    return entry.get(_lang(handler), entry["de"])


def _field(handler, key: str) -> str:
    entry = FIELD_LABELS.get(key, {"de": key, "en": key})
    return entry.get(_lang(handler), entry["de"])


def _field_allowed_for_tab(op_type: str | None, field_key: str | None) -> bool:
    if op_type is None or field_key is None:
        return False
    op_type = _normalize_op_type(op_type)
    return field_key in OP_FIELDS.get(op_type, set())


def _normalize_op_type(op_type: str | None) -> str | None:
    if not isinstance(op_type, str):
        return op_type
    lookup = {
        "PROGRAM_HEADER": OpType.PROGRAM_HEADER,
        "FACE": OpType.FACE,
        "CONTOUR": OpType.CONTOUR,
        "ABSPANEN": OpType.ABSPANEN,
        "THREAD": OpType.THREAD,
        "GROOVE": OpType.GROOVE,
        "DRILL": OpType.DRILL,
        "KEYWAY": OpType.KEYWAY,
    }
    return lookup.get(op_type.strip().upper(), op_type)


def format_user_error(handler, exc: Exception, *, fallback_title: str = "") -> str:
    text = str(exc or "").strip()
    lang = _lang(handler)
    op_match = re.search(r"Operation\s+(\d+)\s+\(([^)]+)\):\s*(.*)", text)
    op_type = None
    op_number = None
    detail = text
    if op_match:
        op_number = op_match.group(1)
        op_type = op_match.group(2)
        detail = op_match.group(3).strip()

    field_match = re.search(r"'([A-Za-z0-9_]+)'", detail)
    field_key = field_match.group(1) if field_match else None
    tab = _tab(handler, op_type)
    field = _field(handler, field_key) if _field_allowed_for_tab(op_type, field_key) else ""

    if "Pflicht-Parameter fehlt" in detail or "Missing parameter" in detail:
        if lang == "de":
            return f"Im Reiter {tab} fehlt das Pflichtfeld {field}." if field else f"Im Reiter {tab} fehlt ein Pflichtfeld."
        return f"The required field {field} is missing in the {tab} tab." if field else f"A required field is missing in the {tab} tab."
    if "Pflicht-Parameter ist leer" in detail or "Empty parameter" in detail:
        if lang == "de":
            return f"Im Reiter {tab} ist das Feld {field} leer." if field else f"Im Reiter {tab} ist ein Pflichtfeld leer."
        return f"The field {field} is empty in the {tab} tab." if field else f"A required field is empty in the {tab} tab."
    if "muss > 0 sein" in detail or "must be > 0" in detail:
        if lang == "de":
            return f"Im Reiter {tab} muss {field} groesser als 0 sein." if field else f"Im Reiter {tab} ist ein Zahlenwert ungueltig."
        return f"{field} must be greater than 0 in the {tab} tab." if field else f"A numeric value is invalid in the {tab} tab."
    if "XT und ZT" in detail:
        if lang == "de":
            return "Im Reiter Programm fehlen XT und ZT fuer den sicheren Werkzeugwechsel mit mehreren Werkzeugen."
        return "XT and ZT are required in the Program tab for safe tool changes with multiple tools."
    if "ZRA/ZRI" in detail:
        if lang == "de":
            return "Im Reiter Programm fehlt die Rueckzugsebene ZRA oder ZRI fuer die gewaehlte Bearbeitung."
        return "The required retract plane ZRA or ZRI is missing in the Program tab."
    if "tool wider than groove" in detail:
        if lang == "de":
            return "Im Reiter Einstich / Abstich ist die Werkzeugbreite groesser als die Nutbreite."
        return "The tool width is larger than the groove width in the Groove / Parting tab."
    if fallback_title and lang == "de":
        return f"{fallback_title}:\n{detail}"
    if fallback_title and lang == "en":
        return f"{fallback_title}:\n{detail}"
    if op_number and lang == "de":
        return f"Fehler in Step {op_number} ({tab}): {detail}"
    if op_number:
        return f"Error in step {op_number} ({tab}): {detail}"
    return detail
