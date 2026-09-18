"""Tests fuer handle_load_tool_table() (der 'Werkzeugtabelle laden'-Button).

LES-052-Testaudit 2026-09-18: der automatische Startpfad
(auto_load_tool_table) war getestet, der manuelle Reload-Button
(ui_tools.py::handle_load_tool_table, verdrahtet auf btn_load_tool_table)
dagegen nirgends - trotz Dateidialog, Fehlerpfad und Settings-Persistenz.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep.tool_table_state import ToolTableState


class _DummySettings:
    def __init__(self):
        self._store = {}
    def value(self, key, default=None, type=None):
        return self._store.get(key, default)
    def setValue(self, key, value):
        self._store[key] = value


class _Widget:
    def __init__(self):
        self.text_value = None
        self.cursor_reset = False
    def setText(self, text):
        self.text_value = text
    def setCursorPosition(self, pos):
        self.cursor_reset = True


def _write_tool_table(tmp_path, lines):
    path = tmp_path / "tool.tbl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _make_bare_handler():
    orig_init = HandlerClass.__init__
    HandlerClass.__init__ = lambda self, halcomp, widgets, paths: None
    handler = HandlerClass(None, None, None)
    HandlerClass.__init__ = orig_init
    handler._runtime = RuntimeState()
    handler._tool_table = ToolTableState()
    handler.root_widget = None
    handler.tool_table_path = _Widget()
    handler.lbl_tool_table_path = _Widget()
    handler._dialog_start_dir = lambda *a, **k: ""
    handler._remember_dialog_path = lambda *a, **k: None
    populated = []
    handler._populate_tool_combos = lambda tools: populated.append(tools)
    handler._update_tool_previews = lambda: populated.append("previews_updated")
    handler._populate_calls = populated
    return handler


def test_handle_load_tool_table_parses_the_chosen_file_and_updates_state(tmp_path):
    """Erfolgspfad: der Dialog liefert einen echten Dateipfad; die real
    geparste Tabelle muss im ToolTableState landen, die Pfad-Widgets muessen
    den neuen Pfad zeigen, und Combos/Previews muessen tatsaechlich
    (mit den echten Tools) aktualisiert worden sein - nicht nur "kein
    Crash", sondern der volle Datenweg vom Dialog bis zum Zustand."""
    filepath = _write_tool_table(tmp_path, ["T1 P1 D0.4 Q0 ; CNMG120408"])
    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: (filepath, None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: _DummySettings()

    handler = _make_bare_handler()
    handler._handle_load_tool_table()

    assert 1 in handler._tool_table.tools
    assert handler._tool_table.tools[1].comment == "CNMG120408"
    assert handler._tool_table.missing_iso == []  # CNMG120408 ist ein gueltiger ISO-Code
    assert handler.tool_table_path.text_value == filepath
    assert handler.lbl_tool_table_path.text_value == filepath
    assert handler._populate_calls[0] == handler._tool_table.tools
    assert "previews_updated" in handler._populate_calls


def test_handle_load_tool_table_cancel_leaves_existing_state_untouched(tmp_path):
    """Bricht der Anwender den Dateidialog ab (leerer Pfad), darf sich am
    bestehenden Zustand nichts aendern - insbesondere darf eine bereits
    geladene Tabelle nicht durch den Abbruch geloescht werden."""
    sys.modules["qtpy.QtWidgets"].QFileDialog = type(
        "F", (), {"getOpenFileName": staticmethod(lambda *a, **k: ("", None))}
    )
    sys.modules["qtpy.QtCore"].QSettings = lambda: _DummySettings()

    handler = _make_bare_handler()
    filepath = _write_tool_table(tmp_path, ["T9 P9 D0.2 Q0 ; DCMT110408"])
    handler._tool_table.tools, handler._tool_table.missing_iso = handler._parse_tool_table(filepath)

    handler._handle_load_tool_table()

    assert list(handler._tool_table.tools) == [9]
    assert handler.tool_table_path.text_value is None
    assert handler._populate_calls == []
