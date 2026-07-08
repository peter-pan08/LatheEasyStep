from __future__ import annotations

from qtpy import QtCore, QtWidgets

from .model import OpType, Operation


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
        handler.parting_contour.setCurrentText(name)
        handler.parting_contour.blockSignals(False)
        handler._update_parting_ready_state()
        handler._update_parting_mode_visibility()


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

        def edge_to_text(edge: str) -> str:
            edge = (edge or "none").lower()
            if edge in ("chamfer", "fase"):
                return "Fase"
            if edge == "radius":
                return "Radius"
            return "Keine"

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
            edge_txt = edge_to_text(seg.get("edge"))
            size_val = f"{float(seg.get('edge_size', 0.0) or 0.0):.3f}"
            arc_txt = seg.get("arc_side", "auto")

            table.setItem(row, 0, make_item(mode_txt))
            table.setItem(row, 1, make_item(x_val))
            table.setItem(row, 2, make_item(z_val))

            edge_combo = QtWidgets.QComboBox()
            edge_combo.addItems(["Keine", "Fase", "Radius"])
            edge_idx = edge_combo.findText(edge_txt, QtCore.Qt.MatchFixedString)
            edge_combo.setCurrentIndex(edge_idx if edge_idx >= 0 else 0)
            edge_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 3, edge_combo)

            table.setItem(row, 4, make_item(size_val))

            arc_combo = QtWidgets.QComboBox()
            arc_combo.addItems(["Auto", "Außen", "Innen"])
            arc_idx = arc_combo.findText(str(arc_txt).capitalize(), QtCore.Qt.MatchFixedString)
            arc_combo.setCurrentIndex(arc_idx if arc_idx >= 0 else 0)
            arc_combo.setEnabled(edge_txt == "Radius")
            arc_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
            table.setCellWidget(row, 5, arc_combo)

        table.blockSignals(False)
        if table.rowCount() > 0:
            table.setCurrentCell(0, 0)

    handler._contour_row_user_selected = False
    handler._sync_contour_edge_controls()
    handler._update_contour_preview_temp()
    handler._update_parting_contour_choices()
    handler._update_parting_ready_state()
