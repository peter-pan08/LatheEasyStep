import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass


class DummySettings:
    def __init__(self):
        self._store = {}

    def value(self, key, default=None, type=None):
        return self._store.get(key, default)

    def setValue(self, key, value):
        self._store[key] = value


def _make_bare_handler():
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    return handler


def test_load_program_repopulates_tool_combos_from_already_loaded_table(tmp_path):
    """Realer Bugreport: Werkzeuge sind beim Programmstart geladen, fehlen
    aber nach 'Programm laden' bei einigen Operationen - erst ein manuelles
    Neuladen der Werkzeugtabelle stellt sie wieder her. Ursache:
    handle_load_program() rief nur das dauerhaft ein-mal-gesperrte
    _auto_load_tool_table() auf, das nach dem ersten Aufruf beim
    Programmstart nichts mehr tut. Die bereits im Speicher gehaltene
    Werkzeugtabelle (handler.tools) muss die Combos jedes Mal neu befuellen,
    auch fuer Reiter-Widgets, die erst jetzt (lazy) entstanden sind."""
    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(_sample_program(tmp_path)), None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: DummySettings()

    handler = _make_bare_handler()

    class _StubModel:
        def __init__(self):
            self.operations = []

        def update_geometry(self, op):
            pass

        def add_operation(self, op):
            self.operations.append(op)

    handler.model = _StubModel()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._dialog_start_dir = lambda *a, **k: ""
    handler._remember_dialog_path = lambda *a, **k: None
    handler._load_program_header_to_form = lambda header: None
    handler._rebuild_all_operation_geometry = lambda: None
    handler._refresh_preview = lambda: None
    handler._clear_dirty_state = lambda: None
    handler._op_row_user_selected = True
    handler._active_form_operation_index = 5
    handler.list_ops = type("L", (), {"count": lambda self: 3, "setCurrentRow": lambda self, row: None})()
    handler._refresh_operation_list = lambda select_index=None: None
    handler._handle_selection_change = lambda idx: None

    handler.tools = {1: object()}
    auto_load_calls = []
    handler._auto_load_tool_table = lambda: auto_load_calls.append(True)
    populate_calls = []
    handler._populate_tool_combos = lambda tools: populate_calls.append(tools)

    handler._handle_load_program()

    assert populate_calls == [handler.tools]
    assert auto_load_calls == []


def test_load_program_falls_back_to_auto_load_when_no_tools_cached(tmp_path):
    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (str(_sample_program(tmp_path)), None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: DummySettings()

    handler = _make_bare_handler()

    class _StubModel:
        def __init__(self):
            self.operations = []

        def update_geometry(self, op):
            pass

        def add_operation(self, op):
            self.operations.append(op)

    handler.model = _StubModel()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._dialog_start_dir = lambda *a, **k: ""
    handler._remember_dialog_path = lambda *a, **k: None
    handler._load_program_header_to_form = lambda header: None
    handler._rebuild_all_operation_geometry = lambda: None
    handler._refresh_preview = lambda: None
    handler._clear_dirty_state = lambda: None
    handler._op_row_user_selected = True
    handler._active_form_operation_index = 5
    handler.list_ops = type("L", (), {"count": lambda self: 3, "setCurrentRow": lambda self, row: None})()
    handler._refresh_operation_list = lambda select_index=None: None
    handler._handle_selection_change = lambda idx: None

    handler.tools = {}
    auto_load_calls = []
    handler._auto_load_tool_table = lambda: auto_load_calls.append(True)
    populate_calls = []
    handler._populate_tool_combos = lambda tools: populate_calls.append(tools)

    handler._handle_load_program()

    assert auto_load_calls == [True]
    assert populate_calls == []


def test_new_program_repopulates_tool_combos_from_already_loaded_table():
    """Analog zum Laden: auch 'Neues Programm' darf die bereits geladene
    Werkzeugtabelle nicht vergessen - Combos erst jetzt vorhandener
    Reiter-Widgets muessen ebenfalls aufgefrischt werden."""
    handler = _make_bare_handler()
    handler.model = type("M", (), {"operations": type("O", (), {"clear": lambda self: None})()})()
    handler._creating_new_program = False
    handler._op_row_user_selected = True
    handler._clear_dirty_state = lambda: None
    handler._refresh_operation_list = lambda select_index=None: None
    handler._refresh_preview = lambda: None

    handler.tools = {1: object()}
    populate_calls = []
    handler._populate_tool_combos = lambda tools: populate_calls.append(tools)

    handler._handle_new_program()

    assert populate_calls == [handler.tools]


def _sample_program(tmp_path):
    sample = tmp_path / "example.lse"
    payload = {
        "version": 1,
        "header": {"program_name": "Demo"},
        "meta": {},
        "operations": [
            {"op_type": "program_header", "params": {"program_name": "Demo"}, "path": []},
            {"op_type": "face", "params": {"tool": 1}, "path": []},
        ],
    }
    sample.write_text(json.dumps(payload))
    return sample
