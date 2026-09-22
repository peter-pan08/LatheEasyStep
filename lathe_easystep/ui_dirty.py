from __future__ import annotations

from qtpy import QtWidgets

from .dirty_state import DirtyState
from .model import OpType
from .translations import TRANSLATIONS
from .ui_helpers import current_language as _lang, tab_label
from .ui_persistence import handle_save_changes
from .ui_step_list_view import StepListView


def init_dirty_state(handler) -> None:
    if not hasattr(handler, "_dirty"):
        handler._dirty = DirtyState()
    handler._update_dirty_status()


def mark_dirty(handler, *, operation_index: int | None = None, program: bool = False) -> None:
    handler._dirty.mark(operation_index=operation_index, program=program)
    try:
        handler._log(f"[LatheEasyStep][debug] mark_dirty: program={program} operation_index={operation_index}", level="debug")
    except Exception:
        pass
    handler._update_dirty_status()


def mark_program_structure_dirty(handler, *, operation_indices: set[int] | None = None) -> None:
    handler._dirty.mark_program_structure(operation_indices)
    try:
        handler._log(f"[LatheEasyStep][debug] mark_program_structure_dirty: operation_indices={operation_indices}", level="debug")
    except Exception:
        pass
    handler._update_dirty_status()


def clear_dirty_state(handler) -> None:
    handler._dirty.clear()
    handler._update_dirty_status()


def clear_program_dirty(handler, *, header: bool = False, structure: bool = False, all_flags: bool = False) -> None:
    handler._dirty.clear_program(header=header, structure=structure, all_flags=all_flags)
    handler._update_dirty_status()


def clear_dirty_operation(handler, operation_index: int) -> None:
    handler._dirty.clear_operation(operation_index)
    handler._update_dirty_status()


