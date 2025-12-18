from lathe_easystep_handler import ProgramModel, Operation, OpType


def test_slice_step_defaults_to_depth_per_pass_when_unset():
    m = ProgramModel()
    # Add a parting operation with depth_per_pass set and without slice_step
    path = [(40.0, 2.0), (25.0, -5.0), (25.0, -35.0)]
    params = {"mode": 0, "depth_per_pass": 0.75, "slice_strategy": 1, "feed": 0.15}
    op = Operation(OpType.ABSPANEN, params=params, path=path)
    m.operations = [op]
    g = "\n".join(m.generate_gcode())
    # The generator documents the chosen slice_step in a #<_slice_step> comment
    assert "#<_slice_step> = 0.750" in g
