"""Tests for preview arc rendering and build_face_path geometry.

Validates that:
1. _sample_arc works correctly in radius-space (not diameter-space)
2. _sample_arc ccw inversion produces the correct visual fillet direction
3. build_face_path chamfer uses 2*edge_size in diameter X
4. build_face_path radius computes quarter-circle in radius-space
"""
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import build_contour_path, build_face_path


# ---------------------------------------------------------------------------
# Helper: minimal LathePreviewWidget._sample_arc extracted for testing
# ---------------------------------------------------------------------------
def _sample_arc_under_test(p1, p2, c, ccw, steps=48):
    """Reproduce the fixed _sample_arc logic for unit testing."""
    x1, z1 = p1[0] / 2.0, p1[1]
    x2, z2 = p2[0] / 2.0, p2[1]
    xc, zc = c[0] / 2.0, c[1]
    r1 = math.hypot(x1 - xc, z1 - zc)
    r2 = math.hypot(x2 - xc, z2 - zc)
    if r1 <= 1e-9 or abs(r1 - r2) > 1e-3:
        return [p1, p2]
    a1 = math.atan2(z1 - zc, x1 - xc)
    a2 = math.atan2(z2 - zc, x2 - xc)
    # Inverted convention: G-code ccw → preview CW sweep, and vice versa
    if not ccw:
        if a2 <= a1:
            a2 += 2 * math.pi
    else:
        if a2 >= a1:
            a2 -= 2 * math.pi
    pts = []
    for k in range(steps + 1):
        t = k / steps
        a = a1 + (a2 - a1) * t
        pts.append(((xc + r1 * math.cos(a)) * 2.0, zc + r1 * math.sin(a)))
    return pts


# ===========================================================================
# _sample_arc tests
# ===========================================================================

class TestSampleArcRadiusSpace:
    """_sample_arc must produce a true circular arc in physical (radius) space."""

    def test_arc_start_and_end_match_inputs(self):
        """Sampled arc must begin at p1 and end at p2."""
        # Use geometry from test_simple_radius_two_segments:
        # pt1_d=(20,0), pt2_d=(40,-10), center_d=(20,-10), ccw=True
        p1 = (20.0, 0.0)
        p2 = (40.0, -10.0)
        c = (20.0, -10.0)
        pts = _sample_arc_under_test(p1, p2, c, ccw=True, steps=48)
        assert len(pts) > 2, "Arc should have more than 2 points"
        # Start matches p1
        assert abs(pts[0][0] - p1[0]) < 0.01
        assert abs(pts[0][1] - p1[1]) < 0.01
        # End matches p2
        assert abs(pts[-1][0] - p2[0]) < 0.01
        assert abs(pts[-1][1] - p2[1]) < 0.01

    def test_arc_points_lie_on_circle_in_radius_space(self):
        """All sampled points must lie on a circle of constant radius
        when X coordinates are halved (converted to radius-space)."""
        p1 = (20.0, 0.0)
        p2 = (40.0, -10.0)
        c = (20.0, -10.0)
        pts = _sample_arc_under_test(p1, p2, c, ccw=True, steps=48)
        # Expected radius in radius-space: hypot(10-10, 0-(-10)) = 10
        expected_r = 10.0
        cx_r = c[0] / 2.0
        cz = c[1]
        for x_d, z in pts:
            x_r = x_d / 2.0
            r = math.hypot(x_r - cx_r, z - cz)
            assert abs(r - expected_r) < 0.01, (
                f"Point ({x_d}, {z}) → radius-space distance {r:.3f} != {expected_r}"
            )

    def test_arc_does_not_degenerate_to_straight_line(self):
        """With the radius-space fix, the arc must NOT fall back to a
        straight line (which happened when r1 != r2 in diameter-space)."""
        # This geometry has r1 != r2 in diameter-space but r1 == r2 in radius-space
        p1 = (20.0, 0.0)
        p2 = (40.0, -10.0)
        c = (20.0, -10.0)
        pts = _sample_arc_under_test(p1, p2, c, ccw=True, steps=48)
        # If degenerate, len would be 2 (just [p1, p2])
        assert len(pts) == 49, f"Expected 49 sample points, got {len(pts)}"


