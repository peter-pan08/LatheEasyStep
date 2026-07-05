"""Tests for drill G-code generation – all modes and collision-free approach/retract.

Validates that:
1. Mode index mapping works correctly (0→G81, 1→G82, 2→G83, 3→G73, 4→G84)
2. Mode-specific parameters (dwell, peck_depth) are emitted
3. G17 is set before cycle and G18 restored after
4. Approach is collision-free (Z first, then X to centerline)
5. Retract to safe_z after G80
6. Coolant is emitted only once
7. build_drill_path produces correct preview geometry
"""
import re
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import build_drill_path
from slicer import gcode_for_drill, Operation, OpType, DRILL_MODE_MAP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_drill_op(mode=0, **overrides):
    """Create a minimal DRILL operation for testing.

    mode: combo index (0=G81, 1=G82, 2=G83, 3=G73, 4=G84)
    """
    params = {
        "tool": 5,
        "spindle": 500,
        "mode": float(mode),
        "diameter": 8.0,
        "depth": -20.0,
        "feed": 0.12,
        "safe_z": 2.0,
    }
    params.update(overrides)
    path = build_drill_path(params)
    return Operation(OpType.DRILL, params, path=path)


def _get_cycle_line(lines):
    """Return the canned cycle line (G81/G82/G83/G73/G84)."""
    for line in lines:
        if re.match(r"G8[1234]|G73", line):
            return line
    return None


# ---------------------------------------------------------------------------
# Mode index → G-code mapping
# ---------------------------------------------------------------------------

class TestDrillModeMap:
    """DRILL_MODE_MAP must cover all 5 combo indices."""

    def test_map_has_five_entries(self):
        assert len(DRILL_MODE_MAP) == 5

    def test_index_0_is_G81(self):
        assert DRILL_MODE_MAP[0] == "G81"

    def test_index_1_is_G82(self):
        assert DRILL_MODE_MAP[1] == "G82"

    def test_index_2_is_G83(self):
        assert DRILL_MODE_MAP[2] == "G83"

    def test_index_3_is_G73(self):
        assert DRILL_MODE_MAP[3] == "G73"

    def test_index_4_is_G84(self):
        assert DRILL_MODE_MAP[4] == "G84"


# ---------------------------------------------------------------------------
# G81 – Normal drilling
# ---------------------------------------------------------------------------

