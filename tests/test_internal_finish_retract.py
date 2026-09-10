import pytest

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import Operation, OpType


def finish_case(reverse=False, radius=0, xri=9, zri=2):
    # xi bewusst weit ueber allen in diesem Modul getesteten xri-Werten
    # (bis 11), damit die XRI-vs-XI-Materialfreiheitspruefung
    # (validate_internal_material_clearance) diese Faelle nicht faelschlich
    # blockiert - hier wird ausschliesslich die Einfahrweg-/Rundungsgrenze
    # der Werkzeugradiuskorrektur getestet, nicht die Materialfreiheit.
    settings = dict(make_program_settings(), xi=20, xri=xri, zri=zri,
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


@pytest.mark.parametrize("reverse", [False, True])
def test_internal_finish_approaches_axially_on_xri_before_cut_diameter(reverse):
    op, settings = finish_case(reverse=reverse, xri=8)
    lines = generate_program_gcode([op], settings)
    section = lines[lines.index("(Schlichtschnitt Kontur)") + 1:]
    start_x, start_z = op.path[0]
    z_move = section.index(f"G0 Z{start_z:.3f}")
    x_move = next(idx for idx, line in enumerate(section) if line.startswith("G1 ") and f"X{start_x:.3f}" in line)
    assert z_move < x_move
    assert "G0 X8.000" in section[:z_move]


@pytest.mark.parametrize("xri", [10.4, 10.4004])
def test_internal_compensation_rejects_insufficient_lead_in_after_rounding(xri):
    op, settings = finish_case(reverse=False, radius=.4, xri=xri)
    with pytest.raises(ValueError, match="Einfahrweg"):
        generate_program_gcode([op], settings)


def test_internal_compensation_accepts_lead_in_just_above_tool_diameter():
    op, settings = finish_case(reverse=False, radius=.4, xri=10.3994)
    lines = generate_program_gcode([op], settings)
    assert "G0 Z-30.000" in lines
    assert "G41.1 D0.8000 L3" in lines
