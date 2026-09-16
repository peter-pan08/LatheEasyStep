from __future__ import annotations

import logging
from typing import Callable, Dict, List, Tuple

from .checks import validate_program_setup
from .contour_features import normalize_relief_mode
from .contour_logic import build_contour_variants, select_thread_relief_for_contour, thread_relief_spec
from .gcode_safety import get_machine_limit_warnings
from .model import OpType, Operation
from .preview_scene import PreviewScene, scene_from_legacy_paths
from .translations import TRANSLATIONS
from .ui_step_list_view import StepListView
from .ui_preview_view import PreviewView

_LOGGER = logging.getLogger(__name__)


def setup_slice_view(handler) -> None:
    if getattr(handler, "_slice_view_setup_done", False):
        return

    # LES-044: (RuntimeError, AttributeError) statt Exception - get_widget_
    # by_name() faengt selbst schon fast jeden Fehler intern ab und liefert
    # sonst None, aber sein schneller Pfad (getattr(widget_root, name, None))
    # kann bei einem bereits zerstoerten C++-Qt-Objekt trotzdem ein
    # RuntimeError("wrapped C/C++ object ... has been deleted") durchlassen -
    # getattr() mit Default faengt nur AttributeError ab, kein RuntimeError.
    if handler.preview is None:
        try:
            handler.preview = handler._get_widget_by_name("previewWidget")
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            pass
    if handler.preview_slice is None:
        try:
            handler.preview_slice = handler._get_widget_by_name("previewSliceWidget")
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            pass
    if handler.btn_slice_view is None:
        try:
            handler.btn_slice_view = handler._get_widget_by_name("btn_slice_view")
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            pass
    if getattr(handler, "btn_reset_view", None) is None:
        try:
            handler.btn_reset_view = handler._get_widget_by_name("btn_reset_view")
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            handler.btn_reset_view = None

    handler._log(
        f"[LatheEasyStep] _setup_slice_view: preview={handler.preview!r} "
        f"preview_slice={handler.preview_slice!r} btn_slice_view={handler.btn_slice_view!r}",
        level="info",
    )

    # Die Preview-UI wird erst waehrend _finalize_ui_ready() aus ihrem
    # Teil-UI geladen. Ein frueher initialized__()-Aufruf darf den Aufbau
    # deshalb nicht dauerhaft als erledigt markieren, solange die drei
    # benoetigten Widgets noch fehlen.
    if handler.preview is None or handler.preview_slice is None or handler.btn_slice_view is None:
        handler._log("[LatheEasyStep] slice view setup deferred until preview UI is loaded", level="info")
        return
    handler._slice_view_setup_done = True

    # LES-044: (RuntimeError, AttributeError) fuer alle folgenden Qt-Widget-
    # Methodenaufrufe in dieser Funktion - RuntimeError bei einem zwischen
    # Lookup und Aufruf zerstoerten C++-Qt-Objekt, AttributeError bei einer
    # fehlenden Methode/einem fehlenden Handler-Attribut (z. B. beim
    # `.connect()` auf einen nicht vorhandenen Handler-Slot).
    if handler.preview is not None:
        try:
            handler.preview.set_view_mode("side")
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            pass

    if handler.preview_slice is not None:
        try:
            handler.preview_slice.set_view_mode("front")
            handler.preview_slice.setVisible(False)
        except (RuntimeError, AttributeError) as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "setup_slice_view", exc)
            pass

    if handler.btn_slice_view is not None:
        try:
            lang = handler._current_language_code() if hasattr(handler, "_current_language_code") else "de"
            handler.btn_slice_view.setChecked(False)
            handler.btn_slice_view.setText(TRANSLATIONS.tr("runtime.preview.slice_view.on", lang))
            handler.btn_slice_view.setToolTip(TRANSLATIONS.tr("runtime.preview.slice_view.tooltip", lang))
            handler.btn_slice_view.toggled.connect(handler._on_toggle_slice_view)
            handler._log("[LatheEasyStep] slice toggle connected", level="info")
        except (RuntimeError, AttributeError, TypeError):
            handler._log("[LatheEasyStep] slice toggle connect failed", level="warning")
    if handler.btn_reset_view is not None:
        try:
            handler.btn_reset_view.clicked.connect(handler._reset_preview_view)
            handler._log("[LatheEasyStep] reset view button connected", level="info")
        except (RuntimeError, AttributeError, TypeError):
            handler._log("[LatheEasyStep] reset view button connect failed", level="warning")
    if handler.preview is not None:
        try:
            handler.preview.sliceChanged.connect(handler._on_slice_changed)
            handler._log("[LatheEasyStep] sliceChanged signal connected", level="info")
        except (RuntimeError, AttributeError, TypeError) as exc:
            handler._log(f"[LatheEasyStep] sliceChanged signal connect failed: {exc}", level="warning")
        try:
            handler.preview._slice_change_callback = handler._on_slice_changed
            handler._log("[LatheEasyStep] slice callback fallback installed", level="info")
        except (RuntimeError, AttributeError) as exc:
            handler._log(f"[LatheEasyStep] slice callback fallback install failed: {exc}", level="warning")


