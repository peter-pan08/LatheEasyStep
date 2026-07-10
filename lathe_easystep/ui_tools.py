from __future__ import annotations

import os
import re

from qtpy import QtCore, QtGui, QtWidgets


def handle_load_tool_table(handler) -> None:
    """Load tool table and refresh all tool widgets."""
    try:
        settings = QtCore.QSettings()
        default_path = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/ToolTableLastDir",
            "LatheEasyStep/LastDialogDir",
            "LatheEasyStep/ToolTablePath",
        )
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            handler.root_widget,
            "Werkzeugtabelle laden",
            default_path,
            "tool.tbl (*.tbl);;Tool Table Dateien (*.tbl);;Alle Dateien (*)",
        )
        if not filepath:
            return

        tools, missing_iso = handler._parse_tool_table(filepath)
        handler.tools = tools
        handler._missing_iso_tools = missing_iso
        handler._populate_tool_combos(tools)
        handler._update_tool_previews()

        if handler.tool_table_path:
            handler.tool_table_path.setText(filepath)
            handler.tool_table_path.setCursorPosition(0)
        if handler.lbl_tool_table_path:
            handler.lbl_tool_table_path.setText(filepath)

        settings.setValue("LatheEasyStep/ToolTablePath", filepath)
        handler._remember_dialog_path(
            settings,
            filepath,
            "LatheEasyStep/ToolTableLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        QtWidgets.QMessageBox.information(
            handler.root_widget or None,
            "LatheEasyStep",
            f"Werkzeugtabelle geladen: {len(tools)} Werkzeuge gefunden.",
        )
        if missing_iso:
            formatted = ", ".join(f"T{num:02d}" for num in missing_iso)
            QtWidgets.QMessageBox.information(
                handler.root_widget or None,
                "ISO fehlt",
                f"ISO-Code/Radius konnte für die folgenden Werkzeuge nicht ermittelt werden (optional):\n{formatted}",
            )
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            handler.root_widget or None,
            "LatheEasyStep",
            f"Fehler beim Laden der Werkzeugtabelle:\n{exc}",
        )


def auto_load_tool_table(handler) -> None:
    """Load the remembered/default tool table quietly during startup."""
    if getattr(handler, "_tool_table_auto_loaded", False):
        return
    handler._tool_table_auto_loaded = True

    candidates: list[str] = []
    try:
        settings = QtCore.QSettings()
        last_path = settings.value("LatheEasyStep/ToolTablePath", "", type=str) or ""
        if last_path:
            candidates.append(last_path)
    except Exception:
        pass

    try:
        local_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tool.tbl"))
        candidates.append(local_default)
    except Exception:
        pass

    for filepath in candidates:
        try:
            if not filepath or not os.path.exists(filepath):
                continue
            tools, missing_iso = handler._parse_tool_table(filepath)
            if not tools:
                continue
            handler.tools = tools
            handler._missing_iso_tools = missing_iso
            handler._populate_tool_combos(tools)
            handler._update_tool_previews()
            if handler.tool_table_path:
                handler.tool_table_path.setText(filepath)
                handler.tool_table_path.setCursorPosition(0)
            if handler.lbl_tool_table_path:
                handler.lbl_tool_table_path.setText(filepath)
            try:
                QtCore.QSettings().setValue("LatheEasyStep/ToolTablePath", filepath)
            except Exception:
                pass
            handler._log(f"[LatheEasyStep] Werkzeugtabelle automatisch geladen: {filepath}", level="info")
            return
        except Exception as exc:
            handler._log(f"[LatheEasyStep] auto-load tool.tbl fehlgeschlagen ({filepath}): {exc}", level="debug")


