from __future__ import annotations

from typing import List, Tuple

from .model import Contour, ContourElement, ContourElementType


ValidationError = Tuple[int, str]  # (Elementindex, Beschreibung)


def validate_contour(contour: Contour) -> List[ValidationError]:
    """Einfache Plausibilitätschecks für eine Kontur.

    Ziel:
      - Bei der Programmierung direkt sinnvolle Fehlermeldungen anzeigen.
      - Hier nur Minimalchecks, später erweiterbar.
    """
    errors: List[ValidationError] = []

    if contour.is_empty():
        errors.append((-1, "Kontur enthält keine Elemente."))

    for idx, elem in enumerate(contour.elements):
        if elem.type in (ContourElementType.ARC_CONCAVE, ContourElementType.ARC_CONVEX):
            if elem.radius is None:
                errors.append((idx, "Bogen ohne Radius definiert."))
            if elem.cw is None:
                errors.append((idx, "Bogen ohne Drehrichtung (G2/G3) definiert."))

    return errors