def reindex_dirty_operations_after_removal(handler, removed_index: int) -> None:
    """SICHERHEITSFUND 2026-09-13: `DirtyState.operation_indices` sind reine
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
    handler._dirty.reindex_after_removal(removed_index)
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
    handler._dirty.reindex_after_insert(inserted_index)
    handler._update_dirty_status()


def swap_dirty_operation_indices(handler, index_a: int, index_b: int) -> None:
    """SICHERHEITSFUND 2026-09-13: siehe `reindex_dirty_operations_after_removal`
    - dasselbe Problem fuer "Step nach oben/unten verschieben"
    (`ProgramModel.move_up()`/`move_down()`, reines Vertauschen zweier
    Listenplaetze). Eine dirty-Markierung muss der OPERATION folgen, nicht
    der Position, sonst "wandert" sie beim Verschieben auf den falschen
    Nachbar-Step."""
    handler._dirty.swap_indices(index_a, index_b)
    handler._update_dirty_status()


def mark_all_operations_dirty(handler) -> None:
    indices = {
        idx
        for idx, op in enumerate(getattr(handler.model, "operations", []) or [])
        if getattr(op, "op_type", None) != OpType.PROGRAM_HEADER
    }
    handler._dirty.mark_all_operations(indices)
    handler._update_dirty_status()


def current_operation_is_dirty(handler, row: int | None = None) -> bool:
    if row is None:
        try:
            row = int(StepListView(handler).selected_row())
        except Exception:
            row = -1
    if row < 0:
        return bool(handler._dirty.program_dirty)
    try:
        op = handler.model.operations[row]
    except Exception:
        return False
    if getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
        return bool(handler._dirty.program_dirty)
    return row in handler._dirty.operation_indices


def has_unsaved_changes(handler) -> bool:
    return handler._dirty.has_unsaved_changes()


def dirty_status_text(handler) -> str:
    lang = _lang(handler)
    dirty_ops = len(handler._dirty.operation_indices)
    if not has_unsaved_changes(handler):
        return TRANSLATIONS.tr("text.label_dirty_status", lang)
    parts = []
    if handler._dirty.program_dirty:
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
        dirty = has_unsaved_changes(handler)
        try:
            button.setText(base + (" *" if dirty else ""))
        except Exception:
            pass
        # LES-024: "Aenderungen speichern" ohne offene Aenderungen zeigte
        # bisher erst NACH dem Klick eine "nichts zu speichern"-Meldung
        # (handle_save_changes()). Wie bei "Step speichern" und den
        # Listenaktionen (siehe update_save_step_button_state()/
        # update_operation_action_button_states()) wird die ungueltige
        # Aktion jetzt per Buttonzustand von vornherein verhindert statt
        # nur beim Klick gemeldet. Die bestehende Klick-Meldung bleibt als
        # letzte Sicherung bestehen (z. B. falls alle dirty Steps ohne
        # verknuepfte Datei sind).
        try:
            button.setEnabled(dirty)
        except Exception:
            pass


def warn_if_dirty(handler, context: str, *, row: int | None = None) -> None:
    if handler._dirty.warning_suppressed:
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


def confirm_discard_or_save_on_exit(handler) -> bool:
    """Speichern/Verwerfen/Abbrechen-Abfrage fuer den Beendigungspfad.

    Rueckgabe True bedeutet: das Fenster darf tatsaechlich schliessen.
    Nutzt ausschliesslich den bestehenden Speicherpfad (handle_save_changes()) -
    keine eigene parallele Speicherlogik.
    """
    if not has_unsaved_changes(handler):
        return True
    lang = _lang(handler)
    parent = getattr(handler, "root_widget", None) or handler._find_root_widget()
    box = QtWidgets.QMessageBox(parent)
    box.setIcon(QtWidgets.QMessageBox.Warning)
    box.setWindowTitle(TRANSLATIONS.tr("dialog.unsaved_changes_on_exit.title", lang))
    box.setText(TRANSLATIONS.tr("dialog.unsaved_changes_on_exit.body", lang))
    save_button = box.addButton(
        TRANSLATIONS.tr("dialog.unsaved_changes_on_exit.save", lang), QtWidgets.QMessageBox.AcceptRole
    )
    discard_button = box.addButton(
        TRANSLATIONS.tr("dialog.unsaved_changes_on_exit.discard", lang), QtWidgets.QMessageBox.DestructiveRole
    )
    box.addButton(
        TRANSLATIONS.tr("dialog.unsaved_changes_on_exit.cancel", lang), QtWidgets.QMessageBox.RejectRole
    )
    box.setDefaultButton(save_button)
    box.exec()
    clicked = box.clickedButton()
    if clicked is save_button:
        handle_save_changes(handler)
        return not has_unsaved_changes(handler)
    if clicked is discard_button:
        return True
    # Abbrechen oder Dialog anderweitig geschlossen (z. B. Fenster-X):
    # sicherer Default ist "nicht schliessen".
    return False


def handle_window_close_event(handler, event) -> None:
    """QtVCP-Fenster-`closeEvent`-Ersatz, gebunden via `class_patch__()`.

    `closing_cleanup__()` laeuft laut QtVCP-Quelltext (`/usr/bin/qtvcp`)
    erst NACH `QApplication.exec()`, kann das Schliessen also nicht mehr
    verhindern. Nur ein echter `closeEvent` auf dem QMainWindow selbst kann
    das (`event.ignore()`); QtVCP patcht dafuer keinen eigenen Handler,
    daher ersetzt `class_patch__()` `self.w.closeEvent` durch diese
    Funktion.

    Fail-safe bei ungeklaertem Zustand: eine unerwartete Ausnahme waehrend
    der Dirty-Pruefung/des Dialogs fuehrt zu `event.ignore()` (Fenster
    bleibt offen), NICHT zum Schliessen trotz moeglicherweise noch
    ungespeicherter Aenderungen - Datenverlust ist der schlechtere Fehler
    als ein Fenster, das sich einmal nicht schliesst. `_runtime.
    closing_window` (`RuntimeState`) verhindert dabei zusaetzlich, dass ein
    reentranter Aufruf (z. B. ein zweites Close-Signal, waehrend der
    Speichern-/Verwerfen-/Abbrechen-Dialog noch offen ist) einen weiteren
    Dialog stapelt - der reentrante Aufruf ignoriert das Event sofort ohne
    erneute Pruefung.
    """
    runtime = getattr(handler, "_runtime", None)
    if runtime is not None and getattr(runtime, "closing_window", False):
        event.ignore()
        return
    if runtime is not None:
        runtime.closing_window = True
    try:
        if confirm_discard_or_save_on_exit(handler):
            event.accept()
        else:
            event.ignore()
    except Exception as exc:
        handler._log(f"[LatheEasyStep] closeEvent dirty-check failed, keeping window open: {exc}", level="warning")
        event.ignore()
    finally:
        if runtime is not None:
            runtime.closing_window = False
