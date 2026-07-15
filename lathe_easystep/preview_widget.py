"""2D-Vorschau-Widget fuer die Drehbank-Kontur (Front-/Slice-Ansicht).

Rein darstellungsbezogen (Qt-Paint-Code, Koordinatentransformation); enthaelt
keine Programmlogik und ist daher unabhaengig vom Handler nutzbar. Als
promoted Widget in lathe_easystep.ui referenziert (siehe <customwidget>
<header>lathe_easystep_handler</header></customwidget> - der Handler
re-exportiert diese Klasse, damit uic.loadUi sie weiterhin ueber den
bestehenden Header findet).
"""

from __future__ import annotations

import math
import os
from typing import Dict, List, Tuple

from qtpy import QtCore, QtGui, QtWidgets

from .gcode_utils import is_internal_side
from .model import Operation, OpType
from .preview_geometry import (
    build_keyway_slot_angles,
    front_view_polar_to_cartesian,
    keyway_slice_bounds,
)


class LathePreviewWidget(QtWidgets.QWidget):
    sliceChanged = QtCore.Signal(float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_is_diameter = True  # X values are treated as radius for drawing but labeled as diameter
        self.paths: List[List[Tuple[float, float]]] = []
        self.primitives: List[List[dict]] = []
        self.active_index: int | None = None
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
        hits = self._interp_x_hits_at_z(path, z)
        if not hits:
            return None
        return min(hits)

    def _interp_x_hits_at_z(self, path, z: float):
        if not path or len(path) < 2:
            return []
        hits = []
        for (x1, z1), (x2, z2) in zip(path[:-1], path[1:]):
            if abs(z2 - z1) < 1e-9:
                if abs(z - z1) < 1e-6:
                    hits.append(x1); hits.append(x2)
                continue
            if (z1 <= z <= z2) or (z2 <= z <= z1):
                t = (z - z1) / (z2 - z1)
                hits.append(x1 + t * (x2 - x1))
        uniq: List[float] = []
        for val in sorted(float(h) for h in hits):
            if not uniq or abs(val - uniq[-1]) > 1e-6:
                uniq.append(val)
        return uniq

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
        if not path:
            return []
        if isinstance(path[0], dict):
            try:
                path = self.primitives_to_points(path)
            except Exception:
                return []
        return self._interp_x_hits_at_z(path, self.slice_z)

    def _front_program_operations(self) -> List[Operation]:
        ops = getattr(self, "front_program", {}).get("__operations")
        if isinstance(ops, list):
            return [op for op in ops if isinstance(op, Operation)]
        op = getattr(self, "front_operation", None)
        return [op] if isinstance(op, Operation) else []

    def _front_operation_side(self, op: Operation) -> str | None:
        params = getattr(op, "params", {}) or {}
        if op.op_type in (OpType.DRILL, OpType.BORE):
            return "inside"
        if op.op_type == OpType.GROOVE:
            try:
                return "inside" if int(float(params.get("lage", 0) or 0)) == 1 else "outside"
            except Exception:
                return "outside"
        if op.op_type == OpType.THREAD:
            return "inside" if is_internal_side(params.get("orientation", 0)) else "outside"
        if op.op_type == OpType.ABSPANEN:
            return "inside" if is_internal_side(params.get("side", 0)) else "outside"
        if op.op_type == OpType.KEYWAY:
            return None
        return "outside"

    def _front_slice_profile(self) -> Dict[str, List[float] | float | None]:
        prog = getattr(self, "front_program", {}) or {}
        try:
            stock_od = abs(float(prog.get("xa", 0.0) or 0.0))
        except Exception:
            stock_od = 0.0
        try:
            stock_id = abs(float(prog.get("xi", 0.0) or 0.0))
        except Exception:
            stock_id = 0.0

        outer_hits: List[float] = []
        inner_hits: List[float] = []
        neutral_hits: List[float] = []

        ops = self._front_program_operations()
        if not ops and self.paths:
            idx = self.active_index if self.active_index is not None else 0
            idx = max(0, min(idx, len(self.paths) - 1))
            raw_hits = [abs(d) for d in self._path_hits_at_slice(self.paths[idx]) if abs(d) > 1e-6]
            return {
                "outer_hits": sorted(raw_hits, reverse=True),
                "inner_hits": [],
                "neutral_hits": [],
                "all_hits": sorted(raw_hits, reverse=True),
                "outer_fill": max(raw_hits) if raw_hits else (stock_od if stock_od > 1e-6 else None),
                "inner_fill": stock_id if stock_id > 1e-6 else None,
            }

        for op in ops:
            if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
                continue
            if getattr(op, "op_type", None) == OpType.KEYWAY:
                continue
            hits = [abs(d) for d in self._path_hits_at_slice(getattr(op, "path", []) or []) if abs(d) > 1e-6]
            if not hits:
                continue
            side = self._front_operation_side(op)
            if side == "inside":
                inner_hits.extend(hits)
            elif side == "outside":
                outer_hits.extend(hits)
            else:
                neutral_hits.extend(hits)

        def _uniq_desc(values: List[float]) -> List[float]:
            uniq: List[float] = []
            for val in sorted((abs(float(v)) for v in values if abs(float(v)) > 1e-6), reverse=True):
                if not uniq or abs(val - uniq[-1]) > 1e-6:
                    uniq.append(val)
            return uniq

        outer_hits = _uniq_desc(outer_hits)
        inner_hits = _uniq_desc(inner_hits)
        neutral_hits = _uniq_desc(neutral_hits)
        all_hits = _uniq_desc(outer_hits + inner_hits + neutral_hits)

        outer_fill = outer_hits[0] if outer_hits else (stock_od if stock_od > 1e-6 else None)
        inner_fill = inner_hits[-1] if inner_hits else (stock_id if stock_id > 1e-6 else None)

        return {
            "outer_hits": outer_hits,
            "inner_hits": inner_hits,
            "neutral_hits": neutral_hits,
            "all_hits": all_hits,
            "outer_fill": outer_fill,
            "inner_fill": inner_fill,
        }

    def _front_active_diameters(self) -> List[float]:
        profile = self._front_slice_profile()
        hits = profile.get("all_hits", [])
        return list(hits) if isinstance(hits, list) else []

    def _front_reference_diameter(self) -> float:
        prog = getattr(self, "front_program", {}) or {}
        candidates: List[float] = []

        for key in ("xa", "xi"):
            try:
                val = abs(float(prog.get(key, 0.0) or 0.0))
            except Exception:
                val = 0.0
            if val > 1e-6:
                candidates.append(val)

        for op in self._front_program_operations():
            if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
                continue
            path = getattr(op, "path", None) or []
            if not path:
                continue
            if isinstance(path[0], dict):
                try:
                    pts = self.primitives_to_points(path)
                except Exception:
                    pts = []
            else:
                pts = path
            for pt in pts:
                try:
                    dia = abs(float(pt[0]))
                except Exception:
                    continue
                if dia > 1e-6:
                    candidates.append(dia)

            if getattr(op, "op_type", None) == OpType.KEYWAY:
                params = getattr(op, "params", {}) or {}
                try:
                    start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
                    nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
                    radial_side = int(float(params.get("radial_side", 0) or 0))
                except Exception:
                    continue
                if start_dia > 1e-6:
                    candidates.append(start_dia)
                    if radial_side != 0 and nut_depth > 1e-6:
                        candidates.append(start_dia + (2.0 * nut_depth))

        return max(candidates, default=10.0)

    def _draw_front_keyway_overlay(self, painter: QtGui.QPainter, center: QtCore.QPointF, scale: float):
        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 120, 120), 2))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80, 80)))
        samples = 14

        for op in self._front_program_operations():
            if op is None or getattr(op, "op_type", None) != OpType.KEYWAY:
                continue
            params = getattr(op, "params", {}) or {}
            try:
                mode = int(float(params.get("mode", 0)))
            except Exception:
                mode = 0
            if mode != 0:
                continue

            try:
                start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
                nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
                slot_width = abs(float(params.get("slot_width", params.get("cutting_width", 0.0)) or 0.0))
                radial_side = int(float(params.get("radial_side", 0) or 0))
            except Exception:
                continue

            bounds = keyway_slice_bounds(params)
            if bounds is None:
                continue
            z_min, z_max = bounds
            if self.slice_z < z_min - 1e-6 or self.slice_z > z_max + 1e-6 or start_dia <= 0.0:
                continue

            base_radius = start_dia * 0.5
            if radial_side == 0:
                slot_outer_radius = base_radius
                slot_inner_radius = max(0.0, base_radius - nut_depth)
            else:
                slot_inner_radius = base_radius
                slot_outer_radius = base_radius + nut_depth

            if slot_outer_radius <= 1e-9:
                continue

            if slot_width > 0.0:
                half_opening = max(math.radians(2.0), min(math.radians(40.0), slot_width / max(slot_outer_radius, 1e-6)))
            else:
                half_opening = math.radians(6.0)

            for a_mid in build_keyway_slot_angles(params):
                a0 = a_mid - half_opening
                a1 = a_mid + half_opening
                poly = QtGui.QPolygonF()
                for i in range(samples + 1):
                    ang = a0 + ((a1 - a0) * i / samples)
                    x_off, y_off = front_view_polar_to_cartesian(ang, slot_outer_radius * scale)
                    poly.append(QtCore.QPointF(
                        center.x() + x_off,
                        center.y() + y_off,
                    ))
                for i in range(samples, -1, -1):
                    ang = a0 + ((a1 - a0) * i / samples)
                    x_off, y_off = front_view_polar_to_cartesian(ang, slot_inner_radius * scale)
                    poly.append(QtCore.QPointF(
                        center.x() + x_off,
                        center.y() + y_off,
                    ))
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
        scale = min(r.width(), r.height()) / max(max_diameter * 1.15, 1e-6)

        painter.setPen(QtGui.QPen(QtGui.QColor(70, 70, 70), 1))
        painter.drawLine(QtCore.QPointF(r.left(), center.y()), QtCore.QPointF(r.right(), center.y()))
        painter.drawLine(QtCore.QPointF(center.x(), r.top()), QtCore.QPointF(center.x(), r.bottom()))

        if stock_od > 1e-6:
            painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150), 1, QtCore.Qt.DashLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (stock_od * 0.5) * scale
            painter.drawEllipse(center, rad, rad)
        if stock_id > 1e-6 and stock_id < stock_od:
            painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 110), 1, QtCore.Qt.DashLine))
            rad = (stock_id * 0.5) * scale
            painter.drawEllipse(center, rad, rad)

        if outer_dia > 1e-6:
            painter.save()
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80, 70)))
            painter.drawEllipse(center, (outer_dia * 0.5) * scale, (outer_dia * 0.5) * scale)
            if inner_dia > 1e-6 and inner_dia < outer_dia - 1e-6:
                painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
                painter.drawEllipse(center, (inner_dia * 0.5) * scale, (inner_dia * 0.5) * scale)
            painter.restore()

        self._draw_front_keyway_overlay(painter, center, scale)

        for diameter in outer_hits:
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 80, 80), 2))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (diameter * 0.5) * scale
            painter.drawEllipse(center, rad, rad)
        for diameter in inner_hits:
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 170, 70), 2))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (diameter * 0.5) * scale
            painter.drawEllipse(center, rad, rad)
        for diameter in active_diams:
            if any(abs(diameter - d) <= 1e-6 for d in outer_hits + inner_hits):
                continue
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 220, 120), 1))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (diameter * 0.5) * scale
            painter.drawEllipse(center, rad, rad)

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

    def _sample_arc(self, p1, p2, c, ccw, steps=48):
        # All X values in primitives are DIAMETER (LinuxCNC lathe convention).
        # The fillet arc is a circle in physical (radius) space, so we must
        # convert X to radius for correct geometry (angles, distances).
        x1, z1 = p1[0] / 2.0, p1[1]
        x2, z2 = p2[0] / 2.0, p2[1]
        xc, zc = c[0] / 2.0, c[1]
        r1 = math.hypot(x1 - xc, z1 - zc)
        r2 = math.hypot(x2 - xc, z2 - zc)
        if r1 <= 1e-9 or abs(r1 - r2) > 1e-3:
            return [p1, p2]
        a1 = math.atan2(z1 - zc, x1 - xc)
        a2 = math.atan2(z2 - zc, x2 - xc)
        # The primitive's ccw flag follows LinuxCNC G18 complex(Z,X)
        # convention, but atan2(z,x) measures angle from X toward Z
        # — opposite rotation sense.  Invert the sweep direction so
        # the preview arc matches the physical fillet.
        if not ccw:          # G-code CW (G2) → preview CCW sweep
            if a2 <= a1:
                a2 += 2 * math.pi
        else:                # G-code CCW (G3) → preview CW sweep
            if a2 >= a1:
                a2 -= 2 * math.pi
        pts = []
        for k in range(steps + 1):
            t = k / steps
            a = a1 + (a2 - a1) * t
            # Sample in radius-space, convert X back to diameter
            pts.append(((xc + r1 * math.cos(a)) * 2.0, zc + r1 * math.sin(a)))
        return pts

    def primitives_to_points(self, prims):
        pts = []
        last = None
        for pr in prims or []:
            if isinstance(pr, (list, tuple)) and len(pr) >= 2:
                try:
                    p = (float(pr[0]), float(pr[1]))
                except Exception:
                    continue
                pts.append(p)
                last = p
                continue
            if not isinstance(pr, dict):
                continue
            typ = (pr.get("type") or "").lower()
            if typ == "line":
                p1 = tuple(pr.get("p1", (0.0, 0.0)))
                p2 = tuple(pr.get("p2", (0.0, 0.0)))
                if last is None:
                    pts.append(p1)
                elif math.hypot(p1[0] - last[0], p1[1] - last[1]) > 1e-6:
                    pts.append(p1)
                pts.append(p2)
                last = p2
            elif typ == "arc":
                p1 = tuple(pr.get("p1", (0.0, 0.0)))
                p2 = tuple(pr.get("p2", (0.0, 0.0)))
                c = tuple(pr.get("c", (0.0, 0.0)))
                ccw = bool(pr.get("ccw", True))
                arc_pts = self._sample_arc(p1, p2, c, ccw)
                if last is None:
                    pts.extend(arc_pts)
                else:
                    if math.hypot(arc_pts[0][0] - last[0], arc_pts[0][1] - last[1]) > 1e-6:
                        pts.append(arc_pts[0])
                    pts.extend(arc_pts[1:])
                last = arc_pts[-1]
        return pts

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
            # Collect bounds across all paths (supports point lists and primitive lists)
            inf = float('inf')
            min_x, max_x = inf, -inf
            min_z, max_z = inf, -inf

            def _upd(xv: float, zv: float):
                nonlocal min_x, max_x, min_z, max_z
                x_draw = self._x_to_display(xv)
                min_x = min(min_x, x_draw)
                max_x = max(max_x, x_draw)
                min_z = min(min_z, zv)
                max_z = max(max_z, zv)

            any_data = False
            for path in self.paths:
                if not path:
                    continue
                any_data = True
                first = path[0]
                if isinstance(first, dict):
                    # primitives (line/arc with p1/p2/c) -> sample to points for bounds
                    try:
                        pts = self.primitives_to_points(path)
                    except Exception:
                        pts = []
                    for (xv, zv) in pts:
                        _upd(float(xv), float(zv))
                else:
                    for (xv, zv) in path:
                        _upd(float(xv), float(zv))

            if not any_data or min_x == inf or min_z == inf:
                min_x = max_x = 0.0
                min_z = max_z = 0.0
            # Ursprung und Mindestgröße immer berücksichtigen
            half_span = self._base_span / 2.0
            min_x = min(min_x, -half_span, 0.0)
            max_x = max(max_x, half_span, 0.0)
            min_z = min(min_z, -half_span, 0.0)
            max_z = max(max_z, half_span, 0.0)

            dx = max_x - min_x
            dz = max_z - min_z

            def ensure_span(min_val: float, max_val: float, base_span: float) -> Tuple[float, float]:
                span = max_val - min_val
                if span < base_span:
                    pad = (base_span - span) / 2.0
                    return min_val - pad, max_val + pad
                return min_val, max_val

            min_x, max_x = ensure_span(min_x, max_x, self._base_span)
            min_z, max_z = ensure_span(min_z, max_z, self._base_span)

            # kleiner Rand um die Geometrie
            dx = max(max_x - min_x, 1e-3)
            dz = max(max_z - min_z, 1e-3)
            pad = 0.05
            min_x -= dx * pad
            max_x += dx * pad
            min_z -= dz * pad
            max_z += dz * pad

            margin = 30
            rect = self.rect().adjusted(margin, margin, -margin, -margin)
            scale_z = rect.width() / max(max_z - min_z, 1e-6)
            scale_x = rect.height() / max(max_x - min_x, 1e-6)
            scale = min(scale_x, scale_z)


            # store mapping for interactive slice
            self._view_rect = rect
            self._view_min_z = min_z
            self._view_max_z = max_z
            self._view_scale = scale

            def to_screen(x_val: float, z_val: float) -> QtCore.QPointF:
                # Z horizontal, X vertikal
                x_draw = self._x_to_display(x_val)
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_draw - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            def to_screen_display(x_display: float, z_val: float) -> QtCore.QPointF:
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_display - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            # optional slice indicator (selected Z)
            if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
                try:
                    zline = float(getattr(self, "slice_z", 0.0))
                    p1 = to_screen_display(min_x, zline)
                    p2 = to_screen_display(max_x, zline)
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
            axis_x_val = 0.0 if min_x <= 0.0 <= max_x else min_x
            axis_z_val = 0.0 if min_z <= 0.0 <= max_z else min_z
            x_axis = to_screen_display(axis_x_val, min_z)
            x_axis_end = to_screen_display(axis_x_val, max_z)
            z_axis = to_screen_display(min_x, axis_z_val)
            z_axis_end = to_screen_display(max_x, axis_z_val)
            painter.drawLine(z_axis, z_axis_end)  # Z-Achse horizontal
            painter.drawLine(x_axis, x_axis_end)  # X-Achse vertikal

            def nice_step(span: float) -> float:
                if span <= 0:
                    return 1.0
                raw = span / 5.0
                power = 10 ** int(math.floor(math.log10(raw)))
                for m in (1, 2, 5, 10):
                    step = m * power
                    if span / step <= 8:
                        return step
                return raw

            tick_pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1)
            font_pen = QtGui.QPen(QtGui.QColor(160, 160, 160), 1)
            painter.setFont(QtGui.QFont("Sans", 8))

            # Z-Ticks (horizontal unten/oben)
            step_z = nice_step(max_z - min_z)
            val = (min_z // step_z) * step_z
            while val <= max_z:
                pt = to_screen_display(axis_x_val, val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 2))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 6, pt.y() + 14), f"{val:.0f}")
                val += step_z

            # X-Ticks (vertikal links/rechts)
            step_x = nice_step(max_x - min_x)
            val = (min_x // step_x) * step_x
            while val <= max_x:
                pt = to_screen_display(val, axis_z_val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x() - 2, pt.y(), pt.x() + 4, pt.y()))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 28, pt.y() + 4), f"{self._display_x_to_label(val):.0f}")
                val += step_x

            # Achsbeschriftungen
            painter.setPen(font_pen)
            painter.drawText(QtCore.QPointF(rect.right() - 20, z_axis.y() - 6), "Z")
            painter.drawText(QtCore.QPointF(x_axis.x() + 6, rect.top() + 12), "X")
            draw_order = [idx for idx in range(len(self.paths)) if idx != self.active_index]
            if self.active_index is not None and 0 <= self.active_index < len(self.paths):
                draw_order.append(self.active_index)

            for idx in draw_order:
                path = self.paths[idx]
                if not path:
                    continue

                # role based styling (e.g. raw stock reference)
                role = None
                if isinstance(path, list) and path:
                    # path can be a list of primitive dicts; pick first non-empty role
                    for d in path:
                        if isinstance(d, dict):
                            r = d.get("role")
                            if r:
                                role = r
                                break

                if role == "stock":
                    color = QtGui.QColor("gray")
                    width = 1
                    style = QtCore.Qt.DashLine
                elif role == "retract":
                    # retract planes: visually distinct and clearly *not* a contour
                    color = QtGui.QColor(0, 180, 180)
                    width = 1
                    style = QtCore.Qt.DashLine
                elif role == "worklimit":
                    # workpiece stick-out / chuck collision limit (Bearbeitungsmaß)
                    color = QtGui.QColor(220, 0, 0)
                    width = 2
                    style = QtCore.Qt.DashLine
                elif role == "chuck_nogo":
                    # chuck safety no-go area
                    color = QtGui.QColor(200, 60, 220)
                    width = 1
                    style = QtCore.Qt.DashDotLine
                elif role == "contour_rough":
                    color = QtGui.QColor(240, 180, 0)
                    width = 2
                    style = QtCore.Qt.DashLine
                elif role == "feature":
                    color = QtGui.QColor(0, 190, 255)
                    width = 2
                    style = QtCore.Qt.SolidLine
                elif role == "feature_separate":
                    color = QtGui.QColor(0, 190, 255)
                    width = 2
                    style = QtCore.Qt.DashDotLine
                else:
                    color = QtGui.QColor("lime") if idx != self.active_index else QtGui.QColor("red")
                    width = 2 if idx != self.active_index else 3
                    style = QtCore.Qt.SolidLine

                pen = QtGui.QPen(color, width)
                pen.setStyle(style)
                painter.setPen(pen)

                # Primitive mode (dict primitives from build_*_outline helpers)
                if isinstance(path[0], dict):
                    # NOTE: do NOT connect independent primitives with a single polyline.
                    # For retract planes this would create confusing diagonal "links" between separate helper lines.
                    if role in ("retract", "stock", "worklimit", "chuck_nogo"):
                        if role == "chuck_nogo":
                            region_pts: List[Tuple[float, float]] = []
                            for prim in path:
                                if not isinstance(prim, dict) or prim.get("type") != "line":
                                    continue
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                if p1 and len(p1) >= 2:
                                    try:
                                        region_pts.append((float(p1[0]), float(p1[1])))
                                    except Exception:
                                        pass
                                if p2 and len(p2) >= 2:
                                    try:
                                        region_pts.append((float(p2[0]), float(p2[1])))
                                    except Exception:
                                        pass
                            if region_pts:
                                rx_min = min(p[0] for p in region_pts)
                                rx_max = max(p[0] for p in region_pts)
                                rz_min = min(p[1] for p in region_pts)
                                rz_max = max(p[1] for p in region_pts)
                                fill_poly = QtGui.QPolygonF([
                                    to_screen(rx_min, rz_min),
                                    to_screen(rx_min, rz_max),
                                    to_screen(rx_max, rz_max),
                                    to_screen(rx_max, rz_min),
                                ])
                                painter.save()
                                painter.setPen(QtCore.Qt.NoPen)
                                painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 60, 220, 55)))
                                painter.drawPolygon(fill_poly)
                                painter.restore()
                        for prim in path:
                            if not isinstance(prim, dict):
                                continue
                            ptype = prim.get("type")
                            if ptype == "line":
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                if not p1 or not p2:
                                    continue
                                s1 = to_screen(float(p1[0]), float(p1[1]))
                                s2 = to_screen(float(p2[0]), float(p2[1]))
                                painter.drawLine(QtCore.QLineF(s1, s2))
                            elif ptype == "arc":
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                c = prim.get("c")
                                if not p1 or not p2 or not c:
                                    continue
                                ccw = bool(prim.get("ccw", True))
                                try:
                                    arc_pts = self._sample_arc((float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1])), (float(c[0]), float(c[1])), ccw)
                                except Exception:
                                    arc_pts = []
                                if len(arc_pts) >= 2:
                                    points = [to_screen(x, z) for x, z in arc_pts]
                                    painter.drawPolyline(QtGui.QPolygonF(points))
                        continue
                    else:
                        try:
                            pts = self.primitives_to_points(path)
                        except Exception:
                            pts = []
                        if len(pts) >= 2:
                            points = [to_screen(x, z) for x, z in pts]
                            painter.drawPolyline(QtGui.QPolygonF(points))
                        elif len(pts) == 1:
                            pt = to_screen(pts[0][0], pts[0][1])
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
                    margin = 6
                    header_h = 18
                    row_h = 16
                    line_len = 26
                    box_w = 155

                    legend_items = [
                        ("Kontur", QtGui.QPen(QtGui.QColor(0, 255, 0), 2, QtCore.Qt.SolidLine)),
                        ("Aktiv", QtGui.QPen(QtGui.QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)),
                        ("Rohteil", QtGui.QPen(QtGui.QColor(180, 180, 180), 1, QtCore.Qt.SolidLine)),
                        ("Rückzug", QtGui.QPen(QtGui.QColor(0, 255, 255), 1, QtCore.Qt.DashLine)),
                        ("Schruppkontur", QtGui.QPen(QtGui.QColor(240, 180, 0), 2, QtCore.Qt.DashLine)),
                        ("Freistich", QtGui.QPen(QtGui.QColor(0, 190, 255), 2, QtCore.Qt.SolidLine)),
                        ("Bearbeitungslinie", QtGui.QPen(QtGui.QColor(255, 0, 0), 1, QtCore.Qt.DashLine)),
                        ("Futter-Sperrzone", QtGui.QPen(QtGui.QColor(200, 60, 220), 1, QtCore.Qt.DashDotLine)),
                    ]

                    x0 = margin
                    y0 = margin - 2

                    # Box height: always header, details only if not collapsed
                    if collapsed:
                        box_h = margin * 2 + header_h
                    else:
                        box_h = margin * 2 + header_h + row_h * len(legend_items)

                    bg = QtGui.QColor(0, 0, 0, 160)
                    painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
                    painter.setBrush(QtGui.QBrush(bg))
                    painter.drawRoundedRect(QtCore.QRectF(x0, y0, box_w, box_h), 6, 6)

                    # Click target = header area (always present)
                    self._legend_click_rect = QtCore.QRectF(x0, y0, box_w, header_h + margin)

                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                    painter.setFont(QtGui.QFont("Sans", 8))
                    painter.drawText(
                        QtCore.QRectF(x0 + margin, y0 + 2, box_w - 2 * margin, header_h),
                        QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                        "Legende"
                    )

                    if not collapsed:
                        for i, (label, pen) in enumerate(legend_items):
                            y = y0 + margin + header_h + i * row_h + 10
                            painter.setPen(pen)
                            painter.drawLine(
                                QtCore.QPointF(x0 + margin, y),
                                QtCore.QPointF(x0 + margin + line_len, y)
                            )
                            painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
                            painter.drawText(QtCore.QPointF(x0 + margin + line_len + 6, y + 4), label)

                except Exception:
                    self._legend_click_rect = None

            if getattr(self, "status_messages", None):
                try:
                    messages = list(self.status_messages)[:4]
                    box_h = 12 + (len(messages) * 16)
                    box_w = min(self.width() - 20, 540)
                    x0 = self.width() - box_w - 8
                    y0 = 8
                    painter.setPen(QtGui.QPen(QtGui.QColor(180, 80, 20), 1))
                    painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 240, 210, 220)))
                    painter.drawRoundedRect(QtCore.QRectF(x0, y0, box_w, box_h), 6, 6)
                    painter.setPen(QtGui.QPen(QtGui.QColor(90, 40, 0), 1))
                    painter.drawText(QtCore.QPointF(x0 + 8, y0 + 14), "Warnungen")
                    for idx, msg in enumerate(messages):
                        painter.drawText(QtCore.QPointF(x0 + 8, y0 + 30 + idx * 15), f"- {msg[:80]}")
                except Exception:
                    pass

        except Exception:
            self._legend_click_rect = None
        finally:
            painter.end()
