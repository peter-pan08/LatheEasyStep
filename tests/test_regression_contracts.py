import copy
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import example_programs, make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation
from lathe_easystep.persistence import build_program_data, step_data_to_operation
from lathe_easystep.ui_flow import describe_operation


def test_example_programs_match_reference_ngc_files():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ngc_dir = os.path.join(root, "ngc")

    for filename, (operations, settings) in example_programs().items():
        generated = "\n".join(generate_program_gcode(copy.deepcopy(operations), dict(settings)))
        with open(os.path.join(ngc_dir, filename), "r", encoding="utf-8") as f:
            expected = f.read()
        assert generated.rstrip("\n") == expected.rstrip("\n"), filename


def test_example_programs_roundtrip_through_program_payload():
    for filename, (operations, settings) in example_programs().items():
        payload = build_program_data(operations, settings, {"source": filename})
        restored = [step_data_to_operation(op_data) for op_data in payload["operations"]]
        restored = [op for op in restored if op is not None]
        assert [op.op_type for op in restored] == [op.op_type for op in operations], filename
        assert [op.params for op in restored] == [op.params for op in operations], filename
        assert [op.path for op in restored] == [op.path for op in operations], filename


def test_face_cycle_profile_contains_no_g0():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "FaceContract"}),
        Operation(
            OpType.FACE,
                {
                    "mode": 0,
                    "tool": 1,
                    "spindle": 1800.0,
                    "feed": 0.12,
                    "depth_max": 0.2,
                    "start_z": 0.0,
                    "end_z": 0.0,
                    "start_x": 42.0,
                    "end_x": 0.0,
                    "finish_allow_z": 0.0,
                    "retract": 1.0,
                    "edge_type": 0,
                    "edge_size": 0.0,
                    "comment": "Face Contract",
            },
            path=[(42.0, 0.0), (0.0, 0.0)],
        ),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "G72 Q" in gcode
    sub_anchor = next(line for line in gcode.splitlines() if line.startswith("o") and " sub" in line)
    sub_num = sub_anchor.split()[0][1:]
    sub_start = gcode.split(f"o{sub_num} sub", 1)[1].split(f"o{sub_num} endsub", 1)[0]
    assert "G0 " not in sub_start


def test_inch_program_uses_g20():
    settings = make_program_settings()
    settings["unit"] = "inch"
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Imperial"}),
        Operation(OpType.THREAD, {"tool": 3, "spindle": 350.0, "pitch": 0.1, "length": 1.0, "major_diameter": 0.5}),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "G20" in gcode
    assert "G21" not in gcode


