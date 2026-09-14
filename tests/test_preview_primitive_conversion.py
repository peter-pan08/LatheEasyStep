"""Direct tests for the pure preview primitive conversion."""

from lathe_easystep.preview_geometry import (
    preview_primitives_to_points,
    sample_preview_arc,
)


def test_invalid_arc_falls_back_to_its_endpoints():
    p1 = (10.0, 0.0)
    p2 = (20.0, 0.0)

    assert sample_preview_arc(p1, p2, (10.0, 0.0), True) == [p1, p2]


def test_connected_line_primitives_share_the_joint_once():
    primitives = [
        {"type": "line", "p1": (0.0, 0.0), "p2": (10.0, 0.0)},
        {"type": "line", "p1": (10.0, 0.0), "p2": (10.0, -5.0)},
    ]

    assert preview_primitives_to_points(primitives) == [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, -5.0),
    ]


def test_mixed_invalid_entries_are_ignored():
    primitives = [None, "bad", (1, 2), ("x", 3)]

    assert preview_primitives_to_points(primitives) == [(1.0, 2.0)]
