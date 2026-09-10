import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.gcode_groove import generate_groove_gcode
from lathe_easystep.gcode_roughing import generate_abspanen_gcode, rough_turn_parallel_x
from lathe_easystep.gcode_safety import emit_approach
from lathe_easystep.gcode_thread import generate_thread_gcode
from lathe_easystep.contour_logic import thread_relief_spec
from lathe_easystep.model import OpType, Operation
from lathe_easystep.motion_state import MotionState


def _append_tool_and_spindle(lines, tool, spindle, settings=None, **_kwargs):
    if tool:
        lines.append(f"T{int(tool):02d}")
    if spindle:
        lines.append(f"S{float(spindle):.0f}")


def _emit_coolant(lines, enabled):
    if enabled:
        lines.append("M8")


def _emit_approach(lines, start_x, start_z, settings=None):
    lines.append(f"G0 X{start_x:.3f} Z{start_z:.3f}")


def test_parallel_x_roughing_merges_touching_wall_and_transition_segments():
    """Realtest-Antwort Q15 ('innenabspanen ist keine Strategie, das ist
    Blödsinn, was da generiert wird'): eine reale Innenkontur mit einer
    senkrechten Bohrungswand (konstantes X), die genau an dem X endet, an dem
    eine angrenzende Fase beginnt, erzeugte fuer dasselbe X-Band ZWEI sich
    ueberschneidende Z-Intervalle statt eines einzigen zusammenhaengenden
    Schnitts - das Werkzeug fuhr denselben Tiefenbereich mehrfach an (sichtbar
    als naeherungsweise identische, aber leicht abweichende Z-Werte in
    aufeinanderfolgenden G1-Zeilen). rough_turn_parallel_z() (die andere
    Strategie) mergt ihre Intervalle bereits ueber merge_intervals() - hier
    fehlte der Aufruf."""
    # Nachgebildet aus der realen Innenkontur "ausdrehen": Fase von (11.4,-44)
    # zu (12,-43.4), gefolgt von einer senkrechten Wand (12,-43.4) bis (12,-10.5).
    path = [(10.0, -44.0), (11.4, -44.0), (12.0, -43.4), (12.0, -10.5), (13.0, -10.0)]
    lines = rough_turn_parallel_x(
        path, external=False, x_stock=10.0, x_target=13.0, step_x=1.0, safe_z=0.0, feed=0.15,
    )
    pass_2 = next(i for i, ln in enumerate(lines) if ln.startswith("(Pass 2:"))
    pass_3_or_end = next((i for i, ln in enumerate(lines) if i > pass_2 and ln.startswith("(Pass")), len(lines))
    pass_2_lines = lines[pass_2:pass_3_or_end]
    g1_lines = [ln for ln in pass_2_lines if ln.startswith("G1 ")]
    approach_lines = [ln for ln in pass_2_lines if ln.startswith("G0 X12.000")]
    # Ein einziger zusammenhaengender Schnitt durch die volle Tiefe (-43.4 bis
    # -10.0): genau EINE Anfahrt und zwei G1-Zeilen (Eintauchen + Schnitt),
    # nicht mehrere sich ueberschneidende Anfahrten/Schnitte im selben Band.
    # -10.0 (nicht -10.5, dem Ende der senkrechten Wand): die "Material-
    # reichweite"-Baenderung (siehe rough_turn_parallel_x) erfasst korrekt
    # auch das kurze anschliessende Uebergangssegment (12,-10.5)->(13,-10),
    # das bei X>=12 ebenfalls noch Material hat - der Schnitt geht deshalb
    # bewusst bis -10.0 statt schon bei -10.5 stehenzubleiben.
    assert len(approach_lines) == 1
    assert len(g1_lines) == 2
    combined = " ".join(g1_lines)
    assert "-43.4" in combined and "-10.000" in combined


def test_abspanen_finish_preserves_radius_as_arc():
    params = {
        "tool": 2,
        "spindle": 1200.0,
        "feed": 0.15,
        "depth_per_pass": 1.0,
        "mode": "finish",
        "side": "outside",
        "undercut_mode": "full",
        "_contour_params": {
            "start_x": 27.0,
            "start_z": 0.0,
            "segments": [
                {"x": 30.0, "z": 0.0, "edge": "radius", "edge_size": 1.0},
                {"x": 30.0, "z": -35.0},
                {"x": 40.0, "z": -37.0},
            ],
        },
    }
    settings = {"xt": 150.0, "zt": 300.0, "xa": 50.0, "za": 1.0, "zra": 5.0, "xra": 52.0, "zra_absolute": True, "xra_absolute": True, "tools": {}}
    lines = generate_abspanen_gcode(params, [(27.0, 0.0), (30.0, 0.0), (30.0, -35.0), (40.0, -37.0)], settings)
    assert any(line.startswith("G2 ") or line.startswith("G3 ") for line in lines)


