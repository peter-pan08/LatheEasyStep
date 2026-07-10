from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .checks import validate_program_setup
from .gcode_drill import generate_drill_gcode
from .gcode_face import generate_face_gcode
from .gcode_groove import generate_groove_gcode, groove_sub_definition
from .gcode_keyway import generate_keyway_gcode
from .gcode_roughing import (
    contour_sub_from_points,
    contour_sub_from_primitives,
    generate_abspanen_gcode,
    step_line_pause_sub_definition,
    step_x_pause_sub_definition,
)
from .gcode_safety import (
    append_tool_and_spindle,
    emit_approach,
    emit_safe_retract_for_op,
    estimate_operation_end_pos,
    get_end_park_lines,
    get_machine_limit_warnings,
)
from .gcode_thread import generate_thread_gcode
from .gcode_utils import (
    REQUIRED_KEYS,
    clean_path,
    emit_coolant,
    float_or_none,
    get_tool_number,
    primitives_to_points,
    require,
    require_positive,
    require_tool,
    sanitize_comment_text,
)
from .model import OpType, Operation


def gcode_from_path(path, feed: float, safe_z: float) -> List[str]:
    lines: List[str] = []
    if not path:
        return lines
    x0, z0 = path[0]
    lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
    if len(path) > 1:
        lines.append(f"G1 Z{z0:.3f} F{feed:.3f}")
    for x, z in path[1:]:
        lines.append(f"G1 X{x:.3f} Z{z:.3f}")
    return lines


