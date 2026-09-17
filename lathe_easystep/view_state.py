"""Vorschau-Ansichtszustand (LES-052, fuenfte Kategorie: `ViewState`).

Ersetzt die bisher lose auf `LathePreviewWidget` (`preview_widget.py`)
gefuehrten Attribute (Zoom/Pan/Slice-Position/Ansichtsmodus/Legenden-Auf-
Zu-Zustand) durch ein einzelnes typisiertes, Qt-freies Objekt
(`widget._view`). Anders als bei `DirtyState`/`ToolTableState`/
`RuntimeState` (deren Aufrufstellen ueber viele Module verteilt waren und
deshalb auf `handler._<name>.<feld>` umgestellt wurden) bleibt hier die
gesamte Nutzung innerhalb einer einzigen Klasse. Deshalb: `LathePreviewWidget`
haelt fuer jedes Feld eine gleichnamige `@property`, die transparent an
`self._view.<feld>` delegiert - bestehender Code (intern wie extern, u. a.
mehrere Tests, die `widget.slice_z`/`widget.active_index`/`widget._view_zoom`
direkt lesen/schreiben) funktioniert dadurch unveraendert weiter, ohne dass
eine der 62 Nutzungsstellen in `preview_widget.py` angefasst werden musste.

`_view_pan` (vormals ein `QtCore.QPointF`) wird hier bewusst als zwei reine
`float`-Felder (`pan_x`/`pan_y`) gehalten, nicht als `QPointF` - damit dieses
Modul komplett ohne Qt-Import auskommt und wie die anderen Zustandsklassen
ohne laufende Qt-Anwendung testbar bleibt. Die `_view_pan`-Property auf dem
Widget baut das `QPointF` erst an der Grenze zu Qt."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ViewState:
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    slice_z: float = 0.0
    slice_enabled: bool = False
    view_mode: str = "side"
    active_index: int | None = None
    legend_collapsed: bool = False
    show_legend: bool = True
    status_messages: list[str] = field(default_factory=list)


__all__ = ["ViewState"]
