import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType
from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep.tool_table_state import ToolTableState


class _StubModel:
    def __init__(self):
        self.operations = []

    def update_geometry(self, op):
        pass

    def add_operation(self, op):
        self.operations.append(op)


def _make_handler():
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    handler.model = _StubModel()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler.list_ops = None
    handler._refresh_operation_list = lambda select_index=None: None
    handler._refresh_preview = lambda: None
    handler._update_parting_contour_choices = lambda: None
    handler._update_parting_ready_state = lambda *args, **kwargs: None
    handler._handle_selection_change = lambda idx: None
    handler._clear_dirty_operation = lambda idx: None
    return handler


def test_insert_loaded_operation_backfills_missing_comment():
    """Realer Bug (Test.lse, Innen-Einstich-Step ohne jeden Kommentar):
    params["comment"] wurde bisher nur ueber sync_form_to_operation() (beim
    naechsten Stepwechsel/Speichern) gesetzt. Wurde ein per 'Step laden'
    eingefuegter Step nie erneut ausgewaehlt, blieb der Kommentar dauerhaft
    leer. _insert_loaded_operation() muss das direkt beim Einfuegen nachholen,
    ohne einen bereits vorhandenen (z. B. bewusst individuellen) Kommentar zu
    ueberschreiben."""
    handler = _make_handler()
    op = Operation(OpType.GROOVE, params={"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0}, path=[])

    handler._insert_loaded_operation(op)

    assert str(op.params.get("comment") or "").strip() != ""


def test_insert_loaded_operation_keeps_existing_comment():
    handler = _make_handler()
    op = Operation(OpType.GROOVE, params={"tool": 7, "comment": "Bewusst individueller Kommentar"}, path=[])

    handler._insert_loaded_operation(op)

    assert op.params["comment"] == "Bewusst individueller Kommentar"


def test_insert_loaded_operation_refreshes_stale_numbered_comment():
    """LES-023, realer Bug: eine per 'Step speichern' gesicherte Step-Datei
    enthaelt den zu ihrer damaligen Position gehoerenden, nummerierten
    Kommentar (z. B. "5. Innenabspanen ..."). Wird dieselbe Datei per 'Step
    laden' spaeter an einer ANDEREN Position eingefuegt (hier: als erste und
    einzige Operation), blieb die alte Nummer bisher stehen - im Widerspruch
    zur tatsaechlichen Listenposition. Nur bewusst individuelle Kommentare
    (siehe test_insert_loaded_operation_keeps_existing_comment) duerfen
    unangetastet bleiben; ein bereits nummeriert aussehender Kommentar muss
    aufgefrischt werden."""
    handler = _make_handler()
    op = Operation(
        OpType.GROOVE,
        params={"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0, "comment": "5. Innenabspanen (Werkzeug 3)"},
        path=[],
    )

    handler._insert_loaded_operation(op)

    comment = str(op.params.get("comment") or "")
    assert comment != "5. Innenabspanen (Werkzeug 3)"
    assert not comment.startswith("1. ")
    assert op.params["_auto_comment"] is True


def test_looks_like_generated_step_comment_helper():
    from lathe_easystep.ui_flow import _looks_like_generated_step_comment

    assert _looks_like_generated_step_comment("") is True
    assert _looks_like_generated_step_comment(None) is True
    assert _looks_like_generated_step_comment("5. Innenabspanen (Werkzeug 3)") is True
    assert _looks_like_generated_step_comment("12. Planen") is True
    assert _looks_like_generated_step_comment("Bewusst individueller Kommentar") is False
    assert _looks_like_generated_step_comment("Kommentar mit 5. mittendrin") is False


def _make_add_operation_handler(op_type, params):
    """Handler-Fixture speziell fuer `handle_add_operation()` (ui_flow.py):
    deckt den End-zu-Ende-Pfad ab, nicht nur den `_looks_like_generated_step_
    comment()`-Helfer alleine - siehe test_looks_like_generated_step_comment_
    helper() oben, das nur die reine Funktion prueft."""
    handler = _make_handler()
    handler._runtime = RuntimeState()
    handler._dirty = DirtyState()
    handler._tool_table = ToolTableState(tools={1: object()})
    handler._ensure_core_widgets = lambda: None
    handler._force_attach_core_widgets = lambda: None
    handler._current_op_type = lambda: op_type
    handler._collect_params = lambda _op_type: dict(params)
    handler._ensure_step_file_link = lambda *a, **kw: True
    handler._mark_program_structure_dirty = lambda **kw: None
    handler._log = lambda *a, **kw: None
    return handler


def test_handle_add_operation_refreshes_stale_numbered_comment():
    """LES-023-Regel end-to-end ueber `handle_add_operation()` (ui_flow.py),
    nicht nur ueber `_insert_loaded_operation()` (siehe Tests oben): ein
    bereits nummeriert aussehender Kommentar muss beim Hinzufuegen einer
    neuen Operation aufgefrischt werden."""
    from lathe_easystep.ui_flow import handle_add_operation

    handler = _make_add_operation_handler(
        OpType.GROOVE,
        {"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0, "comment": "5. Innenabspanen (Werkzeug 3)"},
    )

    handle_add_operation(handler)

    assert len(handler.model.operations) == 1
    op = handler.model.operations[0]
    comment = str(op.params.get("comment") or "")
    assert comment != "5. Innenabspanen (Werkzeug 3)"
    assert op.params["_auto_comment"] is True


def test_handle_add_operation_keeps_individual_comment():
    from lathe_easystep.ui_flow import handle_add_operation

    handler = _make_add_operation_handler(
        OpType.GROOVE,
        {"tool": 7, "lage": 1, "diameter": 12.0, "width": 4.0, "z": -40.0, "comment": "Bewusst individueller Kommentar"},
    )

    handle_add_operation(handler)

    op = handler.model.operations[0]
    assert op.params["comment"] == "Bewusst individueller Kommentar"
