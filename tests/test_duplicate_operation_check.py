import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


def _duplicate_warnings(warnings):
    return [w for w in warnings if "identisch" in w]


def test_identical_operations_produce_optional_warning_not_deletion():
    """Realer Bugreport: eine doppelte Innen-Schlicht-Operation (gleicher
    Typ, gleiche Bearbeitungsparameter) soll gemeldet werden, aber NICHT
    automatisch geloescht oder veraendert werden - der Nutzer entscheidet."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.ABSPANEN,
            {"tool": 11, "side": "inside", "mode": "finish", "contour_name": "ausdrehen", "comment": "11. Abspanen"},
        ),
        Operation(
            OpType.ABSPANEN,
            {"tool": 11, "side": "inside", "mode": "finish", "contour_name": "ausdrehen", "comment": None},
        ),
    ]
    warnings = _duplicate_warnings(validate_program_setup(ops, {}))
    assert len(warnings) == 1
    assert "Operation 3" in warnings[0] and "Operation 2" in warnings[0]
    # Keine automatische Aenderung: beide Operationen bleiben unangetastet.
    assert len(ops) == 3


def test_different_mode_is_not_flagged_as_duplicate():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 11, "side": "inside", "mode": "rough", "contour_name": "ausdrehen"}),
        Operation(OpType.ABSPANEN, {"tool": 11, "side": "inside", "mode": "finish", "contour_name": "ausdrehen"}),
    ]
    assert _duplicate_warnings(validate_program_setup(ops, {})) == []


def test_different_comment_alone_does_not_prevent_duplicate_detection():
    """Kommentar/Cache-Felder duerfen den Vergleich nicht verfaelschen - zwei
    Operationen mit identischen Bearbeitungsparametern aber unterschiedlichem
    (oder fehlendem) Kommentar sind trotzdem ein Duplikat."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.GROOVE, {"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0, "comment": "8. Einstich (7)"}),
        Operation(OpType.GROOVE, {"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0, "comment": None}),
    ]
    assert len(_duplicate_warnings(validate_program_setup(ops, {}))) == 1


def test_contour_operations_are_never_flagged_as_duplicate():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": []}),
        Operation(OpType.CONTOUR, {"name": "ausdrehen", "segments": []}),
    ]
    assert _duplicate_warnings(validate_program_setup(ops, {})) == []
