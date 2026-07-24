import sys, os

# ensure handler & slicer importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, OpType, Operation


def test_abspanen_finish_allowance_comments():
    m = ProgramModel()
    path = [(40.0, 0.0), (30.0, -5.0)]
    params = {"mode": 0, "depth_per_pass": 1.0, "feed": 0.2, "tool": 1,
              "finish_allow_x": 0.5, "finish_allow_z": 0.25,
              "slice_strategy": 1}  # choose parallel X roughing
    op = Operation(OpType.ABSPANEN, params=params, path=path)
    m.add_operation(op)
    m.program_settings = {"sc": 3.0, "xa": 40.0, "xra": 45.0, "zra": 5.0}
    gcode = "\n".join(m.generate_gcode())
    # comment should mention the finish allowances we provided
    assert "Schlichtaufmaß" in gcode or "finish allow" in gcode.lower()

    # rough cycle X value should be reduced by the radial allowance (stock=40)
    assert "X39.500" in gcode or "x39.500" in gcode.lower()
    assert "0.500" in gcode or "0.25" in gcode
