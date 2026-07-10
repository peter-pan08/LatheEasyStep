from __future__ import annotations

from qtpy import QtCore, QtGui, QtWidgets

from .presets import RELIEF_NORMS, relief_thread_sizes
from .contour_logic import validate_contour_segments_for_profile
from .model import OpType
from .preview_geometry import build_contour_path


RELIEF_THREAD_SIZES = relief_thread_sizes()


def available_contour_names(handler):
    names = []
    contour_idx = 0
    for op in handler.model.operations:
        if op is None or op.op_type != OpType.CONTOUR:
            continue
        name = handler._contour_name_or_fallback(op, contour_idx)
        if name and name not in names:
            names.append(name)
        contour_idx += 1
    if getattr(handler, "contour_name", None):
        live_name = handler.contour_name.text().strip()
        if not live_name and getattr(handler, "contour_segments", None) and handler.contour_segments.rowCount() > 0:
            live_name = handler._fallback_contour_name(handler._contour_count())
            try:
                handler.contour_name.blockSignals(True)
                handler.contour_name.setText(live_name)
            finally:
                handler.contour_name.blockSignals(False)
        if live_name and live_name not in names:
            names.append(live_name)
    return names


def current_parting_contour_name(handler) -> str:
    if getattr(handler, "parting_contour", None) is None:
        handler.parting_contour = handler._get_widget_by_name("parting_contour")
    if getattr(handler, "parting_contour", None) is None:
        return ""
    return handler.parting_contour.currentText().strip()


def debug_contour_state(handler, context: str = "") -> None:
    if not getattr(handler, "_verbose_widget_logs", False):
        return
    prefix = f"[LatheEasyStep][debug] parting contour ({context})" if context else "[LatheEasyStep][debug] parting contour"
    try:
        op_infos = []
        contour_idx = 0
        for idx, op in enumerate(handler.model.operations):
            if op.op_type != OpType.CONTOUR:
                continue
            name = handler._contour_name_or_fallback(op, contour_idx)
            segs = op.params.get("segments") if isinstance(op.params, dict) else None
            seg_count = len(segs) if isinstance(segs, list) else "n/a"
            path_len = len(op.path) if getattr(op, "path", None) else 0
            op_infos.append(f"op#{idx} contour_idx={contour_idx} name='{name}' segments={seg_count} path_len={path_len}")
            contour_idx += 1
        live_name = handler.contour_name.text().strip() if getattr(handler, "contour_name", None) else ""
        live_rows = handler.contour_segments.rowCount() if getattr(handler, "contour_segments", None) else 0
        available = handler._available_contour_names()
        handler._log(prefix, level="info")
        handler._log(f"  ops: {op_infos if op_infos else 'keine Kontur-Operationen'}", level="warning")
        handler._log(f"  live contour widget name='{live_name}' rows={live_rows}", level="info")
        handler._log(f"  available names for parting: {available}", level="info")
        if getattr(handler, "parting_contour", None):
            current = handler.parting_contour.currentText().strip()
            handler._log(f"  parting combo current text='{current}' editable={handler.parting_contour.isEditable()}", level="info")
    except Exception as exc:
        handler._log(f"[LatheEasyStep][debug] parting contour debug failed: {exc}", level="debug")


def resolve_contour_path(handler, contour_name: str):
    if not contour_name:
        return []
    contour_idx = 0
    for op in handler.model.operations:
        if op.op_type != OpType.CONTOUR:
            continue
        name = handler._contour_name_or_fallback(op, contour_idx)
        if name != contour_name:
            contour_idx += 1
            continue
        if not op.path:
            handler.model.update_geometry(op)
        try:
            return list(op.path or [])
        except Exception:
            return []
        finally:
            contour_idx += 1
    if getattr(handler, "contour_name", None) and getattr(handler, "contour_segments", None) and handler.contour_name.text().strip() == contour_name:
        try:
            return build_contour_path(
                {
                    "start_x": handler.contour_start_x.value() if getattr(handler, "contour_start_x", None) else 0.0,
                    "start_z": handler.contour_start_z.value() if getattr(handler, "contour_start_z", None) else 0.0,
                    "coord_mode": handler.contour_coord_mode.currentIndex() if getattr(handler, "contour_coord_mode", None) else 0,
                    "segments": handler._collect_contour_segments(),
                }
            )
        except Exception:
            return []
    return []