def populate_tool_combos(handler, tools) -> None:
    """Populate all tool comboboxes with the same set of tools."""
    handler.tools = tools
    if tools:
        handler._loaded_tools = tools
    sorted_tools = sorted(tools.values(), key=lambda t: t.t)
    if sorted_tools:
        items = []
        for tool in sorted_tools:
            extras = []
            if tool.d and tool.d > 0:
                extras.append(f"⌀{tool.d:.2f}".rstrip("0").rstrip(".") if tool.d % 1 else f"⌀{int(tool.d)}")
            if tool.radius_mm and tool.radius_mm > 0:
                extras.append(f"R{tool.radius_mm:.2f}".rstrip("0").rstrip("."))
            label_parts = [f"T{tool.t:02d}"]
            comment = (tool.comment or "").strip()
            if tool.iso_code:
                label_parts.append(tool.iso_code)
            elif comment:
                label_parts.append(comment.split(";")[0].strip())
            if extras:
                label_parts.append(f"({' '.join(extras)})")
            items.append((tool.t, " – ".join(label_parts)))
    else:
        items = []

    combo_names = [
        "face_tool",
        "drill_tool",
        "groove_tool",
        "thread_tool",
        "parting_tool",
        "parting_undercut_tool",
        "key_tool",
    ]
    for combo_name in combo_names:
        combo = getattr(handler, combo_name, None)
        if combo is None:
            combo = handler._get_widget_by_name(combo_name)
        if combo is None or not hasattr(combo, "clear"):
            continue

        previous = combo.currentData() if hasattr(combo, "currentData") else None
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— Werkzeug wählen —", 0)
        for tool_no, text in items:
            combo.addItem(text, tool_no)

        if previous is not None:
            idx = combo.findData(previous)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)


def update_tool_previews(handler) -> None:
    """Update tool preview images for all tool combos."""
    handler._ensure_tool_preview_widgets()
    handler._ensure_tool_preview_calibration_controls()
    handler._reposition_tool_preview_widgets()
    tool_combos = ["face_tool", "drill_tool", "groove_tool", "thread_tool", "parting_tool", "key_tool"]

    for combo_name in tool_combos:
        combo = getattr(handler, combo_name, None)
        img_label = getattr(handler, combo_name + "_img", None)
        if combo is None or img_label is None:
            continue
        handler._style_tool_preview_label(img_label)

        tool_num = handler._tool_number_from_combo(combo)
        tool = handler.tools.get(tool_num)
        if tool:
            try:
                pixmap = handler._render_tool_preview(tool)
                scaled = pixmap.scaled(
                    max(1, img_label.width() - 6),
                    max(1, img_label.height() - 6),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
                img_label.setPixmap(scaled)
                img_label.setText("")
            except Exception as exc:
                handler._log(f"[LatheEasyStep] tool preview render failed for T{tool_num:02d}: {exc}", level="warning")
                lang = handler._current_language_code() if hasattr(handler, "_current_language_code") else "de"
                txt = "Toolfehler" if lang == "de" else "Tool error"
                img_label.setPixmap(handler._render_tool_placeholder(txt))
                img_label.setText("")
        else:
            lang = handler._current_language_code() if hasattr(handler, "_current_language_code") else "de"
            txt = "Tool wählen" if lang == "de" else "Select tool"
            img_label.setPixmap(handler._render_tool_placeholder(txt))
            img_label.setText("")


def ensure_tool_preview_widgets(handler) -> None:
    for combo_name in ("face_tool", "drill_tool", "groove_tool", "thread_tool", "parting_tool", "key_tool"):
        if getattr(handler, combo_name, None) is None:
            try:
                setattr(handler, combo_name, handler._get_widget_by_name(combo_name))
            except Exception:
                pass
    for img_name in ("face_tool_img", "drill_tool_img", "groove_tool_img", "thread_tool_img", "parting_tool_img"):
        if getattr(handler, img_name, None) is None:
            try:
                setattr(handler, img_name, handler._get_widget_by_name(img_name))
            except Exception:
                pass


def style_tool_preview_label(handler, img_label) -> None:
    try:
        min_sz = img_label.minimumSize()
        if min_sz.width() <= 0 or min_sz.height() <= 0:
            img_label.setMinimumSize(96, 96)
        max_sz = img_label.maximumSize()
        if max_sz.width() <= 0 or max_sz.height() <= 0:
            img_label.setMaximumSize(96, 96)
        img_label.setFrameShape(QtWidgets.QFrame.Box)
        img_label.setLineWidth(1)
        img_label.setMidLineWidth(0)
        img_label.setAlignment(QtCore.Qt.AlignCenter)
        img_label.setWordWrap(True)
        img_label.setScaledContents(False)
    except Exception:
        pass


def render_tool_placeholder(_handler, text: str):
    w, h = 96, 96
    pixmap = QtGui.QPixmap(w, h)
    pixmap.fill(QtGui.QColor("#f4f7fb"))

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtGui.QPen(QtGui.QColor("#7a8794"), 1, QtCore.Qt.DashLine))
    painter.drawRect(1, 1, w - 2, h - 2)
    painter.setPen(QtGui.QPen(QtGui.QColor("#9aa5b1"), 1))
    painter.drawLine(18, h - 24, w - 18, 24)
    painter.drawLine(18, 24, w - 18, h - 24)
    painter.setPen(QtGui.QPen(QtGui.QColor("#2d3748"), 1))
    painter.setFont(QtGui.QFont("Arial", 8))
    painter.drawText(QtCore.QRectF(8, h - 30, w - 16, 24), QtCore.Qt.AlignCenter, text)
    painter.end()
    return pixmap


