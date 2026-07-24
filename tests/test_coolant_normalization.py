import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.gcode_utils import emit_coolant


def _emitted(mode):
    lines = []
    emit_coolant(lines, mode)
    return lines[-1]


def test_numeric_coolant_one_turns_coolant_on():
    """Realer Bug: params["coolant"] wird bei Drill/Groove/Thread unveraendert
    durchgereicht (anders als bei Face, das vorher opt_bool() anwendet). Ein
    gespeicherter Zahlenwert 1.0 traf weder den str- noch den bool-Zweig von
    emit_coolant() und fiel auf M9 (AUS) zurueck, obwohl 1.0 "an" bedeuten
    sollte. Real reproduziert: Innen-Einstich, Innengewinde und Bohren mit
    coolant=1.0 blieben ohne Kuehlung (M9 statt M8)."""
    assert _emitted(1.0) == "M8"
    assert _emitted(1) == "M8"


def test_numeric_coolant_zero_turns_coolant_off():
    assert _emitted(0.0) == "M9"
    assert _emitted(0) == "M9"


def test_string_and_bool_coolant_values_unaffected():
    assert _emitted("on") == "M8"
    assert _emitted("off") == "M9"
    assert _emitted("mist") == "M7"
    assert _emitted(True) == "M8"
    assert _emitted(False) == "M9"
