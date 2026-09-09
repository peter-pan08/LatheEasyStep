from copy import deepcopy
import re
import math

import pytest

from lathe_easystep.examples import make_program_settings, example_programs
from lathe_easystep.model import Operation, OpType
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.contour_logic import build_contour_variants
from lathe_easystep.gcode_roughing import contour_sub_from_primitives, _emit_finish_primitives
from lathe_easystep.persistence import operation_to_step_data, step_data_to_operation


PROFILES = {
    "cylinder": [(12., -30.), (12., 0.)],
    "step": [(12., -30.), (12., -15.), (18., -15.), (18., 0.)],
    "cone": [(12., -30.), (18., 0.)],
}


@pytest.mark.parametrize("points", PROFILES.values(), ids=PROFILES.keys())
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("mode", ["rough", "finish", "rough_finish"])
def test_internal_profiles_preserve_xri_and_cut_in_both_contour_directions(points, reverse, mode):
    settings = dict(make_program_settings(), xi=10., xri=9., zri=2., xri_absolute=True, zri_absolute=True)
    op = Operation(OpType.ABSPANEN, {"side": "inside", "mode": mode, "tool": 11,
        "spindle": 800., "feed": .15, "depth_per_pass": .5, "slice_strategy": "parallel_z",
        "finish_allow_x": .2, "finish_allow_z": .1}, path=list(reversed(points)) if reverse else points)
    lines = generate_program_gcode([op], settings)
    assert not any(line.startswith(("G71 ", "G72 ")) for line in lines)
    cuts = [line for line in lines if line.startswith("G1 ")]
    assert cuts
    xs = [float(m.group(1)) for line in cuts if (m := re.search(r"\bX(-?[0-9.]+)", line))]
    assert xs and min(xs) >= settings["xri"]
    if mode == "finish":
        assert not any(line.startswith("(Pass ") for line in lines)
    else:
        assert sum(line.startswith("(Pass ") for line in lines) > 1


def test_relief_features_survive_save_load_and_share_emission_coordinates():
    ops, _ = example_programs()["Freistich_Mitte.ngc"]
    contour = ops[0]
    restored = step_data_to_operation(operation_to_step_data(contour))
    assert restored == contour
    original = deepcopy(contour.params)
    # This is also the primitive source used by ui_preview._collect_paths.
    preview = build_contour_variants(restored.params)["finish_primitives"]
    sub = contour_sub_from_primitives(preview, 100)[1:-1]
    finish = []
    _emit_finish_primitives(finish, preview, feed=.15)
    without_feed = [re.sub(r" F[0-9.]+$", "", line) for line in finish]
    assert without_feed == sub
    assert contour.params == original


def test_internal_allowance_leaves_material_for_the_finish_pass():
    settings = dict(make_program_settings(), xi=10., xri=9., zri=2., xri_absolute=True, zri_absolute=True)
    params = {"side": "inside", "mode": "rough_finish", "tool": 11,
        "spindle": 800., "feed": .15, "depth_per_pass": .5, "slice_strategy": "parallel_z",
        "finish_allow_x": .2, "finish_allow_z": .1}
    lines = generate_program_gcode([Operation(OpType.ABSPANEN, params, [(12., -30.), (12., 0.)])], settings)
    finish_index = lines.index("(Schlichtschnitt Kontur)")
    rough = lines[:finish_index]
    assert "G0 X11.800" in rough
    assert any("Z-29.900" in line for line in rough if line.startswith("G1"))
    assert not any("Z-30.000" in line for line in rough if line.startswith("G1"))
    assert any("X12.000 Z-30.000" in line for line in lines[finish_index:] if line.startswith("G1"))


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("mode", ["rough", "finish", "rough_finish"])
def test_internal_radius_preserves_arcs_and_material_limits(reverse, mode):
    ops, settings = example_programs()["Innen_Radius.ngc"]
    contour = ops[0].params
    if reverse:
        contour.update(start_x=18.0, start_z=0.0, segments=[
            {"x": 18.0, "z": -15.0},
            {"x": 12.0, "z": -15.0, "edge": "radius", "edge_size": 1.0},
            {"x": 12.0, "z": -30.0}])
    ops[-1].params["mode"] = mode
    lines = generate_program_gcode(ops, settings)
    assert not any(line.startswith(("G71 ", "G72 ")) for line in lines)
    assert any(line.startswith("(Pass ") for line in lines) == (mode != "finish")
    cuts = [line for line in lines if line.startswith(("G1 ", "G2 ", "G3 "))]
    xs = [float(m[1]) for line in cuts if (m := re.search(r"\bX(-?[0-9.]+)", line))]
    assert xs and min(xs) > settings["xri"]
    if mode != "rough":
        assert any(line.startswith(("G2 ", "G3 ")) for line in lines)
    primitives = build_contour_variants(contour)["finish_primitives"]
    emitted = []
    _emit_finish_primitives(emitted, primitives, feed=.15)
    sub = contour_sub_from_primitives(primitives, 100)[1:-1]
    assert [re.sub(r" F[0-9.]+$", "", line) for line in emitted] == sub
    position = None
    arcs = 0
    for line in sub:
        words = {key: float(value) for key, value in re.findall(r"\b([XZIK])(-?[0-9.]+)", line)}
        endpoint = (words["X"] / 2, words["Z"])
        if line.startswith(("G2 ", "G3 ")):
            assert position is not None
            center = (position[0] + words["I"], position[1] + words["K"])
            assert math.dist(position, center) == pytest.approx(math.dist(endpoint, center), abs=.002)
            arcs += 1
        position = endpoint
    assert arcs
