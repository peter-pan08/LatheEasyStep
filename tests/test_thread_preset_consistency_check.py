import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation


_PRESET_KEYS = {
    "warning.thread_preset_pitch_mismatch",
    "warning.thread_preset_major_mismatch",
    "warning.thread_preset_field_conflicts",
}


def _preset_warnings(warnings):
    return [w for w in warnings if w["key"] in _PRESET_KEYS]


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
    assert warnings[0]["key"] == "warning.thread_preset_pitch_mismatch"
    assert warnings[0]["params"]["preset_value"] == 3.5
    assert warnings[0]["params"]["actual_value"] == 1.75


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
    assert warnings[0]["key"] == "warning.thread_preset_major_mismatch"
    assert warnings[0]["params"]["preset_value"] == 30.0
    assert warnings[0]["params"]["actual_value"] == 20.0


def test_thread_without_standard_preset_is_silent():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {"pitch": 1.75, "length": 20.0, "major_diameter": 12.0, "thread_start_z": -10.0, "thread_depth": 1.07},
        ),
    ]
    assert _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0})) == []


def test_diverging_derived_preset_values_are_reported_together():
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.THREAD,
            {
                "pitch": 1.5, "length": 20.0, "major_diameter": 10.0,
                "thread_start_z": -10.0, "thread_depth": 9.0,
                "first_depth": 0.2, "infeed_q": 15.0,
                "standard": {"label": "M10", "major": 10.0, "pitch": 1.5, "profile": "metric"},
            },
        ),
    ]

    warnings = _preset_warnings(validate_program_setup(ops, {"za": 0.0, "zi": -50.0}))

    assert len(warnings) == 1
    assert warnings[0]["key"] == "warning.thread_preset_field_conflicts"
    conflict_field_keys = {c["field_key"] for c in warnings[0]["params"]["conflicts"]}
    assert conflict_field_keys == {"thread_depth", "infeed_q", "first_depth"}
