import pytest
import sys
import os
# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType

RETRACT_SETTINGS = {"xra": 45.0, "zra": 5.0}


def test_face_rough_includes_step_x_sub():
    m = ProgramModel()
    m.operations = [Operation(OpType.FACE, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0})]
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" in g


def test_face_finish_suppresses_step_x():
    m = ProgramModel()
    m.operations = [Operation(OpType.FACE, {"mode": 1, "pause_enabled": True, "pause_distance": 1.0})]
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" not in g


def test_abspanen_rough_includes_step_line_sub_and_call():
    m = ProgramModel()
    # enable Parallel X slicing so roughing occurs and calls are generated
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 0.1, "feed": 0.15, "slice_strategy": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_line_pause> sub" in g
    assert "o<step_line_pause> call" in g


def test_abspanen_rough_without_slicing_warns_and_has_no_call():
    m = ProgramModel()
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0, "feed": 0.15}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(WARN: Abspanen-Schruppen ohne Bearbeitungsrichtung ist deaktiviert)" in g
    assert "o<step_line_pause> call" not in g


def test_abspanen_finish_suppresses_step_line():
    m = ProgramModel()
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 1, "pause_enabled": True, "pause_distance": 1.0, "feed": 0.15}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_line_pause> sub" not in g
    assert "o<step_line_pause> call" not in g


def test_mixed_ops_only_includes_needed_subs():
    m = ProgramModel()
    m.operations = [
        Operation(OpType.FACE, {"mode": 1, "pause_enabled": True, "pause_distance": 1.0}),
        Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0}, path=[(0.0, 0.0), (10.0, -2.0)])
    ]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" not in g
    assert "o<step_line_pause> sub" in g
