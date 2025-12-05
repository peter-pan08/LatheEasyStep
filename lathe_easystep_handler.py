"""
LatheEasyStep – QtVCP conversational lathe panel
mit 2D-Vorschau und G-Code-Erzeugung.

UI-Datei: lathe_easystep.ui
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

from qtpy import QtCore, QtGui, QtWidgets
from qtvcp.core import Action


# ----------------------------- Operationstypen -----------------------------


class OpType:
    FACE = "face"
    TURN = "turn"


@dataclass
class Operation:
    op_type: str
    params: Dict[str, float]
    path: List[Tuple[float, float]] = field(default_factory=list)


# ------------------------------ Programmmodell -----------------------------


class ProgramModel:
    def __init__(self) -> None:
        self.operations: List[Operation] = []
        self.program_settings: Dict[str, Any] = {}

    def add_operation(self, op: Operation) -> None:
        self.operations.append(op)

    def remove_operation(self, index: int) -> None:
        if 0 <= index < len(self.operations):
            del self.operations[index]

    def move_up(self, index: int) -> None:
        if 1 <= index < len(self.operations):
            self.operations[index - 1], self.operations[index] = (
                self.operations[index],
                self.operations[index - 1],
            )

    def move_down(self, index: int) -> None:
        if 0 <= index < len(self.operations) - 1:
            self.operations[index + 1], self.operations[index] = (
                self.operations[index],
                self.operations[index + 1],
            )

    def update_geometry(self, op: Operation) -> None:
        builder = {
            OpType.FACE: build_face_path,
            OpType.TURN: build_turn_path,
        }.get(op.op_type)
        if builder:
            op.path = builder(op.params)

    def generate_gcode(self) -> List[str]:
        """Erzeuge einfachen G-Code aus allen Operationen."""
        lines: List[str] = []
        name = self.program_settings.get("name", "")
        unit = self.program_settings.get("unit", "mm")
        xa = self.program_settings.get("xa", 0.0)
        xi = self.program_settings.get("xi", 0.0)
        length = self.program_settings.get("length", 0.0)

        lines.append("(LatheEasyStep – auto generated)")
        if name:
            lines.append(f"(Program: {name})")
        lines.append(f"(Stock: XA={xa:.3f} XI={xi:.3f} L={length:.3f} {unit})")
        lines.append("")
        lines.append("G18 G90 G40 G80")
        lines.append("G54")
        if unit == "inch":
            lines.append("G20")
        else:
            lines.append("G21")
        lines.append("")

        for idx, op in enumerate(self.operations, start=1):
            lines.append(f"(Operation {idx}: {op.op_type})")
            lines.extend(gcode_for_operation(op))
            lines.append("")

        lines.append("M9")
        lines.append("M30")
        lines.append("%")
        return lines


# ------------------------------ Vorschau-Widget ----------------------------


class LathePreviewWidget(QtWidgets.QWidget):
    """Einfache 2D-Vorschau in X–Z."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.paths: List[List[Tuple[float, float]]] = []
        self.active_index: int | None = None
        self.setMinimumHeight(200)

    def set_paths(
        self,
        paths: List[List[Tuple[float, float]]],
        active_index: int | None = None,
    ) -> None:
        self.paths = paths
        self.active_index = active_index
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.black)

        if not self.paths:
            return

        # Alle Punkte sammeln
        all_points = [p for path in self.paths for p in path]
        xs = [p[0] for p in all_points]
        zs = [p[1] for p in all_points]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)

        if min_x == max_x:
            max_x += 1.0
        if min_z == max_z:
            max_z += 1.0

        margin = 20
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        scale_x = rect.width() / (max_x - min_x)
        scale_z = rect.height() / (max_z - min_z)
        scale = min(scale_x, scale_z)

        def to_screen(x_val: float, z_val: float) -> QtCore.QPointF:
            x_pix = rect.left() + (x_val - min_x) * scale
            z_pix = rect.bottom() - (z_val - min_z) * scale  # Z nach unten
            return QtCore.QPointF(x_pix, z_pix)

        for idx, path in enumerate(self.paths):
            if len(path) < 2:
                continue
            color = QtGui.QColor("lime") if idx != self.active_index else QtGui.QColor("yellow")
            pen = QtGui.QPen(color, 2)
            painter.setPen(pen)
            points = [to_screen(x, z) for x, z in path]
            painter.drawPolyline(QtGui.QPolygonF(points))


# ------------------------- Geometrie / Toolpaths ---------------------------


