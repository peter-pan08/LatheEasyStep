import math
import re
from copy import deepcopy

import pytest

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import Operation, OpType

# Nutzerfrage 2026-09-10: liefert eine Kontur mit G71/G72-Zyklus dasselbe
# (korrekte) Ergebnis wie mit explizit erzeugtem ("ISO") G-Code? Wichtig,
# weil der bewegungsbasierte Fallback in der Praxis haeufig aktiv ist -
# u. a. immer dann, wenn das selbst gebaute Spanbruch-/Pausen-Feature
# (`pause_enabled`/`pause_distance`, ein LinuxCNC unbekannter, an einen
# Siemens-Zyklus angelehnter Vorschub-Unterbrecher) genutzt wird. LinuxCNC
# kennt diesen Zyklus nicht - das Feature erzwingt deshalb IMMER den
# expliziten Move-based-Pfad, auch fuer sonst G71/G72-taugliche Konturen.

# Aussenkontur mit kleinem Bogen (identisch zur Innen_Radius-Kontur, nur
# als Aussenkontur interpretiert) - deckt genau den Fall ab, an dem der
# heutige Sehnen-Fix (Innenbearbeitung) urspruenglich gefunden wurde.
_ARC_CONTOUR_SEGMENTS = [
    {"x": 12.0, "z": -15.0, "edge": "radius", "edge_size": 1.0},
    {"x": 18.0, "z": -15.0},
    {"x": 18.0, "z": 0.0},
]


def _true_wall_radius_at_z(z: float) -> float:
    """Wahre Fertigkontur (Radius-Raum), unabhaengig vom Generator direkt
    aus der Kontur nachgerechnet: R6 bis Z-16, R1-Bogen (Zentrum R7/Z-16)
    bis (R7,Z-15), Schulter R9 ab Z-15."""
    if z <= -16.0 - 1e-9:
        return 6.0
    if z <= -15.0 + 1e-9:
        cx, cz, r = 7.0, -16.0, 1.0
        dz = max(-r, min(r, z - cz))
        return cx - math.sqrt(max(0.0, r * r - dz * dz))
    return 9.0


