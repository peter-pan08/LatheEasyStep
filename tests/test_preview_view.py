from types import SimpleNamespace

from lathe_easystep.ui_preview_view import PreviewView
from lathe_easystep.preview_scene import PreviewLayer, PreviewPath, PreviewScene


class _Preview:
    def __init__(self, *, visible=True, legacy=False):
        self.visible = visible
        self.legacy = legacy
        self.calls = []
        self.slice_enabled = False
        self.slice_z = 12.5

    def isVisible(self):
        return self.visible

    def set_paths(self, *args):
        if self.legacy and len(args) == 2:
            raise TypeError("legacy signature")
        self.calls.append(("paths", args))

    def set_collision(self, value):
        self.calls.append(("collision", value))

    def set_status_messages(self, messages):
        self.calls.append(("messages", messages))

    def set_front_context(self, context, operation):
        self.calls.append(("context", context, operation))

    def set_view_mode(self, mode):
        self.calls.append(("mode", mode))

    def set_slice_z(self, value):
        self.calls.append(("slice_z", value))

    def set_preview_scene(self, scene):
        self.preview_scene = scene
        self.calls.append(("scene", scene))


def _handler(preview=None, preview_slice=None, contour_preview=None):
    return SimpleNamespace(
        preview=preview,
        preview_slice=preview_slice,
        contour_preview=contour_preview,
        _ensure_slice_z_matches_operation=lambda operation: None,
    )


def test_apply_paths_updates_all_visible_views_and_context():
    main, slice_view, contour = _Preview(), _Preview(), _Preview()
    view = PreviewView(_handler(main, slice_view, contour))
    paths = [[{"type": "line"}]]
    context = {"preview_warnings": True, "__warnings": ["Grenze"]}

    view.apply_paths(paths, active_index=2, program_context=context,
                     active_operation="op", collision=True)

    assert ("collision", True) in main.calls
    assert ("messages", ["Grenze"]) in main.calls
    assert ("paths", (paths, 2)) in main.calls
    assert ("mode", "front") in slice_view.calls
    assert ("slice_z", 12.5) in slice_view.calls
    assert ("paths", (paths, 2)) in slice_view.calls
    assert ("paths", (paths, 2)) in contour.calls


def test_hidden_slice_and_disabled_contour_are_not_updated():
    main, slice_view, contour = _Preview(), _Preview(visible=False), _Preview()
    PreviewView(_handler(main, slice_view, contour)).apply_paths(
        [], include_contour_preview=False
    )

    assert slice_view.calls == []
    assert contour.calls == []


def test_legacy_set_paths_signature_is_supported():
    main = _Preview(legacy=True)
    PreviewView(_handler(main)).apply_paths([[]], active_index=1)
    assert ("paths", ([[]],)) in main.calls


def test_no_bound_preview_is_a_noop():
    view = PreviewView(_handler())
    assert view.is_bound() is False
    view.apply_paths([])


def test_apply_scene_preserves_layers_and_legacy_path_order():
    main = _Preview()
    main.preview_scene = None
    scene = PreviewScene((
        PreviewPath([{"role": "stock"}], PreviewLayer.AUXILIARY),
        PreviewPath([(20.0, 0.0)], PreviewLayer.TOOL_PATH),
    ), active_index=1)

    PreviewView(_handler(main)).apply_scene(scene)

    assert main.preview_scene is scene
    assert ("scene", scene) in main.calls
    assert ("paths", (scene.paths, 1)) in main.calls
