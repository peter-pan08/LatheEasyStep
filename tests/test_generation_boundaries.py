from copy import deepcopy
from types import SimpleNamespace
import json

import pytest

from lathe_easystep.examples import example_programs, make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_safety import (
    emit_approach,
    emit_safe_retract_for_op,
    append_tool_and_spindle,
    get_approach_warnings,
    move_to_toolchange_pos,
    validate_chuck_segment,
    validate_stock_segment,
)
from lathe_easystep.gcode_utils import require_positive, get_tool_number
from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.motion_state import MotionState
from lathe_easystep.persistence import step_data_to_operation
from lathe_easystep.storage import parse_program_payload
from lathe_easystep import ui_persistence


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "NaN", "inf", "-Infinity", "1e999"])
def test_nonfinite_values_rejected_before_geometry_and_export(value):
    with pytest.raises(ValueError):
        require_positive({"feed": value}, ["feed"], "face")
    with pytest.raises(ValueError):
        step_data_to_operation({"op_type": "face", "params": {"feed": value}})
    with pytest.raises(ValueError):
        parse_program_payload({"version": 1, "header": {"xt": value}}, "test.lse")
    model = ProgramModel(geometry_builders={"face": lambda p: pytest.fail("geometry must not run")})
    with pytest.raises(ValueError):
        model.update_geometry(Operation("face", {"start_x": value}))
    ops, settings = example_programs()["Planen.ngc"]
    ops[-1].params["start_x"] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)


@pytest.mark.parametrize("value", [1.5, "2.9", -1, True, "nan", "bad"])
def test_invalid_tool_numbers_are_not_truncated(value):
    with pytest.raises(ValueError):
        get_tool_number({"tool": value})


@pytest.mark.parametrize("filename", list(example_programs()))
def test_generation_is_repeatable_and_leaves_input_unchanged(filename):
    ops, settings = example_programs()[filename]
    before = deepcopy((ops, settings))
    first = generate_program_gcode(ops, settings)
    assert generate_program_gcode(ops, settings) == first
    assert (ops, settings) == before


def test_removed_contour_never_reuses_cached_geometry_and_failure_is_immutable():
    ops, settings = example_programs()["Abdrehen.ngc"]
    ops[-1].params["_primitives"] = [{"type": "line", "p1": (900, 0), "p2": (900, -5)}]
    ops[-1].params["_contour_params"] = {"start_x": 900, "start_z": 0, "segments": [{"x": 900, "z": -5}]}
    # Named contour is the authoritative source, not cached operation geometry.
    assert "X900" not in "\n".join(generate_program_gcode(ops, settings))
    ops.pop(1)
    before = deepcopy((ops, settings))
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)
    assert (ops, settings) == before


def _chuck_settings():
    return dict(make_program_settings(), xa=50, xi=0, za=0, zi=-50, xra=5, zra=5,
                chuck_no_go_x_min=0, chuck_no_go_x_max=100, chuck_no_go_z_limit=-40)


def test_chuck_collision_blocks_approach_and_keeps_existing_export(tmp_path):
    settings = _chuck_settings()
    lines = []
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        emit_approach(lines, 30, -45, settings)
    assert lines == []
    ops, _ = example_programs()["Planen.ngc"]
    ops[-1].params.update(start_x=30, start_z=-45, end_z=-45)
    target = tmp_path / "program.ngc"
    target.write_text("old program")
    handler = SimpleNamespace(_normalized_file_path=str, _build_gcode_lines=lambda: generate_program_gcode(ops, settings))
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        ui_persistence.write_gcode_file(handler, str(target))
    assert target.read_text() == "old program"


@pytest.mark.parametrize("direction", [1, -1])
def test_chuck_segment_crossing_with_both_endpoints_outside(direction):
    settings = _chuck_settings()
    settings["chuck_no_go_z_limit"] = -40 * direction
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        validate_chuck_segment(settings, (-10, -45 * direction), (110, -45 * direction))
    validate_chuck_segment(settings, (-10, 5 * direction), (110, 5 * direction))


