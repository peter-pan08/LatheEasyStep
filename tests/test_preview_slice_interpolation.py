import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LES-034: GROOVE/THREAD/ABSPANEN haben - anders als die radiale Keilnut -
# keine separat kodierte Schnittansicht-Formel; die Seitenansicht zeichnet
# op.path direkt, die Schnittansicht interpoliert den Durchmesser bei
# slice_z aus genau demselben op.path (_interp_x_hits_at_z). Beide Ansichten
# koennen fuer diese Operationstypen also strukturell nicht auseinanderlaufen
# - sofern die Interpolation selbst korrekt ist. Das war bisher ungetestet;
# diese Tests sichern die Interpolation direkt gegen bekannte Geometrien ab
# (linearer Verlauf, vertikale Wand/Nutflanke, Bereich ausserhalb des Pfads).
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.preview_widget import LathePreviewWidget  # noqa: E402


def test_interp_x_hits_returns_exact_linear_taper_value():
    widget = LathePreviewWidget()
    path = [(40.0, 0.0), (30.0, -10.0)]
    assert widget._interp_x_hits_at_z(path, -5.0) == [35.0]


def test_interp_x_hits_returns_both_edges_of_a_groove_wall():
    """Nutflanke bei z=-5 (aussen 40 -> Nutgrund 30) sowie die Wand zurueck auf
    40 bei z=-8: ein Schnitt bei z=-5 muss beide Durchmesser (30 und 40)
    liefern, nicht nur einen."""
    widget = LathePreviewWidget()
    path = [(40.0, 0.0), (40.0, -5.0), (30.0, -5.0), (30.0, -8.0), (40.0, -8.0)]
    assert widget._interp_x_hits_at_z(path, -5.0) == [30.0, 40.0]


def test_interp_x_at_z_returns_the_smallest_hit_diameter():
    widget = LathePreviewWidget()
    path = [(40.0, 0.0), (40.0, -5.0), (30.0, -5.0), (30.0, -8.0), (40.0, -8.0)]
    assert widget._interp_x_at_z(path, -5.0) == 30.0


def test_interp_x_hits_returns_nothing_outside_the_path_z_range():
    widget = LathePreviewWidget()
    path = [(40.0, 0.0), (30.0, -10.0)]
    assert widget._interp_x_hits_at_z(path, -20.0) == []
    assert widget._interp_x_at_z(path, -20.0) is None
