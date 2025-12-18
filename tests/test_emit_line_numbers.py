import re
import sys
import os
# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import ProgramModel, Operation, OpType


def test_emit_line_numbers_disabled_removes_n_prefix(tmp_path):
    model = ProgramModel()
    # create a simple contour operation; contour output should be comments only
    contour_path = [(40.0, 2.0), (20.0, 0.0), (25.0, -35.0)]
    op = Operation(OpType.CONTOUR, params={"name": "Test"}, path=contour_path)
    model.add_operation(op)

    # disable numbering (should be default but set explicitly)
    model.program_settings = {"emit_line_numbers": False}

    lines = model.generate_gcode()
    # ensure no line begins with an N-number prefix and no executable G0/G1 are present
    assert not any(re.match(r"^\s*[Nn]\d+\b", l) for l in lines)
    assert not any(re.match(r"^\s*G0\b", l) or re.match(r"^\s*G1\b", l) for l in lines)
