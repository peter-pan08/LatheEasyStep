import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation
from lathe_easystep.tools import Tool

# LES-028/LES-032 (2026-09-15): Tool.kind (aus der Q-Orientierung der
# Werkzeugtabelle geparst) wurde bisher nirgends gegen den tatsaechlich
# verwendeten Operationstyp geprueft - ein Werkzeug, dessen Q-Wert laut
# Tabelle z. B. auf ein Bohrwerkzeug hindeutet, konnte unbemerkt einer
# Stech- oder Gewinde-Operation zugewiesen werden.


def _tool(**overrides):
    defaults = dict(
        t=1, p=0, d=8.0, q=None, comment="", iso_code=None, iso_size=None,
        radius_mm=0.5, kind="turning", wear=False, radius_source=None,
    )
    defaults.update(overrides)
    return Tool(**defaults)


def _kind_warnings(warnings):
    return [w for w in warnings if w["key"] == "warning.tool_kind_mismatch"]


def test_drilling_tool_used_for_groove_operation_is_flagged():
    tool = _tool(t=5, q=1, kind="drilling")  # Q1 -> "drilling" per tool_kind_from_orientation
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.GROOVE, {"tool": 5, "lage": 0, "diameter": 20.0, "width": 3.0, "z": -10.0}),
    ]
    warnings = _kind_warnings(validate_program_setup(ops, {"tools": {5: tool}}))
    assert len(warnings) == 1
    assert warnings[0]["params"]["tool_num"] == 5
    assert warnings[0]["params"]["idx"] == 2


def test_drilling_tool_used_for_drill_operation_is_silent():
    tool = _tool(t=5, q=1, kind="drilling")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.DRILL, {"tool": 5, "z": -10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {5: tool}})) == []


def test_grooving_tool_used_for_thread_operation_is_flagged():
    tool = _tool(t=7, q=4, kind="grooving")  # Q4 -> "grooving"
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.THREAD, {"tool": 7, "pitch": 1.5, "length": 10.0}),
    ]
    warnings = _kind_warnings(validate_program_setup(ops, {"tools": {7: tool}}))
    assert len(warnings) == 1
    assert warnings[0]["params"]["tool_num"] == 7
    # "kind" ist der tatsaechlich gefundene Kind (grooving), nicht der fuer
    # THREAD erwartete (threading) - genau das macht die Warnung aus.
    assert warnings[0]["params"]["kind"] == "grooving"
    assert warnings[0]["params"]["op_type"] == "thread"


def test_tool_without_orientation_is_never_flagged():
    """tool.orientation is None liefert per tool_kind_from_orientation() nur
    den Fallback "turning" - keine echte Klassifikation. Ein Werkzeug ohne
    Q-Angabe in der Tabelle darf deshalb nie eine Falschmeldung ausloesen,
    egal wie unpassend der (nur geratene) Kind-Fallback zum Operationstyp
    wirkt."""
    tool = _tool(t=9, q=None, kind="turning")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.DRILL, {"tool": 9, "z": -10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {9: tool}})) == []


def test_unclassified_orientation_parting_kind_is_never_flagged():
    """kind == "parting" ist der Fallback fuer JEDEN nicht zugeordneten
    Q-Wert (siehe tool_kind_from_orientation()), keine gezielte
    Klassifikation - darf ebenfalls nie eine Falschmeldung ausloesen."""
    tool = _tool(t=3, q=42, kind="parting")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.THREAD, {"tool": 3, "pitch": 1.5, "length": 10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {3: tool}})) == []


def test_parting_kind_is_accepted_for_groove_operation():
    tool = _tool(t=3, q=42, kind="parting")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.GROOVE, {"tool": 3, "lage": 0, "diameter": 20.0, "width": 3.0, "z": -10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {3: tool}})) == []


def test_drilling_tool_accepted_for_bore_operation():
    """Bohrungsdreh-Operationen (Q1-3-Innenwerkzeuge teilen sich in dieser
    Tabelle bewusst die "drilling"-Klassifikation mit echten Bohrern) duerfen
    kein Falschsignal ausloesen."""
    tool = _tool(t=6, q=2, kind="drilling")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.BORE, {"tool": 6, "z": -10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {6: tool}})) == []


def test_unknown_tool_number_is_never_flagged_by_kind_check():
    """Eine fehlende Tabellenzuordnung ist Sache von
    validate_tool_table_completeness() - dieser Check darf dafuer nicht
    zusaetzlich (und mit einer irrefuehrenden Meldung) einspringen."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.DRILL, {"tool": 99, "z": -10.0}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {}})) == []


def test_matching_tool_kind_is_silent():
    tool = _tool(t=1, q=0, kind="turning")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.TURN, {"tool": 1}),
    ]
    assert _kind_warnings(validate_program_setup(ops, {"tools": {1: tool}})) == []