def test_toolchange_retracts_to_safe_position_before_next_m6():
    settings = make_program_settings()
    settings.update({"xra": 45.0, "zra": 6.0, "xra_absolute": True, "zra_absolute": True})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ToolchangeSafety"}),
        Operation(
            OpType.FACE,
            {"mode": 0, "tool": 1, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.1, "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0, "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0},
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
        Operation(OpType.DRILL, {"tool": 7, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0), (0.0, -20.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T07 M6")
    prelude = lines[max(0, toolchange_idx - 6):toolchange_idx]
    assert "M9" in prelude
    assert "G0 Z6.000" in prelude
    assert "G0 X45.000" in prelude


def test_toolchange_before_internal_op_still_uses_external_safe_planes():
    settings = make_program_settings()
    settings.update(
        {
            "xra": 45.0,
            "zra": 6.0,
            "xra_absolute": True,
            "zra_absolute": True,
            "xri": 9.8,
            "zri": 1.0,
            "xri_absolute": True,
            "zri_absolute": True,
        }
    )
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ToolchangeExternalSafe"}),
        Operation(OpType.DRILL, {"tool": 10, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0)]),
        # path braucht eine echte Z-Tiefe (nicht nur eine flache Linie), sonst
        # findet die bewegungsbasierte Innen-Schrupplogik (G71/G72 werden fuer
        # Innenbearbeitung nicht mehr verwendet) keinen echten Schnittbereich
        # und die LES-002-Pruefung ("kein Schnitt erzeugt") bricht die
        # Erzeugung ab - dieser Test prueft nur die Werkzeugwechsel-Anfahrt,
        # nicht die Roughing-Geometrie selbst.
        Operation(OpType.ABSPANEN, {"tool": 11, "side": "inside", "spindle": 1200.0, "feed": 0.12, "depth_per_pass": 1.0, "mode": "rough", "slice_strategy": "parallel_z"}, path=[(10.0, 0.0), (19.2, -30.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T11 M6")
    prelude = lines[max(0, toolchange_idx - 8):toolchange_idx]
    assert "G0 Z6.000" in prelude
    assert "G0 X45.000" in prelude
    assert "G0 X9.800" not in prelude


def test_groove_subroutines_are_defined_before_main_calls():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveSubOrder"}),
        Operation(
            OpType.GROOVE,
            {
                "tool": 4,
                "spindle": 900.0,
                "feed": 0.15,
                "safe_z": 2.0,
                "diameter": 25.0,
                "width": 5.0,
                "depth": 2.0,
                "z": -10.0,
                "lage": 0,
                "stepA": 0.8,
                "overlap": 0.2,
                "retract": 0.4,
                "sweep_feed": 0.15,
            },
            path=[],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    call_idx = next(i for i, line in enumerate(lines) if line.startswith("o220 call"))
    sub_idx = next(i for i, line in enumerate(lines) if line.startswith("o220 sub"))
    assert sub_idx < call_idx
    assert lines.index("(=== End Subroutines ===)") < call_idx


def test_groove_face_mode_with_zero_depth_raises_instead_of_infinite_loop():
    """Stirneinstich (mode=1) ohne Tiefe/Zustellung fuehrte vor dem Fix zu Acur==Anext
    in der o229-Schleife, also einer echten LinuxCNC-Endlosschleife. Muss jetzt beim
    Generieren abgebrochen werden statt stillschweigend Null-Bewegungen zu erzeugen."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveZeroStep"}),
        Operation(
            OpType.GROOVE,
            {
                "tool": 4,
                "spindle": 900.0,
                "feed": 0.15,
                "safe_z": 2.0,
                "mode": 1,
                "lage": 2,
                "diameter": 25.0,
                "z": -10.0,
                "width": 5.0,
                "depth": 0.0,
                "overlap": 0.2,
                "retract": 0.4,
                "sweep_feed": 0.15,
            },
            path=[],
        ),
    ]
    try:
        generate_program_gcode(operations, settings)
        assert False, "expected ValueError for zero-step groove cycle"
    except ValueError as exc:
        assert "Zustellung" in str(exc)


def test_groove_tool_wider_than_slot_raises():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveTooWide"}),
        Operation(
            OpType.GROOVE,
            {
                "tool": 4,
                "spindle": 900.0,
                "feed": 0.15,
                "safe_z": 2.0,
                "diameter": 25.0,
                "width": 3.0,
                "wtool": 5.0,
                "use_tool_width": True,
                "depth": 2.0,
                "z": -10.0,
                "lage": 0,
                "stepA": 0.8,
                "overlap": 0.2,
                "retract": 0.4,
                "sweep_feed": 0.15,
            },
            path=[],
        ),
    ]
    try:
        generate_program_gcode(operations, settings)
        assert False, "expected ValueError for tool wider than slot"
    except ValueError as exc:
        assert "breiter" in str(exc)


def test_groove_roughing_loop_has_hard_iteration_cap():
    """Defense-in-depth im o220-Zyklus selbst: auch wenn ungueltige Parameter jemals
    an einer anderen Stelle als generate_groove_gcode eingespeist werden, darf die
    Roughing-Schleife nicht endlos laufen."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveLoopCap"}),
        Operation(
            OpType.GROOVE,
            {
                "tool": 4,
                "spindle": 900.0,
                "feed": 0.15,
                "safe_z": 2.0,
                "diameter": 25.0,
                "width": 5.0,
                "depth": 2.0,
                "z": -10.0,
                "lage": 0,
                "stepA": 0.8,
                "overlap": 0.2,
                "retract": 0.4,
                "sweep_feed": 0.15,
            },
            path=[],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    gcode = "\n".join(lines)
    assert "o229 endwhile" in gcode
    sub_body = gcode.split("o229 while", 1)[1].split("o229 endwhile", 1)[0]
    assert "o229 break" in sub_body
    assert "M99" in gcode.split("o220 sub", 1)[1].split("(Width stepping)", 1)[0]


def test_internal_groove_retracts_via_xri_zri_not_xra_zra():
    """Mantel-Innen-Nut (lage=1) arbeitet in der Bohrung; der Rueckzug nach dem
    Zyklus muss die innenbezogenen Sicherheitsebenen XRI/ZRI verwenden, nicht die
    aussenbezogenen XRA/ZRA (siehe TODO Prioritaet A #2: Ausweitung auf Inneneinstich)."""
    settings = make_program_settings()
    settings.update({
        "xra": 45.0, "zra": 6.0, "xra_absolute": True, "zra_absolute": True,
        "xri": 5.0, "zri": -40.0, "xri_absolute": True, "zri_absolute": True,
    })
    groove_params = {
        "tool": 4,
        "spindle": 900.0,
        "feed": 0.15,
        "safe_z": 2.0,
        "diameter": 25.0,
        "width": 5.0,
        "depth": 2.0,
        "z": -10.0,
        "stepA": 0.8,
        "overlap": 0.2,
        "retract": 0.4,
        "sweep_feed": 0.15,
    }

    internal_ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveInternal"}),
        Operation(OpType.GROOVE, {**groove_params, "lage": 1}, path=[]),
    ]
    internal_lines = generate_program_gcode(internal_ops, dict(settings))
    # Ab dem Step selbst pruefen: der vorausgehende Werkzeugwechsel faehrt
    # legitim auf die AUSSEN-bezogene Sicherheitsposition (XRA/ZRA), da der
    # Retract-Modus zu diesem Zeitpunkt noch nicht auf "internal" steht - das
    # ist unabhaengig von der hier zu pruefenden Eigenschaft (der Einstich
    # selbst muss XRI/ZRI verwenden, nicht XRA/ZRA).
    internal_gcode = "\n".join(internal_lines[internal_lines.index("(Step 1: groove)"):])
    assert "X5.000" in internal_gcode
    assert "Z-40.000" in internal_gcode
    assert "X45.000" not in internal_gcode
    assert "Z6.000" not in internal_gcode

    external_ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "GrooveExternal"}),
        Operation(OpType.GROOVE, {**groove_params, "lage": 0}, path=[]),
    ]
    external_lines = generate_program_gcode(external_ops, dict(settings))
    external_gcode = "\n".join(external_lines)
    assert "X45.000" in external_gcode
    assert "Z6.000" in external_gcode


def test_operation_specific_spindle_mode_overrides_program_header():
    """TODO Prioritaet A #10 / B #6: Drehzahlmodus soll pro Step waehlbar sein.
    Der Generator unterstuetzt das jetzt ueber op.params['spindle_mode'] /
    ['spindle_max_rpm'], mit Fallback auf den globalen Programmkopf-Wert, wenn
    ein Step nichts Eigenes angibt (Rueckwaertskompatibilitaet).

    G96 (CSS) erwartet unter S die Schnittgeschwindigkeit Vc (m/min), nicht
    die Drehzahl - beide Werte sind bewusst unterschiedlich gewaehlt, damit
    ein Test, der die beiden Felder verwechselt, fehlschlagen wuerde."""
    settings = make_program_settings()
    settings["spindle_mode"] = "fixed"  # Programmkopf: G97 als Default
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "PerOpSpindleMode"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0, "tool": 1, "spindle": 1800.0, "feed": 0.12, "depth_max": 0.2,
                "start_z": 0.0, "end_z": 0.0, "start_x": 42.0, "end_x": 0.0,
                "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
                "spindle_mode": "css", "spindle_max_rpm": 2500.0, "cutting_speed": 220.0,
            },
            path=[(42.0, 0.0), (0.0, 0.0)],
        ),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "G97 S1667 M3 (CSS-Anfahrdrehzahl bei X42.000)" in gcode
    assert "G96 D2500 S220.0" in gcode
    assert "G97 S1800 M3" not in gcode
    assert "S1800" not in gcode
    assert gcode.index("G97 S1667") < gcode.index("G0 Z0.000") < gcode.index("G96 D2500") < gcode.index("G72 Q")


