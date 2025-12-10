"""QtVCP conversational lathe panel with 2D preview and G-code generation."""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from weakref import WeakSet

from qtpy import QtCore, QtGui, QtWidgets
from qtvcp.core import Action


# ----------------------------------------------------------------------
# Operation types
# ----------------------------------------------------------------------
class OpType:
    PROGRAM_HEADER = "program_header"
    FACE = "face"
    CONTOUR = "contour"
    TURN = "turn"
    BORE = "bore"
    THREAD = "thread"
    GROOVE = "groove"
    DRILL = "drill"
    KEYWAY = "keyway"


@dataclass
class Operation:
    op_type: str
    params: Dict[str, float]
    path: List[Tuple[float, float]] = field(default_factory=list)


class ProgramModel:
    def __init__(self):
        self.operations: List[Operation] = []
        self.spindle_speed_max: float = 0.0
        self.program_settings: Dict[str, object] = {}

    def add_operation(self, op: Operation):
        self.operations.append(op)

    def remove_operation(self, index: int):
        if 0 <= index < len(self.operations):
            del self.operations[index]

    def move_up(self, index: int):
        if 1 <= index < len(self.operations):
            self.operations[index - 1], self.operations[index] = \
                self.operations[index], self.operations[index - 1]

    def move_down(self, index: int):
        if 0 <= index < len(self.operations) - 1:
            self.operations[index + 1], self.operations[index] = \
                self.operations[index], self.operations[index + 1]

    def update_geometry(self, op: Operation):
        builder = {
            OpType.FACE: build_face_path,
            OpType.CONTOUR: build_contour_path,
            OpType.THREAD: build_thread_path,
            OpType.GROOVE: build_groove_path,
            OpType.DRILL: build_drill_path,
            OpType.KEYWAY: build_keyway_path,
        }.get(op.op_type)
        if builder:
            op.path = builder(op.params)

    def generate_gcode(self) -> List[str]:
        settings = self.program_settings or {}
        program_name = str(settings.get("program_name") or "").strip()
        npv_code = str(settings.get("npv") or "G54").upper()
        unit = (settings.get("unit") or "").strip().lower()
        unit_code = "G21" if unit.startswith("mm") else ("G20" if unit else "")
        shape = settings.get("shape", "")

        lines: List[str] = ["%", "(Programm automatisch erzeugt)"]
        if program_name:
            lines.append(f"(Programmname: {_sanitize_gcode_text(program_name)})")
        if unit:
            lines.append(f"(Maßeinheit: {unit})")
        if shape:
            lines.append(f"(Rohteilform: {shape})")

        def _fmt(name: str, key: str, suffix: str = ""):
            val = settings.get(key, None)
            if val is None:
                return None
            try:
                if float(val) == 0.0 and key not in ("xi", "zi", "zb", "w", "l", "n_edges", "sw"):
                    return None
            except Exception:
                pass
            return f"({name}: {val}{suffix})"

        for comment in filter(
            None,
            [
                _fmt("XA", "xa", " mm"),
                _fmt("XI", "xi", " mm"),
                _fmt("ZA", "za", " mm"),
                _fmt("ZI", "zi", " mm"),
                _fmt("ZB", "zb", " mm"),
                _fmt("W", "w", " mm"),
                _fmt("L", "l", " mm"),
                _fmt("Kantenanzahl N", "n_edges", ""),
                _fmt("Schlüsselweite SW", "sw", " mm"),
                _fmt("XT", "xt", " mm"),
                _fmt("ZT", "zt", " mm"),
                _fmt("SC", "sc", " mm"),
                _fmt("Rückzug", "retract_mode", ""),
                _fmt("XRA", "xra", " mm"),
                _fmt("XRI", "xri", " mm"),
                _fmt("ZRA", "zra", " mm"),
                _fmt("ZRI", "zri", " mm"),
            ],
        ):
            lines.append(comment)

        # Basiszustand
        lines.append("G18 G7 G90 G40 G80")
        if unit_code:
            lines.append(unit_code)
        # mm/U bzw. in/U entsprechend LinuxCNC-Postprozessor
        lines.append("G95")
        if npv_code:
            lines.append(npv_code)

        # Drehzahlbegrenzung aus Programmkopf (nur als Kommentar)
        s1_max = settings.get("s1_max", 0)
        s3_max = settings.get("s3_max", 0)
        has_sub = bool(settings.get("has_subspindle", False))
        if s1_max:
            lines.append(f"(S1 max = {int(s1_max)} U/min)")
        if has_sub and s3_max:
            lines.append(f"(S3 max = {int(s3_max)} U/min)")
        for idx, op in enumerate(self.operations, start=1):
            lines.append(f"( Operation {idx} )")
            lines.append(f"( {op.op_type.upper()} )")
            lines.extend(gcode_for_operation(op))
        lines.extend(["M9", "M30", "%"])

        # Zeilennummerierung wie im LinuxCNC-Postprozessor: Nur echte G-Code-
        # Zeilen erhalten ein N-Präfix mit einer Schrittweite von 1. Kommentare
        # bleiben unnummeriert, damit die Befehlszeilen bei N10 beginnen.
        numbered: List[str] = []
        n = 10
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped == "%":
                numbered.append(line)
                continue
            if stripped.startswith("("):
                numbered.append(line)
                continue
            numbered.append(f"N{n} {line}")
            n += 1

        # Zeichensatz vereinheitlichen: LinuxCNC erwartet ASCII, daher alle
        # Zeilen transliterieren und unzulässige Zeichen ersetzen.
        sanitized = [_sanitize_gcode_text(line) for line in numbered]

        return sanitized


# ----------------------------------------------------------------------
# Preview widget
# ----------------------------------------------------------------------
class LathePreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paths: List[List[Tuple[float, float]]] = []
        self.active_index: int | None = None
        self.setMinimumHeight(200)
        self._base_span = 10.0  # Default 10x10 mm viewport

    def set_paths(self, paths: List[List[Tuple[float, float]]],
                  active_index: int | None = None):
        self.paths = paths
        self.active_index = active_index
        try:
            print(f"[LathePreview] set_paths count={len(paths)} active={active_index} first={paths[0] if paths else '[]'}")
        except Exception:
            pass
        self.update()

    def paintEvent(self, event):  # type: ignore[override]
        painter = QtGui.QPainter(self)
        try:
            painter.fillRect(self.rect(), QtCore.Qt.black)

            all_points = [p for path in self.paths for p in path if len(path) > 0]
            if not all_points:
                all_points = [(0.0, 0.0)]

            xs = [p[0] for p in all_points]
            zs = [p[1] for p in all_points]
            min_x, max_x = min(xs), max(xs)
            min_z, max_z = min(zs), max(zs)

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

            def to_screen(x_val: float, z_val: float) -> QtCore.QPointF:
                # Z horizontal, X vertikal
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_val - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            # Achsen und Skala (außen: links/unten)
            painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
            axis_x_val = 0.0 if min_x <= 0.0 <= max_x else min_x
            axis_z_val = 0.0 if min_z <= 0.0 <= max_z else min_z
            x_axis = to_screen(axis_x_val, min_z)
            x_axis_end = to_screen(axis_x_val, max_z)
            z_axis = to_screen(min_x, axis_z_val)
            z_axis_end = to_screen(max_x, axis_z_val)
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
                pt = to_screen(axis_x_val, val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 2))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 6, pt.y() + 14), f"{val:.0f}")
                val += step_z

            # X-Ticks (vertikal links/rechts)
            step_x = nice_step(max_x - min_x)
            val = (min_x // step_x) * step_x
            while val <= max_x:
                pt = to_screen(val, axis_z_val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x() - 2, pt.y(), pt.x() + 4, pt.y()))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 28, pt.y() + 4), f"{val:.0f}")
                val += step_x

            # Achsbeschriftungen
            painter.setPen(font_pen)
            painter.drawText(QtCore.QPointF(rect.right() - 20, z_axis.y() - 6), "Z")
            painter.drawText(QtCore.QPointF(x_axis.x() + 6, rect.top() + 12), "X")

            for idx, path in enumerate(self.paths):
                if len(path) < 2:
                    # Einzelpunkt als kleines Kreuz darstellen
                    pt = to_screen(path[0][0], path[0][1])
                    painter.setPen(QtGui.QPen(QtGui.QColor("yellow"), 2))
                    painter.drawLine(QtCore.QLineF(pt.x() - 4, pt.y(), pt.x() + 4, pt.y()))
                    painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 4))
                    continue
                color = QtGui.QColor("lime") if idx != self.active_index else QtGui.QColor("yellow")
                painter.setPen(QtGui.QPen(color, 2))
                points = [to_screen(x, z) for x, z in path]
                painter.drawPolyline(QtGui.QPolygonF(points))
        finally:
            painter.end()


# ----------------------------------------------------------------------
# Simple path builders
# ----------------------------------------------------------------------
def build_face_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    """
    Einfache Kontur für die Vorschau:
    Start-X/Z -> End-X/Z, mit optionaler Fase (Radius wird wie 'keine' behandelt).
    """
    x0 = params.get("start_x", 0.0)
    z0 = params.get("start_z", 0.0)
    x1 = params.get("end_x", x0)
    z1 = params.get("end_z", 0.0)
    edge_type = int(params.get("edge_type", 0))
    edge_size = params.get("edge_size", 0.0)

    path: List[Tuple[float, float]] = []
    path.append((x0, z0))

    if edge_type == 1 and edge_size > 0.0:
        z_fase_start = z1 + edge_size
        path.append((x0, z_fase_start))
        path.append((x0 - edge_size, z1))
        path.append((x1, z1))
    else:
        path.append((x0, z1))
        path.append((x1, z1))

    return path


def build_turn_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    length = params.get("length", 0.0)
    safe_z = params.get("safe_z", 2.0)
    return [
        (x_start, safe_z),
        (x_start, 0.0),
        (x_end, -abs(length)),
    ]


def build_bore_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    depth = -abs(params.get("depth", 0.0))
    safe_z = params.get("safe_z", 2.0)
    return [
        (x_start, safe_z),
        (x_start, 0.0),
        (x_end, depth),
    ]


def build_thread_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    major = params.get("major_diameter", 0.0)
    pitch = params.get("pitch", 1.5)
    length = params.get("length", 0.0)
    passes = max(1, int(params.get("passes", 1)))
    safe_z = params.get("safe_z", 2.0)
    start = (major, safe_z)
    path = [start, (major, 0.0)]
    depth_per_pass = pitch * 0.1
    for i in range(passes):
        x_val = major - depth_per_pass * (i + 1)
        path.append((x_val, -abs(length)))
        if i != passes - 1:
            path.append((x_val, safe_z))
    return path


def build_groove_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    diameter = params.get("diameter", 0.0)
    width = params.get("width", 0.0)
    depth = abs(params.get("depth", 0.0))
    z_pos = params.get("z", 0.0)
    safe_z = params.get("safe_z", 2.0)
    return [
        (diameter, safe_z),
        (diameter, z_pos),
        (diameter - depth, z_pos),
        (diameter - depth, z_pos - width),
        (diameter, z_pos - width),
    ]


def build_drill_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    depth = params.get("depth", 0.0)
    safe_z = params.get("safe_z", 2.0)
    return [
        (0.0, safe_z),
        (0.0, depth),
    ]


