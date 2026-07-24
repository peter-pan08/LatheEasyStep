import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import OpType, Operation
from lathe_easystep.preview_widget import LathePreviewWidget


def test_front_slice_profile_keeps_outer_and_inner_hits_at_same_z():
    widget = object.__new__(LathePreviewWidget)
    widget.slice_z = -5.0
    widget.paths = []
    widget.active_index = None
    outer_op = Operation(OpType.ABSPANEN, {"side": "outside"}, path=[(30.0, 0.0), (24.0, -10.0)])
    inner_op = Operation(OpType.ABSPANEN, {"side": "inside"}, path=[(10.0, 0.0), (16.0, -10.0)])
    widget.front_program = {"xa": 40.0, "xi": 0.0, "__operations": [outer_op, inner_op]}
    widget.front_operation = None

    profile = LathePreviewWidget._front_slice_profile(widget)

    assert profile["outer_hits"] == [27.0]
    assert profile["inner_hits"] == [13.0]
    assert profile["all_hits"] == [27.0, 13.0]
    assert profile["outer_fill"] == 27.0
    assert profile["inner_fill"] == 13.0


def test_front_slice_profile_preserves_multiple_thread_diameters_per_side():
    widget = object.__new__(LathePreviewWidget)
    widget.slice_z = -2.5
    widget.paths = []
    widget.active_index = None
    outer_thread = Operation(
        OpType.THREAD,
        {"orientation": "external", "pitch": 2.0, "major_diameter": 20.0, "length": 10.0, "thread_start_z": 0.0},
        path=[(20.0, 0.0), (17.5464, -1.0), (20.0, -2.0), (17.5464, -3.0), (20.0, -4.0)],
    )
    inner_thread = Operation(
        OpType.THREAD,
        {"orientation": "internal", "pitch": 2.0, "major_diameter": 12.0, "length": 10.0, "thread_start_z": 0.0},
        path=[(9.5464, 0.0), (12.0, -1.0), (9.5464, -2.0), (12.0, -3.0), (9.5464, -4.0)],
    )
    widget.front_program = {"__operations": [outer_thread, inner_thread]}
    widget.front_operation = None

    profile = LathePreviewWidget._front_slice_profile(widget)

    assert len(profile["outer_hits"]) >= 1
    assert len(profile["inner_hits"]) >= 1
    assert max(profile["outer_hits"]) > max(profile["inner_hits"])
