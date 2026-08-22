import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def test_din_relief_coverage_gap_for_half_size_metric_threads_is_known():
    """Dokumentiert eine bestehende Luecke (TODO Prioritaet B #5): M2/M2.5/M3.5
    haben Gewinde-Presets, aber (noch) keine DIN-76-Freistich-Vorschlaege, weil
    dafuer eine verifizierte Normtabelle noetig ist statt geschaetzter Werte.
    Dieser Test dokumentiert den Stand bewusst, statt ihn stillschweigend zu
    uebernehmen oder mit ungeprueften Zahlen zu schliessen."""
    thread_sizes = {label for label, _, _ in METRIC_THREAD_PRESETS}
    relief_sizes = set(DIN_RELIEF_TABLE.keys())
    missing = thread_sizes - relief_sizes
    assert missing == {"M2", "M2.5", "M3.5"}
    for label in missing:
        assert get_din_relief_preset(label) is None
