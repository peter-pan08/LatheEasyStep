from lathe_easystep.preview_geometry import (
    FRONT_VIEW_FILL_COLORS,
    FRONT_VIEW_RING_STYLES,
    LEGEND_ENTRIES,
    PREVIEW_DRAW_STYLES,
    STATUS_BOX_STYLE,
    legend_layout,
    status_message_layout,
)

# LES-024/LES-034: legend_layout()/status_message_layout() wurden aus der
# Legende und der Statusmeldungsbox in preview_widget.paintEvent() extrahiert
# - reine Positions-/Groessenberechnung ohne QPainter, jetzt direkt ohne
# echtes PyQt5 testbar. Farben/Stifte blieben damals bewusst im Widget
# (Qt-Stildaten, keine Fachlogik - fuer das damalige Ziel "Geometrie von Qt
# trennen" richtig).
#
# LES-051 (2026-09-15) greift das mit einem anderen Ziel wieder auf: nicht
# Qt-Reinheit, sondern Austauschbarkeit ueber einen stabilen Datenvertrag
# (dasselbe Muster wie `ToolVisualProvider` fuer Werkzeugbilder). Label,
# RGB-Farbe, Linienbreite und ein Qt-freier Stilname liegen jetzt in
# `LEGEND_ENTRIES`; `paintEvent()` konstruiert daraus nur noch die
# QPen/QColor-Objekte. Keine sichtbare Aenderung - reine Datenquelle
# umgezogen, exakt dieselben Werte wie zuvor direkt im Widget.


def test_legend_layout_expanded_includes_one_row_per_item():
    layout = legend_layout(3, collapsed=False)
    assert len(layout["rows"]) == 3
    # jede Zeile tiefer als die vorherige (von oben nach unten)
    ys = [row["line"][0][1] for row in layout["rows"]]
    assert ys == sorted(ys)
    assert ys[1] > ys[0] and ys[2] > ys[1]


def test_legend_layout_collapsed_has_no_rows_and_a_smaller_box():
    expanded = legend_layout(5, collapsed=False)
    collapsed = legend_layout(5, collapsed=True)
    assert collapsed["rows"] == []
    assert collapsed["box_rect"][3] < expanded["box_rect"][3]


def test_legend_layout_click_rect_is_the_header_area_regardless_of_collapse():
    expanded = legend_layout(4, collapsed=False)
    collapsed = legend_layout(4, collapsed=True)
    assert expanded["click_rect"] == collapsed["click_rect"]


def test_legend_layout_box_width_defaults_to_175():
    layout = legend_layout(2)
    assert layout["box_rect"][2] == 175.0


def test_status_message_layout_returns_none_without_messages():
    assert status_message_layout([], widget_width=800.0) is None
    assert status_message_layout(None, widget_width=800.0) is None


def test_status_message_layout_truncates_to_four_messages_and_eighty_chars():
    messages = [f"message {i}" for i in range(10)]
    long_message = "x" * 200
    layout = status_message_layout([long_message] + messages, widget_width=800.0)
    assert len(layout["messages"]) == 4
    assert len(layout["messages"][0]) == 80
    assert layout["messages"][0] == long_message[:80]


def test_status_message_layout_box_hugs_the_right_edge():
    layout = status_message_layout(["a"], widget_width=800.0)
    x0, y0, box_w, box_h = layout["box_rect"]
    assert x0 + box_w == 800.0 - 8.0
    assert len(layout["line_positions"]) == 1


def test_status_message_layout_box_width_is_capped_at_540():
    layout = status_message_layout(["a"], widget_width=5000.0)
    assert layout["box_rect"][2] == 540.0


def test_legend_entries_are_a_pure_qt_free_data_contract():
    """LES-051: kein QColor/QPen/QtCore.Qt-Enum in LEGEND_ENTRIES selbst -
    reine Zahlen/Strings, importierbar und pruefbar ohne echtes PyQt5 (dieser
    Test laeuft bewusst in der Stub-Qt-Suite, nicht bei den Real-Qt-Tests)."""
    assert len(LEGEND_ENTRIES) == 10
    seen_labels = set()
    for entry in LEGEND_ENTRIES:
        assert set(entry.keys()) == {"label", "color", "width", "style"}
        assert isinstance(entry["label"], str) and entry["label"]
        assert entry["label"] not in seen_labels, "Label doppelt vergeben"
        seen_labels.add(entry["label"])
        assert entry["style"] in ("solid", "dash", "dashdot")
        r, g, b = entry["color"]
        for channel in (r, g, b):
            assert isinstance(channel, int) and 0 <= channel <= 255
        assert isinstance(entry["width"], int) and entry["width"] > 0


