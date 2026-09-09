import re
from lathe_easystep_handler import ProgramModel, Operation, OpType


def test_slice_step_defaults_to_depth_per_pass_when_unset():
    m = ProgramModel()
    # Use a non-monotonic X path to force move-based roughing
    path = [(40.0, 2.0), (25.0, -5.0), (30.0, -10.0), (25.0, -35.0)]
    params = {"mode": 0, "depth_per_pass": 0.75, "slice_strategy": 1, "feed": 0.15, "spindle": 1000.0, "tool": 1}
    op = Operation(OpType.ABSPANEN, params=params, path=path)
    m.operations = [op]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 60.0, "zra": 5.0}
    g = "\n".join(m.generate_gcode())
    # Move-based roughing should be used (not G72 cycle)
    assert "Move-based" in g
    # The Z-band width should match depth_per_pass (0.75) – last band may be shorter (remainder)
    bands = re.findall(r"Z-band \[([\-\d.]+),([\-\d.]+)\]", g)
    assert len(bands) > 0, "No Z-band comments found in move-based output"
    for lo, hi in bands[:-1]:  # all bands except the last
        width = float(hi) - float(lo)
        assert abs(width - 0.75) < 0.01, f"Band width {width} != 0.75"
    # Last band may be smaller but must be > 0
    last_w = float(bands[-1][1]) - float(bands[-1][0])
    assert 0 < last_w <= 0.75 + 0.01, f"Last band width {last_w} out of range"
