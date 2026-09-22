"""class_patch__() must replace the QtVCP window's closeEvent with the
dirty-state-aware handler - the only QtVCP hook that can actually cancel
closing (closing_cleanup__() runs after QApplication.exec() returns, per
/usr/bin/qtvcp, and cannot prevent the window from closing)."""

from lathe_easystep_handler import HandlerClass


class _FakeWindow:
    def closeEvent(self, event):
        raise AssertionError("original closeEvent should have been replaced by class_patch__()")


class _FakeHandler:
    def __init__(self):
        self.w = _FakeWindow()
        self.logged = []

    def _log(self, *parts, level=None):
        self.logged.append((level, parts))

    def _handle_window_close_event(self, event):
        return ("patched", event)


def test_class_patch_replaces_window_close_event():
    handler = _FakeHandler()
    original_close_event = handler.w.closeEvent

    HandlerClass.class_patch__(handler)

    assert handler.w.closeEvent is not original_close_event
    assert handler.w.closeEvent("dummy-event") == ("patched", "dummy-event")
    assert handler.logged == []


def test_class_patch_tolerates_missing_window():
    handler = _FakeHandler()
    handler.w = None

    HandlerClass.class_patch__(handler)  # must not raise

    assert handler.w is None
