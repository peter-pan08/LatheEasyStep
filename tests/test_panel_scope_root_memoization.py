"""LES-027, 2026-09-14: get_widget_by_name() recomputed its internal
"panel scope root" (an expensive multi-level parentWidget() walk, each
level doing TWO full recursive findChild() scans) on EVERY single call.
setup_param_maps() alone calls get_widget_by_name() roughly 100 times per
startup - real SIM measurement: connect_param_change_signals() cost ~6.7s
of the ~18s total startup time.  Once tab_params/list_ops are bound (by
ensure_core_widgets(), before ensure_advanced_widgets() and
connect_param_change_signals() run), the scope root is structurally
stable and must be memoized instead of recomputed - real re-measurement
after the fix: 0.02s (from 6.7s), total startup ~11s (from ~18s /
originally 69.1s for two full passes before the LES-027 listOperations
fix). ensure_advanced_widgets() calls get_widget_by_name() ~28x more via
_ensure_row() - EARLIER than connect_param_change_signals() - so the
memoization gate uses tab_params/list_ops presence directly rather than
the later _widget_name_cache_authoritative flag, to also speed up that
call site."""

from types import SimpleNamespace

from PyQt5 import QtWidgets

from lathe_easystep.ui_widget_lookup import get_widget_by_name

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _build_panel_tree():
    host = QtWidgets.QWidget()
    host.setObjectName("host")
    panel = QtWidgets.QWidget(host)
    panel.setObjectName("panel")
    mid = QtWidgets.QWidget(panel)
    tab_params = QtWidgets.QWidget(mid)
    tab_params.setObjectName("tabParams")
    list_ops = QtWidgets.QListWidget(panel)
    list_ops.setObjectName("listOperations")
    target = QtWidgets.QWidget(mid)
    target.setObjectName("my_widget")
    return host, panel, tab_params, list_ops, target


def _handler(host, tab_params, list_ops):
    return SimpleNamespace(
        w=None,
        tab_params=tab_params,
        list_ops=list_ops,
        root_widget=host,
        _find_root_widget=lambda: host,
        _widget_name_cache={},
        _cache_named_widget=lambda widget: None,
    )


def test_scope_root_is_cached_after_first_call_once_core_widgets_bound():
    host, panel, tab_params, list_ops, target = _build_panel_tree()
    handler = _handler(host, tab_params, list_ops)

    found = get_widget_by_name(handler, "my_widget")
    assert found is target
    assert handler._panel_scope_root_cache is panel


def test_second_call_reuses_cached_scope_root_instead_of_recomputing():
    """Nach dem ersten Aufruf `tabParams`/`listOperations` umbenennen, sodass
    ein NEU berechneter Scope-Root nicht mehr `panel` waere (die Bedingung
    "has_tabs and has_ops" schlaegt fehl) - der zweite Aufruf muss trotzdem
    weiterhin `panel` als (gecachten) Scope-Root verwenden und das Widget
    finden, statt auf den globalen Fallback (root_widget) auszuweichen."""
    host, panel, tab_params, list_ops, target = _build_panel_tree()
    handler = _handler(host, tab_params, list_ops)

    first = get_widget_by_name(handler, "my_widget")
    assert first is target
    cached_scope = handler._panel_scope_root_cache
    assert cached_scope is panel

    # Invalidate what a FRESH computation would find, without touching the cache.
    tab_params.setObjectName("tabParams_renamed")
    list_ops.setObjectName("listOperations_renamed")

    second = get_widget_by_name(handler, "my_widget")
    assert second is target
    assert handler._panel_scope_root_cache is cached_scope


def test_scope_root_not_cached_before_list_ops_is_bound():
    """Vor `ensure_core_widgets()` (list_ops noch None) darf nichts gecacht
    werden - der fruehe, noch unvollstaendige Baum darf keinen dauerhaft
    falschen Scope-Root festschreiben."""
    host, panel, tab_params, list_ops, target = _build_panel_tree()
    handler = _handler(host, tab_params, list_ops=None)

    get_widget_by_name(handler, "my_widget")
    assert getattr(handler, "_panel_scope_root_cache", None) is None


def test_scope_root_caching_also_helps_before_widget_name_cache_is_authoritative():
    """ensure_advanced_widgets() (ueber _ensure_row()) ruft get_widget_by_name()
    auf, BEVOR _widget_name_cache_authoritative gesetzt wird - die
    Memoisierung darf nicht an dieses spaetere Flag gekoppelt sein."""
    host, panel, tab_params, list_ops, target = _build_panel_tree()
    handler = _handler(host, tab_params, list_ops)
    assert not hasattr(handler, "_widget_name_cache_authoritative")

    found = get_widget_by_name(handler, "my_widget")
    assert found is target
    assert handler._panel_scope_root_cache is panel
