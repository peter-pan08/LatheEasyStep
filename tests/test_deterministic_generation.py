"""LES-054 Deterministische Programmerzeugung - expliziter Vertrag:

    Dieselben normalisierten fachlichen Programmdaten muessen denselben
    technischen G-Code erzeugen - unabhaengig von Eingabeweg, Vorschau-
    Nutzung, Theme/Ressourcenwahl, Sprache und Embedded-/Standalone-Betrieb.

"Technischer G-Code" bedeutet: alles ausser dem reinen Kommentartext in
Klammern `(...)`. Kommentartext ist bewusst sprachabhaengig (LES-044-
Entscheidung, siehe test_gcode_comments_are_language_dependent.py) und
gehoert deshalb NICHT zum technischen Vergleich - wohl aber die Anzahl und
Position der Kommentare selbst (ein Kommentar, der in einer Sprache
verschwindet oder an anderer Stelle steht, waere trotzdem ein Fehler).
Dateipfade (`meta`/`__program_file_path` etc.) und Zeitstempel sind
untersucht worden: keine Zeitstempel existieren im gesamten Generator-/
Persistenzpfad (kein `datetime`/`time.time()`/`.now()`), und Dateipfade
werden ausschliesslich in `meta` gefuehrt, niemals an `generate_program_
gcode()` uebergeben - beide sind fuer den G-Code-Vergleich irrelevant, weil
sie ihn nachweislich nie erreichen.

Bereits bestehende Nachweise, hier NICHT dupliziert:
- Speichern/Laden bewahrt die Operationsdaten (nicht den G-Code):
  test_regression_contracts.py::test_example_programs_roundtrip_through_program_payload
- Vorschau-Widget-Zustand (auch bewusst kaputte Werte) beeinflusst den
  G-Code nicht: test_regression_contracts.py::test_gcode_unaffected_by_preview_widget_rendering_cache
- Werkzeug-Darstellungsressourcen (Theme) beeinflussen den G-Code nicht,
  ueber ALLE Beispielprogramme: test_tool_preview_layout.py::
  test_switching_tool_visual_resource_never_affects_generated_gcode
- Der Generator selbst ist bei gleichen Objekten wiederholbar und
  mutiert seine Eingabe nicht: test_generation_boundaries.py::
  test_generation_is_repeatable_and_leaves_input_unchanged

Neu ergaenzt in dieser Datei (echte Luecken, siehe LES-054-Audit
2026-09-20):
1. Speichern -> Laden -> Erzeugen tatsaechlich auf G-Code-Ebene verglichen
   (nicht nur Datenaequivalenz wie im bestehenden Test oben).
2. Format-v1-Migration erzeugt denselben G-Code wie nativ gespeichertes
   Format v2 (LES-053).
3. Sprachwechsel aendert nachweislich nur Kommentartext, nicht den
   technischen G-Code.
4. Embedded- und Standalone-Kontext (der einzige strukturelle
   Unterschied ist `handler.root_widget`, siehe
   test_embedded_vs_standalone_root_resolution.py) erzeugen aus
   identischen normalisierten Daten identischen G-Code.

Untersucht und als unproblematisch bestaetigt (kein Fund, keine
Aenderung): `id()`-basierte interne Korrelation in `gcode_program.py`
(Freistich-Zuordnung ueber `id(thread_op)`/`id(feature)`) wird
ausschliesslich fuer Mitgliedschafts-/Lookup-Pruefungen innerhalb EINES
Generatorlaufs verwendet, nie fuer Iterationsreihenfolge, die die Ausgabe
beeinflusst - `automatic_reliefs` bleibt eine Liste in `operations`-
Reihenfolge, Subroutinen-Referenzen werden explizit sortiert
(`sorted(contour_sub_blocks)`). Keine Non-Determinismus-Quelle gefunden.
"""
import copy
import os
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import ProgramModel
from lathe_easystep.persistence import build_program_data, step_data_to_operation
from lathe_easystep.storage import CURRENT_FORMAT_VERSION, parse_program_payload
from lathe_easystep.tools import Tool
from lathe_easystep.ui_flow import build_gcode_lines
from lathe_easystep_handler import HandlerClass


