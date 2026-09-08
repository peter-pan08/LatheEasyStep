from pathlib import Path
from types import SimpleNamespace
import json

from PyQt5 import QtWidgets, uic

import lathe_easystep_handler
from lathe_easystep.examples import example_programs
from lathe_easystep.persistence import build_program_data, step_data_to_operation
from lathe_easystep.ui_persistence import write_program_file
from lathe_easystep.ui_split import load_split_tab_uis
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.preview_geometry import build_face_path


def test_radius_real_widgets_program_save_load_roundtrip(tmp_path):
    root = uic.loadUi(str(Path(__file__).resolve().parents[1] / "lathe_easystep.ui"))
    handler = SimpleNamespace(root_widget=root, _split_tabs_loaded=False, _log=lambda *a, **k: None)
    load_split_tab_uis(handler)
    edge = root.findChild(QtWidgets.QComboBox, "face_edge_type")
    edge.clear()
    for label, value in (("Keine", "none"), ("Fase", "chamfer"), ("Radius", "radius")):
        edge.addItem(label, value)
    edge.setCurrentIndex(edge.findData("radius"))
    radius = QtWidgets.QDoubleSpinBox(root)
    radius.setValue(1.0)
    ops, settings = example_programs()["Planen_Radius.ngc"]
    ops[-1].params.update(edge_type=edge.currentData(), edge_size=radius.value())
    handler.model = SimpleNamespace(operations=ops)
    handler._normalized_file_path = str
    handler._current_program_path = None
    handler._ensure_step_file_link = lambda *a, **k: True
    handler._build_program_data = lambda: build_program_data(ops, settings, {})
    target = tmp_path / "radius.lse"
    write_program_file(handler, str(target))
    payload = json.loads(target.read_text())
    restored = [step_data_to_operation(data) for data in payload["operations"]]
    assert restored[-1].params["edge_type"] == "radius"
    assert build_face_path(restored[-1].params) == build_face_path(ops[-1].params)
    assert generate_program_gcode(restored, payload["header"]) == generate_program_gcode(ops, settings)
    edge.setItemText(edge.currentIndex(), "Round corner")
    assert edge.currentData() == "radius"
    root.close()
