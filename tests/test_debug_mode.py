import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep_handler import HandlerClass, _debug_mode_enabled


def test_debug_mode_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LATHEEASYSTEP_DEBUG", raising=False)
    assert _debug_mode_enabled() is False


def test_debug_mode_enabled_via_env_var(monkeypatch):
    for value in ("1", "true", "True", "yes", "on", "debug"):
        monkeypatch.setenv("LATHEEASYSTEP_DEBUG", value)
        assert _debug_mode_enabled() is True, value


def test_debug_mode_rejects_unrelated_values(monkeypatch):
    for value in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("LATHEEASYSTEP_DEBUG", value)
        assert _debug_mode_enabled() is False, value


def _handler_with_debug(debug_mode):
    h = object.__new__(HandlerClass)
    h.debug_mode = debug_mode
    return h


def test_debug_level_log_suppressed_when_debug_mode_off(capsys):
    h = _handler_with_debug(False)
    h._log("should not appear", level="debug")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_debug_level_log_printed_when_debug_mode_on(capsys):
    h = _handler_with_debug(True)
    h._log("visible debug message", level="debug")
    captured = capsys.readouterr()
    assert "visible debug message" in captured.out


def test_info_level_log_always_printed_regardless_of_debug_mode(capsys):
    h = _handler_with_debug(False)
    h._log("normal info message", level="info")
    captured = capsys.readouterr()
    assert "normal info message" in captured.out