def update_parting_contour_choices(handler) -> None:
    if getattr(handler, "parting_contour", None) is None:
        handler.parting_contour = handler._get_widget_by_name("parting_contour")
    if getattr(handler, "parting_contour", None) is None:
        handler._log("[LatheEasyStep][debug] parting_contour widget not found -> skip refresh", level="debug")
        return
    names = handler._available_contour_names()
    current = handler.parting_contour.currentText().strip()
    existing = [handler.parting_contour.itemText(i).strip() for i in range(handler.parting_contour.count())]
    if getattr(handler, "_startup_in_progress", False) and getattr(handler, "_parting_choices_initialized", False):
        if existing == names:
            handler._update_parting_ready_state()
            return
    if existing == names and (not current or current == handler._current_parting_contour_name()):
        handler._update_parting_ready_state()
        return
    handler._debug_contour_state("before refresh")
    handler.parting_contour.blockSignals(True)
    handler.parting_contour.clear()
    for name in names:
        handler.parting_contour.addItem(name)
    if current:
        handler.parting_contour.setCurrentText(current)
    elif names:
        handler.parting_contour.setCurrentIndex(0)
    handler.parting_contour.blockSignals(False)
    handler._parting_choices_initialized = True
    handler._update_parting_ready_state()
    handler._debug_contour_state("after refresh")


def update_parting_ready_state(handler, *args, **kwargs) -> None:
    if handler.btn_add is None:
        return
    if handler._current_op_type() != OpType.ABSPANEN:
        handler.btn_add.setEnabled(True)
        return
    if getattr(handler, "parting_contour", None) is None:
        handler.parting_contour = handler._get_widget_by_name("parting_contour")
    if getattr(handler, "parting_contour", None) is None:
        handler.btn_add.setEnabled(False)
        return
    available = handler._available_contour_names()
    name = handler._current_parting_contour_name()
    ready = bool(name) and name in available
    handler.btn_add.setEnabled(ready)


def update_parting_mode_visibility(handler) -> None:
    mode_idx = handler.parting_mode.currentIndex() if handler.parting_mode else 0
    show_roughing = mode_idx == 0
    undercut_mode = ""
    if getattr(handler, "parting_undercut_mode", None) is not None:
        try:
            undercut_mode = str(handler.parting_undercut_mode.currentData() or handler.parting_undercut_mode.currentText() or "")
        except Exception:
            undercut_mode = ""
    show_separate_relief = str(undercut_mode).strip().lower() == "separate"
    for widget in (
        handler.label_parting_depth,
        handler.parting_depth_per_pass,
        handler.label_parting_pause,
        handler.parting_pause_enabled,
        handler.label_parting_pause_distance,
        handler.parting_pause_distance,
        handler.label_parting_slice_strategy,
        handler.parting_slice_strategy,
        getattr(handler, "label_parting_allow_undercut", None),
        handler.parting_allow_undercut,
        getattr(handler, "label_parting_finish_allow_x", None),
        getattr(handler, "parting_finish_allow_x", None),
        getattr(handler, "label_parting_finish_allow_z", None),
        getattr(handler, "parting_finish_allow_z", None),
        getattr(handler, "label_parting_undercut_mode", None),
        getattr(handler, "parting_undercut_mode", None),
        getattr(handler, "label_parting_output_preference", None),
        getattr(handler, "parting_output_preference", None),
    ):
        if widget is not None:
            widget.setVisible(show_roughing)
    for widget in (
        getattr(handler, "label_parting_undercut_tool", None),
        getattr(handler, "parting_undercut_tool", None),
        getattr(handler, "label_parting_undercut_spindle", None),
        getattr(handler, "parting_undercut_spindle", None),
        getattr(handler, "label_parting_undercut_feed", None),
        getattr(handler, "parting_undercut_feed", None),
        getattr(handler, "label_parting_optional_stop_before_undercut", None),
        getattr(handler, "parting_optional_stop_before_undercut", None),
    ):
        if widget is not None:
            widget.setVisible(show_roughing and show_separate_relief)
    for hidden_widget in (getattr(handler, "label_parting_slice_step", None), getattr(handler, "parting_slice_step", None)):
        if hidden_widget is not None:
            hidden_widget.setVisible(False)


def init_contour_table(handler) -> None:
    table = handler.contour_segments
    if table is None:
        return
    table.setColumnCount(11)
    table.setHorizontalHeaderLabels(["Typ", "X", "Z", "Kante", "Maß", "Bogen", "Feature", "Gewinde", "Norm", "Seite", "Ort"])
    try:
        table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
    except Exception:
        pass
    try:
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
    except Exception:
        pass
    try:
        table.setStyleSheet(
            "QTableWidget { background: #f5f5f5; color: #000000; gridline-color: #808080; }"
            "QHeaderView::section { background: #d0d0d0; color: #000000; }"
            "QTableWidget::item { color: #000000; background: #ffffff; }"
        )
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
    except Exception:
        pass
    try:
        widths = [60, 80, 80, 80, 80, 80, 110, 90, 90, 80, 70]
        for i, w in enumerate(widths):
            table.setColumnWidth(i, w)
    except Exception:
        pass


