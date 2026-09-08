import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from lathe_easystep.gcode_program import gcode_for_face
from lathe_easystep.model import OpType, Operation


def _face_op(**overrides):
    params = {
        "mode": 0,
        "tool": 1,
        "spindle": 2000.0,
        "feed": 0.1,
        "depth_max": 0.05,
        "start_z": 2.0,
        "end_z": 0.0,
        "start_x": 40.0,
        "end_x": 0.0,
        "finish_allow_z": 0.0,
        "retract": 1.0,
        "edge_type": "none",
        "edge_size": 0.0,
        "coolant": True,
    }
    params.update(overrides)
    return Operation(OpType.FACE, params)


def test_face_edge_type_string_id_none_does_not_crash():
    """Realer Bugreport: Planen mit Kantenform ueber die Combo (liefert die
    String-ID ueber currentData(), nicht mehr den alten numerischen Index)
    schlug fehl mit 'Invalid float for edge_type'."""
    lines = gcode_for_face(_face_op(edge_type="none"), {"xt": 150.0, "zt": 300.0, })
    assert any(l.startswith("G1 X40.000 Z0.000") for l in lines)


def test_face_edge_type_string_id_chamfer_produces_chamfer_geometry():
    lines = gcode_for_face(_face_op(edge_type="chamfer", edge_size=1.0), {"xt": 150.0, "zt": 300.0, })
    assert any("Z-1.000" in l for l in lines)
    assert any("X38.000" in l for l in lines)


def test_face_edge_type_legacy_numeric_chamfer_still_works():
    """Rueckwaertskompatibel: alte Programme/Tests mit numerischem edge_type=1
    muessen weiterhin funktionieren (siehe examples.py Referenzprogramm)."""
    lines = gcode_for_face(_face_op(edge_type=1, edge_size=1.0), {"xt": 150.0, "zt": 300.0, })
    assert any("Z-1.000" in l for l in lines)
    assert any("X38.000" in l for l in lines)


@pytest.mark.parametrize("edge_type", ["radius", 2])
@pytest.mark.parametrize("mode,rough,finish", [("rough", True, False), ("finish", False, True), ("rough_finish", True, True)])
def test_face_radius_preserves_circle_and_cycle_selection(edge_type, mode, rough, finish):
    from math import hypot
    import re
    from lathe_easystep.preview_geometry import build_face_path
    op = _face_op(edge_type=edge_type, edge_size=1.0, mode=mode)
    lines = gcode_for_face(op, {"xt": 150.0, "zt": 300.0})
    arc = next(line for line in lines if line.startswith("G2 "))
    words = {key: float(value) for key, value in re.findall(r"([XZIK])(-?[0-9.]+)", arc)}
    start = (40.0, -1.0)
    center = (start[0] / 2 + words["I"], start[1] + words["K"])
    assert words["I"] == -1.0
    assert hypot(start[0] / 2 - center[0], start[1] - center[1]) == pytest.approx(1.0)
    assert hypot(words["X"] / 2 - center[0], words["Z"] - center[1]) == pytest.approx(1.0)
    assert any(line.startswith("G72 ") for line in lines) == rough
    assert any(line.startswith("G70 ") for line in lines) == finish
    preview = build_face_path(op.params)
    for x, z in preview[1:]:
        assert hypot(x / 2 - center[0], z - center[1]) == pytest.approx(1.0)
    assert preview[-1] == start


@pytest.mark.parametrize("radius", [0.0, -1.0, 21.0, float("nan"), float("inf")])
def test_invalid_face_radius_is_rejected_by_preview_and_generator(radius):
    from lathe_easystep.preview_geometry import build_face_path
    op = _face_op(edge_type="radius", edge_size=radius)
    with pytest.raises(ValueError):
        gcode_for_face(op, {"xt": 150.0, "zt": 300.0})
    with pytest.raises(ValueError):
        build_face_path(op.params)


def test_face_edge_type_missing_raises_clear_error():
    op = _face_op()
    del op.params["edge_type"]
    with pytest.raises(ValueError, match="edge_type"):
        gcode_for_face(op, {"xt": 150.0, "zt": 300.0, })
