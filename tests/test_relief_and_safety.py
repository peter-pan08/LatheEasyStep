from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

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


def test_validate_external_retract_clearance_unit():
    """Direkter Unit-Test der neuen Pruefung selbst (isoliert von der
    Werkzeugwechsel-Diagonale, die denselben Fall teils zufaellig ueber
    einen anderen, weniger spezifischen Fehler abfaengt)."""
    from lathe_easystep.gcode_safety import validate_external_retract_clearance

    settings = make_program_settings()
    settings.update({"xra": -20.0, "zra": -50.0})
    with pytest.raises(ValueError, match="Rueckzugsebene"):
        validate_external_retract_clearance(settings)

    settings_ok = make_program_settings()
    validate_external_retract_clearance(settings_ok)  # Standardwerte: kein Fehler

    settings_z_only = make_program_settings()
    settings_z_only.update({"zra": -50.0})
    # X bleibt am sicheren Standardwert (weit ausserhalb des Durchmessers) -
    # der resultierende Punkt ist real ausserhalb des Werkstuecks.
    validate_external_retract_clearance(settings_z_only)


def test_external_retract_plane_inside_stock_blocks_generation():
    """LES-040: Nutzerentscheidung 2026-09-10 - ausser bei Innenbearbeitung
    darf die Rueckzugsebene (XRA/ZRA) niemals innerhalb der Rohteil-
    Huellkurve liegen (anders als XRI/ZRI, das per Definition oft
    innerhalb liegt, z. B. in einer vorhandenen Bohrung). Anders als der
    obige Test (Operations-ZIELPUNKT absichtlich im Rohteil, nur Warnung)
    ist hier die konfigurierte RUECKZUGSEBENE selbst unplausibel - das
    wird von `validate_external_retract_clearance()` als harter Fehler
    abgelehnt, bevor irgendein G-Code entsteht (u. a. genutzt fuer die
    Werkzeugwechsel-Positionierung vor der allerersten Operation)."""
    settings = make_program_settings()
    # xa=40 (Standard) + xra=-20 relativ = X20 -> innerhalb 0..40;
    # za=0 + zra=-50 relativ = Z-50 -> innerhalb 0..-55.
    settings.update({"xra": -20.0, "zra": -50.0})
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.ABSPANEN,
            {"side": "outside", "mode": "finish", "tool": 1, "spindle": 800.0,
             "feed": 0.15, "depth_per_pass": 0.5, "slice_strategy": "parallel_z"},
            path=[(12.0, -30.0), (18.0, 0.0)],
        ),
    ]
    with pytest.raises(ValueError, match="Rueckzugsebene"):
        generate_program_gcode(operations, settings)


def test_external_retract_plane_outside_stock_in_either_axis_is_accepted():
    """Gegenprobe: liegt die Rueckzugsebene in MINDESTENS einer Achse
    ausserhalb der Rohteil-Huellkurve (hier X weit ausserhalb, Z tief im
    Rohteil), ist der resultierende Punkt real ausserhalb des Werkstuecks
    (es gibt bei diesem Durchmesser dort kein Material) - kein Fehler."""
    settings = make_program_settings()
    settings.update({"zra": -50.0})  # xra bleibt am sicheren Standardwert
    operations = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(
            OpType.ABSPANEN,
            {"side": "outside", "mode": "finish", "tool": 1, "spindle": 800.0,
             "feed": 0.15, "depth_per_pass": 0.5, "slice_strategy": "parallel_z"},
            path=[(12.0, -30.0), (18.0, 0.0)],
        ),
    ]
    generate_program_gcode(operations, settings)  # darf nicht werfen


def _polyline_wall_radius_at_z(points, z):
    """Radius (X/2) einer monoton fallenden (X,Z)-Polylinie an einer
    gegebenen Z-Position, linear interpoliert - fuer geradlinige
    Konturabschnitte (keine Boegen) ist das exakt die wahre Kontur."""
    for (x0, z0), (x1, z1) in zip(points, points[1:]):
        lo, hi = sorted((z0, z1))
        if lo - 1e-9 <= z <= hi + 1e-9:
            if abs(z1 - z0) < 1e-12:
                return max(x0, x1) / 2.0
            t = (z - z0) / (z1 - z0)
            return (x0 + t * (x1 - x0)) / 2.0
    # Ausserhalb des von der Polylinie abgedeckten Z-Bereichs (z. B. minimal
    # vor der Stirnflaeche) den naechstgelegenen Randpunkt verwenden statt
    # ueber die Kontur hinweg zu extrapolieren.
    nearest = min(points, key=lambda pt: abs(pt[1] - z))
    return nearest[0] / 2.0


def _max_wall_radius_over_z_range(points, z_lo, z_hi):
    """Groesster Wandradius innerhalb [z_lo, z_hi] einer stueckweise
    linearen Polylinie - das Maximum liegt immer an einem Intervallende
    oder an einem Stuetzpunkt der Polylinie innerhalb des Intervalls. Fuer
    Aussenbearbeitung ist genau diese Stelle der kritische Fall: ein bei
    konstantem X ueber eine ganze Z-Spanne fahrendes Band muss ueberall
    ausserhalb der (um das Aufmass vergroesserten) Kontur bleiben, also am
    Ort des groessten Wandradius innerhalb der Spanne."""
    candidates = {z_lo, z_hi}
    for _, z in points:
        if z_lo - 1e-9 <= z <= z_hi + 1e-9:
            candidates.add(z)
    return max(_polyline_wall_radius_at_z(points, z) for z in candidates)


