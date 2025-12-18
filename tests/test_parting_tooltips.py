import sys
import os

# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass


class FakeWidget:
    def __init__(self):
        self._tooltip = None
        self._text = None
        self._items = []
        self._current = 0

    def setToolTip(self, text):
        self._tooltip = text

    def setText(self, text):
        self._text = text
    
    def currentIndex(self):
        return 0
    def blockSignals(self, v):
        return None
    def clear(self):
        self._items = []
    def addItem(self, txt):
        self._items.append(txt)
    def setCurrentIndex(self, idx):
        self._current = int(idx)
    def count(self):
        return len(self._items)
    def setWhatsThis(self, text):
        self._whatsthis = text


class FakeCombo:
    def __init__(self, idx):
        self._idx = idx
        self._items = []
        self._current = 0

    def currentIndex(self):
        return self._idx
    def blockSignals(self, v):
        return None
    def clear(self):
        self._items = []
    def addItem(self, txt):
        self._items.append(txt)
    def setCurrentIndex(self, idx):
        self._current = int(idx)
    def count(self):
        return len(self._items)


def test_parting_tooltips_set_for_de_and_en():
    h = object.__new__(HandlerClass)

    # provide a simple _get_widget_by_name which returns fake widgets for specific keys
    widgets = {
        "program_language": FakeCombo(0),
        "parting_slice_strategy": FakeWidget(),
        "parting_slice_step": FakeWidget(),
        "parting_allow_undercut": FakeWidget(),
    }

    def _get_widget_by_name(name):
        return widgets.get(name)

    h._get_widget_by_name = _get_widget_by_name
    h.program_language = widgets["program_language"]

    # Apply German directly to the parting tooltip helper
    h._apply_parting_tooltips("de")
    assert widgets["parting_slice_strategy"]._tooltip is not None
    assert "Bearbeitungsrichtung" in widgets["parting_slice_strategy"]._tooltip
    assert widgets["parting_slice_strategy"]._whatsthis is not None
    assert "Bearbeitungsrichtung" in widgets["parting_slice_strategy"]._whatsthis

    # Apply English directly
    h._apply_parting_tooltips("en")
    assert widgets["parting_slice_strategy"]._tooltip is not None
    assert "roughing direction" in widgets["parting_slice_strategy"]._tooltip.lower()
    assert widgets["parting_slice_strategy"]._whatsthis is not None
    assert "choose the roughing direction" in widgets["parting_slice_strategy"]._whatsthis.lower()
