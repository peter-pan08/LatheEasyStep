from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .model import OpType, Operation


def setup_slice_view(handler) -> None:
    if getattr(handler, "_slice_view_setup_done", False):
        return
    handler._slice_view_setup_done = True

    if handler.preview is None:
        try:
            handler.preview = handler._get_widget_by_name("previewWidget")
        except Exception:
            pass
    if handler.preview_slice is None:
        try:
            handler.preview_slice = handler._get_widget_by_name("previewSliceWidget")
        except Exception:
            pass
    if handler.btn_slice_view is None:
        try:
            handler.btn_slice_view = handler._get_widget_by_name("btn_slice_view")
        except Exception:
            pass

    handler._log(
        f"[LatheEasyStep] _setup_slice_view: preview={handler.preview!r} "
        f"preview_slice={handler.preview_slice!r} btn_slice_view={handler.btn_slice_view!r}",
        level="info",
    )

    if handler.preview is not None:
        try:
            handler.preview.set_view_mode("side")
        except Exception:
            pass

    if handler.preview_slice is not None:
        try:
            handler.preview_slice.set_view_mode("front")
            handler.preview_slice.setVisible(False)
        except Exception:
            pass

    if handler.btn_slice_view is not None:
        try:
            handler.btn_slice_view.setChecked(False)
            handler.btn_slice_view.setText("Schnittansicht")
            handler.btn_slice_view.setToolTip(
                "Blendet zusaetzlich zur Seitenansicht eine Schnittansicht ein. "
                "In der Seitenansicht kann die Schnittlinie mit der Maus verschoben werden."
            )
            handler.btn_slice_view.toggled.connect(handler._on_toggle_slice_view)
            handler._log("[LatheEasyStep] slice toggle connected", level="info")
        except Exception:
            handler._log("[LatheEasyStep] slice toggle connect failed", level="warning")
    else:
        handler._log("[LatheEasyStep] btn_slice_view not found during setup", level="warning")

    if handler.preview is not None:
        try:
            handler.preview.sliceChanged.connect(handler._on_slice_changed)
        except Exception:
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
        selected_row = handler.list_ops.currentRow() if handler.list_ops else -1
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
        except Exception:
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
            except Exception:
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
                except Exception:
                    draft_path = []
                if draft_path:
                    paths.append(draft_path)
                    active = len(paths) - 1
                    active_operation = Operation(current_type, params, draft_path)

    prog = handler._collect_program_header() or {}
    prog["__operations"] = list(handler.model.operations)
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
    if handler.preview:
        collision = _detect_preview_collision(paths)
        try:
            if hasattr(handler.preview, "set_collision"):
                handler.preview.set_collision(collision)
            handler.preview.set_paths(paths, active_index)
        except TypeError:
            handler.preview.set_paths(paths)
        try:
            handler.preview.set_front_context(program_context, active_operation)
        except Exception:
            pass
        try:
            if getattr(handler.preview, "slice_enabled", False):
                handler._ensure_slice_z_matches_operation(active_operation)
        except Exception:
            pass

    if handler.preview_slice and getattr(handler.preview_slice, "isVisible", lambda: False)():
        try:
            handler.preview_slice.set_view_mode("front")
        except Exception:
            pass
        try:
            if handler.preview:
                handler.preview_slice.set_slice_z(getattr(handler.preview, "slice_z", 0.0))
            else:
                handler.preview_slice.set_slice_z(0.0)
        except Exception:
            pass
        try:
            handler.preview_slice.set_paths(paths, active_index)
        except TypeError:
            handler.preview_slice.set_paths(paths)
        try:
            handler.preview_slice.set_front_context(program_context, active_operation)
        except Exception:
            pass

    if include_contour_preview and handler.contour_preview:
        try:
            handler.contour_preview.set_paths(paths, active_index)
        except TypeError:
            handler.contour_preview.set_paths(paths)


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
    try:
        handler.preview.set_slice_enabled(checked)
    except Exception:
        handler._log("[LatheEasyStep] set_slice_enabled failed", level="warning")
    try:
        handler.preview.set_view_mode("side")
    except Exception:
        handler._log("[LatheEasyStep] set_view_mode failed", level="warning")
    if handler.preview_slice is not None:
        try:
            handler.preview_slice.setVisible(checked)
        except Exception:
            handler._log("[LatheEasyStep] preview_slice visibility change failed", level="warning")
    if handler.btn_slice_view is not None:
        try:
            handler.btn_slice_view.setText("Schnittansicht aus" if checked else "Schnittansicht")
        except Exception:
            handler._log("[LatheEasyStep] btn_slice_view text update failed", level="warning")
    if checked:
        try:
            suggested = handler._suggest_slice_z_for_preview()
            handler.preview.set_slice_z(0.0 if suggested is None else suggested, emit=True)
        except Exception:
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
    try:
        if not handler.preview_slice.isVisible():
            return
    except Exception:
        return
    try:
        handler.preview_slice.set_slice_z(getattr(handler.preview, "slice_z", 0.0))
    except Exception:
        pass
    try:
        handler.preview_slice.set_view_mode("front")
    except Exception:
        pass
    try:
        handler.preview_slice.set_paths(getattr(handler.preview, "paths", []), getattr(handler.preview, "active_index", None))
    except Exception:
        pass
    try:
        handler.preview_slice.set_front_context(
            getattr(handler.preview, "front_program", {}),
            getattr(handler.preview, "front_operation", None),
        )
    except Exception:
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
    paths, active, prog, active_operation = collect_preview_state(
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
    handler._set_preview_paths(
        paths,
        active,
        include_contour_preview=True,
        program_context=prog,
        active_operation=active_operation,
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
    except Exception:
        return False