def handle_contour_add_segment(handler) -> None:
    handler._ensure_contour_widgets()
    table = handler.contour_segments
    if table is None:
        return
    handler._init_contour_table()
    row = table.rowCount()
    existing_segments = handler._collect_contour_segments()
    x0 = handler.contour_start_x.value() if handler.contour_start_x else 0.0
    z0 = handler.contour_start_z.value() if handler.contour_start_z else 0.0
    last_x = float(existing_segments[-1].get("x", x0)) if existing_segments else x0
    last_z = float(existing_segments[-1].get("z", z0)) if existing_segments else z0
    default_x = last_x
    default_z = last_z
    table.insertRow(row)

    def _mk_item(text):
        it = QtWidgets.QTableWidgetItem(text)
        try:
            it.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        except Exception:
            pass
        try:
            it.setForeground(QtGui.QBrush(QtGui.QColor("#000000")))
            it.setBackground(QtGui.QBrush(QtGui.QColor("#ffffff")))
        except Exception:
            pass
        return it

    table.setItem(row, 0, _mk_item("XZ"))
    table.setItem(row, 1, _mk_item(f"{default_x:.3f}"))
    table.setItem(row, 2, _mk_item(f"{default_z:.3f}"))
    edge_text = handler._contour_edge_template_text
    edge_size = handler._contour_edge_template_size if edge_text.lower().startswith(("f", "r")) else 0.0
    edge_combo = QtWidgets.QComboBox()
    edge_combo.addItems(["Keine", "Fase", "Radius"])
    idx = edge_combo.findText(edge_text, QtCore.Qt.MatchContains)
    edge_combo.setCurrentIndex(idx if idx >= 0 else 0)
    edge_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 3, edge_combo)
    table.setItem(row, 4, _mk_item(f"{edge_size:.3f}"))
    arc_text = getattr(handler, "_contour_arc_template_text", "Auto")
    arc_combo = QtWidgets.QComboBox()
    arc_combo.addItems(["Auto", "Außen", "Innen"])
    idx = arc_combo.findText(arc_text, QtCore.Qt.MatchFixedString)
    arc_combo.setCurrentIndex(idx if idx >= 0 else 0)
    arc_combo.setEnabled("Radius" in (edge_combo.currentText() if edge_combo else edge_text))
    arc_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 5, arc_combo)
    feature_combo = QtWidgets.QComboBox()
    feature_combo.addItems(["Keine", "DIN-Freistich"])
    feature_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 6, feature_combo)
    thread_combo = QtWidgets.QComboBox()
    thread_combo.addItems([""] + RELIEF_THREAD_SIZES)
    thread_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 7, thread_combo)
    norm_combo = QtWidgets.QComboBox()
    norm_combo.addItems([""] + RELIEF_NORMS)
    norm_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 8, norm_combo)
    side_combo = QtWidgets.QComboBox()
    side_combo.addItems(["Außen", "Innen"])
    side_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 9, side_combo)
    orient_combo = QtWidgets.QComboBox()
    orient_combo.addItems(["Ende", "Start"])
    orient_combo.currentIndexChanged.connect(handler._handle_contour_table_change)
    table.setCellWidget(row, 10, orient_combo)
    table.setCurrentCell(row, 0)
    try:
        table.setRowHeight(row, 22)
        table.show()
        table.raise_()
    except Exception:
        pass
    try:
        cells = []
        for r in range(table.rowCount()):
            cells.append([table.item(r, c).text() if table.item(r, c) else "" for c in range(table.columnCount())])
        handler._log(f"[LatheEasyStep][debug] contour rows={table.rowCount()} data={cells}", level="debug")
    except Exception:
        pass
    handler._contour_row_user_selected = False
    handler._update_selected_operation()
    handler._update_contour_preview_temp()
    handler._sync_contour_edge_controls()


def handle_contour_delete_segment(handler) -> None:
    table = handler.contour_segments
    if table is None:
        return
    row = table.currentRow()
    if row >= 0:
        table.removeRow(row)
        handler._update_selected_operation()
        handler._update_contour_preview_temp()
        handler._sync_contour_edge_controls()


def handle_contour_move_up(handler) -> None:
    table = handler.contour_segments
    if table is None:
        return
    row = table.currentRow()
    if row <= 0:
        return
    table.insertRow(row - 1)
    for col in range(table.columnCount()):
        item = table.takeItem(row + 1, col)
        table.setItem(row - 1, col, item)
        try:
            w = table.cellWidget(row + 1, col)
            if w is not None:
                table.removeCellWidget(row + 1, col)
                table.setCellWidget(row - 1, col, w)
        except Exception:
            pass
    table.removeRow(row + 1)
    table.setCurrentCell(row - 1, 0)
    handler._update_selected_operation()
    handler._update_contour_preview_temp()


