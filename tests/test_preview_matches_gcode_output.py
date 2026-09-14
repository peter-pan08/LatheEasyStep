import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import example_programs
from lathe_easystep.model import OpType
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.preview_geometry import build_contour_path, build_face_path

# LES-034 (Nutzerauftrag "dargestellten Werkzeugweg fuer Referenzprogramme
# gegen die tatsaechliche Ausgabe vergleichen"): fuer jede Referenz mit
# einem expliziten Schlichtpfad (ABSPANEN mode != reines Schruppen, oder
# FACE) wird geprueft, dass jeder real vom G-Code angefahrene Punkt nahe
# am Vorschau-Pfad (Kontur-Eckpunkte bzw. build_face_path()) liegt - die
# Vorschau darf nicht etwas anderes zeigen als das, was die Maschine
# tatsaechlich schneidet.
#
# Richtung der Pruefung bewusst so gewaehlt: der Vorschaupfad kann feiner
# tesselliert sein als die G-Code-Eckpunkte (ein Bogen als G2/G3-Befehl
# mit nur Start-/Endpunkt im Text, aber als viele kleine Liniensegmente in
# der Vorschau dargestellt) - deshalb wird pro tatsaechlichem G-Code-Punkt
# der naechste Vorschaupunkt gesucht, nicht umgekehrt.
#
# Ergebnis (2026-09-14): keine Abweichung gefunden - fuer alle neun
# ABSPANEN/FACE-Operationen mit explizitem Schlichtpfad in den zwoelf
# Referenzen liegt jeder G-Code-Punkt exakt (< 0.01mm) auf dem Vorschau-
# Pfad. THREAD ist bereits separat verifiziert (LES-033,
# test_thread_preview_geometry_matches_actual_g76_output). Reines
# Schruppen (Abdrehen.ngc) hat keinen separaten Schlichtpfad zum
# Vergleichen - bewusst uebersprungen, nicht Teil dieses Tests. DRILL/
# GROOVE brauchen eine andere Vergleichsmethodik (die Vorschau zeigt dort
# die Bohrer-/Werkzeugform, nicht den Werkzeugweg) - nicht Teil dieses
# Tests, siehe TODO.md (LES-034).

TOL = 0.01  # mm


def _parse_motion_full(lines):
    """line index -> (x, z) Maschinenposition nach dieser Zeile, modal ueber
    die GESAMTE Datei verfolgt (G-Code ist modal - eine Zeile mit nur X
    behaelt das zuletzt aktive Z)."""
    positions = {}
    last_x = None
    last_z = None
    last_cmd = None
    for i, line in enumerate(lines):
        s = line.strip()
        m = re.match(r'^(G0|G1|G2|G3)\b', s)
        if m:
            last_cmd = m.group(1)
        xm = re.search(r'X(-?\d+\.?\d*)', s)
        zm = re.search(r'Z(-?\d+\.?\d*)', s)
        if xm:
            last_x = float(xm.group(1))
        if zm:
            last_z = float(zm.group(1))
        if last_cmd in ("G0", "G1", "G2", "G3") and (xm or zm):
            positions[i] = (last_x, last_z)
    return positions


def _find_finish_segment_indices(lines):
    start = None
    for i, line in enumerate(lines):
        if "(Schlichtschnitt Kontur)" in line:
            start = i
            break
    if start is None:
        return None
    idxs = []
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if re.match(r'^(G1|G2|G3)\b', s):
            idxs.append(i)
        elif idxs and re.match(r'^G0\b', s):
            break
    return idxs if idxs else None


def _find_subroutine_indices(lines, sub_name="o100"):
    """FACE nutzt G70/G72 mit einer wiederverwendeten Subroutine
    (o100 sub ... o100 endsub) statt eines "(Schlichtschnitt"-Textblocks -
    die Schlichtgeometrie steckt im Subroutine-Koerper (per G70 fuer den
    Schlichtgang erneut aufgerufen)."""
    start = end = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == f"{sub_name} sub":
            start = i + 1
        elif s == f"{sub_name} endsub" and start is not None:
            end = i
            break
    if start is None or end is None:
        return None
    idxs = [i for i in range(start, end) if re.match(r'^(G0|G1|G2|G3)\b', lines[i].strip())]
    return idxs if idxs else None


def _corner_points_from_primitives(primitives):
    """Nur Eckpunkte (p1 des ersten, dann p2 jedes weiteren) - keine
    Tessellation. Akzeptiert sowohl primitiven-foermige als auch flache
    (x, z)-Tupel-Konturen."""
    if primitives and isinstance(primitives[0], dict):
        pts = []
        for i, prim in enumerate(primitives):
            p1 = tuple(prim["p1"])
            p2 = tuple(prim["p2"])
            if i == 0:
                pts.append(p1)
            pts.append(p2)
        return pts
    return [tuple(p) for p in primitives]


def _contour_dict_resolved(ops):
    result = {}
    for op in ops:
        if op.op_type != OpType.CONTOUR:
            continue
        path = op.path
        if not path:
            path = build_contour_path(op.params)
        result[op.params.get("name")] = path
    return result


def _nearest_dist(point, candidates):
    x, z = point
    best = min(candidates, key=lambda p: (p[0] - x) ** 2 + (p[1] - z) ** 2)
    return ((best[0] - x) ** 2 + (best[1] - z) ** 2) ** 0.5, best


def _collect_cases():
    cases = []
    for name, (ops, settings) in example_programs().items():
        lines = generate_program_gcode(ops, dict(settings))
        positions = _parse_motion_full(lines)
        contours = _contour_dict_resolved(ops)
        for idx, op in enumerate(ops):
            if op.op_type == OpType.ABSPANEN:
                contour_name = op.params.get("contour_name")
                primitives = contours.get(contour_name)
                idxs = _find_finish_segment_indices(lines)
                if not primitives or idxs is None:
                    continue  # reines Schruppen oder keine Kontur - nichts zu vergleichen
                preview_pts = _corner_points_from_primitives(primitives)
                actual_pts = [positions[i] for i in idxs if i in positions]
                cases.append((f"{name}#{idx}:ABSPANEN", preview_pts, actual_pts))
            elif op.op_type == OpType.FACE:
                idxs = _find_finish_segment_indices(lines) or _find_subroutine_indices(lines)
                if idxs is None:
                    continue
                preview_pts = build_face_path(dict(op.params))
                actual_pts = [positions[i] for i in idxs if i in positions]
                cases.append((f"{name}#{idx}:FACE", preview_pts, actual_pts))
    return cases


_CASES = _collect_cases()
assert len(_CASES) >= 9, f"Erwartet mindestens 9 vergleichbare Faelle, gefunden: {len(_CASES)}"


@pytest.mark.parametrize("label,preview_pts,actual_pts", _CASES, ids=[c[0] for c in _CASES])
def test_actual_gcode_points_lie_on_preview_path(label, preview_pts, actual_pts):
    assert preview_pts, f"{label}: Vorschau-Pfad ist leer"
    assert actual_pts, f"{label}: kein tatsaechlicher G-Code-Punkt gefunden"
    problems = []
    for point in actual_pts:
        dist, nearest = _nearest_dist(point, preview_pts)
        if dist > TOL:
            problems.append((point, nearest, dist))
    assert not problems, (
        f"{label}: {len(problems)}/{len(actual_pts)} G-Code-Punkt(e) weichen mehr als {TOL}mm "
        f"vom Vorschau-Pfad ab: {problems}"
    )
