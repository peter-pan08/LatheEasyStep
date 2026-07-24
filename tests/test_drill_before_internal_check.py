import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


def _warns_about_order(warnings):
    return any("vor der (ersten) Bohrung" in w for w in warnings)


def test_internal_abspanen_before_drill_warns():
    """Realer Bugreport: Innenbearbeitung (Abspanen/Einstich/Gewinde) vor der
    Bohrung fährt ins Vollmaterial, da die Werkzeuge auf eine bereits
    vorhandene Bohrung angewiesen sind. Der Generator darf nicht selbst
    umsortieren, muss aber deutlich warnen."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"side": "inside", "tool": 1, "comment": "Innen-Schruppen"}),
        Operation(OpType.DRILL, {"tool": 2, "comment": "Bohren"}),
    ]
    warnings = validate_program_setup(ops, {})
    assert _warns_about_order(warnings)


def test_drill_before_internal_abspanen_is_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.DRILL, {"tool": 2, "comment": "Bohren"}),
        Operation(OpType.ABSPANEN, {"side": "inside", "tool": 1, "comment": "Innen-Schruppen"}),
    ]
    warnings = validate_program_setup(ops, {})
    assert not _warns_about_order(warnings)


def test_internal_op_without_any_drill_warns():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"side": "inside", "tool": 1, "comment": "Innen-Schruppen"}),
    ]
    warnings = validate_program_setup(ops, {})
    assert _warns_about_order(warnings)


def test_internal_groove_and_thread_before_drill_warn():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.GROOVE, {"lage": 1, "tool": 7, "comment": "Innen-Einstich"}),
        Operation(OpType.THREAD, {"orientation": "internal", "tool": 9, "comment": "Innengewinde"}),
        Operation(OpType.DRILL, {"tool": 10, "comment": "Bohren"}),
    ]
    warnings = validate_program_setup(ops, {})
    order_warnings = [w for w in warnings if "vor der (ersten) Bohrung" in w]
    assert len(order_warnings) == 2


def test_external_only_program_is_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"side": "outside", "tool": 1, "comment": "Aussen-Schruppen"}),
        Operation(OpType.GROOVE, {"lage": 0, "tool": 4, "comment": "Aussen-Einstich"}),
        Operation(OpType.THREAD, {"orientation": "external", "tool": 8, "comment": "Aussengewinde"}),
    ]
    warnings = validate_program_setup(ops, {})
    assert not _warns_about_order(warnings)
