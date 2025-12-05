from __future__ import annotations

from typing import List

from .model import Contour, ContourElement, ContourElementType


def contour_to_gcode(contour: Contour, feed: float = 0.2) -> List[str]:
    """Konturelemente in G-Code umsetzen.

    Annahmen:
      - Keine Werkzeugradiuskorrektur (G41/G42) für Milestone 2.
      - Kontur ist in X/Z (Durchmesser) definiert.
      - Zustellung und Schrupp-/Schlichtlogik kommen später.
    """
    lines: List[str] = []
    if contour.is_empty():
        return lines

    # Rapid zum Startpunkt
    lines.append(f"G0 X{contour.x_start:.3f} Z{contour.z_start:.3f}")

    for element in contour.elements:
        lines.extend(_element_to_gcode(element, feed))

    return lines


def _element_to_gcode(element: ContourElement, feed: float) -> List[str]:
    lines: List[str] = []
    x = element.x_end
    z = element.z_end

    if element.type == ContourElementType.LINE_Z:
        lines.append(f"G1 Z{z:.3f} F{feed:.3f}")
    elif element.type == ContourElementType.LINE_X:
        lines.append(f"G1 X{x:.3f} F{feed:.3f}")
    elif element.type == ContourElementType.LINE_XZ:
        lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
    elif element.type in (ContourElementType.ARC_CONCAVE, ContourElementType.ARC_CONVEX):
        # Platzhalter: wir setzen G2/G3 mit Radius.
        # Vorzeichen von Radius, cw/ccw und wirkliche Geometrie
        # kann später genauer definiert werden.
        if element.radius is None or element.cw is None:
            # Ohne vollständige Infos kein Bogen → aktuell als Gerade fahren
            lines.append(f"G1 X{x:.3f} Z{z:.3f} F{feed:.3f}")
        else:
            g_code = "G2" if element.cw else "G3"
            lines.append(
                f"{g_code} X{x:.3f} Z{z:.3f} R{element.radius:.3f} F{feed:.3f}"
            )

    return lines
