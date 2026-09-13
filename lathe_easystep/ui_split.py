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

# LES-024: Step-Liste/Programmverwaltung als eigenes Panel-Modul, nach
# demselben Muster wie die acht Reiter oben - der Container bleibt im
# Geruest (lathe_easystep.ui) leer, der tatsaechliche Inhalt (gleiche
# objectNames wie zuvor direkt im Geruest) kommt aus einer eigenen
# .ui-Datei. Kein anderer Code (Widget-Lookup, Signale, Uebersetzungen)
# musste dafuer angepasst werden, da alle objectNames unveraendert blieben.
STEP_MANAGEMENT_UI_FILES: Dict[str, str] = {
    "stepListPanel": "stepListPanel.ui",
    "stepActionsPanel": "stepActionsPanel.ui",
}


def _load_ui_fragments_into(handler, root: QtWidgets.QWidget, ui_files: Dict[str, str], loaded_flag: str) -> None:
    if getattr(handler, loaded_flag, False):
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
    for container_name, file_name in ui_files.items():
        container = root.findChild(QtWidgets.QWidget, container_name)
        if container is None:
            continue
        ui_file = base_dir / file_name
        if not ui_file.exists():
            continue
        # Skip containers that already contain loaded split content.
        existing_content = container.findChild(QtWidgets.QWidget, f"{container_name}_content")
        if existing_content is not None:
            continue
        content = uic.loadUi(str(ui_file))
        content.setObjectName(f"{container_name}_content")
        if container.layout() is None:
            layout = QtWidgets.QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        else:
            layout = container.layout()
            while layout.count():
                item = layout.takeAt(0)
                child = item.widget()
                if child is not None:
                    child.setParent(None)
        layout.addWidget(content)
        loaded_any = True
    if loaded_any:
        setattr(handler, loaded_flag, True)


def load_split_tab_uis(handler) -> None:
    root = getattr(handler, "root_widget", None)
    if root is None or not isinstance(root, QtWidgets.QWidget):
        return
    _load_ui_fragments_into(handler, root, TAB_UI_FILES, "_split_tabs_loaded")


def load_step_management_uis(handler) -> None:
    root = getattr(handler, "root_widget", None)
    if root is None or not isinstance(root, QtWidgets.QWidget):
        return
    _load_ui_fragments_into(handler, root, STEP_MANAGEMENT_UI_FILES, "_step_management_ui_loaded")


__all__ = [
    "TAB_UI_FILES",
    "STEP_MANAGEMENT_UI_FILES",
    "load_split_tab_uis",
    "load_step_management_uis",
]