def test_operation_without_spindle_mode_falls_back_to_program_header():
    settings = make_program_settings()
    settings["spindle_mode"] = "css"
    settings["spindle_max_rpm"] = 3000.0
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SpindleModeFallback"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0, "tool": 1, "spindle": 1500.0, "feed": 0.12, "depth_max": 0.2,
                "start_z": 0.0, "end_z": 0.0, "start_x": 42.0, "end_x": 0.0,
                "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
                "cutting_speed": 180.0,
            },
            path=[(42.0, 0.0), (0.0, 0.0)],
        ),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "G97 S1364 M3 (CSS-Anfahrdrehzahl bei X42.000)" in gcode
    assert "G96 D3000 S180.0" in gcode


def test_mixed_css_fixed_css_sequence_keeps_speed_units_and_activation_positions():
    settings = make_program_settings()
    face = {
        "mode": 0, "tool": 1, "spindle": 1800.0, "feed": 0.12, "depth_max": 0.2,
        "start_z": 0.0, "end_z": 0.0, "start_x": 40.0, "end_x": 0.0,
        "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
        "spindle_mode": "css", "spindle_max_rpm": 2500.0, "cutting_speed": 120.0,
    }
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "MixedSpindleModes"}),
        Operation(OpType.FACE, dict(face), path=[(40.0, 0.0), (0.0, 0.0)]),
        Operation(OpType.DRILL, {
            "tool": 2, "spindle": 900.0, "feed": 0.1, "safe_z": 2.0,
            "retract": 2.0, "mode": "g81", "diameter": 8.0,
        }, path=[(0.0, 2.0), (0.0, -12.0)]),
        Operation(OpType.FACE, {**face, "cutting_speed": 180.0}, path=[(40.0, 0.0), (0.0, 0.0)]),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    first_css = gcode.index("G96 D2500 S120.0")
    drill_fixed = gcode.index("G97 S900 M3", first_css)
    second_css = gcode.index("G96 D2500 S180.0", drill_fixed)
    assert first_css < drill_fixed < second_css
    assert "G96 D2500 S900" not in gcode
    assert gcode.rindex("G0 X40.000", drill_fixed, second_css) < second_css


