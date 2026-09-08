import sys
import os
import pytest

# Ensure local package directory is on sys.path so tests can import the real modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep.gcode_roughing import (
    RetractCfg,
    generate_abspanen_gcode,
    rough_turn_parallel_x,
    rough_turn_parallel_z,
)
from lathe_easystep_handler import ProgramModel, Operation, OpType


def test_parallel_x_finds_real_material_not_a_hairline_sliver():
    """Die Materialreichweite-Baenderung (siehe rough_turn_parallel_x,
    reach_lo/reach_hi statt eines hauchduennen x_cut+/-1e-3-Fensters) findet
    fuer ein Band innerhalb der Kontur einen echten, spuerbaren Schnitt -
    nicht nur einen ~0.001mm-Splitter nahe der Kontur-Kante (das war der
    vorherige Fensterfehler, den ein frueherer Test hier unbeabsichtigt als
    'Undercut-Erfolg' interpretierte)."""
    path = [(12.0, 0.0), (6.0, -8.0)]
    lines = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=6.0, step_x=4.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    pass_1 = lines.index("(Pass 1: X-band [10.000,14.000])")
    pass_2_or_end = next((i for i, ln in enumerate(lines) if i > pass_1 and ln.startswith("(Pass")), len(lines))
    pass_1_g1 = [ln for ln in lines[pass_1:pass_2_or_end] if ln.startswith("G1 ")]
    # Der Schnitt muss die volle verbleibende Tiefe abdecken (Z-2.667 bis
    # Z-8.000, gut 5mm) - nicht nur einen ~0.003mm-Splitter am Kontur-Rand
    # (das lieferte das alte schmale x_cut+/-1e-3-Fenster).
    assert any("Z-8.000" in ln for ln in pass_1_g1)
    assert any("Z-2.667" in ln for ln in pass_1_g1)


def test_parallel_x_pass_beyond_contour_extent_has_no_material_regardless_of_flag():
    """Eine Zustellung, deren x_cut ueber die eigene Kontur-Grenze
    hinausgeht (echtes Unterschneiden/Undercut), kann mit der korrigierten
    Materialreichweite-Baenderung strukturell nie einen echten Schnitt
    finden - dort existieren schlicht keine Kontursegmente mehr. Die
    allow_undercut-Sperre bleibt als Sicherheitsnetz bestehen, hat bei der
    korrekten Baenderung aber keinen beobachtbaren Effekt mehr: sie griff
    zuvor gegen hauchduenne Kanten-Splitter, die es mit dem Fensterfehler-Fix
    nicht mehr gibt."""
    path = [(10.0, 0.0), (8.0, -2.0)]
    lines_allow = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    lines_no = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    assert lines_allow == lines_no
    # Nur der erste (innerhalb der Kontur liegende) Pass schneidet wirklich;
    # alle Baender jenseits der Kontur-Grenze (X<=8) melden "no cut region".
    assert "(Pass 1: X-band [11.000,14.000])" in lines_allow
    assert sum(1 for ln in lines_allow if "no cut region" in ln) == 3


def test_parallel_x_internal_produces_passes():
    path = [(6.0, 0.0), (8.0, -2.0), (10.0, -2.0)]
    lines = rough_turn_parallel_x(path, external=False, x_stock=4.0, x_target=10.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    assert any("X-band" in ln for ln in lines)


def test_parallel_z_basic_behavior():
    path = [(10.0, -1.0), (12.0, -3.0), (14.0, -3.0)]
    # external True, z_stock=max z = -1, z_target = -3, step_z=1 => passes
    lines = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=-1.0,
        z_target=-3.0,
        step_z=1.0,
        safe_z=5.0,
        feed=0.2,
        start_x=16.0,
        allow_undercut=True,
    )
    assert any("Z-band" in ln for ln in lines)


def test_parallel_z_respects_undercut():
    path = [(8.0, -1.0), (10.0, -3.0)]
    lines_allow = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=-1.0,
        z_target=-4.0,
        step_z=1.0,
        safe_z=5.0,
        feed=0.2,
        start_x=11.0,
        allow_undercut=True,
    )
    lines_no = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=-1.0,
        z_target=-4.0,
        step_z=1.0,
        safe_z=5.0,
        feed=0.2,
        start_x=11.0,
        allow_undercut=False,
    )
    assert any("Z-band" in ln for ln in lines_allow)
    count_allow = sum(1 for ln in lines_allow if ln.startswith('(Pass'))
    count_no = sum(1 for ln in lines_no if ln.startswith('(Pass'))
    assert count_no <= count_allow


