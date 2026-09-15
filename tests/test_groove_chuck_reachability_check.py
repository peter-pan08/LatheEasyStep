import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.model import OpType, Operation
from lathe_easystep.tools import Tool

# LES-032 (2026-09-15): Erreichbarkeits-/Werkzeughuellenpruefung mit
# Tooltable-Daten. Bisher wurde die Futter-Sperrzone nur fuer die
# separaten Rueckzugswege geprueft, nie fuer die eigentliche Stechbewegung
# selbst - und selbst die Rueckzugspruefung behandelt das Werkzeug als
# punktfoermig, ohne dessen reale Schneidenbreite zu beruecksichtigen.

_CHUCK_SETTINGS = {
    "chuck_no_go_x_min": 0.0,
    "chuck_no_go_x_max": 50.0,
    "chuck_no_go_z_limit": -2.0,
    "za": 0.0,
}


def _tool(**overrides):
    defaults = dict(
        t=4, p=0, d=0.2, q=6, comment="Einstechen MGMN200", iso_code=None, iso_size=None,
        radius_mm=0.2, kind="grooving", wear=False, radius_source=None,
    )
    defaults.update(overrides)
    return Tool(**defaults)


def _reach_warnings(warnings):
    return [w for w in warnings if "Futter-Sperrzone" in w]


def _groove_op(z, diameter=20.0, depth=5.0, lage=0, tool=4):
    return Operation(
        OpType.GROOVE,
        {"tool": tool, "lage": lage, "diameter": diameter, "depth": depth, "z": z},
    )


def test_groove_centerline_inside_chuck_zone_is_flagged_even_without_tool_width():
    """Grundfall: die Z-Position selbst liegt bereits in der Sperrzone - muss
    unabhaengig von der Werkzeugbreite erkannt werden."""
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-3.0, tool=0)]
    warnings = _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={})))
    assert len(warnings) == 1
    assert "Schritt 2" in warnings[0]


def test_groove_outside_zone_but_tool_width_reaches_into_it_is_flagged():
    """Realer Fund: Z=-1,5 liegt fuer sich allein NICHT in der Sperrzone
    (Grenze bei -2,0), aber die dem Futter zugewandte Kante eines 2 mm
    breiten Einstechwerkzeugs (T4, "MGMN200") reicht bis Z=-2,5 - also in
    die Sperrzone. Ohne Beruecksichtigung der Werkzeugbreite waere das
    unbemerkt geblieben."""
    tool = _tool(t=4, comment="Einstechen MGMN200")  # 2.00 mm Einsatzbreite
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-1.5, tool=4)]
    warnings = _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={4: tool})))
    assert len(warnings) == 1
    assert "Schritt 2" in warnings[0]


def test_groove_well_clear_of_chuck_zone_is_silent():
    """z_limit=-2.0, za=0.0: die Sperrzone liegt auf der vom Futter
    abgewandten Seite (alles <= z_limit) - naeher an za=0.0 (weniger
    negativ) ist die sichere Seite."""
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-0.5, tool=4)]
    assert _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={4: tool}))) == []


def test_groove_without_configured_chuck_zone_is_silent():
    """validate_chuck_segment() selbst kehrt folgenlos zurueck, wenn keine
    Sperrzone konfiguriert ist - dieselbe Toleranz gilt hier."""
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-3.0, tool=4)]
    assert _reach_warnings(validate_program_setup(ops, {"tools": {4: tool}})) == []


def test_groove_without_recognizable_insert_width_still_checks_centerline():
    """Ohne ableitbare Einsatzbreite bleibt zumindest die reine Z-Mitte
    geprueft (half_width=0) - kein Totalausfall der Pruefung."""
    tool = _tool(t=4, comment="Einstechwerkzeug ohne Codeangabe")
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-3.0, tool=4)]
    warnings = _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={4: tool})))
    assert len(warnings) == 1


def test_only_one_warning_per_operation_even_if_both_edges_collide():
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [Operation(OpType.PROGRAM_HEADER, {}), _groove_op(z=-5.0, tool=4)]
    warnings = _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={4: tool})))
    assert len(warnings) == 1


def test_non_groove_operations_are_never_checked():
    tool = _tool(t=4, comment="Einstechen MGMN200")
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.ABSPANEN, {"tool": 4, "side": "outside", "z": -5.0}),
    ]
    assert _reach_warnings(validate_program_setup(ops, dict(_CHUCK_SETTINGS, tools={4: tool}))) == []
