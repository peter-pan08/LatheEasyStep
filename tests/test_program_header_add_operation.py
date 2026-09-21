"""LES-052 Abschnitt 3 Fund 3/3b (Audit 2026-09-20): der Programmkopf-Zweig
von `handle_add_operation()` ("Hinzufuegen" auf dem Programm-Tab) ist der
EINZIGE Weg, wie ein neues Programm ueberhaupt seinen ersten Programmkopf
bekommt (kein anderer Erzeugungspfad existiert). Der Audit fand zwei echte
Abweichungen vom Soll-Ablauf (Eingabe -> Normalisierung -> Validierung ->
Modelländerung -> Dirty-State -> Preview):

- Fund 3: beide Unterfaelle (neuen Kopf einfuegen, bestehenden Kopf
  ersetzen) aenderten das Modell, ohne jemals `_mark_dirty`/
  `_mark_program_structure_dirty` aufzurufen - ein neues Programm, das nur
  ueber diesen Weg einen Kopf bekommen hat, zeigte "keine ungespeicherten
  Aenderungen" an, obwohl das Modell gerade erst befuellt wurde.
- Fund 3b: der "Kopf ersetzen"-Unterfall rief anders als der "Kopf neu
  einfuegen"-Unterfall (der `model.update_geometry(op)` VOR dem Insert
  aufruft) ueberhaupt keine Validierung auf - `existing.params = params`
  wurde ungeprueft uebernommen.

Diese Datei nutzt eine echte `HandlerClass`-Instanz (kein Stub von
`handle_add_operation()` selbst), damit sowohl die echte
`model.update_geometry()`-Validierung als auch der echte `DirtyState`
mitgetestet werden."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.model import Operation, OpType, ProgramModel
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep_handler import HandlerClass


def _make_handler(*, existing_header_params=None):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    handler._runtime = RuntimeState()
    handler.model = ProgramModel()
    if existing_header_params is not None:
        handler.model.operations = [Operation(OpType.PROGRAM_HEADER, dict(existing_header_params))]
    else:
        handler.model.operations = []
    handler._dirty = DirtyState()
    handler._tool_table = type("T", (), {"tools": {"1": object()}})()
    handler._ensure_core_widgets = lambda: None
    handler._force_attach_core_widgets = lambda: None
    handler._current_op_type = lambda: OpType.PROGRAM_HEADER
    handler.list_ops = None
    handler._refresh_operation_list = lambda select_index=None: None
    handler._refresh_preview = lambda: None
    handler._log = lambda *a, **k: None
    return handler


def test_add_operation_inserts_new_program_header_and_marks_dirty():
    handler = _make_handler()
    handler._collect_program_header = lambda: {"program_name": "Neues Programm"}

    handler._handle_add_operation()

    assert len(handler.model.operations) == 1
    assert handler.model.operations[0].op_type == OpType.PROGRAM_HEADER
    assert handler.model.operations[0].params.get("program_name") == "Neues Programm"
    assert handler._has_unsaved_changes() is True


def test_add_operation_replaces_existing_program_header_and_marks_dirty():
    handler = _make_handler(existing_header_params={"program_name": "Alt"})
    handler._collect_program_header = lambda: {"program_name": "Geaendert"}

    handler._handle_add_operation()

    assert len(handler.model.operations) == 1
    assert handler.model.operations[0].params.get("program_name") == "Geaendert"
    assert handler._has_unsaved_changes() is True


def test_add_operation_rejects_invalid_new_program_header_without_mutating_model_or_dirty():
    handler = _make_handler()
    handler._collect_program_header = lambda: {"program_name": "Kaputt", "xt": float("inf")}

    with pytest.raises(ValueError):
        handler._handle_add_operation()

    assert handler.model.operations == []
    assert handler._has_unsaved_changes() is False


def test_add_operation_rejects_invalid_header_replacement_leaving_existing_header_unchanged():
    handler = _make_handler(existing_header_params={"program_name": "Gueltig", "xt": 12.0})
    original_params = dict(handler.model.operations[0].params)
    handler._collect_program_header = lambda: {"program_name": "Kaputt", "xt": float("inf")}

    with pytest.raises(ValueError):
        handler._handle_add_operation()

    assert len(handler.model.operations) == 1
    assert handler.model.operations[0].params == original_params
    assert handler._has_unsaved_changes() is False
