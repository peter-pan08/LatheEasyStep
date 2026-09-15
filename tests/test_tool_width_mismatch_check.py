import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation
from lathe_easystep.tools import Tool, extract_insert_width_from_comment

# LES-032 (2026-09-15): Tool.insert_width_mm (aus dem ISO-Einstich-
# Einsatzcode im Kommentar abgeleitet, z. B. "MGMN200" -> 2,00 mm) wurde
# bisher nirgends gegen die manuell eingetragene Werkzeugbreite einer
# Stech-Operation geprueft - beide Werte konnten unbemerkt auseinanderlaufen.
# Dieselbe Regel war bisher nur in tool_logic.py::infer_insert_profile()
# (Werkzeugvorschau) redundant implementiert.


def _tool(**overrides):
    defaults = dict(
        t=1, p=0, d=0.2, q=6, comment="Einstechen MGMN200", iso_code=None, iso_size=None,
        radius_mm=0.2, kind="grooving", wear=False, radius_source=None,
    )
    defaults.update(overrides)
    return Tool(**defaults)


def _width_warnings(warnings):
    return [w for w in warnings if "Werkzeugbreite" in w]


def test_extract_insert_width_from_comment_reads_iso_grooving_code():
    assert extract_insert_width_from_comment("Einstechen MGMN200") == 2.0
    assert extract_insert_width_from_comment("Abstechen MRMN300 Innen") == 3.0
    assert extract_insert_width_from_comment("DCMT Außendrehen") is None
    assert extract_insert_width_from_comment("") is None
    assert extract_insert_width_from_comment(None) is None


def test_tool_insert_width_mm_property_matches_helper():
    tool = _tool(comment="Einstechen MGMN200")
    assert tool.insert_width_mm == 2.0
    turning_tool = _tool(comment="DCMT Außendrehen", q=2, kind="turning")
    assert turning_tool.insert_width_mm is None


def test_mismatched_manual_width_is_flagged():
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.GROOVE,
            {"tool": 4, "lage": 0, "diameter": 20.0, "z": -10.0, "use_tool_width": True, "tool_width": 3.0},
        ),
    ]
    warnings = _width_warnings(validate_program_setup(ops, {"tools": {4: tool}}))
    assert len(warnings) == 1
    assert "T04" in warnings[0]
    assert "Schritt 2" in warnings[0]


def test_matching_manual_width_is_silent():
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.GROOVE,
            {"tool": 4, "lage": 0, "diameter": 20.0, "z": -10.0, "use_tool_width": True, "tool_width": 2.0},
        ),
    ]
    assert _width_warnings(validate_program_setup(ops, {"tools": {4: tool}})) == []


def test_width_not_checked_when_operation_does_not_use_tool_width():
    """use_tool_width=False bedeutet, die Operation richtet sich nach der
    Nutbreite, nicht nach der eingetragenen Werkzeugbreite - ein Abweichen
    ist dann kein sinnvolles Warnsignal."""
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.GROOVE,
            {"tool": 4, "lage": 0, "diameter": 20.0, "z": -10.0, "use_tool_width": False, "tool_width": 5.0},
        ),
    ]
    assert _width_warnings(validate_program_setup(ops, {"tools": {4: tool}})) == []


def test_width_not_checked_without_recognizable_insert_code():
    tool = _tool(t=4, comment="Einstechwerkzeug ohne Codeangabe")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.GROOVE,
            {"tool": 4, "lage": 0, "diameter": 20.0, "z": -10.0, "use_tool_width": True, "tool_width": 5.0},
        ),
    ]
    assert _width_warnings(validate_program_setup(ops, {"tools": {4: tool}})) == []


def test_width_not_checked_for_non_groove_operations():
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 4, "side": "outside", "use_tool_width": True, "tool_width": 9.0}),
    ]
    assert _width_warnings(validate_program_setup(ops, {"tools": {4: tool}})) == []