def test_separate_relief_with_chip_breaking_keeps_allowance_and_leaves_groove_untouched():
    """Nutzerauftrag 2026-09-10: der Sehnen-/Aufmass-Fix und der
    Spanbruch-Fix (siehe test_cycle_vs_explicit_parity.py) wurden nur an
    einer einfachen Bogenkontur geprueft. Der eigentliche Risiko-Codepfad
    ist aber ein ANDERER, wenn zusaetzlich ein separat geschruppter
    DIN-Freistich (`undercut_mode='separate'`) mitten in der Kontur sitzt:
    das Schruppen bekommt dann eine um die Nut BEREINIGTE Ersatzkontur
    (`contour_variants['rough_points']`, ueberbrueckt die Nut) statt der
    vollen Fertigkontur, UND gleichzeitig erzwingt Spanbruch (`pause_enabled`)
    den expliziten Pfad. Diese Kombination (Nut-Ueberbrueckung + Aufmass-
    Versatz + Pausen-Emission gleichzeitig im selben Schrupp-Pfad) war
    bisher an keiner Stelle automatisiert getestet."""
    settings = make_program_settings()
    contour_params = {
        "name": "relief_pause_contour", "start_x": 20.0, "start_z": 0.0,
        "segments": [
            {"x": 20.0, "z": -10.0},
            {"x": 20.0, "z": -20.0, "feature": {"feature_type": "din_relief",
             "thread_size": "M10", "orientation": "end", "internal": False}},
            {"x": 26.0, "z": -30.0},
        ],
    }
    variants = build_contour_variants(contour_params)
    contour = Operation(OpType.CONTOUR, contour_params, path=variants["finish_primitives"])
    abspanen = Operation(OpType.ABSPANEN, {
        "tool": 1, "spindle": 900.0, "feed": 0.15, "depth_per_pass": 0.5,
        "slice_strategy": "parallel_z", "mode": "rough_finish", "side": "outside",
        "contour_name": "relief_pause_contour", "undercut_mode": "separate",
        "finish_allow_x": 0.3, "finish_allow_z": 0.15,
        "pause_enabled": True, "pause_distance": 2.0,
    })
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), contour, abspanen], settings)

    assert not any(l.startswith(("G71 ", "G72 ")) for l in lines)
    assert "(Hinterschnitt separat)" in "\n".join(lines)

    rough_start = next(i for i, l in enumerate(lines) if l.startswith("(ABSPANEN Rough"))
    relief_start = next(i for i, l in enumerate(lines) if l == "(Hinterschnitt separat)")
    # relief_mode="separate" allein wuerde hier bereits den Zyklus-Pfad
    # ausschliessen - erst die tatsaechlich emittierten Pausen-Zeilen
    # beweisen, dass das Spanbruch-Feature in diesem (durch die Nut-
    # Ueberbrueckung veraenderten) Schrupp-Pfad wirklich aktiv ist.
    assert any("step_line_pause" in l for l in lines[rough_start:relief_start])

    rough_points = variants["rough_points"]
    allow_radius = 0.3 / 2.0
    checked = 0
    for line in lines[rough_start:relief_start]:
        if "step_line_pause" not in line or "call" not in line:
            continue
        nums = re.findall(r"\[(-?[0-9.]+)\]", line)
        if len(nums) < 4:
            continue
        x0, z0, x1, z1 = (float(nums[0]), float(nums[1]), float(nums[2]), float(nums[3]))
        # Diese Baender fahren bei konstantem X ueber eine ganze Z-Spanne -
        # sicher ist der Schnitt nur, wenn er ENTLANG DER GESAMTEN Spanne
        # Abstand zur wahren Kontur haelt, nicht nur am Endpunkt.
        assert abs(x0 - x1) < 1e-6, "Erwartet: Band bei konstantem X"
        lo_z, hi_z = sorted((z0, z1))
        max_wall_r = _max_wall_radius_over_z_range(rough_points, lo_z, hi_z)
        clearance = x0 / 2.0 - max_wall_r
        checked += 1
        assert clearance >= allow_radius - 1e-6, (
            f"Schrupp-Band X{x0} Z[{lo_z};{hi_z}] verletzt das Aufmass: nur "
            f"{clearance * 2:.3f}mm statt 0.300mm Restaufmass"
        )
    assert checked > 3

    # Die separat geschruppte Nut selbst muss exakt auf Fertigmass liegen
    # (kein Aufmass, kein Spanbruch - Nutenwerkzeuge stechen typischerweise
    # in einem Zug bis auf Endmass, siehe _emit_relief_pass()).
    relief_end = next(i for i, l in enumerate(lines) if l == "(Schlichtschnitt Kontur)")
    relief_lines = lines[relief_start:relief_end]
    assert not any("step_line_pause" in l for l in relief_lines)
    groove_points = [
        (float(m.group(1)), float(m.group(2)))
        for l in relief_lines if l.startswith("G1 ")
        for m in [re.search(r"X(-?[0-9.]+) Z(-?[0-9.]+)", l)] if m
    ]
    assert groove_points == variants["feature_points"]
