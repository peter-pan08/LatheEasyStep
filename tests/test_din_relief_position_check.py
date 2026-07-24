import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


def _relief_warnings(warnings):
    return [w for w in warnings if "Freistich" in w]


def _relief_segment(z, orientation="end"):
    return {
        "mode": "z", "x": 0.0, "z": z, "x_empty": True, "z_empty": False,
        "feature": {
            "feature_type": "din_relief", "internal": False, "norm": "DIN 76-A",
            "orientation": orientation, "side": "external", "thread_size": "M30",
        },
    }


def test_relief_mid_contour_warns_no_geometry():
    """Realer Bugreport: ein M30-Aussengewinde-Freistich bei Z=-35, gefolgt von
    weiterem Wellenprofil bis Z=-60, erzeugt keine Freistich-Geometrie -
    build_contour_variants() erkennt das Feature nur am absoluten Rand der
    GESAMTEN Kontur, nicht am Ende des Gewindes selbst."""
    segments = [
        {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True},
        _relief_segment(-35.0, orientation="end"),
        {"mode": "x", "x": 40.0, "z": -35.0, "x_empty": False, "z_empty": True},
        {"mode": "z", "x": 0.0, "z": -60.0, "x_empty": True, "z_empty": False},
    ]
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    warnings = _relief_warnings(validate_program_setup(ops, {}))
    assert len(warnings) == 1
    assert "Segment 2" in warnings[0]


def test_relief_at_actual_contour_end_is_silent():
    segments = [
        {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True},
        _relief_segment(-35.0, orientation="end"),
    ]
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []


def test_relief_at_actual_contour_start_is_silent():
    segments = [_relief_segment(-2.0, orientation="start"), {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True}]
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []
