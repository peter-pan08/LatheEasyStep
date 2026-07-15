from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

from qtpy import QtWidgets


@lru_cache(maxsize=1)
def load_ui_static_map() -> dict[str, dict[str, object]]:
    ui_path = Path(__file__).resolve().parent.parent / "lathe_easystep.ui"
    tree = ET.parse(ui_path)
    root = tree.getroot()
    mapping: dict[str, dict[str, object]] = {}

    for widget in root.iter("widget"):
        name = widget.get("name") or ""
        if not name:
            continue
        entry = mapping.setdefault(name, {})
        for prop in widget.findall("property"):
            prop_name = prop.get("name") or ""
            string_elem = prop.find("string")
            if string_elem is not None:
                text = (string_elem.text or "").strip()
                # Leere Platzhalter-Strings (z. B. bei Labels, deren Inhalt zur
                # Laufzeit dynamisch gesetzt wird wie Diagramm-/Tool-Previews)
                # sind keine zu uebersetzenden Texte und duerfen nicht als
                # fehlender Uebersetzungsschluessel gemeldet oder mit dem
                # rohen Schluessel ueberschrieben werden.
                if text:
                    entry[prop_name] = text
        items = []
        for item in widget.findall("item"):
            text = ""
            for prop in item.findall("property"):
                if (prop.get("name") or "") != "text":
                    continue
                string_elem = prop.find("string")
                if string_elem is not None:
                    text = (string_elem.text or "").strip()
            if text != "":
                items.append(text)
        if items:
            entry["items"] = items
    return mapping


def ui_required_keys() -> set[str]:
    keys: set[str] = set()
    for name, props in load_ui_static_map().items():
        for prop_name, value in props.items():
            if prop_name == "items":
                for idx, _text in enumerate(value):
                    keys.add(f"ui.{name}.item.{idx}")
            else:
                keys.add(f"ui.{name}.{prop_name}")
    return keys


def apply_ui_static_translations(root_widget, tr, lang: str) -> None:
    static_map = load_ui_static_map()
    for object_name, props in static_map.items():
        widget = root_widget.findChild(QtWidgets.QWidget, object_name)
        if widget is None:
            continue
        for prop_name, value in props.items():
            if prop_name == "items":
                if not hasattr(widget, "setItemText"):
                    continue
                for idx, _text in enumerate(value):
                    try:
                        widget.setItemText(idx, tr(f"ui.{object_name}.item.{idx}", lang))
                    except Exception:
                        pass
                continue
            text = tr(f"ui.{object_name}.{prop_name}", lang)
            try:
                if prop_name == "text" and hasattr(widget, "setText"):
                    widget.setText(text)
                elif prop_name == "toolTip":
                    widget.setToolTip(text)
                elif prop_name == "whatsThis":
                    widget.setWhatsThis(text)
                elif prop_name == "statusTip":
                    widget.setStatusTip(text)
                elif prop_name == "placeholderText" and hasattr(widget, "setPlaceholderText"):
                    widget.setPlaceholderText(text)
                elif prop_name == "suffix" and hasattr(widget, "setSuffix"):
                    widget.setSuffix(text)
                elif prop_name == "windowTitle":
                    widget.setWindowTitle(text)
            except Exception:
                pass
