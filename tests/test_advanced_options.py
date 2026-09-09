import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation
from lathe_easystep.persistence import operation_to_step_data, step_data_to_operation


def test_css_and_custom_park_position_are_emitted():
    settings = make_program_settings()
    settings.update(
        {
            "spindle_mode": "css",
            "spindle_max_rpm": 3200.0,
            "park_mode": "end_position",
            "park_coords": "machine",
            "park_x": 111.0,
            "park_z": 222.0,
            "park_sequential": True,
        }
    )
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "CSSPark"}),
        Operation(
            OpType.THREAD,
            {"tool": 3, "spindle": 500.0, "pitch": 1.5, "length": 12.0, "major_diameter": 10.0, "cutting_speed": 90.0},
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    assert "G97 S2839 M3 (CSS-Anfahrdrehzahl bei X10.092)" in text
    assert "G96 D3200 S90.0" in text
    assert text.index("G97 S2839") < text.index("G96 D3200") < text.index("G76 ")
    park_idx = lines.index("(Parkposition am Ende)")
    assert lines[park_idx + 1] == "G53 G0 X111.000"
    assert lines[park_idx + 2] == "G53 G0 Z222.000"


def test_automatic_thread_relief_requires_a_matching_contour():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ThreadRelief"}),
        Operation(
            OpType.THREAD,
            {
                "tool": 3,
                "spindle": 450.0,
                "pitch": 1.5,
                "length": 20.0,
                "major_diameter": 10.0,
                "relief_mode": "suggest",
                "relief_norm": "DIN 76-A",
                "optional_stop_before": True,
            },
        ),
    ]
    with pytest.raises(ValueError, match="konnte keiner passenden.*Kontur"):
        generate_program_gcode(operations, settings)


def test_thread_relief_suggestion_aborts_when_overlap_exceeds_thread_length():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ThreadReliefTooShort"}),
        Operation(
            OpType.THREAD,
            {
                "tool": 3,
                "spindle": 450.0,
                "pitch": 1.5,
                "length": 1.0,
                "major_diameter": 10.0,
                "relief_mode": "suggest",
                "relief_norm": "DIN 76-A",
            },
        ),
    ]
    with pytest.raises(ValueError, match="Gewindeueberdeckung.*Gewindelaenge"):
        generate_program_gcode(operations, settings)


def test_optional_stop_before_toolchange_is_emitted():
    settings = make_program_settings()
    settings["optional_stop_toolchange"] = True
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "StopTC"}),
        Operation(OpType.THREAD, {"tool": 3, "spindle": 400.0, "pitch": 1.0, "length": 10.0, "major_diameter": 8.0}),
        Operation(OpType.DRILL, {"tool": 7, "spindle": 1000.0, "feed": 0.08, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -10.0), (0.0, -12.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T07 M6")
    assert "M1" in lines[max(0, toolchange_idx - 8):toolchange_idx]


def test_optional_stop_before_first_toolchange_is_emitted():
    """LES-039: das Tooltip verspricht 'vor jedem Werkzeugwechsel', der
    allererste Werkzeugwechsel wurde davon aber bisher stillschweigend
    ausgenommen - genau dort ist Werkzeug/Position am wenigsten bekannt.
    M1 muss ausserdem VOR der angenommenen sicheren Rueckzugsbewegung
    stehen, nicht danach, damit der Bediener vor jeder Bewegung pruefen
    kann."""
    settings = make_program_settings()
    settings["optional_stop_toolchange"] = True
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "StopFirstTC"}),
        Operation(OpType.THREAD, {"tool": 3, "spindle": 400.0, "pitch": 1.0, "length": 10.0, "major_diameter": 8.0}),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T03 M6")
    prelude = lines[:toolchange_idx]
    assert "M1" in prelude
    m1_idx = prelude.index("M1")
    assert not any(line.startswith("G0") for line in prelude[:m1_idx])


def test_advanced_abspanen_params_roundtrip_through_persistence():
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1,
            "contour_name": "C1",
            "undercut_mode": "separate",
            "output_preference": "prefer_explicit",
            "undercut_tool": 5,
            "undercut_spindle": 900.0,
            "undercut_feed": 0.06,
            "optional_stop_before_undercut": True,
        },
        path=[],
    )
    data = operation_to_step_data(op)
    restored = step_data_to_operation(data)
    assert restored is not None
    assert restored.params["undercut_mode"] == "separate"
    assert restored.params["output_preference"] == "prefer_explicit"
    assert restored.params["undercut_tool"] == 5
    assert restored.params["optional_stop_before_undercut"] is True


def test_contour_feature_params_roundtrip_through_persistence():
    op = Operation(
        OpType.CONTOUR,
        {
            "name": "FeatureContour",
            "segments": [
                {"x": 20.0, "z": -10.0},
                {
                    "x": 20.0,
                    "z": -20.0,
                    "feature": {
                        "feature_type": "din_relief",
                        "thread_size": "M10",
                        "norm": "DIN 76-A",
                        "internal": False,
                        "side": "external",
                        "orientation": "end",
                    },
                },
            ],
        },
        path=[],
    )
    data = operation_to_step_data(op)
    restored = step_data_to_operation(data)
    assert restored is not None
    feature = restored.params["segments"][1]["feature"]
    assert feature["feature_type"] == "din_relief"
    assert feature["thread_size"] == "M10"
    assert feature["norm"] == "DIN 76-A"
