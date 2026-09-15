import pytest

from lathe_easystep.preview_widget import LathePreviewWidget


class _BrokenNumber:
    def __float__(self):
        raise RuntimeError("programming error")


def _bare_widget():
    widget = LathePreviewWidget.__new__(LathePreviewWidget)
    widget.x_is_diameter = True
    widget.slice_z = 4.0
    widget.update = lambda: None
    return widget


def test_numeric_display_helpers_keep_their_fallback_for_invalid_user_values():
    widget = _bare_widget()

    assert widget._x_to_display("invalid") == 0.0
    assert widget._display_x_to_label(None) == 0.0


def test_numeric_display_helpers_do_not_hide_programming_errors():
    widget = _bare_widget()

    with pytest.raises(RuntimeError, match="programming error"):
        widget._x_to_display(_BrokenNumber())
    with pytest.raises(RuntimeError, match="programming error"):
        widget._display_x_to_label(_BrokenNumber())


def test_set_slice_z_rejects_invalid_user_value_but_exposes_programming_error():
    widget = _bare_widget()

    widget.set_slice_z("invalid")
    assert widget.slice_z == 4.0

    with pytest.raises(RuntimeError, match="programming error"):
        widget.set_slice_z(_BrokenNumber())


def test_set_paths_ignores_invalid_points_but_exposes_programming_error():
    widget = _bare_widget()

    widget.set_paths([[('invalid', 1.0), (12.0, 3.0)]])
    assert widget.paths == [[(12.0, 3.0)]]

    with pytest.raises(RuntimeError, match="programming error"):
        widget.set_paths([[(_BrokenNumber(), 1.0)]])
