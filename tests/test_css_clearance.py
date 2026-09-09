import pytest

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode


@pytest.mark.parametrize("filename", ["Planen.ngc", "Abdrehen.ngc", "Innen_Stufe.ngc", "Gewinde.ngc", "Einstich.ngc"])
def test_explicit_rapid_moves_leave_css(filename):
    ops, settings = example_programs()[filename]
    ops[-1].params.update(spindle_mode="css", cutting_speed=120, spindle_max_rpm=2500)
    lines = generate_program_gcode(ops, settings)
    active = False
    activations = 0
    in_sub = False
    for line in lines:
        if line.endswith(" sub"):
            in_sub = True
        if line.endswith(" endsub"):
            in_sub = False
            continue
        if in_sub:
            continue
        if line.startswith("G96 "):
            active = True
            activations += 1
        elif line.startswith("G97 "):
            active = False
        elif line.startswith(("G0 ", "G53 ")) or " M6" in line:
            assert not active, line
    assert activations
    assert not active