def _stock_settings():
    return dict(make_program_settings(), xa=50, xi=0, za=0, zi=-50, xra=10, zra=10)


def test_stock_segment_crossing_with_both_endpoints_outside():
    settings = _stock_settings()
    # Diagonal von einer Ecke ausserhalb der Huellkurve zur gegenueberliegenden
    # Ecke: beide Endpunkte liegen einzeln ausserhalb, die Strecke schneidet
    # aber mitten durch das Rohteil-Rechteck X0..50/Z-50..0.
    with pytest.raises(ValueError, match="Rohteil"):
        validate_stock_segment(settings, (-10, -60), (60, 10))
    # Bleibt die Strecke auf einer Seite ausserhalb (hier X immer < 0), ist
    # sie unbedenklich.
    validate_stock_segment(settings, (-10, -60), (-10, 10))


def test_chuck_zone_warning_does_not_contradict_the_actually_safe_path():
    """LES-001: 'Warnung und tatsaechlicher Fahrweg duerfen sich nicht
    widersprechen'. Die Rueckzugsebenen-Warnung pruefte bisher nur den
    Z-Grenzwert der Futter-Sperrzone, nicht das X-Intervall - dieselbe
    Ruecksicht wie validate_chuck_segment(). Eine sichere Position, deren X
    ausserhalb der Sperrzone liegt, durfte nicht als gefaehrdet gemeldet
    werden, obwohl der tatsaechliche (durch validate_chuck_segment bereits
    abgesicherte) Fahrweg dort nie hinfuehrt."""
    base = dict(
        _stock_settings(),
        chuck_no_go_z_limit=20,  # sicheres Z(10) liegt <= 20: Z-Grenzwert allein wuerde ausloesen
    )
    # X60 (die sichere Position) liegt AUSSERHALB des Sperr-X-Bereichs -
    # keine echte Gefaehrdung, die Warnung darf nicht erscheinen.
    safe_settings = dict(base, chuck_no_go_x_min=0, chuck_no_go_x_max=50)
    warnings = get_approach_warnings(safe_settings, (20.0, -20.0))
    assert not any("schneidet den Futterbereich" in w for w in warnings)

    # X60 liegt INNERHALB des Sperr-X-Bereichs - hier ist die Warnung
    # berechtigt.
    unsafe_settings = dict(base, chuck_no_go_x_min=0, chuck_no_go_x_max=100)
    warnings = get_approach_warnings(unsafe_settings, (20.0, -20.0))
    assert any("schneidet den Futterbereich" in w for w in warnings)


def test_external_safe_retract_blocks_diagonal_through_stock():
    settings = _stock_settings()
    lines = []
    # Aktueller Endpunkt und externe Sicherheitsposition liegen je fuer sich
    # ausserhalb der Rohteil-Huellkurve, der direkte Diagonal-Eilgang
    # zwischen beiden wuerde aber durch das Rohteil fuehren.
    with pytest.raises(ValueError, match="Rohteil"):
        emit_safe_retract_for_op(lines, settings, OpType.FACE, current_pos=(-10, -60))
    assert lines == []


def test_internal_safe_retract_skips_stock_rectangle_check():
    # Die Rohteil-Huellkurve bildet keine Bohrung ab; eine interne
    # Sicherheitsposition nahe der Bohrungswand darf deshalb nicht gegen das
    # Aussenrechteck blockiert werden, auch wenn dieselbe Geometrie im
    # Aussen-Fall oben blockiert wird.
    settings = dict(
        _stock_settings(),
        xri=60, xri_absolute=True, zri=10, zri_absolute=True,
        _active_retract_mode="internal",
    )
    lines = []
    emit_safe_retract_for_op(lines, settings, OpType.FACE, current_pos=(-10, -60))
    assert lines == ["G0 X60.000 Z10.000"]


