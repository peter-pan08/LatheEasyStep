"""Regression for the language-wiring gap found during the ID-only full
audit (2026-09-21/2026-09-22): build_gcode_lines() (ui_flow.py) - the
actual 'Programm erzeugen'/write_gcode_file() entry point - previously
never put "lang" into program_settings, so gcode_comment() always fell
back to German regardless of the selected UI language. These tests drive
the real build_gcode_lines() call path (not generate_program_gcode() in
isolation, which was already covered) with a synthetic but real
HandlerClass instance, only substituting _current_language_code() the way
several other tests in this suite already do for language-dependent
behaviour (see tests/test_preview_safety_and_language.py)."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from types import SimpleNamespace

from lathe_easystep.examples import example_programs
from lathe_easystep.model import ProgramModel
from lathe_easystep.ui_flow import build_gcode_lines
from lathe_easystep_handler import HandlerClass


def _make_handler(lang):
    operations, settings = example_programs()["Bohren.ngc"]
    header = dict(settings)
    handler = object.__new__(HandlerClass)
    handler.model = ProgramModel()
    handler.model.operations = list(operations)
    handler._tool_table = SimpleNamespace(tools={})
    handler._collect_program_header = lambda: dict(header)
    handler._current_language_code = lambda: lang
    return handler


def _non_comment_lines(lines):
    """Die technische G-Code-Struktur ohne Kommentarzeilen - muss zwischen
    Sprachen identisch bleiben, nur `(...)`-Kommentare duerfen abweichen."""
    return [line for line in lines if not line.strip().startswith("(")]


def test_ui_path_uses_german_when_language_combo_reports_german():
    lines = build_gcode_lines(_make_handler("de"))
    assert "(Anfahren vor Zyklus)" in lines


def test_ui_path_uses_english_when_language_combo_reports_english():
    lines = build_gcode_lines(_make_handler("en"))
    assert "(Approach before cycle)" in lines
    assert "(Anfahren vor Zyklus)" not in lines


def test_ui_path_uses_spanish_when_language_combo_reports_spanish():
    lines = build_gcode_lines(_make_handler("es"))
    assert "(Aproximacion antes del ciclo)" in lines
    assert "(Anfahren vor Zyklus)" not in lines
    assert "(Approach before cycle)" not in lines


def test_language_switch_without_reloading_program_takes_effect_immediately():
    """Derselbe Handler (dasselbe Modell, nicht neu geladen) - nur die
    Sprachauswahl aendert sich zwischen zwei build_gcode_lines()-Aufrufen,
    wie bei einem Sprachwechsel im laufenden Panel ohne Programmneuladen."""
    handler = _make_handler("de")
    de_lines = build_gcode_lines(handler)
    assert "(Anfahren vor Zyklus)" in de_lines

    handler._current_language_code = lambda: "en"
    en_lines = build_gcode_lines(handler)
    assert "(Approach before cycle)" in en_lines
    assert "(Anfahren vor Zyklus)" not in en_lines


def test_technical_structure_is_identical_across_languages():
    """Nur lokalisierbare Kommentare duerfen sich unterscheiden - die
    eigentliche G-Code-Struktur (Bewegungen, Woerter, Zahlen ausserhalb von
    Kommentaren) muss zwischen den Sprachen byte-identisch bleiben."""
    de_lines = build_gcode_lines(_make_handler("de"))
    en_lines = build_gcode_lines(_make_handler("en"))
    es_lines = build_gcode_lines(_make_handler("es"))

    de_code = _non_comment_lines(de_lines)
    en_code = _non_comment_lines(en_lines)
    es_code = _non_comment_lines(es_lines)

    assert de_code == en_code == es_code
    assert len(de_code) > 0
    # Volle Zeilenzahl (inkl. Kommentare) bleibt gleich - nur der
    # Kommentarinhalt selbst unterscheidet sich, keine Zeilen kommen hinzu
    # oder fallen weg.
    assert len(de_lines) == len(en_lines) == len(es_lines)
    assert de_lines != en_lines
    assert de_lines != es_lines


def test_program_settings_lang_is_not_persisted_into_saved_program_data():
    """.lse-Programme werden dadurch nicht sprachabhaengig: build_program_data()
    (Speicherpfad) ruft _collect_program_header() unabhaengig und ohne
    'lang' erneut auf, statt handler.model.program_settings wiederzuverwenden."""
    from lathe_easystep.ui_persistence import build_program_data

    handler = _make_handler("en")
    build_gcode_lines(handler)  # setzt handler.model.program_settings["lang"]
    assert handler.model.program_settings.get("lang") == "en"

    handler._update_selected_operation = lambda **_kw: None
    handler._rebuild_all_operation_geometry = lambda: None
    handler._program_file_meta = lambda: {}
    program_data = build_program_data(handler)
    assert "lang" not in program_data.get("header", program_data)
    assert "lang" not in program_data