def test_legend_layout_row_count_matches_legend_entries_by_default():
    """legend_layout() nimmt die Anzahl der Zeilen als Parameter entgegen -
    der uebliche Aufruf in paintEvent() uebergibt len(LEGEND_ENTRIES)."""
    layout = legend_layout(len(LEGEND_ENTRIES))
    assert len(layout["rows"]) == len(LEGEND_ENTRIES)


def test_status_box_style_is_a_pure_qt_free_data_contract():
    """LES-051: analog zu LEGEND_ENTRIES - kein QColor/QPen/QBrush in
    STATUS_BOX_STYLE selbst, reine Zahlen/Strings."""
    assert set(STATUS_BOX_STYLE.keys()) == {
        "header", "border_color", "fill_color", "text_color",
    }
    assert isinstance(STATUS_BOX_STYLE["header"], str) and STATUS_BOX_STYLE["header"]
    for key in ("border_color", "fill_color", "text_color"):
        channels = STATUS_BOX_STYLE[key]
        assert len(channels) in (3, 4)  # RGB oder RGBA
        for channel in channels:
            assert isinstance(channel, int) and 0 <= channel <= 255


def test_preview_draw_styles_are_a_pure_qt_free_data_contract():
    """LES-051: analog zu LEGEND_ENTRIES/STATUS_BOX_STYLE - kein QColor/
    QtCore.Qt-Enum in PREVIEW_DRAW_STYLES selbst. Deckt genau die style_key-
    Werte ab, die build_preview_draw_plan() (preview_scene.py) tatsaechlich
    erzeugen kann - fehlt einer, wuerde paintEvent() mit einem KeyError
    abstuerzen."""
    expected_keys = {
        "stock", "retract", "worklimit", "chuck_nogo", "contour_rough",
        "feature", "feature_separate", "active", "workpiece", "auxiliary",
        "tool_path",
    }
    assert set(PREVIEW_DRAW_STYLES.keys()) == expected_keys
    for entry in PREVIEW_DRAW_STYLES.values():
        assert set(entry.keys()) == {"color", "width", "style"}
        assert entry["style"] in ("solid", "dash", "dashdot")
        r, g, b = entry["color"]
        for channel in (r, g, b):
            assert isinstance(channel, int) and 0 <= channel <= 255
        assert isinstance(entry["width"], int) and entry["width"] > 0


def test_front_view_ring_styles_are_a_pure_qt_free_data_contract():
    """LES-044/LES-051: analog zu PREVIEW_DRAW_STYLES - kein QColor/
    QtCore.Qt-Enum in FRONT_VIEW_RING_STYLES selbst. Deckt genau die
    style_key-Werte ab, die build_front_view_draw_plan() (preview_scene.py)
    fuer nicht gefuellte Kreise erzeugt - fehlt einer, wuerde
    _paint_front_view() mit einem KeyError abstuerzen."""
    expected_keys = {"stock_od", "stock_id", "outer_ring", "inner_ring", "active_ring"}
    assert set(FRONT_VIEW_RING_STYLES.keys()) == expected_keys
    for entry in FRONT_VIEW_RING_STYLES.values():
        assert set(entry.keys()) == {"color", "width", "style"}
        assert entry["style"] in ("solid", "dash", "dashdot")
        r, g, b = entry["color"]
        for channel in (r, g, b):
            assert isinstance(channel, int) and 0 <= channel <= 255
        assert isinstance(entry["width"], int) and entry["width"] > 0


def test_front_view_fill_colors_are_a_pure_qt_free_data_contract():
    """LES-044/LES-051: die restlichen zwei style_key-Werte, die
    build_front_view_draw_plan() mit filled=True erzeugt (Endkontur-
    Fuellung/-Loch) - RGBA statt RGB, da die Fuellung Transparenz nutzt."""
    expected_keys = {"end_contour_fill", "end_contour_hole"}
    assert set(FRONT_VIEW_FILL_COLORS.keys()) == expected_keys
    for color in FRONT_VIEW_FILL_COLORS.values():
        assert len(color) == 4
        for channel in color:
            assert isinstance(channel, int) and 0 <= channel <= 255
