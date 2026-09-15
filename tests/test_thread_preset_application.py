import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.presets import thread_preset_values
from lathe_easystep.ui_thread import apply_thread_preset


class _Spin:
    def __init__(self, value=0.0):
        self._value = float(value)

    def value(self):
        return self._value

    def setValue(self, value):
        self._value = float(value)


class _Combo:
    def __init__(self, data):
        self._data = data

    def currentData(self):
        return self._data


def _handler(data, **values):
    names = (
        "thread_major_diameter", "thread_pitch", "thread_depth",
        "thread_first_depth", "thread_peak_offset", "thread_retract_r",
        "thread_infeed_q", "thread_spring_passes", "thread_e", "thread_l",
    )
    handler = SimpleNamespace(
        thread_standard=_Combo(data),
        _thread_applying_standard=False,
        _log=lambda *_args, **_kwargs: None,
    )
    for name in names:
        setattr(handler, name, _Spin(values.get(name, 0.0)))
    handler._set_if_zero = lambda spin, value: (
        spin.setValue(value) is None if abs(spin.value()) < 1e-9 else False
    )
    return handler


def test_normalized_thread_preset_values_cover_all_derived_fields():
    values = thread_preset_values({"label": "M10", "major": 10.0, "pitch": 1.5, "profile": "metric"})
    assert values is not None
    assert values["major_diameter"] == 10.0
    assert values["pitch"] == 1.5
    assert values["thread_depth"] == 1.5 * 0.6134
    assert values["infeed_q"] == 29.5


def test_selection_soft_fills_empty_fields_but_keeps_manual_derived_value():
    data = {"label": "M10", "major": 10.0, "pitch": 1.5, "profile": "metric"}
    handler = _handler(data, thread_depth=0.8)

    apply_thread_preset(handler, force=False)

    assert handler.thread_major_diameter.value() == 10.0
    assert handler.thread_pitch.value() == 1.5
    assert handler.thread_depth.value() == 0.8
    assert handler.thread_first_depth.value() > 0.0
    assert handler.thread_retract_r.value() == 1.5


def test_force_application_replaces_manual_values_with_normalized_preset():
    data = {"label": "Tr 20", "major": 20.0, "pitch": 4.0, "profile": "tr"}
    handler = _handler(data, thread_depth=9.0, thread_infeed_q=29.5)

    apply_thread_preset(handler, force=True)

    assert handler.thread_depth.value() == 2.0
    assert handler.thread_infeed_q.value() == 15.0
