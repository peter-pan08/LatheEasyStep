import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

for _mod in ("qtpy", "qtpy.QtCore", "qtpy.QtGui", "qtpy.QtWidgets"):
    sys.modules.pop(_mod, None)

from PyQt5 import QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.model import OpType, Operation  # noqa: E402
from lathe_easystep.ui_operations import load_operation_params_to_form  # noqa: E402


def test_load_operation_params_to_form_does_not_fire_widget_signals():
    """LES-025: Step-/Operationswechsel darf nicht als Nutzeraenderung
    gelten. load_operation_params_to_form() muss beim Befuellen der Felder
    mit den gespeicherten Werten blockSignals nutzen, sonst wuerde jeder
    Stepwechsel ueber _handle_param_change() den Step faelschlich als
    'dirty' markieren, ohne dass der Nutzer etwas geaendert hat."""
    depth = QtWidgets.QDoubleSpinBox()
    depth.setObjectName("parting_depth_per_pass")
    depth.setDecimals(3)
    depth.setRange(0.0, 100.0)

    mode = QtWidgets.QComboBox()
    mode.setObjectName("parting_mode")
    mode.addItem("Schruppen", "rough")
    mode.addItem("Schlichten", "finish")

    undercut = QtWidgets.QCheckBox()
    undercut.setObjectName("parting_allow_undercut")

    fired = []
    depth.valueChanged.connect(lambda *_a: fired.append("depth"))
    mode.currentIndexChanged.connect(lambda *_a: fired.append("mode"))
    undercut.toggled.connect(lambda *_a: fired.append("undercut"))

    handler = SimpleNamespace(
        _setup_param_maps=lambda: None,
        param_widgets={
            OpType.ABSPANEN: {
                "depth_per_pass": depth,
                "mode": mode,
                "allow_undercut": undercut,
            }
        },
        parting_contour=None,
    )
    op = Operation(
        OpType.ABSPANEN,
        {"depth_per_pass": 1.5, "mode": "finish", "allow_undercut": True, "contour_name": "abdrehen"},
    )

    load_operation_params_to_form(handler, op)

    assert fired == []
    assert depth.value() == pytest.approx(1.5)
    assert mode.currentData() == "finish"
    assert undercut.isChecked() is True
