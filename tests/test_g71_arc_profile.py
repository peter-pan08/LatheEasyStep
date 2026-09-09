"""Test that G71 cycle subroutine correctly uses G2/G3 for arcs (fillets)."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType, build_contour_path


def test_g71_profile_contains_arc_for_fillet():
    """A contour with a radius fillet must produce G2/G3 in the G71 sub, not just G1."""
    # Build contour with radius at corner between X-move and Z-move
    # Segments: Start(0,0) -> (20,0) with R=10 -> (20,-20) -> (30,-20) -> (30,-30) -> (40,-30)
    segments = [
        {"x": 20.0, "z": 0.0, "edge": "radius", "edge_size": 10.0},
        {"x": 20.0, "z": -20.0},
        {"x": 30.0, "z": -20.0},
        {"x": 30.0, "z": -30.0},
        {"x": 40.0, "z": -30.0},
    ]
    primitives = build_contour_path({"start_x": 0.0, "start_z": 0.0, "segments": segments})

    # Verify primitives contain an arc
    arc_prims = [p for p in primitives if p.get("type") == "arc"]
    assert len(arc_prims) >= 1, f"Expected arc primitives, got: {primitives}"

    # Now create a program that uses this contour with ABSPANEN parallel_z
    m = ProgramModel()
    contour_op = Operation(OpType.CONTOUR, {"name": "test_contour"}, path=primitives)
    abspanen_op = Operation(
        OpType.ABSPANEN,
        {
            "mode": 0,
            "slice_strategy": "parallel_z",
            "depth_per_pass": 1.0,
            "feed": 0.2,
            "spindle": 1000.0,
            "tool": 1,
            "contour_name": "test_contour",
        },
        path=[],  # will be resolved from contour
    )
    m.operations = [contour_op, abspanen_op]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xa": 40.0, "xra": 50.0, "zra": 5.0}
    gcode = "\n".join(m.generate_gcode())

    # G71 cycle should be present (monotonic Z decreasing, monotonic X increasing)
    assert "G71 Q" in gcode, f"Expected G71 cycle in output:\n{gcode}"

    # The profile subroutine must contain G2 or G3 for the arc
    assert "G2 " in gcode or "G3 " in gcode, f"Expected G2/G3 arc in profile sub:\n{gcode}"

    # NO G0 in profile sub (only G1/G2/G3 allowed)
    # Find the sub block
    sub_start = gcode.find("o100 sub")
    if sub_start < 0:
        sub_start = gcode.find("o101 sub")
    assert sub_start >= 0, f"Sub block not found in:\n{gcode}"
    sub_end = gcode.find("endsub", sub_start)
    sub_block = gcode[sub_start:sub_end]
    assert "G0 " not in sub_block, f"G0 found in profile sub (not allowed for G71):\n{sub_block}"


def test_fillet_arc_ccw_for_g18_xz_plane():
    """Fillet arcs must use G3 (CCW) for corners where X increases then Z
    decreases.  LinuxCNC G18 defines CW/CCW looking from +Y; the cross
    product in (X,Z) coords is inverted compared to the (Z,X) plane.
    """
    segments = [
        {"x": 20.0, "z": 0.0, "edge": "radius", "edge_size": 10.0},
        {"x": 20.0, "z": -20.0},
        {"x": 30.0, "z": -20.0},
        {"x": 30.0, "z": -30.0},
        {"x": 40.0, "z": -30.0},
    ]
    prims = build_contour_path({"start_x": 0.0, "start_z": 0.0, "segments": segments})
    arcs = [p for p in prims if p.get("type") == "arc"]
    assert len(arcs) >= 1, f"No arc found: {prims}"
    for arc in arcs:
        assert arc["ccw"] is True, (
            f"Arc must be CCW (G3) for G18 XZ-plane: {arc}"
        )


def test_fillet_arc_passes_linuxcnc_monotonicity():
    """Verify that the fillet arc passes LinuxCNC's interp_g7x.cc
    round_segment::monotonic() check (reproduced from source).
    """
    segments = [
        {"x": 20.0, "z": 0.0, "edge": "radius", "edge_size": 10.0},
        {"x": 20.0, "z": -20.0},
        {"x": 30.0, "z": -20.0},
        {"x": 30.0, "z": -30.0},
        {"x": 40.0, "z": -30.0},
    ]
    prims = build_contour_path({"start_x": 0.0, "start_z": 0.0, "segments": segments})
    for arc in (p for p in prims if p.get("type") == "arc"):
        # G7 halves X and I values; simulate LinuxCNC complex(z, x)
        x1, z1 = arc["p1"][0] / 2.0, arc["p1"][1]
        x2, z2 = arc["p2"][0] / 2.0, arc["p2"][1]
        xc, zc = arc["c"][0] / 2.0, arc["c"][1]
        entry = x1 - xc
        exit_ = x2 - xc
        dz = z2 - z1
        ccw = arc["ccw"]
        if ccw:
            ok = entry >= -1e-3 and exit_ >= -1e-3 and dz <= -1e-3
        else:
            ok = entry <= 1e-3 and exit_ <= 1e-3 and dz <= -1e-3
        assert ok, (
            f"Arc fails LinuxCNC monotonic() check: "
            f"ccw={ccw} entry={entry} exit={exit_} dz={dz}"
        )


def test_simple_radius_two_segments():
    """Minimal test: 2 segments with radius → arc in output.

    Fillet geometry is computed in RADIUS (physical) space.
    Use geometry where R=10 fits comfortably: horizontal segment
    from X=0 (r=0) to X=40 (r=20) → l1_phys = 20mm > t=10.
    """
    # Start X0 Z0, segment to (40,0) with R10, then (40,-30)
    segments = [
        {"x": 40.0, "z": 0.0, "edge": "radius", "edge_size": 10.0},
        {"x": 40.0, "z": -30.0},
    ]
    primitives = build_contour_path({"start_x": 0.0, "start_z": 0.0, "segments": segments})

    types = [p["type"] for p in primitives]
    assert "arc" in types, f"Expected arc primitive, got types: {types}"

    # Verify arc geometry (all values in diameter coordinates)
    arc = next(p for p in primitives if p["type"] == "arc")
    # In radius space: corner at (20,0), R=10, t=10
    # pt1_r = (10, 0), pt2_r = (20, -10), center_r = (10, -10)
    # → diameter: P1=(20, 0), P2=(40, -10), C=(20, -10)
    assert abs(arc["p1"][0] - 20.0) < 0.1, f"Arc P1 X unexpected: {arc['p1']}"
    assert abs(arc["p1"][1] - 0.0) < 0.1, f"Arc P1 Z unexpected: {arc['p1']}"
    assert abs(arc["p2"][0] - 40.0) < 0.1, f"Arc P2 X unexpected: {arc['p2']}"
    assert abs(arc["p2"][1] - (-10.0)) < 0.1, f"Arc P2 Z unexpected: {arc['p2']}"
    # Center in diameter
    assert abs(arc["c"][0] - 20.0) < 0.1, f"Arc C X unexpected: {arc['c']}"
    assert abs(arc["c"][1] - (-10.0)) < 0.1, f"Arc C Z unexpected: {arc['c']}"
    # Direction must be CCW (G3) for G18 XZ plane
    assert arc["ccw"] is True, f"Arc must be CCW for G18 XZ-plane: ccw={arc['ccw']}"


def test_g71_monotonic_increasing_x_allowed():
    """G71 must work with monotonically increasing X (external turning from small to large Ø)."""
    m = ProgramModel()
    # Simple increasing X profile, decreasing Z
    path = [(10.0, 0.0), (20.0, -10.0), (30.0, -20.0), (40.0, -30.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {"mode": 0, "slice_strategy": "parallel_z", "depth_per_pass": 1.0, "feed": 0.2, "spindle": 1000.0, "tool": 1},
            path=path,
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xa": 40.0, "xra": 50.0, "zra": 5.0}
    gcode = "\n".join(m.generate_gcode())
    assert "G71 Q" in gcode, f"G71 should be used for monotonic increasing X:\n{gcode}"
    assert "Move-based" not in gcode