def test_parallel_z_horizontal_cut():
    path = [(19.0, 0.0), (20.5, -1.5), (22.0, -3.0)]
    lines = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=0.0,
        z_target=-3.0,
        step_z=0.5,
        safe_z=2.0,
        feed=0.15,
        start_x=24.0,
    )
    # Expect at least one vertical Z movement (G1 Z...)
    assert any(ln.startswith('G1 Z') for ln in lines)


def test_parallel_z_inward_progression():
    # Ensure that for external stock X cut targets progress monotonically inward (non-increasing)
    path = [(40.0, 2.0), (25.0, -7.0)]
    lines = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=2.0,
        z_target=-7.0,
        step_z=1.0,
        safe_z=4.0,
        feed=0.15,
        start_x=40.0,
    )
    # Extract cut X targets from 'G1 X' lines that follow a 'G1 Z' per pass
    cut_xs = []
    for i, ln in enumerate(lines):
        if ln.startswith('G1 Z'):
            # next non-empty G1 X line
            for j in range(i+1, min(i+4, len(lines))):
                if lines[j].startswith('G1 X'):
                    parts = lines[j].split()
                    for part in parts:
                        if part.startswith('X'):
                            try:
                                cut_xs.append(float(part[1:]))
                            except Exception:
                                pass
                    break
    # Ensure the cut Xs exist and are non-increasing (moving inward)
    assert cut_xs, 'no cut X targets found'
    assert all(cut_xs[i] >= cut_xs[i+1] - 1e-6 for i in range(len(cut_xs)-1))


def test_parallel_z_respects_configured_retracts_via_generate():
    # For cycle-based output (monotonic path), retracts are implicit in the cycle.
    # Test with non-monotonic X to force move-based roughing where retracts are visible.
    m = ProgramModel()
    path = [(40.0, 2.0), (25.0, -3.0), (30.0, -5.0), (25.0, -7.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "depth_per_pass": 1.0, "feed": 0.15, "tool": 1}, path=path)
    m.add_operation(op)
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 42.0, "zra": 3.0, "xra_absolute": True, "zra_absolute": True}
    g = "\n".join(m.generate_gcode())
    # Move-based: After a pass the G0 X retract should be to X42.000 (configured absolute)
    assert "G0 X42.000" in g
    # And Z retracts should use Z=3.000
    assert "G0 Z3.000" in g


def test_parallel_z_retract_incremental_delta_behaviour():
    # When the configured retract X is marked as incremental, it should be
    # applied relative to the current cut X (not treated as an absolute coord).
    path = [(40.0, 2.0), (25.0, -7.0)]
    lines = rough_turn_parallel_z(
        path,
        external=True,
        z_stock=2.0,
        z_target=-7.0,
        step_z=1.0,
        safe_z=4.0,
        feed=0.15,
        start_x=40.0,
        retract_cfg=RetractCfg(x_value=2.0, z_value=None, x_absolute=False, z_absolute=True),
    )
    # find a pass: G1 Z... followed by G1 X<cut> then G0 X<retract>
    found = False
    for i, ln in enumerate(lines):
        if ln.startswith('G1 Z'):
            # look for the next G1 X and following G0 X
            cut_x = None
            for j in range(i+1, min(i+6, len(lines))):
                if lines[j].startswith('G1 X'):
                    # extract cut X
                    for part in lines[j].split():
                        if part.startswith('X'):
                            cut_x = float(part[1:])
                            break
                if lines[j].startswith('G0 X') and cut_x is not None:
                    # extract retract X
                    for part in lines[j].split():
                        if part.startswith('X'):
                            retract_x = float(part[1:])
                            # retract should be cut_x + 2.0 (incremental)
                            assert abs(retract_x - (cut_x + 2.0)) < 1e-6
                            found = True
                            break
                if found:
                    break
        if found:
            break
    assert found, 'did not find expected retract sequence'


def test_parallel_z_retract_default_incremental_behaviour():
    # If a program setting provides 'xra' but no 'xra_absolute' flag, the
    # generator should treat the value as incremental (new default behaviour).
    # Use non-monotonic X to force move-based roughing.
    m = ProgramModel()
    path = [(40.0, 2.0), (25.0, -3.0), (30.0, -5.0), (25.0, -7.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "depth_per_pass": 1.0, "feed": 0.15, "tool": 1}, path=path)
    m.add_operation(op)
    # configure a small xra value which under absolute interpretation would be near X=2.0
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 2.0, "zra": 5.0}
    g = "\n".join(m.generate_gcode())
    # Absolute G0 X2.000 should NOT appear, because the value is interpreted as incremental
    assert "G0 X2.000" not in g
    # And a retract X greater than the cut target should exist (we expect incremental addition)
    assert any(ln.startswith('G0 X') for ln in g.splitlines())


