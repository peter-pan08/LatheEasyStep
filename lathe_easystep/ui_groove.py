from __future__ import annotations

from qtpy import QtCore, QtGui


def setup_groove_tab_ui(handler) -> None:
    try:
        handler.groove_lage = handler._get_widget_by_name("groove_lage")
        handler.groove_ref = handler._get_widget_by_name("groove_ref")
        handler.groove_use_tool_width = handler._get_widget_by_name("groove_use_tool_width")
        handler.groove_cutting_width = handler._get_widget_by_name("groove_cutting_width")
        handler.groove_lage_img = handler._get_widget_by_name("groove_lage_img")
        handler.groove_ref_img = handler._get_widget_by_name("groove_ref_img")
        handler.groove_width = handler._get_widget_by_name("groove_width")
    except Exception:
        return
    if not all([handler.groove_ref, handler.groove_ref_img, handler.groove_use_tool_width, handler.groove_cutting_width]):
        return
    try:
        handler.groove_ref.currentIndexChanged.connect(handler._update_groove_tab_ui)
    except Exception:
        pass
    try:
        handler.groove_use_tool_width.toggled.connect(handler._update_groove_tab_ui)
    except Exception:
        pass
    try:
        handler.groove_width.valueChanged.connect(handler._update_groove_tab_ui)
    except Exception:
        pass
    try:
        if handler.groove_lage is not None:
            handler.groove_lage.currentIndexChanged.connect(handler._update_groove_tab_ui)
    except Exception:
        pass
    handler._update_groove_tab_ui()


def update_groove_tab_ui(handler) -> None:
    try:
        use_tw = bool(handler.groove_use_tool_width.isChecked()) if handler.groove_use_tool_width else False
        if handler.groove_cutting_width:
            handler.groove_cutting_width.setVisible(use_tw)
        lbl = handler._get_widget_by_name("label_groove_cutting_width")
        if lbl:
            lbl.setVisible(use_tw)
        idx = int(handler.groove_lage.currentIndex()) if handler.groove_lage is not None else 0
        lbl_z = handler._get_widget_by_name("label_23")
        if lbl_z:
            if idx in (0, 1):
                lbl_z.setText("Z0 Bezugspunkt (abs)")
            else:
                lbl_z.setText("Z0 Bezugspunkt (abs)")
        handler._render_groove_diagrams()
        handler._refresh_preview()
    except Exception:
        pass


def render_groove_diagrams(handler) -> None:
    try:
        def _mk_pix(w: int, h: int):
            pm = QtGui.QPixmap(w, h)
            pm.fill(QtCore.Qt.transparent)
            return pm
        if handler.groove_lage_img is not None:
            pm = _mk_pix(180, 70)
            p = QtGui.QPainter(pm)
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            pen = QtGui.QPen(QtCore.Qt.white)
            pen.setWidth(2)
            p.setPen(pen)
            p.drawLine(30, 55, 165, 55)
            p.drawLine(30, 55, 30, 10)
            p.drawText(168, 58, "Z")
            p.drawText(22, 12, "X")
            idx = int(handler.groove_lage.currentIndex()) if handler.groove_lage is not None else 0
            if idx in (0, 1):
                if idx == 1:
                    p.drawLine(40, 40, 160, 40)
                    p.drawText(42, 43, "ID")
                    p.drawRect(95, 40, 18, -12)
                else:
                    p.drawLine(40, 25, 160, 25)
                    p.drawText(42, 22, "OD")
                    p.drawRect(95, 25, 18, 18)
            else:
                p.drawLine(80, 15, 80, 55)
                p.drawText(84, 22, "Stirn")
                p.drawRect(80, 30, 20, 12)
                if idx == 2:
                    p.drawLine(130, 20, 95, 20)
                    p.drawLine(95, 20, 103, 16)
                    p.drawLine(95, 20, 103, 24)
                    p.drawText(118, 16, "Z−")
                else:
                    p.drawLine(95, 20, 130, 20)
                    p.drawLine(130, 20, 122, 16)
                    p.drawLine(130, 20, 122, 24)
                    p.drawText(118, 16, "Z+")
            p.end()
            handler.groove_lage_img.setPixmap(pm)
        if handler.groove_ref_img is not None:
            pm = _mk_pix(180, 70)
            p = QtGui.QPainter(pm)
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            p.drawLine(20, 55, 170, 55)
            p.drawText(172, 58, "Z")
            left = 60
            right = 140
            top = 28
            p.drawRect(left, top, right - left, 18)
            try:
                ref = int(handler.groove_ref.currentIndex()) if handler.groove_ref is not None else 0
            except Exception:
                ref = 0
            z0x = left if ref == 1 else right if ref == 2 else (left + right) // 2
            p.drawLine(z0x, 15, z0x, 65)
            p.drawText(z0x + 2, 14, "Z0")
            p.end()
            handler.groove_ref_img.setPixmap(pm)
    except Exception:
        pass
