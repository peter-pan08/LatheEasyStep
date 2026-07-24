import os
import sys
import json
import builtins

# ensure handler module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, Operation, OpType


class DummySettings:
    def __init__(self):
        self._store = {}

    def value(self, key, default=None, type=None):
        return self._store.get(key, default)

    def setValue(self, key, value):
        self._store[key] = value


def test_load_step_updates_settings(monkeypatch, tmp_path):
    # bypass full initialization so we don't hit Qt/qtvcp logic
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    # restore init for safety in same session
    HandlerClass.__init__ = orig_init

    # create sample path before patching dialog
    sample = tmp_path / "example.step.json"

    # patch QFileDialog class in qtpy stub to return a pretend file path
    class _StubFileDialog:
        @staticmethod
        def getOpenFileName(*args, **kwargs):
            return (str(sample), None)
    # add our stub class to the qtpy widgets namespace
    sys.modules["qtpy.QtWidgets"].QFileDialog = _StubFileDialog

    # provide a valid json file for the handler to read
    sample.write_text(json.dumps({"version": 1, "op_type": "face", "params": {}, "path": []}))

    # patch QSettings to our dummy so we can inspect writes
    dummy = DummySettings()
    sys.modules["qtpy.QtCore"].QSettings = lambda: dummy

    # attach a minimal model stub so insertion won't fail
    class _StubModel:
        def __init__(self):
            self.operations = []
        def update_geometry(self, op):
            pass
        def add_operation(self, op):
            self.operations.append(op)
    handler.model = _StubModel()

    # prepare handler internal state normally set during init
    handler._loading_step = False
    handler._step_last_dir = ""
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler.list_ops = None

    # stub out UI update helpers used by _insert_loaded_operation
    handler._refresh_operation_list = lambda select_index=None: None
    handler._refresh_preview = lambda: None
    handler._update_parting_contour_choices = lambda: None
    handler._update_parting_ready_state = lambda *args, **kwargs: None
    handler._handle_selection_change = lambda idx: None

    # call the loader
    handler._handle_load_step()

    # after load the last directory should be stored in settings
    expected_dir = os.path.dirname(str(sample))
    assert dummy.value("LatheEasyStep/StepLastDir", "") == expected_dir
    assert dummy.value("LatheEasyStep/LastDialogDir", "") == expected_dir


