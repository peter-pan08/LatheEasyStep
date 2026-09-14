from types import SimpleNamespace

from lathe_easystep.ui_step_list_view import StepListView


class _FakeItem:
    def __init__(self, text=""):
        self._text = text

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text


class _FakeListWidget:
    def __init__(self, items=None):
        self._items = list(items or [])
        self._current_row = -1
        self._signals_blocked = False
        self._has_focus = False

    def currentRow(self):
        return self._current_row

    def count(self):
        return len(self._items)

    def row(self, item):
        return self._items.index(item) if item in self._items else -1

    def item(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def blockSignals(self, flag):
        self._signals_blocked = bool(flag)

    def setCurrentRow(self, index):
        assert self._signals_blocked or index == index  # no-op placeholder
        self._current_row = index

    def hasFocus(self):
        return self._has_focus


def _handler(list_ops=None):
    return SimpleNamespace(list_ops=list_ops)


def test_unbound_view_reports_not_bound_and_neutral_defaults():
    view = StepListView(_handler(None))
    assert not view.is_bound()
    assert view.selected_row() == -1
    assert view.count() == 0
    assert view.row_of(object()) == -1
    assert view.set_item_text(0, "x") is False
    assert view.has_focus() is False
    view.select_row(2)  # must not raise despite no widget


def test_bound_view_reads_live_state_from_handler_list_ops():
    widget = _FakeListWidget([_FakeItem("a"), _FakeItem("b")])
    widget._current_row = 1
    handler = _handler(widget)
    view = StepListView(handler)
    assert view.is_bound()
    assert view.selected_row() == 1
    assert view.count() == 2
    assert view.row_of(widget._items[0]) == 0


def test_set_item_text_updates_existing_item_and_rejects_out_of_range():
    widget = _FakeListWidget([_FakeItem("old")])
    view = StepListView(_handler(widget))
    assert view.set_item_text(0, "new") is True
    assert widget._items[0].text() == "new"
    assert view.set_item_text(5, "nope") is False


def test_select_row_without_block_signals_sets_current_row_directly():
    widget = _FakeListWidget([_FakeItem("a"), _FakeItem("b")])
    view = StepListView(_handler(widget))
    view.select_row(1)
    assert widget._current_row == 1
    assert widget._signals_blocked is False


def test_select_row_with_block_signals_wraps_call_and_restores_signal_state():
    widget = _FakeListWidget([_FakeItem("a"), _FakeItem("b")])
    view = StepListView(_handler(widget))
    view.select_row(1, block_signals=True)
    assert widget._current_row == 1
    assert widget._signals_blocked is False  # restored after the call


def test_select_row_swallows_widget_exceptions():
    class _Broken(_FakeListWidget):
        def setCurrentRow(self, index):
            raise RuntimeError("boom")

    view = StepListView(_handler(_Broken()))
    view.select_row(0)  # must not raise


def test_has_focus_reflects_widget_state():
    widget = _FakeListWidget()
    widget._has_focus = True
    assert StepListView(_handler(widget)).has_focus() is True
    widget._has_focus = False
    assert StepListView(_handler(widget)).has_focus() is False


def test_view_re_reads_handler_list_ops_on_every_call_no_stale_cache():
    handler = _handler(None)
    view = StepListView(handler)
    assert not view.is_bound()
    handler.list_ops = _FakeListWidget([_FakeItem("a")])
    assert view.is_bound()
    assert view.count() == 1
