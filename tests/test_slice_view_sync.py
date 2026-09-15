import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.preview_widget import LathePreviewWidget
from lathe_easystep.ui_preview import setup_slice_view, sync_slice_widget
from lathe_easystep_handler import HandlerClass


class _FakePreview:
    def __init__(self):
        self.slice_z = -12.5
        self.paths = [[(20.0, 0.0), (18.0, -20.0)]]
        self.active_index = 0
        self.front_program = {"xa": 20.0}
        self.front_operation = object()


class _FakePreviewSlice:
    def __init__(self, visible=False):
        self._visible = visible
        self.slice_z_calls = []
        self.view_modes = []
        self.paths_calls = []
        self.context_calls = []
        self.update_calls = 0

    def isVisible(self):
        return self._visible

    def set_slice_z(self, z_val):
        self.slice_z_calls.append(float(z_val))

    def set_view_mode(self, mode):
        self.view_modes.append(mode)

    def set_paths(self, paths, active_index=None):
        self.paths_calls.append((paths, active_index))

    def set_front_context(self, program, operation):
        self.context_calls.append((program, operation))

    def update(self):
        self.update_calls += 1


class _Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _SetupPreview:
    def __init__(self):
        self.sliceChanged = _Signal()
        self.modes = []
        self.visible = None

    def set_view_mode(self, mode):
        self.modes.append(mode)

    def setVisible(self, visible):
        self.visible = bool(visible)


class _SetupButton:
    def __init__(self):
        self.toggled = _Signal()

    def setChecked(self, _checked):
        pass

    def setText(self, _text):
        pass

    def setToolTip(self, _text):
        pass


def test_slice_setup_retries_after_preview_ui_is_loaded():
    handler = type("Handler", (), {})()
    handler.preview = None
    handler.preview_slice = None
    handler.btn_slice_view = None
    handler._slice_view_setup_done = False
    handler._get_widget_by_name = lambda _name: None
    handler._log = lambda *_args, **_kwargs: None
    handler._on_toggle_slice_view = lambda _checked: None
    handler._on_slice_changed = lambda _value: None

    setup_slice_view(handler)
    assert handler._slice_view_setup_done is False

    handler.preview = _SetupPreview()
    handler.preview_slice = _SetupPreview()
    handler.btn_slice_view = _SetupButton()
    setup_slice_view(handler)

    assert handler._slice_view_setup_done is True
    assert handler.preview.modes == ["side"]
    assert handler.preview_slice.modes == ["front"]
    assert handler.preview_slice.visible is False
    assert len(handler.btn_slice_view.toggled.callbacks) == 1
    assert len(handler.preview.sliceChanged.callbacks) == 1


def test_sync_slice_widget_updates_front_preview_even_if_widget_is_not_visible():
    logs = []
    handler = type("Handler", (), {})()
    handler.preview = _FakePreview()
    handler.preview_slice = _FakePreviewSlice(visible=False)
    handler._log = lambda message, level="info": logs.append((level, message))

    sync_slice_widget(handler)

    assert handler.preview_slice.slice_z_calls == [-12.5]
    assert handler.preview_slice.view_modes == ["front"]
    assert handler.preview_slice.paths_calls == [(handler.preview.paths, 0)]
    assert handler.preview_slice.context_calls == [(handler.preview.front_program, handler.preview.front_operation)]
    assert handler.preview_slice.update_calls == 1
    assert any("sync_slice_widget" in message for _level, message in logs)


def test_on_slice_changed_logs_and_syncs_widget():
    logs = []
    sync_calls = []
    handler = object.__new__(HandlerClass)
    handler.preview_slice = _FakePreviewSlice(visible=True)
    handler._log = lambda message, level="info": logs.append((level, message))
    handler._sync_slice_widget = lambda: sync_calls.append(True)

    HandlerClass._on_slice_changed(handler, -7.25)

    assert handler._current_slice_z == -7.25
    assert sync_calls == [True]
    assert any("slice changed" in message for _level, message in logs)


def test_preview_widget_emit_uses_callback_fallback():
    widget = LathePreviewWidget.__new__(LathePreviewWidget)
    widget.slice_z = 0.0
    widget.view_mode = "side"
    widget._slice_change_callback_calls = []
    widget._slice_change_callback = lambda value: widget._slice_change_callback_calls.append(float(value))
    widget._debug_slice = lambda _message: None
    widget.update = lambda: None

    LathePreviewWidget.set_slice_z(widget, -12.0, emit=True)

    assert widget.slice_z == -12.0
    assert widget._slice_change_callback_calls == [-12.0]
