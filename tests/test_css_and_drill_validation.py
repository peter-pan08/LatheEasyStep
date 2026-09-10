import re

import pytest

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_safety import append_tool_and_spindle, activate_pending_css
from lathe_easystep.motion_state import SpindleState


def test_css_fallback_discards_previous_pending_activation():
    settings = {"_spindle": SpindleState(pending=(2500, 120))}
    lines = []
    append_tool_and_spindle(lines, 0, 900, settings, spindle_mode="css")
    activate_pending_css(lines, settings)
    assert not any(line.startswith("G96") for line in lines)
    assert "G97 S900 M3" in lines


def test_css_integer_output_never_rounds_above_limit():
    settings = {}
    lines = []
    append_tool_and_spindle(lines, 0, 900, settings, spindle_mode="css",
                            cutting_speed=120, spindle_max_rpm=999.9, css_start_diameter=1)
    activate_pending_css(lines, settings)
    assert int(re.search(r"S(\d+)", lines[0])[1]) <= 999.9
    assert lines[-1] == "G96 D999 S120.0"


@pytest.mark.parametrize("limit", [0.1, 0.9])
def test_css_rejects_limit_below_representable_rpm(limit):
    with pytest.raises(ValueError):
        append_tool_and_spindle([], 0, 900, {}, spindle_mode="css",
                                cutting_speed=120, spindle_max_rpm=limit, css_start_diameter=10)


@pytest.mark.parametrize("mode,key,value", [
    ("g81", "feed", 0), ("g81", "feed", -0.1),
    ("g82", "dwell", -1), ("g83", "peck_depth", 0),
    ("g73", "peck_depth", -1), ("g81", "mode", 1.5),
    ("g81", "mode", "unknown"), ("g81", "mode", 99),
    ("g81", "feed", 0.00001), ("g83", "peck_depth", 0.00001),
])
def test_invalid_drilling_parameters_block_program(mode, key, value):
    ops, settings = example_programs()["Bohren.ngc"]
    ops[-1].params.update(mode=mode, dwell=0, peck_depth=1)
    ops[-1].params[key] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)


@pytest.mark.parametrize("key,value", [("feed", "nan"), ("safe_z", "inf"),
                                      ("retract", "bad"), ("peck_depth", "-inf")])
def test_direct_drill_call_validates_before_motion(key, value):
    from lathe_easystep.gcode_drill import generate_drill_gcode
    from lathe_easystep.gcode_utils import require, require_tool, get_tool_number
    ops, settings = example_programs()["Bohren.ngc"]
    op = ops[-1]
    op.params.update(mode="g83", peck_depth=1)
    op.params[key] = value
    def unexpected(*args, **kwargs):
        pytest.fail("No spindle or motion planning before validation")
    with pytest.raises(ValueError):
        generate_drill_gcode(op, settings, require=require, require_tool=require_tool,
                             get_tool_number=get_tool_number, append_tool_and_spindle=unexpected,
                             emit_coolant=unexpected, emit_approach=unexpected)


def test_invalid_drill_export_preserves_existing_file(tmp_path):
    from types import SimpleNamespace
    from lathe_easystep.ui_persistence import write_gcode_file
    ops, settings = example_programs()["Bohren.ngc"]
    ops[-1].params.update(mode="g83", peck_depth=0)
    target = tmp_path / "existing.ngc"
    target.write_text("previous program")
    handler = SimpleNamespace(_normalized_file_path=str,
                              _build_gcode_lines=lambda: generate_program_gcode(ops, settings))
    with pytest.raises(ValueError):
        write_gcode_file(handler, str(target))
    assert target.read_text() == "previous program"


@pytest.mark.parametrize("value", ["bad", "nan", "inf", "-inf", 1.5, True])
def test_integer_parameters_cannot_silently_fall_back_or_truncate(value):
    from lathe_easystep.gcode_utils import get_param_int
    with pytest.raises(ValueError):
        get_param_int({"mode": value, "groove_mode": 0}, ["mode", "groove_mode"], 0)


def test_invalid_numeric_alias_cannot_fall_back_to_another_dimension():
    from lathe_easystep.gcode_utils import get_param_float
    with pytest.raises(ValueError):
        get_param_float({"width": "bad", "groove_width": 5}, ["width", "groove_width"], 1)


