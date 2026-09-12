from copy import deepcopy

import pytest

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_program import gcode_for_bore, gcode_for_turn
from lathe_easystep.model import OpType, Operation


@pytest.mark.parametrize("key", [
    "width", "depth", "depth_per_pass", "feed", "retract", "finish",
    "overlap", "chip_amp",
])
def test_groove_rejects_negative_magnitude_parameters(key):
    operations, settings = example_programs()["Einstich.ngc"]
    operations = deepcopy(operations)
    operations[-1].params[key] = -0.1
    with pytest.raises(ValueError, match="darf nicht negativ"):
        generate_program_gcode(operations, settings)


@pytest.mark.parametrize("key", ["finish_allow_x", "finish_allow_z", "pause_distance"])
def test_roughing_rejects_negative_allowances_and_pause_distance(key):
    operations, settings = example_programs()["Abdrehen.ngc"]
    operations = deepcopy(operations)
    operations[-1].params[key] = -0.1
    with pytest.raises(ValueError, match="duerfen nicht negativ"):
        generate_program_gcode(operations, settings)


@pytest.mark.parametrize("key", ["feed", "depth_per_pass"])
def test_roughing_rejects_positive_values_that_round_to_zero(key):
    operations, settings = example_programs()["Abdrehen.ngc"]
    operations = deepcopy(operations)
    operations[-1].params[key] = 0.0001
    with pytest.raises(ValueError, match="Ausgaberundung"):
        generate_program_gcode(operations, settings)


def test_thread_rejects_pitch_that_rounds_to_zero():
    operations, settings = example_programs()["Gewinde.ngc"]
    operations = deepcopy(operations)
    operations[-1].params["pitch"] = 0.00001
    with pytest.raises(ValueError, match="Ausgaberundung"):
        generate_program_gcode(operations, settings)


@pytest.mark.parametrize("key", ["feed", "depth_max"])
def test_facing_rejects_positive_values_that_round_to_zero(key):
    operations, settings = example_programs()["Planen.ngc"]
    operations = deepcopy(operations)
    operations[-1].params[key] = 0.0001
    with pytest.raises(ValueError, match="Ausgaberundung"):
        generate_program_gcode(operations, settings)


def test_facing_rejects_negative_pause_distance():
    operations, settings = example_programs()["Planen.ngc"]
    operations = deepcopy(operations)
    operations[-1].params["pause_distance"] = -0.1
    with pytest.raises(ValueError, match="pause_distance"):
        generate_program_gcode(operations, settings)


@pytest.mark.parametrize("generator,op_type", [(gcode_for_turn, OpType.TURN), (gcode_for_bore, OpType.BORE)])
@pytest.mark.parametrize("feed", [-0.1, 0.0001])
def test_legacy_turn_and_bore_reject_invalid_feed(generator, op_type, feed):
    op = Operation(op_type, {"tool": 1, "spindle": 1000.0, "feed": feed, "safe_z": 2.0}, [(20.0, 0.0), (18.0, -2.0)])
    with pytest.raises(ValueError, match="Ausgaberundung"):
        generator(op, {})


def test_thread_peak_offset_that_rounds_to_zero_falls_back_instead_of_vanishing():
    """LES-028 2026-09-12: ein explizit gesetzter, aber winziger
    `peak_offset` (0.00001) verschwand bisher lautlos im vierstellig
    gerundeten G76-I-Wort (`I-0.0000` bzw. `I0.0000`) - weder der
    bestehende Fallback fuer einen fehlenden/exakt-0-Wert griff (der
    prueft nur `peak_offset == 0.0`), noch gab es eine eigene Pruefung
    fuer diesen Fall. Jetzt behandelt wie ein fehlender Wert: der
    Standardwert (`max(first_depth, pitch*0.05)`) wird verwendet, `I`
    bleibt ein echter, von Null verschiedener Wert."""
    operations, settings = example_programs()["Gewinde.ngc"]
    operations = deepcopy(operations)
    operations[-1].params["peak_offset"] = 0.00001
    lines = generate_program_gcode(operations, settings)
    g76_line = next(line for line in lines if line.startswith("G76 "))
    i_word = next(word for word in g76_line.split() if word.startswith("I"))
    assert abs(float(i_word[1:])) > 0.001, f"I-Wert verschwand: {g76_line}"
