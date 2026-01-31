import sys
import os

# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType

DEFAULT_RETRACT_SETTINGS = {"xra": 50.0, "zra": 5.0}


def test_parting_slice_index_triggers_parallel_x():
    m = ProgramModel()
    # slice_strategy data value (1 -> parallel_x)
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 1, "slice_step": 0.5, "depth_per_pass": 0.5, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel X)" in g


def test_parting_slice_index_triggers_parallel_z():
    m = ProgramModel()
    # slice_strategy data value (2 -> parallel_z)
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "slice_step": 0.5, "depth_per_pass": 0.5, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel Z)" in g


def test_parting_slice_string_triggers_parallel_x():
    m = ProgramModel()
    # slice_strategy as explicit string
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": "parallel_x", "slice_step": 1.0, "depth_per_pass": 1.0, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel X)" in g


def test_parting_slice_string_triggers_parallel_z():
    m = ProgramModel()
    # slice_strategy as explicit string
    m.operations = [Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": "parallel_z", "slice_step": 1.0, "depth_per_pass": 1.0, "feed": 0.2, "tool": 1}, path=[(12.0, 0.0), (10.0, -2.0)])]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    g = "\n".join(m.generate_gcode())
    assert "(ABSPANEN Rough - parallel Z)" in g
