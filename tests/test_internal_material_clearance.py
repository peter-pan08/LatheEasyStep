import pytest

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_utils import validate_internal_material_clearance
from lathe_easystep.model import Operation, OpType

# LES-005: "zuerst auf nachweislich freien Innendurchmesser fahren". Die
# axiale Eilgangebene XRI muss innerhalb von Material liegen, das laut
# Programmkopf (XI, vorgebohrtes/Rohr-Rohteil) oder einer vorangehenden
# Bohren-Operation bereits nachweislich offen ist - sonst faehrt der
# Eilgang moeglicherweise durch stehengebliebenes Vollmaterial.


def test_xi_covering_whole_workpiece_allows_any_z():
    validate_internal_material_clearance(
        {"xi": 12.0}, safe_x=9.0, z_values=[-500.0, 2.0], op_label="Test"
    )


def test_xi_smaller_than_xri_blocks():
    with pytest.raises(ValueError, match="XI"):
        validate_internal_material_clearance(
            {"xi": 8.0}, safe_x=9.0, z_values=[-10.0], op_label="Test"
        )


def test_no_known_open_diameter_stays_silent():
    """Weder XI noch eine vorangehende Bohrung bekannt - keine gesicherte
    Aussage moeglich, bewusst kein Fehler (separate Reihenfolge-Warnung in
    checks.py::validate_program_setup deckt diesen Fall ab)."""
    validate_internal_material_clearance(
        {"xi": 0.0}, safe_x=9.0, z_values=[-10.0], op_label="Test"
    )
    validate_internal_material_clearance(
        {}, safe_x=9.0, z_values=[-10.0], op_label="Test"
    )


def test_drill_diameter_and_depth_covering_range_allows():
    validate_internal_material_clearance(
        {"_last_drill_diameter": 9.5, "_last_drill_depth": -30.0},
        safe_x=9.0,
        z_values=[-29.5, 2.0],
        op_label="Test",
    )


def test_drill_diameter_too_small_blocks():
    with pytest.raises(ValueError, match="Bohrung"):
        validate_internal_material_clearance(
            {"_last_drill_diameter": 8.0, "_last_drill_depth": -50.0},
            safe_x=9.0,
            z_values=[-10.0],
            op_label="Test",
        )


def test_drill_diameter_sufficient_but_too_shallow_blocks():
    with pytest.raises(ValueError, match="Bohrtiefe"):
        validate_internal_material_clearance(
            {"_last_drill_diameter": 9.5, "_last_drill_depth": -20.0},
            safe_x=9.0,
            z_values=[-25.0, 2.0],
            op_label="Test",
        )


def test_xi_takes_priority_even_if_drill_diameter_insufficient():
    """XI beschreibt das gesamte Rohteil - reicht es allein aus, ist der
    (kleinere) Bohrdurchmesser fuer diese Pruefung irrelevant."""
    validate_internal_material_clearance(
        {"xi": 12.0, "_last_drill_diameter": 5.0, "_last_drill_depth": -5.0},
        safe_x=9.0,
        z_values=[-100.0],
        op_label="Test",
    )


def _internal_op(xri, tool=11, mode="finish"):
    settings = dict(make_program_settings(), xi=0.0, xri=xri, zri=2.0,
                     xri_absolute=True, zri_absolute=True)
    op = Operation(
        OpType.ABSPANEN,
        {"side": "inside", "mode": mode, "tool": tool, "spindle": 800.0,
         "feed": .15, "depth_per_pass": .5, "slice_strategy": "parallel_z"},
        path=[(12.0, -30.0), (18.0, 0.0)],
    )
    return op, settings


def test_generation_blocks_when_no_drill_and_xri_exceeds_drilled_hint():
    """Ohne XI und ohne vorangehende Bohrung bleibt die Materialfreiheits-
    pruefung selbst stumm (siehe test_no_known_open_diameter_stays_silent) -
    end-to-end mit `generate_program_gcode` bestaetigt, dass allein ein
    fehlender Nachweis kein neuer Fehler wird (nur die bestehende
    Reihenfolge-Warnung greift dafuer, siehe test_drill_before_internal_check.py)."""
    op, settings = _internal_op(xri=9.0)
    generate_program_gcode([op], settings)  # darf nicht werfen


def test_generation_blocks_when_drill_diameter_too_small_for_xri():
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0,
         "diameter": 8.0},
        path=[(0.0, 2.0), (0.0, -35.0)],
    )
    op, settings = _internal_op(xri=9.0)
    with pytest.raises(ValueError, match="Bohrung"):
        generate_program_gcode([drill, op], settings)


def test_generation_accepts_when_drill_diameter_and_depth_are_sufficient():
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0,
         "diameter": 9.2},
        path=[(0.0, 2.0), (0.0, -35.0)],
    )
    op, settings = _internal_op(xri=9.0)
    lines = generate_program_gcode([drill, op], settings)
    assert any(line.startswith("(Schlichtschnitt Kontur)") for line in lines)


def test_generation_blocks_when_drill_does_not_reach_full_depth():
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0,
         "diameter": 9.2},
        path=[(0.0, 2.0), (0.0, -20.0)],
    )
    op, settings = _internal_op(xri=9.0)
    with pytest.raises(ValueError, match="Bohrtiefe"):
        generate_program_gcode([drill, op], settings)
