import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


def _dangling_contour_warnings(warnings):
    return [w for w in warnings if "existiert" in w]


def test_abspanen_referencing_deleted_contour_is_warned_not_silent():
    """SICHERHEITSFUND 2026-09-13: eine ABSPANEN-Operation verweist per
    `contour_name` auf eine CONTOUR-Operation. Wird diese Kontur spaeter
    geloescht (oder umbenannt), blieb das bisher in `validate_program_setup()`
    still - keine Warnung waehrend der Bearbeitung, erst ein harter
    ValueError beim naechsten "Programm erzeugen"/"Speichern". Der kaputte
    Verweis muss stattdessen sofort als Warnung sichtbar sein."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.ABSPANEN,
            {"tool": 1, "side": "outside", "mode": "rough", "contour_name": "geloeschte_kontur"},
        ),
    ]
    warnings = _dangling_contour_warnings(validate_program_setup(ops, {}))
    assert len(warnings) == 1
    assert "geloeschte_kontur" in warnings[0]


def test_abspanen_referencing_existing_contour_stays_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "vorhanden", "segments": []}),
        Operation(
            OpType.ABSPANEN,
            {"tool": 1, "side": "outside", "mode": "rough", "contour_name": "vorhanden"},
        ),
    ]
    assert _dangling_contour_warnings(validate_program_setup(ops, {})) == []


def test_abspanen_without_any_contour_name_is_not_flagged_as_dangling():
    """Ein leerer contour_name ist ueber die UI beim Anlegen einer neuen
    Abspanen-Operation bereits ausgeschlossen (siehe `_handle_add_operation()`)
    - dieser Fall ist deshalb bewusst NICHT als "geloeschte Kontur" gemeldet,
    das waere eine irrefuehrende Ursachenzuschreibung."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 1, "side": "outside", "mode": "rough"}),
    ]
    assert _dangling_contour_warnings(validate_program_setup(ops, {})) == []
