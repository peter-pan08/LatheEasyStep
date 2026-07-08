from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

from .model import OpType, Operation

STEP_FILE_PATH_KEY = "__step_file_path"
PROGRAM_FILE_PATH_KEY = "__program_file_path"
GCODE_FILE_PATH_KEY = "__gcode_file_path"


def normalized_file_path(file_path: str | None) -> str | None:
    if not file_path:
        return None
    try:
        return os.path.abspath(os.path.expanduser(str(file_path)))
    except Exception:
        return str(file_path)


def step_file_path(op: Operation) -> str | None:
    params = getattr(op, "params", {}) or {}
    return normalized_file_path(params.get(STEP_FILE_PATH_KEY))


def set_step_file_path(op: Operation, file_path: str) -> None:
    op.params[STEP_FILE_PATH_KEY] = normalized_file_path(file_path)


def step_filename_stem(op: Operation, index_hint: int | None = None) -> str:
    params = getattr(op, "params", {}) or {}
    base = str(params.get("name") or params.get("contour_name") or op.op_type or "step").strip()
    if not base:
        base = "step"
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._") or "step"
    if index_hint is not None:
        return f"{index_hint:02d}_{base}"
    return base


def program_file_meta(
    operations: List[Operation],
    current_program_path: str | None,
    current_gcode_path: str | None,
) -> Dict[str, object]:
    meta: Dict[str, object] = {}
    program_path = normalized_file_path(current_program_path)
    gcode_path = normalized_file_path(current_gcode_path)
    if program_path:
        meta[PROGRAM_FILE_PATH_KEY] = program_path
    if gcode_path:
        meta[GCODE_FILE_PATH_KEY] = gcode_path
    step_files = []
    for idx, op in enumerate(operations or []):
        if getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
            continue
        step_files.append(
            {
                "index": idx,
                "op_type": getattr(op, "op_type", ""),
                "path": step_file_path(op),
            }
        )
    if step_files:
        meta["step_files"] = step_files
    return meta


def parse_program_payload(
    program_data: Dict[str, object],
    file_path: str,
    *,
    expected_version: int = 1,
) -> Tuple[Dict[str, object], List[Dict[str, object]], str | None, str | None]:
    if program_data.get("version") != expected_version:
        raise ValueError("Ungültiges Dateiformat oder nicht unterstützte Version.")
    header = program_data.get("header", {})
    if not isinstance(header, dict):
        header = {}
    meta = program_data.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    operations = program_data.get("operations", [])
    if not isinstance(operations, list):
        operations = []
    program_path = normalized_file_path(meta.get(PROGRAM_FILE_PATH_KEY) or file_path)
    gcode_path = normalized_file_path(meta.get(GCODE_FILE_PATH_KEY))
    return header, operations, program_path, gcode_path
