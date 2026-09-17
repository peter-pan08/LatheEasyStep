import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.model import Operation, OpType
from lathe_easystep.tool_logic import radius_warning_details
from lathe_easystep.tool_table_state import ToolTableState
from lathe_easystep.tools import Tool
from lathe_easystep.ui_preview import collect_preview_state

# Nutzerauftrag 2026-09-13: das Werkzeug-Warnsystem war vollstaendig
# implementiert, aber nirgends an die tatsaechliche Warnungs-Pipeline
# (prog["__warnings"]) angebunden - Warnungen erschienen nie im Panel.
# Nutzerentscheidung: anbinden, da eine real gepflegte Werkzeugtabelle
# den Radius grundsaetzlich enthaelt, ein Fehlen also ein sinnvolles
# Warnsignal ist.
#
# Bei der Umsetzung stellte sich heraus, dass NUR der Radius-Teil
# (radius_warning_details) tatsaechlich neu ist. Der ebenfalls gefundene
# Orientierungs-Abgleich (tool_logic.py::collect_tool_orientation_warnings)
# ist eine bereits vollstaendig redundante Zweitimplementierung eines
# Checks, der in checks.py::validate_program_setup (Zeilen ~129-132)
# bereits aktiv und in prog["__warnings"] angebunden ist ("Tool T.. wirkt
# wie Innenwerkzeug, Operation aber wie Aussenbearbeitung" o.ae.) - eine
# Anbindung der tool_logic.py-Version haette diese Warnung doppelt
# ausgegeben. Deshalb hier bewusst NICHT verdrahtet, siehe TODO.md.


def _tool(**overrides):
    defaults = dict(
        t=1, p=0, d=8.0, q=None, comment="", iso_code=None, iso_size=None,
        radius_mm=0.5, kind="turning", wear=False, radius_source=None,
    )
    defaults.update(overrides)
    return Tool(**defaults)


class _FakeHandler:
    OpType = OpType

    def __init__(self, operations, tools):
        self.model = type("M", (), {"operations": operations})()
        self._tool_table = ToolTableState(tools=tools)

    def _radius_warning_details(self):
        return radius_warning_details(self)


def test_radius_warning_details_flags_tool_without_radius():
    op = Operation(OpType.ABSPANEN, {"tool": 2, "side": "outside"})
    tool = _tool(t=2, radius_mm=0.0)
    h = _FakeHandler([op], {2: tool})
    details = h._radius_warning_details()
    assert len(details) == 1
    assert "T02" in details[0]["message"]


def test_radius_warning_details_silent_when_radius_known():
    op = Operation(OpType.ABSPANEN, {"tool": 2, "side": "outside"})
    tool = _tool(t=2, radius_mm=0.4)
    h = _FakeHandler([op], {2: tool})
    assert h._radius_warning_details() == []


def _preview_state_kwargs():
    noop_1arg = lambda _p: []
    return dict(
        build_contour_path=noop_1arg,
        build_face_path=noop_1arg,
        build_thread_path=noop_1arg,
        build_groove_preview_path=noop_1arg,
        build_drill_path=noop_1arg,
        build_keyway_path=noop_1arg,
        build_abspanen_path=noop_1arg,
        build_stock_outline=noop_1arg,
        build_retract_primitives=noop_1arg,
        build_worklimit_primitives=lambda _p, _stock: [],
        build_chuck_nogo_primitives=noop_1arg,
    )


class _FakePreviewHandler(_FakeHandler):
    list_ops = None

    def _collect_program_header(self):
        return {}

    def _log(self, *args, **kwargs):
        pass


def test_collect_preview_state_surfaces_radius_warning_in_program_warnings():
    """Regressionstest fuer die Anbindung: vorher wurde radius_warning_details()
    berechnet, aber nie in prog["__warnings"] aufgenommen - die Warnung
    erreichte den Nutzer nie."""
    op = Operation(OpType.ABSPANEN, {"tool": 3, "side": "outside"})
    tool = _tool(t=3, radius_mm=0.0)
    handler = _FakePreviewHandler([op], {3: tool})
    _paths, _active, prog, _active_op = collect_preview_state(handler, **_preview_state_kwargs())
    assert any("T03" in w and "Radius" in w for w in prog["__warnings"])