def test_internal_abspanen_without_xi_uses_contour_min_as_start_stock():
    params = {
        "tool": 11,
        "spindle": 1200.0,
        "feed": 0.15,
        "depth_per_pass": 1.0,
        "mode": "rough",
        "side": "inside",
        "slice_strategy": "parallel_z",
        "undercut_mode": "ignore",
    }
    path = [(10.0, 0.0), (10.0, -44.0), (19.2, 0.0)]
    settings = {"xt": 150.0, "zt": 300.0, "xi": 0.0, "xri": 9.8, "zri": 1.0, "xri_absolute": True, "zri_absolute": True, "tools": {}}
    lines = generate_abspanen_gcode(params, path, settings)
    assert any(line.startswith("(Pass ") for line in lines)
    assert any(line.startswith("G1 X") for line in lines)


def test_internal_finish_with_din_relief_disables_incompatible_nose_compensation():
    relief = thread_relief_spec(
        {"major_diameter": 12.0, "length": 20.0, "thread_start_z": -10.0,
         "orientation": "internal", "relief_mode": "suggest"}
    )
    params = {
        "tool": 9, "spindle": 500.0, "feed": 0.15, "depth_per_pass": 1.0,
        "mode": "finish", "side": "inside", "undercut_mode": "full",
        "_contour_params": {
            "start_x": 10.0, "start_z": 0.0,
            "segments": [{"x": 10.0, "z": -40.0}, {"x": 12.0, "z": -40.0}, {"x": 12.0, "z": -10.0}],
            "auto_thread_reliefs": [relief],
        },
    }
    settings = {"xt": 150.0, "zt": 300.0,
        "xi": 10.0, "xri": 9.3, "zri": 1.0, "xri_absolute": True, "zri_absolute": True,
        "tools": {9: {"radius_mm": 0.4, "q": 6}},
    }
    lines = generate_abspanen_gcode(params, [(10.0, 0.0), (10.0, -40.0), (12.0, -40.0), (12.0, -10.0)], settings)
    assert any("Konkavecke" in line for line in lines)
    assert not any(line.startswith("G41.1") for line in lines)


def test_internal_approach_moves_z_on_xri_before_radial_infeed():
    lines = []
    emit_approach(
        lines,
        10.0,
        -20.0,
        {"xri": 9.3, "zri": 1.0, "xri_absolute": True, "zri_absolute": True,
         "_active_retract_mode": "internal", "_motion": MotionState(x=9.3, z=1.0)},
    )
    assert lines == ["G0 Z-20.000", "G0 X10.000"]


def test_external_groove_approach_uses_safe_planes_before_plunge():
    op = Operation(
        OpType.GROOVE,
        {
            "tool": 4,
            "spindle": 600.0,
            "safe_z": 2.0,
            "lage": 0,
            "mode": 0,
            "width": 4.0,
            "depth": 1.0,
            "z": -40.0,
            "diameter": 40.0,
            "stepA": 0.8,
            "overlap": 0.2,
            "retract": 0.4,
            "feed": 0.15,
            "sweep_feed": 0.15,
        },
        path=[],
    )
    settings = {"xt": 150.0, "zt": 300.0, "xra": 52.0, "zra": 6.0, "xra_absolute": True, "zra_absolute": True, "_active_retract_mode": "external"}
    lines = generate_groove_gcode(
        op,
        settings,
        require_tool=lambda p, _label: int(p["tool"]),
        get_tool_number=lambda p: int(p["tool"]),
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
    )
    approach_idx = lines.index("(Anfahren vor Groove)")
    assert lines[approach_idx + 1:approach_idx + 5] == ["G0 Z6.000", "G0 X52.000", "G0 Z-40.000", "G0 X40.000"]


