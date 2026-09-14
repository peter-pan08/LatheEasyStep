import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.preview_geometry import build_groove_preview_path

# LES-034-Nachuntersuchung 2026-09-14: build_groove_preview_path() hatte
# bisher KEINE Testabdeckung (weder stub noch real), obwohl es die
# Vorschau fuer jede GROOVE-Operation liefert. Ein echter G-Code-Vergleich
# ist hier bewusst NICHT sinnvoll (LES-022-Entscheidung: der o220-
# Nutzyklus stuft die Breite datenabhaengig in mehreren Passes - das in
# Python nachzurechnen wuerde die Zustelllogik des Makros duplizieren).
# build_groove_preview_path() ist stattdessen eine bewusst vereinfachte,
# rein nominale Rechteck-Darstellung der ZIEL-Nut (Endgeometrie, kein
# Werkzeugweg) - diese Tests sichern zumindest deren eigene interne
# Korrektheit ab (Vorzeichen bei Innen-/Aussenbearbeitung, alle drei
# Bezugskanten, radiale und axiale Nut).


def test_matches_the_einstich_reference_fixture_exactly():
    """Reproduziert die Parameter aus examples.py::Einstich.ngc und
    vergleicht gegen den dort hinterlegten, handgepflegten path= -
    unabhaengige Bestaetigung, dass die Funktion fuer diesen realen Fall
    exakt dasselbe liefert."""
    params = {
        "mode": 0, "lage": 0, "diameter": 30.0, "z": -25.0,
        "width": 2.0, "depth": 2.0,
    }
    path = build_groove_preview_path(params)
    assert path == [(30.0, -26.0), (26.0, -26.0), (26.0, -24.0), (30.0, -24.0)]


def test_internal_radial_groove_increases_diameter_at_bottom():
    """lage=1 (Innen/ID) muss den Durchmesser am Nutgrund VERGROESSERN
    (Materialabtrag von innen vergroessert die Bohrung) - das Gegenteil
    einer Aussen-Nut. Ein Vorzeichenfehler hier waere ein echter
    Sicherheitsfund (falsche Zustellrichtung in der Vorschau)."""
    external = build_groove_preview_path(
        {"mode": 0, "lage": 0, "diameter": 30.0, "z": -25.0, "width": 2.0, "depth": 2.0}
    )
    internal = build_groove_preview_path(
        {"mode": 0, "lage": 1, "diameter": 30.0, "z": -25.0, "width": 2.0, "depth": 2.0}
    )
    external_bottom_x = external[1][0]
    internal_bottom_x = internal[1][0]
    assert external_bottom_x == 26.0  # 30 - 2*2
    assert internal_bottom_x == 34.0  # 30 + 2*2
    assert internal_bottom_x > 30.0 > external_bottom_x


def test_radial_groove_reference_edge_zero_is_centered():
    path = build_groove_preview_path(
        {"mode": 0, "lage": 0, "ref": 0, "diameter": 30.0, "z": -25.0, "width": 4.0, "depth": 1.0}
    )
    z_left = path[0][1]
    z_right = path[3][1]
    assert z_left == -27.0  # z - width/2
    assert z_right == -23.0  # z + width/2


def test_radial_groove_reference_edge_one_starts_at_z():
    path = build_groove_preview_path(
        {"mode": 0, "lage": 0, "ref": 1, "diameter": 30.0, "z": -25.0, "width": 4.0, "depth": 1.0}
    )
    z_left = path[0][1]
    z_right = path[3][1]
    assert z_left == -25.0  # ref=1: z ist die linke Kante
    assert z_right == -21.0  # z + width


def test_radial_groove_reference_edge_two_ends_at_z():
    path = build_groove_preview_path(
        {"mode": 0, "lage": 0, "ref": 2, "diameter": 30.0, "z": -25.0, "width": 4.0, "depth": 1.0}
    )
    z_left = path[0][1]
    z_right = path[3][1]
    assert z_left == -29.0  # z - width
    assert z_right == -25.0  # ref=2: z ist die rechte Kante


def test_axial_face_groove_uses_z_as_depth_direction_not_diameter():
    """mode=1 (axiale/stirnseitige Nut) muss in Z (nicht im Durchmesser)
    zustellen - X bleibt zwischen x_near/x_far, Z faehrt auf z_bottom."""
    path = build_groove_preview_path(
        {"mode": 1, "lage": 0, "ref": 0, "diameter": 40.0, "z": 0.0, "width": 3.0, "depth": 1.5}
    )
    xs = [p[0] for p in path]
    zs = [p[1] for p in path]
    assert min(xs) == 38.5 and max(xs) == 41.5  # diameter +/- width/2
    assert min(zs) == -1.5 and max(zs) == 0.0  # z - depth .. z


def test_axial_face_groove_lage_three_cuts_toward_positive_z():
    normal = build_groove_preview_path(
        {"mode": 1, "lage": 0, "diameter": 40.0, "z": 0.0, "width": 3.0, "depth": 1.5}
    )
    reversed_ = build_groove_preview_path(
        {"mode": 1, "lage": 3, "diameter": 40.0, "z": 0.0, "width": 3.0, "depth": 1.5}
    )
    normal_bottom_z = min(p[1] for p in normal)
    reversed_bottom_z = max(p[1] for p in reversed_)
    assert normal_bottom_z == -1.5
    assert reversed_bottom_z == 1.5


def test_zero_width_or_depth_does_not_crash_and_stays_finite():
    path = build_groove_preview_path({"mode": 0, "lage": 0, "diameter": 30.0, "z": -25.0, "width": 0.0, "depth": 0.0})
    assert all(all(abs(coord) < 1e6 for coord in point) for point in path)
