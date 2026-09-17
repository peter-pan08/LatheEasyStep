import os
import sys
from dataclasses import asdict

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LES-044: render_tool_preview() (tool_logic.py) wurde in eine reine
# Geometriefunktion (compute_tool_preview_layout) und einen reinen
# Zeichenteil (render_tool_preview) getrennt. Vorher gab es fuer diese
# Funktion ueberhaupt keine Tests (weder stub noch real). Die hier
# verwendeten Geometrietypen (QPointF/QPolygonF/QRectF) sind im
# projektweiten qtpy-Stub (conftest.py) nicht sinnvoll nutzbar
# (QPointF ist dort ein bedeutungsloses Dummy-Objekt ohne x()/y()) -
# deshalb wie bei anderen Widget-/Geometrie-Tests dieses Projekts mit
# echtem PyQt5. Ausfuehren mit:
# /usr/bin/python3 -m pytest tests/test_tool_preview_layout.py
pytest.importorskip("PyQt5")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: E402

_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

from lathe_easystep.tool_logic import (  # noqa: E402
    build_insert_geometry,
    compute_tool_preview_layout,
    infer_insert_profile,
    infer_insert_shape_key,
    render_tool_preview,
    resolve_tool_visual,
    tool_holder_angle,
    tool_orientation_angle,
)
from lathe_easystep.tools import Tool  # noqa: E402
from lathe_easystep.tool_visuals import ToolVisualProvider  # noqa: E402

_INSERT_SHAPE_KEYS = {"C", "D", "V", "S", "T", "W", "R"}


class _FakeHandler:
    """Minimaler Handler-Ersatz: stellt nur die reinen Geometriehelfer
    bereit, die compute_tool_preview_layout()/render_tool_preview()
    benoetigen - dieselben Funktionen wie lathe_easystep_handler.py,
    keine eigene Logikkopie."""

    _INSERT_SHAPE_KEYS = _INSERT_SHAPE_KEYS

    def __init__(self):
        self._tool_visual_provider = ToolVisualProvider()
        self.logs = []

    def _log(self, message, level=None):
        self.logs.append((level, message))

    def _infer_insert_shape_key(self, tool):
        return infer_insert_shape_key(self, tool)

    def _infer_insert_profile(self, tool):
        return infer_insert_profile(self, tool)

    def _build_insert_geometry(self, shape_key, insert_size, family="turning", handed="neutral", groove_width_mm=0.0):
        return build_insert_geometry(self, shape_key, insert_size, family, handed, groove_width_mm)

    def _tool_orientation_angle(self, orientation):
        return tool_orientation_angle(self, orientation)

    def _tool_holder_angle(self, orientation, family, handed):
        return tool_holder_angle(self, orientation, family, handed)

    def _compute_tool_preview_layout(self, tool):
        return compute_tool_preview_layout(self, tool)

    def _render_tool_preview(self, tool):
        return render_tool_preview(self, tool)

    def _resolve_tool_visual(self, tool):
        return resolve_tool_visual(self, tool)


def _tool(**overrides):
    defaults = dict(
        t=1, p=0, d=8.0, q=None, comment="", iso_code=None, iso_size=None,
        radius_mm=0.0, kind="turning", wear=False, radius_source=None,
    )
    defaults.update(overrides)
    return Tool(**defaults)


def test_turning_tool_without_radius_has_diamond_polygon_and_no_nose_circle():
    h = _FakeHandler()
    tool = _tool(comment="CNMG 120408", iso_code="CNMG120408")
    layout = h._compute_tool_preview_layout(tool)
    assert layout["family"] == "turning"
    assert layout["polygon"] is not None
    assert len(layout["polygon"]) == 4
    assert layout["nose_pt"] is None
    assert layout["nose_radius"] is None
    assert 0.5 <= layout["scale"] <= 12.0


