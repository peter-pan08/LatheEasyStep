"""Zentraler Dirty-/Unsaved-Changes-Zustand (LES-052, erste Etappe).

Ersetzt die bisherigen ad-hoc Handler-Attribute (`_dirty_operation_indices`,
`_program_dirty`, `_dirty_program_header`, `_dirty_program_structure`,
`_dirty_warning_suppressed`) durch ein einzelnes typisiertes Objekt
(`handler._dirty`). Qt-frei und ohne Bezug auf den Handler, damit die
Index-Arithmetik unabhaengig von Widgets testbar bleibt.

Wichtig: `operation_indices` sind reine Listenpositionen in
`ProgramModel.operations`, keine stabilen Operation-IDs. Jede Verschiebung,
Einfuegung oder Entfernung einer Operation muss die betroffene Nachzieh-
Methode aufrufen (`reindex_after_removal()`/`reindex_after_insert()`/
`swap_indices()`), sonst "wandert" eine dirty-Markierung stillschweigend auf
den falschen Nachbar-Step - genau dieser Fehler ist am 2026-09-13 real
aufgetreten (siehe `ui_dirty.py`-Historie vor dieser Kapselung)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass
class DirtyState:
    operation_indices: Set[int] = field(default_factory=set)
    program_dirty: bool = False
    program_header_dirty: bool = False
    program_structure_dirty: bool = False
    warning_suppressed: bool = False

    def mark(self, *, operation_index: int | None = None, program: bool = False) -> None:
        if program:
            self.program_dirty = True
            self.program_header_dirty = True
        if operation_index is not None and operation_index >= 0:
            self.operation_indices.add(int(operation_index))

    def mark_program_structure(self, operation_indices: Iterable[int] | None = None) -> None:
        self.program_dirty = True
        self.program_structure_dirty = True
        if operation_indices:
            for idx in operation_indices:
                if idx is not None and int(idx) >= 0:
                    self.operation_indices.add(int(idx))

    def clear(self) -> None:
        self.program_dirty = False
        self.program_header_dirty = False
        self.program_structure_dirty = False
        self.operation_indices.clear()

    def clear_program(self, *, header: bool = False, structure: bool = False, all_flags: bool = False) -> None:
        if all_flags or header:
            self.program_header_dirty = False
        if all_flags or structure:
            self.program_structure_dirty = False
        self.program_dirty = bool(self.program_header_dirty or self.program_structure_dirty)

    def clear_operation(self, operation_index: int) -> None:
        self.operation_indices.discard(int(operation_index))

    def reindex_after_removal(self, removed_index: int) -> None:
        """Eine Operation wurde bei `removed_index` entfernt - alle
        NACHFOLGENDEN Operationen ruecken eine Position nach vorn."""
        removed_index = int(removed_index)
        new: Set[int] = set()
        for idx in self.operation_indices:
            if idx == removed_index:
                continue
            new.add(idx - 1 if idx > removed_index else idx)
        self.operation_indices = new

    def reindex_after_insert(self, inserted_index: int) -> None:
        """Gegenstueck zu `reindex_after_removal()` - eine Operation wurde
        VOR bereits vorhandenen bei `inserted_index` eingefuegt, alle
        Operationen ab dort ruecken eine Position nach hinten."""
        inserted_index = int(inserted_index)
        self.operation_indices = {
            (idx + 1 if idx >= inserted_index else idx) for idx in self.operation_indices
        }

    def swap_indices(self, index_a: int, index_b: int) -> None:
        """Zwei Operationen haben per `ProgramModel.move_up()`/`move_down()`
        ihre Listenplaetze getauscht - eine dirty-Markierung muss der
        Operation folgen, nicht der Position."""
        index_a, index_b = int(index_a), int(index_b)
        new: Set[int] = set()
        for idx in self.operation_indices:
            if idx == index_a:
                new.add(index_b)
            elif idx == index_b:
                new.add(index_a)
            else:
                new.add(idx)
        self.operation_indices = new

    def mark_all_operations(self, operation_indices: Iterable[int]) -> None:
        self.operation_indices = {int(idx) for idx in operation_indices}
        self.program_dirty = True
        self.program_structure_dirty = True

    def has_unsaved_changes(self) -> bool:
        return bool(self.program_dirty or self.operation_indices)


__all__ = ["DirtyState"]