class TestDrillG81:
    """G81 standard drilling cycle."""

    def test_g81_emitted_for_mode_0(self):
        op = _make_drill_op(mode=0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None, f"No cycle line found in: {lines}"
        assert cycle_line.startswith("G81")

    def test_g81_contains_x_z_r_f(self):
        op = _make_drill_op(mode=0, depth=-20.0, safe_z=2.0, feed=0.12)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert "X0.000" in cycle_line
        assert "Z-20.000" in cycle_line
        assert "R2.000" in cycle_line
        assert "F0.120" in cycle_line

    def test_g81_is_default_for_unknown_mode(self):
        """Unknown mode index should fallback to G81."""
        op = _make_drill_op(mode=99)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None
        assert cycle_line.startswith("G81")

    def test_g81_for_string_mode(self):
        """Mode passed as string 'G81' should also work."""
        op = _make_drill_op()
        op.params["mode"] = "G81"
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line.startswith("G81")


# ---------------------------------------------------------------------------
# G82 – Drilling with dwell
# ---------------------------------------------------------------------------

class TestDrillG82:
    """G82 drilling with dwell."""

    def test_g82_emitted_for_mode_1(self):
        op = _make_drill_op(mode=1, dwell=1.5)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None
        assert cycle_line.startswith("G82")

    def test_g82_contains_dwell_parameter(self):
        op = _make_drill_op(mode=1, dwell=2.0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert "P2.000" in cycle_line


# ---------------------------------------------------------------------------
# G83 – Peck drilling (full retract)
# ---------------------------------------------------------------------------

class TestDrillG83:
    """G83 peck drilling."""

    def test_g83_emitted_for_mode_2(self):
        op = _make_drill_op(mode=2, peck_depth=3.0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None
        assert cycle_line.startswith("G83")

    def test_g83_contains_peck_depth(self):
        op = _make_drill_op(mode=2, peck_depth=5.0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert "Q5.000" in cycle_line


# ---------------------------------------------------------------------------
# G73 – Chip breaking drilling (partial retract)
# ---------------------------------------------------------------------------

class TestDrillG73:
    """G73 chip breaking drilling."""

    def test_g73_emitted_for_mode_3(self):
        op = _make_drill_op(mode=3, peck_depth=2.0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None
        assert cycle_line.startswith("G73")

    def test_g73_contains_peck_depth(self):
        op = _make_drill_op(mode=3, peck_depth=4.0)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert "Q4.000" in cycle_line


# ---------------------------------------------------------------------------
# G84 – Tapping
# ---------------------------------------------------------------------------

class TestDrillG84:
    """G84 tapping cycle."""

    def test_g84_emitted_for_mode_4(self):
        op = _make_drill_op(mode=4)
        lines = gcode_for_drill(op)
        cycle_line = _get_cycle_line(lines)
        assert cycle_line is not None
        assert cycle_line.startswith("G84")


# ---------------------------------------------------------------------------
# Plane switching (G17/G18)
# ---------------------------------------------------------------------------

class TestDrillPlaneSwitch:
    """Canned cycles require G17 for Z-axis plunge, then restore G18."""

    def test_g17_before_cycle(self):
        op = _make_drill_op(mode=0)
        lines = gcode_for_drill(op)
        g17_idx = None
        cycle_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "G17":
                g17_idx = i
            if re.match(r"G8[1234]|G73", line):
                cycle_idx = i
        assert g17_idx is not None, "G17 not found"
        assert cycle_idx is not None, "Cycle not found"
        assert g17_idx < cycle_idx, "G17 must come before the canned cycle"

    def test_g18_after_g80(self):
        op = _make_drill_op(mode=0)
        lines = gcode_for_drill(op)
        g80_idx = None
        g18_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "G80":
                g80_idx = i
            if line.strip() == "G18":
                g18_idx = i
        assert g80_idx is not None, "G80 not found"
        assert g18_idx is not None, "G18 not found"
        assert g18_idx > g80_idx, "G18 must come after G80 (cycle cancel)"


# ---------------------------------------------------------------------------
# Collision-free approach and retract
# ---------------------------------------------------------------------------

class TestDrillApproachRetract:
    """Approach and retract must be collision-free."""

    def test_approach_x_is_centerline(self):
        """Drill must approach on X=0 (centerline)."""
        op = _make_drill_op(mode=0)
        lines = gcode_for_drill(op)
        # Find G0 moves before the cycle
        cycle_idx = next(i for i, l in enumerate(lines) if re.match(r"G8[1234]|G73", l))
        approach_g0 = [l for l in lines[:cycle_idx] if l.startswith("G0") and "X" in l]
        assert len(approach_g0) >= 1
        # Last approach move should have X=0
        last = approach_g0[-1]
        x_match = re.search(r"X([+-]?\d+\.?\d*)", last)
        assert x_match
        assert abs(float(x_match.group(1))) < 0.01, f"Approach X must be 0 (centerline), got {x_match.group(1)}"

    def test_approach_z_is_safe(self):
        """Approach must go to safe_z before drilling."""
        op = _make_drill_op(mode=0, safe_z=5.0)
        lines = gcode_for_drill(op)
        cycle_idx = next(i for i, l in enumerate(lines) if re.match(r"G8[1234]|G73", l))
        approach_g0 = [l for l in lines[:cycle_idx] if l.startswith("G0") and "Z" in l]
        assert len(approach_g0) >= 1
        # All approach Z moves should be >= safe_z (not into material)
        for line in approach_g0:
            z_match = re.search(r"Z([+-]?\d+\.?\d*)", line)
            if z_match:
                z_val = float(z_match.group(1))
                assert z_val >= 5.0 - 0.01, f"Approach Z={z_val} is below safe_z=5.0"

    def test_retract_to_safe_z_after_g80(self):
        """After G80, tool must retract to safe_z before G18 restore."""
        op = _make_drill_op(mode=0, safe_z=3.0)
        lines = gcode_for_drill(op)
        g80_idx = next(i for i, l in enumerate(lines) if l.strip() == "G80")
        g18_idx = next(i for i, l in enumerate(lines) if l.strip() == "G18")
        # Between G80 and G18 there should be a G0 Z retract
        between = lines[g80_idx + 1:g18_idx]
        retract_lines = [l for l in between if l.startswith("G0") and "Z" in l]
        assert len(retract_lines) >= 1, "No retract G0 Z between G80 and G18"
        z_match = re.search(r"Z([+-]?\d+\.?\d*)", retract_lines[0])
        assert z_match
        assert abs(float(z_match.group(1)) - 3.0) < 0.01


# ---------------------------------------------------------------------------
# Coolant (no duplicates)
# ---------------------------------------------------------------------------

class TestDrillCoolant:
    """Coolant should be emitted once, not duplicated."""

    def test_coolant_not_duplicated(self):
        op = _make_drill_op(mode=0, coolant=1.0)
        lines = gcode_for_drill(op)
        m8_count = sum(1 for l in lines if l.strip() in ("M8", "M7"))
        assert m8_count <= 1, f"Coolant command emitted {m8_count} times (expected 0 or 1)"


# ---------------------------------------------------------------------------
# build_drill_path – preview geometry
# ---------------------------------------------------------------------------

class TestBuildDrillPath:
    """Preview path for drill operations."""

    def test_starts_at_surface_centerline(self):
        path = build_drill_path({"diameter": 8.0, "depth": -20.0, "safe_z": 2.0})
        assert path[0] == (0.0, 0.0)

    def test_ends_at_drill_depth(self):
        path = build_drill_path({"diameter": 8.0, "depth": -20.0, "safe_z": 2.0})
        assert path[-1][1] == -20.0

    def test_tip_apex_at_center(self):
        """Drill point apex is at X=0 (centerline)."""
        path = build_drill_path({"diameter": 8.0, "depth": -20.0, "safe_z": 2.0})
        assert path[-1][0] == 0.0

    def test_diameter_shown_in_path(self):
        """Path should include the drill diameter at the wall."""
        path = build_drill_path({"diameter": 10.0, "depth": -30.0, "safe_z": 2.0})
        x_values = [p[0] for p in path]
        assert 10.0 in x_values, f"Diameter 10.0 not found in path X values: {x_values}"

    def test_positive_depth_converted_negative(self):
        """Positive depth is interpreted as 'into material' (negative Z)."""
        path = build_drill_path({"diameter": 8.0, "depth": 20.0, "safe_z": 2.0})
        assert path[-1][1] < 0

    def test_118_degree_point_geometry(self):
        """118° drill point = 59° half-angle; cone length = radius / tan(59°)."""
        diameter = 10.0
        depth = -30.0
        path = build_drill_path({"diameter": diameter, "depth": depth, "safe_z": 2.0})
        expected_tip_len = (diameter / 2) / math.tan(math.radians(59))
        # cone_start_z = depth + tip_len
        cone_start_z = depth + expected_tip_len
        # Find the cylindrical wall endpoint
        wall_point = None
        for p in path:
            if abs(p[0] - diameter) < 0.01 and p[1] < 0:
                wall_point = p
        assert wall_point is not None, "Cylindrical wall point not found"
        assert abs(wall_point[1] - cone_start_z) < 0.01, (
            f"Cone start Z should be ~{cone_start_z:.3f}, got {wall_point[1]:.3f}"
        )

    def test_zero_diameter_centerline_only(self):
        """With zero diameter, path is just centerline moves."""
        path = build_drill_path({"diameter": 0.0, "depth": -10.0, "safe_z": 2.0})
        assert len(path) == 2
        for p in path:
            assert p[0] == 0.0
