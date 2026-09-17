import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.tools import parse_tool_table

# LES-052 Abschnitt 5 ("Werkzeugtabelle als eigene Domaene kapseln: Parser,
# normalisierte Werkzeuge, Parse-Warnungen, unbekannte Felder ..."):
# parse_tool_table() selbst hatte bislang ueberhaupt keine eigene
# Testdatei - nur Tool-Konstruktion und darauf aufbauende Pruefungen waren
# getestet, nicht der Parser.


def _write_tool_table(tmp_path, lines):
    path = tmp_path / "tool.tbl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_parses_known_fields_into_tool(tmp_path):
    filepath = _write_tool_table(tmp_path, ["T1 P1 D0.4 Q0 ; CNMG120408"])

    tools, _missing_iso = parse_tool_table(filepath)

    tool = tools[1]
    assert tool.t == 1
    assert tool.p == 1
    assert tool.d == 0.4
    assert tool.q == 0
    assert tool.comment == "CNMG120408"


def test_unknown_fields_are_preserved_not_discarded(tmp_path):
    """Bisheriger Zustand: X/Y/Z/A/B/C/U/V/W/I/J/R-Token (alles ausser
    T/P/D/Q) wurden nur in ein lokales token_map gelesen und danach
    stillschweigend verworfen - nie an das Tool-Objekt weitergegeben."""
    filepath = _write_tool_table(tmp_path, ["T2 P2 D0.8 Q1 R0.2 X1.5 ; DCMT110408"])

    tools, _ = parse_tool_table(filepath)

    tool = tools[2]
    assert tool.unknown_fields == {"R": "0.2", "X": "1.5"}


def test_known_fields_are_not_duplicated_into_unknown_fields(tmp_path):
    filepath = _write_tool_table(tmp_path, ["T3 P3 D0.4 Q4 ; MGMN200"])

    tools, _ = parse_tool_table(filepath)

    tool = tools[3]
    assert tool.unknown_fields == {}


def test_tool_without_any_extra_tokens_has_empty_unknown_fields(tmp_path):
    filepath = _write_tool_table(tmp_path, ["T4 P4 ; plain"])

    tools, _ = parse_tool_table(filepath)

    assert tools[4].unknown_fields == {}
