from __future__ import annotations

"""Schmale View-Schnittstelle auf die Step-Liste (listOperations).

LES-024: buendelt die bisher ueber sechs Module verstreuten direkten
Zugriffe auf ``handler.list_ops`` (QListWidget) hinter benannten Methoden,
damit Fachlogik (ui_dirty/ui_flow/ui_persistence/ui_preview/ui_program/
ui_selection) nicht mehr wissen muss, dass die Step-Liste ein Qt-Widget
ist. Die Bindung/Suche des Widgets selbst (ui_lifecycle/ui_split/
ui_signals/ui_widget_lookup/ui_widgets) bleibt bewusst unveraendert -
dort WIRD ``handler.list_ops`` erst hergestellt.

Zustandslos: liest ``handler.list_ops`` bei jedem Aufruf frisch, damit
spaeteres (Neu-)Binden des Widgets ohne Cache-Invalidierung funktioniert.
"""


class StepListView:
    def __init__(self, handler):
        self._handler = handler

    @property
    def _widget(self):
        return self._handler.list_ops

    def is_bound(self) -> bool:
        return self._widget is not None

    def selected_row(self) -> int:
        widget = self._widget
        if widget is None:
            return -1
        return widget.currentRow()

    def count(self) -> int:
        widget = self._widget
        if widget is None:
            return 0
        return widget.count()

    def row_of(self, item) -> int:
        widget = self._widget
        if widget is None:
            return -1
        return widget.row(item)

    def set_item_text(self, index: int, text: str) -> bool:
        widget = self._widget
        if widget is None:
            return False
        item = widget.item(index)
        if item is None:
            return False
        item.setText(text)
        return True

    def select_row(self, index: int, *, block_signals: bool = False) -> None:
        widget = self._widget
        if widget is None:
            return
        try:
            if block_signals:
                widget.blockSignals(True)
                try:
                    widget.setCurrentRow(index)
                finally:
                    widget.blockSignals(False)
            else:
                widget.setCurrentRow(index)
        except Exception:
            pass

    def has_focus(self) -> bool:
        widget = self._widget
        return widget is not None and bool(widget.hasFocus())
