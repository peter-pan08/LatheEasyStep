from __future__ import annotations

from qtpy import QtCore, QtGui, QtWidgets
from .translations import TRANSLATIONS
from .ui_registry import UI_TOOLTIP_KEYS


class _TooltipRelay(QtCore.QObject):
    """Force tooltip display on hover for embedded/hosted QtVCP widgets."""

    def __init__(self, parent=None, text: str = ""):
        super().__init__(parent)
        self.text = text

    def eventFilter(self, obj, event):
        etype = event.type() if event is not None else None
        if etype not in (QtCore.QEvent.Enter, QtCore.QEvent.ToolTip):
            return False
        text = ""
        try:
            text = str(obj.toolTip() or "").strip()
        except Exception:
            text = ""
        if not text:
            text = self.text
        if not text:
            return False
        try:
            if etype == QtCore.QEvent.ToolTip and hasattr(event, "globalPos"):
                global_pos = event.globalPos()
            elif hasattr(obj, "rect") and hasattr(obj, "mapToGlobal"):
                global_pos = obj.mapToGlobal(obj.rect().center())
            else:
                global_pos = QtGui.QCursor.pos()
            QtWidgets.QToolTip.showText(global_pos, text, obj)
        except Exception:
            return False
        return etype == QtCore.QEvent.ToolTip



def set_tooltip_deep(self, widget, text: str):
    if widget is None or not text:
        return
    if not hasattr(self, "_tooltip_relays"):
        self._tooltip_relays = {}
    targets = [widget]
    label_name = f"label_{widget.objectName()}" if hasattr(widget, "objectName") else ""
    if label_name:
        label = self._get_widget_by_name(label_name)
        if label is not None:
            targets.append(label)
    try:
        line_edit = widget.lineEdit() if hasattr(widget, "lineEdit") else None
    except Exception:
        line_edit = None
    if line_edit is not None:
        targets.append(line_edit)
    try:
        view = widget.view() if hasattr(widget, "view") else None
    except Exception:
        view = None
    if view is not None:
        targets.append(view)
    try:
        targets.extend(widget.findChildren(QtWidgets.QWidget))
    except Exception:
        pass
    for target in targets:
        try:
            target.setToolTip(text)
        except Exception:
            pass
        try:
            target.setWhatsThis(text)
        except Exception:
            pass
        try:
            target.setStatusTip(text)
        except Exception:
            pass
        try:
            target.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips, True)
        except Exception:
            pass
        try:
            target.setMouseTracking(True)
        except Exception:
            pass
        try:
            target.setToolTipDuration(20000)
        except Exception:
            pass
        try:
            relay = self._tooltip_relays.get(id(target))
            if relay is None:
                relay = _TooltipRelay(target, text)
                target.installEventFilter(relay)
                self._tooltip_relays[id(target)] = relay
            else:
                relay.text = text
        except Exception:
            pass


def fallback_tooltip_text(self, widget) -> str:
    if widget is None:
        return ""
    try:
        name = str(widget.objectName() or "").strip()
    except Exception:
        name = ""
    label_candidates = []
    if name:
        label_candidates.extend(
            [
                f"label_{name}",
                f"label_prog_{name[8:]}" if name.startswith("program_") else "",
                f"label_face_{name[5:]}" if name.startswith("face_") else "",
                f"label_thread_{name[7:]}" if name.startswith("thread_") else "",
                f"label_groove_{name[7:]}" if name.startswith("groove_") else "",
                f"label_drill_{name[6:]}" if name.startswith("drill_") else "",
                f"label_key_{name[4:]}" if name.startswith("key_") else "",
                f"label_parting_{name[8:]}" if name.startswith("parting_") else "",
            ]
        )
    for candidate in [entry for entry in label_candidates if entry]:
        try:
            label = self._get_widget_by_name(candidate)
        except Exception:
            label = None
        if label is None:
            continue
        try:
            text = str(label.text() or "").strip()
        except Exception:
            text = ""
        if text:
            return text
    label = self._form_label_for_widget(widget)
    if label is not None:
        try:
            text = str(label.text() or "").strip()
        except Exception:
            text = ""
        if text:
            return text
    try:
        own_text = str(widget.text() or "").strip() if hasattr(widget, "text") else ""
    except Exception:
        own_text = ""
    return own_text


def apply_registered_tooltips(self, lang: str):
    for name, key in UI_TOOLTIP_KEYS.items():
        widget = self._get_widget_by_name(name)
        if widget is None:
            continue
        text = TRANSLATIONS.tr(key, lang)
        try:
            widget.setProperty("tooltip_key", key)
            widget.setProperty("tooltip_fallback_auto", False)
        except Exception:
            pass
        self._set_tooltip_deep(widget, text)


