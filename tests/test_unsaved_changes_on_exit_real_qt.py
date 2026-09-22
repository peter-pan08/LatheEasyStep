"""Regressions for the Speichern/Verwerfen/Abbrechen dirty-state exit dialog.

QtVCP's closing_cleanup__() runs only after QApplication.exec() has already
returned (verified against the installed /usr/bin/qtvcp) and therefore
cannot cancel a close. The only hook that can is a genuine closeEvent on the
QtVCP window itself (installed via class_patch__(), see
test_class_patch_close_event.py) - these tests exercise that closeEvent's
actual accept/ignore behaviour with a real QCloseEvent and a real
QMessageBox against the buttons the dialog creates.
"""

from types import SimpleNamespace

from PyQt5 import QtGui, QtWidgets

from lathe_easystep.dirty_state import DirtyState
from lathe_easystep.runtime_state import RuntimeState
from lathe_easystep.ui_dirty import (
    clear_dirty_state,
    handle_window_close_event,
    has_unsaved_changes,
    update_dirty_status,
)
import lathe_easystep.ui_dirty as ui_dirty


def _make_handler(*, dirty: bool):
    window = QtWidgets.QWidget()
    state = DirtyState()
    if dirty:
        state.mark(operation_index=0)
    handler = SimpleNamespace(
        w=window,
        root_widget=window,
        _dirty=state,
        _runtime=RuntimeState(),
        _log=lambda *a, **k: None,
        _find_root_widget=lambda: window,
        label_dirty_status=None,
        btn_save_changes=None,
    )
    handler._has_unsaved_changes = lambda: has_unsaved_changes(handler)
    handler._update_dirty_status = lambda: update_dirty_status(handler)
    handler._clear_dirty_state = lambda: clear_dirty_state(handler)
    return handler, window


def _click_role(role):
    """Fake QMessageBox.exec(): click the button with the given role."""

    def _fake_exec(self):
        for button in self.buttons():
            if self.buttonRole(button) == role:
                self.clickedButton = lambda b=button: b
                return 0
        raise AssertionError(f"no button with role {role} found")

    return _fake_exec


def test_close_without_dirty_state_accepts_without_dialog(monkeypatch):
    handler, window = _make_handler(dirty=False)

    def _must_not_be_called(self):
        raise AssertionError("QMessageBox.exec must not run without dirty state")

    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _must_not_be_called)

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert event.isAccepted()


def test_close_with_dirty_state_cancel_blocks_close(monkeypatch):
    handler, window = _make_handler(dirty=True)
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _click_role(QtWidgets.QMessageBox.RejectRole))

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert not event.isAccepted()
    assert has_unsaved_changes(handler)


def test_close_with_dirty_state_discard_allows_close(monkeypatch):
    handler, window = _make_handler(dirty=True)
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _click_role(QtWidgets.QMessageBox.DestructiveRole))

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert event.isAccepted()
    # "Verwerfen" laesst schliessen zu, raeumt aber keinen fachlichen
    # Zustand auf - das Fenster schliesst ohnehin.
    assert has_unsaved_changes(handler)


def test_close_with_dirty_state_save_success_closes(monkeypatch):
    handler, window = _make_handler(dirty=True)
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _click_role(QtWidgets.QMessageBox.AcceptRole))

    def _fake_save(h):
        h._clear_dirty_state()

    monkeypatch.setattr(ui_dirty, "handle_save_changes", _fake_save)

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert event.isAccepted()
    assert not has_unsaved_changes(handler)


def test_close_with_dirty_state_save_failure_stays_open(monkeypatch):
    handler, window = _make_handler(dirty=True)
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _click_role(QtWidgets.QMessageBox.AcceptRole))

    # Simuliert z. B. "nichts verknuepft" - handle_save_changes() kehrt
    # zurueck, ohne den Dirty-State zu raeumen.
    monkeypatch.setattr(ui_dirty, "handle_save_changes", lambda h: None)

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert not event.isAccepted()
    assert has_unsaved_changes(handler)


def test_close_event_exception_fails_closed(monkeypatch):
    """Ein unerwarteter Fehler bei ungeklaertem Dirty-State darf das Fenster
    NICHT schliessen lassen - Datenverlust ist der schlechtere Fehler als
    ein Fenster, das sich einmal nicht schliesst."""
    handler, window = _make_handler(dirty=True)

    def _boom(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _boom)

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert not event.isAccepted()
    assert has_unsaved_changes(handler)
    # Der Reentranz-Guard muss nach der Ausnahme wieder frei sein, sonst
    # waere ein zweiter Schliessversuch (z. B. nach einem behobenen Fehler)
    # permanent blockiert.
    assert handler._runtime.closing_window is False


def test_close_event_reentrant_call_ignored_without_second_dialog(monkeypatch):
    """Ein zweites Close-Signal, waehrend der erste Aufruf noch laeuft (z. B.
    der Dialog ist noch offen), darf keinen zweiten Dialog stapeln."""
    handler, window = _make_handler(dirty=True)
    exec_calls = []

    def _reentrant_exec(self):
        exec_calls.append(self)
        # Simuliert ein zweites Close-Signal, waehrend der erste Dialog
        # noch laeuft (handler._runtime.closing_window ist bereits True).
        nested_event = QtGui.QCloseEvent()
        handle_window_close_event(handler, nested_event)
        assert not nested_event.isAccepted()
        for button in self.buttons():
            if self.buttonRole(button) == QtWidgets.QMessageBox.DestructiveRole:
                self.clickedButton = lambda b=button: b
                return 0
        raise AssertionError("Verwerfen-Button nicht gefunden")

    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _reentrant_exec)

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert len(exec_calls) == 1  # kein zweiter Dialog wurde erzeugt
    assert event.isAccepted()  # der urspruengliche Aufruf (Verwerfen) schliesst
    assert handler._runtime.closing_window is False


def test_real_handle_save_changes_integration_closes_when_program_saved(monkeypatch, tmp_path):
    """End-to-End mit der echten handle_save_changes()-Speicherfunktion,
    nicht nur der gemockten Orchestrierung oben."""
    handler, window = _make_handler(dirty=False)
    handler._dirty.mark(program=True)
    handler.model = SimpleNamespace(operations=[])
    handler._current_program_path = str(tmp_path / "program.lse")
    handler._current_gcode_path = None
    handler._normalized_file_path = lambda p: p
    handler._update_selected_operation = lambda *a, **k: None
    handler._write_program_file = lambda path: None
    handler._remember_dialog_path = lambda *a, **k: None

    infos = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", _click_role(QtWidgets.QMessageBox.AcceptRole))
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", staticmethod(lambda *a, **k: infos.append(a)))

    event = QtGui.QCloseEvent()
    handle_window_close_event(handler, event)

    assert event.isAccepted()
    assert not has_unsaved_changes(handler)
    assert infos  # the real save-summary dialog was shown
