import math
import re
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.contour_logic import build_contour_path
from lathe_easystep.gcode_roughing import _emit_finish_primitives, contour_sub_from_primitives


def _gcode_from_primitives(prims, *, feed):
    lines = []
    _emit_finish_primitives(lines, prims, feed=feed)
    return lines


def _assert_arc_line_is_geometrically_valid(line, start_x_diam, start_z):
    """LinuxCNC lehnt G2/G3 ab, wenn der Abstand Start->Zentrum vom Abstand
    Ende->Zentrum abweicht ("Radius to end of arc differs from radius to
    start"). I ist dabei IMMER ein Radiuswert, auch im Durchmessermodus (G7) -
    diese Pruefung rechnet daher X-Koordinaten konsequent in Radius um, bevor
    sie mit I/K (die das Zentrum relativ zum Startpunkt beschreiben)
    verglichen werden."""
    m = re.search(r"X([+-]?[\d.]+)\s*Z([+-]?[\d.]+)\s*I([+-]?[\d.]+)\s*K([+-]?[\d.]+)", line)
    assert m, f"Keine G2/G3-Bogenzeile mit I/K gefunden: {line!r}"
    end_x_diam, end_z, i_val, k_val = (float(v) for v in m.groups())
    start_r = start_x_diam / 2.0
    end_r = end_x_diam / 2.0
    center_r = start_r + i_val
    center_z = start_z + k_val
    dist_start = math.hypot(start_r - center_r, start_z - center_z)
    dist_end = math.hypot(end_r - center_r, end_z - center_z)
    assert abs(dist_start - dist_end) < 0.01, (
        f"Bogen geometrisch ungueltig: Radius zum Start ({dist_start:.4f}) "
        f"weicht vom Radius zum Ende ({dist_end:.4f}) ab - LinuxCNC wuerde "
        f"dies mit 'Radius to end of arc differs from radius to start' ablehnen"
    )


def test_arc_primitive_outputs_valid_G2_G3():
    # simple L-shape with a radius corner of 10mm
    params = {
        "start_x": 5.0,
        "start_z": 0.0,
        "segments": [
            {"x": 5.0, "z": -10.0, "edge": "radius", "edge_size": 10.0, "arc_side": "auto"},
            {"x": 10.0, "z": -10.0, "edge": "none", "edge_size": 0.0, "arc_side": "auto"},
        ],
    }
    prims = build_contour_path(params)
    # verify we got one arc primitive with a nonzero center
    arcs = [p for p in prims if p.get("type") == "arc"]
    assert len(arcs) == 1
    arc = arcs[0]
    assert "c" in arc or "center" in arc
    # generate gcode and inspect I/K values
    gcode = _gcode_from_primitives(prims, feed=100)
    # should contain a G2 or G3 line with nonzero I/K
    arc_lines = [l for l in gcode if l.startswith("G2") or l.startswith("G3")]
    assert len(arc_lines) == 1
    line = arc_lines[0]
    assert "I0" not in line or "K0" not in line

    # additionally, the gcode endpoint should match the primitive's p2 coordinate,
    # not collapse to the start point (which previously produced degenerate arcs).
    # our primitive p2 was roughly (9.995,-10.0), so ensure the gcode contains X9.995 or
    # Z-10.000 rather than X5.000 Z0.000.
    assert "X9.995" in line or "Z-10.000" in line


def test_arc_geometry_from_error_case():
    # reproduce geometry that earlier produced a LinuxCNC radius mismatch error
    params = {
        "start_x": 5.0,
        "start_z": 0.0,
        "segments": [
            {"x": 5.0, "z": -10.0, "edge": "radius", "edge_size": 10.0, "arc_side": "auto"},
            {"x": 10.0, "z": -10.0, "edge": "none", "edge_size": 0.0, "arc_side": "auto"},
        ],
    }
    prims = build_contour_path(params)
    gcode = _gcode_from_primitives(prims, feed=100)
    # the arc line should not be degenerate (start != end)
    arc_lines = [l for l in gcode if l.startswith("G2") or l.startswith("G3")]
    assert len(arc_lines) == 1
    line = arc_lines[0]
    # ensure end coordinates differ from start
    assert "X5.000 Z0.000" not in line


def test_arc_I_is_radius_not_diameter_delta():
    """Realer Bugreport (LinuxCNC-Log): 'Radius to end of arc differs from
    radius to start' beim Abfahren eines generierten Programms. Ursache:
    I wurde als rohe Durchmesser-Differenz zum Zentrum berechnet, obwohl I
    in LinuxCNC/Fanuc-Lathe-Dialekten IMMER ein Radiuswert ist - auch im
    Durchmessermodus G7. Reproduziert exakt die Kontur aus dem realen
    Testprogramm des Nutzers (Innenkontur 'ausdrehen')."""
    prims = [
        {"type": "line", "p1": [12.0, -43.4], "p2": [12.0, -10.5]},
        {"type": "arc", "p1": [12.0, -10.5], "p2": [13.0, -10.0], "c": [13.0, -10.5], "ccw": True},
    ]
    lines = _gcode_from_primitives(prims, feed=0.15)
    arc_line = next(l for l in lines if l.startswith("G2") or l.startswith("G3"))
    _assert_arc_line_is_geometrically_valid(arc_line, start_x_diam=12.0, start_z=-10.5)


def test_contour_sub_from_primitives_arc_I_is_radius_not_diameter_delta():
    """Wie test_arc_I_is_radius_not_diameter_delta(), aber fuer den zweiten,
    unabhaengigen Emissionspfad (G71/G72-Zyklus-Subroutine)."""
    prims = [
        {"type": "line", "p1": [12.0, -43.4], "p2": [12.0, -10.5]},
        {"type": "arc", "p1": [12.0, -10.5], "p2": [13.0, -10.0], "c": [13.0, -10.5], "ccw": True},
    ]
    lines = contour_sub_from_primitives(prims, 101)
    arc_line = next(l for l in lines if l.startswith("G2") or l.startswith("G3"))
    _assert_arc_line_is_geometrically_valid(arc_line, start_x_diam=12.0, start_z=-10.5)


def test_arc_from_real_fillet_algorithm_is_geometrically_valid():
    """Kontrollfall mit einer garantiert gueltigen, ueber build_contour_path()
    (Fillet-Algorithmus) erzeugten Kontur - muss vor und nach dem Fix
    gueltig bleiben."""
    params = {
        "start_x": 5.0,
        "start_z": 0.0,
        "segments": [
            {"x": 5.0, "z": -10.0, "edge": "radius", "edge_size": 10.0, "arc_side": "auto"},
            {"x": 10.0, "z": -10.0, "edge": "none", "edge_size": 0.0, "arc_side": "auto"},
        ],
    }
    prims = build_contour_path(params)
    lines = _gcode_from_primitives(prims, feed=100)
    arc_line = next(l for l in lines if l.startswith("G2") or l.startswith("G3"))
    arc_prim = next(p for p in prims if p["type"] == "arc")
    arc_start_x, arc_start_z = arc_prim["p1"]
    _assert_arc_line_is_geometrically_valid(arc_line, start_x_diam=arc_start_x, start_z=arc_start_z)
