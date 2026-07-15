from __future__ import annotations

import math
import os
import re

from qtpy import QtCore, QtGui

from .gcode_utils import is_internal_side


def tool_combo_label(_handler, tool, max_comment: int = 32) -> str:
    comment = (tool.comment or "").strip() or "kein Kommentar"
    if len(comment) > max_comment:
        comment = comment[: max_comment - 1].rstrip() + "…"
    diameter = f"{tool.d:.2f}".rstrip("0").rstrip(".")
    diameter = diameter if diameter else "0"
    return f"T{tool.t:02d} – {comment} ({diameter} mm)"


def operation_side_hint(_handler, op):
    params = op.params or {}
    if op.op_type == _handler.OpType.FACE:
        raw = params.get("finish_direction", 0)
        if isinstance(raw, str):
            idx = 1 if raw.strip().lower() == "inside_out" else 0
        else:
            try:
                idx = int(float(raw))
            except Exception:
                idx = 0
        return "outside" if idx == 0 else "inside"
    if op.op_type == _handler.OpType.GROOVE:
        try:
            idx = int(float(params.get("lage", 0)))
        except Exception:
            idx = 0
        if idx == 0:
            return "outside"
        if idx == 1:
            return "inside"
    if op.op_type == _handler.OpType.ABSPANEN:
        return "inside" if is_internal_side(params.get("side", 0)) else "outside"
    if op.op_type == _handler.OpType.THREAD:
        return "inside" if is_internal_side(params.get("orientation", 0)) else "outside"
    return None


def tool_comment_side_hint(_handler, comment: str):
    if not comment:
        return None
    normalized = re.sub(r"[^a-z0-9]+", " ", comment.lower())
    words = normalized.split()
    inside_words = {"innen", "inside", "inner", "id"}
    outside_words = {"außen", "aussen", "outside", "outer", "od"}
    if any(word in inside_words for word in words):
        return "inside"
    if any(word in outside_words for word in words):
        return "outside"
    return None


def tool_orientation_mismatch(handler, op):
    hint = handler._operation_side_hint(op)
    if not hint:
        return None
    try:
        tool_num = int(float(op.params.get("tool", 0)))
    except Exception:
        tool_num = 0
    if tool_num <= 0:
        return None
    tool = handler.tools.get(tool_num)
    if not tool:
        return None
    comment_hint = handler._tool_comment_side_hint(tool.comment)
    if comment_hint and comment_hint != hint:
        detail = tool.comment or tool.iso_code or ""
        if detail:
            detail = f" ({detail})"
        return f"Tool T{tool.toolno:02d} scheint für {comment_hint} zu sein, die Operation wirkt aber wie {hint}{detail}."
    return None


def collect_tool_orientation_warnings(handler):
    warnings = []
    for idx, op in enumerate(handler.model.operations):
        message = handler._tool_orientation_mismatch(op)
        if message:
            warnings.append(f"Schritt {idx+1}: {message}")
    return warnings


def radius_warning_details(handler):
    details = []
    for idx, op in enumerate(handler.model.operations):
        if op.op_type != handler.OpType.ABSPANEN:
            continue
        tool_value = op.params.get("tool")
        try:
            tool_num = int(float(tool_value)) if tool_value is not None else 0
        except Exception:
            tool_num = 0
        if tool_num <= 0:
            continue
        tool = handler.tools.get(tool_num)
        radius = tool.radius_mm if tool else 0.0
        if radius <= 0.0:
            comment = tool.comment if tool and tool.comment else "kein Kommentar"
            message = f"Step {idx+1}: Tool T{tool_num:02d} ({comment}) hat keinen bekannten Radius → Kompensation (G41.1/G42.1) wird deaktiviert."
            details.append({"idx": idx, "op": op, "tool_num": tool_num, "message": message})
    return details


def build_program_filepath(_handler, name_raw):
    base = (name_raw or "").strip() or "conv_lathe"
    base = base.replace(" ", "_")
    base = re.sub(r"[^A-Za-z0-9_\-]", "", base) or "conv_lathe"
    filename = base if base.lower().endswith(".ngc") else f"{base}.ngc"
    return os.path.expanduser(os.path.join("~/linuxcnc/nc_files", filename))


def infer_insert_shape_key(handler, tool) -> str:
    iso = (tool.iso_code or "").upper().strip()
    if iso and iso[0] in handler._INSERT_SHAPE_KEYS:
        return iso[0]
    comment = (tool.comment or "").upper()
    if not comment:
        return ""
    token_pattern = re.compile(r"\b([A-Z][A-Z0-9]{2,})\b")
    for match in token_pattern.finditer(comment):
        token = match.group(1)
        if token and token[0] in handler._INSERT_SHAPE_KEYS:
            return token[0]
    return ""


