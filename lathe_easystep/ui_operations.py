from __future__ import annotations

from qtpy import QtCore, QtWidgets

from .ui_contour import RELIEF_NORMS, RELIEF_THREAD_SIZES
from .model import OpType, Operation
from .ui_helpers import current_language as _lang, populate_combo as _populate_combo


CONTOUR_EDGE_OPTIONS = [
    ("none", "combo.contour_edge_type.none"),
    ("chamfer", "combo.contour_edge_type.chamfer"),
    ("radius", "combo.contour_edge_type.radius"),
]
CONTOUR_ARC_OPTIONS = [
    ("auto", "runtime.contour.arc.auto"),
    ("outer", "runtime.contour.arc.outer"),
    ("inner", "runtime.contour.arc.inner"),
]
CONTOUR_FEATURE_OPTIONS = [
    ("none", "runtime.contour.feature.none"),
    ("din_relief", "runtime.contour.feature.din_relief"),
]
CONTOUR_SIDE_OPTIONS = [
    ("external", "runtime.contour.side.external"),
    ("internal", "runtime.contour.side.internal"),
]
CONTOUR_ORIENTATION_OPTIONS = [
    ("end", "runtime.contour.orientation.end"),
    ("start", "runtime.contour.orientation.start"),
]


def load_operation_params_to_form(handler, op: Operation) -> None:
    handler._setup_param_maps()
    if op.op_type == OpType.PROGRAM_HEADER:
        handler._load_program_header_to_form(op.params)
        return

    widgets = handler.param_widgets.get(op.op_type, {})
    for key, widget in widgets.items():
        if widget is None or key not in op.params:
            continue
        widget.blockSignals(True)
        val = op.params[key]
        if isinstance(widget, QtWidgets.QComboBox):
            handled = False
            if key == "slice_strategy":
                handled = handler._select_slice_strategy_index(widget, val)
            if not handled:
                try:
                    data_idx = widget.findData(val)
                except Exception:
                    data_idx = -1
                if data_idx >= 0:
                    widget.setCurrentIndex(data_idx)
                    handled = True
            if not handled:
                try:
                    widget.setCurrentIndex(int(val))
                    handled = True
                except Exception:
                    try:
                        txt = str(val).strip()
                        idx = widget.findText(txt)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                            handled = True
                    except Exception:
                        pass
        elif isinstance(widget, QtWidgets.QAbstractButton):
            widget.setChecked(bool(val))
        else:
            try:
                if isinstance(widget, QtWidgets.QSpinBox):
                    widget.setValue(int(val))
                else:
                    widget.setValue(val)
            except Exception:
                try:
                    widget.setValue(float(val))
                except Exception:
                    pass
        widget.blockSignals(False)

    if op.op_type == OpType.CONTOUR:
        _load_contour_operation_to_form(handler, op)
        return

    if op.op_type == OpType.ABSPANEN and getattr(handler, "parting_contour", None):
        name = str(op.params.get("contour_name") or "")
        handler.parting_contour.blockSignals(True)
        idx = handler.parting_contour.findData(name, QtCore.Qt.UserRole)
        if idx >= 0:
            handler.parting_contour.setCurrentIndex(idx)
        else:
            handler.parting_contour.setCurrentText(name)
        handler.parting_contour.blockSignals(False)
        handler._update_parting_ready_state()
        handler._update_parting_mode_visibility()
    if op.op_type == OpType.GROOVE:
        try:
            handler._update_groove_tab_ui()
        except Exception:
            pass