def reset_preview_view(handler) -> None:
    """LES-050: sichtbare Aktion zum Zuruecksetzen von Zoom/Pan der Vorschau,
    gleichwertig zum bestehenden Doppelklick (LathePreviewWidget.reset_view()).
    Betrifft nur die Bildschirmtransformation, nie Modell- oder
    Bearbeitungsdaten. Setzt beide Vorschau-Widgets zurueck (auch die
    Schnittansicht), falls dort in Zukunft ebenfalls navigiert werden kann."""
    for widget_name in ("preview", "preview_slice"):
        widget = getattr(handler, widget_name, None)
        reset = getattr(widget, "reset_view", None)
        if callable(reset):
            try:
                # LES-044: RuntimeError bei zerstoertem C++-Qt-Objekt
                # zwischen getattr() und Aufruf.
                reset()
            except RuntimeError as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "reset_preview_view", exc)
                pass


def update_slice_view_button(handler, checked: bool) -> None:
    button = getattr(handler, "btn_slice_view", None)
    if button is None:
        return
    try:
        # LES-044: _current_language_code() faengt ihre eigenen Qt-Wert-
        # Zugriffe (combo.currentData()/currentIndex()) bereits intern ab,
        # aber ihr get_widget_by_name()-Aufruf liest "self.root_widget"
        # ohne getattr()-Fallback - auf einem minimalen Test-Handler ohne
        # dieses Attribut (verbreitetes Testmuster in diesem Projekt) loest
        # das ein AttributeError aus, kein RuntimeError.
        lang = handler._current_language_code() if hasattr(handler, "_current_language_code") else "de"
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "update_slice_view_button", exc)
        lang = "de"
    text_key = "runtime.preview.slice_view.off" if checked else "runtime.preview.slice_view.on"
    try:
        # AttributeError zusaetzlich zu RuntimeError: "button" ist ein per
        # Widget-Lookup/Test-Double ermitteltes Objekt, dessen Typ (und
        # damit das Vorhandensein von setText()) nicht garantiert ist.
        button.setText(TRANSLATIONS.tr(text_key, lang))
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "update_slice_view_button", exc)
        pass
    try:
        button.setToolTip(TRANSLATIONS.tr("runtime.preview.slice_view.tooltip", lang))
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "update_slice_view_button", exc)
        pass