def gcode_for_turn(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    settings = settings or {}
    p = op.params
    require_tool(p, "TURN")
    path = op.path or []
    if not path:
        return []
    feed = float(p.get("feed", 0.2))
    safe_z = float(p.get("safe_z", 2.0))
    lines: List[str] = []
    append_tool_and_spindle(lines, get_tool_number(p), p.get("spindle"), settings)
    if bool(p.get("coolant", False)):
        lines.append("M8")
    lines.extend(gcode_from_path(path, feed, safe_z))
    return lines


def gcode_for_bore(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    settings = settings or {}
    p = op.params
    require_tool(p, "BORE")
    path = op.path or []
    if not path:
        return []
    feed = float(p.get("feed", 0.15))
    safe_z = float(p.get("safe_z", 2.0))
    lines: List[str] = []
    append_tool_and_spindle(lines, get_tool_number(p), p.get("spindle"), settings)
    if bool(p.get("coolant", False)):
        lines.append("M8")
    lines.extend(gcode_from_path(path, feed, safe_z))
    return lines


def gcode_for_drill(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_drill_gcode(
        op,
        settings,
        require=require,
        require_tool=require_tool,
        get_tool_number=get_tool_number,
        append_tool_and_spindle=append_tool_and_spindle,
        emit_coolant=emit_coolant,
        emit_approach=emit_approach,
    )


def gcode_for_groove(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_groove_gcode(
        op,
        settings,
        require_tool=require_tool,
        get_tool_number=get_tool_number,
        append_tool_and_spindle=append_tool_and_spindle,
        emit_coolant=emit_coolant,
    )


def gcode_for_keyway(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_keyway_gcode(op, settings, require=require, require_positive=require_positive)


def gcode_for_face(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_face_gcode(
        op,
        settings,
        require_tool=require_tool,
        append_tool_and_spindle=append_tool_and_spindle,
        emit_coolant=emit_coolant,
        emit_approach=emit_approach,
        clean_path=clean_path,
    )


def gcode_for_thread(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    return generate_thread_gcode(
        op,
        settings,
        require_tool=require_tool,
        get_tool_number=get_tool_number,
        append_tool_and_spindle=append_tool_and_spindle,
        emit_coolant=emit_coolant,
        emit_approach=emit_approach,
        sanitize_comment_text=sanitize_comment_text,
    )


def gcode_for_operation(op: Operation, settings: Dict[str, object] | None = None) -> List[str]:
    settings = settings or {}
    if op.op_type == OpType.PROGRAM_HEADER:
        result: List[str] = []
    elif op.op_type == OpType.FACE:
        result = gcode_for_face(op, settings)
    elif op.op_type == OpType.CONTOUR:
        result = []
    elif op.op_type == OpType.TURN:
        result = gcode_for_turn(op, settings)
    elif op.op_type == OpType.BORE:
        result = gcode_for_bore(op, settings)
    elif op.op_type == OpType.DRILL:
        result = gcode_for_drill(op, settings)
    elif op.op_type == OpType.GROOVE:
        result = gcode_for_groove(op, settings)
    elif op.op_type == OpType.ABSPANEN:
        result = generate_abspanen_gcode(op.params, op.path, settings)
    elif op.op_type == OpType.THREAD:
        result = gcode_for_thread(op, settings)
    elif op.op_type == OpType.KEYWAY:
        result = gcode_for_keyway(op, settings)
    else:
        result = []
    comment = sanitize_comment_text(op.params.get("comment") or "").strip()
    if comment:
        result.insert(0, f"(STEP: {comment})")
    return result


def generate_program_gcode(operations: List[Operation], program_settings: Dict[str, object]) -> List[str]:
    settings = dict(program_settings or {})
    validation_warnings = validate_program_setup(operations, settings)
    for i, op in enumerate(operations):
        if op.op_type in REQUIRED_KEYS:
            require(op.params, REQUIRED_KEYS[op.op_type], op.op_type)
            if op.op_type in [OpType.FACE, OpType.ABSPANEN, OpType.KEYWAY, OpType.DRILL]:
                require_positive(op.params, REQUIRED_KEYS[op.op_type], op.op_type)
        try:
            gcode_for_operation(op, settings)
        except ValueError as e:
            raise ValueError(f"Operation {i+1} ({op.op_type}): {str(e)}") from e

    class SubAllocator:
        def __init__(self, start: int = 100):
            self.next_id = start

        def allocate(self) -> int:
            result = self.next_id
            self.next_id += 1
            return result

    settings["sub_allocator"] = SubAllocator()
    program_name = sanitize_comment_text(settings.get("program_name", "Program"))
    unit = sanitize_comment_text(settings.get("unit", "mm"))
    header_lines: List[str] = ["%", "(Programm automatisch erzeugt)", f"(Programmname: {program_name})", f"(Masseinheit: {unit})"]
    handler_header_lines = [str(x) for x in settings.get("header_lines", []) or []]
    footer_lines_from_settings = [str(x) for x in settings.get("footer_lines", []) or []]
    if handler_header_lines:
        settings["_skip_tool_move"] = True
    header_lines.extend(["G18 G7 G90 G40 G80", "G20" if str(unit).strip().lower() in ("inch", "in", "zoll", "imperial") else "G21", "G95", "G54", ""])
    header_lines.append("(=== SICHERHEITSPARAMETER ===)")
    xt = settings.get("xt")
    zt = settings.get("zt")
    toolchange_coords = str(settings.get("toolchange_coords", "") or "").strip().lower()
    if toolchange_coords not in ("work", "machine"):
        xt_abs = settings.get("xt_absolute", True)
        zt_abs = settings.get("zt_absolute", True)
        if bool(xt_abs) != bool(zt_abs):
            toolchange_coords = "mixed"
        else:
            toolchange_coords = "work" if xt_abs and zt_abs else "machine"
    if xt is not None and zt is not None:
        try:
            if toolchange_coords == "machine":
                coord_note = " Maschinenkoordinaten G53"
            elif toolchange_coords == "mixed":
                coord_note = " gemischt legacy"
            else:
                coord_note = " Werkstueckkoordinaten"
            header_lines.append(f"(Werkzeugwechselpunkt: X{float(xt):.3f} Z{float(zt):.3f}{coord_note})")
        except (TypeError, ValueError):
            pass
    xra = settings.get("xra")
    xri = settings.get("xri")
    zra = settings.get("zra")
    zri = settings.get("zri")
    header_lines.append(f"(Rueckzugsebenen: XRA={float(xra):.3f} XRI={float(xri):.3f})" if xra is not None and xri is not None else "(Rueckzugsebenen: XRA=n.def. XRI=n.def.)")
    header_lines.append(f"(               ZRA={float(zra):.3f} ZRI={float(zri):.3f})" if zra is not None and zri is not None else "(               ZRA=n.def. ZRI=n.def.)")
    xa = settings.get("xa")
    za = settings.get("za")
    zi = settings.get("zi")
    if xa is not None:
        try:
            header_lines.append(f"(Rohteil Aussendurchmesser: {float(xa):.3f} mm)")
        except (TypeError, ValueError):
            pass
    if za is not None and zi is not None:
        try:
            header_lines.append(f"(Rohteil Z-Bereich: {float(za):.3f} bis {float(zi):.3f} mm)")
        except (TypeError, ValueError):
            pass
    header_lines.extend(["(=== END SICHERHEITSPARAMETER ===)", ""])
    for warning in get_machine_limit_warnings(settings):
        header_lines.append(f"(WARN: {warning})")
    for warning in validation_warnings:
        header_lines.append(f"(WARN: {warning})")
    header_lines.append("")

    all_subs: List[List[str]] = []

    def _extract_sub_blocks(block_lines: List[str]) -> List[str]:
        out: List[str] = []
        i = 0
        while i < len(block_lines):
            line = block_lines[i].strip()
            m = re.match(r"^o\s*<?\s*(\d+)\s*>?\s+sub\b", line, flags=re.IGNORECASE)
            if m:
                sub_block = [block_lines[i]]
                i += 1
                while i < len(block_lines):
                    sub_block.append(block_lines[i])
                    if re.match(rf"^o\s*<?\s*{re.escape(m.group(1))}\s*>?\s+endsub\b", block_lines[i].strip(), flags=re.IGNORECASE):
                        i += 1
                        break
                    i += 1
                all_subs.append(sub_block)
                continue
            out.append(block_lines[i])
            i += 1
        return out

    contour_subs: Dict[str, int] = {}
    contour_geom_map: Dict[tuple, int] = {}

    def _round6(val: object) -> float:
        try:
            return round(float(val), 6)
        except Exception:
            return 0.0

    def _contour_key_from_primitives(prims: List[Dict[str, object]]) -> tuple:
        key_items: List[tuple] = []
        for pr in prims:
            typ = pr.get("type")
            if typ == "line":
                p1 = pr.get("p1") or (0.0, 0.0)
                p2 = pr.get("p2") or (0.0, 0.0)
                key_items.append(("l", _round6(p1[0]), _round6(p1[1]), _round6(p2[0]), _round6(p2[1])))
            elif typ == "arc":
                p1 = pr.get("p1") or (0.0, 0.0)
                p2 = pr.get("p2") or (0.0, 0.0)
                c = pr.get("c") or pr.get("center") or (0.0, 0.0)
                key_items.append(("a", _round6(p1[0]), _round6(p1[1]), _round6(p2[0]), _round6(p2[1]), _round6(c[0]), _round6(c[1]), bool(pr.get("ccw"))))
        return tuple(key_items)

    def _contour_key_from_points(points: List[Tuple[float, float]]) -> tuple:
        return tuple((_round6(x), _round6(z)) for x, z in points)

    for op in operations:
        if op.op_type != OpType.CONTOUR:
            continue
        name = str(op.params.get("name") or "").strip()
        if not name or not op.path:
            continue
        if isinstance(op.path[0], dict):
            key = ("prims", _contour_key_from_primitives(op.path))
            if key not in contour_geom_map:
                contour_geom_map[key] = settings["sub_allocator"].allocate()
                all_subs.append(contour_sub_from_primitives(op.path, contour_geom_map[key]))
            contour_subs[name] = contour_geom_map[key]
        else:
            key = ("pts", _contour_key_from_points(op.path))
            if key not in contour_geom_map:
                contour_geom_map[key] = settings["sub_allocator"].allocate()
                all_subs.append(contour_sub_from_points(op.path, contour_geom_map[key]))
            contour_subs[name] = contour_geom_map[key]

    settings["contour_subs"] = contour_subs
    helper_subs = settings.get("helper_subs", None)
    if helper_subs:
        for sb in helper_subs:
            all_subs.append([str(x) for x in sb])
    if settings.get("needs_step_line_pause_sub"):
        all_subs.append(step_line_pause_sub_definition())
    if settings.get("needs_step_x_pause_sub"):
        all_subs.append(step_x_pause_sub_definition())
    if any(op.op_type == OpType.GROOVE for op in operations):
        all_subs.append(groove_sub_definition())

    main_flow_lines: List[str] = []
    if handler_header_lines:
        has_tool = any(get_tool_number(op.params) > 0 for op in operations if op.op_type not in (OpType.PROGRAM_HEADER, OpType.CONTOUR))
        if not has_tool:
            main_flow_lines.extend(handler_header_lines)
    first_tool = 0
    for op in operations:
        if op.op_type in (OpType.PROGRAM_HEADER, OpType.CONTOUR):
            continue
        tval = get_tool_number(op.params)
        if tval > 0:
            first_tool = tval
            break
    if first_tool > 0 and int(float(settings.get("_current_tool", 0))) == 0:
        pre_tool_lines: List[str] = []
        append_tool_and_spindle(pre_tool_lines, first_tool, None, settings)
        main_flow_lines.extend(pre_tool_lines)
    main_flow_lines.append("")

    step_num = 0
    for op in operations:
        if op.op_type == OpType.PROGRAM_HEADER:
            continue
        step_num += 1
        op_tool = get_tool_number(op.params)
        if op_tool > 0:
            tool_lines: List[str] = []
            append_tool_and_spindle(tool_lines, op_tool, None, settings)
            if tool_lines:
                main_flow_lines.extend(tool_lines)
        if op.op_type == OpType.ABSPANEN:
            contour_name = op.params.get("contour_name")
            if contour_name:
                contour_op = next((o for o in operations if o.op_type == OpType.CONTOUR and o.params.get("name") == contour_name), None)
                if contour_op and contour_op.path:
                    if isinstance(contour_op.params, dict):
                        op.params["_contour_params"] = dict(contour_op.params)
                    if isinstance(contour_op.path[0], dict):
                        op.params["_primitives"] = contour_op.path
                        op.path = primitives_to_points(contour_op.path)
                    else:
                        op.path = contour_op.path
                else:
                    op.path = []
        main_flow_lines.append("")
        op_title = sanitize_comment_text(op.params.get("title", op.op_type))
        tool_val = get_tool_number(op.params)
        tools = settings.get("tools", {})
        tool_desc = ""
        if tool_val > 0 and tool_val in tools:
            tool_desc = f" | T{tool_val}: {sanitize_comment_text(tools[tool_val].get('comment', ''))}"
        op_lines = _extract_sub_blocks(gcode_for_operation(op, settings))
        if op_lines and any(not line.startswith("(") for line in op_lines):
            main_flow_lines.append(f"(Step {step_num}: {op_title}{tool_desc})")
            main_flow_lines.extend(op_lines)
        elif op_lines and op.op_type != OpType.CONTOUR:
            main_flow_lines.append(f"(Step {step_num}: {op_title}{tool_desc})")
            main_flow_lines.extend(op_lines)
        if op_lines and any(not line.startswith("(") for line in op_lines) and op.op_type not in (OpType.CONTOUR, OpType.PROGRAM_HEADER):
            emit_safe_retract_for_op(main_flow_lines, settings, op.op_type, current_pos=estimate_operation_end_pos(op))

    lines: List[str] = []
    lines.extend(header_lines)
    if all_subs:
        lines.extend(["", "(=== Subroutine Definitions ===)"])
        for sb in all_subs:
            lines.extend(sb)
        lines.extend(["(=== End Subroutines ===)", ""])
    lines.extend(main_flow_lines)
    if not footer_lines_from_settings:
        lines.append("")
        lines.extend(get_end_park_lines(settings))
    lines.append("")
    lines.extend(footer_lines_from_settings)
    lines.extend(["M5", "M9", "M30", "%"])
    return lines


__all__ = ["gcode_for_operation", "generate_program_gcode"]
