import math

from lathe_easystep.preview_geometry import (
    compute_side_viewport,
    nice_tick_step,
    side_view_axis_lines,
    side_view_slice_line,
    side_view_ticks,
    side_view_to_screen,
)


def test_empty_side_viewport_keeps_origin_and_minimum_span():
    viewport = compute_side_viewport([], width=220.0, height=110.0)

    assert viewport == {
        "min_x": -5.5,
        "max_x": 5.5,
        "min_z": -5.5,
        "max_z": 5.5,
        "scale": 10.0,
    }


def test_side_viewport_uses_diameter_x_and_padded_geometry_bounds():
    viewport = compute_side_viewport(
        [[(40.0, -20.0), (20.0, 0.0)]],
        width=220.0,
        height=110.0,
    )

    assert viewport["min_x"] == -6.25
    assert viewport["max_x"] == 21.25
    assert viewport["min_z"] == -21.25
    assert viewport["max_z"] == 6.25
    assert viewport["scale"] == 4.0


def test_side_viewport_samples_arc_primitives_for_bounds():
    arc = {
        "type": "arc",
        "p1": (20.0, 0.0),
        "p2": (40.0, -10.0),
        "c": (20.0, -10.0),
        "ccw": True,
    }

    viewport = compute_side_viewport([[arc]], width=300.0, height=200.0)

    assert viewport["max_x"] > 20.0
    assert viewport["min_z"] < -10.0
    assert viewport["scale"] > 0.0


def test_nice_tick_step_uses_stable_one_two_five_intervals():
    assert nice_tick_step(0.0) == 1.0
    assert nice_tick_step(11.0) == 2
    assert nice_tick_step(100.0) == 20
    assert math.isclose(nice_tick_step(0.11), 0.02)


def test_side_view_screen_mapping_halves_diameter_and_points_x_upward():
    viewport = {
        "min_x": -5.0, "max_x": 15.0,
        "min_z": -10.0, "max_z": 10.0, "scale": 10.0,
    }

    assert side_view_to_screen(
        20.0, 0.0, viewport, left=30.0, bottom=230.0
    ) == (130.0, 80.0)
    assert side_view_to_screen(
        10.0, 0.0, viewport, left=30.0, bottom=230.0, x_is_display=True
    ) == (130.0, 80.0)


def test_side_view_axes_cross_at_machine_origin_when_visible():
    viewport = {
        "min_x": -5.0, "max_x": 15.0,
        "min_z": -10.0, "max_z": 10.0, "scale": 10.0,
    }

    axes = side_view_axis_lines(viewport, left=30.0, bottom=230.0)

    assert axes["axis_x"] == 0.0
    assert axes["axis_z"] == 0.0
    assert axes["x_line"] == ((30.0, 180.0), (230.0, 180.0))
    assert axes["z_line"] == ((130.0, 230.0), (130.0, 30.0))


def test_side_view_slice_line_spans_the_displayed_x_range():
    viewport = {
        "min_x": -5.0, "max_x": 15.0,
        "min_z": -10.0, "max_z": 10.0, "scale": 10.0,
    }

    assert side_view_slice_line(
        viewport, -2.0, left=30.0, bottom=230.0
    ) == ((110.0, 230.0), (110.0, 30.0))


def test_side_view_ticks_include_positions_and_diameter_labels():
    viewport = {
        "min_x": -5.0, "max_x": 15.0,
        "min_z": -10.0, "max_z": 10.0, "scale": 10.0,
    }

    ticks = side_view_ticks(viewport, left=30.0, bottom=230.0)

    assert ticks["x"] == [
        (-5.0, -10.0, (130.0, 230.0)),
        (0.0, 0.0, (130.0, 180.0)),
        (5.0, 10.0, (130.0, 130.0)),
        (10.0, 20.0, (130.0, 80.0)),
        (15.0, 30.0, (130.0, 30.0)),
    ]
    assert ticks["z"] == [
        (-10.0, -10.0, (30.0, 180.0)),
        (-5.0, -5.0, (80.0, 180.0)),
        (0.0, 0.0, (130.0, 180.0)),
        (5.0, 5.0, (180.0, 180.0)),
        (10.0, 10.0, (230.0, 180.0)),
    ]
