from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.contour_logic import build_contour_variants, select_thread_relief_for_contour, thread_relief_spec, validate_contour_segments_for_profile
from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation


def test_validate_contour_respects_x_empty_z_empty_placeholders():
    """Realer Bug: Segmente, die nur eine Achse setzen (mode='x'/'z'), tragen
    fuer die jeweils andere Achse einen Platzhalter (haeufig 0.0) mit
    x_empty/z_empty == True. Die Validierung nahm diesen Platzhalter bisher
    als echtes Ziel an, statt die vorherige Koordinate beizubehalten - dadurch
    entstand eine voellig falsche Punktliste, die faelschlich 'Radius zu
    gross' bzw. 'nur an einer Ecke moeglich (colinear)' meldete und die
    komplette Kontur-Vorschau leerte (siehe ui_contour.update_contour_preview_temp:
    bei Validierungsfehlern wird _set_preview_paths([]) aufgerufen). Dieser
    Test bildet exakt die reale Innenkontur nach, die davon betroffen war."""
    params = {
        "start_x": 10.0, "start_z": -44.0,
        "segments": [
            {"mode": "x", "x": 12.0, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "chamfer", "edge_size": 0.6},
            {"mode": "z", "x": 0.0, "z": -10.0, "x_empty": True, "z_empty": False, "edge": "radius", "edge_size": 0.5},
            {"mode": "x", "x": 16.0, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "none", "edge_size": 0.0},
            {"mode": "z", "x": 0.0, "z": 0.0, "x_empty": True, "z_empty": False, "edge": "radius", "edge_size": 1.0},
            {"mode": "x", "x": 19.0, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "none", "edge_size": 0.0},
        ],
    }
    ok, errors = validate_contour_segments_for_profile(params)
    assert ok is True, errors
    assert errors == []


def test_contour_geometry_reaches_absolute_zero_targets():
    """Realer Bug (Python-Falsy-Falle): Fuer absolute Koordinaten wurde bisher
    `s.get(key, last) or last` verwendet. Ein bewusst gesetztes Ziel von exakt
    0.0 ist in Python falsy, wodurch der Ausdruck stillschweigend auf den
    VORHERIGEN Punkt zurueckfiel, statt 0.0 zu uebernehmen. Damit blieb jeder
    Folgepunkt (auch nachfolgende Segmente) auf der falschen Koordinate haengen.
    Real beobachtet: eine Innenkontur, die eigentlich bis Z0/X19.2 laeuft,
    endete in Vorschau UND generiertem Programm bei X16/Z-10."""
    params = {
        "start_x": 10.0, "start_z": -44.0,
        "segments": [
            {"mode": "x", "x": 12.0, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "chamfer", "edge_size": 0.6},
            {"mode": "z", "x": 0.0, "z": -10.0, "x_empty": True, "z_empty": False, "edge": "radius", "edge_size": 0.5},
            {"mode": "x", "x": 16.0, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "none", "edge_size": 0.0},
            {"mode": "z", "x": 0.0, "z": 0.0, "x_empty": True, "z_empty": False, "edge": "radius", "edge_size": 1.0},
            {"mode": "x", "x": 19.2, "z": 0.0, "x_empty": False, "z_empty": True, "edge": "none", "edge_size": 0.0},
        ],
    }
    variants = build_contour_variants(params)
    finish_points = variants["finish_points"]
    last_x, last_z = finish_points[-1]
    assert abs(last_z - 0.0) < 1e-6, f"letzter Punkt muss bei Z=0 enden, ist aber {finish_points[-1]}"
    assert abs(last_x - 19.2) < 1e-6, f"letzter Punkt muss bei X=19.2 enden, ist aber {finish_points[-1]}"
    # Kein Punkt darf faelschlich bei Z=-10 haengen bleiben, nachdem die Kontur
    # bereits nach Z=0 uebergegangen ist.
    assert finish_points[-2][1] != -10.0


def test_build_contour_variants_split_relief_geometry():
    params = {
        "name": "relief_contour",
        "start_x": 20.0,
        "start_z": 0.0,
        "segments": [
            {"x": 20.0, "z": -10.0},
            {
                "x": 20.0,
                "z": -20.0,
                "feature": {
                    "feature_type": "din_relief",
                    "thread_size": "M10",
                    "orientation": "end",
                    "internal": False,
                },
            },
        ],
    }
    variants = build_contour_variants(params)
    assert variants["feature_points"]
    assert len(variants["finish_points"]) > len(variants["rough_points"])
    assert variants["feature_points"][0] == (20.0, -20.0)