def build_keyway_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    mode = int(params.get("mode", 0))
    nut_length = params.get("nut_length", 0.0)
    nut_depth = params.get("nut_depth", 0.0)
    start_dia = params.get("start_x_dia", 0.0)
    start_z = params.get("start_z", 0.0)
    top_clearance = params.get("top_clearance", 1.0)

    if mode == 0:  # axial
        radial_side = int(params.get("radial_side", 0))
        rad_sign = -1 if radial_side == 0 else 1
        top_z = start_z + top_clearance
        bottom_z = start_z - nut_length
        final_dia = start_dia + rad_sign * 2 * nut_depth
        return [
            (start_dia, top_z),
            (start_dia, start_z),
            (final_dia, bottom_z),
        ]

    # face mode
    top_x = start_dia + top_clearance
    inner_x = start_dia - 2 * nut_length
    back_z = start_z - nut_depth
    return [
        (top_x, start_z),
        (inner_x, start_z),
        (inner_x, back_z),
        (top_x, back_z),
    ]


def build_contour_path(params: Dict[str, object]) -> List[Tuple[float, float]]:
    """
    Konturpfad aus der Segmenttabelle:
    - Startpunkt (start_x, start_z)
    - jede Tabellenzeile liefert einen Zielpunkt (X, Z)
    - Kanten (Fase/Radius) werden erst berechnet, sobald ein Folgesegment existiert
    """
    start_x = float(params.get("start_x", 0.0))
    start_z = float(params.get("start_z", 0.0))
    coord_mode_idx = int(params.get("coord_mode", 0))
    incremental = coord_mode_idx == 1  # 0=Absolut, 1=Inkremental
    segments = params.get("segments") or []

    # Roh-Punkte (vor Kantenbearbeitung)
    raw_points: List[Tuple[float, float]] = [(start_x, start_z)]
    raw_meta: List[Dict[str, object]] = []

    cur_x, cur_z = start_x, start_z
    for seg in segments:
        sx = float(seg.get("x", cur_x))
        sz = float(seg.get("z", cur_z))
        x_empty = bool(seg.get("x_empty", False))
        z_empty = bool(seg.get("z_empty", False))
        # 'mode' dient nur als Hinweis; falls eine Koordinate fehlt, bleibt die vorherige
        mode = str(seg.get("mode", "xz")).lower()
        if mode == "x":
            if incremental:
                cur_x = cur_x + sx
            else:
                if not x_empty:
                    cur_x = sx
            # Z bleibt
        elif mode == "z":
            if incremental:
                cur_z = cur_z + sz
            else:
                if not z_empty:
                    cur_z = sz
            # X bleibt
        else:  # xz
            if incremental:
                cur_x = cur_x + sx
                cur_z = cur_z + sz
            else:
                if not x_empty:
                    cur_x = sx
                if not z_empty:
                    cur_z = sz
        raw_points.append((cur_x, cur_z))
        raw_meta.append(
            {
                "edge": str(seg.get("edge", "none")).lower(),
                "edge_size": float(seg.get("edge_size", 0.0) or 0.0),
            }
        )

    if len(raw_points) <= 1:
        return raw_points

    # Kanten/Übergänge anwenden, sobald ein Folgesegment vorhanden ist
    path: List[Tuple[float, float]] = [raw_points[0]]
    for i in range(1, len(raw_points)):
        p_prev = raw_points[i - 1]
        p_curr = raw_points[i]

        edge_info = raw_meta[i - 1] if i - 1 < len(raw_meta) else {}
        edge_type = edge_info.get("edge", "none")
        edge_size = max(float(edge_info.get("edge_size", 0.0) or 0.0), 0.0)
        has_next = i < len(raw_points) - 1

        if edge_type in ("chamfer", "fase", "radius") and edge_size > 0 and has_next:
            p_next = raw_points[i + 1]
            v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
            v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            len1 = math.hypot(*v1)
            len2 = math.hypot(*v2)

            if len1 > 1e-6 and len2 > 1e-6:
                offset = min(edge_size, len1 * 0.499, len2 * 0.499)
                dir1 = (v1[0] / len1, v1[1] / len1)
                dir2 = (v2[0] / len2, v2[1] / len2)

                cut_start = (p_curr[0] - dir1[0] * offset, p_curr[1] - dir1[1] * offset)
                cut_end = (p_curr[0] + dir2[0] * offset, p_curr[1] + dir2[1] * offset)

                path.append(cut_start)
                if edge_type.startswith(("chamfer", "fase")):
                    path.append(cut_end)
                else:  # radius -> einfache Approximation
                    steps = 4
                    for s in range(1, steps):
                        t = s / steps
                        path.append(
                            (
                                cut_start[0] * (1 - t) + cut_end[0] * t,
                                cut_start[1] * (1 - t) + cut_end[1] * t,
                            )
                        )
                    path.append(cut_end)
                continue

        # Standard: direkte Linie übernehmen
        if p_curr != path[-1]:
            path.append(p_curr)

    return path


# ----------------------------------------------------------------------
# G-code helpers
# ----------------------------------------------------------------------
def gcode_from_path(path: List[Tuple[float, float]],
                    feed: float, safe_z: float) -> List[str]:
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


def gcode_for_keyway(op: Operation) -> List[str]:
    p = op.params
    lines = ["(KEYWAY)"]
    lines.append(f"#<_mode> = {int(p.get('mode', 0))}")
    lines.append(f"#<_radial_side> = {int(p.get('radial_side', 0))}")
    lines.append(f"#<_slot_count> = {int(p.get('slot_count', 1))}")
    lines.append(f"#<_slot_start_angle> = {p.get('slot_start_angle', 0.0):.3f}")
    lines.append(f"#<_start_x_dia_input> = {p.get('start_x_dia', 0.0):.3f}")
    lines.append(f"#<_start_z_input> = {p.get('start_z', 0.0):.3f}")
    lines.append(f"#<_nut_length> = {p.get('nut_length', 0.0):.3f}")
    lines.append(f"#<_nut_depth> = {p.get('nut_depth', 0.0):.3f}")
    lines.append(f"#<_depth_per_pass> = {p.get('depth_per_pass', 0.1):.3f}")
    lines.append(f"#<_top_clearance> = {p.get('top_clearance', 0.0):.3f}")
    lines.append(f"#<_plunge_feed> = {p.get('plunge_feed', 200.0):.3f}")
    lines.append(f"#<_use_c_axis> = {1 if p.get('use_c_axis', True) else 0}")
    lines.append(f"#<_use_c_axis_switch> = {1 if p.get('use_c_axis_switch', True) else 0}")
    lines.append(f"#<_c_axis_switch_p> = {int(p.get('c_axis_switch_p', 0))}")
    lines.append("o<keyway_c> call")
    return lines


def _sanitize_gcode_text(text: str) -> str:
    """Ersetzt Umlaute/Akzente durch ASCII, um falsche Zeichensätze zu vermeiden."""
    translit = {
        "ä": "ae",
        "Ä": "Ae",
        "ö": "oe",
        "Ö": "Oe",
        "ü": "ue",
        "Ü": "Ue",
        "ß": "ss",
    }

    for src, repl in translit.items():
        text = text.replace(src, repl)

    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "replace").decode("ascii")


def gcode_for_contour(op: Operation) -> List[str]:
    """Kontur nur als Kommentar anhängen, damit kein Fahrbefehl entsteht."""
    p = op.params
    lines: List[str] = ["(KONTUR)"]

    name = str(p.get("name") or "").strip()
    if name:
        lines.append(f"(Name: {name})")

    side_idx = int(p.get("side", 0))
    lines.append("(Seite: Außen)" if side_idx == 0 else "(Seite: Innen)")

    # Punkte als reine Information (keine G0/G1-Befehle)
    for idx, (x, z) in enumerate(op.path, start=1):
        lines.append(f"(P{idx}: X={x:.3f} Z={z:.3f})")

    segments = p.get("segments") or []
    for i, seg in enumerate(segments, start=1):
        edge = seg.get("edge", "none")
        edge_size = float(seg.get("edge_size", 0.0))
        if edge != "none" and edge_size > 0.0:
            lines.append(f"(Segment {i}: Kante={edge}, Maß={edge_size:.3f})")

    return lines


def gcode_for_face(op: Operation) -> List[str]:
    """G-Code für Planen mit Schruppen/Schlichten und optionaler Fase."""
    p = op.params

    x0 = p.get("start_x", 0.0)
    z0 = p.get("start_z", 0.0)
    x1 = p.get("end_x", x0)
    z1 = p.get("end_z", 0.0)

    safe_z = p.get("safe_z", z0 + 2.0)
    feed = p.get("feed", 0.2)

    depth_per_pass = float(p.get("depth_per_pass", 0.0))
    depth_max = float(p.get("depth_max", 0.0))
    depth_total = abs(z0 - z1)

    # effektive Zustellung pro Schnitt: bevorzugt depth_per_pass, sonst depth_max,
    # immer gedeckelt auf die tatsächlich abzunehmende Tiefe. Anschließend wird
    # die Zustellung auf gleichmäßige Schritte verteilt, damit der letzte Hub
    # nicht deutlich kleiner ausfällt.
    desired_depth = depth_per_pass if depth_per_pass > 0 else depth_max
    if desired_depth <= 0.0:
        desired_depth = depth_total
    desired_depth = max(min(desired_depth, depth_total), 0.0)

    finish_allow_x = max(p.get("finish_allow_x", 0.0), 0.0)
    finish_allow_z = max(p.get("finish_allow_z", 0.0), 0.0)
    finish_dir = int(p.get("finish_direction", 0))  # 0=Außen→Innen, 1=Innen→Außen

    # gleichmäßige Verteilung der Zustellungen über die gesamte Schruppstrecke
    if z1 < z0:
        z_limit_rough = z1 + finish_allow_z
    else:
        z_limit_rough = z1 - finish_allow_z
    total_rough_depth = abs(z0 - z_limit_rough)
    rough_passes = max(1, math.ceil(total_rough_depth / desired_depth)) if total_rough_depth > 0 else 0
    depth = total_rough_depth / rough_passes if rough_passes > 0 else 0.0

    mode_idx = int(p.get("mode", 0))  # 0=Schruppen, 1=Schlichten, 2=Schruppen+Schlichten (fallback)
    edge_type = int(p.get("edge_type", 0))  # 0=keine, 1=Fase, 2=Radius (wie keine)
    edge_size = max(p.get("edge_size", 0.0), 0.0)
    spindle = p.get("spindle", 0.0)
    coolant_enabled = bool(p.get("coolant", False))

    tool_num = int(p.get("tool", 0))

    lines: List[str] = []

    if tool_num > 0:
        lines.append(f"(Werkzeug T{tool_num:02d})")
        lines.append(f"T{tool_num:02d} M6")

    # lokale Drehzahl, falls gesetzt
    if spindle and spindle > 0:
        lines.append(f"S{int(spindle)} M3")

    if coolant_enabled:
        lines.append("M8")

    # -------------------------
    # 1) Schruppen (Z-Schritte, Bewegung in X)
    # -------------------------
    do_rough = mode_idx in (0, 2)
    do_finish = mode_idx in (1, 2)

    if do_rough and depth > 0.0 and abs(z0 - z1) > finish_allow_z:
        if z1 < z0:
            dz = -depth
            z_limit_rough = z1 + finish_allow_z
            cmp = lambda z: z > z_limit_rough + 1e-4
        else:
            dz = depth
            z_limit_rough = z1 - finish_allow_z
            cmp = lambda z: z < z_limit_rough - 1e-4

        if x1 < x0:
            x_limit_rough = x1 + finish_allow_x
        else:
            x_limit_rough = x1 - finish_allow_x

        z_curr = z0
        for _ in range(rough_passes):
            z_next = z_curr + dz
            if dz < 0 and z_next < z_limit_rough:
                z_next = z_limit_rough
            elif dz > 0 and z_next > z_limit_rough:
                z_next = z_limit_rough

            lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
            lines.append(f"G0 Z{z_next:.3f}")
            lines.append(f"G1 X{x_limit_rough:.3f} F{feed:.3f}")
            lines.append(f"G0 Z{safe_z:.3f}")

            z_curr = z_next

    # -------------------------
    # 2) Schlichten
    # -------------------------
    if do_finish:
        lines.append("(Schlichtschnitt Plan)")

        x_outside = max(x0, x1)
        x_inside = min(x0, x1)
        start_finish_x = x_outside if finish_dir == 0 else x_inside
        end_finish_x = x_inside if finish_dir == 0 else x_outside

        lines.append(f"G0 X{start_finish_x:.3f} Z{safe_z:.3f}")

        if edge_type == 1 and edge_size > 0.0:
            if finish_dir == 0:
                z_fase_start = z1 + edge_size
                lines.append(f"G0 Z{z_fase_start:.3f}")
                lines.append(f"G1 X{(x_outside - edge_size):.3f} Z{z1:.3f} F{feed:.3f}")
                lines.append(f"G1 X{end_finish_x:.3f} Z{z1:.3f}")
            else:
                z_fase_end = z1 + edge_size
                lines.append(f"G0 Z{z1:.3f}")
                lines.append(f"G1 X{(x_outside - edge_size):.3f} F{feed:.3f}")
                lines.append(f"G1 X{x_outside:.3f} Z{z_fase_end:.3f}")
        else:
            lines.append(f"G0 Z{z1:.3f}")
            lines.append(f"G1 X{end_finish_x:.3f} F{feed:.3f}")

        lines.append(f"G0 Z{safe_z:.3f}")

    if coolant_enabled:
        lines.append("M9")

    return lines


