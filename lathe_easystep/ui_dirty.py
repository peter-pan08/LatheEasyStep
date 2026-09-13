from __future__ import annotations

from qtpy import QtWidgets

from .model import OpType
from .translations import TRANSLATIONS
from .ui_helpers import current_language as _lang, tab_label


def init_dirty_state(handler) -> None:
    if not hasattr(handler, "_dirty_operation_indices"):
        handler._dirty_operation_indices = set()
    if not hasattr(handler, "_program_dirty"):
        handler._program_dirty = False
    if not hasattr(handler, "_dirty_program_header"):
        handler._dirty_program_header = False
    if not hasattr(handler, "_dirty_program_structure"):
        handler._dirty_program_structure = False
    if not hasattr(handler, "_dirty_warning_suppressed"):
        handler._dirty_warning_suppressed = False
    handler._update_dirty_status()


def mark_dirty(handler, *, operation_index: int | None = None, program: bool = False) -> None:
    if program:
        handler._program_dirty = True
        handler._dirty_program_header = True
    if operation_index is not None and operation_index >= 0:
        handler._dirty_operation_indices.add(int(operation_index))
    try:
        handler._log(f"[LatheEasyStep][debug] mark_dirty: program={program} operation_index={operation_index}", level="debug")
    except Exception:
        pass
    handler._update_dirty_status()


def mark_program_structure_dirty(handler, *, operation_indices: set[int] | None = None) -> None:
    handler._program_dirty = True
    handler._dirty_program_structure = True
    if operation_indices:
        for operation_index in operation_indices:
            if operation_index is not None and int(operation_index) >= 0:
                handler._dirty_operation_indices.add(int(operation_index))
    try:
        handler._log(f"[LatheEasyStep][debug] mark_program_structure_dirty: operation_indices={operation_indices}", level="debug")
    except Exception:
        pass
    handler._update_dirty_status()


def clear_dirty_state(handler) -> None:
    handler._program_dirty = False
    handler._dirty_program_header = False
    handler._dirty_program_structure = False
    handler._dirty_operation_indices.clear()
    handler._update_dirty_status()


def clear_program_dirty(handler, *, header: bool = False, structure: bool = False, all_flags: bool = False) -> None:
    if all_flags or header:
        handler._dirty_program_header = False
    if all_flags or structure:
        handler._dirty_program_structure = False
    handler._program_dirty = bool(
        getattr(handler, "_dirty_program_header", False)
        or getattr(handler, "_dirty_program_structure", False)
    )
    handler._update_dirty_status()


def clear_dirty_operation(handler, operation_index: int) -> None:
    handler._dirty_operation_indices.discard(int(operation_index))
    handler._update_dirty_status()


def reindex_dirty_operations_after_removal(handler, removed_index: int) -> None:
    """SICHERHEITSFUND 2026-09-13: `_dirty_operation_indices` sind reine
    Listenpositionen. Loeschen einer Operation verschiebt alle NACHFOLGENDEN
    Operationen um eine Position nach vorn (`ProgramModel.remove_operation()`),
    ohne dass die dirty-Menge das je nachvollzogen hat - ein zuvor dirty
    markierter Step "wanderte" dadurch stillschweigend auf einen ANDEREN,
    tatsaechlich unveraenderten Step (und der wirklich geaenderte Step verlor
    seine dirty-Markierung komplett). "Aenderungen speichern" haette dadurch
    die falsche Step-Datei aktualisiert und die echte Aenderung verloren,
    ohne jede Warnung. Muss VOR oder NACH dem eigentlichen Entfernen
    aufgerufen werden (reine Index-Arithmetik, kein Zugriff auf die Liste
    selbst noetig)."""
    old = getattr(handler, "_dirty_operation_indices", set())
    removed_index = int(removed_index)
    new = set()
    for idx in old:
        if idx == removed_index:
            continue
        new.add(idx - 1 if idx > removed_index else idx)
    handler._dirty_operation_indices = new
    handler._update_dirty_status()


def reindex_dirty_operations_after_insert(handler, inserted_index: int) -> None:
    """SICHERHEITSFUND 2026-09-13: Gegenstueck zu
    `reindex_dirty_operations_after_removal` - wird eine Operation VOR
    bereits vorhandenen eingefuegt (aktuell nur der Sonderfall "Programmkopf
    nachtraeglich an Position 0 einfuegen", `operations.insert(0, op)`),
    verschieben sich alle Operationen AB `inserted_index` um eine Position
    nach hinten. Ohne Nachziehen der dirty-Menge waere jeder bereits
    dirty markierte Index um eins zu niedrig und zeigte dadurch auf die
    FALSCHE (eine Position zu frueh liegende) Operation."""
    old = getattr(handler, "_dirty_operation_indices", set())
    inserted_index = int(inserted_index)
    new = {(idx + 1 if idx >= inserted_index else idx) for idx in old}
    handler._dirty_operation_indices = new
    handler._update_dirty_status()


def swap_dirty_operation_indices(handler, index_a: int, index_b: int) -> None:
    """SICHERHEITSFUND 2026-09-13: siehe `reindex_dirty_operations_after_removal`
    - dasselbe Problem fuer "Step nach oben/unten verschieben"
    (`ProgramModel.move_up()`/`move_down()`, reines Vertauschen zweier
    Listenplaetze). Eine dirty-Markierung muss der OPERATION folgen, nicht
    der Position, sonst "wandert" sie beim Verschieben auf den falschen
    Nachbar-Step."""
    old = getattr(handler, "_dirty_operation_indices", set())
    index_a, index_b = int(index_a), int(index_b)
    new = set()
    for idx in old:
        if idx == index_a:
            new.add(index_b)
        elif idx == index_b:
            new.add(index_a)
        else:
            new.add(idx)
    handler._dirty_operation_indices = new
    handler._update_dirty_status()


def mark_all_operations_dirty(handler) -> None:
    dirty = set()
    for idx, op in enumerate(getattr(handler.model, "operations", []) or []):
        if getattr(op, "op_type", None) != OpType.PROGRAM_HEADER:
            dirty.add(idx)
    handler._dirty_operation_indices = dirty
    handler._program_dirty = True
    handler._dirty_program_structure = True
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
        return TRANSLATIONS.tr("text.label_dirty_status", lang)
    parts = []
    if handler._program_dirty:
        parts.append(TRANSLATIONS.tr("dirty.program", lang))
    if dirty_ops:
        unit_key = "dirty.steps_plural" if dirty_ops != 1 else "dirty.steps_singular"
        parts.append(f"{dirty_ops} {TRANSLATIONS.tr(unit_key, lang)}")
    prefix = TRANSLATIONS.tr("dirty.unsaved_prefix", lang)
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
        base = TRANSLATIONS.tr("text.btnSaveChanges", _lang(handler))
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
    title = TRANSLATIONS.tr("dialog.unsaved_changes.title", lang)
    if row is not None and row >= 0:
        try:
            op_type = handler.model.operations[row].op_type
        except Exception:
            op_type = None
    else:
        op_type = handler._current_op_type() if hasattr(handler, "_current_op_type") else None
    tab = tab_label(handler, op_type)
    template = TRANSLATIONS.tr("dialog.unsaved_changes.body", lang)
    text = template.format(tab=tab, context=context)
    parent = getattr(handler, "root_widget", None) or handler._find_root_widget()
    try:
        QtWidgets.QMessageBox.warning(parent, title, text)
    except Exception:
        pass