def test_css_mode_without_cutting_speed_falls_back_to_g97_with_warning():
    """Ohne Schnittgeschwindigkeit darf G96 NICHT die Drehzahl als Vc
    missbrauchen (physikalisch falsch - `m/min` vs. `U/min`) - stattdessen
    sicherer Fallback auf G97 mit einer Warnung im Kommentar."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "CssWithoutVc"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0, "tool": 1, "spindle": 1500.0, "feed": 0.12, "depth_max": 0.2,
                "start_z": 0.0, "end_z": 0.0, "start_x": 42.0, "end_x": 0.0,
                "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
                "spindle_mode": "css", "spindle_max_rpm": 2500.0,
            },
            path=[(42.0, 0.0), (0.0, 0.0)],
        ),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "G97 S1500 M3" in gcode
    assert "G96" not in gcode
    assert "Schnittgeschwindigkeit fehlt" in gcode


def test_string_valued_combo_params_do_not_crash_generation():
    """Regression fuer einen realen Absturz: seit der ID-only-Umstellung liefern
    thread_orientation/thread_hand/parting_side/face_mode/parting_mode/drill_mode
    ueber currentData() String-IDs (z.B. 'internal', 'left', 'outside', 'rough')
    statt des frueheren numerischen Combo-Index. Mehrere Codepfade parsten das
    weiterhin mit int()/float() und stuerzten damit ab (u.a. beobachtet als
    "sync previous operation failed: invalid literal for int() with base 10:
    'internal'" beim Wechseln der Steps im echten Panel, und ein hartes
    ValueError beim Generieren von FACE/ABSPANEN-G-Code). Dieser Test baut
    Operationen exakt so auf, wie _collect_params() sie aus den echten Combos
    sammelt, und muss ohne Fehler durchlaufen."""
    settings = make_program_settings()
    settings.update({"xri": 3.0, "xri_absolute": True, "zri": -50.0, "zri_absolute": True})

    thread_ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "StringThread"}),
        Operation(
            OpType.THREAD,
            {
                "tool": 3, "spindle": 400.0, "safe_z": 2.0,
                "major_diameter": 10.0, "pitch": 1.5, "length": 15.0,
                "orientation": "internal", "hand": "left",
            },
        ),
    ]
    thread_gcode = "\n".join(generate_program_gcode(thread_ops, dict(settings)))
    assert "G76" in thread_gcode or "G33" in thread_gcode or thread_gcode

    abspanen_ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "StringAbspanen"}),
        Operation(
            OpType.ABSPANEN,
            {
                "tool": 1, "spindle": 900.0, "feed": 0.15, "depth_per_pass": 1.0,
                "side": "outside", "mode": "rough", "slice_strategy": "parallel_z",
            },
            path=[(40.0, 0.0), (20.0, -20.0)],
        ),
    ]
    assert generate_program_gcode(abspanen_ops, dict(settings))

    face_ops = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "StringFace"}),
        Operation(
            OpType.FACE,
            {
                "mode": "rough", "tool": 1, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.2,
                "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0,
                "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
            },
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
    ]
    assert generate_program_gcode(face_ops, dict(settings))


def test_string_orientation_and_hand_produce_correct_internal_left_geometry():
    """Nicht nur 'stuerzt nicht ab', sondern auch fachlich richtig: 'internal'/
    'left' muessen dieselbe Geometrie ergeben wie die alten Werte 1/1."""
    from lathe_easystep.preview_geometry import build_thread_path

    base = {"major_diameter": 10.0, "pitch": 1.5, "length": 15.0, "thread_start_z": 0.0}
    legacy = build_thread_path({**base, "orientation": 1, "hand": 1})
    new_style = build_thread_path({**base, "orientation": "internal", "hand": "left"})
    assert new_style == legacy
    assert new_style  # not empty


def test_drill_mode_string_id_selects_correct_gcode_cycle():
    from lathe_easystep.gcode_drill import generate_drill_gcode
    from lathe_easystep.gcode_safety import append_tool_and_spindle, emit_approach
    from lathe_easystep.gcode_utils import require, require_tool, get_tool_number, emit_coolant

    op = Operation(
        OpType.DRILL,
        {"tool": 7, "spindle": 900.0, "feed": 0.08, "mode": "g83", "peck_depth": 2.0, "safe_z": 2.0},
        path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0), (0.0, -20.0)],
    )
    lines = generate_drill_gcode(
        op, {"xt": 150.0, "zt": 300.0}, require=require, require_tool=require_tool, get_tool_number=get_tool_number,
        append_tool_and_spindle=append_tool_and_spindle, emit_coolant=emit_coolant, emit_approach=emit_approach,
    )
    assert any(line.startswith("G83 ") for line in lines)


def test_drill_approach_uses_shared_safety_helper_like_other_operations():
    """Realtest-Antwort (Q8): 'die Anfahrt sollte so sein wie die Abfahrt,
    Abfahrt ist gut'. Bohren hatte bisher eine eigene, bespoke Anfahrlogik
    (generische sichere Position ueber separates Z/X, danach nochmal separat
    auf x_start/safe_z) mit teils redundanten Bewegungen. Bohren nutzt jetzt
    denselben emit_approach()-Helfer wie Abspanen/Einstich - von einer bereits
    sicheren Position aus ergibt das denselben kombinierten Ziel-Move wie bei
    jeder anderen Operation, statt zweier separater Bewegungen."""
    from lathe_easystep.gcode_drill import generate_drill_gcode
    from lathe_easystep.gcode_safety import append_tool_and_spindle, emit_approach
    from lathe_easystep.gcode_utils import require, require_tool, get_tool_number, emit_coolant

    settings = make_program_settings()
    settings.update({"_is_at_safe": True})
    op = Operation(
        OpType.DRILL,
        {"tool": 7, "spindle": 900.0, "feed": 0.08, "mode": "g81", "safe_z": 2.0},
        path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0), (0.0, -20.0)],
    )
    lines = generate_drill_gcode(
        op, settings, require=require, require_tool=require_tool, get_tool_number=get_tool_number,
        append_tool_and_spindle=append_tool_and_spindle, emit_coolant=emit_coolant, emit_approach=emit_approach,
    )
    # Ab "(Anfahren vor Zyklus)" pruefen: das vorausgehende append_tool_and_spindle()
    # (Werkzeug 7 ist neu -> echter Wechsel) fuehrt eine eigene, bereits
    # abgesicherte Sicherheitsbewegung aus, die zufaellig denselben Z-Wert
    # treffen kann - das ist nicht Teil der hier zu pruefenden Bohr-Anfahrt.
    approach_idx = lines.index("(Anfahren vor Zyklus)")
    cycle_idx = next(i for i, line in enumerate(lines) if line.startswith("G81 "))
    approach_lines = lines[approach_idx:cycle_idx]
    assert "G0 X0.000" in approach_lines
    assert approach_lines.count("G0 Z2.000") == 0


def test_missing_required_field_error_includes_step_and_operation_context():
    """Regression: require()/require_positive() liefen VOR dem try/except, das
    die 'Operation N (typ):'-Kontext-Praefix ergaenzt. Dadurch verlor genau die
    haeufigste Fehlerklasse (fehlendes Werkzeug/Feed/...) die Stelle-Info, und
    format_user_error() konnte weder den Tab/Feldnamen auflösen noch zum
    richtigen Step springen - das war die Ursache der 'zu ungenauen' Fehler."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "MissingToolTest"}),
        Operation(
            OpType.FACE,
            {
                "mode": "rough", "spindle": 1200.0, "feed": 0.12, "depth_max": 0.2,
                "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0,
                "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
                # "tool" absichtlich weggelassen
            },
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
    ]
    try:
        generate_program_gcode(operations, settings)
        assert False, "expected ValueError for missing tool"
    except ValueError as exc:
        message = str(exc)
        assert message.startswith("Operation 2 (face):"), message
        assert "'tool'" in message