def test_abspanen_relief_finish_only_keeps_relief_for_finish_pass():
    settings = make_program_settings()
    contour_params = {
        "name": "relief_contour",
        "start_x": 20.0,
        "start_z": 0.0,
        "segments": [
            {"x": 20.0, "z": -10.0},
            {
                "x": 20.0,
                "z": -20.0,
                "feature": {
                    "feature_type": "din_relief",
                    "thread_size": "M10",
                    "orientation": "end",
                    "internal": False,
                },
            },
        ],
    }
    contour = Operation(OpType.CONTOUR, contour_params, path=build_contour_variants(contour_params)["finish_primitives"])
    abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1,
            "spindle": 1200.0,
            "feed": 0.15,
            "depth_per_pass": 0.5,
            "slice_strategy": "parallel_z",
            "mode": 2,
            "contour_name": "relief_contour",
            "undercut_mode": "finish_only",
            "comment": "Relief finish only",
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings)
    text = "\n".join(lines)
    assert "(Hinterschnitt-Modus: finish_only)" in text
    assert "(Hinterschnitt separat)" not in text
    assert "X17.700" in text
    assert "X17.700 Z-25.200" in text


def test_abspanen_relief_separate_emits_separate_section():
    settings = make_program_settings()
    contour_params = {
        "name": "relief_contour",
        "start_x": 20.0,
        "start_z": 0.0,
        "segments": [
            {"x": 20.0, "z": -10.0},
            {
                "x": 20.0,
                "z": -20.0,
                "feature": {
                    "feature_type": "din_relief",
                    "thread_size": "M10",
                    "orientation": "end",
                    "internal": False,
                },
            },
        ],
    }
    contour = Operation(OpType.CONTOUR, contour_params, path=build_contour_variants(contour_params)["finish_primitives"])
    abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1,
            "spindle": 1200.0,
            "feed": 0.15,
            "depth_per_pass": 0.5,
            "slice_strategy": "parallel_z",
            "mode": 0,
            "contour_name": "relief_contour",
            "undercut_mode": "separate",
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings)
    assert "(Hinterschnitt separat)" in "\n".join(lines)


def test_full_relief_contour_never_uses_non_monotonic_g71_subroutine():
    settings = make_program_settings()
    contour_params = {
        "name": "full_relief",
        "start_x": 30.0,
        "start_z": 0.0,
        "segments": [
            {"x": 30.0, "z": -20.0, "feature": {"feature_type": "din_relief", "thread_size": "M10", "internal": False}},
            {"x": 40.0, "z": -20.0},
        ],
    }
    contour = Operation(OpType.CONTOUR, contour_params, path=build_contour_variants(contour_params)["finish_primitives"])
    abspanen = Operation(
        OpType.ABSPANEN,
        {"tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 0.5,
         "slice_strategy": "parallel_z", "mode": 0, "contour_name": "full_relief", "undercut_mode": "full"},
    )
    text = "\n".join(generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings))
    assert "G71 Q" not in text
    assert "Freistich in voller Kontur ist nicht G71-monoton" in text


def test_automatic_thread_relief_is_spliced_at_thread_end_for_preview_and_gcode():
    settings = make_program_settings()
    contour_params = {
        "name": "thread_shoulder",
        "start_x": 30.0,
        "start_z": 0.0,
        "segments": [
            {"x": 30.0, "z": -40.0},
            {"x": 40.0, "z": -40.0},
        ],
    }
    contour = Operation(OpType.CONTOUR, contour_params, path=build_contour_variants(contour_params)["finish_primitives"])
    rough_finish = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 0.5,
            "slice_strategy": "parallel_z", "mode": 1, "contour_name": "thread_shoulder",
            "undercut_mode": "full",
        },
    )
    thread = Operation(
        OpType.THREAD,
        {
            "tool": 3, "spindle": 450.0, "pitch": 1.5, "length": 20.0,
            "major_diameter": 30.0, "relief_mode": "suggest", "relief_norm": "DIN 76-A",
        },
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, rough_finish, thread], settings)
    text = "\n".join(lines)
    # M30: endpoint -20, f=4.7 -> entry -15.3; g2=12 -> exit -27.3.
    # The DIN profile is sloped and rounded, not a rectangular pocket.
    assert "G1 X25.000 Z-19.600" in text
    assert "G2 X28.200 Z-27.300" in text
    assert "(Gewindeende Z=-20.000; Ueberdeckung f=4.700)" in text


