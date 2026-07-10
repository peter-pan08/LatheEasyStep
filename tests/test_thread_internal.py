"""Tests for G76 threading – external vs. internal.

Validates that:
1. External threading: I < 0 (boring=0), approach at G76 driveline outside major diameter
2. Internal threading: I > 0 (boring=1), approach at G76 driveline inside minor diameter
3. Preview contour: single zig-zag line, no pass sequence
"""
import re
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import build_thread_path
from slicer import gcode_for_thread, Operation, OpType
from lathe_easystep.model import ProgramModel


def _make_thread_op(orientation=0, **overrides):
    """Create a minimal THREAD operation for testing."""
    params = {
        "tool": 8,
        "spindle": 800,
        "major_diameter": 10.0,
        "pitch": 1.5,
        "length": 20.0,
        "safe_z": 2.0,
        "orientation": orientation,
    }
    params.update(overrides)
    return Operation(OpType.THREAD, params, path=[])


def _thread_settings(**overrides):
    settings = {"xi": 0.0, "xri": 7.0, "xri_absolute": True, "zri": 4.0, "zri_absolute": True}
    settings.update(overrides)
    return settings


# ---------------------------------------------------------------------------
# G-code generation tests
# ---------------------------------------------------------------------------

class TestExternalThreadGCode:
    """External threading (orientation=0): standard behavior."""

    def test_peak_offset_I_is_negative(self):
        """I must be negative for external threading (boring=0 in LinuxCNC)."""
        op = _make_thread_op(orientation=0)
        lines = gcode_for_thread(op, _thread_settings())
        g76_line = [l for l in lines if l.startswith("G76")][0]
        i_match = re.search(r"I([+-]?\d+\.?\d*)", g76_line)
        assert i_match, f"No I parameter in G76 line: {g76_line}"
        i_val = float(i_match.group(1))
        assert i_val < 0, f"I must be negative for external thread, got I={i_val}"

    def test_approach_at_diam_mode_g76_driveline(self):
        """In G7 diameter mode, the approach X must be the G76 driveline Xi.

        LinuxCNC's g76diam helper uses:
            xi = major_diameter - I
        with negative I for external threads, which places Xi slightly outside
        the major diameter.
        """
        op = _make_thread_op(orientation=0, major_diameter=25.0)
        lines = gcode_for_thread(op, _thread_settings())
        # Find the last G0 before G76 — that's the approach move
        approach_lines = [l for l in lines if l.startswith("G0") and "X" in l]
        assert len(approach_lines) >= 1
        last_approach = approach_lines[-1]
        x_match = re.search(r"X([+-]?\d+\.?\d*)", last_approach)
        assert x_match
        x_val = float(x_match.group(1))
        expected_drive = 25.0 - (-0.0900)
        assert abs(x_val - expected_drive) < 0.01, (
            f"External approach X should be {expected_drive:.3f} (G76 driveline), got {x_val}"
        )

    def test_comment_says_aussen(self):
        op = _make_thread_op(orientation=0)
        lines = gcode_for_thread(op, _thread_settings())
        assert any("Aussen" in l for l in lines)

    def test_right_hand_thread_runs_towards_negative_z_from_start_z(self):
        op = _make_thread_op(orientation=0, hand=0, thread_start_z=-2.0, length=18.0, safe_z=3.0)
        lines = gcode_for_thread(op, _thread_settings())
        assert "G0 Z-2.000" in lines
        g76_line = [l for l in lines if l.startswith("G76")][0]
        assert "Z-20.000" in g76_line


