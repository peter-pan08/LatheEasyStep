import sys
import os
import pytest

# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType

DEFAULT_RETRACT_SETTINGS = {"xra": 50.0, "zra": 5.0}


def test_parting_slice_index_triggers_parallel_x():
    m = ProgramModel()
    # slice_strategy data value (1 -> parallel_x)
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 1, "slice_step": 0.5, "depth_per_pass": 0.5, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel X)" in g


def test_parting_slice_index_triggers_parallel_z():
    m = ProgramModel()
    # slice_strategy data value (2 -> parallel_z)
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "slice_step": 0.5, "depth_per_pass": 0.5, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel Z)" in g


def test_parting_slice_string_triggers_parallel_x():
    m = ProgramModel()
    # slice_strategy as explicit string
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": "parallel_x", "slice_step": 1.0, "depth_per_pass": 1.0, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel X)" in g


def test_parting_slice_string_triggers_parallel_z():
    m = ProgramModel()
    # slice_strategy as explicit string
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": "parallel_z", "slice_step": 1.0, "depth_per_pass": 1.0, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel Z)" in g


def test_parting_parallel_z_non_monotonic_x_falls_back_to_move_based():
    m = ProgramModel()
    # Non-monotonic X profile -> must fall back to move-based roughing.
    path = [(20.0, 0.0), (10.0, -5.0), (15.0, -10.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {
                "mode": 0,
                "slice_strategy": "parallel_z",
                "slice_step": 1.0,
                "depth_per_pass": 1.0,
                "feed": 0.2,
                "tool": 1,
            },
            path=path,
        )
    ]
    m.program_settings = {"xa": 40.0, "xra": 50.0, "zra": 5.0}
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel Z - Move-based)" in g
    assert "G71 Q" not in g


def test_internal_parallel_z_cycle_uses_contour_based_stock_x_when_xi_is_zero():
    m = ProgramModel()
    path = [(50.0, 0.0), (40.0, -10.0), (10.0, -40.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {
                "mode": 0,
                "side": 1,
                "slice_strategy": "parallel_z",
                "depth_per_pass": 1.0,
                "feed": 0.2,
                "tool": 1,
            },
            path=path,
        )
    ]
    m.program_settings = {"xi": 0.0, "xri": 2.0, "zri": 5.0}
    g = "\n".join(m.generate_gcode())
    # G71/G72 werden fuer Innenbearbeitung nicht mehr verwendet (real gegen
    # den LinuxCNC-Interpreter bestaetigt: der Zyklus erzeugt dort fuer
    # Innenkonturen nur einen einzigen durchgehenden Schnitt statt echter
    # Treppenstufen-Passes) - die bewegungsbasierte Ersatzloesung uebernimmt
    # weiterhin korrekt den kontur-basierten Materialgrenzwert (10.0, nicht
    # 0.0), sichtbar am ersten X-Band, das bei diesem Wert beginnt.
    assert "G71 Q" not in g
    assert "(Pass 1: X-band [10.000,11.000])" in g


def test_internal_finish_with_nose_comp_gets_nonzero_entry_move():
    m = ProgramModel()
    path = [(50.0, 0.0), (40.0, -10.0), (10.0, -40.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {
                "mode": 1,
                "side": 1,
                "slice_strategy": "parallel_z",
                "depth_per_pass": 1.0,
                "feed": 0.2,
                "tool": 5,
            },
            path=path,
        )
    ]
    m.program_settings = {
        "xi": 0.0,
        "xri": 9.0,
        "xri_absolute": True,
        "zri": 2.0,
        "zri_absolute": True,
        "tools": {5: {"radius_mm": 0.4, "q": 3}},
    }
    g = "\n".join(m.generate_gcode())
    assert "G41.1 D0.8000 L3" in g
    assert "G0 X50.000 Z2.000" in g
    assert "G1 X50.000 Z0.000 F0.200" in g


def test_internal_parallel_z_approach_uses_xri_and_zri_safe_position():
    m = ProgramModel()
    path = [(50.0, 0.0), (40.0, -10.0), (10.0, -40.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {
                "mode": 0,
                "side": 1,
                "slice_strategy": "parallel_z",
                "depth_per_pass": 1.0,
                "feed": 0.2,
                "tool": 1,
            },
            path=path,
        )
    ]
    m.program_settings = {"xi": 0.0, "xri": 9.0, "xri_absolute": True, "zri": 4.0, "zri_absolute": True}
    lines = m.generate_gcode()
    # G71 wird fuer Innenbearbeitung nicht mehr verwendet (siehe Kommentar im
    # Test oben) - die sichere XRI-/ZRI-Anfahrt bleibt aber ueber denselben
    # resolve_retract_targets()-Pfad auch in der bewegungsbasierten
    # Ersatzloesung erhalten.
    idx = lines.index("(ABSPANEN Rough - parallel Z - Move-based)")
    assert lines[idx + 1] == "G0 Z4.000"
    assert lines[idx + 2] == "G0 X9.000"


def test_internal_parallel_z_rejects_unplausible_xri():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {"mode": 0, "side": 1, "slice_strategy": "parallel_z", "depth_per_pass": 1.0, "feed": 0.2, "tool": 1},
            path=[(50.0, 0.0), (40.0, -10.0), (10.0, -40.0)],
        )
    ]
    m.program_settings = {"xi": 0.0, "xri": 12.0, "xri_absolute": True, "zri": 4.0, "zri_absolute": True}
    with pytest.raises(ValueError, match="XRI=.*unplausibel"):
        m.generate_gcode()


def test_internal_finish_entry_uses_checked_approach_not_raw_diagonal_move():
    """Realer Bug (Test.lse, Innen-Schlichten): der Einfahrpunkt vor dem
    Schlichtschnitt wurde als EIN einzelner diagonaler G0 (X und Z gleichzeitig)
    direkt aus der vorherigen Position emittiert - ohne jede Pruefung, ob dieser
    Punkt im Rohteil bzw. in der Futter-Sperrzone liegt, und ohne die sichere
    Zwei-Schritt-Sequenz (erst Z, dann X), die an anderer Stelle im selben
    Generator (Schrupp-Zustellung) bereits verwendet wird. Jetzt laeuft die
    Schlicht-Einfahrt ueber denselben emit_approach()-Helfer wie die
    Schrupp-Zustellung, der die Lage prueft und warnt."""
    m = ProgramModel()
    path = [(10.0, 0.0), (10.0, -20.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {"mode": 1, "side": 1, "slice_strategy": "parallel_z", "depth_per_pass": 1.0, "feed": 0.15, "tool": 11},
            path=path,
        )
    ]
    m.program_settings = {
        # za bewusst tiefer als der berechnete Einfahrpunkt (Z=2, aus
        # ZRI=0/absolute=False -> safe_z=0 + Leadout 2.0), damit der
        # Einfahrpunkt tatsaechlich noch im Rohteil liegt und die Warnung
        # unabhaengig vom Schrupp-/Schlicht-Modus dieselbe Kollisionslage prueft.
        "xa": 50.0, "xi": 0.0, "za": 5.0, "zi": -80.0,
        "xri": 9.8, "xri_absolute": True, "zri": 0.0, "zri_absolute": False,
    }
    g = "\n".join(m.generate_gcode())
    assert "liegt im Rohteil" in g
