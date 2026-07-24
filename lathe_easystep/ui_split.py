from __future__ import annotations

from pathlib import Path
from typing import Dict

from qtpy import QtWidgets


TAB_UI_FILES: Dict[str, str] = {
    "tabProgram": "tabProgram.ui",
    "tabFace": "tabFace.ui",
    "tabContour": "tabContour.ui",
    "tabParting": "tabParting.ui",
    "tabThread": "tabThread.ui",
    "tabGroove": "tabGroove.ui",
    "tabDrill": "tabDrill.ui",
    "tabKeyway": "tabKeyway.ui",
}


def load_split_tab_uis(handler) -> None:
    root = getattr(handler, "root_widget", None)
    if root is None or not isinstance(root, QtWidgets.QWidget):
        return
    if getattr(handler, "_split_tabs_loaded", False):
        return
    try:
        from PyQt5 import uic
    except Exception as exc:
        log = getattr(handler, "_log", None)
        if callable(log):
            log(f"[LatheEasyStep] split UI loader unavailable: {exc}", level="warning")
        return

    base_dir = Path(__file__).resolve().parent / "ui_parts"
    loaded_any = False
    for tab_name, file_name in TAB_UI_FILES.items():
        tab = root.findChild(QtWidgets.QWidget, tab_name)
        if tab is None:
            continue
        ui_file = base_dir / file_name
        if not ui_file.exists():
            continue
        # Skip tabs that already contain loaded split content.
        existing_content = tab.findChild(QtWidgets.QWidget, f"{tab_name}_content")
        if existing_content is not None:
            continue
        content = uic.loadUi(str(ui_file))
        content.setObjectName(f"{tab_name}_content")
        if tab.layout() is None:
            layout = QtWidgets.QVBoxLayout(tab)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        else:
            layout = tab.layout()
            while layout.count():
                item = layout.takeAt(0)
                child = item.widget()
                if child is not None:
                    child.setParent(None)
        layout.addWidget(content)
        loaded_any = True
    if loaded_any:
        handler._split_tabs_loaded = True


__all__ = ["TAB_UI_FILES", "load_split_tab_uis"]