def test_automatic_internal_thread_relief_expands_the_bore_at_thread_end():
    contour_params = {
        "start_x": 10.0,
        "start_z": 0.0,
        "segments": [{"x": 10.0, "z": -30.0}],
    }
    feature = thread_relief_spec(
        {"major_diameter": 10.0, "length": 20.0, "orientation": "internal", "relief_mode": "suggest"}
    )
    assert feature is not None
    contour_params["auto_thread_reliefs"] = [feature]
    variants = build_contour_variants(contour_params)
    points = variants["feature_points"]
    assert any(x > 10.0 for x, _z in points)
    assert points[0] == (10.0, -16.2)
    assert points[-1] == (10.0, -24.0)


def test_automatic_thread_relief_uses_din_short_form_before_a_near_shoulder():
    contour_params = {"start_x": 30.0, "start_z": 0.0, "segments": [{"x": 30.0, "z": -35.0}]}
    feature = thread_relief_spec({"major_diameter": 30.0, "pitch": 3.5, "length": 30.0, "relief_mode": "suggest"})
    selected = select_thread_relief_for_contour(contour_params, feature)
    assert selected is not None
    assert selected["variant"] == "short"
    assert selected["width"] == 9.0
    variants = build_contour_variants({**contour_params, "auto_thread_reliefs": [selected]})
    assert variants["feature_points"][0] == (30.0, -25.3)
    assert variants["feature_points"][-1] == (30.0, -34.3)
    assert any(primitive["type"] == "arc" for primitive in variants["feature_primitives"])
    vertical_rough_lines = [
        primitive for primitive in variants["rough_primitives"]
        if primitive["type"] == "line" and primitive["p1"][0] == primitive["p2"][0] == 30.0
    ]
    assert len(vertical_rough_lines) == 1
    assert vertical_rough_lines[0]["p2"] == [30.0, -35.0]


def test_toolchange_has_m5_before_each_m6():
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.THREAD, {"tool": 3, "spindle": 300.0, "pitch": 1.5, "length": 10.0, "major_diameter": 12.0}),
        Operation(OpType.DRILL, {"tool": 7, "spindle": 800.0, "feed": 0.08, "safe_z": 2.0}, path=[(0.0, 0.0), (8.0, 0.0), (8.0, -10.0), (0.0, -12.0)]),
    ]
    lines = generate_program_gcode(operations, settings)
    for idx, line in enumerate(lines):
        if line.endswith("M6"):
            assert "M5" in lines[max(0, idx - 6):idx]


def test_validation_warning_comment_sanitizes_parentheses():
    """_check_drill_before_internal_machining() erzeugt eine Warnung, die
    selbst ein inneres Klammerpaar enthaelt ("... vor der (ersten) Bohrung
    ..."). Als LinuxCNC-Kommentar (WARN: ...) muessen verschachtelte Klammern
    entfernt/ersetzt werden, sonst entsteht ein "nested comment"-Parserfehler."""
    settings = make_program_settings()
    settings.update({"xa": 50.0, "za": 1.0, "zi": -80.0, "xri": 9.0, "xri_absolute": True})
    internal_abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "side": "inside", "mode": "finish", "spindle": 1200.0,
            "feed": 0.15, "depth_per_pass": 1.0, "slice_strategy": "parallel_z",
            "comment": "Innen-Schlichten ohne vorherige Bohrung",
        },
        path=[(10.0, 0.0), (10.0, -20.0)],
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), internal_abspanen], settings)
    warning_line = next(line for line in lines if line.startswith("(WARN: Innenbearbeitung"))
    payload = warning_line[len("(WARN: "):-1]
    assert "(" not in payload
    assert ")" not in payload


def test_start_inside_stock_emits_warning():
    settings = make_program_settings()
    settings.update({"xra": 45.0, "zra": 6.0, "xra_absolute": True, "zra_absolute": True})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.FACE,
            {
                "mode": 0,
                "tool": 1,
                "spindle": 1000.0,
                "feed": 0.12,
                "depth_max": 0.1,
                "start_x": 30.0,
                "start_z": -10.0,
                "end_x": 20.0,
                "end_z": -10.0,
                "finish_allow_z": 0.0,
                "retract": 1.0,
                "edge_type": 0,
                "edge_size": 0.0,
            },
            path=[(30.0, -10.0), (20.0, -10.0)],
        ),
    ]
    text = "\n".join(generate_program_gcode(operations, settings))
    assert "liegt im Rohteil" in text
