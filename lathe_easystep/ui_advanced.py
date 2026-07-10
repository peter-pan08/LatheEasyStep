from __future__ import annotations

from qtpy import QtCore, QtWidgets

from .presets import relief_thread_sizes


RELIEF_THREAD_SIZES = relief_thread_sizes()


def ensure_advanced_widgets(handler) -> None:
    root = getattr(handler, "root_widget", None) or handler._find_root_widget()
    if root is None:
        return

    _ensure_program_widgets(handler, root)
    _ensure_parting_widgets(handler, root)
    _ensure_thread_widgets(handler, root)
    _ensure_groove_widgets(handler, root)
    _ensure_status_widgets(handler, root)


def _form_layout(root, tab_name: str, layout_name: str):
    tab = root.findChild(QtWidgets.QWidget, tab_name, QtCore.Qt.FindChildrenRecursively)
    if tab is None:
        return None
    layout = tab.findChild(QtWidgets.QFormLayout, layout_name, QtCore.Qt.FindChildrenRecursively)
    if layout is None:
        layout = tab.layout()
    return layout if isinstance(layout, QtWidgets.QFormLayout) else None


def _ensure_row(handler, layout: QtWidgets.QFormLayout, label_name: str, label_text: str, widget):
    existing_widget = getattr(handler, widget.objectName(), None)
    if existing_widget is None:
        existing_widget = handler._get_widget_by_name(widget.objectName())
    if existing_widget is not None:
        setattr(handler, widget.objectName(), existing_widget)
        existing_label = getattr(handler, label_name, None) or handler._get_widget_by_name(label_name)
        if existing_label is not None:
            setattr(handler, label_name, existing_label)
        return existing_widget

    label = QtWidgets.QLabel(label_text)
    label.setObjectName(label_name)
    layout.addRow(label, widget)
    setattr(handler, label_name, label)
    setattr(handler, widget.objectName(), widget)
    return widget


def _combo(items: list[tuple[str, object]], name: str) -> QtWidgets.QComboBox:
    widget = QtWidgets.QComboBox()
    widget.setObjectName(name)
    for text, data in items:
        widget.addItem(text, data)
    return widget


def _double_spin(name: str, suffix: str = "", minimum: float = -100000.0, maximum: float = 100000.0, value: float = 0.0, decimals: int = 3) -> QtWidgets.QDoubleSpinBox:
    widget = QtWidgets.QDoubleSpinBox()
    widget.setObjectName(name)
    widget.setDecimals(decimals)
    widget.setMinimum(minimum)
    widget.setMaximum(maximum)
    widget.setValue(value)
    if suffix:
        widget.setSuffix(suffix)
    return widget


def _check(name: str, text: str) -> QtWidgets.QCheckBox:
    widget = QtWidgets.QCheckBox(text)
    widget.setObjectName(name)
    return widget


def _label(name: str, text: str) -> QtWidgets.QLabel:
    widget = QtWidgets.QLabel(text)
    widget.setObjectName(name)
    return widget


