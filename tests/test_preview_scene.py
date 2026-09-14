from lathe_easystep.model import OpType, Operation
from lathe_easystep.preview_scene import PreviewLayer, primitive_strokes, scene_from_legacy_paths


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
