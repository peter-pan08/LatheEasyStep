from __future__ import annotations

from typing import Dict, List, Tuple

from .model import OpType, Operation
from .numeric import finite_float, validate_finite_data
from .comments import is_generated_comment, unnumbered_comment


def operation_to_step_data(op: Operation) -> Dict[str, object]:
    data = {
        "op_type": op.op_type,
        "params": dict(op.params or {}),
    }
    if data["params"].get("_auto_comment") or is_generated_comment(data["params"].get("comment")):
        if data["params"].get("comment"):
            data["params"]["comment"] = unnumbered_comment(data["params"]["comment"])
            data["params"]["_auto_comment"] = True
    if op.path and isinstance(op.path[0], dict):
        data["primitives"] = op.path
    else:
        data["path"] = [[float(x), float(z)] for x, z in (op.path or [])]
    return data


def step_data_to_operation(data: Dict[str, object]) -> Operation | None:
    if not isinstance(data, dict):
        return None
    validate_finite_data(data, "Step")
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
    if not isinstance(path_data, (list, tuple)):
        raise ValueError("Step.path muss eine Liste von X/Z-Punkten sein.")
    for index, entry in enumerate(path_data):
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError(f"Step.path[{index}]: X/Z-Punkt erforderlich.")
        path.append((finite_float(entry[0], f"Step.path[{index}].X"),
                     finite_float(entry[1], f"Step.path[{index}].Z")))
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
