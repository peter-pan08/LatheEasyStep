"""Direct unit coverage for ToolTableState (LES-052), independent of the
handler integration exercised in test_tool_table_persists_across_program_
actions.py/test_tool_warning_wiring.py. Qt-free."""

from lathe_easystep.tool_table_state import ToolTableState


def test_defaults_are_empty():
    state = ToolTableState()
    assert state.tools == {}
    assert state.loaded_tools is None
    assert state.missing_iso == []


def test_set_tools_updates_tools_and_loaded_tools_cache():
    state = ToolTableState()
    tools = {1: object()}
    state.set_tools(tools)
    assert state.tools is tools
    assert state.loaded_tools is tools


def test_set_tools_with_empty_dict_clears_tools_but_keeps_loaded_tools_cache():
    """Verhalten aus ui_tools.py::populate_tool_combos() bewusst so
    uebernommen: `loaded_tools` ist eine "letzte bekannte gute Tabelle"-
    Cache fuer lazy auftauchende Combo-Widgets und wird nur bei einer
    NICHT-leeren Tabelle aktualisiert - eine leere Tabelle darf einen
    frueher geladenen guten Cache nicht ueberschreiben."""
    state = ToolTableState()
    first = {1: object()}
    state.set_tools(first)
    state.set_tools({})
    assert state.tools == {}
    assert state.loaded_tools is first


def test_missing_iso_is_a_plain_field_independent_of_set_tools():
    state = ToolTableState()
    state.set_tools({1: object()})
    state.missing_iso = [1]
    assert state.missing_iso == [1]
    # set_tools() beruehrt missing_iso nicht.
    state.set_tools({2: object()})
    assert state.missing_iso == [1]
