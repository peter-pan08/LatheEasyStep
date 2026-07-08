from __future__ import annotations

from typing import Dict, List, Tuple

from .model import OpType, Operation


def operation_to_step_data(op: Operation) -> Dict[str, object]:
    data = {
        "op_type": op.op_type,
        "params": dict(op.params or {}),
    }
    if op.path and isinstance(op.path[0], dict):
        data["primitives"] = op.path
    else:
        data["path"] = [[float(x), float(z)] for x, z in (op.path or [])]
    return data


def step_data_to_operation(data: Dict[str, object]) -> Operation | None:
    if not isinstance(data, dict):
        return None
    op_type = str(data.get("op_type") or OpType.FACE)
    params_raw = data.get("params") or {}
    if not isinstance(params_raw, dict):
        params_raw = {}
    params = {str(key): value for key, value in params_raw.items()}

    if isinstance(data.get("primitives"), list) and data.get("primitives"):
        prim = data.get("primitives") or []
        return Operation(op_type, params, list(prim))

    path_data = data.get("path") or []
    path: List[Tuple[float, float]] = []
    for entry in path_data:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            try:
                x = float(entry[0])
                z = float(entry[1])
            except Exception:
                continue
            path.append((x, z))
    return Operation(op_type, params, path)


def build_program_data(
    operations: List[Operation],
    header: Dict[str, object],
    meta: Dict[str, object],
) -> Dict[str, object]:
    ops_data = []
    for op in operations:
        op_dict = operation_to_step_data(op)
        op_dict["title"] = op.params.get("title", "")
        ops_data.append(op_dict)
    return {
        "version": 1,
        "header": header,
        "operations": ops_data,
        "meta": meta,
    }