def test_toolchange_position_blocks_diagonal_through_stock():
    # Externe Sicherheitsposition liegt bei (60, 10); eine Werkzeugwechsel-
    # position auf der gegenueberliegenden Ecke (-10, -60) waere fuer sich
    # ausserhalb der Huellkurve, der direkte Diagonal-Eilgang dorthin
    # durchquert aber das Rohteil-Rechteck X0..50/Z-50..0.
    settings = dict(_stock_settings(), xt=-10, zt=-60)
    with pytest.raises(ValueError, match="Rohteil"):
        move_to_toolchange_pos(settings)


@pytest.mark.parametrize(
    "op_type,expected_order",
    [
        (OpType.GROOVE, ["G0 X60.000", "G0 Z10.000"]),
        (OpType.KEYWAY, ["G0 X60.000", "G0 Z10.000"]),
        (OpType.DRILL, ["G0 Z10.000", "G0 X60.000"]),
        (OpType.THREAD, ["G0 Z10.000", "G0 X60.000"]),
    ],
)
def test_safe_retract_axis_order_is_operation_specific(op_type, expected_order):
    """LES-001: Bohren/Gewinde muessen axial (Z) vor radial (X) zurueckziehen,
    unabhaengig vom Startpunkt - ein im Einstich/Gewindegang stehendes
    Werkzeug darf nicht zuerst radial bewegt werden. Einstich/Keilnut ist
    umgekehrt (X vor Z), wie fuer ein im Nutgrund stehendes Werkzeug noetig."""
    settings = _stock_settings()
    lines = []
    emit_safe_retract_for_op(lines, settings, op_type, current_pos=(25, -25))
    assert lines == expected_order


def test_groove_second_leg_retract_blocks_chuck_violation():
    """LES-001: bei Einstich/Keilnut haelt der zweite Rueckzugsschritt (Z bei
    konstantem X=XRA) - eine zu klein gewaehlte XRA, die noch in der Futter-
    Sperrzone liegt, darf die restliche Z-Strecke nicht ungeprueft
    durchqueren."""
    settings = dict(_stock_settings(), chuck_no_go_x_min=0, chuck_no_go_x_max=100, chuck_no_go_z_limit=-40)
    lines = []
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        emit_safe_retract_for_op(lines, settings, OpType.GROOVE, current_pos=(25, -45))
    assert lines == []


def test_sequential_retract_from_chuck_nogo_requires_xra_to_clear_the_zone():
    """Realer Bugreport (reproduziert aus test_slicer_extra.py): mit XRA=60
    bei einer Futter-Sperrzone X20..80 verlaesst der erste Rueckzugsschritt
    (X auf XRA) die Sperrzone NICHT wirklich - der anschliessende Z-Zwischen-
    zug bei konstantem X=60 wuerde die gesamte restliche Z-Strecke durch die
    Sperrzone fuehren. Eine XRA, die die Zone tatsaechlich verlaesst (hier 90),
    ist dagegen sicher."""
    base = dict(
        _stock_settings(),
        chuck_no_go_x_min=20, chuck_no_go_x_max=80, chuck_no_go_z_limit=-40,
    )
    unsafe = dict(base, xra=10)  # x_safe = xa(50) + xra(10) = 60, noch in der Zone
    lines = []
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        emit_safe_retract_for_op(lines, unsafe, OpType.FACE, current_pos=(40, -50))
    assert lines == []

    safe = dict(base, xra=40)  # x_safe = xa(50) + xra(40) = 90, ausserhalb der Zone
    lines = []
    emit_safe_retract_for_op(lines, safe, OpType.FACE, current_pos=(40, -50))
    assert lines == ["G0 X90.000", "G0 Z10.000"]


