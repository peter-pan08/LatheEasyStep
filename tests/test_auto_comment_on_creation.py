import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType


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
    assert comment.startswith("1. ")


def test_handle_add_operation_refreshes_stale_numbered_comment_via_helper():
    from lathe_easystep.ui_flow import _looks_like_generated_step_comment

    assert _looks_like_generated_step_comment("") is True
    assert _looks_like_generated_step_comment(None) is True
    assert _looks_like_generated_step_comment("5. Innenabspanen (Werkzeug 3)") is True
    assert _looks_like_generated_step_comment("12. Planen") is True
    assert _looks_like_generated_step_comment("Bewusst individueller Kommentar") is False
    assert _looks_like_generated_step_comment("Kommentar mit 5. mittendrin") is False
