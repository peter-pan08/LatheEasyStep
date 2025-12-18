import sys
import os

# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass


class BoolWidget:
    def __init__(self):
        self.visible = None

    def setVisible(self, v):
        self.visible = bool(v)


class FakeCombo:
    def __init__(self, idx):
        self._idx = idx

    def currentIndex(self):
        return self._idx


def test_parting_visibility_rough_shows_widgets():
    h = object.__new__(HandlerClass)
    h.parting_mode = FakeCombo(0)  # 0 = Schruppen / Rough

    # widgets that are shown/hidden
    h.label_parting_depth = BoolWidget()
    h.parting_depth_per_pass = BoolWidget()
    h.label_parting_pause = BoolWidget()
    h.parting_pause_enabled = BoolWidget()
    h.label_parting_pause_distance = BoolWidget()
    h.parting_pause_distance = BoolWidget()
    h.label_parting_slice_strategy = BoolWidget()
    h.parting_slice_strategy = BoolWidget()
    # slicing step is auto-managed and not shown in the UI
    h.label_parting_slice_step = BoolWidget()
    h.parting_slice_step = BoolWidget()
    h.label_parting_allow_undercut = BoolWidget()
    h.parting_allow_undercut = BoolWidget()

    h._update_parting_mode_visibility()

    assert h.parting_depth_per_pass.visible is True
    assert h.parting_pause_enabled.visible is True
    assert h.parting_slice_strategy.visible is True
    # ensure slice_step remains hidden
    assert h.parting_slice_step.visible is False


def test_parting_visibility_finish_hides_widgets():
    h = object.__new__(HandlerClass)
    h.parting_mode = FakeCombo(1)  # 1 = Schlichten / Finish

    h.label_parting_depth = BoolWidget()
    h.parting_depth_per_pass = BoolWidget()
    h.label_parting_pause = BoolWidget()
    h.parting_pause_enabled = BoolWidget()
    h.label_parting_pause_distance = BoolWidget()
    h.parting_pause_distance = BoolWidget()
    h.label_parting_slice_strategy = BoolWidget()
    h.parting_slice_strategy = BoolWidget()
    # slicing step is auto-managed and not shown in the UI
    h.label_parting_slice_step = BoolWidget()
    h.parting_slice_step = BoolWidget()
    h.label_parting_allow_undercut = BoolWidget()
    h.parting_allow_undercut = BoolWidget()

    h._update_parting_mode_visibility()

    assert h.parting_depth_per_pass.visible is False
    assert h.parting_pause_enabled.visible is False
    assert h.parting_slice_strategy.visible is False
    # slice_step should still be hidden
    assert h.parting_slice_step.visible is False