def build_face_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    x_start = params.get("start_diameter", 0.0)
    z_target = params.get("target_z", 0.0)
    safe_z = params.get("safe_z", 2.0)

    return [
        (x_start, safe_z),
        (x_start, z_target),
        (0.0, z_target),
    ]


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


def gcode_from_path(path: List[Tuple[float, float]], feed: float, safe_z: float) -> List[str]:
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


def gcode_for_operation(op: Operation) -> List[str]:
    p = op.params
    if op.op_type == OpType.FACE:
        feed = p.get("feed", 0.2)
        safe_z = p.get("safe_z", 2.0)
        return gcode_from_path(op.path, feed, safe_z)

    if op.op_type == OpType.TURN:
        feed = p.get("feed", 0.2)
        safe_z = p.get("safe_z", 2.0)
        return gcode_from_path(op.path, feed, safe_z)

    return []


# ------------------------------ Handler-Klasse -----------------------------


class HandlerClass:
    """QtVCP-Handler für LatheEasyStep."""

    def __init__(self, halcomp, widgets, paths) -> None:
        self.hal = halcomp
        self.w = widgets
        self.paths = paths
        self.model = ProgramModel()

        # Widgets auflösen
        self.preview: LathePreviewWidget | None = getattr(widgets, "previewWidget", None)
        if self.preview is None and hasattr(widgets, "findChild"):
            self.preview = widgets.findChild(LathePreviewWidget, "previewWidget")

        self.list_ops = self._widget("listOperations", QtWidgets.QListWidget)
        self.tab_params = self._widget("tabParams", QtWidgets.QTabWidget)

        self.btn_add = self._widget("btnAdd", QtWidgets.QPushButton)
        self.btn_delete = self._widget("btnDelete", QtWidgets.QPushButton)
        self.btn_move_up = self._widget("btnMoveUp", QtWidgets.QPushButton)
        self.btn_move_down = self._widget("btnMoveDown", QtWidgets.QPushButton)
        self.btn_new_program = self._widget("btnNewProgram", QtWidgets.QPushButton)
        self.btn_generate = self._widget("btnGenerate", QtWidgets.QPushButton)

        # Programm-Tab
        self.program_name = self._widget("program_name", QtWidgets.QLineEdit)
        self.program_unit = self._widget("program_unit", QtWidgets.QComboBox)
        self.program_shape = self._widget("program_shape", QtWidgets.QComboBox)
        self.program_xa = self._widget("program_xa", QtWidgets.QDoubleSpinBox)
        self.program_xi = self._widget("program_xi", QtWidgets.QDoubleSpinBox)
        self.program_l = self._widget("program_l", QtWidgets.QDoubleSpinBox)

        # Layouts (für evtl. spätere Feinjustierung)
        self.h_layout = self._widget("horizontalLayout", QtWidgets.QHBoxLayout)
        self.v_layout = self._widget("verticalLayout", QtWidgets.QVBoxLayout)
        self.right_layout = self._widget("rightLayout", QtWidgets.QVBoxLayout)

        try:
            if self.h_layout:
                self.h_layout.setStretch(0, 1)
                self.h_layout.setStretch(1, 3)
            if self.v_layout:
                self.v_layout.setStretch(0, 1)
                self.v_layout.setStretch(1, 0)
            if self.right_layout:
                self.right_layout.setStretch(0, 3)
                self.right_layout.setStretch(1, 2)
            if self.preview:
                self.preview.setMinimumSize(240, 220)
                self.preview.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Expanding,
                )
        except Exception:
            # Layout-Optimierung ist nice-to-have – keine harten Fehler
            pass

        self._setup_param_maps()
        self._connect_signals()
        self._refresh_preview()

    # ---- QtVCP Lifecycle -------------------------------------------------

    def initialized__(self) -> None:
        """Wird von QtVCP nach dem Laden aufgerufen."""
        pass

    # ---- Hilfsfunktionen -------------------------------------------------

    def _widget(self, name: str, cls):
        """Widget per Attribut oder QObject-Namen holen."""
        widget = getattr(self.w, name, None)
        if widget is None and hasattr(self.w, "findChild"):
            try:
                widget = self.w.findChild(cls, name)
            except Exception:
                widget = None
        return widget

    def _setup_param_maps(self) -> None:
        """Zuordnung Operation → Formularfelder."""
        self.param_widgets: Dict[str, Dict[str, QtCore.QObject]] = {
            OpType.FACE: {
                "start_diameter": self._widget("face_start_diameter", QtWidgets.QDoubleSpinBox),
                "target_z": self._widget("face_target_z", QtWidgets.QDoubleSpinBox),
                "safe_z": self._widget("face_safe_z", QtWidgets.QDoubleSpinBox),
                "feed": self._widget("face_feed", QtWidgets.QDoubleSpinBox),
            },
            OpType.TURN: {
                "start_diameter": self._widget("turn_start_diameter", QtWidgets.QDoubleSpinBox),
                "end_diameter": self._widget("turn_end_diameter", QtWidgets.QDoubleSpinBox),
                "length": self._widget("turn_length", QtWidgets.QDoubleSpinBox),
                "safe_z": self._widget("turn_safe_z", QtWidgets.QDoubleSpinBox),
                "feed": self._widget("turn_feed", QtWidgets.QDoubleSpinBox),
            },
        }

    def _connect_signals(self) -> None:
        # Buttons
        if self.btn_add:
            self.btn_add.clicked.connect(self._handle_add_operation)
        if self.btn_delete:
            self.btn_delete.clicked.connect(self._handle_delete_operation)
        if self.btn_move_up:
            self.btn_move_up.clicked.connect(self._handle_move_up)
        if self.btn_move_down:
            self.btn_move_down.clicked.connect(self._handle_move_down)
        if self.btn_new_program:
            self.btn_new_program.clicked.connect(self._handle_new_program)
        if self.btn_generate:
            self.btn_generate.clicked.connect(self._handle_generate_gcode)

        # Schrittliste
        if self.list_ops:
            self.list_ops.currentRowChanged.connect(self._handle_selection_change)

        # Parameterfelder
        for widgets in self.param_widgets.values():
            for widget in widgets.values():
                if widget is None:
                    continue
                if isinstance(widget, QtWidgets.QComboBox):
                    widget.currentIndexChanged.connect(self._handle_param_change)
                elif isinstance(widget, QtWidgets.QAbstractButton):
                    widget.toggled.connect(self._handle_param_change)
                else:
                    widget.valueChanged.connect(self._handle_param_change)

        # Programmdaten
        if self.program_name:
            self.program_name.textChanged.connect(self._handle_program_change)
        for widget in [self.program_unit, self.program_shape, self.program_xa, self.program_xi, self.program_l]:
            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self._handle_program_change)
            else:
                widget.valueChanged.connect(self._handle_program_change)

    # ---- Parameterhandling -----------------------------------------------

    def _current_op_type(self) -> str:
        """Ermittle Operationstyp anhand des aktiven Tabs."""
        idx = self.tab_params.currentIndex() if self.tab_params else 0
        # Tab-Reihenfolge: Programm, Planen, Längsdrehen
        mapping = [None, OpType.FACE, OpType.TURN]
        if 0 <= idx < len(mapping) and mapping[idx] is not None:
            return mapping[idx]  # type: ignore[return-value]
        return OpType.FACE

    def _collect_params(self, op_type: str) -> Dict[str, float]:
        widgets = self.param_widgets.get(op_type, {})
        params: Dict[str, float] = {}
        for key, widget in widgets.items():
            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                params[key] = float(widget.value())
            elif isinstance(widget, QtWidgets.QComboBox):
                params[key] = float(widget.currentIndex())
            elif isinstance(widget, QtWidgets.QAbstractButton):
                params[key] = float(widget.isChecked())
        return params

    def _load_params_to_form(self, op: Operation) -> None:
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
            elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                widget.setValue(val)
            widget.blockSignals(False)

    def _collect_program_settings(self) -> Dict[str, Any]:
        return {
            "name": self.program_name.text() if self.program_name else "",
            "unit": self.program_unit.currentText() if self.program_unit else "mm",
            "shape": self.program_shape.currentText() if self.program_shape else "",
            "xa": self.program_xa.value() if self.program_xa else 0.0,
            "xi": self.program_xi.value() if self.program_xi else 0.0,
            "length": self.program_l.value() if self.program_l else 0.0,
        }

    def _refresh_preview(self) -> None:
        if self.preview is None:
            return
        paths = [op.path for op in self.model.operations]
        active = self.list_ops.currentRow() if self.list_ops else -1
        self.preview.set_paths(paths, active)

    def _update_selected_operation(self) -> None:
        idx = self.list_ops.currentRow() if self.list_ops else -1
        if idx < 0 or idx >= len(self.model.operations):
            return
        op = self.model.operations[idx]
        op.params = self._collect_params(op.op_type)
        self.model.update_geometry(op)
        self._refresh_preview()

    # ---- Button-Handler --------------------------------------------------

    def _handle_add_operation(self) -> None:
        if self.list_ops is None:
            return
        op_type = self._current_op_type()
        params = self._collect_params(op_type)
        op = Operation(op_type, params)
        self.model.update_geometry(op)
        self.model.add_operation(op)
        self.list_ops.addItem(self._describe_operation(op, len(self.model.operations)))
        self.list_ops.setCurrentRow(self.list_ops.count() - 1)
        self._refresh_preview()

    def _handle_delete_operation(self) -> None:
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx < 0:
            return
        self.model.remove_operation(idx)
        self.list_ops.takeItem(idx)
        self._renumber_operations()
        self._refresh_preview()

    def _handle_move_up(self) -> None:
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx <= 0:
            return
        self.model.move_up(idx)
        item = self.list_ops.takeItem(idx)
        self.list_ops.insertItem(idx - 1, item)
        self.list_ops.setCurrentRow(idx - 1)
        self._renumber_operations()
        self._refresh_preview()

    def _handle_move_down(self) -> None:
        if self.list_ops is None:
            return
        idx = self.list_ops.currentRow()
        if idx < 0 or idx >= self.list_ops.count() - 1:
            return
        self.model.move_down(idx)
        item = self.list_ops.takeItem(idx)
        self.list_ops.insertItem(idx + 1, item)
        self.list_ops.setCurrentRow(idx + 1)
        self._renumber_operations()
        self._refresh_preview()

    def _handle_new_program(self) -> None:
        self.model.operations.clear()
        if self.list_ops:
            self.list_ops.clear()
        self._refresh_preview()

    def _handle_generate_gcode(self) -> None:
        """G-Code-Datei erzeugen und im LinuxCNC öffnen."""
        filepath = os.path.expanduser("~/linuxcnc/nc_files/lathe_easystep.ngc")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.model.program_settings = self._collect_program_settings()
        lines = self.model.generate_gcode()
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except OSError:
            return

        try:
            Action.CALLBACK_OPEN_PROGRAM(filepath)
        except Exception:
            # Wenn Action nicht verfügbar ist, wollen wir nicht crashen.
            pass

    def _handle_param_change(self) -> None:
        self._update_selected_operation()

    def _handle_program_change(self) -> None:
        # Aktuell kein direkter Einfluss auf Geometrie, aber
        # wir halten die Settings im Model aktuell.
        self.model.program_settings = self._collect_program_settings()

    def _handle_selection_change(self, row: int) -> None:
        if row < 0 or row >= len(self.model.operations):
            self._refresh_preview()
            return
        op = self.model.operations[row]

        # Tab anhand Operationstyp wählen
        if self.tab_params:
            # Tab-Indizes: 0=Programm,1=Planen,2=Längsdrehen
            idx = 1 if op.op_type == OpType.FACE else 2
            self.tab_params.setCurrentIndex(idx)

        self._load_params_to_form(op)
        self._refresh_preview()

    # ---- Darstellung / Nummerierung --------------------------------------

    def _describe_operation(self, op: Operation, number: int) -> str:
        if op.op_type == OpType.FACE:
            label = "Planen"
        elif op.op_type == OpType.TURN:
            label = "Längsdrehen"
        else:
            label = op.op_type
        return f"{number}: {label}"

    def _renumber_operations(self) -> None:
        if self.list_ops is None:
            return
        for i in range(self.list_ops.count()):
            item = self.list_ops.item(i)
            op = self.model.operations[i]
            item.setText(self._describe_operation(op, i + 1))

    # ---- User-Command-Hook -----------------------------------------------

    def call_user_command_(self, command_file: str | None) -> None:
        """Optionales User-Skript laden (QtVCP-Konvention)."""
        if not command_file or not os.path.isfile(command_file):
            return

        namespace: Dict[str, Any] = {}
        try:
            with open(command_file, "r", encoding="utf-8") as fh:
                code = compile(fh.read(), command_file, "exec")
            exec(code, namespace, namespace)
        except Exception:
            return

        user_command = namespace.get("user_command")
        if callable(user_command):
            try:
                user_command(self)
            except Exception:
                return


# ------------------------- QtVCP Entry Point -------------------------------


def get_handlers(halcomp, widgets, paths):
    """Von QtVCP aufgerufen, um Handler-Instanzen zu erzeugen."""
    return [HandlerClass(halcomp, widgets, paths)]
