import pytest
import sys
import os
# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType

RETRACT_SETTINGS = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0}


def test_face_rough_includes_step_x_sub():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.FACE, {
        "mode": 0, "pause_enabled": True, "pause_distance": 1.0,
        "start_x": 40.0, "start_z": 1.0, "end_x": -1.0, "end_z": 0.0,
        "finish_allow_z": 0.05, "depth_max": 0.4, "retract": 0.5,
        "feed": 0.2, "spindle": 1300.0, "tool": 1,
        "edge_type": 0, "edge_size": 0.0, "coolant": False
    })]
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" in g


def test_face_finish_suppresses_step_x():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.FACE, {
        "mode": 1, "pause_enabled": True, "pause_distance": 1.0,
        "start_x": 40.0, "start_z": 1.0, "end_x": -1.0, "end_z": 0.0,
        "finish_allow_z": 0.05, "depth_max": 0.4, "retract": 0.5,
        "feed": 0.2, "spindle": 1300.0, "tool": 1,
        "edge_type": 0, "edge_size": 0.0, "coolant": False
    })]
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" not in g


def test_abspanen_rough_includes_step_line_sub_and_call():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    # enable Parallel X slicing so roughing occurs and calls are generated
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 0.1, "depth_per_pass": 0.5, "feed": 0.15, "slice_strategy": 1, "spindle": 1000.0, "tool": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_line_pause> sub" in g
    assert "o<step_line_pause> call" in g


def test_abspanen_rough_without_slicing_aborts_generation():
    """LES-002: ein Schruppstep ohne Bearbeitungsrichtung erzeugte frueher nur
    eine Warnzeile und keinen Schnitt - ein leises, leicht zu uebersehendes
    Nichts im Programm. Das ist jetzt ein harter Abbruch mit ValueError, damit
    ein solcher Step nicht unbemerkt als scheinbar gueltiges Programm
    durchgeht."""
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0, "depth_per_pass": 0.5, "feed": 0.15, "spindle": 1000.0, "tool": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    with pytest.raises(ValueError, match="keinen einzigen Schnitt"):
        m.generate_gcode()


def test_abspanen_finish_suppresses_step_line():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 1, "pause_enabled": True, "pause_distance": 1.0, "depth_per_pass": 0.5, "feed": 0.15, "spindle": 1000.0, "tool": 1}, path=[(0.0, 0.0), (10.0, -2.0)])]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_line_pause> sub" not in g
    assert "o<step_line_pause> call" not in g


def test_mixed_ops_only_includes_needed_subs():
    m = ProgramModel()
    m.program_settings.update({"xt": 150.0, "zt": 300.0})
    m.operations = [
        Operation(OpType.FACE, {
            "mode": 1, "pause_enabled": True, "pause_distance": 1.0,
            "start_x": 40.0, "start_z": 1.0, "end_x": -1.0, "end_z": 0.0,
            "finish_allow_z": 0.05, "depth_max": 0.4, "retract": 0.5,
            "feed": 0.2, "spindle": 1300.0, "tool": 1,
            "edge_type": 0, "edge_size": 0.0, "coolant": False
        }),
        Operation(OpType.ABSPANEN, {"mode": 0, "pause_enabled": True, "pause_distance": 1.0, "depth_per_pass": 0.5, "spindle": 1000.0, "tool": 1, "slice_strategy": "parallel_z"}, path=[(0.0, 0.0), (10.0, -2.0)])
    ]
    m.program_settings = RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "o<step_x_pause> sub" not in g
    assert "o<step_line_pause> sub" in g