def ensure_preview_widgets(handler, preview_widget_cls, qt_widget_cls) -> None:
    root = handler.root_widget or handler._find_root_widget()
    if not root:
        return

    def accept_as_preview(widget):
        return widget is not None and (hasattr(widget, "set_primitives") or hasattr(widget, "set_paths"))

    if handler.preview is None:
        widget = root.findChild(preview_widget_cls, "previewWidget")
        if accept_as_preview(widget):
            handler.preview = widget
    if handler.contour_preview is None:
        widget = root.findChild(preview_widget_cls, "contourPreview")
        if accept_as_preview(widget):
            handler.contour_preview = widget

    if handler.preview is None:
        widget = root.findChild(qt_widget_cls, "previewWidget")
        if accept_as_preview(widget):
            handler.preview = widget
    if handler.contour_preview is None:
        widget = root.findChild(qt_widget_cls, "contourPreview")
        if accept_as_preview(widget):
            handler.contour_preview = widget


def collect_preview_state(
    handler,
    *,
    build_contour_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_face_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_thread_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_groove_preview_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_drill_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_keyway_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_abspanen_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_stock_outline: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_retract_primitives: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_worklimit_primitives: Callable[[Dict[str, object], List[Tuple[float, float]]], List[Tuple[float, float]]],
    build_chuck_nogo_primitives: Callable[[Dict[str, object]], List[Tuple[float, float]]],
) -> tuple[list, int, dict, Operation | None]:
    paths: List[List[Tuple[float, float]]] = []
    active = -1
    active_operation: Operation | None = None

    if handler.model.operations:
        selected_row = StepListView(handler).selected_row()
        for row_idx, op in enumerate(handler.model.operations):
            if not op.path:
                continue
            path_idx = len(paths)
            paths.append(op.path)
            if row_idx == selected_row:
                active = path_idx
                active_operation = op
    else:
        try:
            current_type = handler._current_op_type()
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "collect_preview_state", exc)
            current_type = OpType.PROGRAM_HEADER

        if current_type == OpType.CONTOUR and (handler.contour_start_x or handler.contour_segments):
            params: Dict[str, object] = {
                "start_x": handler.contour_start_x.value() if handler.contour_start_x else 0.0,
                "start_z": handler.contour_start_z.value() if handler.contour_start_z else 0.0,
                "coord_mode": handler.contour_coord_mode.currentIndex() if getattr(handler, "contour_coord_mode", None) else 0,
                "segments": handler._collect_contour_segments(),
            }
            contour_prims = build_contour_path(params)
            if contour_prims:
                paths.append(contour_prims)
                active = len(paths) - 1
                active_operation = Operation(OpType.CONTOUR, params, contour_prims)
        elif current_type != OpType.PROGRAM_HEADER:
            try:
                params = handler._collect_params(current_type)
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "collect_preview_state", exc)
                params = {}
            if current_type == OpType.ABSPANEN:
                contour_name = handler._current_parting_contour_name()
                params["contour_name"] = contour_name
                params["source_path"] = handler._resolve_contour_path(contour_name)
            preview_builder = {
                OpType.FACE: build_face_path,
                OpType.THREAD: build_thread_path,
                OpType.GROOVE: build_groove_preview_path,
                OpType.DRILL: build_drill_path,
                OpType.KEYWAY: build_keyway_path,
                OpType.ABSPANEN: build_abspanen_path,
            }.get(current_type)
            if preview_builder:
                try:
                    draft_path = preview_builder(params)
                except Exception as exc:
                    _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "collect_preview_state", exc)
                    draft_path = []
                if draft_path:
                    paths.append(draft_path)
                    active = len(paths) - 1
                    active_operation = Operation(current_type, params, draft_path)

    # A thread relief belongs to the finished component geometry, not to the
    # currently selected Abspanen form.  Add it once for every linked contour
    # so the complete program preview remains truthful while another step
    # (for example the thread itself) is selected.
    if handler.model.operations:
        contours = {
            str((op.params or {}).get("name") or "").strip(): op
            for op in handler.model.operations
            if op.op_type == OpType.CONTOUR and isinstance(op.params, dict)
        }
        rendered_reliefs = set()
        for parting_op in handler.model.operations:
            if parting_op.op_type != OpType.ABSPANEN:
                continue
            parting_params = dict(parting_op.params or {})
            contour_name = str(parting_params.get("contour_name") or "").strip()
            contour_op = contours.get(contour_name)
            if contour_op is None or not contour_op.params.get("segments"):
                continue
            side_internal = str(parting_params.get("side", 0)).strip().lower() in ("1", "inside", "internal", "innen", "id")
            key = (contour_name, side_internal)
            if key in rendered_reliefs:
                continue
            contour_params = dict(contour_op.params)
            reliefs = []
            for thread_op in handler.model.operations:
                if thread_op.op_type != OpType.THREAD:
                    continue
                try:
                    relief = thread_relief_spec(thread_op.params)
                except ValueError:
                    continue
                if relief is not None and bool(relief.get("internal")) == side_internal:
                    selected = select_thread_relief_for_contour(contour_params, relief)
                    if selected is not None:
                        reliefs.append(selected)
            if not reliefs:
                continue
            contour_params["auto_thread_reliefs"] = reliefs
            variants = build_contour_variants(contour_params)
            if variants.get("feature_primitives"):
                paths.append([dict(pr, role="feature") for pr in variants["feature_primitives"]])
                rendered_reliefs.add(key)

    prog = handler._collect_program_header() or {}
    prog["__operations"] = list(handler.model.operations)
    try:
        prog["__warnings"] = (
            get_machine_limit_warnings(prog)
            + validate_program_setup(handler.model.operations, {**prog, "tools": getattr(handler, "tools", {})})
            + [detail["message"] for detail in handler._radius_warning_details()]
        )
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "collect_preview_state", exc)
        prog["__warnings"] = []
    try:
        inserts = 0
        stock_primitives = build_stock_outline(prog)
        if stock_primitives:
            paths.insert(0, stock_primitives)
            inserts += 1

        retract_primitives = build_retract_primitives(prog)
        if retract_primitives:
            paths.insert(inserts, retract_primitives)
            inserts += 1

        worklimit_primitives = build_worklimit_primitives(prog, stock_primitives or [])
        if worklimit_primitives:
            paths.insert(inserts, worklimit_primitives)
            inserts += 1

        chuck_nogo_primitives = build_chuck_nogo_primitives(prog)
        if chuck_nogo_primitives:
            paths.insert(inserts, chuck_nogo_primitives)
            inserts += 1

        if active >= 0 and inserts:
            active += inserts
    except Exception as exc:
        handler._log("[LatheEasyStep] stock/retract preview ERROR:", exc, level="error")

    if active_operation and active_operation.op_type == OpType.ABSPANEN:
        params = dict(active_operation.params or {})
        contour_name = str(params.get("contour_name") or "").strip()
        contour_op = next(
            (
                op
                for op in handler.model.operations
                if op.op_type == OpType.CONTOUR and str((op.params or {}).get("name") or "").strip() == contour_name
            ),
            None,
        )
        if contour_op is not None and isinstance(contour_op.params, dict) and contour_op.params.get("segments"):
            contour_params = dict(contour_op.params)
            side_internal = str(params.get("side", 0)).strip().lower() in ("1", "inside", "internal", "innen", "id")
            reliefs = []
            for op in handler.model.operations:
                if op.op_type != OpType.THREAD:
                    continue
                try:
                    relief = thread_relief_spec(op.params)
                except ValueError:
                    continue
                if relief is not None and bool(relief.get("internal")) == side_internal:
                    selected = select_thread_relief_for_contour(contour_params, relief)
                    if selected is not None:
                        reliefs.append(selected)
            if reliefs:
                contour_params["auto_thread_reliefs"] = reliefs
            variants = build_contour_variants(contour_params)
            relief_mode = normalize_relief_mode(params.get("undercut_mode"))
            if variants.get("rough_primitives") and relief_mode in ("ignore", "finish_only", "separate"):
                paths.append([dict(pr, role="contour_rough") for pr in variants["rough_primitives"]])
            # The feature itself was already added above as part geometry.
            # This branch only adds the optional roughing representation.

    return paths, active, prog, active_operation


