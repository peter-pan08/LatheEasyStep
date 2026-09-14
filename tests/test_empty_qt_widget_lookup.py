"""Regressions for Qt widgets whose truth value depends on their contents."""

from types import SimpleNamespace

from PyQt5 import QtWidgets

from lathe_easystep.ui_widget_lookup import find_any_widget, widgets_by_name
from lathe_easystep.ui_widgets import ensure_core_widgets

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_empty_list_widget_is_found_and_bound():
    root = QtWidgets.QWidget()
    list_ops = QtWidgets.QListWidget(root)
    list_ops.setObjectName("listOperations")
    assert not bool(list_ops)  # The PyQt behaviour that caused the regression.

    handler = SimpleNamespace(
        root_widget=root,
        list_ops=None,
        contour_segments=None,
        program_unit=None,
        preview=None,
        _find_root_widget=lambda: root,
    )
    handler._find_any_widget = lambda name: find_any_widget(handler, name)

    assert handler._find_any_widget("listOperations") is list_ops


def test_core_lookup_keeps_empty_list_widget():
    root = QtWidgets.QWidget()
    list_ops = QtWidgets.QListWidget(root)
    list_ops.setObjectName("listOperations")

    handler = SimpleNamespace(root_widget=root, list_ops=None, contour_segments=None,
                              program_unit=None, preview=None)
    handler._panel_from_widget = lambda _widget: None
    handler._find_root_widget = lambda: root
    handler._ensure_list_ops_type = lambda: None
    handler._resolve_core_widgets_strict = lambda: None

    # Limit this regression to the first binding operation; the remaining
    # large handler surface is covered by the integration tests.
    # Supply all attributes referenced after list_ops and stop deliberately.
    def stop_after_first_assignment():
        assert handler.list_ops is list_ops
        raise RuntimeError("binding verified")
    handler._ensure_list_ops_type = stop_after_first_assignment

    import pytest
    with pytest.raises(RuntimeError, match="binding verified"):
        ensure_core_widgets(handler)


def test_authoritative_widget_cache_does_not_repeat_full_tree_lookup():
    handler = SimpleNamespace(
        _widget_name_cache={"known": [object()]},
        _widget_name_cache_authoritative=True,
        _get_widget_by_name=lambda name: (_ for _ in ()).throw(
            AssertionError(f"unexpected full lookup for {name}")
        ),
    )

    assert widgets_by_name(handler, "missing_label") == []


def test_authoritative_cache_accepts_dynamic_handler_widget():
    dynamic = QtWidgets.QCheckBox()
    dynamic.setObjectName("program_preview_warnings")
    handler = SimpleNamespace(
        program_preview_warnings=dynamic,
        _widget_name_cache={},
        _widget_name_cache_authoritative=True,
    )
    handler._cache_named_widget = lambda widget: handler._widget_name_cache.setdefault(
        widget.objectName(), []
    ).append(widget)

    assert widgets_by_name(handler, "program_preview_warnings") == [dynamic]
