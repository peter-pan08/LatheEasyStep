import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from lathe_easystep.gcode_program import gcode_for_face
from lathe_easystep.model import OpType, Operation


def _face_op(**overrides):
    params = {
        "mode": 0,
        "tool": 1,
        "spindle": 2000.0,
        "feed": 0.1,
        "depth_max": 0.05,
        "start_z": 2.0,
        "end_z": 0.0,
        "start_x": 40.0,
        "end_x": 0.0,
        "finish_allow_z": 0.0,
        "retract": 1.0,
        "edge_type": "none",
        "edge_size": 0.0,
        "coolant": True,
    }
    params.update(overrides)
    return Operation(OpType.FACE, params)


def test_face_edge_type_string_id_none_does_not_crash():
    """Realer Bugreport: Planen mit Kantenform ueber die Combo (liefert die
    String-ID ueber currentData(), nicht mehr den alten numerischen Index)
    schlug fehl mit 'Invalid float for edge_type'."""
    lines = gcode_for_face(_face_op(edge_type="none"), {})
    assert any(l.startswith("G1 X40.000 Z0.000") for l in lines)


def test_face_edge_type_string_id_chamfer_produces_chamfer_geometry():
    lines = gcode_for_face(_face_op(edge_type="chamfer", edge_size=1.0), {})
    assert any("Z-1.000" in l for l in lines)
    assert any("X38.000" in l for l in lines)


def test_face_edge_type_legacy_numeric_chamfer_still_works():
    """Rueckwaertskompatibel: alte Programme/Tests mit numerischem edge_type=1
    muessen weiterhin funktionieren (siehe examples.py Referenzprogramm)."""
    lines = gcode_for_face(_face_op(edge_type=1, edge_size=1.0), {})
    assert any("Z-1.000" in l for l in lines)
    assert any("X38.000" in l for l in lines)


def test_face_edge_type_radius_raises_clear_not_implemented_error():
    """'Radius' ist in der Combo waehlbar, aber im Generator noch nicht
    umgesetzt (LES-036) - statt eines stillschweigend falschen (ungerundeten)
    Ergebnisses muss ein klarer Fehler kommen."""
    with pytest.raises(ValueError, match="Radius"):
        gcode_for_face(_face_op(edge_type="radius", edge_size=1.0), {})


def test_face_edge_type_missing_raises_clear_error():
    op = _face_op()
    del op.params["edge_type"]
    with pytest.raises(ValueError, match="edge_type"):
        gcode_for_face(op, {})
