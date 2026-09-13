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


@pytest.mark.parametrize("generator,op_type", [(gcode_for_turn, OpType.TURN), (gcode_for_bore, OpType.BORE)])
def test_legacy_turn_and_bore_switch_coolant_off_instead_of_leaving_it_running(generator, op_type):
    """LES-042 SICHERHEITSFUND 2026-09-13: TURN/BORE gaben Kuehlmittel bisher
    per direktem 'M8' aus, aber NIE ein zugehoeriges 'M9' - eine Operation
    mit coolant=False liess ein zuvor per M8 laufendes Kuehlmittel einfach
    weiterlaufen, statt es abzuschalten. Diese Operationstypen sind ueber
    die UI nicht mehr erstellbar, aber ueber alte gespeicherte Programme
    (unveraendertes Dateiformat seit Version 1, keine ablehnende Migration)
    weiterhin ladbar und generierbar - kein toter Code. `emit_coolant()`
    gibt jetzt wie bei jeder anderen Operation immer explizit den
    aktuellen Sollzustand aus."""
    # Zeile direkt nach dem Spindelstart ("G97 S.. M3") ist die
    # Kuehlmittel-Ausgabe dieser Operation - nicht einfach "M9" IRGENDWO in
    # der Ausgabe suchen, das erscheint bereits unabhaengig davon im
    # Werkzeugwechsel-Vorlauf (M5/M9 vor jedem Toolchange).
    settings = {"xt": 150.0, "zt": 300.0}
    op_on = Operation(op_type, {"tool": 1, "spindle": 800.0, "feed": 0.2, "coolant": True}, [(20.0, 0.0), (20.0, -10.0)])
    lines_on = generator(op_on, dict(settings))
    spindle_idx = next(i for i, l in enumerate(lines_on) if l.startswith("G97 "))
    assert lines_on[spindle_idx + 1] == "M8"
    op_off = Operation(op_type, {"tool": 1, "spindle": 800.0, "feed": 0.2, "coolant": False}, [(20.0, 0.0), (20.0, -10.0)])
    lines_off = generator(op_off, dict(settings))
    spindle_idx = next(i for i, l in enumerate(lines_off) if l.startswith("G97 "))
    assert lines_off[spindle_idx + 1] == "M9"


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
