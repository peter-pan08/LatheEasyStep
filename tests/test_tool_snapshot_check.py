"""Tests fuer die LES-032/LES-053-Werkzeug-Snapshot-Vergleichspruefung.

`op.params["tool_snapshot"]` (siehe `tools.py::build_tool_snapshot()`) haelt
Radius/Orientierung/Einstichbreite zum Speicherzeitpunkt fest.
`checks.py::_check_tool_matches_snapshot()` (ueber `validate_program_setup()`
aufgerufen) vergleicht das gegen die AKTUELL geladene Tooltable und meldet
Abweichungen nur als Warnung, nie als Sperre.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import Operation, OpType
from lathe_easystep.tools import Tool, build_tool_snapshot


def _tool(t=1, radius_mm=0.4, q=0, comment="CNMG120408"):
    return Tool(
        t=t, p=t, d=0.0, q=q, comment=comment, iso_code=None, iso_size=None,
        radius_mm=radius_mm, kind="turning",
    )


def _abspanen_op(tool_snapshot=None, tool=1):
    params = {"tool": tool, "side": 0, "mode": 0, "slice_strategy": 1}
    if tool_snapshot is not None:
        params["tool_snapshot"] = tool_snapshot
    return Operation(OpType.ABSPANEN, params, path=[(40.0, 0.0), (20.0, -20.0)])


_SNAPSHOT_KEYS = {
    "warning.tool_snapshot_radius_changed",
    "warning.tool_snapshot_orientation_changed",
    "warning.tool_snapshot_width_changed",
}


def _snapshot_warnings(warnings):
    return [w for w in warnings if w["key"] in _SNAPSHOT_KEYS]


def test_build_tool_snapshot_contains_only_the_three_relevant_fields():
    tools = {1: _tool(radius_mm=0.4, q=3, comment="MGMN200")}
    snapshot = build_tool_snapshot(1, tools)
    assert set(snapshot) == {"radius_mm", "orientation", "insert_width_mm"}
    assert snapshot["radius_mm"] == 0.4
    assert snapshot["orientation"] == 3
    assert snapshot["insert_width_mm"] == 2.0


def test_build_tool_snapshot_is_none_without_tool_number_or_unknown_tool():
    assert build_tool_snapshot(None, {1: _tool()}) is None
    assert build_tool_snapshot(0, {1: _tool()}) is None
    assert build_tool_snapshot(5, {1: _tool()}) is None  # T5 nicht in der Tabelle
    assert build_tool_snapshot(1, {}) is None  # keine Tabelle geladen


def test_unchanged_tool_produces_no_warning():
    tool = _tool(radius_mm=0.4, q=0)
    snapshot = build_tool_snapshot(1, {1: tool})
    op = _abspanen_op(tool_snapshot=snapshot)
    warnings = validate_program_setup([op], {"tools": {1: tool}})
    assert _snapshot_warnings(warnings) == []


def test_changed_radius_is_detected():
    snapshot = build_tool_snapshot(1, {1: _tool(radius_mm=0.4)})
    op = _abspanen_op(tool_snapshot=snapshot)
    current_tools = {1: _tool(radius_mm=0.8)}
    warnings = validate_program_setup([op], {"tools": current_tools})
    hits = _snapshot_warnings(warnings)
    assert len(hits) == 1
    assert hits[0]["key"] == "warning.tool_snapshot_radius_changed"
    assert hits[0]["params"]["tool_num"] == 1


def test_changed_orientation_is_detected():
    snapshot = build_tool_snapshot(1, {1: _tool(q=0)})
    op = _abspanen_op(tool_snapshot=snapshot)
    current_tools = {1: _tool(q=3)}
    warnings = validate_program_setup([op], {"tools": current_tools})
    hits = _snapshot_warnings(warnings)
    assert len(hits) == 1
    assert hits[0]["key"] == "warning.tool_snapshot_orientation_changed"


def test_changed_insert_width_is_detected():
    snapshot = build_tool_snapshot(1, {1: _tool(comment="MGMN200")})
    op = _abspanen_op(tool_snapshot=snapshot)
    current_tools = {1: _tool(comment="MGMN300")}
    warnings = validate_program_setup([op], {"tools": current_tools})
    hits = _snapshot_warnings(warnings)
    assert len(hits) == 1
    assert hits[0]["key"] == "warning.tool_snapshot_width_changed"


def test_operation_without_snapshot_produces_no_warning():
    """Ueber Format v1 geladene (und nach v2 migrierte) Altoperationen haben
    keinen Snapshot - dafuer entsteht bewusst KEINE Warnung, da kein
    historischer Vergleichswert existiert."""
    op = _abspanen_op(tool_snapshot=None)
    current_tools = {1: _tool(radius_mm=0.9)}
    warnings = validate_program_setup([op], {"tools": current_tools})
    assert _snapshot_warnings(warnings) == []


def test_missing_current_tool_does_not_duplicate_completeness_warning():
    """Fehlt das Werkzeug in der aktuellen Tabelle komplett, ist das
    Sache von validate_tool_table_completeness() (LES-028, harter Fehler) -
    die Snapshot-Vergleichspruefung selbst darf dafuer keine eigene,
    doppelte Warnung erzeugen."""
    snapshot = build_tool_snapshot(1, {1: _tool()})
    op = _abspanen_op(tool_snapshot=snapshot, tool=1)
    warnings = validate_program_setup([op], {"tools": {}})  # T1 aktuell nicht geladen
    assert _snapshot_warnings(warnings) == []