def test_parallel_x_skips_degenerate_intervals():
    # Horizontal Kontur -> Schnittbereich hat Länge 0 und darf keinen G1-Schnitt erzeugen
    path = [(12.0, 0.0), (10.0, 0.0)]
    lines = rough_turn_parallel_x(
        path,
        external=True,
        x_stock=12.0,
        x_target=10.0,
        step_x=1.0,
        safe_z=2.0,
        feed=0.1,
    )
    assert not any(ln.startswith('G1 Z0.000') for ln in lines)


def test_abspanen_respects_program_clearance_and_retract():
    # Use non-monotonic X to force move-based roughing
    path = [(40.0, 0.0), (30.0, -5.0), (35.0, -7.0), (30.0, -10.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 1, "depth_per_pass": 2.0, "feed": 0.2, "tool": 1}, path=path)
    m = ProgramModel()
    m.add_operation(op)
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "sc": 3.0,
        "xa": 40.0,
        "xra": 45.0,
        "xra_absolute": True,
        "zra": 5.0,
        "zra_absolute": True,
    }
    g = "\n".join(m.generate_gcode())
    assert "G0 Z5.000" in g
    assert "G0 X45.000" in g


def test_parallel_x_retract_default_incremental_behaviour():
    # Use non-monotonic X to force move-based roughing (X goes 40->30->35->25)
    path = [(40.0, 0.0), (30.0, -5.0), (35.0, -7.0), (25.0, -10.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 1, "depth_per_pass": 2.0, "feed": 0.2, "tool": 1}, path=path)
    m = ProgramModel()
    m.add_operation(op)
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xa": 40.0, "xra": 2.0, "zra": 5.0}  # Standard: inkrementell
    g = "\n".join(m.generate_gcode())
    # Absoluter Rückzug auf X2.000 darf nicht auftreten
    assert "G0 X2.000" not in g
    # Rückzug soll relativ zum Schnitt erfolgen (hier 2 mm über dem aktuellen Schnittniveau)
    found_delta = False
    lines = g.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("G1 X") and "Z" in ln:
            try:
                cut_x = float(ln.split()[1][1:])
            except Exception:
                continue
            # look ahead for the next retract X
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].startswith("G0 X"):
                    try:
                        retract_x = float(lines[j].split()[1][1:])
                    except Exception:
                        continue
                    if abs(retract_x - (cut_x + 2.0)) < 1e-6:
                        found_delta = True
                        break
            if found_delta:
                break
    assert found_delta, "inkrementeller Rückzug (cut_x + 2.0) wurde nicht gefunden"


def test_parallel_x_retract_settings_required():
    path = [(40.0, 0.0), (25.0, -5.0)]
    params = {"mode": 0, "slice_strategy": 1, "depth_per_pass": 1.0, "feed": 0.15, "tool": 1}
    settings = {"xt": 150.0, "zt": 300.0, "sc": 1.0}
    with pytest.raises(ValueError):
        generate_abspanen_gcode(params, path, settings)


def test_program_unit_inch_emits_g20():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(20.0, 0.0), (18.0, -2.0)],
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "unit": "inch",
        "xra": 45.0,
        "zra": 5.0,
        "xra_absolute": True,
        "zra_absolute": True,
    }
    g = "\n".join(m.generate_gcode())
    assert "G20" in g
    assert "G21" not in g


def test_face_cycle_sub_uses_feed_moves_only():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.FACE,
            {
                "mode": 0,
                "start_x": 40.0,
                "start_z": 1.0,
                "end_x": 5.0,
                "end_z": 0.0,
                "finish_allow_z": 0.1,
                "depth_max": 0.4,
                "retract": 0.5,
                "feed": 0.2,
                "spindle": 1200.0,
                "tool": 1,
                "edge_type": 0,
                "edge_size": 0.0,
                "coolant": False,
            },
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0, "xra_absolute": True, "zra_absolute": True}
    g = "\n".join(m.generate_gcode())
    sub_block = g.split("o100 sub", 1)[1].split("o100 endsub", 1)[0]
    assert "G0" not in sub_block
    assert "G1 X" in sub_block


def test_global_safe_retract_respects_incremental_flags():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(20.0, 0.0), (18.0, -2.0)],
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "xa": 40.0,
        "za": 0.0,
        "xra": 2.0,
        "zra": 5.0,
        "xra_absolute": False,
        "zra_absolute": False,
    }
    lines = m.generate_gcode()
    assert "G0 X42.000 Z5.000" in lines


