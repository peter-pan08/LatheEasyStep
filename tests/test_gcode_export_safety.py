from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import ProgramModel
from lathe_easystep.ui_persistence import write_gcode_file


def test_model_does_not_hide_an_unavailable_generator():
    model = ProgramModel(gcode_generator=None)
    # Import is available in the test environment, so force the unavailable
    # case explicitly rather than accepting the former three-line fallback.
    model._gcode_generator = False
    with pytest.raises(RuntimeError, match="nicht verfuegbar"):
        model.generate_gcode()


def test_failed_gcode_export_keeps_existing_file(tmp_path):
    target = tmp_path / "existing.ngc"
    target.write_text("old program", encoding="utf-8")

    class Handler:
        _current_gcode_path = None

        @staticmethod
        def _normalized_file_path(path):
            return str(path)

        @staticmethod
        def _build_gcode_lines():
            return ["%", "M30"]

    with pytest.raises(ValueError, match="kein vollstaendiges Programm"):
        write_gcode_file(Handler(), str(target))
    assert target.read_text(encoding="utf-8") == "old program"
