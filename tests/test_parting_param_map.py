import sys
import os

# Ensure local package directory is on sys.path so tests can import the handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep_handler import HandlerClass, OpType


def test_parting_param_map_includes_finish_allowance():
    h = object.__new__(HandlerClass)
    # stub _get_widget_by_name to return None; we're only interested in keys
    h._get_widget_by_name = lambda name: None
    # call setup
    h._setup_param_maps()
    parting_map = h.param_widgets.get(OpType.ABSPANEN)
    assert parting_map is not None
    assert "finish_allow_x" in parting_map
    assert "finish_allow_z" in parting_map


def test_setup_param_maps_is_cached_once_all_widgets_are_found():
    """Performance-Regression: setup_param_maps() wurde bisher bei jedem
    Stepwechsel/Feld-Edit komplett neu aufgebaut (100+ _get_widget_by_name()-
    Aufrufe mit eigener Baumsuche pro Aufruf) - das war die Hauptursache fuer
    traege Tab-/Stepwechsel. Sobald alle Widgets einmal gefunden wurden, darf
    ein erneuter Aufruf keine weiteren Lookups mehr ausloesen."""
    h = object.__new__(HandlerClass)
    calls = {"count": 0}

    class _Widget:
        pass

    def _counting_lookup(name):
        calls["count"] += 1
        return _Widget()

    h._get_widget_by_name = _counting_lookup
    h._setup_param_maps()
    first_call_count = calls["count"]
    assert first_call_count > 0

    h._setup_param_maps()
    assert calls["count"] == first_call_count, "setup_param_maps rebuilt widgets on a second call despite full cache"
