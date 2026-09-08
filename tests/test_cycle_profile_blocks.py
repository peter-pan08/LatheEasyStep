import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType


def test_g71_profile_sub_uses_only_g1_g2_g3_for_profile():
    m = ProgramModel()
    path = [(40.0, 0.0), (30.0, -5.0), (20.0, -10.0)]
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
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xa": 40.0, "xra": 50.0, "zra": 5.0}
    g = "\n".join(m.generate_gcode())

    assert "G71 Q" in g
    assert "o100 sub" in g
    sub_block = g.split("o100 sub", 1)[1].split("o100 endsub", 1)[0]
    assert "G0 X" not in sub_block