class TestInternalThreadGCode:
    """Internal threading (orientation=1): boring bar cuts outward."""

    def test_peak_offset_I_is_positive(self):
        """I must be positive for internal threading (boring=1 in LinuxCNC).

        From interp_convert.cc:
            boring = (i_number > 0);
        When boring=1, each threading pass moves OUTWARD (+X).
        """
        op = _make_thread_op(orientation=1)
        lines = gcode_for_thread(op, _thread_settings())
        g76_line = [l for l in lines if l.startswith("G76")][0]
        i_match = re.search(r"I([+-]?\d+\.?\d*)", g76_line)
        assert i_match, f"No I parameter in G76 line: {g76_line}"
        i_val = float(i_match.group(1))
        assert i_val > 0, (
            f"I must be positive for internal thread (boring=1), got I={i_val}"
        )

    def test_approach_at_diam_mode_g76_driveline(self):
        """In G7 diameter mode, internal threading approaches at Xi = minor - I.

        LinuxCNC's g76diam helper uses positive I for internal threads, which
        places the driveline slightly inside the minor diameter.
        """
        op = _make_thread_op(orientation=1, major_diameter=10.0, pitch=1.5)
        lines = gcode_for_thread(op, _thread_settings())
        approach_lines = [l for l in lines if l.startswith("G0") and "X" in l]
        assert len(approach_lines) >= 1
        last_approach = approach_lines[-1]
        x_match = re.search(r"X([+-]?\d+\.?\d*)", last_approach)
        assert x_match
        x_val = float(x_match.group(1))
        thread_depth = 1.5 * 0.6134
        minor_dia = 10.0 - 2.0 * thread_depth
        expected_drive = minor_dia - 0.0900
        assert abs(x_val - expected_drive) < 0.01, (
            f"Internal approach X should be {expected_drive:.3f} (G76 driveline), "
            f"got {x_val:.3f}"
        )

    def test_comment_says_innen(self):
        op = _make_thread_op(orientation=1)
        lines = gcode_for_thread(op, _thread_settings())
        assert any("Innen" in l for l in lines)

    def test_left_hand_thread_runs_towards_positive_z_from_start_z(self):
        op = _make_thread_op(orientation=1, hand=1, thread_start_z=-30.0, length=30.0, safe_z=2.0)
        lines = gcode_for_thread(op, _thread_settings())
        assert "G0 Z-30.000" in lines
        g76_line = [l for l in lines if l.startswith("G76")][0]
        assert "Z0.000" in g76_line
        assert any("Linksgewinde" in l for l in lines)

    def test_K_is_always_positive(self):
        """K (thread depth) is always positive for both internal and external.
        The direction is controlled by the sign of I, not K."""
        for orient in (0, 1):
            op = _make_thread_op(orientation=orient)
            lines = gcode_for_thread(op, _thread_settings())
            g76_line = [l for l in lines if l.startswith("G76")][0]
            k_match = re.search(r"K([+-]?\d+\.?\d*)", g76_line)
            assert k_match
            k_val = float(k_match.group(1))
            assert k_val > 0, f"K must be positive, got {k_val} for orientation={orient}"
            expected_k = 2.0 * (1.5 * 0.6134)
            assert abs(k_val - expected_k) < 0.01, (
                f"K should be full diameter thread depth {expected_k:.4f} in G7, got {k_val:.4f}"
            )

    def test_J_is_always_positive(self):
        """J (first depth) must be > 0 and uses G7 diameter semantics."""
        for orient in (0, 1):
            op = _make_thread_op(orientation=orient)
            lines = gcode_for_thread(op, _thread_settings())
            g76_line = [l for l in lines if l.startswith("G76")][0]
            j_match = re.search(r"J([+-]?\d+\.?\d*)", g76_line)
            assert j_match
            j_val = float(j_match.group(1))
            assert j_val > 0, f"J must be positive, got {j_val} for orientation={orient}"
            expected_j = 2.0 * max((1.5 * 0.6134) * 0.1, 1.5 * 0.05)
            assert abs(j_val - expected_j) < 0.01, (
                f"J should be diameter-mode initial cut depth {expected_j:.4f}, got {j_val:.4f}"
            )

    def test_K_greater_than_J(self):
        """LinuxCNC requires K > J, per error check in interp_convert.cc."""
        for orient in (0, 1):
            op = _make_thread_op(orientation=orient)
            lines = gcode_for_thread(op, _thread_settings())
            g76_line = [l for l in lines if l.startswith("G76")][0]
            k_match = re.search(r"K([+-]?\d+\.?\d*)", g76_line)
            j_match = re.search(r"J([+-]?\d+\.?\d*)", g76_line)
            assert k_match and j_match
            k_val = float(k_match.group(1))
            j_val = float(j_match.group(1))
            assert k_val > j_val, (
                f"K ({k_val}) must be > J ({j_val}) for orientation={orient}"
            )

    def test_internal_thread_approach_uses_xri_and_zri_safe_position(self):
        m = ProgramModel()
        m.operations = [_make_thread_op(orientation=1, thread_start_z=-6.0, safe_z=3.0)]
        m.program_settings = _thread_settings()
        lines = m.generate_gcode()
        assert "G0 Z4.000" in lines
        assert "G0 X7.000" in lines
        assert "G0 X8.068 Z3.000" in lines

    def test_internal_thread_rejects_unplausible_xri(self):
        m = ProgramModel()
        m.operations = [_make_thread_op(orientation=1)]
        m.program_settings = _thread_settings(xri=9.0)
        with pytest.raises(ValueError, match="XRI=.*unplausibel"):
            m.generate_gcode()


