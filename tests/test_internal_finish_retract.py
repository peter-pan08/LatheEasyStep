import pytest

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import Operation, OpType


def finish_case(reverse=False, radius=0, xri=9):
    settings = dict(make_program_settings(), xi=10, xri=xri, zri=2,
                    xri_absolute=True, zri_absolute=True,
                    tools={11: {"radius_mm": radius, "q": 3}})
    points = [(12., -30.), (18., 0.)]
    op = Operation(OpType.ABSPANEN, {"side": "inside", "mode": "finish", "tool": 11,
        "spindle": 800, "feed": .15, "depth_per_pass": .5, "slice_strategy": "parallel_z"},
        list(reversed(points)) if reverse else points)
    return op, settings


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("radius", [0, .4])
def test_internal_finish_retracts_radially_before_axially(reverse, radius):
    op, settings = finish_case(reverse, radius)
    lines = generate_program_gcode([op], settings)
    end_x, end_z = op.path[-1]
    end = lines.index(f"G1 X{end_x:.3f} Z{end_z:.3f} F0.150")
    tail = lines[end + 1:]
    if radius:
        assert tail[:3] == ["G40", "G1 X9.000 F0.150", "G0 Z2.000"]
    else:
        assert tail[:2] == ["G0 X9.000", "G0 Z2.000"]


@pytest.mark.parametrize("xri", [11, 10.4, 10.3996])
def test_internal_compensation_cannot_cancel_with_insufficient_radial_clearance(xri):
    op, settings = finish_case(reverse=True, radius=.4, xri=xri)
    with pytest.raises(ValueError, match="Abwahl"):
        generate_program_gcode([op], settings)


def test_clearance_just_above_diameter_after_rounding_is_accepted():
    op, settings = finish_case(reverse=True, radius=.4, xri=10.3994)
    assert "G1 X10.399 F0.150" in generate_program_gcode([op], settings)
