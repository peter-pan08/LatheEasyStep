import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType
from lathe_easystep.model import ProgramModel


def test_build_program_data_refreshes_stale_abspanen_source_path():
    """Realer Bug (Report-Punkt 6, 'Konturdaten sind intern widerspruechlich'):
    Ein Abspanen-Step cacht die Kontur-Geometrie in params["source_path"] (fuer
    die Vorschau in der 'alle Steps'-Uebersicht). Dieser Cache wurde bisher nur
    beim PROGRAMM-LADEN aufgefrischt (_rebuild_all_operation_geometry), nicht
    beim Speichern. Wurde eine Kontur bearbeitet, ohne dass der davon
    abhaengige Abspanen-Step zwischenzeitlich erneut ausgewaehlt wurde, landete
    die veraltete Kontur-Geometrie im gespeicherten Programm - obwohl die
    G-Code-Erzeugung selbst (generate_program_gcode) die Kontur immer frisch
    aufloest und daher korrekt blieb. build_program_data() (aufgerufen vor
    jedem Speichern) muss dieselbe Auffrischung vornehmen wie das Laden."""
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    contour_params = {
        "name": "ausdrehen",
        "start_x": 10.0, "start_z": -44.0,
        "segments": [
            {"mode": "xz", "x": 19.2, "z": 0.0, "x_empty": False, "z_empty": False},
        ],
    }
    contour = Operation(OpType.CONTOUR, contour_params, path=[(10.0, -44.0), (19.2, 0.0)])
    abspanen = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11,
            "side": "inside",
            "contour_name": "ausdrehen",
            "comment": "Innen-Schlichten",
            # Absichtlich veraltete Kontur-Geometrie, wie sie vor einer
            # spaeteren Kontur-Bearbeitung im Step gecacht gewesen sein koennte.
            "source_path": [(99.0, -99.0)],
        },
        path=[(99.0, -99.0)],
    )

    handler.model = ProgramModel()
    handler.model.operations = [contour, abspanen]
    handler._update_selected_operation = lambda force=False: None
    handler._collect_program_header = lambda: {"program_name": "Test"}
    handler._current_program_path = None
    handler._current_gcode_path = None

    data = handler._build_program_data()

    refreshed_abspanen = next(op for op in data["operations"] if op["op_type"] == OpType.ABSPANEN)
    refreshed_source_path = refreshed_abspanen["params"]["source_path"]
    assert refreshed_source_path != [(99.0, -99.0)]
    endpoints = {tuple(pt) for prim in refreshed_source_path for pt in (prim["p1"], prim["p2"])}
    assert (10.0, -44.0) in endpoints
    assert (19.2, 0.0) in endpoints
