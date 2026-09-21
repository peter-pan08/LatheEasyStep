"""LES-052 Abschnitt 3 (Audit 2026-09-20/Fix 2026-09-21), Teil A.

`ui_preview.py::collect_preview_state()` ruft fuer eine noch nicht zum
Programm hinzugefuegte, gerade erst begonnene Kontur (Kontur-Tab aktiv,
`handler.model.operations` noch leer - z. B. direkt nach "Neues Programm",
solange der Kontur-Tab aktiv bleibt und noch keine Segmentzeile existiert)
`build_contour_path()` mit dem live aus den Widgets gesammelten Zustand
auf. Seit dem `contour_logic.py`-Fix (LES-052 Abschnitt 3, 2026-09-20)
wirft `build_contour_path()` fuer <2 Punkte einen `ValueError` (vorher ein
verwirrender `TypeError`) - dieser fachlich korrekte Fehler darf im
Preview-Aufbau aber nicht unbehandelt durchschlagen, weil eine
unvollstaendige Kontur ein voellig normaler, temporaerer Eingabezustand
ist (der Nutzer hat schlicht noch keine erste Zeile hinzugefuegt).

`update_contour_preview_temp()` (`ui_contour.py`) loest genau dieses
Problem bereits fuer die Kontur-Tab-eigene Live-Vorschau, indem es vor
`build_contour_path()` erst `validate_contour_segments_for_profile()`
aufruft und bei ungueltigen Daten einfach keine Geometrie erzeugt. Diese
Tests pruefen denselben Mechanismus fuer den zweiten, bisher ungeschuetzten
Aufrufer in `collect_preview_state()` (Haupt-Vorschau-Canvas).

Wie `test_tool_warning_wiring.py` mit einem einfachen Fake-Handler statt
einer echten HandlerClass/Qt-Kette - `collect_preview_state()` braucht fuer
den Kontur-Zweig nur `.value()`/`_collect_contour_segments()`, keine echten
Widgets."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import OpType
from lathe_easystep.ui_preview import collect_preview_state


def _noop_1arg(_p):
    return []


def _preview_state_kwargs():
    return dict(
        build_contour_path=_noop_1arg,
        build_face_path=_noop_1arg,
        build_thread_path=_noop_1arg,
        build_groove_preview_path=_noop_1arg,
        build_drill_path=_noop_1arg,
        build_keyway_path=_noop_1arg,
        build_abspanen_path=_noop_1arg,
        build_stock_outline=_noop_1arg,
        build_retract_primitives=_noop_1arg,
        build_worklimit_primitives=lambda _p, _stock: [],
        build_chuck_nogo_primitives=_noop_1arg,
    )


class _Value:
    def __init__(self, v=0.0):
        self._v = v
    def value(self):
        return self._v


class _FakeContourDraftHandler:
    """Wie unmittelbar nach "Neues Programm" (`handle_new_program()`,
    `ui_flow.py`): `model.operations` leer, der Kontur-Tab ist die aktuell
    aktive Ansicht."""
    OpType = OpType
    list_ops = None
    contour_coord_mode = None

    def __init__(self, segments):
        self.model = type("M", (), {"operations": []})()
        self.contour_start_x = _Value(0.0)
        self.contour_start_z = _Value(0.0)
        self._segments = segments

    def _current_op_type(self):
        return OpType.CONTOUR

    def _collect_contour_segments(self):
        return self._segments

    def _collect_program_header(self):
        return {}

    def _log(self, *args, **kwargs):
        pass


def _real_build_contour_path_kwargs():
    from lathe_easystep.preview_geometry import build_contour_path
    kwargs = _preview_state_kwargs()
    kwargs["build_contour_path"] = build_contour_path
    return kwargs


def test_empty_contour_draft_does_not_raise_and_produces_no_contour_path():
    handler = _FakeContourDraftHandler(segments=[])

    paths, active, _prog, active_operation = collect_preview_state(
        handler, **_real_build_contour_path_kwargs()
    )  # darf NICHT werfen

    assert paths == []
    assert active == -1
    assert active_operation is None


def test_single_segment_contour_draft_does_not_raise_and_produces_no_contour_path():
    """Auch eine Kontur mit genau EINEM Segment darf hier keine Geometrie
    erzeugen - dieselbe Schwelle ("mindestens 2 Segmente"), die die bereits
    etablierte Live-Vorschau (update_contour_preview_temp()) schon
    verwendet."""
    handler = _FakeContourDraftHandler(segments=[{
        "mode": "xz", "x": 10.0, "z": -5.0, "x_empty": False, "z_empty": False,
        "edge": "none", "edge_size": 0.0, "arc_side": "auto", "arc_side_raw": "",
    }])

    paths, active, _prog, active_operation = collect_preview_state(
        handler, **_real_build_contour_path_kwargs()
    )  # darf NICHT werfen

    assert paths == []
    assert active == -1
    assert active_operation is None
