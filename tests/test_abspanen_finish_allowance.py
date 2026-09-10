import sys, os

# ensure handler & slicer importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, OpType, Operation


def test_abspanen_finish_allowance_comments():
    m = ProgramModel()
    path = [(40.0, 0.0), (30.0, -5.0)]
    params = {"mode": 0, "depth_per_pass": 1.0, "feed": 0.2, "spindle": 1000.0, "tool": 1,
              "finish_allow_x": 0.5, "finish_allow_z": 0.25,
              "slice_strategy": 1}  # choose parallel X roughing
    op = Operation(OpType.ABSPANEN, params=params, path=path)
    m.add_operation(op)
    m.program_settings = {"xt": 150.0, "zt": 300.0, "sc": 3.0, "xa": 40.0, "xra": 45.0, "zra": 5.0}
    gcode = "\n".join(m.generate_gcode())
    # comment should mention the finish allowances we provided
    assert "Schlichtaufmaß" in gcode or "finish allow" in gcode.lower()

    # LES-003 Fix 2026-09-10: der Zyklus-Startpunkt bleibt beim vollen
    # Rohteil (X40.000) - das Aufmass wird stattdessen ueber den echten
    # G71/G72-"D"-Parameter (radiales Aufmass zur Kontur) sowie "I"
    # (radiale Zustelltiefe) ausgedrueckt, empirisch gegen den realen
    # LinuxCNC-Interpreter verifiziert. D = finish_allow_x/2 = 0.250,
    # I = depth_per_pass/2 = 0.500 (beide UI-Werte sind Durchmesserwerte).
    assert "X40.000" in gcode
    assert "D0.250" in gcode
    assert "I0.500" in gcode
