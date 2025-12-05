from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


class ContourElementType(Enum):
    """Arten von Konturelementen, angelehnt an klassische Drehkontur-Programmierung."""

    LINE_Z = auto()        # Gerade nur in Z-Richtung
    LINE_X = auto()        # Gerade nur in X-Richtung
    LINE_XZ = auto()       # Schräge Linie
    ARC_CONCAVE = auto()   # Innenradius
    ARC_CONVEX = auto()    # Außenradius


@dataclass
class ContourElement:
    """Ein einzelnes Konturelement zwischen zwei Punkten.

    Alle Werte sind im Werkstück-Koordinatensystem (X/Z).
    X wird als Durchmesser angenommen, nicht Radius.
    """

    type: ContourElementType

    # Endpunkt des Elements
    x_end: float
    z_end: float

    # Nur für Kreise relevant
    radius: Optional[float] = None   # < 0 kann später z.B. als "Auto" interpretiert werden
    cw: Optional[bool] = None        # True = G2, False = G3, None = nicht relevant

    # Flags für spätere Erweiterungen (z.B. Schruppen/Schlichten etc.)
    roughing: bool = True
    finishing: bool = False


@dataclass
class Contour:
    """Komplette Kontur, bestehend aus mehreren Elementen."""

    # Startpunkt der Kontur (X/Z) – z.B. Rohteildurchmesser und Z-Start
    x_start: float
    z_start: float

    # Liste der Elemente in Reihenfolge
    elements: List[ContourElement] = field(default_factory=list)

    # Metadaten (z.B. Name für die Liste im UI)
    name: str = "Kontur 1"

    def add_element(self, element: ContourElement) -> None:
        self.elements.append(element)

    def is_empty(self) -> bool:
        return not self.elements