def apply_preview_paths(
    handler,
    paths,
    *,
    active_index: int | None = None,
    include_contour_preview: bool = True,
    program_context: Dict[str, object] | None = None,
    active_operation: Operation | None = None,
) -> None:
    PreviewView(handler).apply_paths(
        paths,
        active_index=active_index,
        include_contour_preview=include_contour_preview,
        program_context=program_context,
        active_operation=active_operation,
        collision=_detect_preview_collision(paths),
    )


def collect_preview_scene(handler, **builders) -> tuple[PreviewScene, dict, Operation | None]:
    """Build a semantically layered scene while retaining legacy builders."""
    paths, active, program_context, active_operation = collect_preview_state(
        handler, **builders
    )
    scene = scene_from_legacy_paths(
        paths,
        active,
        getattr(handler.model, "operations", ()),
        active_operation,
    )
    return scene, program_context, active_operation


def on_toggle_slice_view(handler, checked: bool) -> None:
    if handler.preview is None:
        handler._log("[LatheEasyStep] _on_toggle_slice_view ignored: preview is None", level="warning")
        return
    checked = bool(checked)
    handler._log(
        f"[LatheEasyStep] _on_toggle_slice_view checked={checked} "
        f"current_mode={getattr(handler.preview, 'view_mode', None)} "
        f"slice_enabled={getattr(handler.preview, 'slice_enabled', None)}",
        level="info",
    )
    # LES-044: (RuntimeError, AttributeError) - Qt-Widget-Methodenaufrufe auf
    # handler.preview/preview_slice/btn_slice_view, deren Lebensdauer nicht
    # garantiert ist (siehe Begruendung in setup_slice_view() oben).
    try:
        handler.preview.set_slice_enabled(checked)
    except (RuntimeError, AttributeError):
        handler._log("[LatheEasyStep] set_slice_enabled failed", level="warning")
    try:
        handler.preview.set_view_mode("side")
    except (RuntimeError, AttributeError):
        handler._log("[LatheEasyStep] set_view_mode failed", level="warning")
    if handler.preview_slice is not None:
        try:
            handler.preview_slice.setVisible(checked)
        except (RuntimeError, AttributeError):
            handler._log("[LatheEasyStep] preview_slice visibility change failed", level="warning")
    if handler.btn_slice_view is not None:
        try:
            update_slice_view_button(handler, checked)
        except (RuntimeError, AttributeError):
            handler._log("[LatheEasyStep] btn_slice_view text update failed", level="warning")
    if checked:
        try:
            # _suggest_slice_z_for_preview() -> default_slice_z_for_operation()
            # faengt ihre eigenen Umrechnungsfehler bereits intern ab.
            suggested = handler._suggest_slice_z_for_preview()
            handler.preview.set_slice_z(0.0 if suggested is None else suggested, emit=True)
        except (RuntimeError, AttributeError):
            handler._log("[LatheEasyStep] set_slice_z failed", level="warning")
    handler._log(
        f"[LatheEasyStep] slice view updated: mode={getattr(handler.preview, 'view_mode', None)} "
        f"slice_enabled={getattr(handler.preview, 'slice_enabled', None)} "
        f"slice_z={getattr(handler.preview, 'slice_z', None)} "
        f"slice_widget_visible={getattr(handler.preview_slice, 'isVisible', lambda: None)() if handler.preview_slice else None}",
        level="info",
    )
    handler._sync_slice_widget()