def gcode_for_operation(op: Operation) -> List[str]:
    if op.op_type == OpType.PROGRAM_HEADER:
        # Programmkopf wird zentral in ProgramModel.generate_gcode() behandelt
        return []
    if op.op_type == OpType.FACE:
        return gcode_for_face(op)
    if op.op_type == OpType.CONTOUR:
        return gcode_for_contour(op)
    if op.op_type == OpType.TURN:
        return gcode_from_path(op.path,
                               op.params.get("feed", 0.2),
                               op.params.get("safe_z", 2.0))
    if op.op_type == OpType.BORE:
        return gcode_from_path(op.path,
                               op.params.get("feed", 0.15),
                               op.params.get("safe_z", 2.0))
    if op.op_type == OpType.DRILL:
        return gcode_from_path(op.path,
                               op.params.get("feed", 0.12),
                               op.params.get("safe_z", 2.0))
    if op.op_type == OpType.GROOVE:
        return gcode_from_path(op.path,
                               op.params.get("feed", 0.15),
                               op.params.get("safe_z", 2.0))
    if op.op_type == OpType.THREAD:
        safe_z = op.params.get("safe_z", 2.0)
        major_diameter = op.params.get("major_diameter", 0.0)
        pitch = op.params.get("pitch", 1.5)
        length = op.params.get("length", 0.0)
        spring_passes = max(0, int(op.params.get("passes", 1)))

        thread_depth = pitch * 0.6134
        initial_depth = max(thread_depth * 0.1, pitch * 0.05)
        peak_offset = -max(thread_depth * 0.5, pitch * 0.25)

        return [
            f"G0 X{major_diameter:.3f} Z{safe_z:.3f}",
            (
                "G76 "
                f"P{pitch:.4f} "
                f"Z{-abs(length):.3f} "
                f"I{peak_offset:.4f} "
                f"J{initial_depth:.4f} "
                "R1.5 "
                f"K{thread_depth:.4f} "
                "Q29.5 "
                f"H{spring_passes:d} "
                "E0.0 L0"
            ),
        ]
    if op.op_type == OpType.KEYWAY:
        return gcode_for_keyway(op)
    return []


