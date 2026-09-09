"""Zentraler Bewegungszustand fuer die G-Code-Erzeugung (LES-022, erste Etappe).

Ersetzt die bisherigen ad-hoc settings-Keys `_is_at_safe`/`_safe_x`/`_safe_z`
durch ein typisiertes Objekt. `MotionState` haelt ausschliesslich die zuletzt
tatsaechlich bekannte X/Z-Position (nicht mehr, nicht weniger) - es ist KEIN
vollstaendiger G-Code-Simulator und verfolgt keine Schnittbewegungen
(G1/G2/G3) innerhalb einer Operation, sondern nur die Rueckzugs-/Anfahrt-/
Werkzeugwechsel-Positionierung in `gcode_safety.py`.

Wichtig: `x`/`z` muessen auf `None` gesetzt (bzw. per `clear()` invalidiert)
werden, sobald die reale Position nicht mehr zuverlaessig bekannt ist (z. B.
nach dem Schruppen, dessen Einzelschnitte hier nicht mitgefuehrt werden) -
ein veralteter, aber weiterhin als gueltig behandelter Zustand kann sonst
dazu fuehren, dass ein noetiger Rueckzug auf eine sichere Ebene faelschlich
uebersprungen wird und ein Eilgang direkt durch Restmaterial faehrt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class MotionState:
    x: Optional[float] = None
    z: Optional[float] = None

    def record(self, x: float, z: float) -> None:
        """Beide Achsen auf eine neu erreichte, bekannte Position setzen."""
        self.x = x
        self.z = z

    def update(self, *, x: Optional[float] = None, z: Optional[float] = None) -> None:
        """Nur die tatsaechlich bewegten Achsen aktualisieren (Teilzustellung)."""
        if x is not None:
            self.x = x
        if z is not None:
            self.z = z

    def clear(self) -> None:
        self.x = None
        self.z = None

    def at(self, x: float, z: float, *, tol: float = 1e-6) -> bool:
        return (
            self.x is not None
            and self.z is not None
            and abs(self.x - x) < tol
            and abs(self.z - z) < tol
        )


@dataclass
class SpindleState:
    """CSS(G96)-Modalzustand (LES-022, zweite Etappe).

    `pending` ist eine vorbereitete, aber noch nicht aktivierte CSS-Anfahrt
    (Werkzeug bereits gewaehlt, G97-Anfahrdrehzahl bereits ausgegeben, aber
    die eigentliche G96-Aktivierung wartet auf die tatsaechliche Bearbeitungs-
    position). `active` sind die Parameter der zuletzt tatsaechlich per G96
    aktivierten CSS. `fixed_rpm` ist die zugehoerige begrenzte Anfahrdrehzahl,
    die fuer eine spaetere CSS-Freifahrt (G97-Fallback vor Rueckzug/Werkzeug-
    wechsel) wiederverwendet wird. Ersetzt `_pending_css`/`_active_css`/
    `_css_fixed_rpm`.
    """

    pending: Optional[Tuple[float, float]] = None
    active: Optional[Tuple[float, float]] = None
    fixed_rpm: Optional[int] = None

    def request(self, rpm_limit: float, vc: float, fixed_rpm: int) -> None:
        self.pending = (rpm_limit, vc)
        self.fixed_rpm = fixed_rpm

    def activate(self) -> Optional[Tuple[float, float]]:
        pending, self.pending = self.pending, None
        if pending is not None:
            self.active = pending
        return pending

    def suspend(self, *, resume: bool = False) -> Optional[Tuple[float, float]]:
        active, self.active = self.active, None
        if resume:
            if active is not None:
                self.pending = active
        else:
            self.pending = None
        return active


__all__ = ["MotionState", "SpindleState"]