def test_pre_toolchange_retreat_skips_move_already_at_that_safe_position():
    """LES-031: steht das Werkzeug bereits exakt auf der Aussen-Sicherheits-
    position (haeufigster Fall: die vorherige Operation hat per
    emit_safe_retract_for_op() bereits dorthin zurueckgezogen), ist der vor
    jedem Werkzeugwechsel unbedingt ausgegebene Rueckzug auf dieselbe
    Position eine bedeutungslose Nullbewegung."""
    settings = dict(_stock_settings(), _current_tool=1, _motion=MotionState(x=60.0, z=10.0))
    lines = []
    append_tool_and_spindle(lines, 2, 1000.0, settings)
    assert "G0 X60.000" not in lines
    assert "G0 Z10.000" not in lines
    assert "T02 M6" in lines


def test_pre_toolchange_retreat_still_moves_from_a_different_safe_position():
    """Kontrollfall: Kam die vorherige Operation aus dem Innen-Modus (andere
    sichere Position) oder ist die Position gaenzlich unbekannt, muss der
    Rueckzug weiterhin ausgegeben werden."""
    settings = dict(_stock_settings(), _current_tool=1, _motion=MotionState(x=9.0, z=4.0))
    lines = []
    append_tool_and_spindle(lines, 2, 1000.0, settings)
    assert "G0 X60.000" in lines
    assert "G0 Z10.000" in lines

    settings2 = dict(_stock_settings(), _current_tool=1)  # Position unbekannt (kein _motion)
    lines2 = []
    append_tool_and_spindle(lines2, 2, 1000.0, settings2)
    assert "G0 X60.000" in lines2
    assert "G0 Z10.000" in lines2


def test_combined_internal_rough_finish_after_external_op_retracts_before_finish_entry():
    """LES-022: reproduzierter Sicherheitsfehler. Eine Innenbearbeitung im
    kombinierten Schruppen+Schlichten-Modus (Move-based Fallback, da G71/G72
    fuer Innenbearbeitung nicht zuverlaessig ist) nach einer vorangehenden
    AUSSEN-Operation liess das Werkzeug per veraltetem `_is_at_safe`-Flag
    faelschlich als 'bereits sicher' gelten - obwohl die tatsaechlich zuletzt
    erreichte Position die AUSSEN-Sicherheitsebene (XRA/ZRA) war, nicht die
    fuer diese Operation gueltige INNEN-Ebene (XRI/ZRI). emit_approach()
    ueberspringt in diesem Fall faelschlich den Rueckzug auf die sichere
    Z-Ebene vor dem Schlichtschnitt und faehrt stattdessen im Eilgang (G0)
    diagonal direkt durch das noch stehengebliebene Restmaterial. Seit der
    zentralen Bewegungszustandsverfolgung (MotionState) wird die reale
    Position statt eines reinen Flags verglichen bzw. nach dem Schruppen
    explizit als unbekannt markiert - der Rueckzug wird jetzt zuverlaessig
    ausgegeben."""
    settings = dict(make_program_settings(), xi=10.0, xri=9.0, zri=2.0, xri_absolute=True, zri_absolute=True)
    op_face = Operation(
        OpType.FACE,
        {
            "mode": "rough", "tool": 5, "spindle": 1200.0, "feed": 0.12, "depth_max": 0.2,
            "start_x": 40.0, "end_x": 0.0, "start_z": 0.0, "end_z": 0.0,
            "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
        },
        path=[(40.0, 0.0), (0.0, 0.0)],
    )
    op_bore = Operation(
        OpType.ABSPANEN,
        {
            "side": "inside", "mode": "rough_finish", "tool": 5,
            "spindle": 800.0, "feed": 0.15, "depth_per_pass": 0.5, "slice_strategy": "parallel_z",
            "finish_allow_x": 0.2, "finish_allow_z": 0.1,
        },
        path=[(12.0, -30.0), (12.0, 0.0)],
    )
    lines = generate_program_gcode([op_face, op_bore], settings)
    finish_idx = lines.index("(Schlichtschnitt Kontur)")
    # Direkt nach der Schlichtschnitt-Markierung muss zuerst auf die sichere
    # Innen-Z-Ebene zurueckgezogen werden, bevor X ueberhaupt bewegt wird -
    # kein Eilgang darf X allein/zuerst anfahren, waehrend Z noch auf der
    # (falschen) tiefen Schruppposition steht.
    assert lines[finish_idx + 1] == "G0 Z2.000"
    assert lines[finish_idx + 2] == "G0 X9.000"
    # Dieselbe Absicherung gilt fuer den Einstieg ins Schruppen selbst.
    rough_idx = lines.index("(ABSPANEN Rough - parallel Z - Move-based)")
    assert lines[rough_idx + 1] == "G0 Z2.000"
    assert lines[rough_idx + 2] == "G0 X9.000"


