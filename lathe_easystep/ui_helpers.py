from __future__ import annotations

from .model import OpType
from .translations import TRANSLATIONS


def current_language(handler) -> str:
    try:
        return handler._current_language_code()
    except Exception:
        return "de"


def translate(handler, key: str, **kwargs) -> str:
    text = TRANSLATIONS.tr(key, current_language(handler))
    return text.format(**kwargs) if kwargs else text


def populate_combo(combo, options, lang: str, current_value=None, *, allow_empty: bool = False) -> None:
    combo.blockSignals(True)
    combo.clear()
    if allow_empty:
        combo.addItem("", "")
    target_idx = -1
    for idx, (value, key) in enumerate(options):
        combo.addItem(TRANSLATIONS.tr(key, lang), value)
        if current_value is not None and str(current_value).strip().lower() == str(value).strip().lower():
            target_idx = idx + (1 if allow_empty else 0)
    combo.setCurrentIndex(target_idx if target_idx >= 0 else (1 if allow_empty and options else 0))
    combo.blockSignals(False)


def tab_label(handler, op_type: str | None) -> str:
    if isinstance(op_type, str):
        op_type = getattr(OpType, op_type.upper(), op_type)
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
    return TRANSLATIONS.tr(mapping.get(op_type, "tab.tabProgram.title"), current_language(handler))


__all__ = ["current_language", "populate_combo", "tab_label", "translate"]
