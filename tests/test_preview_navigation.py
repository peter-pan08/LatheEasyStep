import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtWidgets  # noqa: E402

from lathe_easystep.preview_widget import LathePreviewWidget  # noqa: E402


_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _WheelEvent:
    def __init__(self, pos, delta):
        self._pos = pos
        self._delta = delta
        self.accepted = False

    def pos(self):
        return self._pos

    def angleDelta(self):
        return QtCore.QPoint(0, self._delta)

    def accept(self):
        self.accepted = True


class _MouseEvent:
    def __init__(self, pos, button=QtCore.Qt.LeftButton):
        self._pos = pos
        self._button = button
        self.accepted = False

    def pos(self):
        return self._pos

    def button(self):
        return self._button

    def accept(self):
        self.accepted = True


def _widget():
    widget = LathePreviewWidget()
    widget.resize(400, 240)
    widget.show()
    _app.processEvents()
    return widget


def test_wheel_zoom_uses_cursor_as_fixed_screen_anchor_and_has_limits():
    widget = _widget()
    cursor = QtCore.QPoint(310, 90)
    event = _WheelEvent(cursor, 120)

    widget.wheelEvent(event)

    assert event.accepted is True
    assert widget._view_zoom == pytest.approx(1.2)
    center = widget.rect().center()
    anchor = QtCore.QPointF(cursor - center)
    # Bei einem Zoom um den Mauszeiger kompensiert Pan genau den Anteil,
    # den die Skalierung sonst vom Cursor weg bewegen wuerde.
    assert widget._view_pan.x() == pytest.approx(anchor.x() * (1.0 - 1.2))
    assert widget._view_pan.y() == pytest.approx(anchor.y() * (1.0 - 1.2))

    for _ in range(100):
        widget.wheelEvent(_WheelEvent(cursor, 120))
    assert widget._view_zoom == 20.0
    for _ in range(200):
        widget.wheelEvent(_WheelEvent(cursor, -120))
    assert widget._view_zoom == 0.2


def test_left_drag_pans_when_slice_drag_is_not_active_and_reset_fits_again():
    widget = _widget()
    press = _MouseEvent(QtCore.QPoint(100, 80))
    move = _MouseEvent(QtCore.QPoint(135, 105))
    release = _MouseEvent(QtCore.QPoint(135, 105))

    widget.mousePressEvent(press)
    widget.mouseMoveEvent(move)
    widget.mouseReleaseEvent(release)

    assert widget._view_pan == QtCore.QPointF(35.0, 25.0)
    assert widget._pan_drag is False

    widget._view_zoom = 3.0
    widget.reset_view()
    assert widget._view_zoom == 1.0
    assert widget._view_pan == QtCore.QPointF(0.0, 0.0)


def test_slice_line_keeps_priority_over_left_button_pan():
    widget = _widget()
    widget.set_paths([[(10.0, -10.0), (10.0, 10.0)]])
    widget.set_slice_enabled(True)
    widget.repaint()
    _app.processEvents()

    pos = widget._view_rect.center()
    widget.mousePressEvent(_MouseEvent(pos))

    assert widget._slice_drag is True
    assert widget._pan_drag is False


def test_double_click_restores_fitted_view():
    widget = _widget()
    widget._view_zoom = 4.0
    widget._view_pan = QtCore.QPointF(50.0, -25.0)
    event = _MouseEvent(QtCore.QPoint(200, 120))

    widget.mouseDoubleClickEvent(event)

    assert event.accepted is True
    assert widget._view_zoom == 1.0
    assert widget._view_pan == QtCore.QPointF(0.0, 0.0)


def test_view_zoom_and_pan_properties_delegate_to_view_state():
    """LES-052-Extraktion (ViewState, preview_widget.py): `_view_zoom`/
    `_view_pan` sind jetzt Properties auf `self._view` (ViewState.zoom,
    ViewState.pan_x/pan_y als reine floats, kein QPointF im Zustandsobjekt
    selbst). Diese Rueckuebersetzung an der Qt-Grenze ist die einzige echte
    Logik dieser Kapselung - direkt abgesichert, unabhaengig von den
    komplexeren Navigations-Tests oben."""
    widget = _widget()

    widget._view_zoom = 2.5
    assert widget._view.zoom == 2.5

    widget._view_pan = QtCore.QPointF(12.0, -7.5)
    assert widget._view.pan_x == 12.0
    assert widget._view.pan_y == -7.5
    assert widget._view_pan == QtCore.QPointF(12.0, -7.5)