def infer_insert_profile(handler, tool):
    comment = (tool.comment or "")
    text = comment.upper()
    shape_key = handler._infer_insert_shape_key(tool)
    family = "turning"
    handed = "neutral"
    groove_width_mm = 0.0
    if re.search(r"\b(E|I)R\d+\b", text) or "GEWINDE" in text or "AG60" in text or "MMT" in text:
        family = "thread"
        if re.search(r"\bIR\d+\b", text) or "INNEN" in text:
            handed = "internal"
        elif re.search(r"\bER\d+\b", text) or "AUSSEN" in text or "AUßEN" in text:
            handed = "external"
        if not shape_key:
            shape_key = "V"
    elif re.search(r"\b(MGMN|MRMN)\d+\b", text) or "EINSTECH" in text or "ABSTECH" in text:
        family = "groove"
        if "INNEN" in text:
            handed = "internal"
        elif "AUSSEN" in text or "AUßEN" in text:
            handed = "external"
        match = re.search(r"\b(?:MGMN|MRMN)(\d{3})\b", text)
        if match:
            try:
                groove_width_mm = int(match.group(1)) / 100.0
            except Exception:
                groove_width_mm = 0.0
        if not shape_key:
            shape_key = "S"
    elif "ER" in text and ("AUFNAHME" in text or "COLLET" in text or "SPAN" in text):
        family = "holder"
        handed = "neutral"
        if not shape_key:
            shape_key = ""
    return {"shape_key": shape_key, "family": family, "handed": handed, "groove_width_mm": groove_width_mm}


def build_insert_geometry(handler, shape_key, insert_size, family="turning", handed="neutral", groove_width_mm=0.0):
    key = (shape_key or "").upper().strip()
    if family == "holder":
        drill_len = insert_size * 1.6
        drill_half = insert_size * 0.12
        poly = QtGui.QPolygonF([QtCore.QPointF(drill_len, 0.0), QtCore.QPointF(-insert_size * 0.2, drill_half), QtCore.QPointF(-insert_size * 0.2, -drill_half)])
        return poly, 0.0
    if family == "thread":
        tip_angle = 60.0
        tip_x = insert_size * 0.95
        rear_x = insert_size * 0.55
        half_h = (tip_x + rear_x) * math.tan(math.radians(tip_angle) * 0.5)
        half_h = min(half_h, insert_size * 0.95)
        poly = QtGui.QPolygonF([QtCore.QPointF(tip_x, 0.0), QtCore.QPointF(-rear_x, half_h), QtCore.QPointF(-rear_x, -half_h)])
        return poly, 0.0
    if family == "groove":
        blade_h = max(insert_size * 0.16, min(insert_size * 0.55, insert_size * (groove_width_mm / 3.0) * 0.5)) if groove_width_mm > 0 else insert_size * 0.28
        blade_tip = insert_size * 0.95
        blade_back = insert_size * 0.9
        direction = -1.0 if handed == "internal" else 1.0
        poly = QtGui.QPolygonF([
            QtCore.QPointF(direction * blade_tip, -blade_h),
            QtCore.QPointF(-direction * blade_back, -blade_h),
            QtCore.QPointF(-direction * blade_back, blade_h),
            QtCore.QPointF(direction * blade_tip, blade_h),
        ])
        return poly, 0.0
    if key == "R":
        return None, insert_size * 0.56
    if key in ("C", "D", "V", "S"):
        angle_map = {"C": 80.0, "D": 55.0, "V": 35.0, "S": 90.0}
        corner_angle = angle_map[key]
        half_h = insert_size * 0.52
        tan_half = math.tan(math.radians(corner_angle) * 0.5) or 1e-6
        half_w = min(insert_size * 1.55, half_h / tan_half)
        poly = QtGui.QPolygonF([QtCore.QPointF(half_w, 0.0), QtCore.QPointF(0.0, half_h), QtCore.QPointF(-half_w, 0.0), QtCore.QPointF(0.0, -half_h)])
        return poly, 0.0
    if key in ("T", "W"):
        tip_angle = 60.0 if key == "T" else 80.0
        tip_x = insert_size * 0.9
        rear_x = insert_size * 0.55
        height = (tip_x + rear_x) * math.tan(math.radians(tip_angle) * 0.5)
        height = min(height, insert_size * 0.95)
        poly = QtGui.QPolygonF([QtCore.QPointF(tip_x, 0.0), QtCore.QPointF(-rear_x, height), QtCore.QPointF(-rear_x, -height)])
        return poly, 0.0
    return handler._build_insert_geometry("C", insert_size)


def tool_orientation_angle(_handler, orientation):
    if orientation is None:
        return 0.0
    angle_map = {0: 0.0, 1: 225.0, 2: 225.0, 3: 135.0, 4: 180.0, 5: 225.0, 6: 270.0, 7: 315.0, 8: 225.0, 9: 315.0}
    angle = angle_map.get(int(orientation), 0.0)
    try:
        settings = QtCore.QSettings()
        offset = float(settings.value("LatheEasyStep/ToolPreviewOrientationOffsetDeg", 0.0))
        mirrored = bool(settings.value("LatheEasyStep/ToolPreviewOrientationMirror", False, type=bool))
        angle = -angle if mirrored else angle
        angle += offset
    except Exception:
        pass
    return angle