def _ensure_program_widgets(handler, root) -> None:
    layout = _form_layout(root, "tabProgram", "formLayoutProgram")
    if layout is None:
        return
    _ensure_row(
        handler,
        layout,
        "label_program_spindle_mode",
        "Spindelmodus",
        _combo([("Festdrehzahl (G97)", "fixed"), ("CSS (G96)", "css")], "program_spindle_mode"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_spindle_max_rpm",
        "CSS Max-RPM",
        _double_spin("program_spindle_max_rpm", " U/min", minimum=0.0, maximum=50000.0, value=2500.0, decimals=0),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_park_mode",
        "Parkmodus",
        _combo([("Werkzeugwechselpunkt", "toolchange"), ("Freie Parkposition", "end_position")], "program_park_mode"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_toolchange_coords",
        "Werkzeugwechsel-Koordinaten",
        _combo([("Werkstueckkoordinaten", "work"), ("Maschinenkoordinaten (G53)", "machine")], "program_toolchange_coords"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_park_coords",
        "Park-Koordinaten",
        _combo([("Werkstueckkoordinaten", "work"), ("Maschinenkoordinaten (G53)", "machine")], "program_park_coords"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_park_x",
        "Park X",
        _double_spin("program_park_x", " mm", minimum=-10000.0, maximum=10000.0, value=0.0),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_park_z",
        "Park Z",
        _double_spin("program_park_z", " mm", minimum=-10000.0, maximum=10000.0, value=0.0),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_park_sequential",
        "Parkbewegung",
        _check("program_park_sequential", "achsenweise fahren"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_optional_stop_toolchange",
        "Optionalstop Werkzeugwechsel",
        _check("program_optional_stop_toolchange", "M1 vor Werkzeugwechsel"),
    )
    _ensure_row(
        handler,
        layout,
        "label_program_preview_warnings",
        "Sicherheitswarnungen in Vorschau",
        _check("program_preview_warnings", "im Preview markieren"),
    )


def _ensure_parting_widgets(handler, root) -> None:
    layout = _form_layout(root, "tabParting", "formLayoutParting")
    if layout is None:
        return
    _ensure_row(
        handler,
        layout,
        "label_parting_undercut_mode",
        "Hinterschnitt-Modus",
        _combo(
            [
                ("Ignorieren", "ignore"),
                ("Nur Schlichten", "finish_only"),
                ("Separat schruppen", "separate"),
                ("Voll in Kontur", "full"),
            ],
            "parting_undercut_mode",
        ),
    )
    _ensure_row(
        handler,
        layout,
        "label_parting_output_preference",
        "Ausgabe bevorzugen",
        _combo(
            [
                ("Automatisch", "auto"),
                ("Zyklus bevorzugen", "prefer_cycle"),
                ("Ausgeschrieben bevorzugen", "prefer_explicit"),
            ],
            "parting_output_preference",
        ),
    )
    _ensure_row(
        handler,
        layout,
        "label_parting_undercut_tool",
        "Hinterschnitt-Werkzeug",
        _named_combo("parting_undercut_tool"),
    )
    _ensure_row(
        handler,
        layout,
        "label_parting_undercut_spindle",
        "Hinterschnitt-Drehzahl",
        _double_spin("parting_undercut_spindle", " U/min", minimum=0.0, maximum=50000.0, value=1200.0, decimals=0),
    )
    _ensure_row(
        handler,
        layout,
        "label_parting_undercut_feed",
        "Hinterschnitt-Vorschub",
        _double_spin("parting_undercut_feed", " mm/U", minimum=0.0, maximum=1000.0, value=0.15),
    )
    _ensure_row(
        handler,
        layout,
        "label_parting_optional_stop_before_undercut",
        "Optionalstop Hinterschnitt",
        _check("parting_optional_stop_before_undercut", "M1 vor separatem Hinterschnitt"),
    )


def _ensure_thread_widgets(handler, root) -> None:
    layout = _form_layout(root, "tabThread", "formLayoutThread")
    if layout is None:
        return
    _ensure_row(
        handler,
        layout,
        "label_thread_relief_mode",
        "Freistich-Vorschlag",
        _combo([("Aus", "off"), ("DIN-Freistich vorschlagen", "suggest")], "thread_relief_mode"),
    )
    _ensure_row(
        handler,
        layout,
        "label_thread_relief_norm",
        "Freistich-Norm",
        _combo([("DIN 76 Form A", "DIN 76-A"), ("DIN 76 Form B", "DIN 76-B"), ("DIN 76 Form C", "DIN 76-C")], "thread_relief_norm"),
    )
    _ensure_row(
        handler,
        layout,
        "label_thread_optional_stop_before",
        "Optionalstop Gewinde",
        _check("thread_optional_stop_before", "M1 vor Gewinde"),
    )


def _ensure_groove_widgets(handler, root) -> None:
    layout = _form_layout(root, "tabGroove", "formLayoutGroove")
    if layout is None:
        return
    _ensure_row(
        handler,
        layout,
        "label_groove_process_type",
        "Betriebsart",
        _combo([("Einstich", "groove"), ("Abstich", "parting")], "groove_process_type"),
    )


def _ensure_status_widgets(handler, root) -> None:
    button = root.findChild(QtWidgets.QPushButton, "btnSaveChanges", QtCore.Qt.FindChildrenRecursively)
    if button is None or button.parentWidget() is None:
        return
    existing = getattr(handler, "label_dirty_status", None)
    if existing is None:
        existing = root.findChild(QtWidgets.QLabel, "label_dirty_status", QtCore.Qt.FindChildrenRecursively)
    if existing is not None:
        handler.label_dirty_status = existing
        return
    layout = button.parentWidget().layout()
    if layout is None:
        return
    label = _label("label_dirty_status", "Keine offenen Aenderungen")
    try:
        label.setStyleSheet("QLabel { color: #2e7d32; font-weight: 600; }")
    except Exception:
        pass
    layout.insertWidget(max(layout.indexOf(button), 0), label)
    handler.label_dirty_status = label


def _named_combo(name: str) -> QtWidgets.QComboBox:
    widget = QtWidgets.QComboBox()
    widget.setObjectName(name)
    return widget