class TestSampleArcDirection:
    """The ccw inversion must produce the correct (short) fillet arc."""

    def test_fillet_arc_curves_through_correct_side(self):
        """For a contour corner going X+ then Z-, the fillet arc must
        curve through the upper-right quadrant (concave side), NOT
        through the lower-left (which would be the 270° wrong arc)."""
        # Geometry: start(0,0) → corner(40,0) → end(40,-30)
        # Fillet R=10 at corner → arc from (20,0) to (40,-10) around (20,-10)
        p1 = (20.0, 0.0)
        p2 = (40.0, -10.0)
        c = (20.0, -10.0)
        pts = _sample_arc_under_test(p1, p2, c, ccw=True, steps=48)

        # The correct fillet arc (90° short arc) curves through the
        # upper-right of the center.  All midpoints must have:
        #   x_r > center_x_r (= 10)  → x_d > 20
        #   z > center_z (= -10)
        cx_r = c[0] / 2.0  # 10
        cz = c[1]           # -10
        for x_d, z in pts[1:-1]:  # skip start/end (they're on the boundary)
            x_r = x_d / 2.0
            assert x_r >= cx_r - 0.01, (
                f"Arc point ({x_d}, {z}) is LEFT of center — wrong arc direction"
            )
            assert z >= cz - 0.01, (
                f"Arc point ({x_d}, {z}) is BELOW center — wrong arc direction"
            )

    def test_fillet_arc_sweep_is_short_90_degrees(self):
        """The sampled arc should sweep approximately 90°, not 270°."""
        p1 = (20.0, 0.0)
        p2 = (40.0, -10.0)
        c = (20.0, -10.0)
        pts = _sample_arc_under_test(p1, p2, c, ccw=True, steps=48)
        # Total arc length in radius-space ≈ r * π/2 ≈ 10 * 1.5708 ≈ 15.71
        total_len = 0.0
        for i in range(1, len(pts)):
            dx = pts[i][0] / 2.0 - pts[i-1][0] / 2.0
            dz = pts[i][1] - pts[i-1][1]
            total_len += math.hypot(dx, dz)
        expected_len = 10.0 * math.pi / 2.0  # ≈ 15.71
        assert abs(total_len - expected_len) < 0.5, (
            f"Arc length {total_len:.2f} != expected {expected_len:.2f} "
            f"(should be ~90° short arc, not 270°)"
        )


class TestSampleArcFromBuildContourPath:
    """End-to-end: build_contour_path → _sample_arc produces correct preview."""

    def test_contour_fillet_arc_preview_stays_within_bounds(self):
        """The preview arc from a built contour must stay within the
        bounding box of the two adjacent segments."""
        segments = [
            {"x": 40.0, "z": 0.0, "edge": "radius", "edge_size": 5.0},
            {"x": 40.0, "z": -30.0},
        ]
        prims = build_contour_path({"start_x": 0.0, "start_z": 0.0, "segments": segments})
        arcs = [p for p in prims if p.get("type") == "arc"]
        assert len(arcs) >= 1

        arc = arcs[0]
        pts = _sample_arc_under_test(
            arc["p1"], arc["p2"], arc["c"], arc["ccw"], steps=48
        )
        # All points should have X >= 0 (not go to negative diameter)
        # and Z >= -30 (not go below the end of the second segment)
        for x_d, z in pts:
            assert x_d >= -0.1, f"Arc point X={x_d} is negative (wrong sweep)"
            assert z >= -30.1, f"Arc point Z={z} below segment end"


# ===========================================================================
# build_face_path tests
# ===========================================================================

