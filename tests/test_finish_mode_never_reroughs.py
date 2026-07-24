import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation


def _generate(mode, contour_name="k", path=None):
    settings = make_program_settings()
    path = path or [(20.0, 0.0), (15.0, -5.0), (10.0, -10.0)]
    contour = Operation(OpType.CONTOUR, {"name": contour_name}, path=path)
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "slice_strategy": "parallel_z", "mode": mode, "contour_name": contour_name,
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, op], settings)
    return "\n".join(lines)


def test_finish_only_mode_never_emits_g71_or_g72():
    """Realer Bugreport (Inventor-Post-Vergleich): 'mode=finish darf keinen
    neuen Schruppzyklus G71 erzeugen'. Ein dedizierter Schlichtstep (z. B. mit
    eigenem Schlichtwerkzeug nach einem separaten Schruppstep) fuehrte bei
    gueltiger Bearbeitungsrichtung trotzdem einen vollen G71/G72-Schruppzyklus
    aus - das Material war durch den fruaheren Schruppstep bereits abgetragen,
    die Wiederholung ist unnoetig und potenziell gefaehrlich (falsches
    Werkzeug im bereits geschruppten Material)."""
    text = _generate(mode=1)
    assert "G71" not in text
    assert "G72" not in text
    assert "Schlichtschnitt Kontur" in text


def test_rough_mode_emits_g71_g72_as_before():
    text = _generate(mode=0)
    assert "G71 Q" in text
    assert "Schlichtschnitt Kontur" not in text


def test_rough_finish_mode_still_emits_cycle_and_finish():
    text = _generate(mode=2)
    assert "G71 Q" in text


def test_rough_finish_string_id_resolves_like_numeric_index():
    """Realtest-Antwort Q14 ('drittes Combo-Item Schruppen + Schlichten? -
    ja'): PARTING_MODE_INDEX kannte bisher nur 'rough'/'finish', nicht
    'rough_finish' - das ID-only-Combo liefert seit der Umstellung aber
    String-IDs ueber currentData(), keine numerischen Indizes mehr. Ohne den
    fehlenden Eintrag waere resolve_enum_index() auf den default (0/rough)
    zurueckgefallen, sobald jemand das neue dritte Combo-Item waehlt - Schlichten
    waere dann stillschweigend uebersprungen worden."""
    text_numeric = _generate(mode=2)
    text_string_id = _generate(mode="rough_finish")
    assert text_string_id == text_numeric
    assert "G71 Q" in text_string_id
    assert "Schlichtschnitt Kontur" in text_string_id