# ----------------------------------------------------------------------
# Handler
# ----------------------------------------------------------------------
class HandlerClass:
    def __init__(self, halcomp, widgets, paths):
        self.hal = halcomp
        self.w = widgets
        self.paths = paths
        self.model = ProgramModel()
        self._connected_param_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()
        self._connected_global_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()

        # zentrale Widgets
        self.preview = getattr(self.w, "previewWidget", None)
        self.contour_preview = getattr(self.w, "contourPreview", None)
        self.list_ops = getattr(self.w, "listOperations", None)
        self.tab_params = getattr(self.w, "tabParams", None)

        self.btn_add = getattr(self.w, "btnAdd", None)
        self.btn_delete = getattr(self.w, "btnDelete", None)
        self.btn_move_up = getattr(self.w, "btnMoveUp", None)
        self.btn_move_down = getattr(self.w, "btnMoveDown", None)
        self.btn_new_program = getattr(self.w, "btnNewProgram", None)
        self.btn_generate = getattr(self.w, "btnGenerate", None)

        # Programm-Tab
        self.tab_program = getattr(self.w, "tabProgram", None)
        self.program_unit = getattr(self.w, "program_unit", None)
        self.program_shape = getattr(self.w, "program_shape", None)
        self.program_retract_mode = getattr(self.w, "program_retract_mode", None)
        self.program_has_subspindle = getattr(self.w, "program_has_subspindle", None)

        # Root-Widget des Panels (für globale Suche nach Labels/Spinboxen)
        self.root_widget = self._find_root_widget()

        # falls das Objekt in der .ui anders heißt: automatisch finden
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()

        self.program_xa = getattr(self.w, "program_xa", None)
        self.program_xi = getattr(self.w, "program_xi", None)
        self.label_prog_xi = getattr(self.w, "label_prog_xi", None)
        self.program_za = getattr(self.w, "program_za", None)
        self.program_zi = getattr(self.w, "program_zi", None)
        self.program_zb = getattr(self.w, "program_zb", None)
        self.program_w = getattr(self.w, "program_w", None)
        self.label_prog_w = getattr(self.w, "label_prog_w", None)
        self.program_l = getattr(self.w, "program_l", None)
        self.label_prog_l = getattr(self.w, "label_prog_l", None)
        self.program_n = getattr(self.w, "program_n", None)
        self.label_prog_n = getattr(self.w, "label_prog_n", None)
        self.program_sw = getattr(self.w, "program_sw", None)
        self.label_prog_sw = getattr(self.w, "label_prog_sw", None)
        self.program_xt = getattr(self.w, "program_xt", None)
        self.program_zt = getattr(self.w, "program_zt", None)
        self.program_sc = getattr(self.w, "program_sc", None)

        self.program_name = getattr(self.w, "program_name", None)

        self.program_xra = getattr(self.w, "program_xra", None)
        self.label_prog_xra = getattr(self.w, "label_prog_xra", None)
        self.program_xri = getattr(self.w, "program_xri", None)
        self.label_prog_xri = getattr(self.w, "label_prog_xri", None)
        self.program_zra = getattr(self.w, "program_zra", None)
        self.label_prog_zra = getattr(self.w, "label_prog_zra", None)
        self.program_zri = getattr(self.w, "program_zri", None)
        self.label_prog_zri = getattr(self.w, "label_prog_zri", None)

        self.program_s1 = getattr(self.w, "program_s1", None)
        self.label_prog_s1 = getattr(self.w, "label_prog_s1", None)
        self.program_s3 = getattr(self.w, "program_s3", None)
        self.label_prog_s3 = getattr(self.w, "label_prog_s3", None)

        # optionale globale Felder (falls du sie später in der UI ergänzt)
        self.program_spindle = getattr(self.w, "program_spindle_speed", None)
        self.program_tool = getattr(self.w, "program_tool", None)
        self.program_npv = getattr(self.w, "program_npv", None)

        # Planen-spezifische Optionen
        self.face_mode = getattr(self.w, "face_mode", None)
        self.face_edge_type = getattr(self.w, "face_edge_type", None)
        self.label_face_edge_size = getattr(self.w, "label_face_edge_size", None)
        self.face_edge_size = getattr(self.w, "face_edge_size", None)
        self.label_face_finish_allow_x = getattr(self.w, "label_face_finish_allow_x", None)
        self.face_finish_allow_x = getattr(self.w, "face_finish_allow_x", None)
        self.label_face_finish_allow_z = getattr(self.w, "label_face_finish_allow_z", None)
        self.face_finish_allow_z = getattr(self.w, "face_finish_allow_z", None)
        self.label_face_depth_max = getattr(self.w, "label_face_depth_max", None)
        self.face_depth_max = getattr(self.w, "face_depth_max", None)

        # Kontur-Widgets
        self.contour_side = getattr(self.w, "contour_side", None)
        self.contour_start_x = getattr(self.w, "contour_start_x", None)
        self.contour_start_z = getattr(self.w, "contour_start_z", None)
        self.contour_name = getattr(self.w, "contour_name", None)
        self.contour_segments = getattr(self.w, "contour_segments", None)
        self.contour_add_segment = getattr(self.w, "contour_add_segment", None)
        self.contour_delete_segment = getattr(self.w, "contour_delete_segment", None)
        self.contour_move_up = getattr(self.w, "contour_move_up", None)
        self.contour_move_down = getattr(self.w, "contour_move_down", None)
        self.contour_edge_type = getattr(self.w, "contour_edge_type", None)
        self.label_contour_edge_size = getattr(self.w, "label_contour_edge_size", None)
        self.contour_edge_size = getattr(self.w, "contour_edge_size", None)
        self._contour_edge_template_text = "Keine"
        self._contour_edge_template_size = 0.0
        self._contour_row_user_selected = False
        self._op_row_user_selected = False

        # Parameter-Widgets für jede Operation
        self._setup_param_maps()
        self._connect_signals()
        self._connect_contour_signals()
        self._apply_unit_suffix()
        self._update_program_visibility()
        self._refresh_preview()
        self._ensure_core_widgets()

        # letzter bekannter Einheiten-Index für Polling
        self._unit_last_index = (
            self.program_unit.currentIndex() if self.program_unit else -1
        )

    # ---- interne Helfer zur Widget-Suche ------------------------------
    def _find_root_widget(self):
        """Beliebiges Widget aus self.w nehmen und dessen window() als Root verwenden."""
        for name in dir(self.w):
            if name.startswith("_"):
                continue
            try:
                obj = getattr(self.w, name)
            except AttributeError:
                continue
            if isinstance(obj, QtWidgets.QWidget):
                return obj.window()
        app = QtWidgets.QApplication.instance()
        if app:
            # bevorzugt das Panel selbst, sonst erstes Toplevel
            for widget in app.topLevelWidgets():
                if isinstance(widget, QtWidgets.QWidget):
                    if widget.objectName() == "LatheConversationalPanel":
                        return widget
                    if widget.window() == widget:
                        return widget
        return None

    def _find_unit_combo(self):
        """ComboBox mit Einträgen 'mm' und 'inch' direkt in self.w suchen."""
        for name in dir(self.w):
            if name.startswith("_"):
                continue
            try:
                obj = getattr(self.w, name)
            except AttributeError:
                continue

            if not isinstance(obj, QtWidgets.QComboBox):
                continue

            texts = [obj.itemText(i).strip().lower() for i in range(obj.count())]
            if "mm" in texts and "inch" in texts:
                print(f"[LatheEasyStep] using '{name}' as program_unit combo")
                return obj

        print("[LatheEasyStep] no unit combo found via widgets")
        return None

    def _find_shape_combo(self):
        """ComboBox für Rohteilform (Zylinder/Rohr/Rechteck/N-Eck) im ganzen Fenster suchen."""
        # Root-Widget holen
        root = self.root_widget or self._find_root_widget()
        if root is None:
            print("[LatheEasyStep] _find_shape_combo: no root_widget")
            return None

        for combo in root.findChildren(QtWidgets.QComboBox):
            texts = [combo.itemText(i).strip().lower() for i in range(combo.count())]
            print(f"[LatheEasyStep] shape combo candidate {combo.objectName()}: {texts}")
            if any(t in texts for t in ("zylinder", "rohr", "rechteck", "n-eck")):
                print(f"[LatheEasyStep] using '{combo.objectName()}' as program_shape combo")
                return combo

        print("[LatheEasyStep] no shape combo found in tree")
        return None

    def _get_widget_by_name(self, name: str) -> QtWidgets.QWidget | None:
        """Besorgt Widgets robuster: erst direct Attribute, dann UI-Baum."""

        widget = getattr(self.w, name, None)
        if widget:
            return widget

        root = self.root_widget or self._find_root_widget()
        if root:
            widget = root.findChild(QtWidgets.QWidget, name)
        return widget

    # ---- QtVCP lifecycle ---------------------------------------------
    def initialized__(self):
        """Wird aufgerufen, wenn QtVCP die UI komplett aufgebaut hat."""
        # Jetzt ist das Widget-Hierarchie sicher fertig -> Combos suchen

        # Einheiten-Combo sicherstellen
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()

        # Rohteilform-Combo sicherstellen
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()

        # Gegenspindel-Checkbox und S3-Felder sicherstellen
        root = self.root_widget or self._find_root_widget()
        if self.program_has_subspindle is None and root:
            self.program_has_subspindle = root.findChild(QtWidgets.QCheckBox, "program_has_subspindle")
        if self.label_prog_s3 is None and root:
            self.label_prog_s3 = root.findChild(QtWidgets.QWidget, "label_prog_s3")
        if self.program_s3 is None and root:
            self.program_s3 = root.findChild(QtWidgets.QWidget, "program_s3")

        # Rückzug-Combo sicherstellen
        if self.program_retract_mode is None:
            # 1. Versuch: direkt über widgets-Proxy
            self.program_retract_mode = getattr(self.w, "program_retract_mode", None)

        if self.program_retract_mode is None:
            # 2. Versuch: im Widget-Baum suchen
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                for combo in root.findChildren(QtWidgets.QComboBox):
                    if combo.objectName() == "program_retract_mode":
                        self.program_retract_mode = combo
                        break

        if self.program_retract_mode:
            items = [self.program_retract_mode.itemText(i) for i in range(self.program_retract_mode.count())]
            print(
                f"[LatheEasyStep] retract combo found: "
                f"{self.program_retract_mode.objectName()}, "
                f"items={items}, "
                f"current='{self.program_retract_mode.currentText()}'"
            )
            # Signal hier (spät) sicher verbinden
            self.program_retract_mode.currentIndexChanged.connect(self._handle_global_change)
        else:
            print("[LatheEasyStep] initialized__: no program_retract_mode combo found")

        # falls wir die Rohteilform-Combo jetzt haben: Signal anschließen
        if self.program_shape:
            self.program_shape.currentIndexChanged.connect(self._handle_global_change)

        # falls Gegenspindel-Checkbox jetzt vorhanden: Signal anschließen
        if self.program_has_subspindle:
            self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)

        # Planen-Combos sicherstellen (für Sichtbarkeitsschaltung)
        if self.face_mode is None and root:
            self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
        if self.face_edge_type is None and root:
            self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")
        if self.face_mode:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
        if self.face_edge_type:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)

        # Kontur-Widgets sicherstellen
        if self.contour_side is None and root:
            self.contour_side = root.findChild(QtWidgets.QComboBox, "contour_side")
        if self.contour_start_x is None and root:
            self.contour_start_x = root.findChild(QtWidgets.QDoubleSpinBox, "contour_start_x")
        if self.contour_start_z is None and root:
            self.contour_start_z = root.findChild(QtWidgets.QDoubleSpinBox, "contour_start_z")
        if self.contour_name is None and root:
            self.contour_name = root.findChild(QtWidgets.QLineEdit, "contour_name")
        if self.contour_segments is None and root:
            self.contour_segments = root.findChild(QtWidgets.QTableWidget, "contour_segments")
        if self.contour_add_segment is None and root:
            self.contour_add_segment = root.findChild(QtWidgets.QPushButton, "contour_add_segment")
        if self.contour_delete_segment is None and root:
            self.contour_delete_segment = root.findChild(QtWidgets.QPushButton, "contour_delete_segment")
        if self.contour_move_up is None and root:
            self.contour_move_up = root.findChild(QtWidgets.QPushButton, "contour_move_up")
        if self.contour_move_down is None and root:
            self.contour_move_down = root.findChild(QtWidgets.QPushButton, "contour_move_down")
        if self.contour_edge_type is None and root:
            self.contour_edge_type = root.findChild(QtWidgets.QComboBox, "contour_edge_type")
        if self.label_contour_edge_size is None and root:
            self.label_contour_edge_size = root.findChild(QtWidgets.QLabel, "label_contour_edge_size")
        if self.contour_edge_size is None and root:
            self.contour_edge_size = root.findChild(QtWidgets.QDoubleSpinBox, "contour_edge_size")

        self._connect_contour_signals()

        # Gegenspindel-Checkbox sicherstellen
        if self.program_has_subspindle is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.program_has_subspindle = root.findChild(QtWidgets.QCheckBox, "program_has_subspindle")
        if self.program_has_subspindle:
            self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)

        # Planen-Combos sicherstellen
        if self.face_mode is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
        if self.face_edge_type is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")

        if self.face_mode:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
        if self.face_edge_type:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)

        # einmal initial anwenden
        QtCore.QTimer.singleShot(0, self._apply_unit_suffix)
        QtCore.QTimer.singleShot(0, self._update_program_visibility)
        QtCore.QTimer.singleShot(0, self._update_retract_visibility)
        QtCore.QTimer.singleShot(0, self._update_subspindle_visibility)
        QtCore.QTimer.singleShot(0, self._update_face_visibility)
        # Kontur-Tab initial vorbereiten (Spalten/Leerzeile optional)
        QtCore.QTimer.singleShot(0, self._init_contour_table)
        QtCore.QTimer.singleShot(0, self._sync_contour_edge_controls)
        QtCore.QTimer.singleShot(0, self._update_contour_preview_temp)

        # Polling-Timer für die Einheit (mm/inch),
        # falls das Qt-Signal aus irgendeinem Grund nicht feuert
        if self.program_unit:
            self._unit_last_index = self.program_unit.currentIndex()
            self._unit_timer = QtCore.QTimer(self.root_widget or None)
            self._unit_timer.setInterval(200)  # alle 200 ms prüfen
            self._unit_timer.timeout.connect(self._check_unit_change)
            self._unit_timer.start()
            print("[LatheEasyStep] unit polling timer started")
        else:
            print("[LatheEasyStep] initialized__: still no unit combo")

        # Jetzt sicherstellen, dass die Preview-Widgets referenziert sind
        self._ensure_preview_widgets()
        self._refresh_preview()
        # Buttons/Liste sicher verbinden (falls erst jetzt gefunden)
        self._connect_signals()
        try:
            print(f"[LatheEasyStep] core widgets: list_ops={self.list_ops}, btn_add={self.btn_add}, btn_delete={self.btn_delete}")
        except Exception:
            pass
        # Finaler Versuch nach vollständigem UI-Aufbau
        self._ensure_core_widgets()
        self._connect_signals()
        self._debug_widget_names()
        QtCore.QTimer.singleShot(0, self._finalize_ui_ready)

    def _finalize_ui_ready(self):
        """Nach dem ersten Eventloop-Tick erneut nach Widgets suchen und verbinden."""
        self._ensure_core_widgets()
        self._setup_param_maps()
        self._connect_signals()
        self._debug_widget_names()

    def _debug_widget_names(self):
        """Debug-Ausgabe: vorhandene Buttons/ListWidgets im Baum."""
        root = self.root_widget or self._find_root_widget()
        if root is None:
            print("[LatheEasyStep] debug: no root widget")
            return
        btns = [w.objectName() for w in root.findChildren(QtWidgets.QPushButton)]
        lists = [w.objectName() for w in root.findChildren(QtWidgets.QListWidget)]
        print(f"[LatheEasyStep] debug root: {root.objectName()}")
        print(f"[LatheEasyStep] debug buttons: {btns}")
        print(f"[LatheEasyStep] debug list widgets: {lists}")

    def _connect_button_once(self, button, handler, flag_name: str):
        """Verbindet Buttons nur einmal, egal wie oft _connect_signals aufgerufen wird."""
        if button and not getattr(self, flag_name, False):
            button.clicked.connect(handler)
            setattr(self, flag_name, True)

    def _ensure_core_widgets(self):
        """Sucht fehlende Kern-Widgets (Liste/Buttons/Tabs) im UI-Baum nach."""
        root = (
            self.root_widget
            or (self.program_unit.window() if self.program_unit else None)
            or (self.preview.window() if self.preview else None)
            or self._find_root_widget()
        )
        if root is None:
            return
        self.root_widget = self.root_widget or root

        # Direkt nach bekannten Namen suchen (Fallback: QWidget, falls Typ nicht passt)
        def _find(name: str, cls):
            current = getattr(self, name, None)
            if current:
                return current
            obj_name = (
                "listOperations" if name == "list_ops" else
                "tabParams" if name == "tab_params" else
                "btnAdd" if name == "btn_add" else
                "btnDelete" if name == "btn_delete" else
                "btnMoveUp" if name == "btn_move_up" else
                "btnMoveDown" if name == "btn_move_down" else
                "btnNewProgram" if name == "btn_new_program" else
                "btnGenerate" if name == "btn_generate" else name
            )
            obj = root.findChild(cls, obj_name)
            if obj is None:
                obj = root.findChild(QtCore.QObject, obj_name)
            if obj is None:
                obj = root.findChild(QtWidgets.QWidget, obj_name)
            if obj:
                setattr(self, name, obj)
            return getattr(self, name, None)

        self.list_ops = _find("list_ops", QtWidgets.QListWidget)
        self.tab_params = _find("tab_params", QtWidgets.QTabWidget)
        self.btn_add = _find("btn_add", QtWidgets.QPushButton)
        self.btn_delete = _find("btn_delete", QtWidgets.QPushButton)
        self.btn_move_up = _find("btn_move_up", QtWidgets.QPushButton)
        self.btn_move_down = _find("btn_move_down", QtWidgets.QPushButton)
        self.btn_new_program = _find("btn_new_program", QtWidgets.QPushButton)
        self.btn_generate = _find("btn_generate", QtWidgets.QPushButton)

        # Fallbacks, falls die Typ-Suche scheitert
        if self.list_ops is None:
            candidates = root.findChildren(QtWidgets.QListWidget) or root.findChildren(QtWidgets.QWidget)
            if candidates:
                self.list_ops = candidates[0]
        if self.tab_params is None:
            candidates = root.findChildren(QtWidgets.QTabWidget)
            if candidates:
                self.tab_params = candidates[0]

        # Falls wir erst jetzt Buttons gefunden haben: Signale verbinden
        self._connect_button_once(self.btn_add, self._handle_add_operation, "_btn_add_connected")
        self._connect_button_once(self.btn_delete, self._handle_delete_operation, "_btn_delete_connected")
        self._connect_button_once(self.btn_move_up, self._handle_move_up, "_btn_move_up_connected")
        self._connect_button_once(self.btn_move_down, self._handle_move_down, "_btn_move_down_connected")
        self._connect_button_once(self.btn_new_program, self._handle_new_program, "_btn_new_program_connected")
        self._connect_button_once(self.btn_generate, self._handle_generate_gcode, "_btn_generate_connected")

    def _check_unit_change(self):
        """Pollt die Einheit-Combo und triggert _apply_unit_suffix() bei Änderung."""
        if self.program_unit is None:
            return

        idx = self.program_unit.currentIndex()
        if idx != self._unit_last_index:
            self._unit_last_index = idx
            print(f"[LatheEasyStep] unit changed (poll) idx={idx}")
            self._apply_unit_suffix()
            self._update_program_visibility()
            self._update_retract_visibility()
            self._update_subspindle_visibility()
            self._update_face_visibility()

    # ---- Parameter-Mapping --------------------------------------------
    def _setup_param_maps(self):
        self.param_widgets: Dict[str, Dict[str, QtWidgets.QWidget]] = {
            OpType.FACE: {
                "tool": self._get_widget_by_name("face_tool"),
                "start_x": self._get_widget_by_name("face_start_x"),
                "start_z": self._get_widget_by_name("face_start_z"),
                "end_x": self._get_widget_by_name("face_end_x"),
                "end_z": self._get_widget_by_name("face_end_z"),
                "safe_z": self._get_widget_by_name("face_safe_z"),
                "feed": self._get_widget_by_name("face_feed"),
                "depth_per_pass": self._get_widget_by_name("face_depth_per_pass"),
                "finish_allow_x": self._get_widget_by_name("face_finish_allow_x"),
                "finish_allow_z": self._get_widget_by_name("face_finish_allow_z"),
                "finish_direction": self._get_widget_by_name("face_finish_direction"),
                "depth_max": self._get_widget_by_name("face_depth_max"),
                "mode": self._get_widget_by_name("face_mode"),
                "edge_type": self._get_widget_by_name("face_edge_type"),
                "edge_size": self._get_widget_by_name("face_edge_size"),
                "spindle": self._get_widget_by_name("face_spindle"),
                "coolant": self._get_widget_by_name("face_coolant"),
            },
            OpType.CONTOUR: {
                "side": self._get_widget_by_name("contour_side"),
                "start_x": self._get_widget_by_name("contour_start_x"),
                "start_z": self._get_widget_by_name("contour_start_z"),
                "coord_mode": self._get_widget_by_name("contour_coord_mode"),
            },
            OpType.THREAD: {
                "major_diameter": self._get_widget_by_name("thread_major_diameter"),
                "pitch": self._get_widget_by_name("thread_pitch"),
                "length": self._get_widget_by_name("thread_length"),
                "passes": self._get_widget_by_name("thread_passes"),
                "safe_z": self._get_widget_by_name("thread_safe_z"),
            },
            OpType.GROOVE: {
                "diameter": self._get_widget_by_name("groove_diameter"),
                "width": self._get_widget_by_name("groove_width"),
                "depth": self._get_widget_by_name("groove_depth"),
                "z": self._get_widget_by_name("groove_z"),
                "feed": self._get_widget_by_name("groove_feed"),
                "safe_z": self._get_widget_by_name("groove_safe_z"),
            },
            OpType.DRILL: {
                "diameter": self._get_widget_by_name("drill_diameter"),
                "depth": self._get_widget_by_name("drill_depth"),
                "feed": self._get_widget_by_name("drill_feed"),
                "safe_z": self._get_widget_by_name("drill_safe_z"),
            },
            OpType.KEYWAY: {
                "mode": self._get_widget_by_name("key_mode"),
                "radial_side": self._get_widget_by_name("key_radial_side"),
                "slot_count": self._get_widget_by_name("key_slot_count"),
                "slot_start_angle": self._get_widget_by_name("key_slot_start_angle"),
                "start_x_dia": self._get_widget_by_name("key_start_diameter"),
                "start_z": self._get_widget_by_name("key_start_z"),
                "nut_length": self._get_widget_by_name("key_nut_length"),
                "nut_depth": self._get_widget_by_name("key_nut_depth"),
                "top_clearance": self._get_widget_by_name("key_top_clearance"),
                "depth_per_pass": self._get_widget_by_name("key_depth_per_pass"),
                "plunge_feed": self._get_widget_by_name("key_plunge_feed"),
                "use_c_axis": self._get_widget_by_name("key_use_c_axis"),
                "use_c_axis_switch": self._get_widget_by_name("key_use_c_axis_switch"),
                "c_axis_switch_p": self._get_widget_by_name("key_c_axis_switch_p"),
            },
        }

    # ---- Signalanschlüsse ---------------------------------------------
    def _connect_signals(self):
        self._connect_button_once(self.btn_add, self._handle_add_operation, "_btn_add_connected")
        self._connect_button_once(self.btn_delete, self._handle_delete_operation, "_btn_delete_connected")
        self._connect_button_once(self.btn_move_up, self._handle_move_up, "_btn_move_up_connected")
        self._connect_button_once(self.btn_move_down, self._handle_move_down, "_btn_move_down_connected")
        self._connect_button_once(self.btn_new_program, self._handle_new_program, "_btn_new_program_connected")
        self._connect_button_once(self.btn_generate, self._handle_generate_gcode, "_btn_generate_connected")
        if self.list_ops and not getattr(self, "_list_ops_connected", False):
            self.list_ops.currentRowChanged.connect(self._handle_selection_change)
            self._list_ops_connected = True
        if self.list_ops and not getattr(self, "_list_ops_click_connected", False):
            self.list_ops.clicked.connect(self._mark_operation_user_selected)
            self._list_ops_click_connected = True

        # Parameterfelder
        for widgets in self.param_widgets.values():
            for widget in widgets.values():
                if widget is None:
                    continue
                if widget in self._connected_param_widgets:
                    continue
                if isinstance(widget, QtWidgets.QComboBox):
                    widget.currentIndexChanged.connect(self._handle_param_change)
                elif isinstance(widget, QtWidgets.QAbstractButton):
                    widget.toggled.connect(self._handle_param_change)
                else:
                    widget.valueChanged.connect(self._handle_param_change)
                self._connected_param_widgets.add(widget)

        # Form-Logik (Einheiten / Rohteilform / Rückzug)
        if self.program_unit and self.program_unit not in self._connected_global_widgets:
            self.program_unit.currentIndexChanged.connect(self._handle_global_change)
            self._connected_global_widgets.add(self.program_unit)
        if self.program_shape and self.program_shape not in self._connected_global_widgets:
            self.program_shape.currentIndexChanged.connect(self._handle_global_change)
            self._connected_global_widgets.add(self.program_shape)
        if self.program_retract_mode and self.program_retract_mode not in self._connected_global_widgets:
            self.program_retract_mode.currentIndexChanged.connect(self._handle_global_change)
            self._connected_global_widgets.add(self.program_retract_mode)
        if self.program_has_subspindle and self.program_has_subspindle not in self._connected_global_widgets:
            self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)
            self._connected_global_widgets.add(self.program_has_subspindle)

        # Planen-spezifische Logik
        if getattr(self, "face_mode", None) and self.face_mode not in self._connected_param_widgets:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
            self._connected_param_widgets.add(self.face_mode)
        if getattr(self, "face_edge_type", None) and self.face_edge_type not in self._connected_param_widgets:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)
            self._connected_param_widgets.add(self.face_edge_type)

        self._connect_contour_signals()

    def _connect_contour_signals(self):
        """Verbindet alle Kontur-Widgets nur einmal."""
        if getattr(self, "contour_add_segment", None):
            self._connect_button_once(
                self.contour_add_segment,
                self._handle_contour_add_segment,
                "_contour_add_connected",
            )
        if getattr(self, "contour_delete_segment", None):
            self._connect_button_once(
                self.contour_delete_segment,
                self._handle_contour_delete_segment,
                "_contour_delete_connected",
            )
        if getattr(self, "contour_move_up", None):
            self._connect_button_once(
                self.contour_move_up,
                self._handle_contour_move_up,
                "_contour_move_up_connected",
            )
        if getattr(self, "contour_move_down", None):
            self._connect_button_once(
                self.contour_move_down,
                self._handle_contour_move_down,
                "_contour_move_down_connected",
            )

        if getattr(self, "contour_segments", None) and not getattr(self, "_contour_table_connected", False):
            self.contour_segments.itemChanged.connect(self._handle_contour_table_change)
            self.contour_segments.currentCellChanged.connect(self._handle_contour_row_select)
            self._contour_table_connected = True

        if getattr(self, "contour_start_x", None) and not getattr(self, "_contour_start_x_connected", False):
            self.contour_start_x.valueChanged.connect(self._update_contour_preview_temp)
            self._contour_start_x_connected = True
        if getattr(self, "contour_start_z", None) and not getattr(self, "_contour_start_z_connected", False):
            self.contour_start_z.valueChanged.connect(self._update_contour_preview_temp)
            self._contour_start_z_connected = True
        if getattr(self, "contour_side", None) and not getattr(self, "_contour_side_connected", False):
            self.contour_side.currentIndexChanged.connect(self._update_contour_preview_temp)
            self._contour_side_connected = True
        if getattr(self, "contour_name", None) and not getattr(self, "_contour_name_connected", False):
            self.contour_name.textChanged.connect(self._update_contour_preview_temp)
            self._contour_name_connected = True

        if getattr(self, "contour_edge_type", None) and not getattr(self, "_contour_edge_type_connected", False):
            self.contour_edge_type.currentIndexChanged.connect(self._handle_contour_edge_change)
            self._contour_edge_type_connected = True
        if getattr(self, "contour_edge_size", None) and not getattr(self, "_contour_edge_size_connected", False):
            self.contour_edge_size.valueChanged.connect(self._handle_contour_edge_change)
            self._contour_edge_size_connected = True

    # ---- Helfer -------------------------------------------------------
    def _current_op_type(self) -> str:
        idx = self.tab_params.currentIndex() if self.tab_params else 0
        mapping = {
            0: OpType.PROGRAM_HEADER,  # Programmkopf
            1: OpType.FACE,            # Planen
            2: OpType.CONTOUR,         # Kontur
            3: OpType.THREAD,
            4: OpType.GROOVE,
            5: OpType.DRILL,
            6: OpType.KEYWAY,
        }
        return mapping.get(idx, OpType.FACE)

    def _collect_params(self, op_type: str) -> Dict[str, float]:
        widgets = self.param_widgets.get(op_type, {})
        params: Dict[str, float] = {}
        for key, widget in widgets.items():
            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QComboBox):
                params[key] = float(widget.currentIndex())
            elif isinstance(widget, QtWidgets.QAbstractButton):
                params[key] = float(widget.isChecked())
            else:  # QDoubleSpinBox
                params[key] = float(widget.value())

        # Kontur-Segmente separat aus Tabelle einsammeln
        if op_type == OpType.CONTOUR:
            params["segments"] = self._collect_contour_segments()
            if getattr(self, "contour_name", None):
                params["name"] = self.contour_name.text().strip()
        return params

    def _collect_program_header(self) -> Dict[str, object]:
        """Sammelt alle Programmkopf-Parameter für Kommentare/G-Code."""
        # Fehlende Widgets nachladen, falls sie zum Zeitpunkt der Initialisierung
        # noch nicht gefunden wurden (z. B. wegen verzögertem UI-Aufbau).
        if self.program_npv is None:
            self.program_npv = self._get_widget_by_name("program_npv")
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()
        if self.program_retract_mode is None:
            self.program_retract_mode = self._get_widget_by_name("program_retract_mode")
        if self.program_s1 is None:
            self.program_s1 = self._get_widget_by_name("program_s1")
        if self.program_s3 is None:
            self.program_s3 = self._get_widget_by_name("program_s3")
        if self.program_has_subspindle is None:
            self.program_has_subspindle = self._get_widget_by_name("program_has_subspindle")
        if self.program_xt is None:
            self.program_xt = self._get_widget_by_name("program_xt")
        if self.program_zt is None:
            self.program_zt = self._get_widget_by_name("program_zt")
        if self.program_sc is None:
            self.program_sc = self._get_widget_by_name("program_sc")

        header: Dict[str, object] = {}
        if self.program_npv:
            header["npv"] = self.program_npv.currentText().strip()
        if self.program_unit:
            header["unit"] = self.program_unit.currentText().strip()
        if self.program_shape:
            header["shape"] = self.program_shape.currentText().strip()

        def _val(widget):
            return float(widget.value()) if widget else None

        # Rohteilabmessungen / Spannmaße
        header["xa"] = _val(self.program_xa)
        header["xi"] = _val(self.program_xi)
        header["za"] = _val(self.program_za)
        header["zi"] = _val(self.program_zi)
        header["zb"] = _val(self.program_zb)
        header["w"] = _val(self.program_w)
        header["l"] = _val(self.program_l)
        header["n_edges"] = _val(self.program_n)
        header["sw"] = _val(self.program_sw)

        # Rückzug/Ebenen
        header["retract_mode"] = (
            self.program_retract_mode.currentText().strip()
            if self.program_retract_mode
            else ""
        )
        header["xra"] = _val(self.program_xra)
        header["xri"] = _val(self.program_xri)
        header["zra"] = _val(self.program_zra)
        header["zri"] = _val(self.program_zri)

        # Werkzeugwechsel-/Sicherheitspositionen
        header["xt"] = _val(self.program_xt)
        header["zt"] = _val(self.program_zt)
        header["sc"] = _val(self.program_sc)

        if self.program_name:
            header["program_name"] = self.program_name.text().strip()

        # Drehzahlbegrenzung (S3 nur, wenn Gegenspindel aktiv)
        header["has_subspindle"] = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
        header["s1_max"] = float(self.program_s1.value()) if self.program_s1 else 0.0
        if header["has_subspindle"]:
            header["s3_max"] = float(self.program_s3.value()) if self.program_s3 else 0.0
        else:
            header["s3_max"] = 0.0

        return header

    def _collect_contour_segments(self) -> List[Dict[str, object]]:
        table = self.contour_segments
        if table is None:
            return []

        segments: List[Dict[str, object]] = []
        for row in range(table.rowCount()):
            mode_item = table.item(row, 0)
            x_item = table.item(row, 1)
            z_item = table.item(row, 2)
            edge_item = table.item(row, 3)
            size_item = table.item(row, 4)

            mode_raw = mode_item.text().strip().lower() if mode_item else "xz"
            if mode_raw.startswith("xz"):
                mode = "xz"
            elif mode_raw.startswith("x"):
                mode = "x"
            elif mode_raw.startswith("z"):
                mode = "z"
            else:
                mode = "xz"

            edge_txt = edge_item.text().strip().lower() if edge_item and edge_item.text() else "keine"
            if edge_txt.startswith("f"):
                edge = "chamfer"
            elif edge_txt.startswith("r"):
                edge = "radius"
            else:
                edge = "none"

            def _to_float(item):
                try:
                    txt = item.text().replace(",", ".")
                    return float(txt)
                except Exception:
                    return 0.0

            x_text = x_item.text().strip() if x_item and x_item.text() else ""
            z_text = z_item.text().strip() if z_item and z_item.text() else ""

            segments.append(
                {
                    "mode": mode,
                    "x": _to_float(x_item) if x_item else 0.0,
                    "z": _to_float(z_item) if z_item else 0.0,
                    "x_empty": x_text == "",
                    "z_empty": z_text == "",
                    "edge": edge,
                    "edge_size": _to_float(size_item) if size_item else 0.0,
                }
            )

        return segments

    def _write_contour_row(self, row: int, edge_text: str | None = None, edge_size: float | None = None):
        """Schreibt Kante/Maß in die aktuelle Tabellenzeile und hält Typ/X/Z unberührt."""
        table = self.contour_segments
        if table is None or row < 0 or row >= table.rowCount():
            return
        item_cls = QtWidgets.QTableWidgetItem
        if edge_text is not None:
            table.setItem(row, 3, item_cls(edge_text))
        if edge_size is not None:
            table.setItem(row, 4, item_cls(f"{edge_size:.3f}"))

    def _load_params_to_form(self, op: Operation):
        widgets = self.param_widgets.get(op.op_type, {})
        for key, widget in widgets.items():
            if widget is None or key not in op.params:
                continue
            widget.blockSignals(True)
            val = op.params[key]
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(int(val))
            elif isinstance(widget, QtWidgets.QAbstractButton):
                widget.setChecked(bool(val))
            else:
                widget.setValue(val)
            widget.blockSignals(False)

    def _set_preview_paths(
        self,
        paths: List[List[Tuple[float, float]]],
        active_index: int | None = None,
        include_contour_preview: bool = True,
    ) -> None:
        """Aktualisiert Haupt- und optional den Kontur-Tab-Preview."""

        self._ensure_preview_widgets()
        if self.preview:
            self.preview.set_paths(paths, active_index)
        if include_contour_preview and self.contour_preview:
            self.contour_preview.set_paths(paths, None)

    def _refresh_preview(self):
        if self.preview is None:
            self._ensure_preview_widgets()
        if self.preview is None:
            return
        paths: List[List[Tuple[float, float]]] = []

        # Kontur-Eingabe immer mitzeigen, wenn wir auf dem Kontur-Tab sind oder keine Ops existieren
        if self.contour_start_x or self.contour_segments:
            params: Dict[str, object] = {
                "start_x": self.contour_start_x.value() if self.contour_start_x else 0.0,
                "start_z": self.contour_start_z.value() if self.contour_start_z else 0.0,
                "coord_mode": self.contour_coord_mode.currentIndex() if getattr(self, "contour_coord_mode", None) else 0,
                "segments": self._collect_contour_segments(),
            }
            paths.append(build_contour_path(params))

        # vorhandene Operationen hinzufügen
        if self.model.operations:
            paths.extend([op.path for op in self.model.operations if op.path])
            active = self.list_ops.currentRow() if self.list_ops else -1
        else:
            active = -1

        # falls gar nichts vorhanden, leere Liste übergeben -> Achsenkreuz
        self._set_preview_paths(paths, active, include_contour_preview=False)

    def _refresh_operation_list(self, select_index: int | None = None):
        """Synchronisiert die linke Operationsliste mit dem internen Modell."""
        if self.list_ops is None:
            return

        current = self.list_ops.currentRow()
        self.list_ops.blockSignals(True)
        self._op_row_user_selected = False
        self.list_ops.clear()
        for i, op in enumerate(self.model.operations):
            self.list_ops.addItem(self._describe_operation(op, i + 1))

        if select_index is None:
            select_index = current
        if select_index is None:
            select_index = -1

        if 0 <= select_index < self.list_ops.count():
            self.list_ops.setCurrentRow(select_index)
        elif self.list_ops.count() > 0:
            self.list_ops.setCurrentRow(self.list_ops.count() - 1)
        self.list_ops.blockSignals(False)

    def _ensure_preview_widgets(self):
        """Versucht fehlende Preview-Widget-Referenzen aus dem UI zu holen."""
        root = self.root_widget or self._find_root_widget()
        if root:
            if self.preview is None:
                self.preview = root.findChild(LathePreviewWidget, "previewWidget")
            if self.contour_preview is None:
                self.contour_preview = root.findChild(LathePreviewWidget, "contourPreview")

    def _mark_operation_user_selected(self, *args, **kwargs):
        self._op_row_user_selected = True

    def _update_selected_operation(self, *, force: bool = False):
        if self.list_ops is None:
            return
        if not force and not self._op_row_user_selected:
            return
        idx = self.list_ops.currentRow()
        if idx < 0 or idx >= len(self.model.operations):
            return
        op = self.model.operations[idx]
        op.params = self._collect_params(op.op_type)
        self.model.update_geometry(op)
        if self.list_ops:
            item = self.list_ops.item(idx)
            if item:
                item.setText(self._describe_operation(op, idx + 1))
        self._refresh_preview()

    # ---- Button-Handler -----------------------------------------------
    def _handle_add_operation(self):
        # Sicherheitsnetz: Widgets nachziehen, falls sie erst später verfügbar sind
        self._ensure_core_widgets()
        try:
            print("[LatheEasyStep] add operation triggered")
        except Exception:
            pass
        op_type = self._current_op_type()
        if op_type == OpType.PROGRAM_HEADER:
            params = self._collect_program_header()
            # nur einen Programmkopf zulassen -> ersetzen oder neu hinzufügen
            for i, existing in enumerate(self.model.operations):
                if existing.op_type == OpType.PROGRAM_HEADER:
                    existing.params = params
                    if self.list_ops:
                        item = self.list_ops.item(i)
                        if item:
                            item.setText(self._describe_operation(existing, i + 1))
                        self.list_ops.setCurrentRow(i)
                    self._refresh_preview()
                    return
            # noch kein Programmkopf: vorne einfügen
            op = Operation(op_type, params)
            self.model.update_geometry(op)
            self.model.operations.insert(0, op)
            self._refresh_operation_list(select_index=0)
            self._refresh_preview()
        else:
            params = self._collect_params(op_type)
            op = Operation(op_type, params)
            self.model.update_geometry(op)
            self.model.add_operation(op)

            self._refresh_operation_list(select_index=len(self.model.operations) - 1)
            self._refresh_preview()

    def _handle_delete_operation(self):
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx < 0:
            return
        self.model.remove_operation(idx)
        self._refresh_operation_list(select_index=min(idx, len(self.model.operations) - 1))
        self._refresh_preview()

    def _handle_move_up(self):
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx <= 0:
            return
        self.model.move_up(idx)
        self._refresh_operation_list(select_index=idx - 1)
        self._refresh_preview()

    def _handle_move_down(self):
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx < 0 or idx >= self.list_ops.count() - 1:
            return
        self.model.move_down(idx)
        self._refresh_operation_list(select_index=idx + 1)
        self._refresh_preview()

    def _init_contour_table(self):
        """Sorgt für Spalten/Headers in der Kontur-Tabelle."""
        table = self.contour_segments
        if table is None:
            return
        if table.columnCount() < 5:
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Typ", "X", "Z", "Kante", "Maß"])

    # ---- Kontur: Segment-Tabelle --------------------------------------
    def _handle_contour_add_segment(self):
        table = self.contour_segments
        if table is None:
            return

        self._init_contour_table()

        row = table.rowCount()
        existing_segments = self._collect_contour_segments()
        x0 = self.contour_start_x.value() if self.contour_start_x else 0.0
        z0 = self.contour_start_z.value() if self.contour_start_z else 0.0

        last_x = float(existing_segments[-1].get("x", x0)) if existing_segments else x0
        last_z = float(existing_segments[-1].get("z", z0)) if existing_segments else z0
        default_x = last_x
        default_z = last_z

        table.insertRow(row)

        item_cls = QtWidgets.QTableWidgetItem
        table.setItem(row, 0, item_cls("XZ"))
        # X/Z leer lassen, damit sie nicht automatisch auf 0 gezogen werden
        table.setItem(row, 1, item_cls(""))
        table.setItem(row, 2, item_cls(""))

        # Vorlage verwenden (Kante/Maß)
        edge_text = self._contour_edge_template_text
        edge_size = (
            self._contour_edge_template_size
            if edge_text.lower().startswith(("f", "r"))
            else 0.0
        )
        table.setItem(row, 3, item_cls(edge_text))
        table.setItem(row, 4, item_cls(f"{edge_size:.3f}"))

        table.setCurrentCell(row, 0)
        # neuer Datensatz -> Vorlage-Modus, nicht automatisch Zeile editieren
        self._contour_row_user_selected = False
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_delete_segment(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)
            self._update_selected_operation()
            self._update_contour_preview_temp()
            self._sync_contour_edge_controls()

    def _handle_contour_move_up(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row <= 0:
            return
        table.insertRow(row - 1)
        for col in range(table.columnCount()):
            item = table.takeItem(row + 1, col)
            table.setItem(row - 1, col, item)
        table.removeRow(row + 1)
        table.setCurrentCell(row - 1, 0)
        self._update_selected_operation()
        self._update_contour_preview_temp()

    def _handle_contour_move_down(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row < 0 or row >= table.rowCount() - 1:
            return
        table.insertRow(row + 2)
        for col in range(table.columnCount()):
            item = table.takeItem(row, col)
            table.setItem(row + 2, col, item)
        table.removeRow(row)
        table.setCurrentCell(row + 1, 0)
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_table_change(self, *args, **kwargs):
        """Aktualisiert die aktive Operation, wenn die Segmenttabelle editiert wird."""
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_row_select(self, *args, **kwargs):
        # merken, ob der Benutzer die Tabelle aktiv fokussiert hat
        table = self.contour_segments
        self._contour_row_user_selected = bool(table and table.hasFocus())
        self._sync_contour_edge_controls()

    def _handle_contour_edge_change(self, *args, **kwargs):
        """
        Kante/Kantenmaß:
        - wenn die Tabelle den Fokus hat und eine Zeile ausgewählt ist, wird diese Zeile geändert
        - ansonsten wird nur die Vorlage für das nächste Segment aktualisiert
        """
        edge_text = self.contour_edge_type.currentText() if self.contour_edge_type else ""
        edge_size = self.contour_edge_size.value() if self.contour_edge_size else 0.0

        # Vorlage immer merken – zählt für das nächste Segment+
        self._contour_edge_template_text = edge_text
        self._contour_edge_template_size = edge_size

        table = self.contour_segments
        if table is not None and table.currentRow() >= 0 and self._contour_row_user_selected:
            # Benutzer bearbeitet aktiv eine Tabellenzeile
            self._write_contour_row(table.currentRow(), edge_text=edge_text, edge_size=edge_size)
            self._update_selected_operation()
            self._update_contour_preview_temp()

        # Anzeige/Eingaben nachziehen (zeigt entweder Zeile oder Vorlage)
        self._sync_contour_edge_controls()

    def _update_contour_preview_temp(self):
        """Zeigt eine Vorschau der Kontur auch ohne ausgewählte Operation."""
        if self.preview is None:
            return
        # Nur auf dem Kontur-Tab sinnvoll
        params: Dict[str, object] = {
            "start_x": self.contour_start_x.value() if self.contour_start_x else 0.0,
            "start_z": self.contour_start_z.value() if self.contour_start_z else 0.0,
            "coord_mode": self.contour_coord_mode.currentIndex() if getattr(self, "contour_coord_mode", None) else 0,
            "segments": self._collect_contour_segments(),
        }
        if self.contour_name:
            params["name"] = self.contour_name.text().strip()
        path = build_contour_path(params)
        try:
            print(f"[LatheEasyStep] contour preview path points: {path}")
        except Exception:
            pass
        self._set_preview_paths([path], None)

    def _sync_contour_edge_controls(self):
        """Synchronisiert Kante/Maß-Eingabe mit der aktuellen Tabellenzeile und blendet Felder."""
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        edge_txt = self._contour_edge_template_text
        size_val = self._contour_edge_template_size

        # Nur wenn der Benutzer aktiv eine Zeile ausgewählt/bearbeitet, zeigen wir deren Werte
        if row >= 0 and self._contour_row_user_selected:
            edge_item = table.item(row, 3)
            size_item = table.item(row, 4)
            if edge_item and edge_item.text():
                edge_txt = edge_item.text().strip()
            if size_item and size_item.text():
                try:
                    size_val = float(size_item.text())
                except Exception:
                    size_val = 0.0

        # Edge combo
        if self.contour_edge_type:
            idx = self.contour_edge_type.findText(edge_txt, QtCore.Qt.MatchFixedString)
            if idx < 0:
                idx = 0
            self.contour_edge_type.blockSignals(True)
            self.contour_edge_type.setCurrentIndex(idx)
            self.contour_edge_type.blockSignals(False)

        # Edge size Steuerung: Feld bleibt sichtbar; enable nur bei Fase/Radius
        edge_txt_ctrl = self.contour_edge_type.currentText() if self.contour_edge_type else edge_txt
        enable_size = edge_txt_ctrl.lower().startswith("f") or edge_txt_ctrl.lower().startswith("r")
        if self.label_contour_edge_size:
            self.label_contour_edge_size.setVisible(True)
            self.label_contour_edge_size.setEnabled(True)
        if self.contour_edge_size:
            self.contour_edge_size.blockSignals(True)
            self.contour_edge_size.setVisible(True)
            self.contour_edge_size.setEnabled(enable_size)
            self.contour_edge_size.setValue(size_val)
            self.contour_edge_size.blockSignals(False)

    def _handle_new_program(self):
        self.model.operations.clear()
        self._op_row_user_selected = False
        self._refresh_operation_list(select_index=-1)
        self._refresh_preview()

    def _handle_generate_gcode(self):
        header = self._collect_program_header()

        filepath = self._build_program_filepath(header.get("program_name", ""))
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.program_settings = header
        self.model.spindle_speed_max = float(header.get("s1_max") or 0.0)

        lines = self.model.generate_gcode()
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        open_fn = getattr(Action, "CALLBACK_OPEN_PROGRAM", None)
        if callable(open_fn):
            open_fn(filepath)
        else:
            print(f"[LatheEasyStep] Hinweis: Programm geschrieben nach {filepath}, automatisches Öffnen nicht verfügbar")

    def _build_program_filepath(self, name_raw: str | None) -> str:
        base = (name_raw or "").strip()
        if not base:
            base = "conv_lathe"

        # Dateinamen säubern: Nur Buchstaben/Ziffern/_/- behalten, Leerzeichen -> _
        base = base.replace(" ", "_")
        base = re.sub(r"[^A-Za-z0-9_\-]", "", base)
        if not base:
            base = "conv_lathe"

        filename = base if base.lower().endswith(".ngc") else f"{base}.ngc"
        return os.path.expanduser(os.path.join("~/linuxcnc/nc_files", filename))

    def _handle_param_change(self):
        if self._op_row_user_selected:
            self._update_selected_operation()
        elif self._current_op_type() == OpType.CONTOUR:
            # Trotzdem Live-Vorschau anbieten, ohne bestehende Operationen zu überschreiben
            self._update_contour_preview_temp()

    def _handle_selection_change(self, row: int):
        self._op_row_user_selected = bool(
            self.list_ops
            and (self.list_ops.hasFocus() or self._op_row_user_selected)
        )
        if row < 0 or row >= len(self.model.operations):
            return
        op = self.model.operations[row]
        if self.tab_params:
            type_to_tab = {
                OpType.FACE: 1,
                OpType.CONTOUR: 2,
                OpType.THREAD: 3,
                OpType.GROOVE: 4,
                OpType.DRILL: 5,
                OpType.KEYWAY: 6,
            }
            self.tab_params.setCurrentIndex(type_to_tab.get(op.op_type, 1))
        self._load_params_to_form(op)
        self._refresh_preview()

    def _handle_global_change(self, *args, **kwargs):
        print("[LatheEasyStep] _handle_global_change() called")
        self._apply_unit_suffix()
        self._update_program_visibility()
        self._update_retract_visibility()
        self._update_subspindle_visibility()
        self._update_face_visibility()

    # ---- Form-Optik ---------------------------------------------------
    def _apply_unit_suffix(self):
        """Einheit mm/inch im gesamten Panel sichtbar umschalten."""

        # Falls aus irgendeinem Grund noch keine Combo referenziert ist:
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()
            if self.program_unit is None:
                print("[LatheEasyStep] _apply_unit_suffix: no unit combo, abort")
                return

        idx = self.program_unit.currentIndex()
        unit = "mm" if idx == 0 else "inch"

        unit_suffix = f" {unit}"
        feed_suffix = f" {unit}/U"

        # Root-Widget bestimmen
        root = self.root_widget or self.program_unit.window()
        if root is None:
            print("[LatheEasyStep] _apply_unit_suffix: no root widget")
            return

        print(f"[LatheEasyStep] _apply_unit_suffix(): unit={unit}, root={root.objectName()}")

        # --- 1) Alle DoubleSpinBoxen im Fenster behandeln ---
        for sb in root.findChildren(QtWidgets.QDoubleSpinBox):
            name = sb.objectName()

            # Drehzahlfelder S1/S3 nicht anfassen
            if name in ("program_s1", "program_s3") or "spindle" in name.lower():
                continue

            if "feed" in name.lower():
                sb.setSuffix(feed_suffix)
            else:
                sb.setSuffix(unit_suffix)

        # --- 2) Beschriftungstexte: Einheiten komplett entfernen (nur einmal) ---
        if not hasattr(self, "_labels_cleaned") or not self._labels_cleaned:
            for lbl in root.findChildren(QtWidgets.QLabel):
                text = lbl.text()
                # nur Labels anfassen, die überhaupt Klammern mit Einheit haben
                if "(" in text and ")" in text and any(u in text for u in ("mm", "inch", "/U")):
                    prefix = text.split("(", 1)[0].rstrip()
                    lbl.setText(prefix)
            self._labels_cleaned = True

        # Fenstertitel markieren, damit man sofort sieht, dass was passiert
        win = root.window()
        try:
            old_title = win.windowTitle()
            win.setWindowTitle(f"{old_title.split('[')[0].strip()} [{unit}]")
        except Exception:
            pass

    def _update_program_visibility(self, shape=None):
        """Zeigt/verbirgt Programmpfelder abhängig von der Rohteilform."""

        # aktuelle Form ermitteln
        if shape is None and hasattr(self, "program_shape") and self.program_shape is not None:
            shape = self.program_shape.currentText()

        if not shape:
            print("[LatheEasyStep] _update_program_visibility: keine Form")
            return

        # wir vergleichen in Kleinbuchstaben
        shape_l = shape.lower()
        print(f"[LatheEasyStep] _update_program_visibility(): shape='{shape}'")

        # Root-Widget wie in _apply_unit_suffix benutzen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if root is None:
            print("[LatheEasyStep] _update_program_visibility: kein root_widget")
            return

        def show(name, visible):
            w = root.findChild(QtWidgets.QWidget, name)
            if w is None:
                print(f"[LatheEasyStep] _update_program_visibility: widget '{name}' nicht gefunden")
                return
            w.setVisible(visible)

        # Alle "Sonder"-Widgets erst mal ausblenden
        special_widgets = [
            "label_prog_xi", "program_xi",
            "label_prog_w", "program_w",
            "label_prog_l", "program_l",
            "label_prog_n", "program_n",
            "label_prog_sw", "program_sw",
        ]
        for name in special_widgets:
            show(name, False)

        # Jetzt je nach Form einschalten
        if shape_l == "rohr":
            # Rohr: Innen-Ø zusätzlich
            show("label_prog_xi", True)
            show("program_xi", True)

        elif shape_l == "rechteck":
            # Rechteck: Breite und Länge
            show("label_prog_w", True)
            show("program_w", True)
            show("label_prog_l", True)
            show("program_l", True)

        elif shape_l in ("n-eck", "n-eck"):
            # N-Eck: Kantenanzahl und Schlüsselweite
            show("label_prog_n", True)
            show("program_n", True)
            show("label_prog_sw", True)
            show("program_sw", True)

    def _update_retract_visibility(self, widget=None, mode_in=None):
        """Zeigt/verbirgt Rückzugsebenen abhängig vom Rückzug-Modus."""

        # Combo ermitteln
        combo = self.program_retract_mode
        if isinstance(widget, QtWidgets.QComboBox):
            combo = widget

        # Modustext ermitteln
        if mode_in is not None:
            mode_text = str(mode_in)
        elif combo is not None:
            mode_text = combo.currentText()
        else:
            print("[LatheEasyStep] _update_retract_visibility: kein Combo / Modus")
            return

        mode_norm = mode_text.strip().lower()
        print(f"[LatheEasyStep] _update_retract_visibility(): widget={combo}, mode='{mode_text}', mode_norm='{mode_norm}'")

        # Root-Widget wie in _update_program_visibility benutzen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if root is None:
            print("[LatheEasyStep] _update_retract_visibility: kein root_widget")
            return

        def show(name: str, visible: bool):
            w = root.findChild(QtWidgets.QWidget, name)
            if w is None:
                print(f"[LatheEasyStep] _update_retract_visibility: widget '{name}' nicht gefunden")
                return
            w.setVisible(visible)

        # alle Rückzugs-Widgets erst mal ausblenden
        all_widgets = [
            "label_prog_xra", "program_xra",
            "label_prog_xri", "program_xri",
            "label_prog_zra", "program_zra",
            "label_prog_zri", "program_zri",
        ]
        for name in all_widgets:
            show(name, False)

        # --------- Modus-spezifische Sichtbarkeit --------------------
        if mode_norm == "einfach":
            # gemäß Siemens-Beispiel: XRA und ZRA auch im Modus "einfach"
            show("label_prog_xra", True)
            show("program_xra", True)
            show("label_prog_zra", True)
            show("program_zra", True)

        elif mode_norm == "erweitert":
            # erweiterte Kontrolle: außen + innere X-Ebene
            show("label_prog_xra", True)
            show("program_xra", True)
            show("label_prog_zra", True)
            show("program_zra", True)
            show("label_prog_xri", True)
            show("program_xri", True)

        elif mode_norm == "alle":
            # alle Ebenen sichtbar (volle manuelle Kontrolle)
            for name in all_widgets:
                show(name, True)
        else:
            print(f"[LatheEasyStep] _update_retract_visibility: unbekannter Modus '{mode_norm}'")

    def _update_subspindle_visibility(self, *args, **kwargs):
        """Blendet S3-Felder aus/ein, wenn eine Gegenspindel vorhanden ist."""
        has_sub = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
        print(f"[LatheEasyStep] _update_subspindle_visibility(): has_sub={has_sub}")

        # Falls Referenzen fehlen, per findChild nachholen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if self.label_prog_s3 is None and root:
            self.label_prog_s3 = root.findChild(QtWidgets.QWidget, "label_prog_s3")
        if self.program_s3 is None and root:
            self.program_s3 = root.findChild(QtWidgets.QWidget, "program_s3")

        if self.label_prog_s3:
            self.label_prog_s3.setVisible(has_sub)
        else:
            print("[LatheEasyStep] _update_subspindle_visibility: label_prog_s3 not found")

        if self.program_s3:
            self.program_s3.setVisible(has_sub)
        else:
            print("[LatheEasyStep] _update_subspindle_visibility: program_s3 not found")

    def _update_face_visibility(self, *args, **kwargs):
        """Blendet Felder im Reiter 'Planen' abhängig von Modus und Fase/Radius ein/aus."""
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if root:
            if self.face_mode is None:
                self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
            if self.face_edge_type is None:
                self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")
            if self.label_face_finish_allow_x is None:
                self.label_face_finish_allow_x = root.findChild(QtWidgets.QLabel, "label_face_finish_allow_x")
            if self.face_finish_allow_x is None:
                self.face_finish_allow_x = root.findChild(QtWidgets.QDoubleSpinBox, "face_finish_allow_x")
            if self.label_face_finish_allow_z is None:
                self.label_face_finish_allow_z = root.findChild(QtWidgets.QLabel, "label_face_finish_allow_z")
            if self.face_finish_allow_z is None:
                self.face_finish_allow_z = root.findChild(QtWidgets.QDoubleSpinBox, "face_finish_allow_z")
            if self.label_face_depth_max is None:
                self.label_face_depth_max = root.findChild(QtWidgets.QLabel, "label_face_depth_max")
            if self.face_depth_max is None:
                self.face_depth_max = root.findChild(QtWidgets.QDoubleSpinBox, "face_depth_max")
            if self.label_face_edge_size is None:
                self.label_face_edge_size = root.findChild(QtWidgets.QLabel, "label_face_edge_size")
            if self.face_edge_size is None:
                self.face_edge_size = root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_size")

        mode_text = self.face_mode.currentText().lower() if self.face_mode else ""
        edge_text = self.face_edge_type.currentText().lower() if self.face_edge_type else ""

        is_rough = "schrupp" in mode_text
        edge_visible = edge_text in ("fase", "radius")

        # Schrupp-Optionen
        if self.label_face_finish_allow_x:
            self.label_face_finish_allow_x.setVisible(is_rough)
        if self.face_finish_allow_x:
            self.face_finish_allow_x.setVisible(is_rough)

        if self.label_face_finish_allow_z:
            self.label_face_finish_allow_z.setVisible(is_rough)
        if self.face_finish_allow_z:
            self.face_finish_allow_z.setVisible(is_rough)

        if self.label_face_depth_max:
            self.label_face_depth_max.setVisible(is_rough)
        if self.face_depth_max:
            self.face_depth_max.setVisible(is_rough)

        # Kantenform
        if self.label_face_edge_size:
            self.label_face_edge_size.setVisible(edge_visible)
        if self.face_edge_size:
            self.face_edge_size.setVisible(edge_visible)

        if self.label_face_edge_size:
            if edge_text == "fase":
                self.label_face_edge_size.setText("Fasenlänge")
            elif edge_text == "radius":
                self.label_face_edge_size.setText("Radius")
            else:
                self.label_face_edge_size.setText("Kantengröße")

    # ---- Hilfsfunktionen ----------------------------------------------
    def _describe_operation(self, op: Operation, number: int) -> str:
        tool = int(op.params.get("tool", 0)) if isinstance(op.params, dict) else 0
        suffix = f" (T{tool:02d})" if tool > 0 else ""
        if op.op_type == OpType.PROGRAM_HEADER:
            npv = op.params.get("npv", "G54") if isinstance(op.params, dict) else "G54"
            return f"{number}: Programmkopf ({npv})"
        if op.op_type == OpType.CONTOUR:
            name = op.params.get("name", "") if isinstance(op.params, dict) else ""
            name_suffix = f" [{name}]" if name else ""
            return f"{number}: Kontur{name_suffix}{suffix}"
        if op.op_type == OpType.FACE:
            mode_idx = int(op.params.get("mode", 0)) if isinstance(op.params, dict) else 0
            mode_label = {
                0: "Schruppen",
                1: "Schlichten",
                2: "Schruppen+Schlichten",
            }.get(mode_idx, "Planen")
            start_z = op.params.get("start_z", 0.0) if isinstance(op.params, dict) else 0.0
            end_z = op.params.get("end_z", 0.0) if isinstance(op.params, dict) else 0.0
            coolant_hint = " mit Kühlung" if bool(op.params.get("coolant", False)) else ""
            return f"{number}: Planen {mode_label} (Z {start_z}→{end_z}){coolant_hint}{suffix}"
        return f"{number}: {op.op_type.title()}{suffix}"

    def _renumber_operations(self):
        if self.list_ops is None:
            return
        for i in range(self.list_ops.count()):
            item = self.list_ops.item(i)
            op = self.model.operations[i]
            item.setText(self._describe_operation(op, i + 1))

    # ---- QtVCP user command hook (leer) -------------------------------
    def call_user_command_(self, command_file: str | None):
        # Wird von QtVCP erwartet, hier aber bewusst leer gehalten.
        return


def get_handlers(halcomp, widgets, paths):
    return [HandlerClass(halcomp, widgets, paths)]
