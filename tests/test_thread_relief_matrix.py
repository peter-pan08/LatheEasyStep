from copy import deepcopy
from types import SimpleNamespace
import pytest

from lathe_easystep.verification_cases import thread_relief_case, same_tool_transition_case
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.ui_persistence import write_gcode_file


@pytest.mark.parametrize("internal", [False, True])
@pytest.mark.parametrize("left", [False, True])
def test_thread_relief_matrix(internal, left):
    ops, settings = thread_relief_case(internal, left)
    before = deepcopy((ops, settings))
    lines = generate_program_gcode(ops, settings)
    cycle = next(line for line in lines if line.startswith("G76 "))
    assert f"Z{-10 if left else -25:.3f}" in cycle
    assert any(line.startswith(("G2 ", "G3 ")) for line in lines)
    assert (ops, settings) == before
    # Extending the contour behind the thread must not move its relief.
    if internal:
        ops[0].params["start_z"] = -50.0
    else:
        ops[0].params["segments"][-1]["z"] = -50.0
    extended = generate_program_gcode(ops, settings)
    arcs = lambda output: [line for line in output if line.startswith(("G2 ", "G3 "))]
    assert arcs(extended) == arcs(lines)
    assert next(line for line in extended if line.startswith("G76 ")) == cycle


@pytest.mark.parametrize("internal", [False, True])
@pytest.mark.parametrize("left", [False, True])
def test_insufficient_relief_space_preserves_export(internal, left, tmp_path):
    ops, settings = thread_relief_case(internal, left, insufficient=True)
    target = tmp_path / "existing.ngc"
    target.write_text("existing program")
    handler = SimpleNamespace(_normalized_file_path=str,
        _build_gcode_lines=lambda: generate_program_gcode(ops, settings))
    with pytest.raises(ValueError, match="Freistich"):
        write_gcode_file(handler, str(target))
    assert target.read_text() == "existing program"


@pytest.mark.parametrize("internal", [False, True])
def test_same_tool_rough_finish_has_fixed_speed_clearance(internal):
    ops, settings = same_tool_transition_case(internal)
    lines = generate_program_gcode(ops, settings)
    assert sum(" M6" in line for line in lines) == 1
    finish = lines.index("(Schlichtschnitt Kontur)")
    assert any(line.startswith("G97 ") for line in lines[:finish])
    start = next(i for i in range(finish, len(lines)) if lines[i].startswith("G96 "))
    assert any(line.startswith("G0 ") for line in lines[finish:start])
    assert "S100.0" in lines[start]
