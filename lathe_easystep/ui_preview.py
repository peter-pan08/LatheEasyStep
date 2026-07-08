from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .model import OpType, Operation


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
    handler._ensure_preview_widgets()

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
