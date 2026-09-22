"""Regressions for the structured checks.py warnings (ID-only-Vollaudit
2026-09-21): validate_program_setup()/radius_warning_details() must return
stable keys+params, never localized prose - translation only happens at
format_warning(), the display boundary. Domain logic (tests filtering by
substring before this change) must not depend on language-specific text."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import format_warning
from lathe_easystep.gcode_utils import gcode_comment


def test_format_warning_translates_simple_key_across_languages():
    warning = {"key": "warning.thread_start_end_identical", "params": {}}
    de = format_warning(warning, "de")
    en = format_warning(warning, "en")
    es = format_warning(warning, "es")
    assert de == "Gewindestart und Gewindeende sind identisch"
    assert en == "Thread start and thread end are identical"
    assert es == "El inicio y el fin de la rosca son identicos"
    assert len({de, en, es}) == 3  # tatsaechlich unterschiedlich, keine Kopien


def test_format_warning_tool_kind_mismatch_resolves_nested_labels():
    """kind/op_type bleiben rohe Enum-Werte in den Parametern (siehe
    tests/test_tool_kind_mismatch_check.py) - erst format_warning() loest
    sie in sichtbare, sprachabhaengige Labels auf."""
    warning = {
        "key": "warning.tool_kind_mismatch",
        "params": {"tool_num": 5, "orientation": 1, "kind": "drilling", "idx": 2, "op_type": "groove"},
    }
    de = format_warning(warning, "de")
    en = format_warning(warning, "en")
    assert "T05" in de and "Bohrwerkzeug" in de and "Stech-Operation" in de
    assert "T05" in en and "drilling tool" in en and "grooving operation" in en


def test_format_warning_unnamed_preset_label_fallback_is_translated():
    warning = {
        "key": "warning.thread_preset_pitch_mismatch",
        "params": {"label": "", "preset_value": 3.5, "actual_value": 1.75},
    }
    de = format_warning(warning, "de")
    en = format_warning(warning, "en")
    assert "(unbenannt)" in de
    assert "(unnamed)" in en


def test_format_warning_thread_preset_field_conflicts_joins_translated_fields():
    warning = {
        "key": "warning.thread_preset_field_conflicts",
        "params": {
            "label": "M10",
            "conflicts": [
                {"field_key": "thread_depth", "actual": 9.0, "target": 8.8},
                {"field_key": "infeed_q", "actual": 15.0, "target": 14.0},
            ],
        },
    }
    de = format_warning(warning, "de")
    en = format_warning(warning, "en")
    assert "Gewindetiefe" in de and "Zustellwinkel Q" in de
    assert "thread depth" in en and "infeed angle Q" in en


def test_format_warning_tool_radius_unknown_empty_comment_fallback():
    warning = {"key": "warning.tool_radius_unknown", "params": {"idx": 1, "tool_num": 3, "comment": ""}}
    de = format_warning(warning, "de")
    en = format_warning(warning, "en")
    assert "kein Kommentar" in de
    assert "no comment" in en


_ALL_CHECKS_WARNING_KEYS = {
    "warning.drill_before_internal_machining",
    "warning.duplicate_operation",
    "warning.tool_kind_mismatch",
    "warning.tool_width_mismatch",
    "warning.tool_snapshot_radius_changed",
    "warning.tool_snapshot_orientation_changed",
    "warning.tool_snapshot_width_changed",
    "warning.groove_reaches_chuck_no_go_zone",
    "warning.tool_looks_internal_op_external",
    "warning.tool_looks_external_op_internal",
    "warning.thread_g76_invalid_pitch_length",
    "warning.thread_g76_negative_depth",
    "warning.thread_start_end_identical",
    "warning.thread_start_outside_stock",
    "warning.thread_end_outside_stock",
    "warning.thread_preset_pitch_mismatch",
    "warning.thread_preset_major_mismatch",
    "warning.thread_preset_field_conflicts",
    "warning.thread_preset_field_conflict_item",
    "warning.dangling_contour_reference",
    "warning.din_relief_missing_thread_size",
    "warning.din_relief_missing_side",
    "warning.groove_tool_wider_than_relief",
    "warning.relief_separate_no_tool",
    "warning.relief_separate_tool_mismatch",
    "warning.retract_plane_not_set",
    "warning.tool_radius_unknown",
    "warning.unnamed_preset_label",
    "warning.no_tool_comment",
}

_LOOKUP_KEYS = (
    {f"tool.kind.{k}" for k in ("turning", "drilling", "grooving", "threading", "parting")}
    | {f"optype.{k}" for k in ("face", "turn", "bore", "abspanen", "thread", "groove", "drill")}
    | {
        f"field.{k}"
        for k in ("thread_depth", "first_depth", "peak_offset", "retract_r", "infeed_q", "spring_passes", "e", "l")
    }
)


def test_all_warning_and_lookup_keys_exist_in_every_language():
    """Kein Schluessel darf auf sich selbst zurueckfallen (== fehlender
    .lng-Eintrag) - fuer alle drei Sprachen."""
    for lang in ("de", "en", "es"):
        for key in _ALL_CHECKS_WARNING_KEYS | _LOOKUP_KEYS:
            text = gcode_comment(key, lang)
            assert text != key, f"missing .lng entry for {key!r} ({lang})"
            assert text.strip(), f"empty .lng entry for {key!r} ({lang})"
