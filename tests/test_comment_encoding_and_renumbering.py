import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.gcode_utils import sanitize_gcode_text
from lathe_easystep.ui_flow import handle_move_down, handle_move_up, renumber_operations
from lathe_easystep.model import OpType, Operation


def test_sanitize_gcode_text_transliterates_arrow_instead_of_question_mark():
    """Realer Bug: Ein gespeicherter Kommentar mit Pfeil ("Z 0.0->0.0", als
    echtes Unicode-Zeichen U+2192) wurde beim Schreiben ins G-Code-Programm zu
    "Z 0.0?0.0" - der generische ASCII-Fallback (encode('ascii', 'replace'))
    ersetzt jedes nicht transliterierte Nicht-ASCII-Zeichen durch ein
    bedeutungsloses '?'. Der Pfeil fehlte in der Transliterationstabelle."""
    assert sanitize_gcode_text("Z 0.0→0.0") == "Z 0.0->0.0"
    assert "?" not in sanitize_gcode_text("Z 0.0→0.0")


class _Ops:
    def __init__(self, row, count_val=2):
        self._row = row
        self._count = count_val

    def currentRow(self):
        return self._row

    def count(self):
        return self._count

    def item(self, i):
        return self._items[i]


class _ListItem:
    def __init__(self):
        self.text_value = ""

    def setText(self, text):
        self.text_value = text


class _Model:
    def __init__(self, operations):
        self.operations = operations

    def move_up(self, idx):
        self.operations[idx - 1], self.operations[idx] = self.operations[idx], self.operations[idx - 1]

    def move_down(self, idx):
        self.operations[idx], self.operations[idx + 1] = self.operations[idx + 1], self.operations[idx]


class _Handler:
    def __init__(self, operations):
        self.model = _Model(operations)
        self.list_ops = _Ops(row=1)
        self.list_ops._items = [_ListItem() for _ in operations]
        self._moving_up = False
        self._moving_down = False
        self._mark_program_structure_dirty = lambda operation_indices=None: None
        self._refresh_preview = lambda: None

    def _describe_operation(self, op, number):
        return f"{number}. {op.op_type}"

    def _refresh_operation_list(self, select_index=None):
        self.list_ops._row = select_index if select_index is not None else self.list_ops._row
        for i, op in enumerate(self.model.operations):
            self.list_ops.item(i).setText(self._describe_operation(op, i + 1))

    def _renumber_operations(self):
        renumber_operations(self)


def test_move_up_refreshes_stale_step_number_in_stored_comment():
    """Realer Bug: '(Step 4: ...)' (frisch aus der laufenden Nummerierung) vs.
    '(STEP: 5. ...)' (veralteter, gespeicherter Kommentar) nach einer
    Umsortierung. handle_move_up() muss params["comment"] jeder betroffenen
    Operation auf die neue Position aktualisieren, nicht nur den Listentext."""
    ops = [
        Operation(OpType.FACE, {"comment": "1. face"}),
        Operation(OpType.ABSPANEN, {"comment": "2. abspanen"}),
        Operation(OpType.GROOVE, {"comment": "3. groove"}),
    ]
    handler = _Handler(ops)
    handler.list_ops._row = 1  # "abspanen" nach oben verschieben

    handle_move_up(handler)

    assert ops[0].params["comment"] == "1. abspanen"
    assert ops[1].params["comment"] == "2. face"
    assert ops[2].params["comment"] == "3. groove"


def test_move_down_refreshes_stale_step_number_in_stored_comment():
    ops = [
        Operation(OpType.FACE, {"comment": "1. face"}),
        Operation(OpType.ABSPANEN, {"comment": "2. abspanen"}),
        Operation(OpType.GROOVE, {"comment": "3. groove"}),
    ]
    handler = _Handler(ops)
    handler.list_ops._row = 0  # "face" nach unten verschieben

    handle_move_down(handler)

    assert ops[0].params["comment"] == "1. abspanen"
    assert ops[1].params["comment"] == "2. face"
    assert ops[2].params["comment"] == "3. groove"
