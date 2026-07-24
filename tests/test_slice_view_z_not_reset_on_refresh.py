import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType


class _FakePreview:
    def __init__(self):
        self.slice_z = 0.0
        self.set_slice_z_calls = []

    def set_slice_z(self, z_val, emit=False):
        self.slice_z = float(z_val)
        self.set_slice_z_calls.append(z_val)


def _make_handler():
    h = object.__new__(HandlerClass)
    h.preview = _FakePreview()
    return h


def test_ensure_slice_z_matches_operation_does_not_reset_on_repeated_refresh_of_same_op():
    """Realer Bug: die Schnittansicht wirkte 'eingefroren' - beim Ziehen an der
    Schnittkante aenderte sich die dargestellte Position nicht. Ursache:
    _ensure_slice_z_matches_operation() wird bei JEDEM _refresh_preview()-Aufruf
    ausgefuehrt (nicht nur beim Wechsel des Steps) und setzte slice_z
    bedingungslos auf den vorgeschlagenen Standardwert zurueck - jeder
    beliebige Refresh waehrend des Ziehens (Tab-Wechsel, Parameteraenderung,
    periodische Aktualisierung) machte die manuelle Positionierung dadurch
    unsichtbar rueckgaengig."""
    h = _make_handler()
    op = Operation(OpType.ABSPANEN, {"tool": 1}, path=[(10.0, 0.0), (10.0, -20.0)])

    # Erster Refresh fuer diese Operation: Vorschlag darf gesetzt werden.
    h._ensure_slice_z_matches_operation(op)
    assert h.preview.set_slice_z_calls == [-10.0]

    # Nutzer zieht die Schnittkante manuell auf einen anderen Wert.
    h.preview.slice_z = -3.5

    # Ein erneuter Refresh DERSELBEN Operation (z. B. durch einen unabhaengigen
    # Tab-/Parameter-Refresh waehrend des Ziehens) darf die manuell gesetzte
    # Position NICHT zuruecksetzen.
    h._ensure_slice_z_matches_operation(op)
    assert h.preview.slice_z == -3.5
    assert len(h.preview.set_slice_z_calls) == 1


def test_ensure_slice_z_matches_operation_applies_suggestion_for_a_new_operation():
    h = _make_handler()
    op1 = Operation(OpType.ABSPANEN, {"tool": 1}, path=[(10.0, 0.0), (10.0, -20.0)])
    op2 = Operation(OpType.ABSPANEN, {"tool": 2}, path=[(10.0, -30.0), (10.0, -50.0)])

    h._ensure_slice_z_matches_operation(op1)
    assert h.preview.slice_z == -10.0

    h.preview.slice_z = -3.5  # Nutzer zieht manuell

    # Wechsel auf einen ANDEREN Step darf wieder einen neuen Vorschlag setzen.
    h._ensure_slice_z_matches_operation(op2)
    assert h.preview.slice_z == -40.0