def test_turning_tool_with_radius_places_nose_circle_on_rightmost_polygon_point():
    h = _FakeHandler()
    tool = _tool(comment="CNMG 120408", iso_code="CNMG120408", radius_mm=0.8)
    layout = h._compute_tool_preview_layout(tool)
    assert layout["nose_pt"] is not None
    assert layout["nose_radius"] is not None and layout["nose_radius"] > 0.0
    expected_x = max(p.x() for p in layout["polygon"])
    assert layout["nose_pt"].x() == pytest.approx(expected_x)


def test_internal_groove_tool_places_nose_circle_on_leftmost_point_not_rightmost():
    """handed="internal" muss den entgegengesetzten Extrempunkt liefern wie
    handed="external" - sonst zeigt die Werkzeugspitze in der Vorschau in
    die falsche Richtung."""
    h = _FakeHandler()
    internal = _tool(comment="MGMN200 Innen", radius_mm=0.2)
    external = _tool(comment="MGMN200 Aussen", radius_mm=0.2)
    internal_layout = h._compute_tool_preview_layout(internal)
    external_layout = h._compute_tool_preview_layout(external)
    assert internal_layout["family"] == "groove"
    assert internal_layout["handed"] == "internal"
    assert external_layout["handed"] == "external"
    internal_expected_x = min(p.x() for p in internal_layout["polygon"])
    external_expected_x = max(p.x() for p in external_layout["polygon"])
    assert internal_layout["nose_pt"].x() == pytest.approx(internal_expected_x)
    assert external_layout["nose_pt"].x() == pytest.approx(external_expected_x)
    assert internal_layout["nose_pt"].x() < 0.0
    assert external_layout["nose_pt"].x() > 0.0


def test_thread_tool_layout_has_triangular_polygon():
    h = _FakeHandler()
    tool = _tool(comment="Aussen Gewinde ER16", iso_code="ER16")
    layout = h._compute_tool_preview_layout(tool)
    assert layout["family"] == "thread"
    assert layout["polygon"] is not None
    assert len(layout["polygon"]) == 3


def test_holder_tool_layout_has_no_insert_polygon_but_a_drill_triangle():
    h = _FakeHandler()
    tool = _tool(comment="ER Collet Spannzangenaufnahme", d=10.0)
    layout = h._compute_tool_preview_layout(tool)
    assert layout["family"] == "holder"
    assert layout["polygon"] is not None
    assert len(layout["polygon"]) == 3


def test_render_tool_preview_still_produces_a_pixmap_for_every_family():
    h = _FakeHandler()
    tools = [
        _tool(comment="CNMG 120408", iso_code="CNMG120408", radius_mm=0.8),
        _tool(comment="MGMN200 Innen", radius_mm=0.2, t=2),
        _tool(comment="Aussen Gewinde ER16", iso_code="ER16", t=3),
        _tool(comment="ER Collet Spannzangenaufnahme", d=10.0, t=4),
    ]
    for tool in tools:
        pixmap = h._render_tool_preview(tool)
        assert pixmap is not None
        assert pixmap.width() == 140
        assert pixmap.height() == 140


def test_external_png_is_rendered_without_changing_tool_data(tmp_path):
    source = QtGui.QPixmap(20, 10)
    source.fill(QtGui.QColor("#123456"))
    image = tmp_path / "turning.png"
    assert source.save(str(image), "PNG")
    h = _FakeHandler()
    h._tool_visual_provider = ToolVisualProvider(tmp_path, {"turning": image.name})
    tool = _tool(comment="CNMG 120408", iso_code="CNMG120408")
    before = asdict(tool)

    visual = h._resolve_tool_visual(tool)
    pixmap = h._render_tool_preview(tool)

    assert visual.uses_resource is True
    assert pixmap.size() == QtCore.QSize(140, 140)
    assert pixmap.toImage().pixelColor(70, 70) == QtGui.QColor("#123456")
    assert asdict(tool) == before
    assert h.logs == []