def test_same_tool_two_operations_share_single_toolchange():
    """LES-001: zwei aufeinanderfolgende Operationen mit demselben Werkzeug
    (Aussen-Schruppen -> Schlichten) duerfen nur EINEN Werkzeugwechsel
    ausgeben; die Anfahrt der zweiten Operation muss trotzdem ohne Fehler
    durchlaufen (sichere Z-Rueckzugsebene haelt X-Repositionierung frei)."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "SameToolExternal"}),
        Operation(
            OpType.CONTOUR,
            {"name": "main_contour"},
            path=[(0.0, 0.0), (20.0, 0.0), (25.0, -5.0), (25.0, -10.025), (39.985, -54.980), (40.0, -55.0)],
        ),
        Operation(
            OpType.ABSPANEN,
            {
                "mode": "rough", "tool": 5, "spindle": 1300.0, "feed": 0.15,
                "depth_per_pass": 0.5, "slice_strategy": 1, "contour_name": "main_contour",
            },
        ),
        Operation(
            OpType.ABSPANEN,
            {
                "mode": "finish", "tool": 5, "spindle": 1500.0, "feed": 0.1,
                "depth_per_pass": 0.5, "slice_strategy": 1, "contour_name": "main_contour",
            },
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    assert lines.count("T05 M6") == 1


def test_separate_finish_step_reuses_prior_rough_cycle_sub_via_g70():
    """LES-018: ein reiner Schlichtstep (eigene Operation, eigenes Werkzeug),
    der dieselbe benannte Kontur referenziert wie ein FRUEHERER, per G71
    zyklisch geschruppter Schritt, muss den vorhandenen Kontur-Sub per G70
    wiederverwenden statt die Fertigkontur nochmal explizit als G1-Liste
    auszugeben."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "G70Reuse"}),
        Operation(OpType.CONTOUR, {"name": "c1"}, path=[(27.0, 0.0), (30.0, -35.0), (50.0, -60.0)]),
        Operation(
            OpType.ABSPANEN,
            {
                "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
                "side": "outside", "mode": "rough", "slice_strategy": "parallel_z",
                "finish_allow_x": 0.1, "finish_allow_z": 0.03, "contour_name": "c1",
            },
        ),
        Operation(
            OpType.ABSPANEN,
            {
                "tool": 2, "spindle": 1500.0, "feed": 0.08, "depth_per_pass": 1.0,
                "side": "outside", "mode": "finish", "slice_strategy": "parallel_z",
                "contour_name": "c1",
            },
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    assert "G71 " in text
    finish_idx = text.index("Schlichtschnitt Kontur")
    finish_section = text[finish_idx:]
    assert "G70 Wiederverwendung des Schruppzyklus" in finish_section
    assert "G70 Q" in finish_section
    # Die explizite G1-Konturliste des alten Pfads darf hier nicht mehr
    # auftauchen - genau EIN G71 (Schruppen) im ganzen Programm, kein
    # zweiter Schruppzyklus, keine erneute explizite Fertigkontur.
    assert text.count("G71 ") == 1
    g70_and_after = finish_section[finish_section.index("G70 Q"):]
    assert "G1 X50.000 Z-60.000" not in g70_and_after


def test_finish_step_falls_back_to_explicit_path_when_no_prior_cycle_exists():
    """Kontrollfall: ohne einen vorherigen, per G71/G72 definierten Zyklus
    (z. B. reiner Schlichtstep ohne vorausgegangenen Schruppschritt) muss
    der bestehende, explizite Schlichtweg unveraendert greifen."""
    settings = make_program_settings()
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "G70NoReuse"}),
        Operation(OpType.CONTOUR, {"name": "c1"}, path=[(27.0, 0.0), (30.0, -35.0), (50.0, -60.0)]),
        Operation(
            OpType.ABSPANEN,
            {
                "tool": 2, "spindle": 1500.0, "feed": 0.08, "depth_per_pass": 1.0,
                "side": "outside", "mode": "finish", "slice_strategy": "parallel_z",
                "contour_name": "c1",
            },
        ),
    ]
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    assert "G70 Wiederverwendung" not in text
    assert "G71 " not in text
    assert "G1 X50.000 Z-60.000" in text


