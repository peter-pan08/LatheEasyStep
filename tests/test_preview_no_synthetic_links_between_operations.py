import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LES-034: Anfahrt, Rueckzug, Werkzeugwechsel und Parken duerfen im Preview nur
# gezeichnet werden, wenn sie aus demselben Bewegungsplan wie der G-Code
# stammen. Heute erzeugt keine Preview-Quelle solche Bewegungen eigenstaendig
# (weder preview_geometry.py noch preview_scene.py noch ui_preview.py bauen
# Anfahrt-/Werkzeugwechsel-/Park-Segmente). Diese Garantie haengt strukturell
# daran, dass paintEvent() jeden Operationspfad ueber einen eigenen
# drawPolyline()-Aufruf zeichnet, statt mehrere unabhaengige Pfade zu einer
# gemeinsamen Polylinie zu verketten. Dieser Test macht genau das dauerhaft
# pruefbar: eine echte Verkettung wuerde aus zwei 2-Punkt-Pfaden einen
# 4-Punkt-Polyline-Aufruf machen (die erfundene Verbindungslinie), statt
# zweier getrennter 2-Punkt-Aufrufe.
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtGui, QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.preview_widget import LathePreviewWidget  # noqa: E402


def _paint(widget):
    widget.resize(400, 300)
    widget.show()
    _app.processEvents()
    widget.repaint()
    _app.processEvents()


def test_no_polyline_bridges_the_gap_between_two_independent_operation_paths(monkeypatch):
    recorded_point_counts = []
    original_draw_polyline = QtGui.QPainter.drawPolyline

    def _record(self, polygon, *args, **kwargs):
        recorded_point_counts.append(polygon.count())
        return original_draw_polyline(self, polygon, *args, **kwargs)

    monkeypatch.setattr(QtGui.QPainter, "drawPolyline", _record)

    widget = LathePreviewWidget()
    path_a = [(10.0, 0.0), (10.0, -20.0)]
    path_b = [(80.0, -50.0), (80.0, -70.0)]  # weit entfernt, keine reale Verbindung
    widget.set_paths([path_a, path_b], active_index=None)
    _paint(widget)

    assert recorded_point_counts.count(2) >= 2
    assert 4 not in recorded_point_counts