def _rough_g1_points(lines):
    """Endpunkte jeder Schrupp-Schnittbewegung - als normales `G1 X.. Z..`
    ODER, bei aktivem Spanbruch, als `o<step_line_pause> call [x0] [z0]
    [x1] [z1] ...` (die eigentliche Bewegung steckt dann in den Klammer-
    Parametern 3/4, kein `G1` wird dafuer ausgegeben)."""
    start_idx = next(i for i, l in enumerate(lines) if l.startswith("(ABSPANEN Rough"))
    finish_idx = next(i for i, l in enumerate(lines) if l.startswith("(Schlichtschnitt"))
    points = []
    for line in lines[start_idx:finish_idx]:
        if line.startswith("G1 "):
            m = re.search(r"X(-?[0-9.]+) Z(-?[0-9.]+)", line)
            if m:
                points.append((float(m.group(1)), float(m.group(2))))
        elif "step_line_pause" in line and "call" in line:
            nums = re.findall(r"\[(-?[0-9.]+)\]", line)
            if len(nums) >= 4:
                points.append((float(nums[2]), float(nums[3])))
    return points


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("output_preference", ["prefer_cycle", "prefer_explicit"])
def test_external_arc_contour_never_undercuts_allowance_regardless_of_output_mode(
    output_preference, reverse
):
    """LES-003/LES-040: unabhaengig davon, ob eine sonst zyklustaugliche
    Aussenkontur per G71/G72 oder explizit ("ISO", z. B. weil das
    Spanbruch-Feature aktiv ist) abgefahren wird, muss dieselbe
    Fertigkontur mit demselben Aufmass herauskommen. `prefer_cycle`
    validiert hier nur, dass die Kontur tatsaechlich zyklustauglich bleibt
    (0 explizite G1-Schruppzeilen); die eigentliche Geometrie des Zyklus
    selbst pruefen die LinuxCNC-Referenz-/rs274-Checks. `prefer_explicit`
    prueft jeden erzeugten Schrupp-G1-Punkt direkt gegen die wahre
    (nicht-linearisierte) Kontur."""
    segments = deepcopy(_ARC_CONTOUR_SEGMENTS)
    if reverse:
        # Gleiche physische Kontur rueckwaerts durchlaufen: der Radius sitzt
        # weiterhin an der Ecke (12,-15), jetzt auf dem SEGMENT, dessen
        # Endpunkt genau dort liegt (zweites statt erstes Segment).
        segments = [{"x": 18.0, "z": -15.0},
                    {"x": 12.0, "z": -15.0, "edge": "radius", "edge_size": 1.0},
                    {"x": 12.0, "z": -30.0}]
        start_x, start_z = 18.0, 0.0
    else:
        start_x, start_z = 12.0, -30.0
    contour = Operation(OpType.CONTOUR, {"name": "parity_test", "start_x": start_x,
        "start_z": start_z, "segments": segments})
    op = Operation(OpType.ABSPANEN, {"contour_name": "parity_test", "side": "outside",
        "mode": "rough_finish", "slice_strategy": "parallel_z", "tool": 11,
        "spindle": 800.0, "feed": 0.15, "depth_per_pass": 0.5,
        "finish_allow_x": 0.2, "finish_allow_z": 0.1,
        "output_preference": output_preference})
    settings = make_program_settings()
    lines = generate_program_gcode([contour, op], settings)

    used_cycle = any(l.startswith(("G71 ", "G72 ")) for l in lines)
    if output_preference == "prefer_cycle":
        assert used_cycle
    else:
        assert not used_cycle

    allow_radius = 0.1
    checked = 0
    for x, z in _rough_g1_points(lines):
        wall_r = _true_wall_radius_at_z(z)
        clearance = x / 2.0 - wall_r
        checked += 1
        assert clearance >= allow_radius - 1e-6, (
            f"{output_preference}: Schrupp-Schnitt X{x} Z{z} verletzt das "
            f"Aufmass: nur {clearance * 2:.3f}mm statt 0.200mm Restaufmass"
        )
    if output_preference == "prefer_explicit":
        assert checked > 10


def test_external_arc_contour_with_chip_breaking_forces_explicit_and_keeps_allowance():
    """Realer Praxisfall (Nutzerhinweis 2026-09-10): das Spanbruch-Feature
    (`pause_enabled`) wird auf einer echten Maschine haeufig genutzt und
    erzwingt IMMER den expliziten Pfad, auch fuer eine sonst G71-taugliche
    Aussenkontur - LinuxCNC kennt diesen (an einen Siemens-Zyklus
    angelehnten) Vorschub-Unterbrecher nicht. Muss trotzdem das Aufmass
    einhalten, exakt wie ohne Spanbruch."""
    contour = Operation(OpType.CONTOUR, {"name": "parity_chipbreak", "start_x": 12.0,
        "start_z": -30.0, "segments": deepcopy(_ARC_CONTOUR_SEGMENTS)})
    op = Operation(OpType.ABSPANEN, {"contour_name": "parity_chipbreak", "side": "outside",
        "mode": "rough_finish", "slice_strategy": "parallel_z", "tool": 11,
        "spindle": 800.0, "feed": 0.15, "depth_per_pass": 0.5,
        "finish_allow_x": 0.2, "finish_allow_z": 0.1,
        "pause_enabled": True, "pause_distance": 3.0})
    settings = make_program_settings()
    lines = generate_program_gcode([contour, op], settings)

    assert not any(l.startswith(("G71 ", "G72 ")) for l in lines)
    assert any(l.startswith("(Fallback-Grund: Spanbruch") for l in lines)

    allow_radius = 0.1
    checked = 0
    for x, z in _rough_g1_points(lines):
        wall_r = _true_wall_radius_at_z(z)
        clearance = x / 2.0 - wall_r
        checked += 1
        assert clearance >= allow_radius - 1e-6
    assert checked > 10
