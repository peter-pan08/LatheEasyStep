from __future__ import annotations

from qtpy import QtWidgets

from .model import OpType


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


def _lang(handler) -> str:
    try:
        return handler._current_language_code()
    except Exception:
        return "de"


def init_dirty_state(handler) -> None:
    if not hasattr(handler, "_dirty_operation_indices"):
        handler._dirty_operation_indices = set()
    if not hasattr(handler, "_program_dirty"):
        handler._program_dirty = False
    if not hasattr(handler, "_dirty_warning_suppressed"):
        handler._dirty_warning_suppressed = False
    handler._update_dirty_status()


def tab_label(handler, op_type: str | None) -> str:
    translations = TAB_LABELS.get(op_type, TAB_LABELS[OpType.PROGRAM_HEADER])
    return translations.get(_lang(handler), translations.get("de", "Programm"))


def mark_dirty(handler, *, operation_index: int | None = None, program: bool = False) -> None:
    if program:
        handler._program_dirty = True
    if operation_index is not None and operation_index >= 0:
        handler._dirty_operation_indices.add(int(operation_index))
    handler._update_dirty_status()


def clear_dirty_state(handler) -> None:
    handler._program_dirty = False
    handler._dirty_operation_indices.clear()
    handler._update_dirty_status()


def clear_dirty_operation(handler, operation_index: int) -> None:
    handler._dirty_operation_indices.discard(int(operation_index))
    handler._update_dirty_status()


def mark_all_operations_dirty(handler) -> None:
    dirty = set()
    for idx, op in enumerate(getattr(handler.model, "operations", []) or []):
        if getattr(op, "op_type", None) != OpType.PROGRAM_HEADER:
            dirty.add(idx)
    handler._dirty_operation_indices = dirty
    handler._program_dirty = True
    handler._update_dirty_status()


def current_operation_is_dirty(handler, row: int | None = None) -> bool:
    if row is None:
        try:
            row = int(handler.list_ops.currentRow()) if handler.list_ops is not None else -1
        except Exception:
            row = -1
    if row < 0:
        return bool(handler._program_dirty)
    try:
        op = handler.model.operations[row]
    except Exception:
        return False
    if getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
        return bool(handler._program_dirty)
    return row in handler._dirty_operation_indices


def has_unsaved_changes(handler) -> bool:
    return bool(handler._program_dirty or handler._dirty_operation_indices)


def dirty_status_text(handler) -> str:
    lang = _lang(handler)
    dirty_ops = len(handler._dirty_operation_indices)
    if not has_unsaved_changes(handler):
        return "Keine offenen Aenderungen" if lang == "de" else "No pending changes"
    parts = []
    if handler._program_dirty:
        parts.append("Programm" if lang == "de" else "Program")
    if dirty_ops:
        parts.append(f"{dirty_ops} Step{'s' if dirty_ops != 1 else ''}")
    prefix = "Ungespeichert: " if lang == "de" else "Unsaved: "
    return prefix + ", ".join(parts)


def update_dirty_status(handler) -> None:
    label = getattr(handler, "label_dirty_status", None)
    text = dirty_status_text(handler)
    if label is not None:
        try:
            label.setText(text)
            if has_unsaved_changes(handler):
                label.setStyleSheet("QLabel { color: #c62828; font-weight: 700; }")
            else:
                label.setStyleSheet("QLabel { color: #2e7d32; font-weight: 600; }")
        except Exception:
            pass
    button = getattr(handler, "btn_save_changes", None)
    if button is not None:
        base = "Aenderungen speichern" if _lang(handler) == "de" else "Save Changes"
        try:
            button.setText(base + (" *" if has_unsaved_changes(handler) else ""))
        except Exception:
            pass


def warn_if_dirty(handler, context: str, *, row: int | None = None) -> None:
    if getattr(handler, "_dirty_warning_suppressed", False):
        return
    if not current_operation_is_dirty(handler, row=row):
        return
    lang = _lang(handler)
    title = "Ungespeicherte Aenderungen" if lang == "de" else "Unsaved changes"
    if row is not None and row >= 0:
        try:
            op_type = handler.model.operations[row].op_type
        except Exception:
            op_type = None
    else:
        op_type = handler._current_op_type() if hasattr(handler, "_current_op_type") else None
    tab = tab_label(handler, op_type)
    if lang == "de":
        text = f"Im Reiter {tab} gibt es ungespeicherte Aenderungen. {context} speichert keine Dateien automatisch."
    else:
        text = f"There are unsaved changes in the {tab} tab. {context} does not save files automatically."
    parent = getattr(handler, "root_widget", None) or handler._find_root_widget()
    try:
        QtWidgets.QMessageBox.warning(parent, title, text)
    except Exception:
        pass