def tool_holder_angle(handler, orientation, family, handed):
    base = 0.0 if family in ("holder", "drilling") else handler._tool_orientation_angle(orientation)
    orthogonal = (0.0, 90.0, 180.0, 270.0)
    snapped = min(orthogonal, key=lambda candidate: abs(((base - candidate + 180.0) % 360.0) - 180.0))
    if handed == "internal" and snapped in (0.0, 180.0):
        snapped = 180.0 if snapped == 0.0 else 0.0
    return snapped


def render_tool_preview(handler, tool):
    size = 140
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtGui.QColor("#f4f7fb"))
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    center_x = size / 2
    center_y = size / 2 - 6
    margin = 12
    axis_pen = QtGui.QPen(QtGui.QColor("#63707c"))
    axis_pen.setWidth(1)
    painter.setPen(axis_pen)
    painter.drawLine(QtCore.QLineF(float(margin), float(center_y), float(size - margin), float(center_y)))
    painter.drawLine(QtCore.QLineF(float(center_x), float(margin), float(center_x), float(size - margin)))
    painter.setFont(QtGui.QFont("Arial", 8))
    painter.drawText(QtCore.QPointF(float(size - margin + 4), float(center_y - 2)), "Z")
    painter.drawText(QtCore.QPointF(float(center_x + 2), float(margin - 2)), "X")
    profile = handler._infer_insert_profile(tool)
    shape_key = profile.get("shape_key", "")
    family = profile.get("family", "turning")
    handed = profile.get("handed", "neutral")
    groove_width_mm = profile.get("groove_width_mm", 0.0)
    visual_span = float(tool.d) if tool.d and tool.d >= 1.0 else (6.0 if family in ("turning", "thread", "groove") else 8.0 if family == "holder" else 4.0)
    tool_span = max(visual_span, 1.0)
    scale = max((size - margin * 2) / max(tool_span * 2.1, 1.0), 0.5)
    scale = min(scale, 12.0)
    insert_size = max(2.0, min(tool_span * 0.65, 5.5))
    polygon, circle_radius = handler._build_insert_geometry(shape_key, insert_size, family, handed, groove_width_mm)
    painter.save()
    painter.translate(center_x, center_y)
    painter.scale(scale, scale)
    insert_angle = handler._tool_orientation_angle(tool.orientation)
    holder_angle = handler._tool_holder_angle(tool.orientation, family, handed)
    painter.save()
    painter.rotate(holder_angle)
    shank_pen = QtGui.QPen(QtGui.QColor("#6b7280"), 0)
    painter.setPen(shank_pen)
    painter.setBrush(QtGui.QColor("#d1d5db"))
    shank_on_positive_x = handed == "internal"
    if family == "holder":
        shank = QtCore.QRectF(-insert_size * 2.1, -insert_size * 0.42, insert_size * 4.2, insert_size * 0.84)
    elif shank_on_positive_x:
        shank = QtCore.QRectF(insert_size * 0.6, -insert_size * 0.28, insert_size * 1.4, insert_size * 0.56)
    else:
        shank = QtCore.QRectF(-insert_size * 2.0, -insert_size * 0.28, insert_size * 1.4, insert_size * 0.56)
    painter.drawRect(shank)
    painter.restore()
    painter.save()
    painter.rotate(insert_angle)
    painter.setPen(QtGui.QPen(QtGui.QColor("#2c3e50"), 0))
    painter.setBrush(QtGui.QColor("#e76f51"))
    if polygon is not None:
        painter.drawPolygon(polygon)
    elif circle_radius > 0:
        painter.drawEllipse(QtCore.QPointF(0.0, 0.0), circle_radius, circle_radius)
    if tool.radius_mm and tool.radius_mm > 0:
        nose_radius = max(tool.radius_mm, insert_size * 0.06)
        nose_radius = min(nose_radius, insert_size * 0.24)
        circle_pen = QtGui.QPen(QtGui.QColor(29, 53, 87, 140))
        circle_pen.setWidthF(0.18)
        painter.setPen(circle_pen)
        painter.setBrush(QtGui.QColor(244, 162, 97, 90))
        if polygon is not None and len(polygon) > 0:
            nose_pt = min((polygon[i] for i in range(len(polygon))), key=lambda p: p.x()) if handed == "internal" else max((polygon[i] for i in range(len(polygon))), key=lambda p: p.x())
            painter.drawEllipse(nose_pt, nose_radius, nose_radius)
        else:
            tip_x = -circle_radius if handed == "internal" else circle_radius
            painter.drawEllipse(QtCore.QPointF(tip_x, 0.0), nose_radius, nose_radius)
    painter.restore()
    painter.setPen(QtGui.QColor("#1c1e26"))
    info_text = f"T{tool.t:02d}"
    if tool.iso_code:
        info_text += f" · {tool.iso_code}"
    painter.drawText(margin, size - margin + 6, info_text)
    if tool.orientation is not None:
        painter.drawText(size - margin - 32, size - margin + 6, f"Q{tool.orientation}")
    painter.end()
    return pixmap