def test_save_step_updates_settings(monkeypatch, tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    # monkeypatch selection index and give a dummy operation list
    handler.model = type("M", (), {})()
    handler.model.operations = [Operation(OpType.FACE, params={}, path=[])]
    monkeypatch.setattr(handler, "_selected_operation_index", lambda: 0)

    # intercept file dialog to return a particular destination
    dest = tmp_path / "saved.step.json"
    class _StubFileDialog:
        @staticmethod
        def getSaveFileName(*args, **kwargs):
            return (str(dest), None)
    # add stub to widgets namespace
    sys.modules["qtpy.QtWidgets"].QFileDialog = _StubFileDialog
    # patch QSettings to our dummy (add attribute directly to stub namespace)
    dummy = DummySettings()
    sys.modules["qtpy.QtCore"].QSettings = lambda: dummy

    # prepare handler internal state normally set during init
    handler._saving_step = False
    handler._last_step_dir = ""
    handler._step_last_dir = ""
    handler.root_widget = None
    handler._find_root_widget = lambda: None

    # bypass update routine which would need more UI
    handler._update_selected_operation = lambda force=False: None

    # call the saver
    handler._handle_save_step()

    # directory should have been written to settings
    expected_dir = os.path.dirname(str(dest))
    assert dummy.value("LatheEasyStep/StepLastDir", "") == expected_dir
    assert dummy.value("LatheEasyStep/LastDialogDir", "") == expected_dir


def test_dialog_start_dir_prefers_global_last_dir(tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    dummy = DummySettings()
    global_dir = tmp_path / "global"
    global_dir.mkdir()
    dummy.setValue("LatheEasyStep/LastDialogDir", str(global_dir))
    handler._step_last_dir = ""
    handler._last_dialog_dir = None

    result = handler._dialog_start_dir(dummy, "LatheEasyStep/ProgramLastDir", "LatheEasyStep/LastDialogDir")
    assert result == str(global_dir)


def test_remember_dialog_path_updates_specific_and_global_keys(tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    dummy = DummySettings()
    target = tmp_path / "programs" / "example.lse"
    target.parent.mkdir()

    handler._remember_dialog_path(
        dummy,
        str(target),
        "LatheEasyStep/ProgramLastDir",
        "LatheEasyStep/LastDialogDir",
    )

    expected_dir = str(target.parent)
    assert handler._last_dialog_dir == expected_dir
    assert handler._step_last_dir == expected_dir
    assert dummy.value("LatheEasyStep/ProgramLastDir", "") == expected_dir
    assert dummy.value("LatheEasyStep/LastDialogDir", "") == expected_dir


def test_update_selected_operation_preserves_internal_file_metadata(monkeypatch):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    op = Operation(
        OpType.FACE,
        params={
            "__step_file_path": "/tmp/example.step.json",
            "tool": 1,
        },
        path=[],
    )
    handler.model = type("M", (), {"operations": [op], "update_geometry": lambda self, op: None})()
    handler.list_ops = type("L", (), {"currentRow": lambda self: 0, "item": lambda self, idx: None})()
    handler._op_row_user_selected = True
    handler._collect_params = lambda op_type: {"tool": 2, "feed": 0.1}
    handler._refresh_preview = lambda: None
    handler._update_parting_contour_choices = lambda: None
    handler._describe_operation = lambda op, idx: "Face"

    handler._update_selected_operation(force=True)

    assert op.params["tool"] == 2
    assert op.params["__step_file_path"] == "/tmp/example.step.json"


def test_program_meta_contains_step_file_links(tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    step_path = tmp_path / "01_face.step.json"
    program_path = tmp_path / "test_program.lse"
    op = Operation(
        OpType.FACE,
        params={"tool": 1, "__step_file_path": str(step_path)},
        path=[(1.0, 2.0)],
    )
    handler.model = type("M", (), {"operations": [op]})()
    handler._current_program_path = str(program_path)
    handler._current_gcode_path = None
    handler._update_selected_operation = lambda force=False: None
    handler._collect_program_header = lambda: {"program_name": "Test"}

    data = handler._build_program_data()

    assert "meta" in data
    assert data["meta"]["step_files"][0]["path"] == str(step_path)


def test_write_program_file_prompts_for_missing_step_links(monkeypatch, tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    op = Operation(OpType.FACE, params={"tool": 1}, path=[])
    handler.model = type("M", (), {"operations": [op]})()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._update_selected_operation = lambda force=False: None
    handler._collect_program_header = lambda: {"program_name": "Test"}
    handler._current_program_path = None
    handler._current_gcode_path = None

    created_step = tmp_path / "01_face.step.json"
    monkeypatch.setattr(handler, "_ensure_step_file_link", lambda *args, **kwargs: (op.params.__setitem__("__step_file_path", str(created_step)) or True))

    program_path = tmp_path / "test_program.lse"
    handler._write_program_file(str(program_path))

    saved = json.loads(program_path.read_text())
    assert saved["meta"]["step_files"][0]["path"] == str(created_step)


def test_save_changes_writes_only_dirty_steps_and_dirty_program(tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    step_a = tmp_path / "01.step.json"
    step_b = tmp_path / "02.step.json"
    program_path = tmp_path / "test.lse"
    gcode_path = tmp_path / "test.ngc"
    op_a = Operation(OpType.FACE, params={"tool": 1, "__step_file_path": str(step_a)}, path=[])
    op_b = Operation(OpType.FACE, params={"tool": 2, "__step_file_path": str(step_b)}, path=[])
    handler.model = type("M", (), {"operations": [op_a, op_b]})()
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._saving_changes = False
    handler._current_program_path = str(program_path)
    handler._current_gcode_path = str(gcode_path)
    handler._dirty_operation_indices = {1}
    handler._program_dirty = False
    handler._dirty_program_header = False
    handler._dirty_program_structure = False
    handler._update_selected_operation = lambda force=False: None
    handler._step_file_path = lambda op: op.params.get("__step_file_path")
    handler._operation_to_step_data = lambda op: {"tool": op.params.get("tool")}
    handler._remember_dialog_path = lambda *args, **kwargs: None
    handler._normalized_file_path = lambda path: str(path) if path else None
    handler._write_program_file = lambda path: (_ for _ in ()).throw(AssertionError("program must not be rewritten"))
    gcode_calls = []
    handler._write_gcode_file = lambda path: gcode_calls.append(path)
    handler._clear_dirty_state = lambda: (setattr(handler, "_dirty_operation_indices", set()), setattr(handler, "_program_dirty", False))
    handler._log = lambda *args, **kwargs: None

    class _Settings:
        pass

    sys.modules["qtpy.QtCore"].QSettings = lambda: _Settings()
    infos = []
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(lambda *args: infos.append(args))
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(lambda *args: (_ for _ in ()).throw(AssertionError(args)))

    handler._handle_save_changes()

    assert step_a.exists() is False
    assert json.loads(step_b.read_text()) == {"tool": 2}
    assert gcode_calls == [str(gcode_path)]


def test_save_step_clears_unlinked_structure_dirty_after_new_step_save(tmp_path):
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    dest = tmp_path / "saved.step.json"
    op = Operation(OpType.FACE, params={}, path=[])
    handler.model = type("M", (), {"operations": [op]})()
    handler._saving_step = False
    handler.root_widget = None
    handler._find_root_widget = lambda: None
    handler._selected_operation_index = lambda: 0
    handler._update_selected_operation = lambda force=False: None
    handler._tool_orientation_mismatch = lambda op: None
    handler._set_step_file_path = lambda op, file_path: op.params.__setitem__("__step_file_path", file_path)
    handler._operation_to_step_data = lambda op: {"tool": 1}
    handler._remember_dialog_path = lambda *args, **kwargs: None
    handler._clear_dirty_operation = lambda idx: handler._dirty_operation_indices.discard(idx)
    handler._clear_program_dirty = lambda **kwargs: (setattr(handler, "_dirty_program_structure", False), setattr(handler, "_program_dirty", False))
    handler._normalized_file_path = lambda path: str(path) if path else None
    handler._current_program_path = None
    handler._current_gcode_path = None
    handler._dirty_operation_indices = {0}
    handler._program_dirty = True
    handler._dirty_program_header = False
    handler._dirty_program_structure = True

    class _StubFileDialog:
        @staticmethod
        def getSaveFileName(*args, **kwargs):
            return (str(dest), None)

    class _Settings:
        pass

    sys.modules["qtpy.QtWidgets"].QFileDialog = _StubFileDialog
    sys.modules["qtpy.QtCore"].QSettings = lambda: _Settings()
    sys.modules["qtpy.QtWidgets"].QMessageBox.information = staticmethod(lambda *args, **kwargs: None)
    sys.modules["qtpy.QtWidgets"].QMessageBox.warning = staticmethod(lambda *args, **kwargs: None)
    sys.modules["qtpy.QtWidgets"].QMessageBox.critical = staticmethod(lambda *args: (_ for _ in ()).throw(AssertionError(args)))

    handler._handle_save_step()

    assert handler._dirty_operation_indices == set()
    assert handler._program_dirty is False
    assert handler._dirty_program_structure is False


def test_load_program_always_selects_program_header_row(tmp_path):
    """Regression: handle_load_program() sprang bisher explizit auf Zeile 1
    (den ersten fachlichen Schritt), sobald ein geladenes Programm mehr als
    eine Operation enthielt - was praktisch immer der Fall ist. Der Nutzer
    erwartet, dass der Programmkopf (Zeile 0) grundsaetzlich der
    Ausgangspunkt nach dem Laden ist, unabhaengig davon, wie viele Schritte
    das Programm enthaelt."""
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init

    sample = tmp_path / "example.lse"
    payload = {
        "version": 1,
        "header": {"program_name": "Demo"},
        "meta": {},
        "operations": [
            {"op_type": "program_header", "params": {"program_name": "Demo"}, "path": []},
            {"op_type": "face", "params": {"tool": 1}, "path": []},
            {"op_type": "face", "params": {"tool": 2}, "path": []},
        ],
    }
    sample.write_text(json.dumps(payload))

    class _StubFileDialog:
        @staticmethod
        def getOpenFileName(*args, **kwargs):
            return (str(sample), None)

    sys.modules["qtpy.QtWidgets"].QFileDialog = _StubFileDialog
    sys.modules["qtpy.QtCore"].QSettings = lambda: DummySettings()

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
    handler._auto_load_tool_table = lambda: None
    handler._refresh_preview = lambda: None
    handler._clear_dirty_state = lambda: None
    handler._op_row_user_selected = True
    handler._active_form_operation_index = 5

    class _List:
        def __init__(self):
            self.current_row = None

        def count(self):
            return 3

        def setCurrentRow(self, row):
            self.current_row = row

    handler.list_ops = _List()
    handler._refresh_operation_list = lambda select_index=None: None
    selected_rows = []
    handler._handle_selection_change = lambda idx: selected_rows.append(idx)

    handler._handle_load_program()

    assert handler.list_ops.current_row == 0
    assert selected_rows == [0]
