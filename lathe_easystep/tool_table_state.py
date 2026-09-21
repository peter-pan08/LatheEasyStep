"""Zentraler Werkzeugtabellen-Zustand (LES-052, dritte Etappe).

Ersetzt die bisherigen losen Handler-Attribute `tools`, `_loaded_tools` und
`_missing_iso_tools` durch ein einzelnes typisiertes Objekt
(`handler._tool_table`). Qt-frei; `Tool` selbst (siehe `tools.py`) war
bereits ein sauberes `frozen`-Dataclass, nur der Container drumherum fehlte.

`loaded_tools` ist bewusst ein zweites Feld statt eines Alias auf `tools`:
`set_tools()` aktualisiert es nur bei einer NICHT-leeren Tabelle (siehe
`ui_tools.py::populate_tool_combos()`, dessen Verhalten hier unveraendert
uebernommen wurde) - es dient als "letzte bekannte gute Tabelle"-Cache fuer
das nachtraegliche Befuellen von erst spaeter (lazy) auftauchenden
Werkzeug-Combo-Widgets, waehrend `tools` auch leer sein darf."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .tools import Tool


@dataclass
class ToolTableState:
    tools: Dict[int, "Tool"] = field(default_factory=dict)
    loaded_tools: Dict[int, "Tool"] | None = None
    missing_iso: List[int] = field(default_factory=list)

    def set_tools(self, tools: Dict[int, "Tool"]) -> None:
        self.tools = tools
        if tools:
            self.loaded_tools = tools


__all__ = ["ToolTableState"]