def test_same_tool_internal_rough_then_finish_shares_single_toolchange():
    """LES-001: Innen-Schruppen -> Schlichten mit identischem Werkzeug darf
    ebenfalls keinen zweiten Werkzeugwechsel ausgeben."""
    bore_to_opening_path = [
        (10.0, -44.0), (11.4, -44.0), (12.0, -43.4), (12.0, -10.5),
        (13.0, -10.0), (16.0, -10.0), (16.0, -1.0), (18.0, 0.0), (19.2, 0.0),
    ]
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 9.3, "xri_absolute": True})
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0, "diameter": 8.0},
        path=[(0.0, 2.0), (0.0, -45.0)],
    )
    rough = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
        },
        path=bore_to_opening_path,
    )
    finish = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1400.0, "feed": 0.1, "depth_per_pass": 1.0,
            "side": "inside", "mode": "finish", "slice_strategy": "parallel_z",
        },
        path=bore_to_opening_path,
    )
    operations = [Operation(OpType.PROGRAM_HEADER, {}), drill, rough, finish]
    lines = generate_program_gcode(operations, settings)
    assert lines.count("T10 M6") == 1
    assert lines.count("T11 M6") == 1


def test_external_approach_uses_safe_x_until_target_z():
    # x_safe = xa(40) + xra(40) = 80.0, z_safe = za(0) + zra(2) = 2.0 -
    # der Bewegungszustand muss exakt darauf stehen, damit der anfaengliche
    # Rueckzug auf die sichere Ebene als bereits erreicht uebersprungen wird.
    settings = dict(make_program_settings(), _motion=MotionState(x=80.0, z=2.0))
    lines = []
    emit_approach(lines, 45, -20, settings)
    assert lines == ["G0 Z-20.000", "G0 X45.000"]


def test_external_approach_blocks_misconfigured_safe_x_inside_stock():
    """LES-001: der Z-Zwischenzug in emit_approach haelt X bewusst auf der
    sicheren Aussenposition XRA, WAEHREND Z auf die Zieltiefe faehrt - das
    ist nur sicher, wenn XRA tatsaechlich ausserhalb des Rohteils liegt. Ein
    fehlkonfiguriertes absolutes XRA innerhalb der Huellkurve (hier 30 bei
    Rohteil X0..50) darf nicht stillschweigend quer durchs Material fahren."""
    settings = dict(
        _stock_settings(),
        xra=30, xra_absolute=True,
    )
    lines = []
    with pytest.raises(ValueError, match="Rohteil"):
        emit_approach(lines, 20, -25, settings)
    assert lines == []