def test_internal_retract_z_uses_front_stock_face_not_rear_end():
    """Realer Sicherheitsbug: Bei Innenbearbeitung wurde die sichere
    Rueckzugsebene in Z bisher als ZI (hinteres Endmass, nahe Futter) + ZRI
    berechnet. Mit ZI=-80 und ZRI=0 (inkrementell) ergab das eine 'sichere'
    Z-Position mitten im/am Ende des Rohteils - der Generator warnte sogar
    selbst davor ('Rueckzugsebene schneidet den Futterbereich'), fuhr die
    G0-Bewegung aber trotzdem. Der Rueckzug muss immer zur vorderen,
    zugaenglichen Seite (ZA) erfolgen, bei Innen- wie bei Aussenbearbeitung -
    nur der Zuschlag (ZRI vs. ZRA) unterscheidet sich."""
    settings = make_program_settings()
    settings.update({
        "xa": 50.0, "xi": 0.0, "za": 1.0, "zi": -80.0,
        "xra": 2.0, "xra_absolute": False,
        "zra": 5.0, "zra_absolute": False,
        "xri": 5.0, "xri_absolute": True,
        "zri": 0.0, "zri_absolute": False,
        "chuck_no_go_x_min": 0.0, "chuck_no_go_x_max": 50.0, "chuck_no_go_z_limit": -75.0,
    })
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "InternalRetractSafety"}),
        Operation(
            OpType.ABSPANEN,
            {
                "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
                "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            },
            path=[(9.8, 0.0), (19.0, -10.0)],
        ),
    ]
    gcode = "\n".join(generate_program_gcode(operations, settings))
    assert "schneidet den Futterbereich" not in gcode
    assert "G0 Z-80.000" not in gcode
    assert "G0 Z1.000" in gcode


