import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.contour_logic import build_contour_path
from lathe_easystep.gcode_roughing import _emit_finish_primitives


def _gcode_from_primitives(prims, *, feed):
    lines = []
    _emit_finish_primitives(lines, prims, feed=feed)
    return lines


def test_arc_primitive_outputs_valid_G2_G3():
    # simple L-shape with a radius corner of 10mm
    params = {
        "start_x": 5.0,
        "start_z": 0.0,
        "segments": [
            {"x": 5.0, "z": -10.0, "edge": "radius", "edge_size": 10.0, "arc_side": "auto"},
            {"x": 10.0, "z": -10.0, "edge": "none", "edge_size": 0.0, "arc_side": "auto"},
        ],
    }
    prims = build_contour_path(params)
    # verify we got one arc primitive with a nonzero center
    arcs = [p for p in prims if p.get("type") == "arc"]
    assert len(arcs) == 1
    arc = arcs[0]
    assert "c" in arc or "center" in arc
    # generate gcode and inspect I/K values
    gcode = _gcode_from_primitives(prims, feed=100)
    # should contain a G2 or G3 line with nonzero I/K
    arc_lines = [l for l in gcode if l.startswith("G2") or l.startswith("G3")]
    assert len(arc_lines) == 1
    line = arc_lines[0]
    assert "I0" not in line or "K0" not in line

    # additionally, the gcode endpoint should match the primitive's p2 coordinate,
    # not collapse to the start point (which previously produced degenerate arcs).
    # our primitive p2 was roughly (9.995,-10.0), so ensure the gcode contains X9.995 or
    # Z-10.000 rather than X5.000 Z0.000.
    assert "X9.995" in line or "Z-10.000" in line


def test_arc_geometry_from_error_case():
    # reproduce geometry that earlier produced a LinuxCNC radius mismatch error
    params = {
        "start_x": 5.0,
        "start_z": 0.0,
        "segments": [
            {"x": 5.0, "z": -10.0, "edge": "radius", "edge_size": 10.0, "arc_side": "auto"},
            {"x": 10.0, "z": -10.0, "edge": "none", "edge_size": 0.0, "arc_side": "auto"},
        ],
    }
    prims = build_contour_path(params)
    gcode = _gcode_from_primitives(prims, feed=100)
    # the arc line should not be degenerate (start != end)
    arc_lines = [l for l in gcode if l.startswith("G2") or l.startswith("G3")]
    assert len(arc_lines) == 1
    line = arc_lines[0]
    # ensure end coordinates differ from start
    assert "X5.000 Z0.000" not in line
