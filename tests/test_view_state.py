"""Direct unit coverage for ViewState (LES-052, fuenfte Zustandskategorie). Qt-frei.

ViewState selbst haelt wie RuntimeState keine eigene Logik - reine
Default-Werte, die vormals als lose Attribute direkt auf LathePreviewWidget
lebten (preview_widget.py). pan_x/pan_y ersetzen das vormalige QPointF,
damit dieses Modul ohne Qt-Import testbar bleibt - preview_widget.py baut
das QPointF an der Grenze ueber die `_view_pan`-Property (siehe
tests/test_preview_navigation.py fuer den Qt-seitigen Rundlauf)."""

from lathe_easystep.view_state import ViewState


def test_defaults_match_previous_loose_attribute_values():
    state = ViewState()
    assert state.zoom == 1.0
    assert state.pan_x == 0.0
    assert state.pan_y == 0.0
    assert state.slice_z == 0.0
    assert state.slice_enabled is False
    assert state.view_mode == "side"
    assert state.active_index is None
    assert state.legend_collapsed is False
    assert state.show_legend is True
    assert state.status_messages == []


def test_fields_are_independent():
    state = ViewState()
    state.slice_enabled = True
    assert state.view_mode == "side"
    assert state.zoom == 1.0


def test_status_messages_default_is_not_shared_between_instances():
    a = ViewState()
    b = ViewState()
    a.status_messages.append("warn")
    assert b.status_messages == []


def test_constructor_accepts_keyword_overrides():
    state = ViewState(view_mode="slice", slice_z=-12.5, active_index=2)
    assert state.view_mode == "slice"
    assert state.slice_z == -12.5
    assert state.active_index == 2
    assert state.zoom == 1.0
