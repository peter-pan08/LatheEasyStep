from copy import deepcopy
import pytest

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode


def test_explicit_finish_preference_prevents_g70_reuse():
    ops, settings = example_programs()["Kontur_Radius_Fase.ngc"]
    ops[-1].params["mode"] = "rough"
    finish = deepcopy(ops[-1])
    finish.params.update(mode="finish", output_preference="prefer_explicit", tool=3)
    ops.append(finish)
    lines = generate_program_gcode(ops, settings)
    assert any(line.startswith("G71 ") for line in lines)
    assert not any(line.startswith("G70 ") for line in lines)
    assert "(Schlichtschnitt Kontur)" in lines


@pytest.mark.parametrize("field,value", [("infeed_q", 89.99999)])
def test_thread_output_rounding_does_not_escape_valid_range(field, value):
    ops, settings = example_programs()["Gewinde.ngc"]
    ops[-1].params[field] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)


@pytest.mark.parametrize("field,value", [("cutting_speed", .01), ("start_x", .00001)])
def test_css_values_must_remain_positive_in_output(field, value):
    ops, settings = example_programs()["Planen.ngc"]
    ops[-1].params.update(spindle_mode="css", cutting_speed=120, spindle_max_rpm=2500)
    ops[-1].params[field] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)
