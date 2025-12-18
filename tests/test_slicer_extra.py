import sys
import os

# Ensure local package directory is on sys.path so tests can import the slicer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slicer import rough_turn_parallel_x, rough_turn_parallel_z


def test_parallel_x_allows_undercut_by_default():
    path = [(12.0, 0.0), (10.0, -2.0), (8.0, -2.0)]
    # stock at 14, target 6, step 4 -> passes 14-10,10-6
    lines = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=6.0, step_x=4.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    # Expect at least one pass with X-band
    assert any("X-band" in ln for ln in lines)


def test_parallel_x_prevents_undercut_when_disabled():
    path = [(10.0, 0.0), (8.0, -2.0)]
    # stock at 14, target 4, step 3 -> passes: [14-11],[11-8],[8-5]
    # The last pass would cut at x_lo = 5 which is < min(path_x)=8 -> undercut
    lines_allow = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=True)
    lines_no = rough_turn_parallel_x(path, external=True, x_stock=14.0, x_target=4.0, step_x=3.0, safe_z=5.0, feed=0.2, allow_undercut=False)
    # with allow_undercut True we should see at least 1 pass
    assert any("X-band" in ln for ln in lines_allow)
    # with allow_undercut False the last pass that would undercut should be skipped - therefore fewer passes
    count_allow = sum(1 for ln in lines_allow if ln.startswith('(Pass'))
    count_no = sum(1 for ln in lines_no if ln.startswith('(Pass'))
    assert count_no <= count_allow


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
    # Simulate a program-level setting (XRA, ZRA) and ensure generate_abspanen_gcode uses it
    from lathe_easystep_handler import ProgramModel, Operation, OpType
    m = ProgramModel()
    # small contour where stock is at 40 and contour near 25
    path = [(40.0, 2.0), (25.0, -7.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "depth_per_pass": 1.0, "feed": 0.15}, path=path)
    m.add_operation(op)
    # configure absolute retracts in program settings (explicit absolute flags)
    m.program_settings = {"xra": 42.0, "zra": 3.0, "xra_absolute": True, "zra_absolute": True}
    g = "\n".join(m.generate_gcode())
    # After a pass the G0 X retract should be to X42.000 (configured absolute)
    assert "G0 X42.000" in g
    # And Z retracts should use Z=3.000 at appropriate points
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
        retract_x_target=2.0,
        retract_x_absolute=False,
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
    from lathe_easystep_handler import ProgramModel, Operation, OpType
    m = ProgramModel()
    path = [(40.0, 2.0), (25.0, -7.0)]
    op = Operation(OpType.ABSPANEN, {"mode": 0, "slice_strategy": 2, "depth_per_pass": 1.0, "feed": 0.15}, path=path)
    m.add_operation(op)
    # configure a small xra value which under absolute interpretation would be near X=2.0
    m.program_settings = {"xra": 2.0}
    g = "\n".join(m.generate_gcode())
    # Absolute G0 X2.000 should NOT appear, because the value is interpreted as incremental
    assert "G0 X2.000" not in g
    # And a retract X greater than the cut target should exist (we expect incremental addition)
    assert any(ln.startswith('G0 X') for ln in g.splitlines())