def _generate(operations, settings):
    return generate_program_gcode(copy.deepcopy(operations), dict(settings))


# ---------------------------------------------------------------------------
# 1. direkt erzeugen -> Programm speichern -> laden -> erneut erzeugen
# ---------------------------------------------------------------------------

def test_save_load_roundtrip_produces_identical_gcode_for_all_example_programs():
    """Ergaenzt test_example_programs_roundtrip_through_program_payload
    (prueft nur, dass op_type/params/path nach dem Rundlauf gleich bleiben)
    um den eigentlich geforderten Vergleich: der aus den geladenen Daten
    erzeugte G-Code muss mit dem urspruenglich erzeugten G-Code identisch
    sein, nicht nur die zugrundeliegenden Datenstrukturen."""
    for filename, (operations, settings) in example_programs().items():
        gcode_before = _generate(operations, settings)

        payload = build_program_data(operations, dict(settings), {"source": filename})
        assert payload["version"] == CURRENT_FORMAT_VERSION
        header, ops_data, _program_path, _gcode_path = parse_program_payload(payload, filename)
        restored_ops = [op for op in (step_data_to_operation(d) for d in ops_data) if op is not None]

        gcode_after = generate_program_gcode(restored_ops, dict(header))
        assert gcode_after == gcode_before, filename


# ---------------------------------------------------------------------------
# 2. Format-v1 laden/migrieren -> erzeugen vs. nativer v2-Zustand -> erzeugen
# ---------------------------------------------------------------------------

def _fixed_tool_table():
    return {
        1: Tool(
            t=1, p=1, d=0.4, q=0, comment="CNMG120408", iso_code="CNMG1204",
            iso_size="1204", radius_mm=0.4, kind="turning",
        ),
    }


def test_migrated_v1_program_produces_identical_gcode_to_native_v2_program():
    """LES-053/LES-054: Abdrehen.ngc referenziert Tool 1 - ideal, um zu
    pruefen, dass eine aus Format v1 migrierte Operation (ohne Werkzeug-
    Snapshot, da der erst mit v2/LES-032 existiert) denselben G-Code
    erzeugt wie dieselben normalisierten Daten, wenn sie nativ als v2
    gespeichert wurden (MIT Snapshot) - solange die aktuell geladene
    Tooltable mit dem Snapshot uebereinstimmt (keine erkannte Abweichung,
    also keine zusaetzliche Warnzeile im G-Code-Kopf)."""
    operations, settings = example_programs()["Abdrehen.ngc"]
    header = dict(settings)
    tools = _fixed_tool_table()

    # Format v1: kein Werkzeug-Snapshot moeglich (existierte vor v2).
    from lathe_easystep.persistence import operation_to_step_data
    v1_ops_data = [operation_to_step_data(op) for op in operations]
    v1_payload = {"version": 1, "header": dict(header), "operations": v1_ops_data, "meta": {}}
    migrated_header, migrated_ops_data, _p1, _g1 = parse_program_payload(v1_payload, "legacy.lse")
    migrated_ops = [op for op in (step_data_to_operation(d) for d in migrated_ops_data) if op is not None]
    assert all("tool_snapshot" not in (op.params or {}) for op in migrated_ops)
    settings_from_v1 = dict(migrated_header)
    settings_from_v1["tools"] = tools
    gcode_from_v1 = generate_program_gcode(copy.deepcopy(migrated_ops), settings_from_v1)

    # Nativ Format v2: derselbe Speichervorgang mit geladener Tooltable
    # stempelt einen Snapshot, der exakt der aktuellen Tabelle entspricht.
    v2_payload = build_program_data(operations, dict(header), {}, tools)
    assert v2_payload["version"] == CURRENT_FORMAT_VERSION
    v2_header, v2_ops_data, _p2, _g2 = parse_program_payload(v2_payload, "native.lse")
    v2_ops = [op for op in (step_data_to_operation(d) for d in v2_ops_data) if op is not None]
    assert any(op.params.get("tool_snapshot") for op in v2_ops)
    settings_from_v2 = dict(v2_header)
    settings_from_v2["tools"] = tools
    gcode_from_v2 = generate_program_gcode(copy.deepcopy(v2_ops), settings_from_v2)

    assert gcode_from_v1 == gcode_from_v2


