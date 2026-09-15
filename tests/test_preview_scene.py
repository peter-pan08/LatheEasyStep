from lathe_easystep.model import OpType, Operation
from lathe_easystep.preview_scene import (
    PreviewLayer,
    PreviewPath,
    PreviewScene,
    build_front_view_draw_plan,
    build_front_view_screen_plan,
    build_preview_draw_plan,
    primitive_strokes,
    scene_from_legacy_paths,
    stroke_bounding_rectangle,
)


def test_scene_separates_workpiece_tool_path_and_auxiliary_without_reordering():
    contour_path = [(30.0, 0.0), (20.0, -10.0)]
    face_path = [(40.0, 1.0), (0.0, 0.0)]
    stock = [{"type": "line", "role": "stock", "p1": (40, 0), "p2": (40, -20)}]
    relief = [{"type": "line", "role": "feature", "p1": (20, -10), "p2": (19, -11)}]
    contour = Operation(OpType.CONTOUR, {}, contour_path)
    face = Operation(OpType.FACE, {}, face_path)
    paths = [stock, contour_path, face_path, relief]

    scene = scene_from_legacy_paths(paths, 2, [contour, face], face)

    assert scene.paths == paths
    assert scene.paths_for(PreviewLayer.WORKPIECE) == [contour_path, relief]
    assert scene.paths_for(PreviewLayer.TOOL_PATH) == [face_path]
    assert scene.paths_for(PreviewLayer.AUXILIARY) == [stock]
    assert scene.active_entry.operation is face


def test_drill_silhouette_is_not_mislabeled_as_verified_tool_path():
    drill_path = [(0.0, 0.0), (10.0, -5.0)]
    drill = Operation(OpType.DRILL, {}, drill_path)
    scene = scene_from_legacy_paths([drill_path], 0, [drill], drill)
    assert scene.entries[0].layer == PreviewLayer.AUXILIARY


def test_disconnected_primitives_remain_separate_strokes():
    primitives = [
        {"type": "line", "p1": (0, 0), "p2": (1, 0)},
        {"type": "line", "p1": (10, 10), "p2": (11, 10)},
    ]

    strokes = primitive_strokes(primitives, lambda *_args: [])

    assert strokes == [[(0.0, 0.0), (1.0, 0.0)], [(10.0, 10.0), (11.0, 10.0)]]
    assert all(not (stroke[0] == (1.0, 0.0) and stroke[-1] == (10.0, 10.0)) for stroke in strokes)


def test_arc_and_polyline_each_form_their_own_stroke():
    primitives = [
        {"type": "arc", "p1": (0, 0), "p2": (2, 0), "c": (1, 0), "ccw": True},
        {"type": "polyline", "points": [(5, 5), (6, 6), (7, 5)]},
    ]
    strokes = primitive_strokes(primitives, lambda *_args: [(0, 0), (1, 1), (2, 0)])
    assert strokes == [
        [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)],
        [(5.0, 5.0), (6.0, 6.0), (7.0, 5.0)],
    ]


def test_draw_plan_puts_active_path_last_and_uses_scene_layers():
    paths = [[(1, 1)], [(2, 2)], [(3, 3)]]
    scene = PreviewScene((
        PreviewPath(paths[0], PreviewLayer.WORKPIECE),
        PreviewPath(paths[1], PreviewLayer.TOOL_PATH),
        PreviewPath(paths[2], PreviewLayer.AUXILIARY),
    ), active_index=1)

    plan = build_preview_draw_plan(paths, 1, scene)

    assert [item.index for item in plan] == [0, 2, 1]
    assert [item.style_key for item in plan] == ["workpiece", "auxiliary", "active"]


def test_draw_plan_keeps_special_role_style_even_when_path_is_active():
    path = [{"type": "line", "role": "chuck_nogo", "p1": (0, 0), "p2": (1, 1)}]

    plan = build_preview_draw_plan([path], 0)

    assert len(plan) == 1
    assert plan[0].role == "chuck_nogo"
    assert plan[0].style_key == "chuck_nogo"


def test_stroke_bounding_rectangle_encloses_disconnected_primitives():
    strokes = [[(4.0, -8.0), (4.0, -2.0)], [(10.0, -6.0), (7.0, 1.0)]]

    assert stroke_bounding_rectangle(strokes) == [
        (4.0, -8.0),
        (4.0, 1.0),
        (10.0, 1.0),
        (10.0, -8.0),
    ]


def test_stroke_bounding_rectangle_is_empty_without_drawable_points():
    assert stroke_bounding_rectangle([]) == []
    assert stroke_bounding_rectangle([[]]) == []


def test_front_view_draw_plan_orders_stock_then_fill_then_rings():
    plan = build_front_view_draw_plan(
        stock_od=40.0,
        stock_id=20.0,
        outer_fill_diameter=35.0,
        inner_fill_diameter=18.0,
        outer_hits=[35.0],
        inner_hits=[18.0],
        active_diameters=[35.0, 30.0],
    )

    assert [(c.diameter, c.style_key, c.filled) for c in plan] == [
        (40.0, "stock_od", False),
        (20.0, "stock_id", False),
        (35.0, "end_contour_fill", True),
        (18.0, "end_contour_hole", True),
        (35.0, "outer_ring", False),
        (18.0, "inner_ring", False),
        (30.0, "active_ring", False),
    ]


def test_front_view_draw_plan_skips_stock_id_when_not_smaller_than_stock_od():
    plan = build_front_view_draw_plan(
        stock_od=20.0, stock_id=20.0,
        outer_fill_diameter=0.0, inner_fill_diameter=0.0,
        outer_hits=[], inner_hits=[], active_diameters=[],
    )
    assert [c.style_key for c in plan] == ["stock_od"]


def test_front_view_draw_plan_skips_end_contour_hole_without_a_smaller_bore():
    plan = build_front_view_draw_plan(
        stock_od=0.0, stock_id=0.0,
        outer_fill_diameter=30.0, inner_fill_diameter=30.0,
        outer_hits=[], inner_hits=[], active_diameters=[],
    )
    assert [c.style_key for c in plan] == ["end_contour_fill"]


def test_front_view_draw_plan_omits_zero_and_negligible_diameters():
    plan = build_front_view_draw_plan(
        stock_od=0.0, stock_id=0.0,
        outer_fill_diameter=0.0, inner_fill_diameter=0.0,
        outer_hits=[], inner_hits=[], active_diameters=[],
    )
    assert plan == []


def test_front_view_screen_plan_resolves_radii_and_paint_phases():
    circles = build_front_view_draw_plan(
        stock_od=40.0, stock_id=20.0,
        outer_fill_diameter=35.0, inner_fill_diameter=18.0,
        outer_hits=[35.0], inner_hits=[18.0], active_diameters=[30.0],
    )
    plan = build_front_view_screen_plan(
        circles, center=(120.0, 80.0), scale=4.0
    )

    assert [circle.style_key for circle in plan["stock"]] == ["stock_od", "stock_id"]
    assert [circle.style_key for circle in plan["filled"]] == [
        "end_contour_fill", "end_contour_hole",
    ]
    assert [circle.style_key for circle in plan["rings"]] == [
        "outer_ring", "inner_ring", "active_ring",
    ]
    assert plan["stock"][0].center == (120.0, 80.0)
    assert plan["stock"][0].radius == 80.0
    assert plan["filled"][0].filled is True