# ---------------------------------------------------------------------------
# Preview path tests
# ---------------------------------------------------------------------------

class TestExternalThreadPreview:
    """External thread preview: show a single zig-zag contour."""

    def test_contour_spans_major_to_minor(self):
        params = {
            "major_diameter": 20.0,
            "pitch": 2.0,
            "length": 30.0,
            "passes": 3,
            "safe_z": 2.0,
            "orientation": 0,
        }
        path = build_thread_path(params)
        thread_depth = 2.0 * 0.6134
        minor_dia = 20.0 - 2.0 * thread_depth
        assert path[0] == (20.0, 0.0)
        assert abs(path[-1][1] - (-30.0)) < 0.01
        x_values = [p[0] for p in path]
        assert min(x_values) >= minor_dia - 0.01
        assert max(x_values) <= 20.0 + 0.01
        assert any(abs(x - minor_dia) < 0.01 for x in x_values)
        assert any(abs(x - 20.0) < 0.01 for x in x_values)

    def test_left_hand_preview_runs_towards_positive_z(self):
        params = {
            "major_diameter": 20.0,
            "pitch": 2.0,
            "length": 10.0,
            "thread_start_z": -10.0,
            "hand": 1,
            "orientation": 0,
        }
        path = build_thread_path(params)
        assert path[0] == (20.0, -10.0)
        assert path[-1][1] >= 0.0 - 0.01


class TestInternalThreadPreview:
    """Internal thread preview: show a single zig-zag contour."""

    def test_starts_at_bore_surface(self):
        params = {
            "major_diameter": 20.0,
            "pitch": 2.0,
            "length": 30.0,
            "passes": 3,
            "safe_z": 2.0,
            "orientation": 1,
        }
        path = build_thread_path(params)
        # Bore surface = major - 2*thread_depth
        thread_depth = 2.0 * 0.6134  # 1.2268
        bore_dia = 20.0 - 2.0 * thread_depth
        assert abs(path[0][0] - bore_dia) < 0.01, (
            f"Internal preview should start at bore surface {bore_dia:.3f}, "
            f"got {path[0][0]:.3f}"
        )

    def test_internal_contour_spans_bore_to_major(self):
        params = {
            "major_diameter": 20.0,
            "pitch": 2.0,
            "length": 30.0,
            "passes": 3,
            "safe_z": 2.0,
            "orientation": 1,
        }
        path = build_thread_path(params)
        thread_depth = 2.0 * 0.6134
        bore_dia = 20.0 - 2.0 * thread_depth
        assert abs(path[-1][1] - (-30.0)) < 0.01
        x_values = [p[0] for p in path]
        assert min(x_values) >= bore_dia - 0.01
        assert max(x_values) <= 20.0 + 0.01
        assert any(abs(x - bore_dia) < 0.01 for x in x_values)
        assert any(abs(x - 20.0) < 0.01 for x in x_values)

    def test_internal_preview_respects_thread_start_z(self):
        params = {
            "major_diameter": 20.0,
            "pitch": 2.0,
            "length": 12.0,
            "thread_start_z": -4.0,
            "orientation": 1,
        }
        path = build_thread_path(params)
        assert abs(path[0][1] - (-4.0)) < 0.01
        assert abs(path[-1][1] - (-16.0)) < 0.01
