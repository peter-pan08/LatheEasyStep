import sys
import os

# Ensure local package directory is on sys.path so tests can import the slicer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slicer import rough_turn_parallel_x, rough_turn_parallel_z


def test_parallel_x_allows_undercut_by_default():
    path = [(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)]
    # stock at 14, target 6, step 4 -> passes 14-10,10-6
    lines = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=6.0, step_x=4.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    # Expect at least one pass with X-band
    assert any("X-band" in ln for ln in lines)


def test_parallel_x_prevents_undercut_when_disabled():
    path = [(10.0, 0.0), (8.0, -2.0)]
    # stock at 14, target 4, step 3 -> passes: [14-11],[11-8],[8-5]
    # The last pass would cut at x_lo = 5 which is < min(path_x)=8 -> undercut
    lines_allow = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    lines_no = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    # with allow_undercut True we should see at least 1 pass
    assert any("X-band" in ln for ln in lines_allow)
    # with allow_undercut False the last pass that would undercut should be skipped - therefore fewer passes
    count_allow = sum(1 for ln in lines_allow if ln.startswith('(Pass'))
    count_no = sum(1 for ln in lines_no if ln.startswith('(Pass'))
    assert count_no <= count_allow


def test_parallel_x_internal_produces_passes():
    path = [(6.0, 0.0), (8.0, -2.0), (10.0, -2.0)]
    lines = rough_turn_parallel_x(path, external=False, x_stock=4.0, x_target=10.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    assert any("X-band" in ln for ln in lines)


def test_parallel_z_basic_behavior():
    path = [(10.0, -1.0), (12.0, -3.0), (14.0, -3.0)]
    # external True, z_stock=max z = -1, z_target = -3, step_z=1 => passes
    lines = rough_turn_parallel_z(path, external=True, z_stock=-1.0, z_target=-3.0, step_z=1.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    assert any("Z-band" in ln for ln in lines)


def test_parallel_z_respects_undercut():
    path = [(8.0, -1.0), (10.0, -3.0)]
    lines_allow = rough_turn_parallel_z(path, external=True, z_stock=-1.0, z_target=-4.0, step_z=1.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    lines_no = rough_turn_parallel_z(path, external=True, z_stock=-1.0, z_target=-4.0, step_z=1.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    assert any("Z-band" in ln for ln in lines_allow)
    count_allow = sum(1 for ln in lines_allow if ln.startswith('(Pass'))
    count_no = sum(1 for ln in lines_no if ln.startswith('(Pass'))
    assert count_no <= count_allow