def test_internal_thread_approach_keeps_xri_until_thread_start_z():
    op = Operation(
        OpType.THREAD,
        {
            "tool": 9,
            "spindle": 500.0,
            "pitch": 1.75,
            "length": 20.0,
            "major_diameter": 12.0,
            "thread_depth": 1.07,
            "first_depth": 0.22,
            "peak_offset": 0.54,
            "orientation": "internal",
            "thread_start_z": -10.0,
        },
        path=[],
    )
    settings = {"xt": 150.0, "zt": 300.0, "xri": 9.8, "zri": 1.0, "xri_absolute": True, "zri_absolute": True}
    try:
        generate_thread_gcode(
            op,
            settings,
            require_tool=lambda p, _label: int(p["tool"]),
            get_tool_number=lambda p: int(p["tool"]),
            append_tool_and_spindle=_append_tool_and_spindle,
            emit_coolant=_emit_coolant,
            emit_approach=_emit_approach,
            sanitize_comment_text=str,
        )
        assert False, "expected ValueError when internal thread would underrun XRI"
    except ValueError as exc:
        assert "harte Sicherheitsgrenze" in str(exc)


def test_internal_thread_allows_generation_when_xri_is_respected():
    op = Operation(
        OpType.THREAD,
        {
            "tool": 9,
            "spindle": 500.0,
            "pitch": 1.75,
            "length": 20.0,
            "major_diameter": 12.0,
            "thread_depth": 1.07,
            "first_depth": 0.22,
            "peak_offset": 0.02,
            "orientation": "internal",
            "thread_start_z": -10.0,
        },
        path=[],
    )
    settings = {"xt": 150.0, "zt": 300.0, "xri": 9.8, "zri": 1.0, "xri_absolute": True, "zri_absolute": True}
    lines = generate_thread_gcode(
        op,
        settings,
        require_tool=lambda p, _label: int(p["tool"]),
        get_tool_number=lambda p: int(p["tool"]),
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
        emit_approach=_emit_approach,
        sanitize_comment_text=str,
    )
    assert any(line.startswith("G76 ") for line in lines)


def test_external_thread_records_real_end_position_not_stale_approach():
    """LES-022 (dritte Etappe): vor dieser Korrektur aktualisierte
    `generate_thread_gcode()` den gemeinsamen Bewegungszustand nach G76
    ueberhaupt nicht - er blieb auf der zuletzt VOR dem Gewinde bekannten
    Position stehen (hier: gar nichts, da die injizierte `_emit_approach`
    in diesem Test bewusst keinen Zustand setzt). Real (per rs274 verifiziert)
    endet G76 aber IMMER exakt bei (approach_x, end_z) - dem tiefsten Punkt
    des letzten Gewindeschnitts, OHNE automatischen Rueckzug. Ein Folgeschritt,
    der sich auf einen veralteten Zustand verlaesst, koennte einen noetigen
    Rueckzug faelschlich als bereits erledigt ansehen."""
    op = Operation(
        OpType.THREAD,
        {
            "tool": 3, "spindle": 500.0, "pitch": 1.5, "length": 20.0,
            "major_diameter": 10.0, "thread_start_z": 0.0,
        },
        path=[],
    )
    settings = {"xt": 150.0, "zt": 300.0}
    lines = generate_thread_gcode(
        op, settings,
        require_tool=lambda p, _label: int(p["tool"]),
        get_tool_number=lambda p: int(p["tool"]),
        append_tool_and_spindle=_append_tool_and_spindle,
        emit_coolant=_emit_coolant,
        emit_approach=_emit_approach,
        sanitize_comment_text=str,
    )
    # Erwartete Werte direkt aus der eigenen Ausgabe ableiten statt separat
    # nachzurechnen: die letzte "G0 X.."-Zeile vor G76 ist approach_x, das
    # Z-Wort der G76-Zeile ist end_z.
    g76_idx = next(i for i, ln in enumerate(lines) if ln.startswith("G76 "))
    approach_line = next(ln for ln in reversed(lines[:g76_idx]) if ln.startswith("G0 X"))
    expected_x = float(next(w[len("X"):] for w in approach_line.split() if w.startswith("X")))
    expected_z = float(next(w[1:] for w in lines[g76_idx].split() if w.startswith("Z")))

    state = settings["_motion"]
    assert isinstance(state, MotionState)
    # tol groesser als das Standard-1e-6: expected_x/z sind aus der auf drei
    # Nachkommastellen gerundeten Textausgabe geparst, der Zustand haelt die
    # ungerundeten internen Werte.
    assert state.at(expected_x, expected_z, tol=1e-3)