@pytest.mark.parametrize(
    "filename,cut_command",
    [
        ("Planen.ngc", "G72 Q"),
        ("Abdrehen.ngc", "G1 "),
        ("Einstich.ngc", "o220 call"),
        ("Gewinde.ngc", "G76 "),
    ],
)
def test_css_starts_with_limited_g97_and_activates_only_after_approach(filename, cut_command):
    ops, settings = example_programs()[filename]
    machining_op = next(op for op in reversed(ops) if op.op_type != OpType.PROGRAM_HEADER)
    machining_op.params.update(
        spindle_mode="css", spindle_max_rpm=2400.0, cutting_speed=120.0
    )
    lines = generate_program_gcode(ops, settings)
    step_idx = next(idx for idx, line in enumerate(lines) if line.startswith("(Step "))
    section = lines[step_idx:]
    startup_idx = next(idx for idx, line in enumerate(section) if line.startswith("G97 "))
    css_idx = next(idx for idx, line in enumerate(section) if line == "G96 D2400 S120.0")
    cut_idx = next(idx for idx, line in enumerate(section[css_idx + 1 :], css_idx + 1) if line.startswith(cut_command))
    approach_moves = [idx for idx, line in enumerate(section[:css_idx]) if line.startswith("G0 ")]
    assert startup_idx < max(approach_moves) < css_idx < cut_idx
    assert int(section[startup_idx].split("S", 1)[1].split()[0]) <= 2400


def test_css_rejects_zero_start_diameter_before_emitting_operation():
    ops, settings = example_programs()["Planen.ngc"]
    ops[-1].params.update(
        start_x=0.0, spindle_mode="css", spindle_max_rpm=2400.0, cutting_speed=120.0
    )
    with pytest.raises(ValueError, match="Bearbeitungsdurchmesser"):
        generate_program_gcode(ops, settings)


@pytest.mark.parametrize("missing", ["xt", "zt"])
def test_single_tool_requires_complete_toolchange_position(missing):
    ops, settings = example_programs()["Planen.ngc"]
    settings.pop(missing)
    lines = []
    with pytest.raises(ValueError, match="XT/ZT"):
        append_tool_and_spindle(lines, 1, 1000, settings)
    assert lines == []
    with pytest.raises(ValueError, match="XT/ZT"):
        generate_program_gcode(ops, settings)


def _save_handler(path, payload, link=True):
    return SimpleNamespace(
        _normalized_file_path=str, _current_program_path="previous.lse", root_widget=None,
        _find_root_widget=lambda: None, model=SimpleNamespace(operations=[Operation("face", {})]),
        _ensure_step_file_link=lambda *a, **k: link, _build_program_data=lambda: payload,
    )


@pytest.mark.parametrize("failure", ["link", "serialize", "replace"])
def test_failed_program_save_preserves_existing_file_path_and_cleans_temporary(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(ui_persistence.QtCore, "QSettings", lambda: None, raising=False)
    target = tmp_path / "program.lse"
    target.write_text("old program")
    payload = {"version": 1}
    if failure == "serialize":
        payload["cycle"] = payload
    handler = _save_handler(target, payload, link=failure != "link")
    if failure == "replace":
        def fail_replace(*a):
            raise OSError("write error")
        monkeypatch.setattr(ui_persistence.os, "replace", fail_replace)
    with pytest.raises((ValueError, OSError)):
        ui_persistence.write_program_file(handler, str(target))
    assert target.read_text() == "old program"
    assert handler._current_program_path == "previous.lse"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["program.lse"]


def test_successful_program_save_commits_path_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_persistence.QtCore, "QSettings", lambda: None, raising=False)
    target = tmp_path / "program.lse"
    handler = _save_handler(target, {"version": 1})
    ui_persistence.write_program_file(handler, str(target))
    assert json.loads(target.read_text()) == {"version": 1}
    assert handler._current_program_path == str(target)


@pytest.mark.parametrize("path", [[[1, "bad"]], [[1]], [None], "bad"])
def test_malformed_path_is_not_silently_shortened(path):
    with pytest.raises(ValueError):
        step_data_to_operation({"op_type": "contour", "path": path})


