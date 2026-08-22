import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_utils import is_monotonic_z, is_monotonic_z_decreasing, is_monotonic_z_increasing
from lathe_easystep.model import OpType, Operation

# Reale Innenkontur (Nutzer-Testprogramm "ausdrehen"): vom tiefsten Punkt
# (Bohrungsgrund) zur Bohrungsoeffnung definiert - Z UND X steigen monoton
# ueber den gesamten Pfad. Geometrisch einwandfrei, wurde aber vor dem Fix
# von is_monotonic_z_decreasing() als "nicht G71-tauglich" verworfen, weil
# nur die FALLENDE Richtung akzeptiert wurde.
_BORE_TO_OPENING_PATH = [
    (10.0, -44.0),
    (11.4, -44.0),
    (12.0, -43.4),
    (12.0, -10.5),
    (13.0, -10.0),
    (16.0, -10.0),
    (16.0, -1.0),
    (18.0, 0.0),
    (19.2, 0.0),
]


def _internal_rough_op(path, **overrides):
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 9.3, "xri_absolute": True})
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
            **overrides,
        },
        path=path,
    )
    return [Operation(OpType.PROGRAM_HEADER, {}), op], settings


def test_is_monotonic_z_accepts_both_directions():
    increasing = [(0.0, -10.0), (1.0, -5.0), (2.0, 0.0)]
    decreasing = [(0.0, 0.0), (1.0, -5.0), (2.0, -10.0)]
    non_monotonic = [(0.0, -10.0), (1.0, 0.0), (2.0, -5.0)]
    assert is_monotonic_z_increasing(increasing) is True
    assert is_monotonic_z_decreasing(increasing) is False
    assert is_monotonic_z(increasing) is True
    assert is_monotonic_z(decreasing) is True
    assert is_monotonic_z(non_monotonic) is False


def test_internal_roughing_bore_to_opening_direction_uses_g71_cycle():
    """Realer Bugreport: Innen-Abspanen mit einer vom Bohrungsgrund zur
    Oeffnung definierten Kontur (Z steigt monoton) fiel bisher auf eine grobe
    bewegungsbasierte Ersatzloesung zurueck ("Fallback-Grund: automatische
    Entscheidung -> Move-based") statt den G71-Zyklus zu nutzen, obwohl die
    Kontur geometrisch fuer G71 geeignet ist (X und Z beide monoton)."""
    operations, settings = _internal_rough_op(_BORE_TO_OPENING_PATH)
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    assert any(line.startswith("G71 ") for line in lines)
    assert "Fallback-Grund: automatische Entscheidung -> Move-based" not in text
    assert "ABSPANEN Rough - parallel Z - Move-based" not in text


def test_internal_roughing_opening_to_bore_direction_still_uses_g71_cycle():
    """Kontrollfall: die umgekehrte (bereits vorher funktionierende) Richtung
    - von der Oeffnung zum Bohrungsgrund, Z faellt monoton - darf durch die
    symmetrische Pruefung nicht regressieren."""
    reversed_path = list(reversed(_BORE_TO_OPENING_PATH))
    operations, settings = _internal_rough_op(reversed_path)
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    assert any(line.startswith("G71 ") for line in lines)
    assert "Fallback-Grund: automatische Entscheidung -> Move-based" not in text


def test_internal_roughing_uses_drilled_diameter_as_stock_when_xi_unset():
    """Realer Bugreport: Bei Vollzylinder-Rohteil (kein XI im Programmkopf
    gesetzt, xi=0.0 - die Bohrung entsteht erst durch einen vorangehenden
    Bohren-Step) fiel _resolve_roughing_stock_x() auf den kleinsten X-Wert
    der ZIELKONTUR selbst zurueck (hier 10.0). Der G71-Zyklus 'startete'
    damit praktisch schon auf der Fertigkontur - kein echter Zustellweg zum
    Abfahren, sichtbar als 'nur einmal die Kontur nachfahren, keine echte
    Abspanstrategie'. Der tatsaechlich gebohrte Durchmesser (hier 8.0, aus
    dem vorangehenden Bohren-Step) muss stattdessen als Materialgrenze
    verwendet werden, wenn er kleiner als die Zielkontur ist."""
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 6.0, "xri_absolute": True})
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0, "diameter": 8.0},
        path=[(0.0, 2.0), (0.0, -45.0)],
    )
    rough = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
        },
        path=_BORE_TO_OPENING_PATH,
    )
    operations = [Operation(OpType.PROGRAM_HEADER, {}), drill, rough]
    lines = generate_program_gcode(operations, settings)
    g71_lines = [line for line in lines if line.startswith("G71 ")]
    assert len(g71_lines) == 1
    assert "X8.000" in g71_lines[0]


def test_internal_roughing_ignores_drilled_diameter_larger_than_target():
    """Kontrollfall: ein gebohrter Durchmesser, der bereits (fehlerhaft)
    groesser als die Zielkontur waere, darf nicht blind uebernommen werden -
    Fallback bleibt der bisherige, sichere kleinste Konturwert."""
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 6.0, "xri_absolute": True})
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0, "diameter": 15.0},
        path=[(0.0, 2.0), (0.0, -45.0)],
    )
    rough = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
        },
        path=_BORE_TO_OPENING_PATH,
    )
    operations = [Operation(OpType.PROGRAM_HEADER, {}), drill, rough]
    lines = generate_program_gcode(operations, settings)
    g71_lines = [line for line in lines if line.startswith("G71 ")]
    assert len(g71_lines) == 1
    assert "X10.000" in g71_lines[0]