def handle_contour_move_down(handler) -> None:
    table = handler.contour_segments
    if table is None:
        return
    row = table.currentRow()
    if row < 0 or row >= table.rowCount() - 1:
        return
    table.insertRow(row + 2)
    for col in range(table.columnCount()):
        item = table.takeItem(row, col)
        table.setItem(row + 2, col, item)
        try:
            w = table.cellWidget(row, col)
            if w is not None:
                table.removeCellWidget(row, col)
                table.setCellWidget(row + 2, col, w)
        except Exception:
            pass
    table.removeRow(row)
    table.setCurrentCell(row + 1, 0)
    handler._update_selected_operation()
    handler._update_contour_preview_temp()
    handler._sync_contour_edge_controls()


def handle_contour_table_change(handler, *args, **kwargs) -> None:
    handler._update_selected_operation()
    handler._update_contour_preview_temp()
    handler._sync_contour_edge_controls()


def handle_contour_row_select(handler, *args, **kwargs) -> None:
    table = handler.contour_segments
    handler._contour_row_user_selected = bool(table and table.currentRow() >= 0)
    handler._sync_contour_edge_controls()


def handle_contour_edge_change(handler, *args, **kwargs) -> None:
    edge_text = handler.contour_edge_type.currentText() if handler.contour_edge_type else ""
    edge_size = handler.contour_edge_size.value() if handler.contour_edge_size else 0.0
    handler._contour_edge_template_text = edge_text
    handler._contour_edge_template_size = edge_size
    table = handler.contour_segments
    if table is not None and table.currentRow() >= 0:
        handler._write_contour_row(table.currentRow(), edge_text=edge_text, edge_size=edge_size)
        handler._update_selected_operation()
        handler._update_contour_preview_temp()
    handler._sync_contour_edge_controls()


def update_contour_preview_temp(handler) -> None:
    try:
        segs = handler._collect_contour_segments()
        if not segs:
            handler._set_preview_paths([])
            return
        params = {
            "start_x": getattr(handler, "contour_start_x", None).value() if getattr(handler, "contour_start_x", None) else 0.0,
            "start_z": getattr(handler, "contour_start_z", None).value() if getattr(handler, "contour_start_z", None) else 0.0,
            "coord_mode": getattr(handler, "contour_coord_mode", None).currentIndex() if getattr(handler, "contour_coord_mode", None) else 0,
            "segments": segs,
        }
        _ok, errs = validate_contour_segments_for_profile(params)
        if errs:
            handler._log("[LatheEasyStep][contour][INVALID]", level="error")
            for err in errs:
                handler._log("  -", err, level="info")
            handler._set_preview_paths([])
            return
        primitives = build_contour_path(params)
        handler._set_preview_paths([primitives])
    except Exception as exc:
        handler._log("[LatheEasyStep] _update_contour_preview_temp ERROR:", exc, level="error")
        handler._set_preview_paths([])


def sync_contour_edge_controls(handler) -> None:
    table = handler.contour_segments
    if table is None:
        return
    row = table.currentRow()
    edge_txt = handler._contour_edge_template_text
    size_val = handler._contour_edge_template_size
    if row >= 0:
        edge_item = table.item(row, 3)
        edge_widget = table.cellWidget(row, 3)
        size_item = table.item(row, 4)
        if edge_widget is not None and hasattr(edge_widget, "currentText"):
            edge_txt = str(edge_widget.currentText()).strip()
        elif edge_item and edge_item.text():
            edge_txt = edge_item.text().strip()
        if size_item and size_item.text():
            try:
                size_val = float(size_item.text())
            except Exception:
                size_val = 0.0
    if handler.contour_edge_type:
        idx = handler.contour_edge_type.findText(edge_txt, QtCore.Qt.MatchFixedString)
        if idx < 0:
            idx = 0
        handler.contour_edge_type.blockSignals(True)
        handler.contour_edge_type.setCurrentIndex(idx)
        handler.contour_edge_type.blockSignals(False)
    edge_txt_ctrl = handler.contour_edge_type.currentText() if handler.contour_edge_type else edge_txt
    enable_size = edge_txt_ctrl.lower().startswith("f") or edge_txt_ctrl.lower().startswith("r")
    if handler.label_contour_edge_size:
        handler.label_contour_edge_size.setVisible(True)
        handler.label_contour_edge_size.setEnabled(True)
    if handler.contour_edge_size:
        handler.contour_edge_size.blockSignals(True)
        handler.contour_edge_size.setVisible(True)
        handler.contour_edge_size.setEnabled(enable_size)
        handler.contour_edge_size.setValue(size_val)
        handler.contour_edge_size.blockSignals(False)
