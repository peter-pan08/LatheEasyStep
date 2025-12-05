from __future__ import annotations

from typing import List, Tuple

from .model import Contour, ContourElement, ContourElementType


Point = Tuple[float, float]  # (X, Z)


def build_contour_path(contour: Contour) -> List[Point]:
    """Berechnet eine Punktliste für die Vorschau.

    Ziel:
      - möglichst einfache, robuste Darstellung
      - keine Werkzeugradiuskorrektur, reine Werkstückkontur

    Diese Funktion kann Schritt für Schritt erweitert werden.
    Im Moment: Minimal-Implementierung mit klarer Struktur.
    """
    if contour.is_empty():
        return []

    path: List[Point] = []

    # Startpunkt der Kontur
    current_x = contour.x_start
    current_z = contour.z_start
    path.append((current_x, current_z))

    for element in contour.elements:
        segment_points = _build_segment(current_x, current_z, element)
        if not segment_points:
            continue
        # letzten Punkt übernehmen, um beim nächsten weiterzumachen
        current_x, current_z = segment_points[-1]
        # ersten Punkt ist identisch mit current_x/current_z -> nur die restlichen übernehmen
        path.extend(segment_points[1:])

    return path


def _build_segment(x0: float, z0: float, element: ContourElement) -> List[Point]:
    """Ein Konturelement in Punkte umsetzen.

    Aktuell:
      - Linien: zwei Punkte (Start/Ende)
      - Kreise: einfache Approximation mit wenigen Punkten (später verfeinern)
    """
    x1, z1 = element.x_end, element.z_end

    if element.type in (ContourElementType.LINE_X, ContourElementType.LINE_Z, ContourElementType.LINE_XZ):
        return [(x0, z0), (x1, z1)]

    if element.type in (ContourElementType.ARC_CONCAVE, ContourElementType.ARC_CONVEX):
        # Platzhalter: 5-Punkte-Approximation der Bogenverbindung.
        # Später kann man hier eine echte Kreisgeometrie implementieren.
        points = [(x0, z0)]
        steps = 4
        for i in range(1, steps + 1):
            t = i / steps
            # einfache lineare Interpolation → nur Dummy,
            # damit die Vorschau nicht leer ist
            xi = x0 + (x1 - x0) * t
            zi = z0 + (z1 - z0) * t
            points.append((xi, zi))
        return points

    # Unbekannter Typ → gar nichts zeichnen
    return []
