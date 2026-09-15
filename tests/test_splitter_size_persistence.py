import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep import ui_lifecycle
from lathe_easystep.ui_lifecycle import (
    _parse_saved_splitter_sizes,
    _persist_splitter_sizes,
    _restore_splitter_sizes,
)


class _FakeSettings:
    """Shares one dict across every QSettings() call, like the real backend -
    unlike conftest.py's per-instance _DummySettings stub, which is fine for
    the rest of the suite (each feature there only ever does one write or one
    read per test) but would hide a persist-then-restore round trip bug."""

    def __init__(self):
        self._values = {}

    def value(self, key, default=None, type=None):
        value = self._values.get(key, default)
        return type(value) if type is not None and value is not None else value

    def setValue(self, key, value):
        self._values[key] = value


class _FakeSplitter:
    def __init__(self, sizes):
        self._sizes = list(sizes)
        self.set_sizes_calls = []

    def sizes(self):
        return list(self._sizes)

    def setSizes(self, sizes):
        self.set_sizes_calls.append(list(sizes))
        self._sizes = list(sizes)


def test_parse_saved_splitter_sizes_accepts_valid_pair():
    assert _parse_saved_splitter_sizes("340,700", 2) == [340, 700]


def test_parse_saved_splitter_sizes_rejects_wrong_count():
    assert _parse_saved_splitter_sizes("340,700,10", 2) is None


def test_parse_saved_splitter_sizes_rejects_non_positive_values():
    assert _parse_saved_splitter_sizes("0,700", 2) is None
    assert _parse_saved_splitter_sizes("-5,700", 2) is None


def test_parse_saved_splitter_sizes_rejects_garbage():
    assert _parse_saved_splitter_sizes("abc,def", 2) is None


def test_parse_saved_splitter_sizes_rejects_empty():
    assert _parse_saved_splitter_sizes("", 2) is None
    assert _parse_saved_splitter_sizes(None, 2) is None


def test_restore_splitter_sizes_applies_plausible_saved_value(monkeypatch):
    settings = _FakeSettings()
    settings.setValue("LatheEasyStep/WorkspaceSplitterSizes", "400,600")
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    splitter = _FakeSplitter([340, 700])
    _restore_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes", (330, 380))

    assert splitter.set_sizes_calls == [[400, 600]]


def test_restore_splitter_sizes_ignores_value_below_minimum(monkeypatch):
    settings = _FakeSettings()
    settings.setValue("LatheEasyStep/WorkspaceSplitterSizes", "100,600")
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    splitter = _FakeSplitter([340, 700])
    _restore_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes", (330, 380))

    # zu schmal fuer die bekannten Button-Grid-Mindestbreiten - Standardwerte
    # aus dem Aufrufer bleiben unangetastet (kein setSizes()-Aufruf).
    assert splitter.set_sizes_calls == []


def test_restore_splitter_sizes_ignores_missing_value(monkeypatch):
    settings = _FakeSettings()
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    splitter = _FakeSplitter([340, 700])
    _restore_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes", (330, 380))

    assert splitter.set_sizes_calls == []


def test_persist_splitter_sizes_writes_current_sizes(monkeypatch):
    settings = _FakeSettings()
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    splitter = _FakeSplitter([123, 456])
    _persist_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes")

    assert settings.value("LatheEasyStep/WorkspaceSplitterSizes", "", type=str) == "123,456"


def test_persist_then_restore_round_trip(monkeypatch):
    settings = _FakeSettings()
    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", lambda: settings)

    saved_from = _FakeSplitter([250, 790])
    _persist_splitter_sizes(saved_from, "LatheEasyStep/PreviewParamsSplitterSizes")

    restored_into = _FakeSplitter([180, 520])
    _restore_splitter_sizes(restored_into, "LatheEasyStep/PreviewParamsSplitterSizes", (140, 100))

    assert restored_into.set_sizes_calls == [[250, 790]]


def test_restore_and_persist_tolerate_a_broken_settings_backend(monkeypatch):
    """QSettings() faellt in ungewoehnlichen Umgebungen (fehlender Schreibzugriff
    auf das Konfigverzeichnis o.ae.) unter Umstaenden mit einer Exception aus -
    das darf die Splitter-Einrichtung/-Bedienung nicht zum Absturz bringen."""

    class _BrokenSettings:
        def value(self, *_a, **_k):
            raise OSError("no config dir")

        def setValue(self, *_a, **_k):
            raise OSError("no config dir")

    monkeypatch.setattr(ui_lifecycle.QtCore, "QSettings", _BrokenSettings)

    splitter = _FakeSplitter([340, 700])
    _restore_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes", (330, 380))
    _persist_splitter_sizes(splitter, "LatheEasyStep/WorkspaceSplitterSizes")

    assert splitter.set_sizes_calls == []
