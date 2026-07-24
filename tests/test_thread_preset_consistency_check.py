import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


def _preset_warnings(warnings):
    return [w for w in warnings if "Preset" in w]


def test_diverging_preset_pitch_is_reported():
    """Realer Bugreport: ein Gewinde-Step trug params["standard"] mit dem
    Preset fuer M30x3.5 (pitch=3.5), tatsaechlich verwendet wurde aber
    pitch=1.75 - Preset-Metadaten und der fuer G76 genutzte Wert waren
    auseinandergelaufen (z. B. Preset gewaehlt, dann Steigung manuell
    ueberschrieben, ohne dass "standard" nachgezogen wurde)."""
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {
                "pitch": 1.75, "length": 20.0, "major_diameter": 30.0,
                "thread_start_z": -10.0, "thread_depth": 1.07,
                "standard": {"label_key": "thread.standard.metric.m30x3_5", "major": 30.0, "pitch": 3.5},
            },
        ),
    ]
    warnings = _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0}))
    assert len(warnings) == 1
    assert "3.500" in warnings[0] and "1.750" in warnings[0]


def test_matching_preset_and_pitch_is_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {
                "pitch": 3.5, "length": 20.0, "major_diameter": 30.0,
                "thread_start_z": -10.0, "thread_depth": 1.07,
                "standard": {"label": "M30x3.5", "major": 30.0, "pitch": 3.5},
            },
        ),
    ]
    warnings = _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0}))
    assert warnings == []


def test_diverging_preset_major_diameter_is_reported():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {
                "pitch": 3.5, "length": 20.0, "major_diameter": 20.0,
                "thread_start_z": -10.0, "thread_depth": 1.07,
                "standard": {"label": "M30x3.5", "major": 30.0, "pitch": 3.5},
            },
        ),
    ]
    warnings = _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0}))
    assert len(warnings) == 1
    assert "30.000" in warnings[0] and "20.000" in warnings[0]


def test_thread_without_standard_preset_is_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {"pitch": 1.75, "length": 20.0, "major_diameter": 12.0, "thread_start_z": -10.0, "thread_depth": 1.07},
        ),
    ]
    assert _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0})) == []
