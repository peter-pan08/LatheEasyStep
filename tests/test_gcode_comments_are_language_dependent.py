import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode

# LES-044 Entscheidung (2026-09-14): G-Code-Werkstattkommentare sind jetzt
# sprachabhaengig. Diese Tests laufen End-to-End durch den echten
# Generatorpfad (nicht die einzelnen gcode_*.py-Funktionen isoliert, die
# viele injizierte Callables brauchen) und pruefen an je einer Operation pro
# konvertierter Datei: (a) Deutsch bleibt exakt der bisherige Text (Default
# ohne "lang" bleibt unveraendert - siehe test_tool_table_completeness_check.py
# fuer dasselbe Prinzip bei anderen Aenderungen), (b) Englisch unterscheidet
# sich tatsaechlich.


def _lines_for(example_name: str, lang: str | None):
    ops, settings = example_programs()[example_name]
    settings = dict(settings)
    if lang is not None:
        settings["lang"] = lang
    return generate_program_gcode(ops, settings)


def _joined(lines):
    return "\n".join(lines)


def test_drill_approach_comment_is_translated():
    de = _joined(_lines_for("Bohren.ngc", None))
    en = _joined(_lines_for("Bohren.ngc", "en"))
    assert "(Anfahren vor Zyklus)" in de
    assert "(Approach before cycle)" in en
    assert "(Anfahren vor Zyklus)" not in en


def test_face_approach_comment_is_translated():
    de = _joined(_lines_for("Planen.ngc", None))
    en = _joined(_lines_for("Planen.ngc", "en"))
    assert "(Anfahren vor Zyklus)" in de
    assert "(Approach before cycle)" in en


def test_groove_approach_comment_is_translated():
    de = _joined(_lines_for("Einstich.ngc", None))
    en = _joined(_lines_for("Einstich.ngc", "en"))
    assert "(Anfahren vor Groove)" in de
    assert "(Approach before groove)" in en


def test_thread_comments_are_translated():
    de = _joined(_lines_for("Gewinde.ngc", None))
    en = _joined(_lines_for("Gewinde.ngc", "en"))
    assert "(Anfahren vor Gewinde)" in de
    assert "(Approach before thread)" in en
    assert "Gewindetyp" in de
    assert "Thread type" in en


def test_program_header_safety_block_is_translated():
    de = _joined(_lines_for("Abdrehen.ngc", None))
    en = _joined(_lines_for("Abdrehen.ngc", "en"))
    assert "(Programm automatisch erzeugt)" in de
    assert "(Program generated automatically)" in en
    assert "SICHERHEITSPARAMETER" in de
    assert "SAFETY PARAMETERS" in en
    assert "Rueckzugsebenen" in de
    assert "Retract planes" in en


def test_toolchange_and_start_condition_comments_are_translated():
    de = _joined(_lines_for("Abdrehen.ngc", None))
    en = _joined(_lines_for("Abdrehen.ngc", "en"))
    assert "STARTBEDINGUNG" in de
    assert "START CONDITION" in en
    assert "Erster Werkzeugwechsel" in de
    assert "First tool change" in en
    assert "Werkzeugwechselpunkt" in de
    assert "Tool change point" in en


def test_roughing_strategy_and_allowance_comments_are_translated():
    de = _joined(_lines_for("Innen_Stufe.ngc", None))
    en = _joined(_lines_for("Innen_Stufe.ngc", "en"))
    assert "(Strategie: parallel_z)" in de
    assert "(Strategy: parallel_z)" in en
    assert "Schlichtaufmass" in de
    assert "Finish allowance" in en


def test_abspanen_rough_label_is_translated():
    de = _joined(_lines_for("Innen_Stufe.ngc", None))
    en = _joined(_lines_for("Innen_Stufe.ngc", "en"))
    assert "(ABSPANEN)" in de  # unveraendert - ABSPANEN ist der feste Operationsname
    assert "ABSPANEN Rough" in de or "Schlichtschnitt Kontur" in de
    assert "ABSPANEN rough" in en or "Finish pass contour" in en


def test_missing_lang_key_defaults_to_the_historic_german_text():
    """settings ohne 'lang' (z. B. Referenzregeneration, aeltere Aufrufer)
    darf sich nicht aendern - das war die bisherige, feste Sprache."""
    with_key = _joined(_lines_for("Bohren.ngc", "de"))
    without_key = _joined(_lines_for("Bohren.ngc", None))
    assert with_key == without_key


def test_spanish_translation_also_differs_from_german_and_english():
    de = _joined(_lines_for("Einstich.ngc", None))
    en = _joined(_lines_for("Einstich.ngc", "en"))
    es = _joined(_lines_for("Einstich.ngc", "es"))
    assert "(Aproximacion antes del ranurado)" in es
    assert es != de
    assert es != en
