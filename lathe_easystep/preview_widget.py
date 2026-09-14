"""2D-Vorschau-Widget fuer die Drehbank-Kontur (Front-/Slice-Ansicht).

Rein darstellungsbezogen (Qt-Paint-Code, Koordinatentransformation); enthaelt
keine Programmlogik und ist daher unabhaengig vom Handler nutzbar. Als
promoted Widget in lathe_easystep.ui referenziert (siehe <customwidget>
<header>lathe_easystep_handler</header></customwidget> - der Handler
re-exportiert diese Klasse, damit uic.loadUi sie weiterhin ueber den
bestehenden Header findet).
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from qtpy import QtCore, QtGui, QtWidgets

from .model import Operation, OpType
from .preview_scene import (
    build_front_view_draw_plan,
    build_preview_draw_plan,
    primitive_strokes,
    stroke_bounding_rectangle,
)
from .preview_geometry import (
    build_keyway_front_polygons,
    compute_side_viewport,
    front_operation_side,
    front_reference_diameter,
    front_slice_profile,
    front_view_scale,
    interp_x_at_z,
    interp_x_hits_at_z,
    legend_layout,
    path_hits_at_slice,
    preview_primitives_to_points,
    sample_preview_arc,
    side_view_axis_lines,
    side_view_slice_line,
    side_view_ticks,
    status_message_layout,
    side_view_to_screen,
)


class LathePreviewWidget(QtWidgets.QWidget):
    sliceChanged = QtCore.Signal(float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_is_diameter = True  # X values are treated as radius for drawing but labeled as diameter
        self.paths: List[List[Tuple[float, float]]] = []
        self.primitives: List[List[dict]] = []
        self.active_index: int | None = None
        self.preview_scene = None
        # Legend visibility & collision indication
        self.show_legend = True
        self._legend_collapsed = False
        self._legend_click_rect = None

        self._collision_active = False
        self._blink_state = False
        self._blink_timer = QtCore.QTimer(self)
        self._blink_timer.setInterval(350)
        # Slice view support (side view + draggable Z-slice)
        self.view_mode = "side"  # "side" or "slice"
        self.slice_enabled = False
        self.slice_z = 0.0
        self._slice_drag = False
        self._view_rect = None
        self._view_min_z = None
        self._view_max_z = None
        self._view_scale = None
        self.front_program: Dict[str, object] = {}
        self.front_operation: Operation | None = None
        self.status_messages: List[str] = []
        self._blink_timer.timeout.connect(self._on_blink_timer)
        self.setMinimumHeight(200)
        self._base_span = 10.0  # Default 10x10 mm viewport

    def _debug_slice(self, message: str) -> None:
        value = str(os.environ.get("LATHEEASYSTEP_DEBUG", "")).strip().lower()
        if value not in {"1", "true", "yes", "on", "debug"}:
            return
        try:
            print(f"[LatheEasyStep][debug] {message}")
        except Exception:
            pass

    def _x_to_display(self, x_val: float) -> float:
        """Map stored X values (diameter programming) to displayed X values (radius)."""
        try:
            x_num = float(x_val)
        except Exception:
            return 0.0
        return x_num * 0.5 if getattr(self, "x_is_diameter", False) else x_num

    def _display_x_to_label(self, x_display: float) -> float:
        """Map display-space X back to the user-facing axis label value."""
        try:
            x_num = float(x_display)
        except Exception:
            return 0.0
        return x_num * 2.0 if getattr(self, "x_is_diameter", False) else x_num


    def _on_blink_timer(self):
        # Blink when collision is active
        if not self._collision_active:
            if self._blink_state:
                self._blink_state = False
                self.update()
            return
        self._blink_state = not self._blink_state
        self.update()

    def set_collision(self, active: bool):
        self._collision_active = bool(active)
        if self._collision_active:
            if not self._blink_timer.isActive():
                self._blink_timer.start()
        else:
            if self._blink_timer.isActive():
                self._blink_timer.stop()
            self._blink_state = False
            self.update()

    def set_status_messages(self, messages):
        self.status_messages = [str(msg) for msg in (messages or []) if str(msg).strip()]
        self.update()

    def toggle_legend(self):
        # keep a small header visible, toggle between collapsed/expanded
        self._legend_collapsed = not getattr(self, "_legend_collapsed", False)
        self.update()

    def set_view_mode(self, mode: str):
        self.view_mode = mode
        self.update()

    def set_slice_enabled(self, enabled: bool):
        self.slice_enabled = bool(enabled)
        self._slice_drag = False
        self.update()

    def set_slice_z(self, z_val: float, emit: bool = False):
        try:
            z_val = float(z_val)
        except Exception:
            return
        old_z = float(getattr(self, "slice_z", 0.0) or 0.0)
        self.slice_z = z_val
        if abs(old_z - z_val) > 1e-9:
            self._debug_slice(
                f"preview slice_z updated: view_mode={getattr(self, 'view_mode', None)} "
                f"emit={emit} from={old_z:.6f} to={z_val:.6f}"
            )
        if emit:
            try:
                self.sliceChanged.emit(self.slice_z)
            except Exception:
                pass
            callback = getattr(self, "_slice_change_callback", None)
            if callable(callback):
                try:
                    callback(self.slice_z)
                except Exception:
                    pass
        self.update()

    def _pixel_to_z(self, px: float):
        rect = getattr(self, "_view_rect", None)
        min_z = getattr(self, "_view_min_z", None)
        scale = getattr(self, "_view_scale", None)
        if rect is None or min_z is None or scale in (None, 0):
            return None
        z = float(min_z) + (px - rect.left()) / float(scale)
        max_z = getattr(self, "_view_max_z", None)
        if max_z is not None:
            z = max(float(min_z), min(float(max_z), z))
        return z

    def _set_slice_from_pos(self, pos: QtCore.QPoint):
        z = self._pixel_to_z(pos.x())
        if z is None:
            self._debug_slice("preview slice drag ignored: pixel position outside active view")
            return
        self.set_slice_z(z, emit=True)

    def _interp_x_at_z(self, path, z: float):
        return interp_x_at_z(path, z)

    def _interp_x_hits_at_z(self, path, z: float):
        return interp_x_hits_at_z(path, z)

    def _paint_slice_view(self, painter: QtGui.QPainter):
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        diam = None
        if self.paths:
            idx = self.active_index if self.active_index is not None else 0
            idx = max(0, min(idx, len(self.paths) - 1))
            path = self.paths[idx]
            if path and isinstance(path[0], (list, tuple)):
                diam = self._interp_x_at_z(path, self.slice_z)

        if diam is None:
            diam = 10.0

        r = self.rect().adjusted(20, 20, -20, -40)
        cx, cy = r.center().x(), r.center().y()
        radius = abs(float(diam)) / 2.0
        scale = min(r.width(), r.height()) / max(radius * 2.2, 1e-3)
        pix_rad = radius * scale

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        painter.drawEllipse(QtCore.QPointF(cx, cy), pix_rad, pix_rad)

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        painter.drawText(10, self.height() - 10, f"Schnitt bei Z = {self.slice_z:.3f} mm")

    def set_front_context(self, program: Dict[str, object] | None = None, operation: Operation | None = None):
        self.front_program = dict(program or {})
        self.front_operation = operation
        self.update()

    def _path_hits_at_slice(self, path) -> List[float]:
        return path_hits_at_slice(path, self.slice_z, self.primitives_to_points)

    def _front_program_operations(self) -> List[Operation]:
        ops = getattr(self, "front_program", {}).get("__operations")
        if isinstance(ops, list):
            return [op for op in ops if isinstance(op, Operation)]
        op = getattr(self, "front_operation", None)
        return [op] if isinstance(op, Operation) else []

    def _front_operation_side(self, op: Operation) -> str | None:
        return front_operation_side(op)

    def _front_slice_profile(self) -> Dict[str, List[float] | float | None]:
        return front_slice_profile(
            front_program=getattr(self, "front_program", {}) or {},
            front_operations=self._front_program_operations(),
            paths=self.paths,
            active_index=self.active_index,
            slice_z=self.slice_z,
            to_points=self.primitives_to_points,
        )

    def _front_active_diameters(self) -> List[float]:
        profile = self._front_slice_profile()
        hits = profile.get("all_hits", [])
        return list(hits) if isinstance(hits, list) else []

    def _front_reference_diameter(self) -> float:
        return front_reference_diameter(
            front_program=getattr(self, "front_program", {}) or {},
            front_operations=self._front_program_operations(),
            to_points=self.primitives_to_points,
        )

    def _draw_front_keyway_overlay(self, painter: QtGui.QPainter, center: QtCore.QPointF, scale: float):
        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 120, 120), 2))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80, 80)))
        for op in self._front_program_operations():
            if op is None or getattr(op, "op_type", None) != OpType.KEYWAY:
                continue
            params = getattr(op, "params", {}) or {}
            for points in build_keyway_front_polygons(params, self.slice_z):
                poly = QtGui.QPolygonF([
                    QtCore.QPointF(center.x() + x_off * scale, center.y() + y_off * scale)
                    for x_off, y_off in points
                ])
                painter.drawPolygon(poly)
        painter.restore()

    def _paint_front_view(self, painter: QtGui.QPainter):
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        def _float(value: object, default: float = 0.0) -> float:
            try:
                if value is None:
                    return default
                return float(value)
            except Exception:
                return default

        prog = getattr(self, "front_program", {}) or {}
        stock_od = abs(_float(prog.get("xa"), 0.0))
        stock_id = abs(_float(prog.get("xi"), 0.0))
        profile = self._front_slice_profile()
        active_diams = [abs(d) for d in (profile.get("all_hits", []) if isinstance(profile.get("all_hits", []), list) else []) if abs(d) > 1e-6]
        outer_hits = [abs(d) for d in (profile.get("outer_hits", []) if isinstance(profile.get("outer_hits", []), list) else []) if abs(d) > 1e-6]
        inner_hits = [abs(d) for d in (profile.get("inner_hits", []) if isinstance(profile.get("inner_hits", []), list) else []) if abs(d) > 1e-6]
        outer_dia = abs(_float(profile.get("outer_fill"), 0.0))
        inner_dia = abs(_float(profile.get("inner_fill"), 0.0))

        max_diameter = max(self._front_reference_diameter(), 10.0)
        r = self.rect().adjusted(20, 20, -20, -36)
        center = QtCore.QPointF(float(r.center().x()), float(r.center().y()))
        scale = front_view_scale(max_diameter, r.width(), r.height())

        painter.setPen(QtGui.QPen(QtGui.QColor(70, 70, 70), 1))
        painter.drawLine(QtCore.QPointF(r.left(), center.y()), QtCore.QPointF(r.right(), center.y()))
        painter.drawLine(QtCore.QPointF(center.x(), r.top()), QtCore.QPointF(center.x(), r.bottom()))

        draw_plan = build_front_view_draw_plan(
            stock_od=stock_od,
            stock_id=stock_id,
            outer_fill_diameter=outer_dia,
            inner_fill_diameter=inner_dia,
            outer_hits=outer_hits,
            inner_hits=inner_hits,
            active_diameters=active_diams,
        )
        ring_styles = {
            "stock_od": (QtGui.QColor(150, 150, 150), 1, QtCore.Qt.DashLine),
            "stock_id": (QtGui.QColor(110, 110, 110), 1, QtCore.Qt.DashLine),
            "outer_ring": (QtGui.QColor(255, 80, 80), 2, QtCore.Qt.SolidLine),
            "inner_ring": (QtGui.QColor(255, 170, 70), 2, QtCore.Qt.SolidLine),
            "active_ring": (QtGui.QColor(255, 220, 120), 1, QtCore.Qt.SolidLine),
        }

        def draw_ring(circle) -> None:
            color, width, style = ring_styles[circle.style_key]
            painter.setPen(QtGui.QPen(color, width, style))
            painter.setBrush(QtCore.Qt.NoBrush)
            radius = (circle.diameter * 0.5) * scale
            painter.drawEllipse(center, radius, radius)

        for circle in draw_plan:
            if circle.style_key in ("stock_od", "stock_id"):
                draw_ring(circle)

        end_contour = [c for c in draw_plan if c.filled]
        if end_contour:
            painter.save()
            painter.setPen(QtCore.Qt.NoPen)
            for circle in end_contour:
                painter.setBrush(
                    QtGui.QBrush(QtCore.Qt.black)
                    if circle.style_key == "end_contour_hole"
                    else QtGui.QBrush(QtGui.QColor(255, 80, 80, 70))
                )
                radius = (circle.diameter * 0.5) * scale
                painter.drawEllipse(center, radius, radius)
            painter.restore()

        self._draw_front_keyway_overlay(painter, center, scale)

        for circle in draw_plan:
            if circle.style_key in ("outer_ring", "inner_ring", "active_ring"):
                draw_ring(circle)

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        painter.drawText(10, self.height() - 10, f"Vorderansicht bei Z = {self.slice_z:.3f} mm")
        if active_diams:
            painter.drawText(10, 16, "D final: " + ", ".join(f"{d:.3f}" for d in active_diams[:3]))
        painter.drawText(10, 32, f"D max: {max_diameter:.3f}")

    def mousePressEvent(self, event):  # type: ignore[override]
        # Click on legend to toggle
        rect = getattr(self, "_legend_click_rect", None)
        if rect and rect.contains(event.pos()):
            self.toggle_legend()
            event.accept()
            return

        # Drag slice line in side view
        if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
            vrect = getattr(self, "_view_rect", None)
            if vrect is not None and vrect.contains(event.pos()) and event.button() == QtCore.Qt.LeftButton:
                self._slice_drag = True
                self._set_slice_from_pos(event.pos())
                event.accept()
                return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):  # type: ignore[override]
        if getattr(self, "_slice_drag", False) and getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
            self._set_slice_from_pos(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        if getattr(self, "_slice_drag", False):
            self._slice_drag = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _sample_arc(self, p1, p2, c, ccw):
        return sample_preview_arc(p1, p2, c, ccw)

    def primitives_to_points(self, prims):
        return preview_primitives_to_points(prims)

    def set_paths(self, paths, active_index: int | None = None):
        # paths can be:
        #   - list of list-of-(x,z) points (legacy)
        #   - list of primitives [{type:line/arc,...}, ...] for a single path
        #   - list of list-of-primitives for multiple paths
        self.active_index = active_index

        # IMPORTANT:
        # We keep "primitive" paths (list of dicts) as-is so the paintEvent
        # can style them by role (e.g. stock / retract) and still draw them.
        norm_paths = []
        for entry in paths or []:
            if isinstance(entry, dict) and "type" in entry:
                # single primitive dict
                norm_paths.append([entry])
                continue

            if isinstance(entry, (list, tuple)):
                # list of primitives (dict) or list of points
                if entry and isinstance(entry[0], dict) and "type" in entry[0]:
                    norm_paths.append(list(entry))
                    continue

                pts = []
                for pt in entry:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        try:
                            pts.append((float(pt[0]), float(pt[1])))
                        except Exception:
                            continue
                if pts:
                    norm_paths.append(pts)

        self.paths = norm_paths
        self.update()

    def set_preview_scene(self, scene) -> None:
        """Retain semantic layers; path transfer remains separately compatible."""
        self.preview_scene = scene

    def set_primitives(self, primitives):
        """
        Kompatibilität: Einige Teile des Codes arbeiten mit 'primitives'
        (Linien/Arcs/Polylines). Dieses Widget zeichnet aber über 'paths'.
        Daher: primitives -> points -> set_paths().
        """
        self.primitives = primitives or []
        try:
            paths = self.primitives_to_points(self.primitives)
        except Exception:
            paths = []
        self.set_paths(paths)

    def paintEvent(self, event):  # type: ignore[override]
        painter = QtGui.QPainter(self)
        if getattr(self, "view_mode", "side") == "slice":
            try:
                self._paint_slice_view(painter)
            finally:
                painter.end()
            return
        if getattr(self, "view_mode", "side") == "front":
            try:
                self._paint_front_view(painter)
            finally:
                painter.end()
            return
        self._legend_click_rect = None
        try:
            painter.fillRect(self.rect(), QtCore.Qt.black)
            margin = 30
            rect = self.rect().adjusted(margin, margin, -margin, -margin)
            viewport = compute_side_viewport(
                self.paths,
                rect.width(),
                rect.height(),
                x_is_diameter=self.x_is_diameter,
                base_span=self._base_span,
            )
            min_x, max_x = viewport["min_x"], viewport["max_x"]
            min_z, max_z = viewport["min_z"], viewport["max_z"]
            scale = viewport["scale"]

            # store mapping for interactive slice
            self._view_rect = rect
            self._view_min_z = min_z
            self._view_max_z = max_z
            self._view_scale = scale

            def to_screen(x_val: float, z_val: float) -> QtCore.QPointF:
                point = side_view_to_screen(
                    x_val, z_val, viewport, left=rect.left(), bottom=rect.bottom(),
                    x_is_diameter=self.x_is_diameter,
                )
                return QtCore.QPointF(*point)

            # optional slice indicator (selected Z)
            if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
                try:
                    zline = float(getattr(self, "slice_z", 0.0))
                    line = side_view_slice_line(
                        viewport, zline, left=rect.left(), bottom=rect.bottom()
                    )
                    p1, p2 = QtCore.QPointF(*line[0]), QtCore.QPointF(*line[1])
                    pen = QtGui.QPen(QtGui.QColor(255, 180, 0), 2, QtCore.Qt.DashLine)
                    painter.setPen(pen)
                    painter.drawLine(p1, p2)
                    label = f"Schnitt Z {zline:.3f}"
                    text_pos = QtCore.QPointF(min(p1.x() + 8, rect.right() - 90), rect.top() + 16)
                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 220, 120), 1))
                    painter.drawText(text_pos, label)
                except Exception:
                    pass

            # Achsen und Skala (außen: links/unten)
            painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
            axes = side_view_axis_lines(
                viewport, left=rect.left(), bottom=rect.bottom()
            )
            x_axis, x_axis_end = (QtCore.QPointF(*point) for point in axes["x_line"])
            z_axis, z_axis_end = (QtCore.QPointF(*point) for point in axes["z_line"])
            painter.drawLine(z_axis, z_axis_end)  # Z-Achse horizontal
            painter.drawLine(x_axis, x_axis_end)  # X-Achse vertikal

            tick_pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1)
            font_pen = QtGui.QPen(QtGui.QColor(160, 160, 160), 1)
            painter.setFont(QtGui.QFont("Sans", 8))

            ticks = side_view_ticks(
                viewport, left=rect.left(), bottom=rect.bottom(),
                x_is_diameter=self.x_is_diameter,
            )

            # Z-Ticks (horizontal unten/oben)
            for _value, label_value, point in ticks["z"]:
                pt = QtCore.QPointF(*point)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 2))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 6, pt.y() + 14), f"{label_value:.0f}")

            # X-Ticks (vertikal links/rechts)
            for _value, label_value, point in ticks["x"]:
                pt = QtCore.QPointF(*point)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x() - 2, pt.y(), pt.x() + 4, pt.y()))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 28, pt.y() + 4), f"{label_value:.0f}")

            # Achsbeschriftungen
            painter.setPen(font_pen)
            painter.drawText(QtCore.QPointF(rect.right() - 20, z_axis.y() - 6), "Z")
            painter.drawText(QtCore.QPointF(x_axis.x() + 6, rect.top() + 12), "X")
            styles = {
                "stock": (QtGui.QColor("gray"), 1, QtCore.Qt.DashLine),
                "retract": (QtGui.QColor(0, 180, 180), 1, QtCore.Qt.DashLine),
                "worklimit": (QtGui.QColor(220, 0, 0), 2, QtCore.Qt.DashLine),
                "chuck_nogo": (QtGui.QColor(200, 60, 220), 1, QtCore.Qt.DashDotLine),
                "contour_rough": (QtGui.QColor(240, 180, 0), 2, QtCore.Qt.DashLine),
                "feature": (QtGui.QColor(0, 190, 255), 2, QtCore.Qt.SolidLine),
                "feature_separate": (QtGui.QColor(0, 190, 255), 2, QtCore.Qt.DashDotLine),
                "active": (QtGui.QColor("red"), 3, QtCore.Qt.SolidLine),
                "workpiece": (QtGui.QColor(70, 155, 255), 2, QtCore.Qt.SolidLine),
                "auxiliary": (QtGui.QColor(145, 145, 145), 1, QtCore.Qt.DashDotLine),
                "tool_path": (QtGui.QColor("lime"), 2, QtCore.Qt.SolidLine),
            }
            draw_plan = build_preview_draw_plan(
                self.paths, self.active_index, self.preview_scene
            )
            for item in draw_plan:
                idx, role = item.index, item.role
                path = self.paths[idx]
                color, width, style = styles[item.style_key]

                pen = QtGui.QPen(color, width)
                pen.setStyle(style)
                painter.setPen(pen)

                # Primitive mode (dict primitives from build_*_outline helpers)
                if isinstance(path[0], dict):
                    # Every primitive is a separate stroke. Joining the sampled
                    # points of disconnected primitives would invent diagonal
                    # machine moves that neither model nor G-code contains.
                    strokes = primitive_strokes(path, self._sample_arc)
                    if role == "chuck_nogo":
                        region = stroke_bounding_rectangle(strokes)
                        if region:
                            fill_poly = QtGui.QPolygonF([to_screen(*point) for point in region])
                            painter.save()
                            painter.setPen(QtCore.Qt.NoPen)
                            painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 60, 220, 55)))
                            painter.drawPolygon(fill_poly)
                            painter.restore()
                    for stroke in strokes:
                        if len(stroke) >= 2:
                            painter.drawPolyline(QtGui.QPolygonF([to_screen(x, z) for x, z in stroke]))
                        elif len(stroke) == 1:
                            pt = to_screen(stroke[0][0], stroke[0][1])
                            painter.drawLine(QtCore.QLineF(pt.x() - 4, pt.y(), pt.x() + 4, pt.y()))
                            painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 4))
                    continue
                points = [to_screen(x, z) for x, z in path]
                painter.drawPolyline(QtGui.QPolygonF(points))

            legend_enabled = getattr(self, "show_legend", True)
            collapsed = getattr(self, "_legend_collapsed", False)

            if legend_enabled:
                # --- Legend: "Legende" header is always visible, click toggles details ---
                try:
                    legend_items = [
                        ("Werkzeugweg", QtGui.QPen(QtGui.QColor(0, 255, 0), 2, QtCore.Qt.SolidLine)),
                        ("Werkstück", QtGui.QPen(QtGui.QColor(70, 155, 255), 2, QtCore.Qt.SolidLine)),
                        ("Hilfsgeometrie", QtGui.QPen(QtGui.QColor(145, 145, 145), 1, QtCore.Qt.DashDotLine)),
                        ("Aktiv", QtGui.QPen(QtGui.QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)),
                        ("Rohteil", QtGui.QPen(QtGui.QColor(180, 180, 180), 1, QtCore.Qt.SolidLine)),
                        ("Rückzug", QtGui.QPen(QtGui.QColor(0, 255, 255), 1, QtCore.Qt.DashLine)),
                        ("Schruppkontur", QtGui.QPen(QtGui.QColor(240, 180, 0), 2, QtCore.Qt.DashLine)),
                        ("Freistich", QtGui.QPen(QtGui.QColor(0, 190, 255), 2, QtCore.Qt.SolidLine)),
                        ("Bearbeitungslinie", QtGui.QPen(QtGui.QColor(255, 0, 0), 1, QtCore.Qt.DashLine)),
                        ("Futter-Sperrzone", QtGui.QPen(QtGui.QColor(200, 60, 220), 1, QtCore.Qt.DashDotLine)),
                    ]

                    layout = legend_layout(len(legend_items), collapsed=collapsed)

                    bg = QtGui.QColor(0, 0, 0, 160)
                    painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
                    painter.setBrush(QtGui.QBrush(bg))
                    painter.drawRoundedRect(QtCore.QRectF(*layout["box_rect"]), 6, 6)

                    # Click target = header area (always present)
                    self._legend_click_rect = QtCore.QRectF(*layout["click_rect"])

                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                    painter.setFont(QtGui.QFont("Sans", 8))
                    painter.drawText(
                        QtCore.QRectF(*layout["header_text_rect"]),
                        QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                        "Legende"
                    )

                    for (label, pen), row in zip(legend_items, layout["rows"]):
                        painter.setPen(pen)
                        painter.drawLine(QtCore.QPointF(*row["line"][0]), QtCore.QPointF(*row["line"][1]))
                        painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
                        painter.drawText(QtCore.QPointF(*row["label_pos"]), label)

                except Exception:
                    self._legend_click_rect = None

            status_layout = status_message_layout(
                getattr(self, "status_messages", None), widget_width=self.width()
            )
            if status_layout is not None:
                try:
                    painter.setPen(QtGui.QPen(QtGui.QColor(180, 80, 20), 1))
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 240, 210, 220)))
                    painter.drawRoundedRect(QtCore.QRectF(*status_layout["box_rect"]), 6, 6)
                    painter.setPen(QtGui.QPen(QtGui.QColor(90, 40, 0), 1))
                    painter.drawText(QtCore.QPointF(*status_layout["header_pos"]), "Warnungen")
                    for msg, pos in zip(status_layout["messages"], status_layout["line_positions"]):
                        painter.drawText(QtCore.QPointF(*pos), f"- {msg}")
                except Exception:
                    pass

        except Exception:
            self._legend_click_rect = None
        finally:
            painter.end()