def sync_slice_widget(handler) -> None:
    if handler.preview is None or handler.preview_slice is None:
        return
    # LES-044: (RuntimeError, AttributeError) fuer die Qt-Widget-Aufrufe
    # unten - siehe Begruendung in setup_slice_view() oben; das Debug-Log
    # zwischendrin bekommt zusaetzlich TypeError (Formatierungs-/len()-
    # Fehler bei unerwarteten Attributwerten statt einem Qt-Aufruf).
    visible = None
    try:
        visible = bool(handler.preview_slice.isVisible())
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        visible = None
    try:
        handler._log(
            f"[LatheEasyStep][debug] sync_slice_widget: visible={visible} "
            f"slice_z={getattr(handler.preview, 'slice_z', None)!r} "
            f"paths={len(getattr(handler.preview, 'paths', []) or [])} "
            f"active_index={getattr(handler.preview, 'active_index', None)!r}",
            level="debug",
        )
    except (RuntimeError, TypeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass
    try:
        handler.preview_slice.set_slice_z(getattr(handler.preview, "slice_z", 0.0))
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass
    try:
        handler.preview_slice.set_view_mode("front")
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass
    try:
        handler.preview_slice.set_paths(getattr(handler.preview, "paths", []), getattr(handler.preview, "active_index", None))
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass
    try:
        handler.preview_slice.set_front_context(
            getattr(handler.preview, "front_program", {}),
            getattr(handler.preview, "front_operation", None),
        )
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass
    try:
        handler.preview_slice.update()
    except (RuntimeError, AttributeError) as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "sync_slice_widget", exc)
        pass


