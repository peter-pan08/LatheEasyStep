import re

import pytest
import sys
import os
# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType

RETRACT_SETTINGS = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0}


def test_face_rough_with_pause_raises_instead_of_silently_ignoring():
    """SICHERHEITSFUND 2026-09-13: PLANEN-Schruppen nutzt ausschliesslich den
    G72-Zyklus - eine Vorschub-Unterbrechung kann dort nicht eingefuegt
    werden. Vorher wurde die Checkbox stillschweigend ignoriert (eine nie
    aufgerufene Subroutine-Definition landete im Programm, ohne jede
    Wirkung). Jetzt lauter Abbruch statt stiller Wirkungslosigkeit."""
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.FACE, {
        "mode": 0, "pause_enabled": True, "pause_distance": 1.0,
        "start_x": 40.0, "start_z": 1.0, "end_x": -1.0, "end_z": 0.0,
        "finish_allow_z": 0.05, "depth_max": 0.4, "retract": 0.5,
        "feed": 0.2, "spindle": 1300.0, "tool": 1,
        "edge_type": 0, "edge_size": 0.0, "coolant": False
    })]
    with pytest.raises(ValueError, match="Vorschub-Unterbrechung"):
        m.generate_gcode()


def test_face_finish_ignores_pause_flag_harmlessly():
    """Reines Schlichten (G70) schruppt nicht - die Pause-Checkbox bleibt
    hier wirkungslos, aber das ist keine stille Ueberraschung: G70 fuehrt
    ohnehin nur die Fertigkontur einmal ab, kein Schruppdurchgang, der
    unterbrochen werden koennte."""
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.FACE, {
        "mode": 1, "pause_enabled": True, "pause_distance": 1.0,
        "start_x": 40.0, "start_z": 1.0, "end_x": -1.0, "end_z": 0.0,
        "finish_allow_z": 0.05, "depth_max": 0.4, "retract": 0.5,
        "feed": 0.2, "spindle": 1300.0, "tool": 1,
        "edge_type": 0, "edge_size": 0.0, "coolant": False
    })]
    g = "\n".join(m.generate_gcode())
    assert "G70 " in g


def test_abspanen_rough_pause_emits_real_segmented_feed_with_dwells():
    """SICHERHEITSFUND 2026-09-13: der fruehere `o<step_line_pause> call [...]`
    rief eine Subroutine auf, die NUR `G4 P[#7]` (eine Verweilzeit) enthielt -
    keine Bewegung. Die gesamte lange Schnittstrecke wurde dadurch nie
    tatsaechlich geschnitten, obwohl das Programm anschliessend so weiterlief,
    als sei das Material bereits entfernt (per rs274-Bewegungsspur bestaetigt).
    Jetzt muss die Strecke als echte G1-Teilschnitte mit G4-Pausen dazwischen
    erscheinen und tatsaechlich am Zielpunkt ankommen."""
    m = ProgramModel()
    m.program_settings.update(dict(RETRACT_SETTINGS, xa=40.0, xi=0.0, za=0.0, zi=-55.0))
    m.operations = [Operation(OpType.ABSPANEN, {
        "mode": 0, "pause_enabled": True, "pause_distance": 5.0,
        "depth_per_pass": 2.0, "feed": 0.15, "slice_strategy": "parallel_z",
        "spindle": 1000.0, "tool": 1,
    }, path=[(0.0, 0.0), (30.0, 0.0), (30.0, -20.0)])]
    g = "\n".join(m.generate_gcode())

    assert "o<step_line_pause>" not in g

    lines = g.split("\n")
    # Erster Schrupp-Pass haelt X konstant auf X38 (Rohteil 40, erste
    # Zustelltiefe 2mm) und schneidet in vier 5mm-Teilschnitten von Z0 bis
    # Z-20, mit G4-Pausen dazwischen.
    pass1 = lines[lines.index("(Pass 1: X-band [38.000,40.000])"):]
    pass1 = pass1[:pass1.index("(Pass 2: X-band [36.000,38.000])")]
    cuts = [l for l in pass1 if l.startswith("G1 ")]
    dwells = [l for l in pass1 if l.startswith("G4 ")]
    z_values = [float(re.search(r"Z(-?[0-9.]+)", l).group(1)) for l in cuts]
    # G1 Z0.000 (Einfahrt auf z_entry) + vier 5mm-Teilschnitte bis zum
    # tatsaechlichen Bandende Z-20.000 (nicht nur "irgendwo nahe dran").
    assert z_values == [0.0, -5.0, -10.0, -15.0, -20.0]
    assert len(dwells) == 3  # 4 Teilschnitte -> 3 Pausen dazwischen
    assert all(l == "G4 P0.500" for l in dwells)


def test_abspanen_rough_pause_reaches_actual_endpoint_via_rs274_equivalent_math():
    """Cross-check ohne externen Interpreter: die letzte G1-Zeile jeder
    unterbrochenen Schnittstrecke muss exakt auf dem geometrisch wahren
    Endpunkt liegen (nicht nur "irgendwo nahe dran")."""
    from lathe_easystep.gcode_roughing import _emit_segment_with_pauses

    lines = []
    _emit_segment_with_pauses(lines, (10.0, 0.0), (10.0, -13.0), 0.2, True, 4.0, 0.5)
    cuts = [l for l in lines if l.startswith("G1 ")]
    assert cuts[-1] == "G1 X10.000 Z-13.000 F0.200"
    dwells = [l for l in lines if l.startswith("G4 ")]
    assert len(dwells) == len(cuts) - 1


def test_abspanen_rough_without_slicing_aborts_generation():
    """LES-002: ein Schruppstep ohne Bearbeitungsrichtung erzeugte frueher nur
    eine Warnzeile und keinen Schnitt - ein leises, leicht zu uebersehendes
    Nichts im Programm. Das ist jetzt ein harter Abbruch mit ValueError, damit
    ein solcher Step nicht unbemerkt als scheinbar gueltiges Programm
    durchgeht."""
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0, "depth_per_pass": 0.5, "feed": 0.15, "spindle": 1000.0, "tool": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    with pytest.raises(ValueError, match="keinen einzigen Schnitt"):
        m.generate_gcode()


def test_abspanen_finish_suppresses_pause_segmentation():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 1, "pause_enabled": True, "pause_distance": 1.0, "depth_per_pass": 0.5, "feed": 0.15, "spindle": 1000.0, "tool": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "G4 " not in g
