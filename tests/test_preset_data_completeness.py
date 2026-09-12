import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from lathe_easystep.presets.thread_presets import (
    METRIC_THREAD_PRESETS,
    TRAPEZOIDAL_THREAD_PRESETS,
    THREAD_PRESET_INDEX,
    get_thread_preset,
    validate_thread_preset_data,
)
from lathe_easystep.presets.din_relief_presets import (
    DIN_RELIEF_TABLE,
    get_din_relief_preset,
    get_thread_with_relief,
    validate_din_relief_preset_data,
)


def test_all_metric_and_trapezoidal_thread_presets_are_valid():
    for label, _diameter, _pitch in METRIC_THREAD_PRESETS + TRAPEZOIDAL_THREAD_PRESETS:
        preset = get_thread_preset(label)
        assert preset is not None, f"{label}: preset failed validation or is missing"
        assert not validate_thread_preset_data(preset), label


def test_thread_preset_index_has_no_duplicate_or_placeholder_entries():
    seen_majors = {}
    for label, entry in THREAD_PRESET_INDEX.items():
        assert entry["major"] > 0.0, label
        assert entry["pitch"] > 0.0, label
        key = (entry["profile"], round(entry["major"], 6))
        seen_majors.setdefault(key, []).append(label)


def test_all_din_relief_presets_are_structurally_valid():
    for size, sides in DIN_RELIEF_TABLE.items():
        for side_name, data in sides.items():
            errors = validate_din_relief_preset_data(data)
            assert not errors, f"{size}/{side_name}: {errors}"
            assert get_din_relief_preset(size, internal=(side_name == "internal")) is not None


def test_m30_relief_contains_norm_width_overlap_and_radius():
    external = get_din_relief_preset("M30", internal=False)
    internal = get_din_relief_preset("M30", internal=True)
    assert external is not None and internal is not None
    assert external["pitch"] == 3.5
    assert external["width"] == 12.0
    assert external["thread_overlap"] == 4.7
    assert external["radius"] == 1.6
    assert internal["width"] == 17.7
    assert external["bottom_width"] == 7.7
    assert internal["bottom_width"] == 14.0


def test_get_thread_with_relief_returns_side_metadata():
    combined = get_thread_with_relief("M20", internal=False)
    assert combined is not None
    assert combined["thread_size"] == "M20"
    assert combined["internal"] is False
    assert combined["side"] == "external"


def test_din_relief_coverage_no_longer_has_a_gap_for_half_size_metric_threads():
    """LES-019 2026-09-11: M2, M2.5 und zuletzt M3.5 waren die einzigen
    METRIC_THREAD_PRESETS-Groessen ohne DIN-76-Freistichdaten (TODO
    Prioritaet B #5). Alle drei sind jetzt belegt - M2/M2.5 per zwei
    unabhaengigen, sich exakt deckenden Quellen (DIN 76 T1 12.83 und DIN
    76-1:2016-08), M3.5 aus der P=0.6-Zeile derselben 1983er-Tabelle (per
    Tabellen-Fussnote fuer jedes Gewinde dieser Steigung gueltig, siehe
    Kommentar in din_relief_presets.py). Kein METRIC_THREAD_PRESETS-Eintrag
    ist mehr ohne Freistichdaten."""
    thread_sizes = {label for label, _, _ in METRIC_THREAD_PRESETS}
    relief_sizes = set(DIN_RELIEF_TABLE.keys())
    missing = thread_sizes - relief_sizes
    assert missing == set()


@pytest.mark.parametrize("size,internal,expected", [
    ("M2", False, {"pitch": 0.4, "diameter_delta": -0.7, "width": 1.4, "short_width": 1.0, "radius": 0.2}),
    ("M2", True, {"pitch": 0.4, "diameter_delta": 0.2, "width": 2.2, "short_width": 1.6, "radius": 0.2}),
    ("M2.5", False, {"pitch": 0.45, "diameter_delta": -0.7, "width": 1.6, "short_width": 1.1, "radius": 0.2}),
    ("M2.5", True, {"pitch": 0.45, "diameter_delta": 0.2, "width": 2.4, "short_width": 1.7, "radius": 0.2}),
])
def test_din_relief_m2_and_m2_5_match_din_76_t1_and_din_76_1_2016(size, internal, expected):
    """Gegen zwei unabhaengige, sich deckende Quellen verifiziert (DIN 76 T1
    12.83 "Tabellenbuch Metall"/Europa-Lehrmittel und DIN 76-1:2016-08
    "Technische Kommunikation" K54/handwerk-technik.de): Steigung,
    Freistichdurchmesser-Differenz, Breite (g2, Form A/C Regelfall),
    Kurzform-Breite (Form B/D) und Radius. `bottom_width`/`short_bottom_width`
    (g1) sind bewusst NICHT gegengeprueft - keine der beiden Quellen weist
    g1 direkt aus, siehe Code-Kommentar in din_relief_presets.py."""
    preset = get_din_relief_preset(size, internal=internal)
    assert preset is not None
    for key, value in expected.items():
        assert preset[key] == pytest.approx(value), f"{key}: {preset[key]} != {value}"


@pytest.mark.parametrize("internal,expected", [
    (False, {"pitch": 0.6, "diameter_delta": -1.0, "width": 2.1, "short_width": 1.5, "radius": 0.4}),
    (True, {"pitch": 0.6, "diameter_delta": 0.3, "width": 3.3, "short_width": 2.4, "radius": 0.4}),
])
def test_din_relief_m3_5_matches_din_76_t1_pitch_row(internal, expected):
    """M3.5 hat keine eigene Tabellenzeile in DIN 76 T1 12.83, aber genau die
    Steigung (P=0.6) der Zeile zwischen M3 und M4 - per Tabellen-Fussnote
    ("Fuer Feingewinde sind die Masse des Gewindefreistichs der einfachen
    Steigung P zu waehlen") fuer jedes Gewinde dieser Steigung gueltig.
    Absichtlich NICHT gegen die 2016-Ausgabe verifiziert (keine Daten fuer
    diese Steigung verfuegbar) - die Aussenwerte (Form A/B) der 1983er-Ausgabe
    lagen bei der direkten Nachbarzeile M3 ca. 0.05mm ueber der 2016er-Ausgabe,
    siehe Code-Kommentar in din_relief_presets.py."""
    preset = get_din_relief_preset("M3.5", internal=internal)
    assert preset is not None
    for key, value in expected.items():
        assert preset[key] == pytest.approx(value), f"{key}: {preset[key]} != {value}"