def test_missing_external_visual_uses_marked_procedural_fallback(tmp_path):
    h = _FakeHandler()
    h._tool_visual_provider = ToolVisualProvider(tmp_path, {"turning": "missing.svg"})

    pixmap = h._render_tool_preview(_tool())

    assert pixmap.size() == QtCore.QSize(140, 140)
    assert any(level == "warning" and "missing" in message for level, message in h.logs)
    image = pixmap.toImage()
    orange = QtGui.QColor("#fb923c")
    assert any(
        image.pixelColor(x, y) == orange
        for x in range(118, 136)
        for y in range(4, 22)
    )


def test_render_tool_preview_never_marks_program_dirty(tmp_path):
    """LES-052-Abnahmekriterium (doc/PANEL_ARCHITECTURE.md, Abschnitt
    "Darstellungs- und Ressourcenadapter"): fehlende optionale Ressource
    fuehrt zu sichtbarer Diagnose, aber nicht zu geaendertem G-Code oder
    Dirty-/Save-State. Rendern einer Werkzeugvorschau ist eine reine
    Anzeigeaktion und darf _mark_dirty() nie aufrufen - weder mit
    vorhandener noch mit fehlender externer Ressource."""
    h = _FakeHandler()
    h._tool_visual_provider = ToolVisualProvider(tmp_path, {"turning": "missing.svg"})
    dirty_calls = []
    h._mark_dirty = lambda **kwargs: dirty_calls.append(kwargs)

    h._render_tool_preview(_tool())

    assert dirty_calls == []


def test_unreadable_external_visual_falls_back_in_qt_adapter(tmp_path):
    image = tmp_path / "broken.png"
    image.write_bytes(b"not a png")
    h = _FakeHandler()
    h._tool_visual_provider = ToolVisualProvider(tmp_path, {"turning": image.name})

    pixmap = h._render_tool_preview(_tool())

    assert pixmap.size() == QtCore.QSize(140, 140)
    assert any("cannot be decoded" in message for _level, message in h.logs)


def test_switching_tool_visual_resource_never_affects_generated_gcode(tmp_path):
    """LES-051/LES-052 Abnahmekriterium: das Austauschen einer Schneidplatten-
    Grafik darf weder Operationen, Werkzeugdaten noch G-Code veraendern - fuer
    mindestens zwei Darstellungs-/Ressourcensaetze (LES-052-Formulierung).
    Fuer Werkzeugdaten bereits durch `test_external_png_is_rendered_without_
    changing_tool_data` (asdict-Vergleich) belegt; hier zusaetzlich end-to-
    end fuer den tatsaechlichen G-Code-Generatorpfad nachgewiesen, ueber ALLE
    Beispielprogramme (nicht nur eines) - kein gcode_*.py-/checks.py-Modul
    importiert `tool_visuals`/`render_tool_preview` ueberhaupt (rein
    architekturell entkoppelt), dieser Test macht das als Regression konkret
    pruefbar statt nur als Codedurchsicht."""
    from lathe_easystep.examples import example_programs
    from lathe_easystep.gcode_program import generate_program_gcode

    # Werkzeugvorschau mit einer externen Ressource "benutzen" - voellig
    # unabhaengige Tool-/Handler-Instanzen, kein gemeinsamer Zustand mit den
    # unten erzeugten Operationen/Settings.
    source = QtGui.QPixmap(20, 10)
    source.fill(QtGui.QColor("#123456"))
    image = tmp_path / "turning.png"
    assert source.save(str(image), "PNG")

    for filename, (ops_before, settings_before) in example_programs().items():
        gcode_before = generate_program_gcode(ops_before, settings_before)

        h = _FakeHandler()
        h._tool_visual_provider = ToolVisualProvider(tmp_path, {"turning": image.name})
        h._render_tool_preview(_tool(comment="DCMT Außendrehen", iso_code="DCMT110408"))

        ops_after, settings_after = example_programs()[filename]
        gcode_after = generate_program_gcode(ops_after, settings_after)

        assert gcode_after == gcode_before, filename