def tool_number_from_combo(_handler, combo) -> int:
    if combo is None:
        return 0
    try:
        data = combo.currentData()
    except Exception:
        data = None

    if isinstance(data, (int, float)):
        try:
            n = int(data)
            if n > 0:
                return n
        except Exception:
            pass

    if isinstance(data, str):
        m = re.search(r"\bT\s*(\d+)\b", data, re.IGNORECASE)
        if not m:
            m = re.search(r"(\d+)", data)
        if m:
            try:
                n = int(m.group(1))
                if n > 0:
                    return n
            except Exception:
                pass

    try:
        txt = combo.currentText() or ""
    except Exception:
        txt = ""
    m = re.search(r"\bT\s*(\d+)\b", txt, re.IGNORECASE)
    if m:
        try:
            n = int(m.group(1))
            if n > 0:
                return n
        except Exception:
            pass
    return 0


def reposition_tool_preview_widgets(handler) -> None:
    if getattr(handler, "_tool_preview_repositioned", False):
        return
    handler._ensure_tool_preview_widgets()

    pairs = [
        ("face_tool", "face_tool_img"),
        ("drill_tool", "drill_tool_img"),
        ("groove_tool", "groove_tool_img"),
        ("thread_tool", "thread_tool_img"),
        ("parting_tool", "parting_tool_img"),
    ]

    moved_any = False
    for combo_name, img_name in pairs:
        combo = getattr(handler, combo_name, None)
        img_label = getattr(handler, img_name, None)
        if combo is None or img_label is None:
            continue
        parent = combo.parentWidget()
        if parent is None:
            continue
        layout = parent.layout()
        if not isinstance(layout, QtWidgets.QFormLayout):
            continue

        row, _role = layout.getWidgetPosition(combo)
        if row < 0:
            continue

        try:
            layout.removeWidget(img_label)
        except Exception:
            pass

        target_row = row + 1
        while layout.itemAt(target_row, QtWidgets.QFormLayout.FieldRole) is not None:
            target_row += 1

        layout.setWidget(target_row, QtWidgets.QFormLayout.FieldRole, img_label)
        handler._style_tool_preview_label(img_label)
        try:
            img_label.show()
        except Exception:
            pass
        moved_any = True

    if moved_any:
        handler._tool_preview_repositioned = True


