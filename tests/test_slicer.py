import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slicer import Segment, segments_from_polyline, intersect_segment_with_x_band, merge_intervals, compute_pass_x_levels, rough_turn_parallel_x


def test_intersect_horizontal_segment():
    s = Segment(0.0, 0.0, 10.0, 0.0)
    assert intersect_segment_with_x_band(s, 2.0, 4.0) == (0.0, 0.0)


def test_intersect_vertical_segment_in_band():
    s = Segment(3.0, -1.0, 3.0, 5.0)
    assert intersect_segment_with_x_band(s, 2.5, 3.5) == (-1.0, 5.0)


def test_merge_intervals():
    inp = [(0, 10), (9, 12), (20, 30)]
    out = merge_intervals(inp)
    assert out == [(0, 12), (20, 30)]


def test_compute_pass_levels_external():
    passes = compute_pass_x_levels(40.0, 30.0, 5.0, True)
    assert passes == [(40.0, 35.0), (35.0, 30.0)]


def test_rough_turn_parallel_x_simple():
    # simple sloped contour
    path = [(40.0, 0.0), (35.0, -10.0), (30.0, -20.0)]
    lines = rough_turn_parallel_x(path, external=True, x_stock=40.0, x_target=30.0, step_x=5.0, safe_z=5.0, feed=0.2)
    assert any("Pass 1" in L for L in lines)
    assert any("Pass 2" in L for L in lines)
