"""Tests fuer den Arbeitsblock "Werkzeugwechsel und Programmabschluss"
(2026-09-23):

1. Werkzeugoffset-Aktivierung: laut installierter LinuxCNC-Dokumentation
   (docs/src/lathe/lathe-user.adoc, docs/src/gcode/g-code.adoc "G43 Tool
   Length Offset") aktivieren weder Tn noch M6 den Werkzeugoffset aus der
   Tooltable - das dokumentierte Muster ist "Tn M6 G43", auch fuer
   Drehmaschinen. G43 H<n> muss nach JEDEM Tn M6 stehen, auch wenn
   #<_current_tool> == n am Programmstart bereits gilt (der Skip-Zweig
   garantiert keinen aktiven Offset).
2. Werkzeugwechselposition: neue Auswahl LES (bisheriges XT/ZT-Verhalten)
   vs. LinuxCNC/Maschine (keine XT/ZT-Fahrt, aber unveraendert sichere
   Rueckzuege, Tn M6, G43).
3. Programmende: park_mode um "program_start" erweitert (Position bei
   Programmstart, ueber LinuxCNC-Interpreterparameter #<_x>/#<_z> zur
   LAUFZEIT erfasst und zurueckgeschrieben, nie ein zur Erzeugungszeit in
   Python berechneter Literalwert). Ausserdem behobener Bug: build_gcode_lines()
   (ui_flow.py, der tatsaechliche "Programm erzeugen"-Pfad) ueberschrieb
   footer_lines bisher IMMER mit der Werkzeugwechselposition, wodurch die
   bereits vorhandene get_end_park_lines()-Logik (gcode_safety.py) fuer
   "Freie Parkposition" in der echten UI faktisch nie erreichbar war.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from types import SimpleNamespace

from lathe_easystep.examples import example_programs, make_program_settings
from lathe_easystep.gcode_safety import get_end_park_lines
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.persistence import build_program_data
from lathe_easystep.storage import parse_program_payload
from lathe_easystep.ui_flow import build_gcode_lines
from lathe_easystep_handler import HandlerClass


# ---------------------------------------------------------------------------
# 1. Werkzeugoffset-Aktivierung (G43)
# ---------------------------------------------------------------------------


def test_first_tool_gets_offset_activated_when_not_previously_loaded():
    """Erster Werkzeugbedarf: der Wechsel-Zweig (innerhalb des von
    LinuxCNC zur Laufzeit ausgewerteten if/endif) endet mit T<n> M6, und
    G43 H<n> steht unbedingt direkt nach dem endif - LinuxCNC entscheidet
    zur Laufzeit anhand von #<_current_tool>, ob der Wechsel-Zweig
    ueberhaupt ausgefuehrt wird; G43 muss in jedem Fall laufen."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "FirstToolInactive"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    if_idx = lines.index("o<les_first_tool> if [#<_current_tool> NE 3]")
    endif_idx = lines.index("o<les_first_tool> endif")
    assert lines[endif_idx - 1] == "T03 M6"
    assert if_idx < endif_idx
    assert lines[endif_idx + 1] == "G43 H3"


def test_first_tool_offset_is_activated_even_when_already_loaded():
    """Erster Werkzeugbedarf bereits aktiv: #<_current_tool> == n am
    Programmstart garantiert NICHT, dass der passende Werkzeugoffset schon
    aktiv ist (z. B. G43/G49 aus einem vorherigen Programm oder nach dem
    Einschalten) - G43 H<n> muss deshalb unbedingt ausserhalb des
    if/endif stehen, nicht nur im Wechsel-Zweig."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "FirstToolActive"}),
        Operation(OpType.TURN, {"tool": 5, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    endif_idx = lines.index("o<les_first_tool> endif")
    assert lines[endif_idx + 1] == "G43 H5"
    # G43 selbst steht bewusst NICHT im bedingten if-Zweig - es muss immer
    # ausgefuehrt werden, unabhaengig davon, ob LinuxCNC den Vergleich zur
    # Laufzeit als wahr oder falsch auswertet.
    if_idx = lines.index("o<les_first_tool> if [#<_current_tool> NE 5]")
    assert if_idx < endif_idx < lines.index("G43 H5")


def test_same_tool_change_is_skipped_without_redundant_offset():
    """T3 -> T3: kein unnoetiger Wechsel, kein zusaetzliches G43 (der
    zuvor per G43 aktivierte Offset gilt innerhalb desselben Programmlaufs
    unveraendert weiter)."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SameTool"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(18.0, -2.0), (16.0, -4.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert lines.count("T03 M6") == 1
    assert lines.count("G43 H3") == 1


def test_different_tool_change_activates_new_offset():
    """T3 -> T5: Wechsel wird angefordert, inkl. eigenem G43 H5 fuer das
    neue Werkzeug."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "DifferentTool"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
        Operation(OpType.DRILL, {"tool": 5, "spindle": 900.0, "feed": 0.08, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -10.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert lines.count("T03 M6") == 1
    assert lines.count("T05 M6") == 1
    m6_idx = lines.index("T05 M6")
    assert lines[m6_idx + 1] == "G43 H5"


# ---------------------------------------------------------------------------
# 2. Werkzeugwechselposition: LES vs. LinuxCNC
# ---------------------------------------------------------------------------


def test_toolchange_position_mode_les_keeps_existing_behavior():
    """Modus LES (Default, Rueckwaertskompatibilitaet fuer alte .lse ohne
    dieses Feld): unveraendertes Verhalten - sicherer Rueckzug, XT/ZT-Fahrt,
    Tn M6, G43."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "LesMode"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert "G53 G0 X150.000 Z300.000" in lines or "G0 X150.000 Z300.000" in lines
    endif_idx = lines.index("o<les_first_tool> endif")
    assert lines[endif_idx - 1] == "T03 M6"
    assert lines[endif_idx + 1] == "G43 H3"


def test_toolchange_position_mode_linuxcnc_omits_xt_zt_move():
    """Modus LinuxCNC: keine XT/ZT-Fahrt, aber sicherer Rueckzug (M5/M9),
    Tn M6 und G43 bleiben LES-Aufgabe."""
    # park_mode bewusst auf "end_position" gesetzt: der Default-park_mode
    # ("toolchange") wuerde am PROGRAMMENDE unabhaengig vom
    # toolchange_position_mode weiterhin XT/ZT verwenden (das ist die
    # separate Endpositions-Auswahl) - dieser Test isoliert die reine
    # Werkzeugwechselpunkt-Fahrt.
    settings = make_program_settings()
    settings.update({"toolchange_position_mode": "linuxcnc", "park_mode": "end_position", "park_x": 5.0, "park_z": 6.0})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "LinuxCncMode"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert "G0 X150.000 Z300.000" not in lines
    assert "G53 G0 X150.000 Z300.000" not in lines
    assert "M5" in lines
    assert "M9" in lines
    endif_idx = lines.index("o<les_first_tool> endif")
    assert lines[endif_idx - 2:endif_idx] == ["M9", "T03 M6"]
    assert lines[endif_idx + 1] == "G43 H3"


def test_toolchange_position_mode_linuxcnc_applies_to_every_change_not_only_first():
    settings = make_program_settings()
    settings.update({"toolchange_position_mode": "linuxcnc", "park_mode": "end_position", "park_x": 5.0, "park_z": 6.0})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "LinuxCncModeMulti"}),
        Operation(OpType.TURN, {"tool": 3, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
        Operation(OpType.DRILL, {"tool": 5, "spindle": 900.0, "feed": 0.08, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -10.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert "G0 X150.000 Z300.000" not in lines
    assert "G53 G0 X150.000 Z300.000" not in lines
    assert lines.count("T03 M6") == 1
    assert lines.count("T05 M6") == 1
    assert lines.count("G43 H3") == 1
    assert lines.count("G43 H5") == 1


def test_toolchange_position_mode_linuxcnc_still_retracts_from_internal_op():
    """Innen-Sicherheitsrueckzug vor dem Werkzeugwechsel bleibt auch im
    LinuxCNC-Modus erhalten - nur die XT/ZT-Fahrt entfaellt."""
    settings = make_program_settings()
    settings.update({"toolchange_position_mode": "linuxcnc", "xri": 9.0, "zri": 1.0, "xri_absolute": True, "zri_absolute": True})
    operations = [
        Operation(OpType.DRILL, {"tool": 10, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0)]),
        Operation(OpType.ABSPANEN, {"tool": 11, "side": "inside", "spindle": 1200.0, "feed": 0.12, "depth_per_pass": 1.0, "mode": "rough", "slice_strategy": "parallel_z"}, path=[(10.0, 0.0), (19.2, -30.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    m6_idx = lines.index("T11 M6")
    prelude = lines[max(0, m6_idx - 6):m6_idx]
    assert "M5" in prelude
    assert "M9" in prelude
    assert not any("150.000" in line or "300.000" in line for line in prelude)


# ---------------------------------------------------------------------------
# 3. Programmende: drei Varianten, ueber generate_program_gcode() (isoliert)
# ---------------------------------------------------------------------------


def test_end_park_lines_toolchange_default_unchanged():
    settings = make_program_settings()
    lines = get_end_park_lines(settings)
    assert lines[0] == "(Werkzeugwechselpunkt am Ende)"
    assert lines[1] in ("G0 X150.000 Z300.000", "G53 G0 X150.000 Z300.000")


def test_end_park_lines_defined_end_position():
    settings = make_program_settings()
    settings.update({"park_mode": "end_position", "park_x": 12.0, "park_z": 34.0})
    lines = get_end_park_lines(settings)
    assert lines == ["(Parkposition am Ende)", "G0 X12.000 Z34.000"]


def test_end_park_lines_program_start_uses_runtime_parameters_not_a_literal():
    """Keine Position aus dem Zeitpunkt der G-Code-Erzeugung: die
    Rueckkehr-Zeile muss ein Interpreter-Ausdruck sein (#<_les_start_x>/
    #<_les_start_z>), niemals ein von Python vorberechneter Zahlenwert."""
    settings = make_program_settings()
    settings["park_mode"] = "program_start"
    lines = get_end_park_lines(settings)
    assert lines == ["(Rueckkehr zur Position bei Programmstart)", "G0 X[#<_les_start_x>*2] Z[#<_les_start_z>]"]
    # X wird verdoppelt (Radius -> Durchmesser fuer G7), Z nicht.
    assert "*2" in lines[1].split("Z")[0]
    assert "*2" not in lines[1].split("Z")[1]


def test_end_park_lines_program_start_sequential():
    settings = make_program_settings()
    settings.update({"park_mode": "program_start", "park_sequential": True})
    lines = get_end_park_lines(settings)
    assert lines == [
        "(Rueckkehr zur Position bei Programmstart)",
        "G0 X[#<_les_start_x>*2]",
        "G0 Z[#<_les_start_z>]",
    ]


def test_program_start_position_is_captured_once_near_the_very_beginning():
    settings = make_program_settings()
    settings["park_mode"] = "program_start"
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "CaptureStart"}),
        Operation(OpType.TURN, {"tool": 1, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert lines.count("#<_les_start_x> = #<_x>") == 1
    assert lines.count("#<_les_start_z> = #<_z>") == 1
    capture_idx = lines.index("#<_les_start_x> = #<_x>")
    # Vor jeder eigenen Bewegung/Werkzeugaktion erfasst - insbesondere vor
    # dem ersten Werkzeugwechsel-Check.
    assert capture_idx < lines.index("o<les_first_tool> if [#<_current_tool> NE 1]")
    assert capture_idx < 8  # nahe am Dateianfang, nicht irgendwo im Verlauf


def test_program_start_mode_without_toolchange_still_ends_at_captured_position():
    """park_mode=program_start funktioniert auch fuer Programme, deren
    Werkzeugwechsel im LinuxCNC-Modus laeuft - beide Einstellungen sind
    unabhaengig voneinander waehlbar."""
    settings = make_program_settings()
    settings.update({"toolchange_position_mode": "linuxcnc", "park_mode": "program_start"})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "CombinedModes"}),
        Operation(OpType.TURN, {"tool": 1, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    assert "#<_les_start_x> = #<_x>" in lines
    end_idx = lines.index("(Rueckkehr zur Position bei Programmstart)")
    assert lines[end_idx + 1] == "G0 X[#<_les_start_x>*2] Z[#<_les_start_z>]"
    # Der informative Kopfkommentar "Werkzeugwechselpunkt: X.. Z.." (rein
    # dokumentarisch, siehe gcode_program.py) zeigt XT/ZT unabhaengig vom
    # gewaehlten Modus an - hier zaehlt nur, dass KEIN ausgefuehrter G0-
    # Eilgang mehr auf XT/ZT faehrt.
    assert not any(line.startswith("G0 ") and ("150.000" in line or "300.000" in line) for line in lines)


# ---------------------------------------------------------------------------
# 4. Sicherer Rueckzug vor der Endpositionierung bleibt erhalten
# ---------------------------------------------------------------------------


def test_safe_retract_precedes_end_position_for_external_last_operation():
    """Vor jeder Endpositionierung muss der vorhandene sichere
    Bearbeitungsrueckzug erhalten bleiben - keine direkte Bewegung aus dem
    Werkstueck zur Parkposition."""
    settings = make_program_settings()
    settings.update({"park_mode": "end_position", "park_x": 12.0, "park_z": 34.0})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SafeRetractExternal"}),
        Operation(
            OpType.FACE,
            {"mode": 0, "tool": 1, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.1, "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0, "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0},
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    park_idx = lines.index("(Parkposition am Ende)")
    prelude = lines[max(0, park_idx - 6):park_idx]
    # Die Aussen-Sicherheitsebene (XRA=40/ZRA=2 aus make_program_settings())
    # muss vor dem Park angefahren worden sein.
    assert "G0 X40.000" in prelude
    assert "G0 Z2.000" in prelude


def test_safe_retract_precedes_program_start_end_position_for_internal_last_operation():
    settings = make_program_settings()
    settings.update({"park_mode": "program_start", "xri": 9.0, "zri": 1.0, "xri_absolute": True, "zri_absolute": True})
    operations = [
        Operation(OpType.DRILL, {"tool": 10, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0)]),
        Operation(OpType.ABSPANEN, {"tool": 10, "side": "inside", "spindle": 1200.0, "feed": 0.12, "depth_per_pass": 1.0, "mode": "rough", "slice_strategy": "parallel_z"}, path=[(10.0, 0.0), (19.2, -30.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    end_idx = lines.index("(Rueckkehr zur Position bei Programmstart)")
    prelude = lines[max(0, end_idx - 6):end_idx]
    assert "G0 X9.000" in prelude
    assert "G0 Z1.000" in prelude


# ---------------------------------------------------------------------------
# 5. Der tatsaechliche "Programm erzeugen"-Pfad (build_gcode_lines(),
#    ui_flow.py) - hier stak der Bug, der get_end_park_lines() faktisch
#    unerreichbar machte, indem footer_lines immer mit der
#    Werkzeugwechselposition ueberschrieben wurde.
# ---------------------------------------------------------------------------


def _make_ui_handler(example: str, lang: str, header_overrides: dict | None = None):
    operations, settings = example_programs()[example]
    header = dict(settings)
    if header_overrides:
        header.update(header_overrides)
    handler = object.__new__(HandlerClass)
    handler.model = ProgramModel()
    handler.model.operations = list(operations)
    handler._tool_table = SimpleNamespace(tools={})
    handler._collect_program_header = lambda: dict(header)
    handler._current_language_code = lambda: lang
    return handler


def test_build_gcode_lines_toolchange_default_reaches_xt_zt():
    lines = build_gcode_lines(_make_ui_handler("Bohren.ngc", "de"))
    assert "(Werkzeugwechselpunkt am Ende)" in lines
    assert any(line.startswith("G0 X150.000") or line.startswith("G53 G0 X150.000") for line in lines)


def test_build_gcode_lines_end_position_is_actually_reachable():
    """Regression fuer den gefundenen Bug: vorher wurde footer_lines in
    build_gcode_lines() IMMER mit der Werkzeugwechselposition ueberschrieben,
    wodurch park_mode="end_position" in der echten UI nie wirkte."""
    lines = build_gcode_lines(_make_ui_handler("Bohren.ngc", "de", {"park_mode": "end_position", "park_x": 77.0, "park_z": 88.0}))
    assert "(Parkposition am Ende)" in lines
    park_idx = lines.index("(Parkposition am Ende)")
    assert lines[park_idx + 1] == "G0 X77.000 Z88.000"
    # Die Werkzeugwechselfahrt (LES-Modus, Default) verwendet weiterhin
    # XT/ZT - nur die Endposition wurde umgestellt, das ist der eigentliche
    # Bug-Regressionstest: vorher wurde die Parkposition IMMER durch die
    # Werkzeugwechselposition ersetzt.
    assert lines.count("(Parkposition am Ende)") == 1
    assert "(Werkzeugwechselpunkt am Ende)" not in lines


def test_build_gcode_lines_program_start_is_reachable():
    lines = build_gcode_lines(_make_ui_handler("Bohren.ngc", "de", {"park_mode": "program_start"}))
    assert "#<_les_start_x> = #<_x>" in lines
    assert "G0 X[#<_les_start_x>*2] Z[#<_les_start_z>]" in lines


def test_build_gcode_lines_linuxcnc_toolchange_mode_has_no_xt_zt_anywhere():
    # park_mode explizit auf "end_position" gesetzt: sonst wuerde die
    # Default-Endposition ("toolchange") unabhaengig vom
    # toolchange_position_mode weiterhin XT/ZT fuer den Programmabschluss
    # verwenden (separate Einstellung, siehe get_end_park_lines()).
    lines = build_gcode_lines(
        _make_ui_handler(
            "CSS_Wechsel.ngc",
            "de",
            {"toolchange_position_mode": "linuxcnc", "park_mode": "end_position", "park_x": 5.0, "park_z": 6.0},
        )
    )
    # Der informative Kopfkommentar "Werkzeugwechselpunkt: X.. Z.." (rein
    # dokumentarisch) zeigt XT/ZT unabhaengig vom Modus an - relevant ist
    # nur, dass kein ausgefuehrter G0-Eilgang mehr auf XT/ZT faehrt.
    assert not any(line.startswith("G0 ") and ("150.000" in line or "300.000" in line) for line in lines)
    assert lines.count("G43 H1") == 2  # T01 wird zweimal geladen (T01 -> T02 -> T01)
    assert lines.count("G43 H2") == 1


def test_build_gcode_lines_does_not_require_xt_zt_when_neither_toolchange_nor_end_needs_it():
    """Weder LES-Werkzeugwechselfahrt noch XT/ZT-Endposition: XT/ZT darf
    dann fehlen, ohne dass die Erzeugung abbricht."""
    lines = build_gcode_lines(
        _make_ui_handler(
            "Bohren.ngc",
            "de",
            {"toolchange_position_mode": "linuxcnc", "park_mode": "end_position", "park_x": 5.0, "park_z": 6.0, "xt": None, "zt": None},
        )
    )
    assert "M30" in lines


def test_build_gcode_lines_still_requires_xt_zt_for_default_end_mode():
    import pytest

    with pytest.raises(ValueError):
        build_gcode_lines(_make_ui_handler("Bohren.ngc", "de", {"toolchange_position_mode": "linuxcnc", "xt": None, "zt": None}))


# ---------------------------------------------------------------------------
# 6. Save/Load der neuen Einstellungen
# ---------------------------------------------------------------------------


def test_new_settings_survive_a_save_load_roundtrip():
    header = dict(make_program_settings())
    header.update({"toolchange_position_mode": "linuxcnc", "park_mode": "program_start"})
    payload = build_program_data([], header, {})
    loaded_header, _ops, _program_path, _gcode_path = parse_program_payload(payload, "roundtrip.lse")
    assert loaded_header["toolchange_position_mode"] == "linuxcnc"
    assert loaded_header["park_mode"] == "program_start"


def test_old_lse_without_new_settings_still_loads_and_defaults_to_legacy_behavior():
    """Bestehende .lse-Dateien (vor diesem Arbeitsblock gespeichert) haben
    weder toolchange_position_mode noch das erweiterte park_mode - das darf
    weder beim Laden noch bei der Erzeugung einen Fehler ausloesen, und das
    Verhalten muss dem bisherigen (LES/XT-ZT) entsprechen."""
    header = dict(make_program_settings())
    assert "toolchange_position_mode" not in header
    payload = build_program_data([], header, {})
    loaded_header, _ops, _program_path, _gcode_path = parse_program_payload(payload, "legacy.lse")
    assert loaded_header.get("toolchange_position_mode") is None
    assert loaded_header.get("park_mode") is None
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Legacy"}),
        Operation(OpType.TURN, {"tool": 1, "feed": 0.2, "safe_z": 2.0, "spindle": 1000.0}, path=[(20.0, 0.0), (18.0, -2.0)]),
    ]
    lines = generate_program_gcode(operations, loaded_header)
    assert any(line.startswith("G0 X150.000") or line.startswith("G53 G0 X150.000") for line in lines)
    assert "(Werkzeugwechselpunkt am Ende)" in lines