def ensure_tool_preview_calibration_controls(handler) -> None:
    if getattr(handler, "_tool_preview_calibration_ready", False):
        return
    try:
        existing_offset = handler._get_widget_by_name("tool_preview_orient_offset")
    except Exception:
        existing_offset = None
    try:
        existing_mirror = handler._get_widget_by_name("tool_preview_orient_mirror")
    except Exception:
        existing_mirror = None
    try:
        existing_label = handler._get_widget_by_name("label_tool_preview_orientation")
    except Exception:
        existing_label = None

    if existing_offset is not None and existing_mirror is not None:
        handler.tool_preview_orient_offset = existing_offset
        handler.tool_preview_orient_mirror = existing_mirror
        handler.tool_preview_orient_label = existing_label
        handler._apply_tool_preview_calibration_settings_to_controls()
        handler._tool_preview_calibration_ready = True
        return

    tool_path = getattr(handler, "tool_table_path", None) or handler._get_widget_by_name("tool_table_path")
    load_btn = getattr(handler, "btn_load_tool_table", None) or handler._get_widget_by_name("btn_load_tool_table")

    parent = None
    if tool_path is not None:
        parent = tool_path.parentWidget()
    if parent is None and load_btn is not None:
        parent = load_btn.parentWidget()
    if parent is None:
        return

    layout = parent.layout()
    if layout is None:
        return

    label = QtWidgets.QLabel(parent)
    label.setObjectName("label_tool_preview_orientation")
    label.setText("Vorschau-Lage")

    row_widget = QtWidgets.QWidget(parent)
    row_widget.setObjectName("tool_preview_orientation_row")
    row_layout = QtWidgets.QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)

    offset = QtWidgets.QDoubleSpinBox(row_widget)
    offset.setObjectName("tool_preview_orient_offset")
    offset.setRange(-360.0, 360.0)
    offset.setSingleStep(5.0)
    offset.setDecimals(1)
    offset.setSuffix(" °")
    offset.setToolTip("Winkel-Offset für Werkzeugvorschau (Anzeige)")

    mirror = QtWidgets.QCheckBox(row_widget)
    mirror.setObjectName("tool_preview_orient_mirror")
    mirror.setText("spiegeln")
    mirror.setToolTip("Vorschau-Lage spiegeln (Anzeige)")

    row_layout.addWidget(offset)
    row_layout.addWidget(mirror)
    row_layout.addStretch(1)

    inserted = False
    if isinstance(layout, QtWidgets.QFormLayout):
        insert_row = layout.rowCount()
        layout.insertRow(insert_row, label, row_widget)
        inserted = True
    elif isinstance(layout, QtWidgets.QGridLayout):
        row = layout.rowCount()
        layout.addWidget(label, row, 0)
        layout.addWidget(row_widget, row, 1)
        inserted = True

    if not inserted:
        try:
            label.setParent(None)
            row_widget.setParent(None)
        except Exception:
            pass
        return

    handler.tool_preview_orient_offset = offset
    handler.tool_preview_orient_mirror = mirror
    handler.tool_preview_orient_label = label
    handler._apply_tool_preview_calibration_settings_to_controls()
    handler._tool_preview_calibration_ready = True

    try:
        offset.valueChanged.connect(handler._on_tool_preview_calibration_changed)
    except Exception:
        pass
    try:
        mirror.toggled.connect(handler._on_tool_preview_calibration_changed)
    except Exception:
        pass


def apply_tool_preview_calibration_settings_to_controls(_handler, offset_widget, mirror_widget) -> None:
    if offset_widget is None or mirror_widget is None:
        return
    try:
        settings = QtCore.QSettings()
        offset = float(settings.value("LatheEasyStep/ToolPreviewOrientationOffsetDeg", 0.0))
        mirror = bool(settings.value("LatheEasyStep/ToolPreviewOrientationMirror", False, type=bool))
    except Exception:
        offset = 0.0
        mirror = False

    try:
        offset_widget.blockSignals(True)
        offset_widget.setValue(offset)
        offset_widget.blockSignals(False)
    except Exception:
        pass
    try:
        mirror_widget.blockSignals(True)
        mirror_widget.setChecked(mirror)
        mirror_widget.blockSignals(False)
    except Exception:
        pass


def on_tool_preview_calibration_changed(handler) -> None:
    try:
        offset_widget = getattr(handler, "tool_preview_orient_offset", None)
        mirror_widget = getattr(handler, "tool_preview_orient_mirror", None)
        if offset_widget is None or mirror_widget is None:
            return
        offset = float(offset_widget.value())
        mirror = bool(mirror_widget.isChecked())
        settings = QtCore.QSettings()
        settings.setValue("LatheEasyStep/ToolPreviewOrientationOffsetDeg", offset)
        settings.setValue("LatheEasyStep/ToolPreviewOrientationMirror", mirror)
    except Exception:
        return
    handler._update_tool_previews()
