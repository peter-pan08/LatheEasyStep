import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation


def test_keyway_generation_does_not_fail_on_missing_safe_z_before_real_error():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "KeywayValidation"}),
        Operation(
            OpType.KEYWAY,
            {
                "depth_per_pass": 0.1,
                "comment": "Keyway",
            },
        ),
    ]

    try:
        generate_program_gcode(operations, settings)
    except ValueError as exc:
        text = str(exc)
        assert "safe_z" not in text
        assert "KEYWAY verwendet Makro-Variablen" in text
    else:
        raise AssertionError("Expected KEYWAY generation to fail on the current macro restriction")
