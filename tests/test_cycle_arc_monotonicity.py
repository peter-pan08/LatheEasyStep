from copy import deepcopy

import pytest

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode


@pytest.mark.parametrize("strategy", ["parallel_z", "parallel_x"])
def test_long_arc_with_monotonic_endpoints_is_rejected_before_cycle(strategy):
    ops, settings = example_programs()["Kontur_Radius_Fase.ngc"]
    ops[1].path[1] = {"type": "arc", "p1": (32., -8.), "p2": (26., -16.),
                      "c": (26., -11.4375), "ccw": False}
    ops[1].path[2]["p1"] = (26., -16.)
    ops[-1].params["slice_strategy"] = strategy
    with pytest.raises(ValueError, match="Bogen.*monoton"):
        generate_program_gcode(ops, settings)


def test_primitive_only_contour_keeps_arc_in_explicit_finish():
    ops, settings = example_programs()["Kontur_Radius_Fase.ngc"]
    ops[-1].params["mode"] = "finish"
    lines = generate_program_gcode(deepcopy(ops), settings)
    section = lines[lines.index("(Schlichtschnitt Kontur)"):]
    assert any(line.startswith(("G2 ", "G3 ")) for line in section)