# ---------------------------------------------------------------------------
# 3. Sprachwechsel -> erneut erzeugen (nur Kommentartext darf sich aendern)
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r"\([^)]*\)")


def _strip_comment_text(line: str) -> str:
    """Ersetzt jeden Klammerkommentar durch einen neutralen Platzhalter:
    Anzahl/Position von Kommentaren bleibt vergleichbar, ihr (bewusst
    sprachabhaengiger) Text wird ignoriert."""
    return _COMMENT_RE.sub("(...)", line).rstrip()


def test_language_switch_changes_only_comment_text_not_technical_gcode():
    """LES-044-Entscheidung: Kommentare sind sprachabhaengig. LES-054
    verlangt, dass das die einzige Aenderung ist - jede Bewegungs-/Modal-/
    Zyklus-/Parameterzeile muss zwischen Deutsch, Englisch und Spanisch
    technisch identisch bleiben."""
    for filename, (operations, settings) in example_programs().items():
        variants = {}
        for lang in ("de", "en", "es"):
            s = dict(settings)
            s["lang"] = lang
            variants[lang] = [_strip_comment_text(line) for line in _generate(operations, s)]
        assert variants["de"] == variants["en"], filename
        assert variants["de"] == variants["es"], filename

    # Gegenprobe: mindestens eine Datei muss tatsaechlich unterschiedlichen
    # (nicht nur zufaellig identischen) Kommentartext zwischen den Sprachen
    # haben - sonst waere der Vergleich oben wirkungslos.
    ops, settings = example_programs()["Abdrehen.ngc"]
    de_raw = _generate(ops, dict(settings, lang="de"))
    en_raw = _generate(ops, dict(settings, lang="en"))
    assert de_raw != en_raw


# ---------------------------------------------------------------------------
# 4. Embedded und Standalone gegen dieselben normalisierten Daten
# ---------------------------------------------------------------------------

def test_embedded_and_standalone_produce_identical_gcode_from_same_normalized_data():
    """build_gcode_lines() (ui_flow.py) ist der gemeinsame Aufrufpfad fuer
    Embedded- und Standalone-Start. Er liest nachweislich (Codelesung)
    nirgends `handler.root_widget` oder eine andere Embedding-spezifische
    Eigenschaft - nur `_collect_program_header()`, `_tool_table.tools` und
    `model.operations`. `root_widget` ist strukturell der einzige
    Unterschied zwischen Embedded und Standalone (siehe
    test_embedded_vs_standalone_root_resolution.py). Dieser Test haelt das
    als Regression fest: bei identischer `_collect_program_header()`-
    Antwort und identischem Modell unterscheidet sich der erzeugte G-Code
    nicht danach, ob `root_widget` auf `None` (Standalone) oder ein
    fremdes Host-Fenster (Embedded) zeigt."""
    _filename, (operations, settings) = next(iter(example_programs().items()))
    header = dict(settings)

    def _make_handler(root_widget):
        handler = object.__new__(HandlerClass)
        handler.model = ProgramModel()
        handler.model.operations = copy.deepcopy(operations)
        handler._tool_table = SimpleNamespace(tools={})
        handler._collect_program_header = lambda: dict(header)
        handler.root_widget = root_widget
        return handler

    standalone_handler = _make_handler(None)
    embedded_host = SimpleNamespace(objectName=lambda: "qtdragon_lathe_host")
    embedded_handler = _make_handler(embedded_host)

    gcode_standalone = build_gcode_lines(standalone_handler)
    gcode_embedded = build_gcode_lines(embedded_handler)

    assert gcode_standalone == gcode_embedded