def test_duplicate_contour_names_and_unknown_operations_abort():
    ops, settings = example_programs()["Abdrehen.ngc"]
    ops.insert(1, deepcopy(ops[1]))
    with pytest.raises(ValueError, match="nicht eindeutig"):
        generate_program_gcode(ops, settings)
    with pytest.raises(ValueError, match="Unbekannter Operationstyp"):
        generate_program_gcode([Operation("unsupported", {})], settings)


def test_changed_contour_matches_fresh_save_load_after_previous_export():
    from lathe_easystep.persistence import operation_to_step_data
    ops, settings = example_programs()["Abdrehen.ngc"]
    old = generate_program_gcode(ops, settings)
    ops[1].path[2] = (26., -5.)
    fresh = [step_data_to_operation(operation_to_step_data(op)) for op in ops]
    changed = generate_program_gcode(ops, settings)
    assert changed != old
    assert changed == generate_program_gcode(fresh, settings)


@pytest.mark.parametrize("failure", ["serialize", "replace"])
def test_failed_step_save_preserves_file_and_link(tmp_path, monkeypatch, failure):
    from lathe_easystep.storage import set_step_file_path
    from lathe_easystep.persistence import operation_to_step_data
    target = tmp_path / "new.step.json"
    target.write_text("old")
    op = Operation("face", {"__step_file_path": "previous.step.json"})
    handler = SimpleNamespace(_normalized_file_path=str, _set_step_file_path=set_step_file_path,
                              _operation_to_step_data=operation_to_step_data)
    if failure == "serialize":
        op.params["bad"] = object()
    else:
        monkeypatch.setattr(ui_persistence.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises((TypeError, OSError)):
        ui_persistence.write_step_file(handler, op, str(target))
    assert target.read_text() == "old"
    assert op.params["__step_file_path"] == "previous.step.json"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("case", ["second_write_failure", "unlinked_step"])
def test_save_changes_preserves_dirty_state_when_not_all_steps_saved(tmp_path, monkeypatch, case):
    from lathe_easystep.persistence import operation_to_step_data
    a, b = tmp_path / "a.step.json", tmp_path / "b.step.json"
    b.write_text("old b")
    ops = [Operation("face", {"__step_file_path": str(a)}),
           Operation("face", {"__step_file_path": str(b)})]
    if case == "second_write_failure":
        ops[1].params["bad"] = object()
    else:
        ops[1].params.pop("__step_file_path")
    cleared, errors = [], []
    handler = SimpleNamespace(
        _saving_changes=False, root_widget=None, _find_root_widget=lambda: None,
        _update_selected_operation=lambda **k: None, _log=lambda *a, **k: None,
        model=SimpleNamespace(operations=ops), _dirty_operation_indices={0, 1},
        _current_program_path=None, _current_gcode_path=None, _program_dirty=False,
        _step_file_path=lambda op: op.params.get("__step_file_path"),
        _operation_to_step_data=operation_to_step_data, _remember_dialog_path=lambda *a, **k: None,
        _normalized_file_path=lambda path: path, _clear_dirty_state=lambda: cleared.append(True),
    )
    monkeypatch.setattr(ui_persistence, "_tr",
                        lambda handler, key, **kw: f"{key} {kw}")
    monkeypatch.setattr(ui_persistence.QtWidgets.QMessageBox, "information", lambda *a: None)
    monkeypatch.setattr(ui_persistence.QtWidgets.QMessageBox, "critical", lambda *args: errors.append(args[-1]))
    ui_persistence.handle_save_changes(handler)
    assert a.exists() and b.read_text() == "old b"
    assert handler._dirty_operation_indices == {0, 1} and not cleared
    assert not handler._saving_changes
    if case == "second_write_failure":
        assert len(errors) == 1 and "steps_updated" in errors[0] and "1" in errors[0]
    else:
        assert not errors