class TestBuildFacePathChamfer:
    """Chamfer in build_face_path must use 2*edge_size for diameter X."""

    def test_chamfer_consistent_with_slicer(self):
        """The chamfer start X must be x_outer - 2*edge_size (matching
        the G-code generator in slicer.py)."""
        params = {
            "outer_diameter": 50.0,
            "inner_diameter": 0.0,
            "start_z": 2.0,
            "end_z": 0.0,
            "edge_type": 1,
            "edge_size": 2.0,
        }
        path = build_face_path(params)
        # Last two points should be the chamfer:
        # (x_outer - 2*edge_size, z_end) = (46.0, 0.0)
        # (x_outer, z_end - edge_size)    = (50.0, -2.0)
        chamfer_start = path[-2]
        chamfer_end = path[-1]
        assert abs(chamfer_start[0] - 46.0) < 0.01, (
            f"Chamfer start X should be 46.0 (50-2*2), got {chamfer_start[0]}"
        )
        assert abs(chamfer_start[1] - 0.0) < 0.01
        assert abs(chamfer_end[0] - 50.0) < 0.01
        assert abs(chamfer_end[1] - (-2.0)) < 0.01

    def test_chamfer_is_physical_45_degrees(self):
        """The chamfer angle must be 45° in physical (radius) space."""
        params = {
            "outer_diameter": 50.0,
            "inner_diameter": 0.0,
            "start_z": 2.0,
            "end_z": 0.0,
            "edge_type": 1,
            "edge_size": 3.0,
        }
        path = build_face_path(params)
        chamfer_start = path[-2]
        chamfer_end = path[-1]
        # Physical change: radial = (end_x - start_x)/2, axial = (end_z - start_z)
        dx_physical = (chamfer_end[0] - chamfer_start[0]) / 2.0  # diameter → radius
        dz_physical = abs(chamfer_end[1] - chamfer_start[1])
        assert abs(dx_physical - dz_physical) < 0.01, (
            f"Chamfer should be 45°: radial={dx_physical}, axial={dz_physical}"
        )


class TestBuildFacePathRadius:
    """Quarter-circle radius in build_face_path must be computed in radius-space."""

    def test_radius_start_and_end_correct(self):
        """Radius arc must start at (x_outer-2*edge, z_end) and end near
        (x_outer, z_end-edge)."""
        params = {
            "outer_diameter": 50.0,
            "inner_diameter": 0.0,
            "start_z": 2.0,
            "end_z": 0.0,
            "edge_type": 2,
            "edge_size": 3.0,
        }
        path = build_face_path(params)
        # First radius point after the face start: tangent start on face plane
        radius_start = path[1]
        radius_end = path[-1]
        # Tangent start: x_outer_r - edge = 25 - 3 = 22 → diameter = 44
        assert abs(radius_start[0] - 44.0) < 0.01, (
            f"Radius start X should be 44.0 (diameter), got {radius_start[0]}"
        )
        assert abs(radius_start[1] - 0.0) < 0.01
        # Tangent end: (x_outer, z_end - edge) = (50, -3)
        assert abs(radius_end[0] - 50.0) < 0.1, (
            f"Radius end X should be ~50.0, got {radius_end[0]}"
        )
        assert abs(radius_end[1] - (-3.0)) < 0.1

    def test_radius_points_lie_on_circle_in_radius_space(self):
        """All radius points must lie on a circle of the specified radius
        when X is converted to radius-space."""
        edge = 5.0
        params = {
            "outer_diameter": 40.0,
            "inner_diameter": 0.0,
            "start_z": 2.0,
            "end_z": 0.0,
            "edge_type": 2,
            "edge_size": edge,
        }
        path = build_face_path(params)
        # Radius points start at index 1 (after the face start point)
        radius_pts = path[1:]  # includes tangent start + arc samples
        # Center in radius-space: (x_outer_r - edge, z_end - edge) = (20-5, 0-5) = (15, -5)
        cx_r = 40.0 / 2.0 - edge  # 15
        cz = 0.0 - edge            # -5
        for x_d, z in radius_pts:
            x_r = x_d / 2.0
            r = math.hypot(x_r - cx_r, z - cz)
            assert abs(r - edge) < 0.05, (
                f"Point ({x_d}, {z}) → radius-space distance {r:.3f} != {edge}"
            )
