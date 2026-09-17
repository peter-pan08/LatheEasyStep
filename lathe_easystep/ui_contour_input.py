from __future__ import annotations

from typing import Dict, List
from .contour_logic import normalize_arc_side
from .numeric import finite_float


def collect_contour_segments(self) -> List[Dict[str, object]]:
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
        # Edge type can be a QComboBox cell widget (preferred) or a text item
        edge_widget = table.cellWidget(row, 3)
        arc_side_item = table.item(row, 5)
        arc_side_widget = table.cellWidget(row, 5)
        feature_widget = table.cellWidget(row, 6)
        thread_widget = table.cellWidget(row, 7)
        norm_widget = table.cellWidget(row, 8)
        side_widget = table.cellWidget(row, 9)
        orient_widget = table.cellWidget(row, 10)

        mode_raw = mode_item.text().strip().lower() if mode_item else "xz"
        if mode_raw.startswith("xz"):
            mode = "xz"
        elif mode_raw.startswith("x"):
            mode = "x"
        elif mode_raw.startswith("z"):
            mode = "z"
        else:
            mode = "xz"

        # Edge type: prefer stable combo data IDs.
        edge_txt = ""
        try:
            if edge_widget is not None and hasattr(edge_widget, "currentData"):
                edge_txt = str(edge_widget.currentData() or "").strip().lower()
            elif edge_item is not None and edge_item.text():
                edge_txt = edge_item.text().strip().lower()
        except Exception:
            edge_txt = ""
        if not edge_txt:
            edge_txt = "none"

        if edge_txt in ("chamfer", "fase"):
            edge = "chamfer"
        elif edge_txt == "radius":
            edge = "radius"
        else:
            edge = "none"


        # Bogen-Seite (Auto/Außen/Innen) – nur relevant bei Radius
        arc_txt = ""
        try:
            if arc_side_widget is not None and hasattr(arc_side_widget, "currentData"):
                arc_txt = str(arc_side_widget.currentData() or "").strip().lower()
            elif arc_side_item is not None and arc_side_item.text():
                arc_txt = arc_side_item.text().strip().lower()
        except Exception:
            arc_txt = ""

        arc_side = normalize_arc_side(arc_txt)

        feature_type = "none"
        try:
            feature_txt = str(feature_widget.currentData() or "").strip().lower() if feature_widget is not None and hasattr(feature_widget, "currentData") else ""
        except Exception:
            feature_txt = ""
        if feature_txt == "din_relief":
            feature_type = "din_relief"

        thread_size = ""
        norm = ""
        side = "external"
        orientation = "end"
        try:
            if thread_widget is not None and hasattr(thread_widget, "currentData"):
                thread_size = str(thread_widget.currentData() or "").strip().upper()
            if norm_widget is not None and hasattr(norm_widget, "currentData"):
                norm = str(norm_widget.currentData() or "").strip()
            if side_widget is not None and hasattr(side_widget, "currentData"):
                side_txt = str(side_widget.currentData() or "").strip().lower()
                side = "internal" if side_txt == "internal" else "external"
            if orient_widget is not None and hasattr(orient_widget, "currentData"):
                orient_txt = str(orient_widget.currentData() or "").strip().lower()
                orientation = "start" if orient_txt == "start" else "end"
        except Exception:
            pass

        def _to_float(item):
            text = item.text().replace(",", ".").strip() if item else ""
            return finite_float(text, f"Kontur Zeile {row + 1}") if text else 0.0

        x_text = x_item.text().strip() if x_item and x_item.text() else ""
        z_text = z_item.text().strip() if z_item and z_item.text() else ""

        seg = {
            "mode": mode,
            "x": _to_float(x_item) if x_item else 0.0,
            "z": _to_float(z_item) if z_item else 0.0,
            "x_empty": x_text == "",
            "z_empty": z_text == "",
            "edge": edge,
            "edge_size": _to_float(size_item) if size_item else 0.0,
            "arc_side": arc_side,
            "arc_side_raw": arc_txt,
        }
        if feature_type != "none":
            seg["feature"] = {
                "feature_type": feature_type,
                "thread_size": thread_size,
                "norm": norm,
                "side": side,
                "internal": side == "internal",
                "orientation": orientation,
            }
        segments.append(seg)

    return segments