def test_turn_uses_simultaneous_safe_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(20.0, 0.0), (18.0, -2.0)],
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0, "xra_absolute": True, "zra_absolute": True}
    lines = m.generate_gcode()
    assert "G0 X45.000 Z5.000" in lines


def test_groove_uses_x_then_z_safe_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.GROOVE,
            {
                "tool": 1,
                "spindle": 1200.0,
                "feed": 0.2,
                "safe_z": 2.0,
                "mode": 0,
                "lage": 0,
                "wnut": 2.0,
                "A_start": 30.0,
                "A_end": 28.0,
                "C": -10.0,
                "stepA": 0.5,
                "retract": 0.5,
            },
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0, "xra_absolute": True, "zra_absolute": True}
    lines = m.generate_gcode()
    # Die sichere EINFAHRT (vor dem Zyklusaufruf) nutzt bewusst Z-dann-X (siehe
    # emit_approach()/get_safe_position()) und kann zufaellig dieselben
    # X/Z-Werte wie die RUECKZUGS-Sequenz nach dem Schnitt treffen (hier:
    # xra=45/zra=5 fuer beide). lines.index() faende sonst die Einfahrt statt
    # des Rueckzugs - deshalb erst ab dem Zyklusaufruf suchen.
    cycle_idx = next(i for i, l in enumerate(lines) if l.startswith("o220 call"))
    retract_lines = lines[cycle_idx:]
    idx_x = retract_lines.index("G0 X45.000")
    idx_z = retract_lines.index("G0 Z5.000")
    assert idx_x < idx_z


def test_drill_uses_z_then_x_safe_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.DRILL,
            {"tool": 1, "feed": 0.12, "safe_z": 2.0, "mode": 0},
            path=[(10.0, 0.0), (10.0, -5.0)],
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0, "xra": 45.0, "zra": 5.0, "xra_absolute": True, "zra_absolute": True}
    lines = m.generate_gcode()
    idx_z = lines.index("G0 Z5.000")
    idx_x = lines.index("G0 X45.000")
    assert idx_z < idx_x


def test_turn_inside_stock_falls_back_to_x_then_z_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(30.0, 0.0), (28.0, -10.0)],
        )
    ]
    # Endpunkt liegt im Rohteilbereich: X in [0..40], Z in [-20..0]
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "xa": 40.0,
        "za": 0.0,
        "zi": -20.0,
        "xra": 45.0,
        "zra": 5.0,
        "xra_absolute": True,
        "zra_absolute": True,
    }
    lines = m.generate_gcode()
    # Ab dem Step selbst pruefen: der Werkzeugwechsel davor faehrt legitim per
    # kombiniertem G0 X.../Z... auf die sichere Position (siehe
    # append_tool_and_spindle()) - das ist eine andere, bereits abgesicherte
    # Bewegung als der hier zu testende Rueckzug NACH dem eigentlichen Schnitt.
    step_lines = lines[lines.index("(Step 1: turn)"):]
    assert "G0 X45.000 Z5.000" not in step_lines
    idx_x = step_lines.index("G0 X45.000")
    idx_z = step_lines.index("G0 Z5.000")
    assert idx_x < idx_z


def test_turn_outside_stock_keeps_simultaneous_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(45.0, 2.0), (46.0, 3.0)],
        )
    ]
    # Endpunkt liegt außerhalb des Rohteils, simultan ist erlaubt
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "xa": 40.0,
        "za": 0.0,
        "zi": -20.0,
        "xra": 48.0,
        "zra": 6.0,
        "xra_absolute": True,
        "zra_absolute": True,
    }
    lines = m.generate_gcode()
    assert "G0 X48.000 Z6.000" in lines


def test_turn_in_chuck_nogo_falls_back_to_x_then_z_retract():
    m = ProgramModel()
    m.operations = [
        Operation(
            OpType.TURN,
            {"tool": 1, "feed": 0.2, "safe_z": 2.0},
            path=[(30.0, 0.0), (40.0, -50.0)],
        )
    ]
    m.program_settings = {"xt": 150.0, "zt": 300.0,
        "xra": 60.0,
        "zra": 6.0,
        "xra_absolute": True,
        "zra_absolute": True,
        "za": 0.0,
        "chuck_no_go_x_min": 20.0,
        "chuck_no_go_x_max": 80.0,
        "chuck_no_go_z_limit": -40.0,
    }
    lines = m.generate_gcode()
    step_lines = lines[lines.index("(Step 1: turn)"):]
    assert "G0 X60.000 Z6.000" not in step_lines
    idx_x = step_lines.index("G0 X60.000")
    idx_z = step_lines.index("G0 Z6.000")
    assert idx_x < idx_z