def test_toolchange_uses_work_or_machine_coords_explicitly():
    settings = make_program_settings()
    settings.update({"xt": 70.0, "zt": 200.0, "toolchange_coords": "work"})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "ToolchangeCoord"}),
        Operation(OpType.FACE, {"mode": 0, "tool": 1, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.1, "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0, "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0}, path=[(40.0, 0.0), (0.0, 0.0)]),
        Operation(OpType.DRILL, {"tool": 7, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0), (0.0, -20.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_line = lines[lines.index("(Toolchange move)") + 1]
    assert toolchange_line == "G0 X70.000 Z200.000"

    settings["toolchange_coords"] = "machine"
    lines = generate_program_gcode(operations, settings)
    toolchange_line = lines[lines.index("(Toolchange move)") + 1]
    assert toolchange_line == "G53 G0 X70.000 Z200.000"


def test_generated_toolchange_does_not_inject_zero_machine_move():
    settings = make_program_settings()
    settings.update({"xt": 70.0, "zt": 200.0, "toolchange_coords": "machine"})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "NoZeroToolchange"}),
        Operation(OpType.FACE, {"mode": 0, "tool": 1, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.1, "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0, "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0}, path=[(40.0, 0.0), (0.0, 0.0)]),
        Operation(OpType.DRILL, {"tool": 7, "spindle": 900.0, "feed": 0.08, "mode": 0, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -18.0), (0.0, -20.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T07 M6")
    post = lines[toolchange_idx + 1:toolchange_idx + 4]
    assert "G53 G0 X0.000 Z0.000" not in lines
    assert "G0 X0.000 Z0.000" not in post


def test_first_toolchange_still_moves_to_defined_toolchange_point():
    settings = make_program_settings()
    settings.update({"xt": 70.0, "zt": 200.0, "toolchange_coords": "machine"})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "FirstToolchange"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0,
                "tool": 7,
                "spindle": 1200.0,
                "feed": 0.12,
                "depth_max": 0.1,
                "start_x": 40.0,
                "end_x": 0.0,
                "start_z": 0.0,
                "end_z": 0.0,
                "finish_allow_z": 0.0,
                "retract": 1.0,
                "edge_type": 0,
                "edge_size": 0.0,
            },
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
        Operation(
            OpType.DRILL,
            {
                "tool": 9,
                "spindle": 900.0,
                "feed": 0.08,
                "mode": 0,
                "safe_z": 2.0,
            },
            path=[(0.0, 0.0), (8.0, 0.0), (8.0, -10.0)],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T07 M6")
    prelude = lines[max(0, toolchange_idx - 6):toolchange_idx]
    assert "G53 G0 X70.000 Z200.000" in prelude


def test_first_toolchange_moves_to_toolchange_point_when_only_one_tool_used():
    """Realer Bugreport: 'erster Wechsel leider nicht am Werkzeugwechselpunkt'.
    Ursache: generate_program_gcode() ruft gcode_for_operation() zuerst NUR zur
    Vorab-Validierung auf, mutiert dabei aber denselben settings-Dict
    (_current_tool ueber append_tool_and_spindle()). Verwenden ALLE
    Operationen dasselbe Werkzeug, landet _current_tool nach der Validierung
    bereits beim ERSTEN echten Werkzeug - der Vergleich "tool_num != last_tool"
    im echten Erzeugungsdurchlauf wird dadurch faelschlich False, und der
    Werkzeugwechselpunkt wird beim ersten (und einzigen) Wechsel nicht
    angefahren. Der bereits vorhandene Test oben nutzt zwei verschiedene
    Werkzeuge (7 dann 9) und uebersieht den Fehler dadurch zufaellig, weil
    das dann IMMER noch wie ein "echter" Wechsel aussieht."""
    settings = make_program_settings()
    settings.update({"xt": 70.0, "zt": 200.0, "toolchange_coords": "machine"})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SingleToolFirstChange"}),
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(20.0, 0.0), (18.0, -2.0)],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    toolchange_idx = lines.index("T01 M6")
    prelude = lines[max(0, toolchange_idx - 6):toolchange_idx]
    assert "G53 G0 X70.000 Z200.000" in prelude


def test_subroutines_are_defined_before_main_program_flow():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SubOrder"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0,
                "tool": 1,
                "spindle": 1200.0,
                "feed": 0.12,
                "depth_max": 0.1,
                "start_x": 40.0,
                "end_x": 0.0,
                "start_z": 0.0,
                "end_z": 0.0,
                "finish_allow_z": 0.0,
                "retract": 1.0,
                "edge_type": 0,
                "edge_size": 0.0,
            },
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    sub_idx = next(i for i, line in enumerate(lines) if line.startswith("o") and " sub" in line)
    end_subs_idx = lines.index("(=== End Subroutines ===)")
    first_step_idx = next(i for i, line in enumerate(lines) if line.startswith("(Step "))
    assert sub_idx < end_subs_idx < first_step_idx


