import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Realer Absturz: die Schnittansicht (view_mode="front"/Slice-Toggle) stuerzte
# das Panel ab, weil preview_widget.py bei der Extraktion aus dem Handler
# (Refactor "Handler-Datei verkleinern") vier Namen ohne Import verwendete
# (is_internal_side, build_keyway_slot_angles, front_view_polar_to_cartesian,
# keyway_slice_bounds). Der projektweite qtpy-Stub (conftest.py) ruft
# paintEvent() nie wirklich auf und haette den fehlenden Import nicht
# gefunden - deshalb wie bei anderen Widget-Tests dieses Projekts mit echtem
# PyQt5. Ausfuehren mit: /usr/bin/python3 -m pytest tests/test_preview_widget_paint_no_crash.py
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Qt bindings are selected once per process by conftest.py.

from PyQt5 import QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.model import Operation, OpType  # noqa: E402
from lathe_easystep.preview_widget import LathePreviewWidget  # noqa: E402


def _paint(widget):
    widget.resize(400, 300)
    widget.show()
    _app.processEvents()
    widget.repaint()
    _app.processEvents()


def _set_front_operations(widget, operations):
    widget.set_front_context({"__operations": operations})


def test_front_view_paints_external_abspanen_without_crash():
    w = LathePreviewWidget()
    w.set_view_mode("front")
    op = Operation(OpType.ABSPANEN, {"side": "outside", "tool": 1}, path=[(30.0, 0.0), (20.0, -10.0)])
    _set_front_operations(w, [op])
    _paint(w)


def test_front_view_paints_internal_abspanen_without_crash():
    """Reproduziert exakt den gemeldeten Absturz (is_internal_side in
    _front_operation_side, aufgerufen aus _front_active_diameters)."""
    w = LathePreviewWidget()
    w.set_view_mode("front")
    op = Operation(OpType.ABSPANEN, {"side": "inside", "tool": 11}, path=[(10.0, 0.0), (19.2, -44.0)])
    _set_front_operations(w, [op])
    _paint(w)


def test_front_view_paints_keyway_without_crash():
    """Reproduziert den zweiten latenten Absturz derselben Klasse
    (build_keyway_slot_angles/front_view_polar_to_cartesian/keyway_slice_bounds
    ebenfalls ohne Import)."""
    w = LathePreviewWidget()
    w.set_view_mode("front")
    op = Operation(
        OpType.KEYWAY,
        {
            "mode": 0,
            "slot_count": 3,
            "start_x_dia": 20.0,
            "nut_depth": 2.0,
            "nut_length": 10.0,
            "slot_width": 4.0,
            "start_z": 0.0,
        },
        path=[],
    )
    _set_front_operations(w, [op])
    w.front_operation = op
    w.set_slice_z(-5.0)
    _paint(w)


def test_side_view_paints_expanded_legend_and_status_messages_without_crash():
    """Uebt legend_layout()/status_message_layout() (LES-024/LES-034) ueber
    den echten Widget-Zeichenpfad aus - inklusive Legende-Header-Klick zum
    Ein-/Ausklappen, das den in der Layoutfunktion berechneten Click-Rect
    verwendet."""
    w = LathePreviewWidget()
    w.set_paths([[(30.0, 0.0), (20.0, -10.0)]])
    w.set_status_messages(["Warnung A", "Warnung B"])
    _paint(w)
    assert w._legend_click_rect is not None

    w.toggle_legend()
    _paint(w)
    assert w._legend_click_rect is not None