def test_numeric_aliases_accept_empty_fields_and_legacy_number_strings():
    from lathe_easystep.gcode_utils import get_param_int, get_param_float
    assert get_param_int({"mode": "", "groove_mode": "1.0"}, ["mode", "groove_mode"]) == 1
    assert get_param_float({"width": None, "groove_width": "2.5"}, ["width", "groove_width"]) == 2.5


@pytest.mark.parametrize("spindle_value", [0, -100, None, 0.3])
def test_append_tool_and_spindle_blocks_when_no_spindle_command_would_be_emitted(spindle_value):
    """LES-040: Realer Bugreport - eine Operation mit spindle=0 (oder fehlend,
    negativ, oder auf 0 U/min gerundet) erzeugte bisher ein vollstaendig
    gueltiges G-Code-Programm OHNE ein einziges M3/S: die Spindel wuerde beim
    Abfahren nie gestartet. append_tool_and_spindle() blockiert das jetzt,
    ausser der Aufrufer uebergibt explizit require_spindle=False (reine
    Werkzeugwechsel-Positionierung ohne Drehzahlkontext)."""
    # tool_value=0 haelt die Werkzeugwechsel-Maschinerie (XT/ZT) aussen vor,
    # damit isoliert nur die Drehzahllogik geprueft wird.
    with pytest.raises(ValueError, match="Drehzahl"):
        append_tool_and_spindle([], 0, spindle_value, {})
    # Reine Positionierung (kein Drehzahlkontext) bleibt erlaubt.
    lines = []
    append_tool_and_spindle(lines, 0, spindle_value, {}, require_spindle=False)
    assert not any("M3" in line for line in lines)


def test_append_tool_and_spindle_blocks_incomplete_css_without_fixed_fallback():
    """LES-040: CSS/G96 ohne vollstaendige Parameter (Vc + Maximaldrehzahl)
    faellt auf die feste Drehzahl zurueck - fehlt auch die, darf ebenfalls
    keine leere Ausgabe entstehen."""
    with pytest.raises(ValueError, match="Drehzahl"):
        append_tool_and_spindle([], 0, 0, {}, spindle_mode="css", cutting_speed=120)


def test_abspanen_with_zero_spindle_blocks_generation_instead_of_silent_no_start():
    """Integrationstest fuer den realen Bugreport: eine komplette Abspanen-
    Operation mit spindle=0 darf kein 'gueltiges' Programm ohne Spindelstart
    mehr erzeugen."""
    from lathe_easystep.examples import make_program_settings
    from lathe_easystep.model import OpType, Operation

    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ZeroSpindle"}),
        Operation(
            OpType.CONTOUR,
            {"name": "c1"},
            path=[(0.0, 0.0), (20.0, 0.0), (20.0, -20.0)],
        ),
        Operation(
            OpType.ABSPANEN,
            {"mode": "rough", "tool": 1, "spindle": 0, "feed": 0.15,
             "depth_per_pass": 0.5, "slice_strategy": 1, "contour_name": "c1"},
        ),
    ]
    with pytest.raises(ValueError, match="Drehzahl"):
        generate_program_gcode(operations, settings)


@pytest.mark.parametrize("feed_value", [0, -0.15])
def test_abspanen_with_non_positive_feed_blocks_generation(feed_value):
    """LES-040: Realer Bugreport - REQUIRED_KEYS[OpType.ABSPANEN] fehlte
    "feed", weshalb feed=0 (Vorschub null, Werkzeug bewegt sich effektiv
    nicht) und sogar ein negativer Vorschub (`G1 ... F-0.150`, von
    LinuxCNC vermutlich ohnehin abgelehnt) bisher ein vollstaendig
    "gueltiges" Programm erzeugten. FACE und DRILL pruefen das bereits
    korrekt (dieselbe REQUIRED_KEYS/require_positive-Maschinerie) - nur
    ABSPANEN, die mit Abstand am haeufigsten genutzte Operation, hatte
    die Luecke."""
    from lathe_easystep.examples import make_program_settings
    from lathe_easystep.model import OpType, Operation

    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ZeroFeed"}),
        Operation(
            OpType.CONTOUR,
            {"name": "c1"},
            path=[(0.0, 0.0), (20.0, 0.0), (20.0, -20.0)],
        ),
        Operation(
            OpType.ABSPANEN,
            {"mode": "rough", "tool": 1, "spindle": 800, "feed": feed_value,
             "depth_per_pass": 0.5, "slice_strategy": 1, "contour_name": "c1"},
        ),
    ]
    with pytest.raises(ValueError, match="feed"):
        generate_program_gcode(operations, settings)
