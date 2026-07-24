import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import OpType, Operation, ProgramModel

DEFAULT_RETRACT_SETTINGS = {"xra": 50.0, "zra": 0.0}


def test_no_redundant_g0_when_finish_contour_already_ends_at_safe_z():
    """Realer Bug (Test.lse Innen-Schlichten): die Kontur endete bereits bei
    Z0.000 und safe_z (ZRA/ZRI) war ebenfalls 0.000 - trotzdem wurde
    zusaetzlich ein 'G0 Z0.000' angehaengt: eine bedeutungslose Nullbewegung
    auf eine bereits erreichte Position."""
    m = ProgramModel()
    path = [(10.0, -10.0), (19.0, 0.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {"mode": 1, "slice_strategy": "parallel_z", "depth_per_pass": 1.0, "feed": 0.15, "tool": 1},
            path=path,
        )
    ]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    lines = m.generate_gcode()
    idx = lines.index("(Schlichtschnitt Kontur)")
    last_cut_idx = max(i for i, l in enumerate(lines) if l.startswith("G1 "))
    tail = lines[last_cut_idx + 1:idx + 6]
    assert "G0 Z0.000" not in tail


def test_retract_still_emitted_when_finish_contour_ends_elsewhere():
    m = ProgramModel()
    path = [(10.0, -10.0), (19.0, -2.0)]
    m.operations = [
        Operation(
            OpType.ABSPANEN,
            {"mode": 1, "slice_strategy": "parallel_z", "depth_per_pass": 1.0, "feed": 0.15, "tool": 1},
            path=path,
        )
    ]
    m.program_settings = DEFAULT_RETRACT_SETTINGS
    lines = m.generate_gcode()
    last_cut_idx = max(i for i, l in enumerate(lines) if l.startswith("G1 "))
    tail = lines[last_cut_idx + 1:last_cut_idx + 3]
    assert "G0 Z0.000" in tail
