import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.preview_geometry import build_abspanen_path


def test_update_geometry_does_not_freeze_stale_path_into_params():
    """Realer Bug (echte Step-Datei test-einstich-aussen.json.step.json):
    update_geometry() fror den JEWEILS AKTUELLEN op.path beim ersten Aufruf,
    bei dem "path" noch nicht in op.params stand, als Snapshot in
    op.params["path"] ein (write-once). Bei jeder spaeteren Parameteraenderung
    (z. B. Aussen-Einstich -> Innen-Einstich mit anderem Werkzeug/Durchmesser)
    wurde dieser Snapshot NIE aktualisiert und driftete von der tatsaechlichen
    Geometrie (op.path) weg. Die gespeicherte Step-Datei enthielt dadurch
    widerspruechliche Angaben: tool=7/lage=1 (innen, Durchmesser ~12mm) in den
    Parametern, aber params["path"] zeigte noch die alten Aussen-Koordinaten
    (~40mm) einer frueheren Aussen-Einstich-Version derselben Operation."""
    model = ProgramModel()
    op = Operation(
        OpType.GROOVE,
        {"diameter": 40.0, "width": 4.0, "depth": 1.0, "z": -40.0, "lage": 0, "tool": 4},
    )
    model.update_geometry(op)
    assert "path" not in op.params
    first_path = list(op.path)
    assert any(x > 30.0 for x, _z in first_path)

    # Nutzer aendert die Operation: aus Aussen- wird Innen-Einstich mit
    # anderem Werkzeug und kleinerem Durchmesser.
    op.params.update({"diameter": 12.0, "lage": 1, "tool": 7})
    model.update_geometry(op)

    assert "path" not in op.params, "op.params darf keinen eingefrorenen Alt-Pfad mehr enthalten"
    assert all(x < 20.0 for x, _z in op.path), "op.path muss die aktuelle (innere) Geometrie widerspiegeln"


def test_build_abspanen_path_handles_primitive_shaped_source_path():
    """Realer Bug: resolve_contour_path() (aufgerufen fuer Abspanen.source_path)
    liefert immer op.path einer Kontur-Operation - und das ist IMMER
    primitiven-foermig ({"type": "line"/"arc", "p1": [...], "p2": [...]}), nie
    eine flache Liste aus (x, z)-Punkten. build_abspanen_path() akzeptierte
    bisher nur den flachen Tupel-Fall, der fuer eine echte Kontur-Referenz nie
    eintritt - jede Abspanen-Vorschau in der 'alle Steps'-Uebersicht war
    dadurch leer (op.path == [])."""
    source_path = [
        {"type": "line", "p1": [10.0, -44.0], "p2": [19.2, -44.0]},
        {"type": "line", "p1": [19.2, -44.0], "p2": [19.2, 0.0]},
    ]
    points = build_abspanen_path({"source_path": source_path})
    assert points == [(10.0, -44.0), (19.2, -44.0), (19.2, 0.0)]


def test_build_abspanen_path_still_handles_flat_tuple_source_path():
    points = build_abspanen_path({"source_path": [(1.0, 2.0), (3.0, 4.0)]})
    assert points == [(1.0, 2.0), (3.0, 4.0)]
