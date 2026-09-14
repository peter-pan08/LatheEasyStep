from lathe_easystep.preview_geometry import legend_layout, status_message_layout

# LES-024/LES-034: legend_layout()/status_message_layout() wurden aus der
# Legende und der Statusmeldungsbox in preview_widget.paintEvent() extrahiert
# - reine Positions-/Groessenberechnung ohne QPainter, jetzt direkt ohne
# echtes PyQt5 testbar. Farben/Stifte bleiben bewusst im Widget (Qt-Stildaten,
# keine Fachlogik).


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
