import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation


def _contour(name, path):
    return Operation(OpType.CONTOUR, {"name": name}, path=path)


def test_unused_contour_subroutine_is_not_emitted():
    """Realer Bugreport: Eine Kontur-Subroutine (o101) wurde immer definiert,
    sobald ihre Kontur einen Namen hatte - unabhaengig davon, ob ein Abspanen-
    Schritt sie ueberhaupt per G71/G72 (Q<num>) referenziert. Faellt die
    Bearbeitung auf Move-based-Code zurueck (z. B. weil die Kontur nicht
    zyklustauglich ist oder 'Ausgabe bevorzugen' auf explizit steht), blieb die
    Definition als toter Code im Programm stehen."""
    settings = make_program_settings()
    # Nicht-monotone X-Werte erzwingen den Move-based-Fallback statt G71/G72.
    non_cycle_path = [(20.0, 0.0), (10.0, -5.0), (15.0, -10.0)]
    contour = _contour("kontur_a", non_cycle_path)
    abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "slice_strategy": "parallel_z", "mode": 0, "contour_name": "kontur_a",
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings)
    text = "\n".join(lines)
    assert "Subroutine Definitions" not in text
    assert "o100 sub" not in text
    assert "Move-based" in text


def test_used_contour_subroutine_is_still_emitted():
    settings = make_program_settings()
    monotonic_path = [(20.0, 0.0), (15.0, -5.0), (10.0, -10.0)]
    contour = _contour("kontur_b", monotonic_path)
    abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "slice_strategy": "parallel_z", "mode": 0, "contour_name": "kontur_b",
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings)
    text = "\n".join(lines)
    assert "Subroutine Definitions" in text
    assert "o100 sub" in text
    assert "G71 Q100" in text