def refresh_preview(
    handler,
    *,
    build_contour_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_face_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_thread_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_groove_preview_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_drill_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_keyway_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_abspanen_path: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_stock_outline: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_retract_primitives: Callable[[Dict[str, object]], List[Tuple[float, float]]],
    build_worklimit_primitives: Callable[[Dict[str, object], List[Tuple[float, float]]], List[Tuple[float, float]]],
    build_chuck_nogo_primitives: Callable[[Dict[str, object]], List[Tuple[float, float]]],
) -> None:
    if handler.preview is None or handler.contour_preview is None:
        handler._ensure_preview_widgets()
    if handler.preview is None and handler.contour_preview is None:
        return
    scene, prog, active_operation = collect_preview_scene(
        handler,
        build_contour_path=build_contour_path,
        build_face_path=build_face_path,
        build_thread_path=build_thread_path,
        build_groove_preview_path=build_groove_preview_path,
        build_drill_path=build_drill_path,
        build_keyway_path=build_keyway_path,
        build_abspanen_path=build_abspanen_path,
        build_stock_outline=build_stock_outline,
        build_retract_primitives=build_retract_primitives,
        build_worklimit_primitives=build_worklimit_primitives,
        build_chuck_nogo_primitives=build_chuck_nogo_primitives,
    )
    PreviewView(handler).apply_scene(
        scene,
        include_contour_preview=True,
        program_context=prog,
        active_operation=active_operation,
        collision=_detect_preview_collision(scene.paths),
    )


def _detect_preview_collision(paths) -> bool:
    try:
        zb = None
        for prim_list in paths:
            for pr in prim_list:
                if pr.get("role") == "worklimit" and pr.get("type") == "line":
                    zb = float(pr.get("p1", (0.0, 0.0))[1])
                    break
            if zb is not None:
                break
        if zb is None:
            return False

        min_z = None
        for prim_list in paths:
            for pr in prim_list:
                role = pr.get("role")
                if role in ("stock", "retract", "worklimit", "chuck_nogo"):
                    continue
                prim_type = pr.get("type")
                if prim_type == "polyline":
                    for _, z in pr.get("points", []):
                        if min_z is None or z < min_z:
                            min_z = z
                elif prim_type == "line":
                    for _, z in (pr.get("p1"), pr.get("p2")):
                        if min_z is None or z < min_z:
                            min_z = z
        return min_z is not None and min_z < zb - 1e-6
    except Exception as exc:
        _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "_detect_preview_collision", exc)
        return False