def test_program_ends_with_m30_and_no_subroutine_afterwards():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "M30Final"}),
        Operation(
            OpType.FACE,
            {
                "mode": 0,
                "tool": 1,
                "spindle": 1200.0,
                "feed": 0.12,
                "depth_max": 0.1,
                "start_x": 40.0,
                "end_x": 0.0,
                "start_z": 0.0,
                "end_z": 0.0,
                "finish_allow_z": 0.0,
                "retract": 1.0,
                "edge_type": 0,
                "edge_size": 0.0,
            },
            path=[(40.0, 0.0), (0.0, 0.0)],
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    m30_idx = lines.index("M30")
    assert m30_idx == len(lines) - 2
    assert not any(line.startswith("o") and " sub" in line for line in lines[m30_idx + 1 :])


def test_contour_step_description_is_neutral():
    class _Handler:
        pass

    text = describe_operation(_Handler(), Operation(OpType.CONTOUR, {"name": "Testkontur"}), 1)
    assert "Kontur: Testkontur" in text
    assert "Aussenkontur" not in text
    assert "Innenkontur" not in text


def test_chuck_no_go_zone_blocks_generation():
    settings = make_program_settings()
    settings.update(
        {
            "xra": 48.0,
            "zra": 4.0,
            "xra_absolute": True,
            "zra_absolute": True,
            "chuck_no_go_x_min": 20.0,
            "chuck_no_go_x_max": 80.0,
            "chuck_no_go_z_limit": -40.0,
            "za": 0.0,
            "zi": -70.0,
        }
    )
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "NoGo"}),
        Operation(
            OpType.FACE,
            {"mode": 0, "tool": 1, "spindle": 1000.0, "feed": 0.12, "depth_max": 0.1, "start_x": 40.0, "start_z": -50.0, "end_x": 30.0, "end_z": -50.0, "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0},
            path=[(40.0, -50.0), (30.0, -50.0)],
        ),
    ]
    import pytest
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        generate_program_gcode(operations, settings)