def _load_contour_operation_to_form(handler, op: Operation) -> None:
    handler._ensure_contour_widgets()
    handler._init_contour_table()

    if getattr(handler, "contour_name", None):
        try:
            handler.contour_name.blockSignals(True)
            handler.contour_name.setText(str(op.params.get("name") or "").strip())
        finally:
            handler.contour_name.blockSignals(False)

    table = getattr(handler, "contour_segments", None)
    if table is not None:
        segs = op.params.get("segments") or []
        table.blockSignals(True)
        table.setRowCount(0)

        def mode_to_text(mode: str) -> str:
            mode = (mode or "xz").lower()
            if mode == "x":
                return "X"
            if mode == "z":
                return "Z"
            return "XZ"

        def edge_to_data(edge: str) -> str:
            edge = (edge or "none").lower()
            if edge in ("chamfer", "fase"):
                return "chamfer"
            if edge == "radius":
                return "radius"
            return "none"

        def make_item(text: str) -> QtWidgets.QTableWidgetItem:
            item = QtWidgets.QTableWidgetItem(text)
            try:
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable
                    | QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsEditable
                )
            except Exception:
                pass
            return item

        for row, seg in enumerate(segs):
            table.insertRow(row)
            mode_txt = mode_to_text(seg.get("mode"))
            x_empty = bool(seg.get("x_empty", False))
            z_empty = bool(seg.get("z_empty", False))
            x_val = "" if x_empty else f"{float(seg.get('x', 0.0)):.3f}"
            z_val = "" if z_empty else f"{float(seg.get('z', 0.0)):.3f}"
            edge_data = edge_to_data(seg.get("edge"))
            size_val = f"{float(seg.get('edge_size', 0.0) or 0.0):.3f}"
            arc_txt = seg.get("arc_side", "auto")
            feature = seg.get("feature") if isinstance(seg.get("feature"), dict) else {}
            feature_type = str(feature.get("feature_type") or "none").strip().lower()
            thread_size_txt = str(feature.get("thread_size") or "").strip().upper()
            norm_txt = str(feature.get("norm") or "").strip()
            side_data = "internal" if bool(feature.get("internal")) or str(feature.get("side") or "").strip().lower() in ("internal", "inner") else "external"
            orient_data = "start" if str(feature.get("orientation") or "end").strip().lower() == "start" else "end"
            lang = _lang(handler)

            table.setItem(row, 0, make_item(mode_txt))
            table.setItem(row, 1, make_item(x_val))
            table.setItem(row, 2, make_item(z_val))

            edge_combo = QtWidgets.QComboBox()
            _populate_combo(edge_combo, CONTOUR_EDGE_OPTIONS, lang, current_value=edge_data)
            edge_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 3, edge_combo)

            table.setItem(row, 4, make_item(size_val))

            arc_combo = QtWidgets.QComboBox()
            _populate_combo(arc_combo, CONTOUR_ARC_OPTIONS, lang, current_value=arc_txt)
            arc_combo.setEnabled(edge_data == "radius")
            arc_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 5, arc_combo)

            feature_combo = QtWidgets.QComboBox()
            _populate_combo(feature_combo, CONTOUR_FEATURE_OPTIONS, lang, current_value=feature_type)
            feature_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 6, feature_combo)

            thread_combo = QtWidgets.QComboBox()
            thread_combo.addItem("", "")
            for value in RELIEF_THREAD_SIZES:
                thread_combo.addItem(value, value)
            if thread_size_txt:
                idx = thread_combo.findData(thread_size_txt, QtCore.Qt.UserRole)
                thread_combo.setCurrentIndex(idx if idx >= 0 else 0)
            thread_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 7, thread_combo)

            norm_combo = QtWidgets.QComboBox()
            norm_combo.addItem("", "")
            for value in RELIEF_NORMS:
                norm_combo.addItem(value, value)
            if norm_txt:
                idx = norm_combo.findData(norm_txt, QtCore.Qt.UserRole)
                norm_combo.setCurrentIndex(idx if idx >= 0 else 0)
            norm_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 8, norm_combo)

            side_combo = QtWidgets.QComboBox()
            _populate_combo(side_combo, CONTOUR_SIDE_OPTIONS, lang, current_value=side_data)
            idx = side_combo.findData(side_data, QtCore.Qt.UserRole)
            side_combo.setCurrentIndex(idx if idx >= 0 else 0)
            side_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 9, side_combo)

            orient_combo = QtWidgets.QComboBox()
            _populate_combo(orient_combo, CONTOUR_ORIENTATION_OPTIONS, lang, current_value=orient_data)
            idx = orient_combo.findData(orient_data, QtCore.Qt.UserRole)
            orient_combo.setCurrentIndex(idx if idx >= 0 else 0)
            orient_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 10, orient_combo)

        table.blockSignals(False)
        if table.rowCount() > 0:
            table.setCurrentCell(0, 0)

    handler._contour_row_user_selected = False
    handler._sync_contour_edge_controls()
    handler._update_contour_preview_temp()
    handler._update_parting_contour_choices()
    handler._update_parting_ready_state()
