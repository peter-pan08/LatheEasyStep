import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_tool_table_completeness
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation

# LES-028 Entscheidung (2026-09-14): jede verwendete Werkzeugnummer muss
# zwingend einen Eintrag in der geladenen Werkzeugtabelle haben, sobald
# ueberhaupt eine geladen wurde. Vorher wurde eine fehlende Nummer weder als
# Fehler noch als Warnung gemeldet - der Werkzeugwechsel wurde stillschweigend
# mit einem unbekannten Werkzeug erzeugt.


def test_missing_tool_raises_when_a_real_table_is_loaded():
    ops = [Operation(OpType.ABSPANEN, {"tool": 7})]
    with pytest.raises(ValueError, match="T07"):
        validate_tool_table_completeness(ops, {1: object(), 2: object()})


def test_present_tool_does_not_raise():
    ops = [Operation(OpType.ABSPANEN, {"tool": 1})]
    validate_tool_table_completeness(ops, {1: object()})  # muss nicht werfen


def test_empty_tool_table_is_not_checked():
    """Kein geladenes tool.tbl (z. B. reine Generatortests oder die
    Referenzregeneration) - unveraendertes Verhalten, keine Pruefung."""
    ops = [Operation(OpType.ABSPANEN, {"tool": 99})]
    validate_tool_table_completeness(ops, {})  # darf nicht werfen
    validate_tool_table_completeness(ops, None)  # darf nicht werfen


def test_program_header_and_unused_tool_slot_are_ignored():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {"tool": 99}),  # kein echtes Werkzeug
        Operation(OpType.FACE, {"tool": 0}),  # 0 = kein Werkzeugwechsel
    ]
    validate_tool_table_completeness(ops, {1: object()})  # darf nicht werfen


def test_multiple_missing_tools_are_all_named_in_the_message():
    ops = [
        Operation(OpType.ABSPANEN, {"tool": 7}),
        Operation(OpType.DRILL, {"tool": 12}),
    ]
    with pytest.raises(ValueError) as excinfo:
        validate_tool_table_completeness(ops, {1: object()})
    assert "T07" in str(excinfo.value)
    assert "T12" in str(excinfo.value)


def test_generate_program_gcode_blocks_on_missing_tool_with_real_table():
    """End-to-End durch den tatsaechlichen Generatorpfad, nicht nur die
    Prueffunktion isoliert."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 5, "depth_per_pass": 1.0, "feed": 0.1}),
    ]
    settings = {"tools": {1: object()}}
    with pytest.raises(ValueError, match="T05"):
        generate_program_gcode(ops, settings)


def test_generate_program_gcode_ignores_missing_tools_without_a_loaded_table():
    """Reproduziert den bestehenden Zustand aller Referenzen/Tests, die
    generate_program_gcode() ohne 'tools' im settings-Dict aufrufen - darf
    durch diese Aenderung nicht brechen (die Operation scheitert hier aus
    anderen Gruenden - z. B. fehlende Kontur -, aber nicht wegen T05)."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 5, "depth_per_pass": 1.0, "feed": 0.1}),
    ]
    try:
        generate_program_gcode(ops, {})
    except ValueError as exc:
        assert "T05" not in str(exc)
