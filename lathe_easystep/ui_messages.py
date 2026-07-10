from __future__ import annotations

import re

from .model import OpType
from .translations import TRANSLATIONS

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
    mapping = {
        OpType.PROGRAM_HEADER: "tab.tabProgram.title",
        OpType.FACE: "tab.tabFace.title",
        OpType.CONTOUR: "tab.tabContour.title",
        OpType.ABSPANEN: "tab.tabParting.title",
        OpType.THREAD: "tab.tabThread.title",
        OpType.GROOVE: "tab.tabGroove.title",
        OpType.DRILL: "tab.tabDrill.title",
        OpType.KEYWAY: "tab.tabKeyway.title",
    }
    return TRANSLATIONS.tr(mapping.get(op_type, "tab.tabProgram.title"), _lang(handler))


def _field(handler, key: str) -> str:
    return TRANSLATIONS.tr(f"field.{key}", _lang(handler))


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
        key = "message.required_field_missing_named" if field else "message.required_field_missing"
        return TRANSLATIONS.tr(key, lang).format(tab=tab, field=field)
    if "Pflicht-Parameter ist leer" in detail or "Empty parameter" in detail:
        key = "message.required_field_empty_named" if field else "message.required_field_empty"
        return TRANSLATIONS.tr(key, lang).format(tab=tab, field=field)
    if "muss > 0 sein" in detail or "must be > 0" in detail:
        key = "message.value_gt_zero_named" if field else "message.value_invalid"
        return TRANSLATIONS.tr(key, lang).format(tab=tab, field=field)
    if "XT und ZT" in detail:
        return TRANSLATIONS.tr("message.xt_zt_required", lang)
    if "ZRA/ZRI" in detail:
        return TRANSLATIONS.tr("message.retract_plane_required", lang)
    if "tool wider than groove" in detail:
        return TRANSLATIONS.tr("message.tool_wider_than_groove", lang)
    if fallback_title:
        return f"{fallback_title}:\n{detail}"
    if op_number:
        return TRANSLATIONS.tr("message.step_error", lang).format(step=op_number, tab=tab, detail=detail)
    return detail
