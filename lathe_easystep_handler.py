"""QtVCP conversational lathe panel with 2D preview and G-code generation."""

from __future__ import annotations

import json
import time
import builtins

import math
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from weakref import WeakSet

from qtpy import QtCore, QtGui, QtWidgets
from qtvcp.core import Action


# ----------------------------------------------------------------------
# Operation types
# ----------------------------------------------------------------------
class OpType:
    PROGRAM_HEADER = "program_header"
    FACE = "face"
    CONTOUR = "contour"
    TURN = "turn"
    BORE = "bore"
    THREAD = "thread"
    GROOVE = "groove"
    DRILL = "drill"
    KEYWAY = "keyway"
    ABSPANEN = "abspanen"


_TOOL_KIND_BY_ORIENTATION: Dict[int, str] = {
    0: "turning",
    1: "drilling",
    2: "drilling",
    3: "drilling",
    4: "grooving",
    5: "grooving",
    6: "grooving",
    7: "grooving",
    8: "threading",
    9: "threading",
}
_ISO_PATTERN = re.compile(r"\b([A-Z]{2,}[A-Z0-9]*?)(\d{2})\b")


@dataclass
class Operation:
    op_type: str
    params: Dict[str, object]
    path: list = field(default_factory=list)  # list of points or primitives


@dataclass(frozen=True)
class Tool:
    """Structured view of a LinuxCNC tool entry (for UI + compensation logic)."""

    t: int
    p: int
    d: float
    q: int | None
    comment: str
    iso_code: str | None
    iso_size: str | None
    radius_mm: float
    kind: str
    wear: bool = False
    radius_source: str | None = None

    @property
    def toolno(self) -> int:
        return self.t

    @property
    def orientation(self) -> int | None:
        return self.q

    def __getitem__(self, key):
        if key == "toolno":
            return self.toolno
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"{key!r} is not part of Tool")

    def get(self, key, default=None):
        if key == "toolno":
            return self.toolno
        if hasattr(self, key):
            return getattr(self, key)
        return default


STANDARD_METRIC_THREAD_SPECS: List[Tuple[str, float, float]] = [
    ("M2", 2.0, 0.4),
    ("M2.5", 2.5, 0.45),
    ("M3", 3.0, 0.5),
    ("M3.5", 3.5, 0.6),
    ("M4", 4.0, 0.7),
    ("M5", 5.0, 0.8),
    ("M6", 6.0, 1.0),
    ("M7", 7.0, 1.0),
    ("M8", 8.0, 1.25),
    ("M9", 9.0, 1.25),
    ("M10", 10.0, 1.5),
    ("M11", 11.0, 1.5),
    ("M12", 12.0, 1.75),
    ("M13", 13.0, 1.75),
    ("M14", 14.0, 2.0),
    ("M15", 15.0, 2.0),
    ("M16", 16.0, 2.0),
    ("M17", 17.0, 2.0),
    ("M18", 18.0, 2.5),
    ("M19", 19.0, 2.5),
    ("M20", 20.0, 2.5),
    ("M21", 21.0, 2.5),
    ("M22", 22.0, 2.5),
    ("M23", 23.0, 3.0),
    ("M24", 24.0, 3.0),
    ("M25", 25.0, 3.0),
]
STANDARD_TR_THREAD_SPECS: List[Tuple[str, float, float]] = [
    ("Tr 10", 10.0, 2.0),
    ("Tr 12", 12.0, 3.0),
    ("Tr 14", 14.0, 3.0),
    ("Tr 16", 16.0, 4.0),
    ("Tr 18", 18.0, 4.0),
    ("Tr 20", 20.0, 4.0),
    ("Tr 22", 22.0, 5.0),
    ("Tr 24", 24.0, 5.0),
    ("Tr 26", 26.0, 5.0),
    ("Tr 28", 28.0, 5.0),
    ("Tr 30", 30.0, 6.0),
    ("Tr 32", 32.0, 6.0),
    ("Tr 36", 36.0, 6.0),
    ("Tr 40", 40.0, 7.0),
    # Zusätzliche TR-Größen (erweiterte Auswahl)
    ("Tr 45", 45.0, 7.0),
    ("Tr 50", 50.0, 8.0),
    ("Tr 55", 55.0, 8.0),
    ("Tr 60", 60.0, 10.0),
]
THREAD_ORIENTATION_LABELS: Tuple[str, str] = ("Aussen", "Innen")
DRILL_MODE_LABELS: Tuple[str, str, str] = (
    "Normal",
    "Spanbruch",
    "Spanbruch + Rückzug",
)

DEFAULT_LANGUAGE = "de"
LANGUAGE_WIDGET_NAME = "program_language"

TAB_TRANSLATIONS = {
    "tabProgram": {"de": "Programm", "en": "Program"},
    "tabFace": {"de": "Planen", "en": "Facing"},
    "tabContour": {"de": "Kontur", "en": "Contour"},
    "tabParting": {"de": "Abspanen", "en": "Parting"},
    "tabThread": {"de": "Gewinde", "en": "Thread"},
    "tabGroove": {"de": "Einstich/Abstich", "en": "Groove/Parting"},
    "tabDrill": {"de": "Bohren", "en": "Drilling"},
    "tabKeyway": {"de": "Keilnut", "en": "Keyway"},
}
TAB_ORDER = [
    "tabProgram",
    "tabFace",
    "tabContour",
    "tabParting",
    "tabThread",
    "tabGroove",
    "tabDrill",
    "tabKeyway",
]
# Root objectName variants depending on how the panel is launched:
# - embedded in LinuxCNC: often the .ui root is a QMainWindow named 'MainWindow'
# - standalone qtvcp panel: often 'lathe_easystep_panel'
# - other possible names depending on template/setup
PANEL_WIDGET_NAMES = (
    'LatheConversationalPanel',
    'lathe_easystep',
    'lathe_easystep_panel',
    'easystep',
    'lathe-easystep',
    'lathe-easystep_panel',
    'lathe-easystep-panel',
    'MainWindow',
    'VCPWindow',
)
TEXT_TRANSLATIONS = {
    "label_prog_npv": {"de": "Nullpunktverschiebung", "en": "Work Offset"},
    "label_prog_unit": {"de": "Maßeinheit", "en": "Units"},
    "label_prog_shape": {"de": "Rohteilform", "en": "Stock Shape"},
    "label_prog_xa": {"de": "XA Außendurchmesser (mm)", "en": "XA Outer Diameter (mm)"},
    "label_prog_xi": {"de": "XI Innendurchmesser (mm)", "en": "XI Inner Diameter (mm)"},
    "label_prog_za": {"de": "ZA Anfangsmaß (mm)", "en": "ZA Start Z (mm)"},
    "label_prog_zi": {"de": "ZI Endmaß (mm)", "en": "ZI End Z (mm)"},
    "label_prog_zb": {"de": "ZB Bearbeitungsmaß (mm)", "en": "ZB Machining Z (mm)"},
    "label_prog_w": {"de": "Breite W (mm)", "en": "Width W (mm)"},
    "label_prog_l": {"de": "Länge L (mm)", "en": "Length L (mm)"},
    "label_prog_n": {"de": "Kantenanzahl N", "en": "Edge Count N"},
    "label_prog_sw": {"de": "Schlüsselweite SW (mm)", "en": "Key Width SW (mm)"},
    "label_prog_retract_mode": {"de": "Rückzug", "en": "Retract"},
    "label_prog_xra": {"de": "XRA äußere Rückzugsebene (mm)", "en": "XRA Outer Retract Plane (mm)"},
    "label_prog_xri": {"de": "XRI innere Rückzugsebene (mm)", "en": "XRI Inner Retract Plane (mm)"},
    "label_prog_zra": {"de": "ZRA äußere Rückzugsebene (mm)", "en": "ZRA Outer Retract Plane (mm)"},
    "label_prog_zri": {"de": "ZRI innere Rückzugsebene (mm)", "en": "ZRI Inner Retract Plane (mm)"},
    "label_prog_xt": {"de": "Werkzeugwechsel XT (mm)", "en": "XT Tool Change (mm)"},
    "label_prog_zt": {"de": "Werkzeugwechsel ZT (mm)", "en": "ZT Tool Change (mm)"},
    "label_prog_sc": {"de": "Sicherheitsabstand SC (mm)", "en": "Safety Clearance SC (mm)"},
    "label_prog_s1": {"de": "max. Drehzahl S1 (U/min)", "en": "Max Spindle S1 (RPM)"},
    "label_prog_s3": {"de": "max. Drehzahl S3 (U/min)", "en": "Max Spindle S3 (RPM)"},
    "program_has_subspindle": {"de": "Gegenspindel vorhanden", "en": "Subspindle available"},
    "label_prog_name": {"de": "Programmname", "en": "Program Name"},
    "label_language": {"de": "Sprache", "en": "Language"},

    "label_face_start_x": {"de": "Start-X (Roh-Ø)", "en": "Start X (Raw ø)"},
    "label_face_start_z": {"de": "Start-Z", "en": "Start Z"},
    "label_face_end_x": {"de": "End-X", "en": "End X"},
    "label_face_end_z": {"de": "End-Z", "en": "End Z"},
    "label_face_mode": {"de": "Strategie", "en": "Strategy"},
    "label_face_finish_direction": {"de": "Schlichtrichtung", "en": "Finish Direction"},
    "label_face_depth_max": {"de": "max. Zustellung", "en": "Max Depth"},
    "label_face_finish_allow_x": {"de": "Schlichtaufmaß X", "en": "Finish Allowance X"},
    "label_face_finish_allow_z": {"de": "Schlichtaufmaß Z", "en": "Finish Allowance Z"},
    "label_face_edge_type": {"de": "Kantenform", "en": "Edge Type"},
    "label_face_edge_size": {"de": "Kantengröße", "en": "Edge Size"},
    "label_3": {"de": "Sicherheits-Z", "en": "Safety Z"},
    "label_4": {"de": "Vorschub", "en": "Feed"},
    "label_face_pause": {"de": "Vorschubunterbrechung", "en": "Feed Interrupt"},
    "face_pause_enabled": {"de": "aktivieren", "en": "Enable"},
    "label_face_pause_distance": {"de": "Unterbrechungsabstand", "en": "Pause Distance"},
    "label_face_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_face_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_face_coolant": {"de": "Kühlung", "en": "Coolant"},
    "face_coolant": {"de": "Kühlmittel einschalten", "en": "Enable coolant"},

    "label_contour_start_x": {"de": "Start X", "en": "Start X"},
    "label_contour_start_z": {"de": "Start Z", "en": "Start Z"},
    "label_contour_coord_mode": {"de": "Koordinaten", "en": "Coordinates"},
    "label_contour_name": {"de": "Konturname", "en": "Contour Name"},
    "contour_add_segment": {"de": "Segment +", "en": "Segment +"},
    "contour_delete_segment": {"de": "Segment -", "en": "Segment -"},
    "label_contour_edge_type": {"de": "Kante", "en": "Edge"},
    "label_contour_edge_size": {"de": "Kantenmaß", "en": "Edge Size"},

    "label_parting_contour": {"de": "Kontur", "en": "Contour"},
    "label_parting_side": {"de": "Seite", "en": "Side"},
    "label_parting_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_parting_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_parting_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_parting_feed": {"de": "Vorschub", "en": "Feed"},
    "label_parting_depth": {"de": "Zustellung", "en": "Depth"},
    "label_parting_mode": {"de": "Strategie", "en": "Strategy"},
    "label_parting_pause": {"de": "Vorschubunterbrechung", "en": "Feed Interrupt"},
    "parting_pause_enabled": {"de": "aktivieren", "en": "Enable"},
    "label_parting_pause_distance": {"de": "Unterbrechungsabstand", "en": "Pause Distance"},
    "label_parting_slice_strategy": {"de": "Bearbeitungsrichtung", "en": "Roughing Direction"},
    "label_parting_slice_step": {"de": "Band-Abstand", "en": "Band Spacing"},
    "label_parting_allow_undercut": {"de": "Hinterschnitt erlauben", "en": "Allow Undercut"},
    "parting_allow_undercut": {"de": "erlauben", "en": "allow"},

    "label_thread_orientation": {"de": "Gewindetyp", "en": "Thread Type"},
    "label_thread_standard": {"de": "Standardgewinde", "en": "Thread Standard"},
    "label_thread_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_thread_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_thread_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_thread_major_diameter": {"de": "Major-Durchmesser (mm)", "en": "Major Diameter (mm)"},
    "label_thread_pitch": {"de": "Steigung (mm)", "en": "Pitch (mm)"},
    "label_thread_length": {"de": "Gewindelänge Z1 (mm)", "en": "Thread length Z1 (mm)"},
    "label_thread_passes": {"de": "Schruppschnitte (Anzahl)", "en": "Rough passes (count)"},
    "label_thread_safe_z": {"de": "Sicherheits-Z (mm)", "en": "Safe Z (mm)"},
    "label_thread_depth": {"de": "Gewindetiefe K (mm)", "en": "Thread depth K (mm)"},
    "label_thread_first_depth": {"de": "Erste Zustellung J (mm)", "en": "First cut J (mm)"},
    "label_thread_peak_offset": {"de": "Spitzenabzug I (mm)", "en": "Crest offset I (mm)"},
    "label_thread_retract_r": {"de": "Rückzug R (mm)", "en": "Retract R (mm)"},
    "label_thread_infeed_q": {"de": "Zustellwinkel Q (°)", "en": "Infeed angle Q (°)"},
    "label_thread_spring_passes": {"de": "Leerschnitte H (Anzahl)", "en": "Spring passes H (count)"},
    "label_thread_e": {"de": "G76-E (Fein/Option)", "en": "G76-E (finish/option)"},
    "label_thread_l": {"de": "G76-L (Option / Mehrstart)", "en": "G76-L (option / multi-start)"},

    "label_groove_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_groove_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_groove_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_20": {"de": "Durchmesser", "en": "Diameter"},
    "label_21": {"de": "Breite", "en": "Width"},
    "label_groove_cutting_width": {"de": "Schneidenbreite", "en": "Cutting Width"},
    "label_22": {"de": "Tiefe", "en": "Depth"},
    "label_23": {"de": "Z-Position", "en": "Z Position"},
    "label_24": {"de": "Vorschub", "en": "Feed"},
    "label_25": {"de": "Sicherheits-Z", "en": "Safety Z"},
    "label_groove_reduced_feed_start_x": {"de": "Abstech-X", "en": "Parting X"},
    "label_groove_reduced_feed": {"de": "Abstech-Vorschub", "en": "Parting Feed"},
    "label_groove_reduced_rpm": {"de": "Abstech-Drehzahl", "en": "Parting Spindle"},
    "label_groove_step_a": {"de": "Zustellung pro Pass", "en": "Depth per pass"},
    "label_groove_overlap": {"de": "Ueberdeckung", "en": "Overlap"},
    "label_groove_retract": {"de": "Rueckzug", "en": "Retract"},
    "label_groove_finish": {"de": "Schlichtaufmass", "en": "Finish allowance"},
    "label_groove_sweep_feed": {"de": "Spanbruch-Vorschub", "en": "Chip break feed"},
    "label_groove_chip_amp": {"de": "Spanbruch-Amplitude", "en": "Chip break amplitude"},
    "label_groove_chip_n": {"de": "Spanbruch-Zyklen", "en": "Chip break cycles"},

    "label_drill_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_drill_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_drill_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_drill_mode": {"de": "Bohren Art", "en": "Drilling Mode"},
    "label_26": {"de": "Hole Diameter", "en": "Hole Diameter"},
    "label_27": {"de": "Tiefe", "en": "Depth"},
    "label_28": {"de": "Feed", "en": "Feed"},
    "label_29": {"de": "Sicherheits-Z", "en": "Safety Z"},

    "label_30": {"de": "Modus", "en": "Mode"},
    "label_31": {"de": "Radialseite", "en": "Radial Side"},
    "label_key_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_32": {"de": "Nutanzahl", "en": "Slot Count"},
    "label_33": {"de": "Startwinkel (°)", "en": "Start Angle (°)"},
    "label_34": {"de": "Startdurchmesser", "en": "Start Diameter"},
    "label_35": {"de": "Start Z", "en": "Start Z"},
    "label_36": {"de": "Nutlänge", "en": "Slot Length"},
    "label_37": {"de": "Nuttiefe", "en": "Slot Depth"},
    "label_key_cutting_width": {"de": "Schneidenbreite", "en": "Cutting Width"},
    "label_38": {"de": "Kopffreiheit", "en": "Top Clearance"},
    "label_39": {"de": "Zustellung pro Pass", "en": "Depth per Pass"},
    "label_40": {"de": "Eintauchvorschub", "en": "Plunge Feed"},
    "label_41": {"de": "C-Achse benutzen", "en": "Use C Axis"},
    "label_42": {"de": "C-Achse Schalter", "en": "C Axis Switch"},
    "label_43": {"de": "C-Achse Schalter P", "en": "C Axis Switch P"},

    "btnAdd": {"de": "Schritt hinzufügen", "en": "Add Step"},
    "btnDelete": {"de": "Schritt löschen", "en": "Delete Step"},
    "btnMoveUp": {"de": "Nach oben", "en": "Move Up"},
    "btnMoveDown": {"de": "Nach unten", "en": "Move Down"},
    "btnNewProgram": {"de": "Neues Programm", "en": "New Program"},
    "btnGenerate": {"de": "Programm erzeugen", "en": "Generate Program"},
}

COMBO_OPTION_TRANSLATIONS = {
    "program_shape": {
        "de": ["Zylinder", "Rohr", "Rechteck", "N-Eck"],
        "en": ["Cylinder", "Tube", "Rectangle", "Polygon"],
    },
    "program_retract_mode": {
        "de": ["einfach", "erweitert", "alle"],
        "en": ["Simple", "Extended", "All"],
    },
    "face_mode": {
        "de": ["Schruppen", "Schlichten", "Schruppen + Schlichten"],
        "en": ["Rough", "Finish", "Rough + Finish"],
    },
    "face_finish_direction": {
        "de": ["Außen → Innen", "Innen → Außen"],
        "en": ["Outside → Inside", "Inside → Outside"],
    },
    "face_edge_type": {
        "de": ["Keine", "Fase", "Radius"],
        "en": ["None", "Chamfer", "Radius"],
    },
    "contour_coord_mode": {"de": ["Absolut", "Inkremental"], "en": ["Absolute", "Incremental"]},
    "contour_edge_type": {
        "de": ["Keine", "Fase", "Radius"],
        "en": ["None", "Chamfer", "Radius"],
    },
    "parting_side": {"de": ["Außenseite", "Innenseite"], "en": ["Outside", "Inside"]},
    "parting_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "parting_mode": {"de": ["Schruppen", "Schlichten"], "en": ["Rough", "Finish"]},
    "parting_slice_strategy": {"de": ["Parallel X", "Parallel Z"], "en": ["Parallel X", "Parallel Z"]},
    "thread_orientation": {"de": ["Aussengewinde", "Innengewinde"], "en": ["External", "Internal"]},
    "thread_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "groove_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "drill_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "drill_mode": {"de": ["Normal", "Spanbruch", "Spanbruch + Rückzug"], "en": ["Normal", "Chip Break", "Chip Break + Retract"]},
    "key_mode": {"de": ["Axial (Z)", "Face (X)"], "en": ["Axial (Z)", "Face (X)"]},
    "key_radial_side": {
        "de": ["Außen (Welle)", "Innen (Bohrung)"],
        "en": ["Outside (shaft)", "Inside (bore)"],
    },
    "key_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "program_language": {"de": ["Deutsch", "English"], "en": ["German", "English"]},
}

BUTTON_TRANSLATIONS = {
    "btnAdd": {"de": "Schritt hinzufügen", "en": "Add Step"},
    "btnDelete": {"de": "Schritt löschen", "en": "Delete Step"},
    "btnMoveUp": {"de": "Nach oben", "en": "Move Up"},
    "btnMoveDown": {"de": "Nach unten", "en": "Move Down"},
    "btnNewProgram": {"de": "Neues Programm", "en": "New Program"},
    "btnGenerate": {"de": "Programm erzeugen", "en": "Generate Program"},
    "btn_thread_preset": {"de": "Preset übernehmen", "en": "Apply preset"},
    "btn_save_step": {"de": "Step speichern", "en": "Save Step"},
    "btn_load_step": {"de": "Step laden", "en": "Load Step"},
}

STEP_FILE_FILTER = "Lathe step files (*.step.json);;JSON (*.json)"

def normalize_arc_side(value: object | None) -> str:
    s = str(value or "auto").strip().lower()
    if s in {"inner", "innen", "in"}:
        return "inner"
    if s in {"outer", "außen", "aussen", "au", "auss", "outside", "out"}:
        return "outer"
    return "auto"

# Tooltips für Gewinde-Widgets (de / en)
THREAD_TOOLTIP_TRANSLATIONS = {
    "thread_length": {
        "de": "Z-Ende relativ/absolut – je nach Modell",
        "en": "Z end relative/absolute – depends on model",
    },
    "thread_safe_z": {"de": "Startpunkt vor dem G76/G32", "en": "Start point before G76/G32"},
    "thread_passes": {"de": "Schruppschnitte (Anzahl)", "en": "Rough passes (count)"},
    "thread_depth": {"de": "Bei Bedarf nachregeln (Material gibt nach)", "en": "Adjust if needed (material gives way)"},
    "thread_first_depth": {"de": "Erste Zustellung; Rest verteilt sich", "en": "First cut; remainder distributed"},
    "thread_peak_offset": {"de": "Für Spitzen/Flankenform; oft negativ", "en": "For crest/face offset; often negative"},
    "thread_retract_r": {"de": "Rückzug am Ende eines Schnitts", "en": "Retract at end of cut"},
    "thread_infeed_q": {"de": "Zustellwinkel Q (°)", "en": "Infeed angle Q (°)"},
    "thread_spring_passes": {"de": "Leerschnitte (Anzahl)", "en": "Spring passes (count)"},
    "thread_e": {"de": "G76-E (Fein/Option)", "en": "G76-E (finish/option)"},
    "thread_l": {"de": "G76-L (Option / Mehrstart)", "en": "G76-L (option / multi-start)"},
}

PARTING_TOOLTIP_TRANSLATIONS = {
    "parting_slice_strategy": {
        "de": "Wählt die axis-parallele Bearbeitungsrichtung für Schruppschnitte (Parallel X oder Parallel Z).",
        "en": "Choose the roughing direction (axis-aligned: Parallel X or Parallel Z).",
    },
    "parting_slice_step": {
        "de": "Abstand zwischen X-Bändern (mm)",
        "en": "Step between X-bands (mm)",
    },
    "parting_allow_undercut": {
        "de": "Erlaubt Hinterschnitte (Schnitt über Kontur hinaus)",
        "en": "Allow undercuts (cut beyond contour)",
    },
}

GROOVE_TOOLTIP_TRANSLATIONS = {
    "groove_depth": {
        "de": "Tiefe radial; X ist Durchmesser (G7). X-Aenderung = 2 * Tiefe.",
        "en": "Radial depth; X is diameter (G7). X change = 2 * depth.",
    },
    "groove_step_a": {
        "de": "Zustellung pro Pass radial; X ist Durchmesser (G7).",
        "en": "Depth per pass is radial; X is diameter (G7).",
    },
    "groove_retract": {
        "de": "Rueckzug radial; X ist Durchmesser (G7).",
        "en": "Retract is radial; X is diameter (G7).",
    },
    "groove_finish": {
        "de": "Schlichtaufmass radial; X ist Durchmesser (G7).",
        "en": "Finish allowance is radial; X is diameter (G7).",
    },
}


class ProgramModel:
    def __init__(self):
        self.operations: List[Operation] = []
        self.spindle_speed_max: float = 0.0
        # Default program settings: make line-number emission opt-out by default
        self.program_settings: Dict[str, object] = {"emit_line_numbers": False}

    def add_operation(self, op: Operation):
        self.operations.append(op)

    def remove_operation(self, index: int):
        if 0 <= index < len(self.operations):
            del self.operations[index]

    def move_up(self, index: int):
        if 1 <= index < len(self.operations):
            self.operations[index - 1], self.operations[index] = \
                self.operations[index], self.operations[index - 1]

    def move_down(self, index: int):
        if 0 <= index < len(self.operations) - 1:
            self.operations[index + 1], self.operations[index] = \
                self.operations[index], self.operations[index + 1]

    def update_geometry(self, op: Operation):
        builder = {
            OpType.FACE: build_face_path,
            OpType.CONTOUR: build_contour_path,
            OpType.THREAD: build_thread_path,
            OpType.GROOVE: build_groove_path,
            OpType.DRILL: build_drill_path,
            OpType.KEYWAY: build_keyway_path,
            OpType.ABSPANEN: build_abspanen_path,
        }.get(op.op_type)
        if not builder:
            op.path = []
            return

        # builder signatures are usually builder(params). Some builders also need program settings.
        try:
            argc = builder.__code__.co_argcount
        except Exception:
            argc = 1

        if argc >= 2:
            op.path = builder(op.params, self.program_settings)
        else:
            # If operation has a custom path, ensure it's in params for the builder
            if hasattr(op, 'path') and op.path and 'path' not in op.params:
                # Only convert if path is list of (x, z) tuples, not primitives
                if op.path and isinstance(op.path[0], (list, tuple)) and len(op.path[0]) == 2:
                    op.params['path'] = [{'x': x, 'z': z} for x, z in op.path]
            op.path = builder(op.params)


    def generate_gcode(self) -> List[str]:
        try:
            from slicer import generate_program_gcode
        except Exception:
            generate_program_gcode = None

        if generate_program_gcode:
            return generate_program_gcode(self.operations, self.program_settings or {})

        # Fallback if slicer not available
        return ["%", "(G-Code generation failed - slicer module not found)", "M30", "%"]


# ----------------------------------------------------------------------
# Preview widget
# ----------------------------------------------------------------------
class LathePreviewWidget(QtWidgets.QWidget):
    sliceChanged = QtCore.Signal(float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_is_diameter = True  # X values are treated as radius for drawing but labeled as diameter
        self.paths: List[List[Tuple[float, float]]] = []
        self.primitives: List[List[dict]] = []
        self.active_index: int | None = None
        # Legend visibility & collision indication
        self.show_legend = True
        self._legend_collapsed = False
        self._legend_click_rect = None

        self._collision_active = False
        self._blink_state = False
        self._blink_timer = QtCore.QTimer(self)
        self._blink_timer.setInterval(350)
        # Slice view support (side view + draggable Z-slice)
        self.view_mode = "side"  # "side" or "slice"
        self.slice_enabled = False
        self.slice_z = 0.0
        self._slice_drag = False
        self._view_rect = None
        self._view_min_z = None
        self._view_max_z = None
        self._view_scale = None
        self._blink_timer.timeout.connect(self._on_blink_timer)
        self.setMinimumHeight(200)
        self._base_span = 10.0  # Default 10x10 mm viewport


    def _on_blink_timer(self):
        # Blink when collision is active
        if not self._collision_active:
            if self._blink_state:
                self._blink_state = False
                self.update()
            return
        self._blink_state = not self._blink_state
        self.update()

    def set_collision(self, active: bool):
        self._collision_active = bool(active)
        if self._collision_active:
            if not self._blink_timer.isActive():
                self._blink_timer.start()
        else:
            if self._blink_timer.isActive():
                self._blink_timer.stop()
            self._blink_state = False
            self.update()

    def toggle_legend(self):
        # keep a small header visible, toggle between collapsed/expanded
        self._legend_collapsed = not getattr(self, "_legend_collapsed", False)
        self.update()

    def set_view_mode(self, mode: str):
        self.view_mode = mode
        self.update()

    def set_slice_enabled(self, enabled: bool):
        self.slice_enabled = bool(enabled)
        self._slice_drag = False
        self.update()

    def set_slice_z(self, z_val: float, emit: bool = False):
        try:
            z_val = float(z_val)
        except Exception:
            return
        self.slice_z = z_val
        if emit:
            try:
                self.sliceChanged.emit(self.slice_z)
            except Exception:
                pass
        self.update()

    def _pixel_to_z(self, px: float):
        rect = getattr(self, "_view_rect", None)
        min_z = getattr(self, "_view_min_z", None)
        scale = getattr(self, "_view_scale", None)
        if rect is None or min_z is None or scale in (None, 0):
            return None
        z = float(min_z) + (px - rect.left()) / float(scale)
        max_z = getattr(self, "_view_max_z", None)
        if max_z is not None:
            z = max(float(min_z), min(float(max_z), z))
        return z

    def _set_slice_from_pos(self, pos: QtCore.QPoint):
        z = self._pixel_to_z(pos.x())
        if z is None:
            return
        self.set_slice_z(z, emit=True)

    def _interp_x_at_z(self, path, z: float):
        if not path or len(path) < 2:
            return None
        hits = []
        for (x1, z1), (x2, z2) in zip(path[:-1], path[1:]):
            if abs(z2 - z1) < 1e-9:
                if abs(z - z1) < 1e-6:
                    hits.append(x1); hits.append(x2)
                continue
            if (z1 <= z <= z2) or (z2 <= z <= z1):
                t = (z - z1) / (z2 - z1)
                hits.append(x1 + t * (x2 - x1))
        if not hits:
            return None
        return min(hits)

    def _paint_slice_view(self, painter: QtGui.QPainter):
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        diam = None
        if self.paths:
            idx = self.active_index if self.active_index is not None else 0
            idx = max(0, min(idx, len(self.paths) - 1))
            path = self.paths[idx]
            if path and isinstance(path[0], tuple):
                diam = self._interp_x_at_z(path, self.slice_z)

        if diam is None:
            diam = 10.0

        r = self.rect().adjusted(20, 20, -20, -40)
        cx, cy = r.center().x(), r.center().y()
        radius = abs(float(diam)) / 2.0
        scale = min(r.width(), r.height()) / max(radius * 2.2, 1e-3)
        pix_rad = radius * scale

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 2))
        painter.drawEllipse(QtCore.QPointF(cx, cy), pix_rad, pix_rad)

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        painter.drawText(10, self.height() - 10, f"Schnitt bei Z = {self.slice_z:.3f} mm")

    def mousePressEvent(self, event):  # type: ignore[override]
        # Click on legend to toggle
        rect = getattr(self, "_legend_click_rect", None)
        if rect and rect.contains(event.pos()):
            self.toggle_legend()
            event.accept()
            return

        # Drag slice line in side view
        if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
            vrect = getattr(self, "_view_rect", None)
            if vrect is not None and vrect.contains(event.pos()) and event.button() == QtCore.Qt.LeftButton:
                self._slice_drag = True
                self._set_slice_from_pos(event.pos())
                event.accept()
                return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):  # type: ignore[override]
        if getattr(self, "_slice_drag", False) and getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
            self._set_slice_from_pos(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # type: ignore[override]
        if getattr(self, "_slice_drag", False):
            self._slice_drag = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _sample_arc(self, p1, p2, c, ccw, steps=48):
        x1, z1 = p1
        x2, z2 = p2
        xc, zc = c
        r1 = math.hypot(x1 - xc, z1 - zc)
        r2 = math.hypot(x2 - xc, z2 - zc)
        if r1 <= 1e-9 or abs(r1 - r2) > 1e-3:
            return [p1, p2]
        a1 = math.atan2(z1 - zc, x1 - xc)
        a2 = math.atan2(z2 - zc, x2 - xc)
        if ccw:
            if a2 <= a1:
                a2 += 2 * math.pi
        else:
            if a2 >= a1:
                a2 -= 2 * math.pi
        pts = []
        for k in range(steps + 1):
            t = k / steps
            a = a1 + (a2 - a1) * t
            pts.append((xc + r1 * math.cos(a), zc + r1 * math.sin(a)))
        return pts

    def primitives_to_points(self, prims):
        pts = []
        last = None
        for pr in prims or []:
            if isinstance(pr, (list, tuple)) and len(pr) >= 2:
                try:
                    p = (float(pr[0]), float(pr[1]))
                except Exception:
                    continue
                pts.append(p)
                last = p
                continue
            if not isinstance(pr, dict):
                continue
            typ = (pr.get("type") or "").lower()
            if typ == "line":
                p1 = tuple(pr.get("p1", (0.0, 0.0)))
                p2 = tuple(pr.get("p2", (0.0, 0.0)))
                if last is None:
                    pts.append(p1)
                elif math.hypot(p1[0] - last[0], p1[1] - last[1]) > 1e-6:
                    pts.append(p1)
                pts.append(p2)
                last = p2
            elif typ == "arc":
                p1 = tuple(pr.get("p1", (0.0, 0.0)))
                p2 = tuple(pr.get("p2", (0.0, 0.0)))
                c = tuple(pr.get("c", (0.0, 0.0)))
                ccw = bool(pr.get("ccw", True))
                arc_pts = self._sample_arc(p1, p2, c, ccw)
                if last is None:
                    pts.extend(arc_pts)
                else:
                    if math.hypot(arc_pts[0][0] - last[0], arc_pts[0][1] - last[1]) > 1e-6:
                        pts.append(arc_pts[0])
                    pts.extend(arc_pts[1:])
                last = arc_pts[-1]
        return pts

    def set_paths(self, paths, active_index: int | None = None):
        # paths can be:
        #   - list of list-of-(x,z) points (legacy)
        #   - list of primitives [{type:line/arc,...}, ...] for a single path
        #   - list of list-of-primitives for multiple paths
        self.active_index = active_index

        # IMPORTANT:
        # We keep "primitive" paths (list of dicts) as-is so the paintEvent
        # can style them by role (e.g. stock / retract) and still draw them.
        norm_paths = []
        for entry in paths or []:
            if isinstance(entry, dict) and "type" in entry:
                # single primitive dict
                norm_paths.append([entry])
                continue

            if isinstance(entry, (list, tuple)):
                # list of primitives (dict) or list of points
                if entry and isinstance(entry[0], dict) and "type" in entry[0]:
                    norm_paths.append(list(entry))
                    continue

                pts = []
                for pt in entry:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        try:
                            pts.append((float(pt[0]), float(pt[1])))
                        except Exception:
                            continue
                if pts:
                    norm_paths.append(pts)

        self.paths = norm_paths
        self.update()

    def set_primitives(self, primitives):
        """
        Kompatibilität: Einige Teile des Codes arbeiten mit 'primitives'
        (Linien/Arcs/Polylines). Dieses Widget zeichnet aber über 'paths'.
        Daher: primitives -> points -> set_paths().
        """
        self.primitives = primitives or []
        try:
            paths = self.primitives_to_points(self.primitives)
        except Exception:
            paths = []
        self.set_paths(paths)

    def paintEvent(self, event):  # type: ignore[override]
        painter = QtGui.QPainter(self)
        if getattr(self, "view_mode", "side") == "slice":
            try:
                self._paint_slice_view(painter)
            finally:
                painter.end()
            return
        self._legend_click_rect = None
        try:
            painter.fillRect(self.rect(), QtCore.Qt.black)
            # Collect bounds across all paths (supports point lists and primitive lists)
            inf = float('inf')
            min_x, max_x = inf, -inf
            min_z, max_z = inf, -inf

            def _upd(xv: float, zv: float):
                nonlocal min_x, max_x, min_z, max_z
                x_draw = xv
                min_x = min(min_x, x_draw)
                max_x = max(max_x, x_draw)
                min_z = min(min_z, zv)
                max_z = max(max_z, zv)

            any_data = False
            for path in self.paths:
                if not path:
                    continue
                any_data = True
                first = path[0]
                if isinstance(first, dict):
                    # primitives (line/arc with p1/p2/c) -> sample to points for bounds
                    try:
                        pts = self.primitives_to_points(path)
                    except Exception:
                        pts = []
                    for (xv, zv) in pts:
                        _upd(float(xv), float(zv))
                else:
                    for (xv, zv) in path:
                        _upd(float(xv), float(zv))

            if not any_data or min_x == inf or min_z == inf:
                min_x = max_x = 0.0
                min_z = max_z = 0.0
            # Ursprung und Mindestgröße immer berücksichtigen
            half_span = self._base_span / 2.0
            min_x = min(min_x, -half_span, 0.0)
            max_x = max(max_x, half_span, 0.0)
            min_z = min(min_z, -half_span, 0.0)
            max_z = max(max_z, half_span, 0.0)

            dx = max_x - min_x
            dz = max_z - min_z

            def ensure_span(min_val: float, max_val: float, base_span: float) -> Tuple[float, float]:
                span = max_val - min_val
                if span < base_span:
                    pad = (base_span - span) / 2.0
                    return min_val - pad, max_val + pad
                return min_val, max_val

            min_x, max_x = ensure_span(min_x, max_x, self._base_span)
            min_z, max_z = ensure_span(min_z, max_z, self._base_span)

            # kleiner Rand um die Geometrie
            dx = max(max_x - min_x, 1e-3)
            dz = max(max_z - min_z, 1e-3)
            pad = 0.05
            min_x -= dx * pad
            max_x += dx * pad
            min_z -= dz * pad
            max_z += dz * pad

            margin = 30
            rect = self.rect().adjusted(margin, margin, -margin, -margin)
            scale_z = rect.width() / max(max_z - min_z, 1e-6)
            scale_x = rect.height() / max(max_x - min_x, 1e-6)
            scale = min(scale_x, scale_z)


            # store mapping for interactive slice
            self._view_rect = rect
            self._view_min_z = min_z
            self._view_max_z = max_z
            self._view_scale = scale

            def to_screen(x_val: float, z_val: float) -> QtCore.QPointF:
                # Z horizontal, X vertikal
                x_draw = x_val
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_draw - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            # optional slice indicator (selected Z)
            if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
                try:
                    zline = float(getattr(self, "slice_z", 0.0))
                    p1 = to_screen(min_x, zline)
                    p2 = to_screen(max_x, zline)
                    pen = QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.DashLine)
                    painter.setPen(pen)
                    painter.drawLine(p1, p2)
                except Exception:
                    pass

            # Achsen und Skala (außen: links/unten)
            painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
            axis_x_val = 0.0 if min_x <= 0.0 <= max_x else min_x
            axis_z_val = 0.0 if min_z <= 0.0 <= max_z else min_z
            x_axis = to_screen(axis_x_val, min_z)
            x_axis_end = to_screen(axis_x_val, max_z)
            z_axis = to_screen(min_x, axis_z_val)
            z_axis_end = to_screen(max_x, axis_z_val)
            painter.drawLine(z_axis, z_axis_end)  # Z-Achse horizontal
            painter.drawLine(x_axis, x_axis_end)  # X-Achse vertikal

            def nice_step(span: float) -> float:
                if span <= 0:
                    return 1.0
                raw = span / 5.0
                power = 10 ** int(math.floor(math.log10(raw)))
                for m in (1, 2, 5, 10):
                    step = m * power
                    if span / step <= 8:
                        return step
                return raw

            tick_pen = QtGui.QPen(QtGui.QColor(100, 100, 100), 1)
            font_pen = QtGui.QPen(QtGui.QColor(160, 160, 160), 1)
            painter.setFont(QtGui.QFont("Sans", 8))

            # Z-Ticks (horizontal unten/oben)
            step_z = nice_step(max_z - min_z)
            val = (min_z // step_z) * step_z
            while val <= max_z:
                pt = to_screen(axis_x_val, val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 2))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 6, pt.y() + 14), f"{val:.0f}")
                val += step_z

            # X-Ticks (vertikal links/rechts)
            step_x = nice_step(max_x - min_x)
            val = (min_x // step_x) * step_x
            while val <= max_x:
                pt = to_screen(val, axis_z_val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x() - 2, pt.y(), pt.x() + 4, pt.y()))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 28, pt.y() + 4), f"{val:.0f}")
                val += step_x

            # Achsbeschriftungen
            painter.setPen(font_pen)
            painter.drawText(QtCore.QPointF(rect.right() - 20, z_axis.y() - 6), "Z")
            painter.drawText(QtCore.QPointF(x_axis.x() + 6, rect.top() + 12), "X")
            for idx, path in enumerate(self.paths):
                if not path:
                    continue

                # role based styling (e.g. raw stock reference)
                role = None
                if isinstance(path, list) and path:
                    # path can be a list of primitive dicts; pick first non-empty role
                    for d in path:
                        if isinstance(d, dict):
                            r = d.get("role")
                            if r:
                                role = r
                                break

                if role == "stock":
                    color = QtGui.QColor("gray")
                    width = 1
                    style = QtCore.Qt.DashLine
                elif role == "retract":
                    # retract planes: visually distinct and clearly *not* a contour
                    color = QtGui.QColor(0, 180, 180)
                    width = 1
                    style = QtCore.Qt.DashLine
                elif role == "worklimit":
                    # workpiece stick-out / chuck collision limit (Bearbeitungsmaß)
                    color = QtGui.QColor(220, 0, 0)
                    width = 2
                    style = QtCore.Qt.DashLine
                else:
                    color = QtGui.QColor("lime") if idx != self.active_index else QtGui.QColor("yellow")
                    width = 2
                    style = QtCore.Qt.SolidLine

                pen = QtGui.QPen(color, width)
                pen.setStyle(style)
                painter.setPen(pen)

                # Primitive mode (dict primitives from build_*_outline helpers)
                if isinstance(path[0], dict):
                    # NOTE: do NOT connect independent primitives with a single polyline.
                    # For retract planes this would create confusing diagonal "links" between separate helper lines.
                    if role in ("retract", "stock", "worklimit"):
                        for prim in path:
                            if not isinstance(prim, dict):
                                continue
                            ptype = prim.get("type")
                            if ptype == "line":
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                if not p1 or not p2:
                                    continue
                                s1 = to_screen(float(p1[0]), float(p1[1]))
                                s2 = to_screen(float(p2[0]), float(p2[1]))
                                painter.drawLine(QtCore.QLineF(s1, s2))
                            elif ptype == "arc":
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                c = prim.get("c")
                                if not p1 or not p2 or not c:
                                    continue
                                ccw = bool(prim.get("ccw", True))
                                try:
                                    arc_pts = self._sample_arc((float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1])), (float(c[0]), float(c[1])), ccw)
                                except Exception:
                                    arc_pts = []
                                if len(arc_pts) >= 2:
                                    points = [to_screen(x, z) for x, z in arc_pts]
                                    painter.drawPolyline(QtGui.QPolygonF(points))
                        continue
                    else:
                        try:
                            pts = self.primitives_to_points(path)
                        except Exception:
                            pts = []
                        if len(pts) >= 2:
                            points = [to_screen(x, z) for x, z in pts]
                            painter.drawPolyline(QtGui.QPolygonF(points))
                        elif len(pts) == 1:
                            pt = to_screen(pts[0][0], pts[0][1])
                            painter.drawLine(QtCore.QLineF(pt.x() - 4, pt.y(), pt.x() + 4, pt.y()))
                            painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 4))
                        continue
                points = [to_screen(x, z) for x, z in path]
                painter.drawPolyline(QtGui.QPolygonF(points))

            legend_enabled = getattr(self, "show_legend", True)
            collapsed = getattr(self, "_legend_collapsed", False)

            if legend_enabled:
                # --- Legend: "Legende" header is always visible, click toggles details ---
                try:
                    margin = 6
                    header_h = 18
                    row_h = 16
                    line_len = 26
                    box_w = 155

                    legend_items = [
                        ("Kontur", QtGui.QPen(QtGui.QColor(0, 255, 0), 2, QtCore.Qt.SolidLine)),
                        ("Aktiv", QtGui.QPen(QtGui.QColor(255, 255, 0), 2, QtCore.Qt.SolidLine)),
                        ("Rohteil", QtGui.QPen(QtGui.QColor(180, 180, 180), 1, QtCore.Qt.SolidLine)),
                        ("Rückzug", QtGui.QPen(QtGui.QColor(0, 255, 255), 1, QtCore.Qt.DashLine)),
                        ("Bearbeitungslinie", QtGui.QPen(QtGui.QColor(255, 0, 0), 1, QtCore.Qt.DashLine)),
                    ]

                    x0 = margin
                    y0 = margin - 2

                    # Box height: always header, details only if not collapsed
                    if collapsed:
                        box_h = margin * 2 + header_h
                    else:
                        box_h = margin * 2 + header_h + row_h * len(legend_items)

                    bg = QtGui.QColor(0, 0, 0, 160)
                    painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
                    painter.setBrush(QtGui.QBrush(bg))
                    painter.drawRoundedRect(QtCore.QRectF(x0, y0, box_w, box_h), 6, 6)

                    # Click target = header area (always present)
                    self._legend_click_rect = QtCore.QRectF(x0, y0, box_w, header_h + margin)

                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                    painter.setFont(QtGui.QFont("Sans", 8))
                    painter.drawText(
                        QtCore.QRectF(x0 + margin, y0 + 2, box_w - 2 * margin, header_h),
                        QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                        "Legende"
                    )

                    if not collapsed:
                        for i, (label, pen) in enumerate(legend_items):
                            y = y0 + margin + header_h + i * row_h + 10
                            painter.setPen(pen)
                            painter.drawLine(
                                QtCore.QPointF(x0 + margin, y),
                                QtCore.QPointF(x0 + margin + line_len, y)
                            )
                            painter.setPen(QtGui.QPen(QtGui.QColor(230, 230, 230), 1))
                            painter.drawText(QtCore.QPointF(x0 + margin + line_len + 6, y + 4), label)

                except Exception:
                    self._legend_click_rect = None

        except Exception:
            self._legend_click_rect = None
        finally:
            painter.end()


# ----------------------------------------------------------------------
# Simple path builders
# ----------------------------------------------------------------------
def build_face_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    """Build a 2D preview path for facing (Planen).

    IMPORTANT: This returns the *cutting contour* only (no closing back to Z0),
    because otherwise the preview draws an extra diagonal/return line.

    Conventions / expectations in this project:
      - X is a diameter coordinate (as used everywhere else in LatheEasyStep).
      - Facing is shown from the center (x_inner) outward to the OD (x_outer).
      - The face plane is z_end (often 0.0). z_start is a safe/approach Z.
      - Chamfer/radius is applied at the outer corner (x_outer, z_end) going into -Z.
    """
    # Check if a custom path is provided
    if "path" in params and params["path"]:
        print(f"DEBUG: Using custom path from params: {params['path']}")
        path_data = params["path"]
        if isinstance(path_data, list) and path_data:
            # Assume path is list of dicts with 'x' and 'z', or tuples
            path = []
            for point in path_data:
                if isinstance(point, dict):
                    x = point.get("x", 0.0)
                    z = point.get("z", 0.0)
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    x, z = point[0], point[1]
                else:
                    continue
                path.append((float(x), float(z)))
            # Add start line for facing preview
            sx = params.get("start_x", None)
            sz = params.get("start_z", None)
            ez = params.get("end_z", sz)
            ex = params.get("end_x", None)
            if sx is not None and sz is not None and ez is not None:
                path = [(float(sx), float(sz)), (float(sx), float(ez))] + path
            if ex is not None and ez is not None:
                path.append((float(ex), float(ez)))
            return path

    # --- X extents (diameter) ---
    x_outer = params.get("outer_diameter", None)
    x_inner = params.get("inner_diameter", None)

    # Compatibility with op-params used by the gcode generators
    sx = params.get("start_x", None)
    ex = params.get("end_x", None)

    # Some older helpers use start_diameter/end_diameter
    sd = params.get("start_diameter", None)
    ed = params.get("end_diameter", None)

    candidates = [v for v in (sx, ex, sd, ed) if isinstance(v, (int, float))]
    if x_outer is None:
        x_outer = max(candidates) if candidates else 0.0
    if x_inner is None:
        x_inner = min(candidates) if candidates else 0.0

    x_outer = float(x_outer or 0.0)
    x_inner = float(x_inner or 0.0)

    # --- Z extents ---
    z_start = float(params.get("start_z", params.get("z_start", 0.0)) or 0.0)
    z_end = float(params.get("end_z", z_start))

    edge_type = int(params.get("edge_type", 0))  # 0=none, 1=chamfer, 2=radius
    edge_size = float(params.get("edge_size", 0.0) or 0.0)

    # Normalize: ensure x_inner <= x_outer
    if x_inner > x_outer:
        x_inner, x_outer = x_outer, x_inner

    path: List[Tuple[float, float]] = []

    # Start at center/inner diameter at safe Z, then to face plane
    path.append((x_inner, z_start))
    path.append((x_inner, z_end))

    # Apply edge at outer corner (x_outer, z_end)
    if edge_type == 1 and edge_size > 0.0:
        # 45° chamfer: go to the chamfer start on the face plane, then down in Z.
        # Expected polyline: (x_inner,z_start)->(x_inner,z_end)->(x_outer-edge,z_end)->(x_outer,z_end-edge)
        path.append((max(x_inner, x_outer - edge_size), z_end))
        path.append((x_outer, z_end - edge_size))
        # NOTE: do NOT append (x_outer, z_end) or close back -> that caused the unwanted return line.

    elif edge_type == 2 and edge_size > 0.0:
        # Outer radius (quarter-circle) from (x_outer-edge, z_end) to (x_outer, z_end-edge)
        x0 = max(x_inner, x_outer - edge_size)
        z0 = z_end
        path.append((x0, z0))
        cx = x_outer - edge_size
        cz = z_end - edge_size
        segments = 10
        import math
        # a: 90°..0° (start at face plane, end at OD line)
        for i in range(1, segments + 1):
            a = (math.pi / 2.0) * (1.0 - (i / segments))
            x = cx + edge_size * math.cos(a)
            z = cz + edge_size * math.sin(a)
            path.append((x, z))
        # ends close to (x_outer, z_end-edge_size)

    else:
        # No edge: just face to OD at z_end
        path.append((x_outer, z_end))

    return path

def build_stock_outline(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a thin reference outline of the raw stock in XZ (diameter X).

    Output format matches the preview widget's 'primitives' list of dicts.
    Uses role='stock' so the widget can draw it in a neutral thin dashed style.
    """
    shape = str(program.get("shape", "")).lower().strip()
    # common fields from program header
    def _sf(v: Any, default: float = 0.0) -> float:
        try:
            if v is None:
                return float(default)
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else float(default)
            return float(v)
        except Exception:
            return float(default)

    xa = _sf(program.get("xa", 0.0), 0.0)  # outer diameter
    xi = _sf(program.get("xi", 0.0), 0.0)  # inner diameter (for tube)
    za = _sf(program.get("za", 0.0), 0.0)  # front face Z
    zi = float(program.get("zi", 0.0) or 0.0)  # back face Z (often negative length)

    if xa <= 0.0:
        return []

    # Normalize Z: ensure za is the front (greater) and zi is the back (smaller) for drawing
    z_front = max(za, zi)
    z_back = min(za, zi)

    primitives: List[Dict[str, Any]] = []

    def add_line(z1: float, x1: float, z2: float, x2: float) -> None:
        primitives.append({"role": "stock", "type": "line", "p1": (x1, z1), "p2": (x2, z2)})

    # Outer contour (L-shape: face + OD + back face + centerline return)
    add_line(z_front, 0.0, z_front, xa)     # front face
    add_line(z_front, xa, z_back, xa)       # OD along Z
    add_line(z_back, xa, z_back, 0.0)       # back face
    # centerline is optional; keep it minimal (no line back to front)

    if shape in ("rohr", "tube") and xi > 0.0 and xi < xa:
        # Inner bore contour as reference (also L-shape)
        add_line(z_front, xi, z_back, xi)
        # (front/back inner face lines are usually not needed for reference)

    return primitives


def build_retract_primitives(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return retract plane lines (XRA/XRI/ZRA/ZRI) as preview primitives.

    Supports absolute/incremental flags:
      - xra_absolute / xri_absolute / zra_absolute / zri_absolute

    Interpretation (matching program header semantics):
      - XRA (outer retract): if incremental -> XA + XRA, else -> XRA
      - XRI (inner retract): if incremental -> XI - XRI, else -> XRI
      - ZRA (front retract): if incremental -> ZA + ZRA, else -> ZRA
      - ZRI (back retract):  if incremental -> ZI - ZRI, else -> ZRI

    Output format:
      {"role":"retract","type":"line","p1":(x,z),"p2":(x,z)}
    """
    def _sf(v: Any, default: float = 0.0) -> float:
        try:
            if v is None:
                return float(default)
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else float(default)
            return float(v)
        except Exception:
            return float(default)

    xa = _sf(program.get("xa", 0.0), 0.0)
    xi = _sf(program.get("xi", 0.0), 0.0)
    za = _sf(program.get("za", 0.0), 0.0)
    zi = _sf(program.get("zi", 0.0), 0.0)

    # drawing span for the helper lines
    z_front = max(za, zi)
    z_back = min(za, zi)

    prim: List[Dict[str, Any]] = []

    def add_line(p1: tuple[float, float], p2: tuple[float, float]) -> None:
        prim.append({"role": "retract", "type": "line", "p1": p1, "p2": p2})

    def vline(x: float) -> None:
        add_line((x, z_front), (x, z_back))

    def hline(z: float) -> None:
        # use XA as max extents (fallback: 0..10mm)
        x_max = xa if xa > 0.0 else 10.0
        add_line((0.0, z), (x_max, z))

    def _is_true(key: str) -> bool:
        try:
            return bool(program.get(key, False))
        except Exception:
            return False

    # XRA (outer)
    xra = program.get("xra", None)
    if xra is not None:
        try:
            xra_f = _sf(xra)
            if abs(xra_f) > 1e-12:
                x = xra_f if _is_true("xra_absolute") else (xa + xra_f)
                vline(x)
        except Exception:
            pass

    # XRI (inner) - only meaningful if XI > 0
    xri = program.get("xri", None)
    if xri is not None and xi > 0.0:
        try:
            xri_f = _sf(xri)
            if abs(xri_f) > 1e-12:
                x = xri_f if _is_true("xri_absolute") else (xi - xri_f)
                vline(x)
        except Exception:
            pass

    # ZRA (front)
    zra = program.get("zra", None)
    if zra is not None:
        try:
            zra_f = _sf(zra)
            if abs(zra_f) > 1e-12:
                z = zra_f if _is_true("zra_absolute") else (za + zra_f)
                hline(z)
        except Exception:
            pass

    # ZRI (back)
    zri = program.get("zri", None)
    if zri is not None:
        try:
            zri_f = _sf(zri)
            if abs(zri_f) > 1e-12:
                # If absolute flag is set, interpret value as absolute Z; otherwise incremental from ZI.
                z = zri_f if _is_true("zri_absolute") else (zi - zri_f)
                hline(z)
        except Exception:
            pass

    return prim



def build_worklimit_primitives(program: Dict[str, Any], stock_prims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bearbeitungsmaß / Werkstück-Überstand (Chuck-Kollisionsgrenze) als Linie.

    program['zb'] = Z-Position der Grenze (wo das Material aus dem Futter herausragt).

    Die Linienlänge wird **aus der Rohteilkontur** abgeleitet, damit sie nicht mit
    Fantasie-Werten (±1000) gezeichnet wird.
    """
    try:
        z = float(program.get("zb", 0.0) or 0.0)
    except Exception:
        z = 0.0

    if abs(z) < 1e-9:
        return []

    # X-Ausdehnung aus Rohteil-Kontur (points sind (x, z))
    x_vals: List[float] = []
    for prim in stock_prims or []:
        if isinstance(prim, dict) and prim.get("type") == "polyline":
            pts = prim.get("points") or []
            for pt in pts:
                if isinstance(pt, (tuple, list)) and len(pt) >= 2:
                    try:
                        x_vals.append(float(pt[0]))
                    except Exception:
                        pass

    if x_vals:
        min_x = min(x_vals)
        max_x = max(x_vals)
        # kleine Sicherheitsmargen (typisch: min bei 0 -> Linie bis ca. -5mm)
        margin_neg = 5.0
        margin_pos = max(2.0, 0.02 * max(abs(max_x), 1.0))
        x_min = min(min_x - margin_neg, -margin_neg)
        x_max = max_x + margin_pos
    else:
        # Fallback, falls keine Rohteil-Kontur verfügbar ist
        x_min = -5.0
        x_max = 50.0

    return [{
        "type": "line",
        "p1": (x_min, z),
        "p2": (x_max, z),
        "role": "worklimit",
    }]


def build_turn_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    length = params.get("length", 0.0)
    safe_z = params.get("safe_z", 2.0)
    return [
        (x_start, safe_z),
        (x_start, 0.0),
        (x_end, -abs(length)),
    ]


def build_bore_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    x_start = params.get("start_diameter", 0.0)
    x_end = params.get("end_diameter", x_start)
    depth = -abs(params.get("depth", 0.0))
    safe_z = params.get("safe_z", 2.0)
    return [
        (x_start, safe_z),
        (x_start, 0.0),
        (x_end, depth),
    ]


def build_thread_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    major = params.get("major_diameter", 0.0)
    pitch = params.get("pitch", 1.5)
    length = params.get("length", 0.0)
    passes = max(1, int(params.get("passes", 1)))
    safe_z = params.get("safe_z", 2.0)
    start = (major, safe_z)
    path = [start, (major, 0.0)]
    depth_per_pass = pitch * 0.1
    for i in range(passes):
        x_val = major - depth_per_pass * (i + 1)
        path.append((x_val, -abs(length)))
        if i != passes - 1:
            path.append((x_val, safe_z))
    return path


def build_groove_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    # Geometrie für die Vorschau (Einstich/Abstich) – grob nach ShopTurn 5.3.2:
    # WICHTIG (User-Anforderung):
    #   In der Vorschau darf nur die Einstich-/Abstich-KONTUR erscheinen –
    #   keine zusätzliche Linie/Anfahrbewegung zu Z0 oder eine Rückzuglinie.
    #
    # Kontur besteht aus:
    #   Startpunkt (Anfangshöhe) -> Tiefe -> Breite -> zurück auf Anfangshöhe.
    diameter = float(params.get("diameter", 0.0) or 0.0)
    width = abs(float(params.get("width", 0.0) or 0.0))
    depth = abs(float(params.get("depth", 0.0) or 0.0))
    z0 = float(params.get("z", 0.0) or 0.0)

    # Bezugspunkt / Einstichlage in Z:
    # 0=Mitte, 1=Linke Flanke, 2=Rechte Flanke
    ref = int(params.get("ref", 0) or 0)
    if ref == 1:  # Linke Flanke
        z_left = z0
        z_right = z0 + width
    elif ref == 2:  # Rechte Flanke
        z_right = z0
        z_left = z0 - width
    else:  # Mitte
        z_left = z0 - (width / 2.0)
        z_right = z0 + (width / 2.0)
    lage = int(params.get("lage", 0) or 0)

    # X ist im Preview als Durchmesser ausgelegt.
    # OD (Mantel außen): Tiefe reduziert Durchmesser.
    # ID (Mantel innen): Tiefe vergrößert Durchmesser.
    if lage == 1:  # Mantel – Innen (ID)
        x_bottom = diameter + depth
    else:
        x_bottom = diameter - depth
    # NUR Kontur (keine Anfahr-/Rückzug-Linie):
    return [
        (diameter, z_left),   # Anfangspunkt (Start-Höhe)
        (x_bottom, z_left),   # Tiefe
        (x_bottom, z_right),  # Breite am Grund
        (diameter, z_right),  # zurück auf Anfangshöhe
    ]
def build_drill_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    """Drill preview path (Bohren).

    Goals (per user request / ShopTurn-like behavior):
      - Z0 is the front face (surface) -> shown at z = 0 in the preview.
      - Drilling goes into the material: negative Z.
        *If the user enters a positive depth, it is interpreted as "into material" and converted to negative.*
      - Show the drilled diameter and a 118° drill point (59° half-angle).

    Conventions in this project:
      - X is a *diameter* coordinate (0 = centerline).
      - Z is horizontal in the preview (see preview widget mapping).
    """
    # --- read inputs
    try:
        diameter = float(params.get("diameter", 0.0) or 0.0)
    except Exception:
        diameter = 0.0

    try:
        depth = float(params.get("depth", 0.0) or 0.0)
    except Exception:
        depth = 0.0

    try:
        safe_z = float(params.get("safe_z", 2.0) or 2.0)
    except Exception:
        safe_z = 2.0

    diameter = max(0.0, diameter)

    # into material => negative Z
    if depth > 0:
        depth = -abs(depth)

    # If no diameter, show only centerline move.
    if diameter <= 1e-9:
        return [
            (0.0, safe_z),
            (0.0, 0.0),
            (0.0, depth),
        ]

    # --- geometry for 118° point (59° half-angle)
    # Our X axis is DIAMETER, so the "radius" at the wall is diameter/2.
    half_angle = math.radians(59.0)
    tanv = math.tan(half_angle)
    tip_len = 0.0
    if abs(tanv) > 1e-12:
        tip_len = (diameter * 0.5) / tanv  # axial length of the point

    # Point apex is at Z = depth. The cylindrical wall ends at cone_start_z.
    cone_start_z = depth + tip_len  # closer to surface (less negative)
    if cone_start_z > 0.0:
        cone_start_z = 0.0  # very shallow: point intersects the surface

    return [
        (0.0, safe_z),            # approach on center
        (0.0, 0.0),               # on surface (Z0)
        (diameter, 0.0),          # diameter at surface
        (diameter, cone_start_z), # cylindrical wall
        (0.0, depth),             # 118° point to center
    ]



def build_keyway_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    mode = int(params.get("mode", 0))
    nut_length = params.get("nut_length", 0.0)
    nut_depth = params.get("nut_depth", 0.0)
    start_dia = params.get("start_x_dia", 0.0)
    start_z = params.get("start_z", 0.0)
    top_clearance = params.get("top_clearance", 1.0)

    if mode == 0:  # axial
        radial_side = int(params.get("radial_side", 0))
        rad_sign = -1 if radial_side == 0 else 1
        top_z = start_z + top_clearance
        bottom_z = start_z - nut_length
        final_dia = start_dia + rad_sign * 2 * nut_depth
        return [
            (start_dia, top_z),
            (start_dia, start_z),
            (final_dia, bottom_z),
        ]

    # face mode
    top_x = start_dia + top_clearance
    inner_x = start_dia - 2 * nut_length
    back_z = start_z - nut_depth
    return [
        (top_x, start_z),
        (inner_x, start_z),
        (inner_x, back_z),
        (top_x, back_z),
    ]


def build_abspanen_path(params: Dict[str, object]) -> List[Tuple[float, float]]:
    """Zeichnet den gewählten Konturpfad für den Abspan-Schritt."""

    source_path = params.get("source_path") or []
    points: List[Tuple[float, float]] = []
    try:
        for point in source_path:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            x_val, z_val = point[0], point[1]
            points.append((float(x_val), float(z_val)))
    except Exception:
        return []
    return points


def build_contour_path(params) -> list:
    """
    Build a contour as **primitives** (lines/arcs) from contour table segments.

    Accepts either:
      - params = {"segments": [...]}  (preferred)
      - params = [...]               (legacy: list of segment dicts)

    Segment dict format (as produced by _collect_contour_segments):
      {
        "mode": "line"|"rapid"|...,
        "x": float, "z": float,
        "x_empty": bool, "z_empty": bool,
        "edge": "none"|"radius"|"chamfer",
        "edge_size": float,
      }

    Notes:
    - X values are **diameter** coordinates (LinuxCNC lathe convention).
    - Edges (radius/chamfer) are applied at the point of the segment row
      (i.e. the corner between previous->this and this->next).
    - Returns a list of primitives:
        {"type":"line","p1":[x,z],"p2":[x,z]}
        {"type":"arc","p1":[x,z],"p2":[x,z],"c":[xc,zc],"ccw":bool}
    """
    # normalize input
    if isinstance(params, dict):
        segments = params.get("segments") or []
    else:
        segments = params or []

    # build absolute point list (respect x_empty/z_empty)
    start_x = 0.0
    start_z = 0.0
    if isinstance(params, dict):
        start_x = float(params.get("start_x", 0.0) or 0.0)
        start_z = float(params.get("start_z", 0.0) or 0.0)

    pts = [(start_x, start_z)]
    last_x = start_x
    last_z = start_z

    coord_mode = 0
    if isinstance(params, dict):
        try:
            coord_mode = int(params.get("coord_mode", 0) or 0)
        except Exception:
            coord_mode = 0

    incremental = coord_mode == 1  # 0=absolut, 1=inkremental

    for s in segments:
        if not isinstance(s, dict):
            continue

        # Coordinate mode handling:
        # - global mode from header (coord_mode) still works
        # - but individual rows may override ABS/INK per axis (as ShopTurn allows mixing)
        #
        # Supported keys in the segment dict (any of them):
        #   x_abs / z_abs (bool)         -> True=ABS, False=INK
        #   x_incremental / z_incremental (bool) -> True=INK, False=ABS
        #   x_mode / z_mode: "abs"|"ink"
        def _axis_is_abs(axis: str) -> Optional[bool]:
            # explicit boolean flags first
            k_abs = f"{axis}_abs"
            if k_abs in s:
                try:
                    return bool(s.get(k_abs))
                except Exception:
                    pass
            k_inc = f"{axis}_incremental"
            if k_inc in s:
                try:
                    return not bool(s.get(k_inc))
                except Exception:
                    pass
            k_mode = f"{axis}_mode"
            if k_mode in s:
                v = str(s.get(k_mode) or "").strip().lower()
                if v in ("abs", "absolute"):
                    return True
                if v in ("ink", "inc", "incremental"):
                    return False
            return None

        x_is_abs = _axis_is_abs("x")
        z_is_abs = _axis_is_abs("z")

        # fall back to global mode if axis override not present
        if x_is_abs is None:
            x_is_abs = not incremental
        if z_is_abs is None:
            z_is_abs = not incremental

        if s.get("x_empty"):
            x = last_x
        else:
            xv = float(s.get("x", 0.0) or 0.0) if not x_is_abs else float(s.get("x", last_x) or last_x)
            x = xv if x_is_abs else (last_x + xv)

        if s.get("z_empty"):
            z = last_z
        else:
            zv = float(s.get("z", 0.0) or 0.0) if not z_is_abs else float(s.get("z", last_z) or last_z)
            z = zv if z_is_abs else (last_z + zv)

        pts.append((x, z))
        last_x, last_z = x, z

    if len(pts) < 2:
        return []
    def _v(a, b):
        return (b[0] - a[0], b[1] - a[1])

    def _norm(v):
        l = math.hypot(v[0], v[1])
        if l <= 1e-12:
            return (0.0, 0.0), 0.0
        return (v[0] / l, v[1] / l), l

    def _perp_ccw(u):
        return (-u[1], u[0])

    def _dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    def _cross(a, b):
        return a[0] * b[1] - a[1] * b[0]

    prim = []
    cur = pts[0]

    def _emit_line(p1, p2):
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) <= 1e-9:
            return
        prim.append({"type": "line", "p1": [float(p1[0]), float(p1[1])], "p2": [float(p2[0]), float(p2[1])]})

    def _emit_arc(p1, p2, c, ccw):
        # avoid degenerate arcs
        if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) <= 1e-9:
            return
        prim.append({
            "type": "arc",
            "p1": [float(p1[0]), float(p1[1])],
            "p2": [float(p2[0]), float(p2[1])],
            "c":  [float(c[0]),  float(c[1])],
            "ccw": bool(ccw),
        })

    for i in range(1, len(pts)):
        p_next = pts[i]

        # edge at point i (corner), requires i in [1, len-2]
        if 1 <= i < len(pts) - 1:
            seg = segments[i - 1] if (i - 1) < len(segments) else {}
            edge_kind = (seg.get("edge") or "none").strip().lower()
            edge_size = float(seg.get("edge_size") or 0.0)

            if edge_kind in ("radius", "fillet") and edge_size > 1e-9:
                p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
                # Directions from corner to previous/next point
                u1, l1 = _norm(_v(p1, p0))   # incoming dir (from corner back)
                u2, l2 = _norm(_v(p1, p2))   # outgoing dir
                if l1 > 1e-9 and l2 > 1e-9:
                    cosang = max(-1.0, min(1.0, _dot(u1, u2)))
                    ang = math.acos(cosang)
                    # if nearly straight, skip edge
                    if ang > 1e-6 and abs(math.pi - ang) > 1e-6:
                        # desired radius, with clamp if geometry is too short
                        r = edge_size
                        tan_half = math.tan(ang / 2.0)
                        if tan_half <= 1e-9:
                            r = 0.0
                        t = r * tan_half if r > 0.0 else 0.0
                        max_t = min(l1, l2) * 0.999
                        if t > max_t and tan_half > 1e-9:
                            r = max_t / tan_half
                            t = max_t

                        if r > 1e-9 and t > 1e-9:
                            # tangent points on each segment
                            pt1 = (p1[0] + u1[0] * t, p1[1] + u1[1] * t)
                            pt2 = (p1[0] + u2[0] * t, p1[1] + u2[1] * t)

                            n1 = _perp_ccw(u1)
                            n2 = _perp_ccw(u2)

                            # compute possible centers by intersecting offset normals
                            tol = max(0.01, r * 0.01)
                            candidates = []
                            for s1 in (1.0, -1.0):
                                c1 = (pt1[0] + n1[0] * r * s1, pt1[1] + n1[1] * r * s1)
                                for s2 in (1.0, -1.0):
                                    c2 = (pt2[0] + n2[0] * r * s2, pt2[1] + n2[1] * r * s2)
                                    if math.hypot(c1[0] - c2[0], c1[1] - c2[1]) <= tol:
                                        c = ((c1[0] + c2[0]) * 0.5, (c1[1] + c2[1]) * 0.5)
                                        candidates.append(c)

                            if candidates:
                                arc_side = normalize_arc_side(seg.get("arc_side"))
                                # pick candidate based on bisector direction
                                bx = u1[0] + u2[0]
                                bz = u1[1] + u2[1]
                                bl = math.hypot(bx, bz)
                                if bl > 1e-9:
                                    bx /= bl
                                    bz /= bl
                                best = None
                                best_score = -1e9
                                for c in candidates:
                                    dx = c[0] - p1[0]
                                    dz = c[1] - p1[1]
                                    score = dx * bx + dz * bz  # projection on bisector
                                    if arc_side == "inner" and score < 0:
                                        continue
                                    if arc_side == "outer" and score > 0:
                                        continue
                                    if abs(score) > best_score:
                                        best_score = abs(score)
                                        best = c
                                if best is None:
                                    best = candidates[0]

                                _emit_line(cur, pt1)
                                # determine CW/CCW using center
                                v1 = (pt1[0] - best[0], pt1[1] - best[1])
                                v2 = (pt2[0] - best[0], pt2[1] - best[1])
                                ccw = _cross(v1, v2) > 0.0
                                _emit_arc(pt1, pt2, best, ccw)
                                cur = pt2
                                continue  # corner consumed

            elif edge_kind in ("chamfer", "fase") and edge_size > 1e-9:
                p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
                u1, l1 = _norm(_v(p0, p1))
                u2, l2 = _norm(_v(p1, p2))
                if l1 > 1e-9 and l2 > 1e-9:
                    d = min(edge_size, l1 * 0.999, l2 * 0.999)
                    pc1 = (p1[0] - u1[0] * d, p1[1] - u1[1] * d)
                    pc2 = (p1[0] + u2[0] * d, p1[1] + u2[1] * d)
                    _emit_line(cur, pc1)
                    _emit_line(pc1, pc2)
                    cur = pc2
                    continue

        # default straight segment
        _emit_line(cur, p_next)
        cur = p_next

    return prim


def validate_contour_segments_for_profile(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate contour definition.

    Important: In the UI, each *row* describes a move to the next point (a segment end point),
    starting from (start_x,start_z). Any edge (chamfer/radius) belongs to the *corner at the end
    of that move* (i.e. between this move and the next one). Therefore edge data is valid for
    all rows except the LAST row (there is no following segment to form a corner).
    """
    errors: List[str] = []
    segs = params.get("contour_segments", []) or []

    if not isinstance(segs, list) or len(segs) < 2:
        errors.append("Kontur: mindestens 2 Segmente/Zeilen erforderlich.")
        return False, errors

    # Start point (implicit first point)
    try:
        start_x = float(params.get("start_x", 0.0))
        start_z = float(params.get("start_z", 0.0))
    except Exception:
        errors.append("Kontur: ungültiger Startpunkt (start_x/start_z).")
        return False, errors

    # Build full point list: p0 = start point, then each row adds a new point.
    pts: List[Tuple[float, float]] = [(start_x, start_z)]
    x, z = start_x, start_z
    for i, seg in enumerate(segs):
        try:
            x = float(seg.get("x", x))
            z = float(seg.get("z", z))
        except Exception:
            errors.append(f"Zeile {i+1}: X/Z ungültig.")
            continue
        pts.append((x, z))

    if len(pts) != len(segs) + 1:
        errors.append("Kontur: interne Punktliste inkonsistent.")
        return False, errors

    # Validate edges (chamfer/radius) at corners:
    # Edge settings live in segs[i] and apply to corner at pts[i+1] with prev=pts[i], next=pts[i+2].
    for i, seg in enumerate(segs):
        etype = (seg.get("edge_type") or "none").strip().lower()
        if etype in ("none", "", "keine"):
            continue

        # last row cannot have an edge (no next segment)
        if i == len(segs) - 1:
            errors.append(f"Zeile {i+1}: {etype} am Ende ist geometrisch unmöglich (keine Folge-Kante).")
            continue

        try:
            ev = float(seg.get("edge_value", 0.0))
        except Exception:
            errors.append(f"Zeile {i+1}: Kantenmaß ungültig.")
            continue

        if ev <= 0.0:
            errors.append(f"Zeile {i+1}: Kantenmaß muss > 0 sein.")
            continue

        p0 = pts[i]
        p1 = pts[i+1]
        p2 = pts[i+2]

        # Vectors along the adjacent segments
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])

        def vlen(v):
            return (v[0] * v[0] + v[1] * v[1]) ** 0.5

        l1 = vlen(v1)
        l2 = vlen(v2)

        # Degenerate segments
        if l1 < 1e-9 or l2 < 1e-9:
            errors.append(f"Zeile {i+1}: Segmentlänge zu klein für {etype}.")
            continue

        # Colinear? (no corner)
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(cross) < 1e-9:
            errors.append(f"Zeile {i+1}: {etype} ist nur an einer Ecke möglich (Segmente sind colinear).")
            continue

        if etype in ("chamfer", "fase"):
            # Simple feasibility: chamfer distance must be smaller than both adjacent segment lengths
            if ev >= min(l1, l2):
                errors.append(f"Zeile {i+1}: Fase ist zu groß für die angrenzenden Segmente.")
        elif etype in ("radius", "r"):
            # Radius needs enough space on both segments.
            # Use same geometry as in build_contour_path: compute offset distance along each segment.
            import math
            cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
            cosang = max(-1.0, min(1.0, cosang))
            ang = math.acos(cosang)
            # For a fillet of radius r, the tangent points are at distance t = r / tan(ang/2)
            t = ev / math.tan(ang / 2.0)
            if t >= l1 or t >= l2:
                errors.append(f"Zeile {i+1}: Radius ist zu groß für die angrenzenden Segmente.")
        else:
            errors.append(f"Zeile {i+1}: unbekannter Kantentyp '{etype}'.")
            continue

    return (len(errors) == 0), errors


def gcode_from_path(path: List[Tuple[float, float]], feed: float, safe_z: float) -> List[str]:
    try:
        from slicer import gcode_from_path as _s
    except Exception:
        _s = None

    if _s:
        return _s([(x, z) for x, z in path], feed, safe_z)

    lines: List[str] = []
    if not path:
        return lines
    x0, z0 = path[0]
    lines.append(f"G0 X{x0:.3f} Z{safe_z:.3f}")
    if len(path) > 1:
        lines.append(f"G1 Z{z0:.3f} F{feed:.3f}")
    for x, z in path[1:]:
        lines.append(f"G1 X{x:.3f} Z{z:.3f}")
    return lines



def gcode_for_operation(
    op: Operation, settings: Dict[str, object] | None = None
) -> List[str]:
    try:
        from slicer import gcode_for_operation as _s
    except Exception:
        _s = None

    if _s:
        return _s(op, settings or {})

    return []


class HandlerClass:
    def __init__(self, halcomp, widgets, paths):
        self.hal = halcomp
        self.w = widgets
        # IMPORTANT: Bind widget lookups strictly to the embedded panel root 'easystep' (not MainWindow)
        self._main_window = widgets
        panel_root = None

        # QTVCP sometimes passes the panel root widget directly as `widgets` (not the main window).
        try:
            if hasattr(self._main_window, 'objectName') and self._main_window.objectName() == 'easystep':
                panel_root = self._main_window
            else:
                panel_root = self._main_window.findChild(QtWidgets.QWidget, 'easystep')
                if panel_root is None:
                    panel_root = getattr(self._main_window, 'easystep', None)
        except Exception:
            panel_root = None

        if panel_root is None:
            # Fallback to the more robust panel discovery helper (handles embedded contexts).
            panel_root = self._find_root_widget()

        if panel_root is None:
            print('[LatheEasyStep][CRITICAL] Panel root "easystep" not found - aborting to avoid wrong widget bindings')
            raise RuntimeError('Panel root "easystep" not found')

        self.w = panel_root
        self.paths = paths
        self.model = ProgramModel()
        self.root_widget = None  # wird nach Panel-Suche gesetzt
        self.tools: Dict[int, Tool] = {}  # loaded tool table
        self._loaded_tools: Dict[int, Tool] | None = None  # cache for repopulating combos after deferred widgets
        self._missing_iso_tools: List[int] = []
        self._connected_param_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()
        self._connected_global_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()
        self._thread_standard_populated = False
        self._thread_standard_signal_connected = False
        self._thread_applying_standard = False
        self._step_last_dir: str | None = None
        self._loading_step = False
        self._deleting = False
        self._saving_step = False
        self._moving_up = False
        self._moving_down = False
        self._generating_gcode = False
        self._creating_new_program = False

        # zentrale Widgets
        self.preview = getattr(self.w, "previewWidget", None)

        # Slice view widgets live inside the embedded panel (objectName: easystep).
        # Depending on how QTVCP instantiates the panel, they may not be direct attributes on self.w.
        panel_root = getattr(self.w, "easystep", None) or self.w

        def _find(name, cls=None):
            w = getattr(self.w, name, None)
            if w is not None:
                return w
            try:
                if cls is None:
                    return panel_root.findChild(QtCore.QObject, name)
                return panel_root.findChild(cls, name)
            except Exception:
                return None

        self.preview_slice = _find("previewSliceWidget", QtWidgets.QWidget)
        self.btn_slice_view = _find("btn_slice_view", QtWidgets.QAbstractButton)

        # Fallback: if the button was renamed in the .ui, pick the first checkable toolbutton
        # that contains 'Schnitt' or 'Seite' in its label.
        if self.btn_slice_view is None:
            try:
                for b in panel_root.findChildren(QtWidgets.QAbstractButton):
                    t = (b.text() or "").lower()
                    if getattr(b, "isCheckable", lambda: False)() and ("schnitt" in t or "seiten" in t):
                        self.btn_slice_view = b
                        break
            except Exception:
                pass
        self.contour_preview = getattr(self.w, "contourPreview", None)
        self.list_ops = getattr(self.w, "listOperations", None)
        self.tab_params = getattr(self.w, "tabParams", None)

        # Standard-Tab auf „Planen“ umschalten, damit beim ersten Klick
        # sofort ein Bearbeitungsschritt hinzugefügt wird (statt nur Programmkopf).
        if self.tab_params is not None:
            try:
                self.tab_params.setCurrentIndex(1)  # 0=Programmkopf, 1=Planen
            except Exception:
                pass

        def _resolve_widget(name: str):
            w = getattr(self.w, name, None)
            if w is not None:
                return w
            w = self._find_any_widget(name)
            if w is not None:
                print(f"[LatheEasyStep] resolved '{name}' via global search")
            return w

        self.btn_add = _resolve_widget("btnAdd")
        self.btn_delete = _resolve_widget("btnDelete")
        self.btn_move_up = _resolve_widget("btnMoveUp")
        self.btn_move_down = _resolve_widget("btnMoveDown")
        self.btn_new_program = _resolve_widget("btnNewProgram")
        self.btn_generate = _resolve_widget("btnGenerate")

        # Programm-Tab
        self.tab_program = _resolve_widget("tabProgram")
        self.program_unit = _resolve_widget("program_unit")
        self.program_shape = _resolve_widget("program_shape")
        self.program_retract_mode = _resolve_widget("program_retract_mode")
        self.program_has_subspindle = _resolve_widget("program_has_subspindle")

        # falls das Objekt in der .ui anders heißt: automatisch finden
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()

        self.program_xa = getattr(self.w, "program_xa", None)
        self.program_xi = getattr(self.w, "program_xi", None)
        self.label_prog_xi = getattr(self.w, "label_prog_xi", None)
        self.program_za = getattr(self.w, "program_za", None)
        self.program_zi = getattr(self.w, "program_zi", None)
        self.program_zb = getattr(self.w, "program_zb", None)
        self.program_w = getattr(self.w, "program_w", None)
        self.label_prog_w = getattr(self.w, "label_prog_w", None)
        self.program_l = getattr(self.w, "program_l", None)
        self.label_prog_l = getattr(self.w, "label_prog_l", None)
        self.program_n = getattr(self.w, "program_n", None)
        self.label_prog_n = getattr(self.w, "label_prog_n", None)
        self.program_sw = getattr(self.w, "program_sw", None)
        self.label_prog_sw = getattr(self.w, "label_prog_sw", None)
        self.program_xt = getattr(self.w, "program_xt", None)
        self.program_zt = getattr(self.w, "program_zt", None)
        self.program_sc = getattr(self.w, "program_sc", None)

        self.program_name = getattr(self.w, "program_name", None)

        self.program_xra = getattr(self.w, "program_xra", None)
        self.label_prog_xra = getattr(self.w, "label_prog_xra", None)
        self.program_xri = getattr(self.w, "program_xri", None)
        self.label_prog_xri = getattr(self.w, "label_prog_xri", None)
        self.program_zra = getattr(self.w, "program_zra", None)
        self.label_prog_zra = getattr(self.w, "label_prog_zra", None)
        self.program_zri = getattr(self.w, "program_zri", None)
        self.label_prog_zri = getattr(self.w, "label_prog_zri", None)

        # Retract option checkboxes (absolute vs incremental)
        self.program_xra_absolute = getattr(self.w, "program_xra_absolute", None)
        self.program_xri_absolute = getattr(self.w, "program_xri_absolute", None)
        self.program_zra_absolute = getattr(self.w, "program_zra_absolute", None)
        self.program_zri_absolute = getattr(self.w, "program_zri_absolute", None)
        self.program_xt_absolute = getattr(self.w, "program_xt_absolute", None)
        self.program_zt_absolute = getattr(self.w, "program_zt_absolute", None)

        self.program_s1 = getattr(self.w, "program_s1", None)
        self.label_prog_s1 = getattr(self.w, "label_prog_s1", None)
        self.program_s3 = getattr(self.w, "program_s3", None)
        self.label_prog_s3 = getattr(self.w, "label_prog_s3", None)

        # optionale globale Felder (falls du sie später in der UI ergänzt)
        self.program_spindle = getattr(self.w, "program_spindle_speed", None)
        self.program_tool = getattr(self.w, "program_tool", None)
        self.program_npv = getattr(self.w, "program_npv", None)

        # Planen-spezifische Optionen
        self.face_mode = getattr(self.w, "face_mode", None)
        self.face_edge_type = getattr(self.w, "face_edge_type", None)
        self.label_face_edge_size = getattr(self.w, "label_face_edge_size", None)
        self.face_edge_size = getattr(self.w, "face_edge_size", None)
        self.label_face_finish_allow_x = getattr(self.w, "label_face_finish_allow_x", None)
        self.face_finish_allow_x = getattr(self.w, "face_finish_allow_x", None)
        self.label_face_finish_allow_z = getattr(self.w, "label_face_finish_allow_z", None)
        self.face_finish_allow_z = getattr(self.w, "face_finish_allow_z", None)
        self.label_face_depth_max = getattr(self.w, "label_face_depth_max", None)
        self.face_depth_max = getattr(self.w, "face_depth_max", None)
        self.label_face_pause = getattr(self.w, "label_face_pause", None)
        self.face_pause_enabled = getattr(self.w, "face_pause_enabled", None)
        self.label_face_pause_distance = getattr(self.w, "label_face_pause_distance", None)
        self.face_pause_distance = getattr(self.w, "face_pause_distance", None)

        # Kontur-Widgets
        self.contour_start_x = getattr(self.w, "contour_start_x", None)
        self.contour_start_z = getattr(self.w, "contour_start_z", None)
        self.contour_name = getattr(self.w, "contour_name", None)
        self.contour_segments = getattr(self.w, "contour_segments", None)
        self.contour_add_segment = getattr(self.w, "contour_add_segment", None)
        self.contour_delete_segment = getattr(self.w, "contour_delete_segment", None)
        self.contour_move_up = getattr(self.w, "contour_move_up", None)
        self.contour_move_down = getattr(self.w, "contour_move_down", None)
        self.contour_edge_type = getattr(self.w, "contour_edge_type", None)
        self.label_contour_edge_size = getattr(self.w, "label_contour_edge_size", None)
        self.contour_edge_size = getattr(self.w, "contour_edge_size", None)
        self._contour_edge_template_text = "Keine"
        self._contour_edge_template_size = 0.0
        self._contour_arc_template_text = "Auto"
        self._contour_row_user_selected = False
        self._op_row_user_selected = False

        # Abspan-Widgets
        self.parting_contour = getattr(self.w, "parting_contour", None)
        self.parting_side = getattr(self.w, "parting_side", None)
        self.parting_tool = getattr(self.w, "parting_tool", None)
        self.parting_spindle = getattr(self.w, "parting_spindle", None)
        self.parting_feed = getattr(self.w, "parting_feed", None)
        self.parting_depth_per_pass = getattr(self.w, "parting_depth_per_pass", None)
        self.parting_mode = getattr(self.w, "parting_mode", None)
        self.parting_pause_enabled = getattr(self.w, "parting_pause_enabled", None)
        self.parting_pause_distance = getattr(self.w, "parting_pause_distance", None)
        self.label_parting_slice_strategy = getattr(self.w, "label_parting_slice_strategy", None)
        self.parting_slice_strategy = getattr(self.w, "parting_slice_strategy", None)
        self._setup_parting_slice_strategy_items()
        self.label_parting_slice_step = getattr(self.w, "label_parting_slice_step", None)
        self.parting_slice_step = getattr(self.w, "parting_slice_step", None)
        # Hide slice step widget by default because value is auto-managed
        if self.label_parting_slice_step is not None:
            try:
                self.label_parting_slice_step.setVisible(False)
            except Exception:
                pass
        if self.parting_slice_step is not None:
            try:
                self.parting_slice_step.setVisible(False)
            except Exception:
                pass
        self.label_parting_allow_undercut = getattr(self.w, "label_parting_allow_undercut", None)
        self.parting_allow_undercut = getattr(self.w, "parting_allow_undercut", None)
        self.label_parting_depth = getattr(self.w, "label_parting_depth", None)
        self.label_parting_pause = getattr(self.w, "label_parting_pause", None)
        self.label_parting_pause_distance = getattr(self.w, "label_parting_pause_distance", None)

        # Gewinde-Widgets
        self.thread_standard = getattr(self.w, "thread_standard", None)
        self.thread_orientation = getattr(self.w, "thread_orientation", None)
        self.thread_tool = getattr(self.w, "thread_tool", None)
        self.thread_spindle = getattr(self.w, "thread_spindle", None)
        self.thread_major_diameter = getattr(self.w, "thread_major_diameter", None)
        self.thread_pitch = getattr(self.w, "thread_pitch", None)
        self.thread_length = getattr(self.w, "thread_length", None)
        self.thread_passes = getattr(self.w, "thread_passes", None)
        self.thread_safe_z = getattr(self.w, "thread_safe_z", None)
        self.thread_depth = getattr(self.w, "thread_depth", None)
        self.thread_peak_offset = getattr(self.w, "thread_peak_offset", None)
        self.thread_first_depth = getattr(self.w, "thread_first_depth", None)
        self.thread_retract_r = getattr(self.w, "thread_retract_r", None)
        self.thread_infeed_q = getattr(self.w, "thread_infeed_q", None)
        self.thread_spring_passes = getattr(self.w, "thread_spring_passes", None)
        self.thread_e = getattr(self.w, "thread_e", None)
        self.thread_l = getattr(self.w, "thread_l", None)
        # Preset-Button (UI: btn_thread_preset)
        self.btn_thread_preset = getattr(self.w, "btn_thread_preset", None)

        # Root-Widget des Panels (für globale Suche nach Labels/Spinboxen)
        self.root_widget = self._find_root_widget()

        # Nach vollständiger Initialisierung aller Widget-Attribute
        # sicherstellen, dass Kern-Widgets gefunden und Signale verbunden werden.
        self._force_attach_core_widgets()

        # Parameter-Widgets für jede Operation
        self._setup_param_maps()
        self._connect_signals()
        self._connect_contour_signals()
        self._setup_thread_helpers()
        self._apply_unit_suffix()
        self._update_program_visibility()
        self._update_parting_mode_visibility()
        self._refresh_preview()
        self._ensure_core_widgets()

        # letzter bekannter Einheiten-Index für Polling
        self._unit_last_index = (
            self.program_unit.currentIndex() if self.program_unit else -1
        )

    # ---- interne Helfer zur Widget-Suche ------------------------------
    def _force_attach_core_widgets(self):
        """Robuste Suche nach Liste/Buttons direkt im Panel-Baum und erneutes Verbinden."""
        app = QtWidgets.QApplication.instance()
        root = self._find_root_widget()
        # Suche primär im Panel-Baum, fallback global allWidgets (embedded-Fall)
        search_roots = []
        if root:
            search_roots.append(root)
        if app:
            search_roots.append(app)  # signalisiert global search below

        def _grab(name: str, cls):
            # zuerst in allen bekannten Wurzel-Widgets suchen
            for r in search_roots:
                if isinstance(r, QtWidgets.QApplication):
                    # global: durch allWidgets iterieren
                    for w in r.allWidgets():
                        try:
                            if w.objectName() == name and isinstance(w, cls):
                                return w
                        except Exception:
                            continue
                        # Zusatz: falls Name passt, aber Typ nicht exakt, trotzdem zurückgeben
                        if w.objectName() == name:
                            return w
                    continue
                obj = r.findChild(cls, name, QtCore.Qt.FindChildrenRecursively)
                if obj:
                    return obj
                obj = r.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
                if obj:
                    return obj
            return None

        self.list_ops = self.list_ops or _grab("listOperations", QtWidgets.QListWidget)
        self.tab_params = self.tab_params or _grab("tabParams", QtWidgets.QTabWidget)
        self.btn_add = self.btn_add or _grab("btnAdd", QtWidgets.QPushButton)
        self.btn_delete = self.btn_delete or _grab("btnDelete", QtWidgets.QPushButton)
        self.btn_move_up = self.btn_move_up or _grab("btnMoveUp", QtWidgets.QPushButton)
        self.btn_move_down = self.btn_move_down or _grab("btnMoveDown", QtWidgets.QPushButton)
        self.btn_new_program = self.btn_new_program or _grab("btnNewProgram", QtWidgets.QPushButton)
        self.btn_generate = self.btn_generate or _grab("btnGenerate", QtWidgets.QPushButton)
        # Sichtbarkeit/Größe sicherstellen, falls das Widget eingebettet "verschwunden" ist
        if self.list_ops:
            try:
                self.list_ops.setMinimumWidth(220)
                self.list_ops.show()
                self.list_ops.raise_()
                # Stelle sicher, dass der Text sichtbar ist (Theme-Unabhängig)
                self.list_ops.setStyleSheet(
                    "QListWidget { background: #e6e6e6; color: black; }"
                    "QListWidget::item:selected { background: #4fa3f7; color: white; }"
                )
            except Exception:
                pass

    def _find_root_widget(self):
        """Suche das Panel auch im eingebetteten Zustand."""
        def _panel_from(widget: QtWidgets.QWidget | None):
            while widget:
                try:
                    if widget.objectName() in PANEL_WIDGET_NAMES:
                        return widget
                except Exception:
                    pass
                widget = widget.parentWidget()
            return None

        def _looks_like_panel(widget: QtWidgets.QWidget) -> bool:
            """Heuristik: verhindert, dass qtdragon_lathe fälschlich als Panel root erkannt wird."""
            try:
                has_ops = widget.findChild(QtWidgets.QWidget, "listOperations", QtCore.Qt.FindChildrenRecursively) is not None
                has_tabs = widget.findChild(QtWidgets.QWidget, "tabParams", QtCore.Qt.FindChildrenRecursively) is not None
                return bool(has_ops and has_tabs)
            except Exception:
                return False

        # direkter Zugriff über widgets-Container
        for panel_name in PANEL_WIDGET_NAMES:
            cand = getattr(self.w, panel_name, None)
            if isinstance(cand, QtWidgets.QWidget):
                return cand

        app = QtWidgets.QApplication.instance()
        # bekannte Panel-Namen direkt suchen
        if app:
            for widget in app.allWidgets():
                try:
                    if widget.objectName() in PANEL_WIDGET_NAMES:
                        if widget.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel(widget):
                            continue
                        return widget
                except Exception:
                    continue

        # aus bestehenden Widgets den Panel-Elternteil hochlaufen
        for w in filter(
            None,
            [
                getattr(self, "root_widget", None),
                getattr(self, "preview", None),
                getattr(self, "contour_preview", None),
                getattr(self, "list_ops", None),
                getattr(self, "tab_params", None),
                getattr(self, "tab_program", None),
                getattr(self, "program_unit", None),
                self.w if isinstance(self.w, QtWidgets.QWidget) else None,
            ],
        ):
            panel = _panel_from(w)
            if panel:
                return panel

        if app:
            # eingebettete Panels sind NICHT topLevelWidgets(), daher allWidgets()
            for widget in app.allWidgets():
                try:
                    if widget.objectName() in PANEL_WIDGET_NAMES:
                        if widget.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel(widget):
                            continue
                        return widget
                except Exception:
                    continue
            # Panel nicht direkt gefunden: Liste suchen und zu Eltern hochlaufen
            try:
                lists = [w for w in app.allWidgets() if getattr(w, "objectName", lambda: "")() == "listOperations"]
            except Exception:
                lists = []
            if lists:
                parent_panel = _panel_from(lists[0])
                if parent_panel:
                    return parent_panel
            # versuche, den Kontur-Tabellen-Container als Root zu nutzen
            try:
                tables = [w for w in app.allWidgets() if getattr(w, "objectName", lambda: "")() == "contour_segments"]
            except Exception:
                tables = []
            for t in tables:
                panel = _panel_from(t)
                if panel:
                    return panel
        # Fallback: irgend ein QWidget aus self.w
        for name in dir(self.w):
            if name.startswith("_"):
                continue
            try:
                obj = getattr(self.w, name)
            except AttributeError:
                continue
            if isinstance(obj, QtWidgets.QWidget):
                return obj  # kein .window(), wir wollen den Embed-Baum
        # letzter Fallback: erstes Toplevel
        if app:
            tops = app.topLevelWidgets()
            if tops:
                return tops[0]
        return None

    def _find_any_widget(self, obj_name: str):
        """Globale Suche per objectName in allen Widgets (embedded-sicher mit erweiterten Fallbacks)."""
        roots: list[QtWidgets.QWidget] = []
        root = self.root_widget or self._find_root_widget()
        if root:
            roots.append(root)
        # Tab-Seiten als zusätzliche Roots berücksichtigen, falls eingebettet
        if root and root.parent():
            parent = root.parent()
            if isinstance(parent, QtWidgets.QTabWidget):
                page = parent.currentWidget()
                if page and page not in roots:
                    roots.append(page)
        # Gemeinsame Ahnen von bekannten Kern-Widgets ergänzen
        if not roots:
            for w in [getattr(self, "list_ops", None), getattr(self, "contour_segments", None)]:
                if isinstance(w, QtWidgets.QWidget):
                    roots.append(w.window())

        # ENHANCED: Search in all root candidates
        for r in roots:
            obj = r.findChild(QtCore.QObject, obj_name, QtCore.Qt.FindChildrenRecursively)
            if obj:
                return obj
        
        app = QtWidgets.QApplication.instance()
        if app:
            # First pass: exact match
            for w in app.allWidgets():
                try:
                    if w.objectName() == obj_name:
                        return w
                except Exception:
                    continue
            
            # ENHANCED: Second pass with tolerant matching for buttons/widgets that might have suffixes
            if obj_name.startswith("btn") or obj_name in ["contour_add_segment", "contour_delete_segment", "contour_move_up", "contour_move_down"]:
                for w in app.allWidgets():
                    try:
                        on = w.objectName()
                        if on and (on == obj_name or re.match(rf"^{re.escape(obj_name)}(_\d+)?$", on)):
                            return w
                    except Exception:
                        continue
        
        # ENHANCED: If still not found, try direct attribute access as last resort
        widget = getattr(self.w, obj_name, None)
        if widget is not None:
            return widget
            
        return None

    def _find_panel_tab_widget(self) -> QtWidgets.QTabWidget | None:
        """Suche das TabWidget innerhalb des eingebetteten Panels."""
        root = self._find_root_widget()
        if root is None:
            return None
        tab_widget = root.findChild(
            QtWidgets.QTabWidget, "tabParams", QtCore.Qt.FindChildrenRecursively
        )
        if tab_widget:
            return tab_widget
        expected_tabs = set(TAB_TRANSLATIONS.keys())
        for candidate in root.findChildren(QtWidgets.QTabWidget):
            for idx in range(candidate.count()):
                page = candidate.widget(idx)
                if page and page.objectName() in expected_tabs:
                    return candidate
        return None

    def _panel_from_widget(self, widget: QtWidgets.QWidget | None):
        """Hilfsfunktion: finde den Panel-Elternteil zu einem Widget."""
        while widget:
            try:
                if widget.objectName() in PANEL_WIDGET_NAMES:
                    return widget
            except Exception:
                pass
            widget = widget.parentWidget()
        return None

    def _find_unit_combo(self):
        """ComboBox mit Einträgen 'mm' und 'inch' direkt in self.w suchen."""
        for name in dir(self.w):
            if name.startswith("_"):
                continue
            try:
                obj = getattr(self.w, name)
            except AttributeError:
                continue

            if not isinstance(obj, QtWidgets.QComboBox):
                continue

            texts = [obj.itemText(i).strip().lower() for i in range(obj.count())]
            if "mm" in texts and "inch" in texts:
                print(f"[LatheEasyStep] using '{name}' as program_unit combo")
                return obj

        print("[LatheEasyStep] no unit combo found via widgets")

        root = self.root_widget or self._find_root_widget()
        if root is not None:
            for combo in root.findChildren(QtWidgets.QComboBox):
                texts = [combo.itemText(i).strip().lower() for i in range(combo.count())]
                txt = " ".join(texts)
                if ("mm" in texts and ("inch" in texts or "in" in txt)) or (
                    "metric" in txt and "imperial" in txt
                ):
                    combo_name = combo.objectName() or "anonymous"
                    print(
                        f"[LatheEasyStep] using tree-scan combo '{combo_name}' as program_unit"
                    )
                    return combo

        return None

    def _find_shape_combo(self):
        """ComboBox für Rohteilform (Zylinder/Rohr/Rechteck/N-Eck) im ganzen Fenster suchen."""
        # Root-Widget holen
        root = self.root_widget or self._find_root_widget()
        if root is None:
            print("[LatheEasyStep] _find_shape_combo: no root_widget")
            return None

        for combo in root.findChildren(QtWidgets.QComboBox):
            texts = [combo.itemText(i).strip().lower() for i in range(combo.count())]
            print(f"[LatheEasyStep] shape combo candidate {combo.objectName()}: {texts}")
            if any(t in texts for t in ("zylinder", "rohr", "rechteck", "n-eck")):
                # In embedded-macro mode, widgets may not exist yet when we do the first
                # round of signal wiring (during import / early init). This means
                # `program_shape` can be discovered later and would then change its value
                # without triggering _handle_global_change(). So: bind + connect here.
                print(f"[LatheEasyStep] using '{combo.objectName()}' as program_shape combo")

                self.program_shape = combo

                if combo not in self._connected_global_widgets:
                    self._connected_global_widgets.add(combo)
                    try:
                        combo.currentIndexChanged.connect(self._handle_global_change)
                    except Exception:
                        pass
                    try:
                        combo.activated.connect(self._handle_global_change)
                    except Exception:
                        pass
                    try:
                        combo.currentTextChanged.connect(self._handle_global_change)
                    except Exception:
                        pass

                return combo

        print("[LatheEasyStep] no shape combo found in tree")
        return None

    def _get_widget_by_name(self, name: str) -> QtWidgets.QWidget | None:
        """Robuste Widget-Auflösung mit erweiterten Fallbacks für embedded Panel.

        Wichtig: Für Parametereinsammeln muss das *richtige* Widget gefunden werden.
        Daher: erst exakte Matches, dann tolerante Matches (z.B. 'foo_2'), dabei
        bevorzugt Eingabewidgets (Spin/DoubleSpin/Combo/LineEdit/Check/Radio).
        """

        # 1) direct attribute (fast path)
        widget = getattr(self.w, name, None)
        if widget is not None:
            return widget

        # 1b) Prefer widgets inside our panel's root (works even if hidden)
        try:
            root = getattr(self, "root_widget", None) or getattr(self, "_find_root_widget", lambda: None)()
        except Exception:
            root = None
        if root is not None:
            try:
                w_in_root = root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
            except Exception:
                w_in_root = None
            if w_in_root is not None:
                return w_in_root

        app = QtWidgets.QApplication.instance()

        preferred_types = (
            QtWidgets.QDoubleSpinBox,
            QtWidgets.QSpinBox,
            QtWidgets.QComboBox,
            QtWidgets.QLineEdit,
            QtWidgets.QCheckBox,
            QtWidgets.QRadioButton,
            QtWidgets.QAbstractButton,
            QtWidgets.QTableWidget,
            QtWidgets.QListWidget,
        )

        def _score(w: QtWidgets.QWidget) -> int:
            # lower is better
            try:
                on = w.objectName() or ""
            except Exception:
                on = ""
            exact = 0 if on == name else 50
            suffix_ok = 0 if re.match(rf"^{re.escape(name)}(_\d+)?$", on) else 20
            type_score = 100
            for i, t in enumerate(preferred_types):
                if isinstance(w, t):
                    type_score = i
                    break
            # prefer widgets inside our panel if possible
            panel_score = 0
            try:
                panel_score = 0 if self._is_widget_in_our_panel(w) else 10
            except Exception:
                panel_score = 10
            return exact + suffix_ok + type_score + panel_score

        # Helper: check if a widget is inside our panel
        # (kept as separate method to avoid nested closure issues)
        if not hasattr(self, "_is_widget_in_our_panel"):
            def _is_widget_in_our_panel(w: QtWidgets.QWidget) -> bool:
                while w is not None:
                    try:
                        if w.objectName() in PANEL_WIDGET_NAMES:
                            return True
                    except Exception:
                        pass
                    try:
                        w = w.parentWidget()
                    except Exception:
                        w = None
                return False
            self._is_widget_in_our_panel = _is_widget_in_our_panel  # type: ignore

        # 2) Exact match inside known panel
        if app:
            for w in app.allWidgets():
                try:
                    if w.objectName() == name and self._is_widget_in_our_panel(w):
                        return w
                except Exception:
                    continue

        # 3) Exact match inside current root widget
        root = self.root_widget or self._find_root_widget()
        if root is not None:
            try:
                widget = root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
                if widget is not None:
                    return widget
            except Exception:
                pass

            # 3b) Tolerant match inside root: name or name_2 etc.
            try:
                candidates = []
                for w in root.findChildren(QtWidgets.QWidget):
                    try:
                        on = w.objectName()
                    except Exception:
                        continue
                    if on == name or re.match(rf"^{re.escape(name)}(_\d+)?$", on):
                        candidates.append(w)
                if candidates:
                    candidates.sort(key=_score)
                    return candidates[0]
            except Exception:
                pass

        # 4) Fallback: exact match anywhere
        if app:
            for w in app.allWidgets():
                try:
                    if w.objectName() == name:
                        return w
                except Exception:
                    continue

            # 4b) Tolerant match anywhere
            try:
                candidates = []
                for w in app.allWidgets():
                    try:
                        on = w.objectName()
                    except Exception:
                        continue
                    if on == name or re.match(rf"^{re.escape(name)}(_\d+)?$", on):
                        candidates.append(w)
                if candidates:
                    candidates.sort(key=_score)
                    return candidates[0]
            except Exception:
                pass

        # 5) ENHANCED: If still not found, set up polling for deferred widgets
        if not hasattr(self, "_deferred_widgets"):
            self._deferred_widgets = set()
        if name not in self._deferred_widgets:
            self._deferred_widgets.add(name)
            # Set up polling timer for this widget (check every 100ms for 3 seconds)
            QtCore.QTimer.singleShot(100, lambda: self._poll_for_widget(name, 30))  # 30 * 100ms = 3 seconds

        return None
    
    def _poll_for_widget(self, name: str, attempts_left: int):
        """Pollt für ein Widget, das bei der ersten Suche nicht gefunden wurde."""
        if attempts_left <= 0:
            print(f"[LatheEasyStep] gave up polling for widget '{name}'")
            return
        
        # Try to find the widget again
        widget = self._find_widget_immediate(name)
        if widget is not None:
            # Found it! Set the attribute and connect signals if it's a button
            setattr(self, name, widget)
            print(f"[LatheEasyStep] found deferred widget '{name}': {widget}")
            
            # If it's a button, try to connect its signal
            if isinstance(widget, QtWidgets.QPushButton):
                self._connect_button_signal(widget, name)
            
            # Update UI state if needed
            self._update_ui_after_widget_found(name, widget)
            return
        
        # Not found yet, schedule next poll
        QtCore.QTimer.singleShot(100, lambda: self._poll_for_widget(name, attempts_left - 1))
    
    def _find_widget_immediate(self, name: str) -> QtWidgets.QWidget | None:
        """Schnelle Widget-Suche ohne Scoring (für Polling)."""
        # Direct attribute
        widget = getattr(self.w, name, None)
        if widget is not None:
            return widget
        
        # Root-based search
        root = self.root_widget or self._find_root_widget()
        if root is not None:
            try:
                return root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
            except Exception:
                pass
        
        # Global search
        app = QtWidgets.QApplication.instance()
        if app:
            for w in app.allWidgets():
                try:
                    if w.objectName() == name:
                        return w
                except Exception:
                    continue
        
        return None
    
    def _connect_button_signal(self, button: QtWidgets.QPushButton, name: str):
        """Verbindet das Signal eines gefundenen Buttons."""
        try:
            if name == "btnAdd":
                button.clicked.connect(self._handle_add_operation)
            elif name == "btnDelete":
                button.clicked.connect(self._handle_delete_operation)
            elif name == "btnMoveUp":
                button.clicked.connect(self._handle_move_up)
            elif name == "btnMoveDown":
                button.clicked.connect(self._handle_move_down)
            elif name == "btnNewProgram":
                button.clicked.connect(self._handle_new_program)
            elif name == "btnGenerate":
                button.clicked.connect(self._handle_generate_gcode)
            elif name == "btn_save_step":
                button.clicked.connect(self._handle_save_step)
            elif name == "btn_load_step":
                button.clicked.connect(self._handle_load_step)
            elif name == "btn_thread_preset":
                button.clicked.connect(self._apply_thread_preset_force)
            elif name == "contour_add_segment":
                button.clicked.connect(self._handle_contour_add_segment)
            elif name == "contour_delete_segment":
                button.clicked.connect(self._handle_contour_delete_segment)
            elif name == "contour_move_up":
                button.clicked.connect(self._handle_contour_move_up)
            elif name == "contour_move_down":
                button.clicked.connect(self._handle_contour_move_down)
            print(f"[LatheEasyStep] connected signal for deferred button '{name}'")
        except Exception as e:
            print(f"[LatheEasyStep] failed to connect signal for button '{name}': {e}")
    
    def _update_ui_after_widget_found(self, name: str, widget: QtWidgets.QWidget):
        """Aktualisiert UI-Zustand nachdem ein Widget gefunden wurde."""
        try:
            # Update visibility states that depend on this widget
            if name in ["face_mode", "face_edge_type"]:
                self._update_face_visibility()
            elif name in ["program_retract_mode", "program_unit"]:
                self._update_retract_visibility()
            elif name == "program_has_subspindle":
                self._update_subspindle_visibility()
            elif name == "program_shape":
                self._update_program_visibility()
            if self._loaded_tools and name in {
                'face_tool', 'thread_tool', 'groove_tool', 'drill_tool', 'parting_tool',
                'contour_tool', 'taper_tool', 'boring_tool'
            }:
                self._populate_tool_combos(self._loaded_tools)
        except Exception as e:
            print(f"[LatheEasyStep] error updating UI after finding '{name}': {e}")
    
    def _force_visibility_updates(self):
        """Erzwingt Sichtbarkeits-Updates für embedded Panel (QtVCP-spezifisch)."""
        try:
            # Force update all visibility-dependent widgets
            self._update_program_visibility()
            self._update_retract_visibility()
            self._update_subspindle_visibility()
            self._update_face_visibility()
            self._update_contour_edge_controls()
            
            # Force repaint of main widgets
            for widget in [self.tab_params, self.list_ops, self.preview]:
                if widget is not None:
                    try:
                        widget.update()
                        widget.repaint()
                    except Exception:
                        pass
            
            # Ensure contour table is visible if it exists
            if self.contour_segments is not None:
                try:
                    self.contour_segments.setVisible(True)
                    self.contour_segments.update()
                except Exception:
                    pass
                    
            print("[LatheEasyStep] forced visibility updates for embedded mode")
        except Exception as e:
            print(f"[LatheEasyStep] error in force visibility updates: {e}")
    
    def _setup_slice_view(self):
        # Optional: side view + slice view (draggable Z slice)
        if getattr(self, "_slice_view_setup_done", False):
            return
        self._slice_view_setup_done = True

        if self.preview is not None:
            try:
                self.preview.set_view_mode("side")
            except Exception:
                pass

        if self.preview_slice is not None:
            try:
                self.preview_slice.set_view_mode("slice")
                self.preview_slice.setVisible(False)
            except Exception:
                pass

        if self.btn_slice_view is not None:
            try:
                self.btn_slice_view.setChecked(False)
                self.btn_slice_view.toggled.connect(self._on_toggle_slice_view)
            except Exception:
                pass

        if self.preview is not None:
            try:
                self.preview.sliceChanged.connect(self._on_slice_changed)
            except Exception:
                pass

    def _on_toggle_slice_view(self, checked: bool):
        if self.preview is None:
            return
        checked = bool(checked)
        # enable/disable slice mode in main preview
        try:
            self.preview.set_slice_enabled(checked)
        except Exception:
            pass
        # show/hide slice preview widget
        if self.preview_slice is not None:
            try:
                self.preview_slice.setVisible(checked)
            except Exception:
                pass
        # update toggle button text
        if self.btn_slice_view is not None:
            try:
                self.btn_slice_view.setText("Seitenansicht" if checked else "Schnittansicht")
            except Exception:
                pass
        # default slice at Z0 when enabling
        if checked:
            try:
                self.preview.set_slice_z(0.0, emit=True)
            except Exception:
                pass
        self._sync_slice_widget()

    def _on_slice_changed(self, z_val: float):
        self._current_slice_z = float(z_val)
        self._sync_slice_widget()

    def _sync_slice_widget(self):
        if self.preview is None or self.preview_slice is None:
            return
        try:
            if not self.preview_slice.isVisible():
                return
        except Exception:
            return
        try:
            self.preview_slice.set_slice_z(getattr(self.preview, "slice_z", 0.0))
        except Exception:
            pass
        try:
            self.preview_slice.set_paths(getattr(self.preview, "paths", []), getattr(self.preview, "active_index", None))
        except Exception:
            pass

    def initialized__(self):
        """Wird aufgerufen, wenn QtVCP die UI komplett aufgebaut hat."""
        self._setup_slice_view()
        # Eindeutige "idx" Dynamic-Properties vergeben (unabhängig von Label-Texten).
        # Hinweis: NICHT in der .ui als Property "idx" hinterlegen, sonst versucht uic setIdx() aufzurufen.
        try:
            from PyQt5.QtWidgets import QWidget
            for _w in self.w.findChildren(QWidget):
                _name = _w.objectName()
                if _name and _w.property("idx") is None:
                    _w.setProperty("idx", _name)
        except Exception:
            pass

        # Jetzt ist das Widget-Hierarchie sicher fertig -> Combos suchen

        # Einheiten-Combo sicherstellen
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()

        # Rohteilform-Combo sicherstellen
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()

        # Gegenspindel-Checkbox und S3-Felder sicherstellen
        root = self.root_widget or self._find_root_widget()
        if self.program_has_subspindle is None and root:
            self.program_has_subspindle = root.findChild(QtWidgets.QCheckBox, "program_has_subspindle")
        if self.label_prog_s3 is None and root:
            self.label_prog_s3 = root.findChild(QtWidgets.QWidget, "label_prog_s3")
        if self.program_s3 is None and root:
            self.program_s3 = root.findChild(QtWidgets.QWidget, "program_s3")

        # Rückzug-Combo sicherstellen
        if self.program_retract_mode is None:
            # 1. Versuch: direkt über widgets-Proxy
            self.program_retract_mode = getattr(self.w, "program_retract_mode", None)

        if self.program_retract_mode is None:
            # 2. Versuch: im Widget-Baum suchen
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                for combo in root.findChildren(QtWidgets.QComboBox):
                    if combo.objectName() == "program_retract_mode":
                        self.program_retract_mode = combo
                        break

        if self.program_retract_mode:
            items = [self.program_retract_mode.itemText(i) for i in range(self.program_retract_mode.count())]
            print(
                f"[LatheEasyStep] retract combo found: "
                f"{self.program_retract_mode.objectName()}, "
                f"items={items}, "
                f"current='{self.program_retract_mode.currentText()}'"
            )
            # Signal hier (spät) sicher verbinden
            self.program_retract_mode.currentIndexChanged.connect(self._handle_global_change)
        else:
            print("[LatheEasyStep] initialized__: no program_retract_mode combo found")

        # falls wir die Rohteilform-Combo jetzt haben: Signal anschließen
        if self.program_shape:
            self.program_shape.currentIndexChanged.connect(self._handle_global_change)

        # falls Gegenspindel-Checkbox jetzt vorhanden: Signal anschließen
        if self.program_has_subspindle:
            self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)

        # Planen-Combos sicherstellen (für Sichtbarkeitsschaltung)
        if self.face_mode is None and root:
            self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
        if self.face_edge_type is None and root:
            self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")
        if self.face_mode:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
        if self.face_edge_type:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)

        # Kontur-Widgets sicherstellen
        if self.contour_start_x is None and root:
            self.contour_start_x = root.findChild(QtWidgets.QDoubleSpinBox, "contour_start_x")
        if self.contour_start_z is None and root:
            self.contour_start_z = root.findChild(QtWidgets.QDoubleSpinBox, "contour_start_z")
        if self.contour_name is None and root:
            self.contour_name = root.findChild(QtWidgets.QLineEdit, "contour_name")
        if self.contour_segments is None and root:
            self.contour_segments = root.findChild(QtWidgets.QTableWidget, "contour_segments")
        if self.contour_add_segment is None and root:
            self.contour_add_segment = root.findChild(QtWidgets.QPushButton, "contour_add_segment")
        if self.contour_delete_segment is None and root:
            self.contour_delete_segment = root.findChild(QtWidgets.QPushButton, "contour_delete_segment")
        if self.contour_move_up is None and root:
            self.contour_move_up = root.findChild(QtWidgets.QPushButton, "contour_move_up")
        if self.contour_move_down is None and root:
            self.contour_move_down = root.findChild(QtWidgets.QPushButton, "contour_move_down")
        if self.contour_edge_type is None and root:
            self.contour_edge_type = root.findChild(QtWidgets.QComboBox, "contour_edge_type")
        if self.label_contour_edge_size is None and root:
            self.label_contour_edge_size = root.findChild(QtWidgets.QLabel, "label_contour_edge_size")
        if self.contour_edge_size is None and root:
            self.contour_edge_size = root.findChild(QtWidgets.QDoubleSpinBox, "contour_edge_size")

        self._connect_contour_signals()

        # Gegenspindel-Checkbox sicherstellen
        if self.program_has_subspindle is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.program_has_subspindle = root.findChild(QtWidgets.QCheckBox, "program_has_subspindle")
        if self.program_has_subspindle:
            self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)

        # Planen-Combos sicherstellen
        if self.face_mode is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
        if self.face_edge_type is None:
            root = self.root_widget or self._find_root_widget()
            if root is not None:
                self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")

        # PATCH: If the UI does not provide dedicated face_* widgets, reuse contour_* widgets.
        # This fixes "keine/fase/radius" switching and enables the edge size input for facing.
        if self.face_edge_type is None and getattr(self, "contour_edge_type", None) is not None:
            self.face_edge_type = self.contour_edge_type
        if getattr(self, "face_edge_size", None) is None and getattr(self, "contour_edge_size", None) is not None:
            self.face_edge_size = self.contour_edge_size
        if getattr(self, "face_edge_size_lbl", None) is None and getattr(self, "contour_edge_size_lbl", None) is not None:
            self.face_edge_size_lbl = self.contour_edge_size_lbl

        if self.face_mode:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
        if self.face_edge_type:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)

        # einmal initial anwenden
        QtCore.QTimer.singleShot(0, self._apply_unit_suffix)
        QtCore.QTimer.singleShot(0, self._update_program_visibility)
        QtCore.QTimer.singleShot(0, self._update_retract_visibility)
        QtCore.QTimer.singleShot(0, self._update_subspindle_visibility)
        QtCore.QTimer.singleShot(0, self._update_face_visibility)
        # Kontur-Tab initial vorbereiten (Spalten/Leerzeile optional)
        QtCore.QTimer.singleShot(0, self._init_contour_table)
        QtCore.QTimer.singleShot(0, self._sync_contour_edge_controls)
        QtCore.QTimer.singleShot(0, self._update_contour_preview_temp)

        # Polling-Timer für die Einheit (mm/inch),
        # falls das Qt-Signal aus irgendeinem Grund nicht feuert
        if self.program_unit:
            self._unit_last_index = self.program_unit.currentIndex()
            self._unit_timer = QtCore.QTimer(self.root_widget or None)
            self._unit_timer.setInterval(200)  # alle 200 ms prüfen
            self._unit_timer.timeout.connect(self._check_unit_change)
            self._unit_timer.start()
            print("[LatheEasyStep] unit polling timer started")
        else:
            print("[LatheEasyStep] initialized__: still no unit combo")

        # Jetzt sicherstellen, dass die Preview-Widgets referenziert sind
        self._ensure_preview_widgets()
        self._refresh_preview()
        # Buttons/Liste sicher verbinden (falls erst jetzt gefunden)
        self._connect_signals()
        try:
            print(f"[LatheEasyStep] core widgets: list_ops={self.list_ops}, btn_add={self.btn_add}, btn_delete={self.btn_delete}")
        except Exception:
            pass
        # Finaler Versuch nach vollständigem UI-Aufbau
        self._ensure_core_widgets()
        self._connect_signals()
        self._setup_thread_helpers()
        self._debug_widget_names()
        # The embedded panel is started in a host environment (QTvcp embed).
        # Depending on timing, the first initialized__ can run before *all* widgets
        # are fully realized / named, so we do a few delayed passes.
        QtCore.QTimer.singleShot(0, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(200, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(700, self._finalize_ui_ready)
        # ENHANCED: More aggressive retries for embedded panel robustness
        QtCore.QTimer.singleShot(100, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(300, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(500, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(1000, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(1500, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(2000, self._finalize_ui_ready)

    def _find_all_core_widgets_comprehensive(self):
        """Umfassende Suche nach Kern-Widgets mit mehreren Fallback-Strategien."""
        root = self._ensure_root_widget() or self._find_root_widget()
        if not root:
            return
        
        def _find_widget_multi(attr_name, obj_names, widget_type):
            """Suche nach einem Widget mit mehreren Strategien."""
            current = getattr(self, attr_name, None)
            if current and isinstance(current, widget_type):
                return current
            
            # Strategie 1-2: Nach objectName suchen (direkt und rekursiv)
            for obj_name in obj_names:
                w = root.findChild(widget_type, obj_name, QtCore.Qt.FindChildrenRecursively)
                if w:
                    setattr(self, attr_name, w)
                    return w
            
            # Strategie 3: Nach Widget-Typ suchen
            children = root.findChildren(widget_type)
            if len(children) == 1:
                setattr(self, attr_name, children[0])
                return children[0]
            
            return None
        
        # Kern-Widgets suchen und speichern
        self.list_ops = _find_widget_multi("list_ops", ["listOperations"], QtWidgets.QListWidget) or self.list_ops
        self.tab_params = _find_widget_multi("tab_params", ["tabParams"], QtWidgets.QTabWidget) or self.tab_params
        self.btn_add = _find_widget_multi("btn_add", ["btnAdd"], QtWidgets.QPushButton) or self.btn_add
        self.btn_delete = _find_widget_multi("btn_delete", ["btnDelete"], QtWidgets.QPushButton) or self.btn_delete
        self.btn_move_up = _find_widget_multi("btn_move_up", ["btnMoveUp"], QtWidgets.QPushButton) or self.btn_move_up
        self.btn_move_down = _find_widget_multi("btn_move_down", ["btnMoveDown"], QtWidgets.QPushButton) or self.btn_move_down
        self.btn_new_program = _find_widget_multi("btn_new_program", ["btnNewProgram"], QtWidgets.QPushButton) or self.btn_new_program
        self.btn_generate = _find_widget_multi("btn_generate", ["btnGenerate"], QtWidgets.QPushButton) or self.btn_generate
        self.btn_save_step = _find_widget_multi("btn_save_step", ["btnSaveStep", "btn_save_step"], QtWidgets.QPushButton) or self.btn_save_step
        self.btn_load_step = _find_widget_multi("btn_load_step", ["btnLoadStep", "btn_load_step"], QtWidgets.QPushButton) or self.btn_load_step
        self.contour_segments = _find_widget_multi("contour_segments", ["contour_segments"], QtWidgets.QTableWidget) or self.contour_segments
        self.contour_add_segment = _find_widget_multi("contour_add_segment", ["contour_add_segment"], QtWidgets.QPushButton) or self.contour_add_segment
        self.contour_delete_segment = _find_widget_multi("contour_delete_segment", ["contour_delete_segment"], QtWidgets.QPushButton) or self.contour_delete_segment
        self.contour_move_up = _find_widget_multi("contour_move_up", ["contour_move_up"], QtWidgets.QPushButton) or self.contour_move_up
        self.contour_move_down = _find_widget_multi("contour_move_down", ["contour_move_down"], QtWidgets.QPushButton) or self.contour_move_down

    def _ensure_root_widget(self) -> QtWidgets.QWidget | None:
        """Stellt sicher, dass self.root_widget gesetzt ist."""
        if self.root_widget:
            return self.root_widget
        self.root_widget = self._find_root_widget()
        return self.root_widget

    def _finalize_ui_ready(self):
        """Nach dem ersten Eventloop-Tick erneut nach Widgets suchen und verbinden."""
        # IMPORTANT: This handler is imported twice in an embedded context:
        #  1) once before the LatheEasyStep .ui is actually loaded (widget tree is incomplete)
        #  2) once after the embedded UI is constructed.
        # If we run our widget lookup / signal connections too early, we bind to the wrong widgets
        # and later UI updates (visibility, previews) won't work.
        if not getattr(self, 'w', None):
            print('[LatheEasyStep] _finalize_ui_ready: widgets not ready (no program_unit) - deferring')
            return

        self._ensure_core_widgets()
        # Nach vollständigem UI-Aufbau explizit auf „Planen“ schalten,
        # damit der erste Klick auf „Schritt hinzufügen“ eine Bearbeitung anlegt.
        if self.tab_params is not None and self.tab_params.currentIndex() == 0:
            try:
                self.tab_params.setCurrentIndex(1)
            except Exception:
                pass
        self._force_attach_core_widgets()
        # Hart nach den Kern-Widgets suchen (embedded-sicher via objectName)
        self.list_ops = self.list_ops or self._find_any_widget("listOperations")
        self.tab_params = self.tab_params or self._find_any_widget("tabParams")
        self.btn_add = self.btn_add or self._find_any_widget("btnAdd")
        self.btn_delete = self.btn_delete or self._find_any_widget("btnDelete")
        self.btn_move_up = self.btn_move_up or self._find_any_widget("btnMoveUp")
        self.btn_move_down = self.btn_move_down or self._find_any_widget("btnMoveDown")
        self.btn_new_program = self.btn_new_program or self._find_any_widget("btnNewProgram")
        self.btn_generate = self.btn_generate or self._find_any_widget("btnGenerate")
        # ENHANCED: Additional search strategies for critical buttons
        if self.btn_add is None:
            self.btn_add = self._get_widget_by_name("btnAdd")
        if self.btn_generate is None:
            self.btn_generate = self._get_widget_by_name("btnGenerate")
        if self.btn_save_step is None:
            self.btn_save_step = self._get_widget_by_name("btn_save_step")
        if self.btn_load_step is None:
            self.btn_load_step = self._get_widget_by_name("btn_load_step")
        # auch Kontur-Buttons per objectName auflösen
        self.contour_add_segment = self.contour_add_segment or self._find_any_widget("contour_add_segment")
        self.contour_delete_segment = self.contour_delete_segment or self._find_any_widget("contour_delete_segment")
        self.contour_move_up = self.contour_move_up or self._find_any_widget("contour_move_up")
        self.contour_move_down = self.contour_move_down or self._find_any_widget("contour_move_down")
        self._ensure_contour_widgets()
        self._init_contour_table()
        try:
            print(f"[LatheEasyStep] core widgets FIX: add={self.btn_add} del={self.btn_delete} list={self.list_ops}")
        except Exception:
            pass
        self._setup_param_maps()
        self._connect_signals()
        self._setup_thread_helpers()
        self._debug_widget_names()
        try:
            print(
                "[LatheEasyStep][debug] finalize: parting_contour=",
                self._get_widget_by_name("parting_contour"),
            )
        except Exception:
            pass
        # Nach vollständigem Aufbau sicherstellen, dass die Kern-Widgets
        # wirklich aus dem Panel stammen (nicht aus dem Host-GUI-Baum).
        self._ensure_core_widgets()
        self._update_parting_contour_choices()
        self._update_parting_ready_state()
        self._apply_tab_titles(self._current_language_code())

        # Ensure language/label texts and all visibility toggles are applied
        # after the widgets are fully available (important for embedded use).
        try:
            self._find_combo_boxes()
            self._apply_language_texts()
            self._handle_global_change()
            # ENHANCED: Force visibility updates for embedded mode
            self._force_visibility_updates()
        except Exception:
            pass

    def _ensure_contour_widgets(self):
        """Sucht fehlende Kontur-Widgets (Start X/Z, Tabelle, Name) robust über objectName."""
        root = self.root_widget or self._panel_from_widget(self.list_ops) or self._find_root_widget()
        if root and self.root_widget is None:
            self.root_widget = root
        def grab(name: str):
            return (
                getattr(self, name, None)
                or self._find_any_widget(name)
                or (root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively) if root else None)
            )
        self.contour_start_x = grab("contour_start_x")
        self.contour_start_z = grab("contour_start_z")
        self.contour_name = grab("contour_name")
        # Tabelle im gleichen Fenster wie die Operationsliste suchen
        candidates: list[QtWidgets.QTableWidget] = []
        table = getattr(self, "contour_segments", None) or grab("contour_segments")
        if table:
            candidates.append(table)
        if root:
            candidates.extend(root.findChildren(QtWidgets.QTableWidget, "contour_segments"))
            candidates.extend(root.findChildren(QtWidgets.QTableWidget))
        app = QtWidgets.QApplication.instance()
        if app:
            candidates.extend([w for w in app.allWidgets() if isinstance(w, QtWidgets.QTableWidget) and w.objectName() == "contour_segments"])
        # beste Übereinstimmung anhand Score wählen
        def _score_table(w: QtWidgets.QTableWidget) -> int:
            score = 0
            if w.objectName() == "contour_segments":
                score += 10
            if self._panel_from_widget(w):
                score += 5
            try:
                if self.list_ops and w.window() == self.list_ops.window():
                    score += 3
            except Exception:
                pass
            try:
                if w.isVisible():
                    score += 1
            except Exception:
                pass
            return score

        chosen = max(candidates, key=_score_table) if candidates else None

        self.contour_segments = chosen
        if self.contour_segments:
            try:
                # genug Platz für ~4-5 Zeilen, darüber Scrollbalken
                self.contour_segments.setMinimumHeight(180)
                self.contour_segments.setMaximumHeight(240)
                self.contour_segments.setMinimumWidth(260)
                self.contour_segments.show()
                self.contour_segments.raise_()
            except Exception:
                pass
        try:
            names = []
            for c in candidates:
                parent = c.parentWidget()
                names.append(
                    f"{c.objectName()} vis={c.isVisible()} score={_score_table(c)} parent={parent.objectName() if parent else None}"
                )
            print(f"[LatheEasyStep][debug] contour table candidates: {names}, chosen={getattr(self.contour_segments, 'objectName', lambda: None)() if self.contour_segments else None}")
        except Exception:
            pass
        self.contour_edge_type = grab("contour_edge_type")
        self.contour_edge_size = grab("contour_edge_size")
        self.label_contour_edge_size = grab("label_contour_edge_size")

    def _ensure_thread_widgets(self):
        """Sichert sich die relevanten Widgets im Gewinde-Tab."""
        if self.thread_standard is None:
            self.thread_standard = self._get_widget_by_name("thread_standard")
        if self.thread_orientation is None:
            self.thread_orientation = self._get_widget_by_name("thread_orientation")
        if self.thread_tool is None:
            self.thread_tool = self._get_widget_by_name("thread_tool")
        if self.thread_spindle is None:
            self.thread_spindle = self._get_widget_by_name("thread_spindle")
        if self.thread_major_diameter is None:
            self.thread_major_diameter = self._get_widget_by_name("thread_major_diameter")
        if self.thread_pitch is None:
            self.thread_pitch = self._get_widget_by_name("thread_pitch")
        if self.thread_length is None:
            self.thread_length = self._get_widget_by_name("thread_length")
        if self.thread_passes is None:
            self.thread_passes = self._get_widget_by_name("thread_passes")
        if self.thread_safe_z is None:
            self.thread_safe_z = self._get_widget_by_name("thread_safe_z")
        if self.thread_depth is None:
            self.thread_depth = self._get_widget_by_name("thread_depth")
        if self.thread_peak_offset is None:
            self.thread_peak_offset = self._get_widget_by_name("thread_peak_offset")
        if self.thread_first_depth is None:
            self.thread_first_depth = self._get_widget_by_name("thread_first_depth")
        if self.thread_retract_r is None:
            self.thread_retract_r = self._get_widget_by_name("thread_retract_r")
        if self.thread_infeed_q is None:
            self.thread_infeed_q = self._get_widget_by_name("thread_infeed_q")
        if self.thread_spring_passes is None:
            self.thread_spring_passes = self._get_widget_by_name("thread_spring_passes")
        if self.thread_e is None:
            self.thread_e = self._get_widget_by_name("thread_e")
        if self.thread_l is None:
            self.thread_l = self._get_widget_by_name("thread_l")
        # Preset-Button: ggf. noch suchen und verbinden
        if self.btn_thread_preset is None:
            self.btn_thread_preset = self._get_widget_by_name("btn_thread_preset")
        if self.btn_thread_preset is not None and not getattr(self, "_thread_preset_connected", False):
            try:
                self._connect_button_once(self.btn_thread_preset, self._apply_thread_preset_force, "_thread_preset_connected")
            except Exception:
                pass

    def _populate_thread_standard_options(self):
        combo = self.thread_standard
        if combo is None or self._thread_standard_populated:
            return

        def _compact(value: float) -> str:
            text = f"{value:.3f}".rstrip("0").rstrip(".")
            return text if text else "0"

        lang = self._current_language_code()
        custom = "Custom" if lang == "en" else "Benutzerdefiniert"

        combo.blockSignals(True)
        combo.clear()
        combo.addItem(custom, {"label": custom})
        # Metric threads (ISO 60°) -> profile "metric"
        for name, diameter, pitch in STANDARD_METRIC_THREAD_SPECS:
            pitch_text = _compact(pitch)
            label = f"{name} x {pitch_text}"
            combo.addItem(
                label,
                {"label": label, "major": diameter, "pitch": pitch, "profile": "metric"},
            )
        # Trapezoidal threads -> profile "tr"
        for name, diameter, pitch in STANDARD_TR_THREAD_SPECS:
            pitch_text = _compact(pitch)
            label = f"{name} x {pitch_text}"
            combo.addItem(
                label,
                {"label": label, "major": diameter, "pitch": pitch, "profile": "tr"},
            )
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self._thread_standard_populated = True

    def _setup_thread_helpers(self):
        self._ensure_thread_widgets()
        combo = self.thread_standard
        if combo is None:
            return
        if not self._thread_standard_populated:
            self._populate_thread_standard_options()
        if not self._thread_standard_signal_connected:
            try:
                combo.currentIndexChanged.connect(self._apply_standard_thread_selection)
                self._thread_standard_signal_connected = True
            except Exception:
                pass
        # Connect preset button (force apply)
        if self.btn_thread_preset is not None and not getattr(self, "_thread_preset_connected", False):
            try:
                self._connect_button_once(self.btn_thread_preset, self._apply_thread_preset_force, "_thread_preset_connected")
            except Exception:
                pass
        # Apply a soft preset now (sets major/pitch + fills empty fields)
        self._apply_standard_thread_selection()

    def _apply_standard_thread_selection(self, *_args, **_kwargs):
        if self._thread_applying_standard:
            return
        combo = self.thread_standard
        if combo is None:
            return
        data = combo.currentData()
        if not isinstance(data, dict):
            return
        major = data.get("major")
        pitch = data.get("pitch")
        self._thread_applying_standard = True
        try:
            # Major & Pitch: immer setzen (sichtbar für den Benutzer)
            if isinstance(major, (int, float)) and self.thread_major_diameter:
                self.thread_major_diameter.setValue(float(major))
            if isinstance(pitch, (int, float)) and self.thread_pitch:
                self.thread_pitch.setValue(float(pitch))
            # Soft-Fill für die restlichen Preset-Werte (nur wenn Felder 0 sind)
            try:
                self._apply_thread_preset(force=False)
            except Exception:
                pass
        finally:
            self._thread_applying_standard = False

    def _set_if_zero(self, spin, value) -> bool:
        """Setzt `spin` nur wenn der aktuellen Wert numerisch ~ 0 ist.

        Returns True wenn gesetzt wurde, False sonst.
        """
        if spin is None:
            return False
        try:
            curr = float(spin.value())
            if abs(curr) < 1e-9:
                spin.setValue(float(value))
                return True
        except Exception:
            pass
        return False

    def _apply_thread_preset(self, force: bool = False):
        """Wendet das im Dropdown gewählte Preset an.

        Wenn force==False: nur Felder befüllen, die noch 0 sind (soft-fill).
        Wenn force==True: alle relevanten Felder überschreiben.
        """
        # Vermeide Rekursion
        if getattr(self, "_thread_applying_standard", False):
            return
        combo = self.thread_standard
        if combo is None:
            return
        data = combo.currentData()
        if not isinstance(data, dict):
            return

        self._thread_applying_standard = True
        try:
            major = data.get("major")
            pitch = data.get("pitch")
            profile = data.get("profile", "metric")

            # Major & Pitch: beim Wechsel immer sichtbar setzen (oder ersetzen bei force)
            if isinstance(major, (int, float)) and self.thread_major_diameter:
                if force or abs(float(self.thread_major_diameter.value())) < 1e-9:
                    self.thread_major_diameter.setValue(float(major))
            if isinstance(pitch, (int, float)) and self.thread_pitch:
                if force or abs(float(self.thread_pitch.value())) < 1e-9:
                    self.thread_pitch.setValue(float(pitch))

            p = float(pitch) if isinstance(pitch, (int, float)) else 1.5

            # Profil-spezifische Default-Werte
            if profile == "tr":
                depth = p * 0.50
                q_angle = 15.0
            else:
                depth = p * 0.6134
                q_angle = 29.5

            first_depth = max(depth * 0.10, p * 0.05)
            peak_offset = -max(depth * 0.50, p * 0.25)

            # Soft-Set / Force-Set
            changed = []
            if force:
                if self.thread_depth is not None:
                    self.thread_depth.setValue(float(depth)); changed.append('depth')
                if self.thread_first_depth is not None:
                    self.thread_first_depth.setValue(float(first_depth)); changed.append('first_depth')
                if self.thread_peak_offset is not None:
                    self.thread_peak_offset.setValue(float(peak_offset)); changed.append('peak_offset')
                if self.thread_retract_r is not None:
                    self.thread_retract_r.setValue(1.5); changed.append('retract_r')
                if self.thread_infeed_q is not None:
                    self.thread_infeed_q.setValue(q_angle); changed.append('infeed_q')
                if self.thread_spring_passes is not None:
                    self.thread_spring_passes.setValue(1); changed.append('spring_passes')
                if self.thread_e is not None:
                    self.thread_e.setValue(0.0); changed.append('e')
                if self.thread_l is not None:
                    self.thread_l.setValue(0); changed.append('l')
            else:
                if self._set_if_zero(self.thread_depth, depth): changed.append('depth')
                if self._set_if_zero(self.thread_first_depth, first_depth): changed.append('first_depth')
                if self._set_if_zero(self.thread_peak_offset, peak_offset): changed.append('peak_offset')
                if self._set_if_zero(self.thread_retract_r, 1.5): changed.append('retract_r')
                if self._set_if_zero(self.thread_infeed_q, q_angle): changed.append('infeed_q')
                # spring passes
                if self.thread_spring_passes is not None:
                    try:
                        if force or int(self.thread_spring_passes.value()) == 0:
                            self.thread_spring_passes.setValue(1); changed.append('spring_passes')
                    except Exception:
                        pass
                if self._set_if_zero(self.thread_e, 0.0): changed.append('e')
                if self.thread_l is not None:
                    try:
                        if force or int(self.thread_l.value()) == 0:
                            self.thread_l.setValue(0); changed.append('l')
                    except Exception:
                        pass
            # Debug-Ausgabe
            try:
                print(f"[LatheEasyStep] _apply_thread_preset: profile={profile}, pitch={p}, changed={changed}")
            except Exception:
                pass
        finally:
            self._thread_applying_standard = False

    def _apply_thread_preset_force(self):
        """Handler: Preset hart anwenden (Button)."""
        try:
            print("[LatheEasyStep] btn_thread_preset clicked: applying preset force")
        except Exception:
            pass
        try:
            self._apply_thread_preset(force=True)
        except Exception:
            pass

    def _debug_widget_names(self):
        """Debug-Ausgabe: vorhandene Buttons/ListWidgets im Baum."""
        root = self.root_widget or self._find_root_widget()
        if root is None:
            print("[LatheEasyStep] debug: no root widget")
            return
        btns = [w.objectName() for w in root.findChildren(QtWidgets.QPushButton)]
        lists = [w.objectName() for w in root.findChildren(QtWidgets.QListWidget)]
        print(f"[LatheEasyStep] debug root: {root.objectName()}")
        print(f"[LatheEasyStep] debug buttons: {btns}")
        print(f"[LatheEasyStep] debug list widgets: {lists}")

    def _connect_button_once(self, button, handler, flag_name: str):

        """Verbindet Buttons stabil (keine Doppel-Auslösung).

    

        Wir disconnecten *immer* zuerst, weil Buttons an mehreren Stellen initialisiert werden können

        (_ensure_core_widgets, _connect_signals, usw.). Das verhindert zuverlässig Mehrfachverbindungen.

        """

        if not button:

            return

        try:

            button.clicked.disconnect()

        except Exception:

            pass

        button.clicked.connect(handler)

        setattr(self, flag_name, True)


    def _ensure_core_widgets(self):
        """Sucht fehlende Kern-Widgets (Liste/Buttons/Tabs) im UI-Baum nach."""
        root = (
            self.root_widget
            or self._panel_from_widget(self.list_ops)
            or self._panel_from_widget(self.contour_segments)
            or (self.program_unit.window() if self.program_unit else None)
            or (self.preview.window() if self.preview else None)
            or self._find_root_widget()
        )
        if root is None:
            return
        self.root_widget = self.root_widget or root

        # Direkt nach bekannten Namen suchen (Fallback: QWidget, falls Typ nicht passt)
        def _find(name: str, cls):
            current = getattr(self, name, None)
            if current:
                return current
            obj_name = (
                "listOperations" if name == "list_ops" else
                "tabParams" if name == "tab_params" else
                "btnAdd" if name == "btn_add" else
                "btnDelete" if name == "btn_delete" else
                "btnMoveUp" if name == "btn_move_up" else
                "btnMoveDown" if name == "btn_move_down" else
                "btnNewProgram" if name == "btn_new_program" else
                "btnGenerate" if name == "btn_generate" else name
            )
            obj = root.findChild(cls, obj_name, QtCore.Qt.FindChildrenRecursively)
            if obj is None:
                obj = root.findChild(
                    QtCore.QObject, obj_name, QtCore.Qt.FindChildrenRecursively
                )
            if obj is None:
                obj = root.findChild(
                    QtWidgets.QWidget, obj_name, QtCore.Qt.FindChildrenRecursively
                )
            if obj:
                setattr(self, name, obj)
            return getattr(self, name, None)

        self.list_ops = _find("list_ops", QtWidgets.QListWidget)
        self.tab_params = _find("tab_params", QtWidgets.QTabWidget)
        self.btn_add = _find("btn_add", QtWidgets.QPushButton)
        self.btn_delete = _find("btn_delete", QtWidgets.QPushButton)
        self.btn_move_up = _find("btn_move_up", QtWidgets.QPushButton)
        self.btn_move_down = _find("btn_move_down", QtWidgets.QPushButton)
        self.btn_new_program = _find("btn_new_program", QtWidgets.QPushButton)
        self.btn_generate = _find("btn_generate", QtWidgets.QPushButton)
        self.btn_save_step = _find("btn_save_step", QtWidgets.QPushButton)
        self.btn_load_step = _find("btn_load_step", QtWidgets.QPushButton)
        self.btn_save_program = _find("btn_save_program", QtWidgets.QPushButton)
        self.btn_load_program = _find("btn_load_program", QtWidgets.QPushButton)
        self.btn_load_tool_table = _find("btn_load_tool_table", QtWidgets.QPushButton)
        self.tool_table_path = _find("tool_table_path", QtWidgets.QLineEdit)
        self.lbl_tool_table_path = _find("lbl_tool_table_path", QtWidgets.QLabel)
        
        # Tool combos and previews
        self.face_tool = _find("face_tool", QtWidgets.QComboBox)
        self.drill_tool = _find("drill_tool", QtWidgets.QComboBox)
        self.groove_tool = _find("groove_tool", QtWidgets.QComboBox)
        self.thread_tool = _find("thread_tool", QtWidgets.QComboBox)
        self.parting_tool = _find("parting_tool", QtWidgets.QComboBox)
        self.face_tool_img = _find("face_tool_img", QtWidgets.QLabel)
        self.drill_tool_img = _find("drill_tool_img", QtWidgets.QLabel)
        self.groove_tool_img = _find("groove_tool_img", QtWidgets.QLabel)
        self.thread_tool_img = _find("thread_tool_img", QtWidgets.QLabel)
        self.parting_tool_img = _find("parting_tool_img", QtWidgets.QLabel)
        # Falls wir die standard Liste nicht finden, versuche ersatzweise gcode_list
        if self.list_ops is None:
            alt = root.findChild(QtWidgets.QListWidget, "gcode_list", QtCore.Qt.FindChildrenRecursively)
            if alt:
                self.list_ops = alt

        # Fallbacks, falls die Typ-Suche scheitert
        if self.list_ops is None:
            candidates = root.findChildren(QtWidgets.QListWidget) or root.findChildren(QtWidgets.QWidget)
            if candidates:
                self.list_ops = candidates[0]
        if self.tab_params is None:
            candidates = root.findChildren(QtWidgets.QTabWidget)
            if candidates:
                self.tab_params = candidates[0]

        # Falls wir erst jetzt Buttons gefunden haben: Signale verbinden
        self._connect_button_once(self.btn_add, self._handle_add_operation, "_btn_add_connected")
        self._connect_button_once(self.btn_delete, self._handle_delete_operation, "_btn_delete_connected")
        self._connect_button_once(self.btn_move_up, self._handle_move_up, "_btn_move_up_connected")
        self._connect_button_once(self.btn_move_down, self._handle_move_down, "_btn_move_down_connected")
        self._connect_button_once(self.btn_new_program, self._handle_new_program, "_btn_new_program_connected")
        self._connect_button_once(self.btn_generate, self._handle_generate_gcode, "_btn_generate_connected")
        self._connect_button_once(self.btn_save_step, self._handle_save_step, "_btn_save_step_connected")
        self._connect_button_once(self.btn_load_step, self._handle_load_step, "_btn_load_step_connected")
        # Preset-Button: hartes Anwenden per Klick
        self._connect_button_once(self.btn_thread_preset, self._apply_thread_preset_force, "_thread_preset_connected")

    def _setup_parting_slice_strategy_items(self):
        combo = getattr(self, "parting_slice_strategy", None)
        if combo is None:
            return
        for idx, data_value in enumerate((1, 2)):
            if idx < combo.count():
                combo.setItemData(idx, data_value, QtCore.Qt.UserRole)

    def _select_slice_strategy_index(self, combo, value) -> bool:
        combo = combo or getattr(self, "parting_slice_strategy", None)
        if combo is None:
            return False
        self._setup_parting_slice_strategy_items()
        try:
            code = int(float(value))
            if code <= 0:
                code = 1
            idx = combo.findData(code, QtCore.Qt.UserRole)
            if idx >= 0:
                combo.setCurrentIndex(idx)
                return True
        except Exception:
            pass
        if isinstance(value, str):
            target = None
            lowered = value.lower()
            if lowered == "parallel_x":
                target = "Parallel X"
            elif lowered == "parallel_z":
                target = "Parallel Z"
            if target is not None:
                idx = combo.findText(target)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                    return True
        return False

    def _check_unit_change(self):
        """Pollt die Einheit-Combo und triggert _apply_unit_suffix() bei Änderung."""
        if self.program_unit is None:
            return

        idx = self.program_unit.currentIndex()
        if idx != self._unit_last_index:
            self._unit_last_index = idx
            print(f"[LatheEasyStep] unit changed (poll) idx={idx}")
            self._apply_unit_suffix()
            self._update_program_visibility()
            self._update_retract_visibility()
            self._update_subspindle_visibility()
            self._update_face_visibility()

    # ---- Parameter-Mapping --------------------------------------------
    def _setup_param_maps(self):
        self.param_widgets: Dict[str, Dict[str, QtWidgets.QWidget]] = {
            OpType.FACE: {
                "tool": self._get_widget_by_name("face_tool"),
                "start_x": self._get_widget_by_name("face_start_x"),
                "start_z": self._get_widget_by_name("face_start_z"),
                "end_x": self._get_widget_by_name("face_end_x"),
                "end_z": self._get_widget_by_name("face_end_z"),
                "safe_z": self._get_widget_by_name("face_safe_z"),
                "feed": self._get_widget_by_name("face_feed"),
                "depth_per_pass": self._get_widget_by_name("face_depth_per_pass"),
                "finish_allow_x": self._get_widget_by_name("face_finish_allow_x"),
                "finish_allow_z": self._get_widget_by_name("face_finish_allow_z"),
                "finish_direction": self._get_widget_by_name("face_finish_direction"),
                "depth_max": self._get_widget_by_name("face_depth_max"),
                "pause_enabled": self._get_widget_by_name("face_pause_enabled"),
                "pause_distance": self._get_widget_by_name("face_pause_distance"),
                "mode": self._get_widget_by_name("face_mode"),
                "edge_type": self._get_widget_by_name("face_edge_type"),
                "edge_size": self._get_widget_by_name("face_edge_size"),
                "spindle": self._get_widget_by_name("face_spindle"),
                "coolant": self._get_widget_by_name("face_coolant"),
            },
            OpType.CONTOUR: {
                "start_x": self._get_widget_by_name("contour_start_x"),
                "start_z": self._get_widget_by_name("contour_start_z"),
                "coord_mode": self._get_widget_by_name("contour_coord_mode"),
            },
            OpType.THREAD: {
                "tool": self._get_widget_by_name("thread_tool"),
                "spindle": self._get_widget_by_name("thread_spindle"),
                "coolant": self._get_widget_by_name("thread_coolant"),
                "orientation": self._get_widget_by_name("thread_orientation"),
                "standard": self._get_widget_by_name("thread_standard"),
                "major_diameter": self._get_widget_by_name("thread_major_diameter"),
                "pitch": self._get_widget_by_name("thread_pitch"),
                "length": self._get_widget_by_name("thread_length"),
                "passes": self._get_widget_by_name("thread_passes"),
                "safe_z": self._get_widget_by_name("thread_safe_z"),
                "thread_depth": self._get_widget_by_name("thread_depth"),
                "peak_offset": self._get_widget_by_name("thread_peak_offset"),
                "first_depth": self._get_widget_by_name("thread_first_depth"),
                "retract_r": self._get_widget_by_name("thread_retract_r"),
                "infeed_q": self._get_widget_by_name("thread_infeed_q"),
                "spring_passes": self._get_widget_by_name("thread_spring_passes"),
                "e": self._get_widget_by_name("thread_e"),
                "l": self._get_widget_by_name("thread_l"),
            },
            OpType.GROOVE: {
                "tool": self._get_widget_by_name("groove_tool"),
                "spindle": self._get_widget_by_name("groove_spindle"),
                "coolant": self._get_widget_by_name("groove_coolant"),
                "diameter": self._get_widget_by_name("groove_diameter"),
                "width": self._get_widget_by_name("groove_width"),
                "ref": self._get_widget_by_name("groove_ref"),
                "lage": self._get_widget_by_name("groove_lage"),
                "use_tool_width": self._get_widget_by_name("groove_use_tool_width"),
                "cutting_width": self._get_widget_by_name("groove_cutting_width"),
                "depth": self._get_widget_by_name("groove_depth"),
                "z": self._get_widget_by_name("groove_z"),
                "feed": self._get_widget_by_name("groove_feed"),
                "stepA": self._get_widget_by_name("groove_step_a"),
                "overlap": self._get_widget_by_name("groove_overlap"),
                "retract": self._get_widget_by_name("groove_retract"),
                "finish": self._get_widget_by_name("groove_finish"),
                "sweep_feed": self._get_widget_by_name("groove_sweep_feed"),
                "chip_amp": self._get_widget_by_name("groove_chip_amp"),
                "chip_n": self._get_widget_by_name("groove_chip_n"),
                "safe_z": self._get_widget_by_name("groove_safe_z"),
                "reduced_feed_start_x": self._get_widget_by_name("groove_reduced_feed_start_x"),
                "reduced_feed": self._get_widget_by_name("groove_reduced_feed"),
                "reduced_rpm": self._get_widget_by_name("groove_reduced_rpm"),
            },
            OpType.DRILL: {
                "tool": self._get_widget_by_name("drill_tool"),
                "spindle": self._get_widget_by_name("drill_spindle"),
                "coolant": self._get_widget_by_name("drill_coolant"),
                "mode": self._get_widget_by_name("drill_mode"),
                "diameter": self._get_widget_by_name("drill_diameter"),
                "depth": self._get_widget_by_name("drill_depth"),
                "feed": self._get_widget_by_name("drill_feed"),
                "safe_z": self._get_widget_by_name("drill_safe_z"),
                "dwell": self._get_widget_by_name("drill_dwell"),
                "peck_depth": self._get_widget_by_name("drill_peck_depth"),
            },
            OpType.KEYWAY: {
                "mode": self._get_widget_by_name("key_mode"),
                "radial_side": self._get_widget_by_name("key_radial_side"),
                "coolant": self._get_widget_by_name("key_coolant"),
                "slot_count": self._get_widget_by_name("key_slot_count"),
                "slot_start_angle": self._get_widget_by_name("key_slot_start_angle"),
                "start_x_dia": self._get_widget_by_name("key_start_diameter"),
                "start_z": self._get_widget_by_name("key_start_z"),
                "nut_length": self._get_widget_by_name("key_nut_length"),
                "nut_depth": self._get_widget_by_name("key_nut_depth"),
                "cutting_width": self._get_widget_by_name("key_cutting_width"),
                "top_clearance": self._get_widget_by_name("key_top_clearance"),
                "depth_per_pass": self._get_widget_by_name("key_depth_per_pass"),
                "plunge_feed": self._get_widget_by_name("key_plunge_feed"),
                "use_c_axis": self._get_widget_by_name("key_use_c_axis"),
                "use_c_axis_switch": self._get_widget_by_name("key_use_c_axis_switch"),
                "c_axis_switch_p": self._get_widget_by_name("key_c_axis_switch_p"),
            },
            OpType.ABSPANEN: {
                "side": self._get_widget_by_name("parting_side"),
                "tool": self._get_widget_by_name("parting_tool"),
                "spindle": self._get_widget_by_name("parting_spindle"),
                "coolant": self._get_widget_by_name("parting_coolant"),
                "feed": self._get_widget_by_name("parting_feed"),
                "depth_per_pass": self._get_widget_by_name("parting_depth_per_pass"),
                "mode": self._get_widget_by_name("parting_mode"),
                "pause_enabled": self._get_widget_by_name("parting_pause_enabled"),
                "pause_distance": self._get_widget_by_name("parting_pause_distance"),
                "slice_strategy": self._get_widget_by_name("parting_slice_strategy"),
                "slice_step": self._get_widget_by_name("parting_slice_step"),
                "allow_undercut": self._get_widget_by_name("parting_allow_undercut"),
            },
        }

    # ---- Signalanschlüsse ---------------------------------------------
    
    
    def _find_by_idx(self, cls, idx: str, fallback_name: str = None):
        """Find widget by custom Qt property 'idx' (preferred) or objectName as fallback."""
        try:
            w = None
            # First pass: idx property
            for cand in self.w.findChildren(cls):
                try:
                    if cand.property("idx") == idx:
                        return cand
                except Exception:
                    continue
            # Fallback: objectName
            if fallback_name:
                return self.w.findChild(cls, fallback_name)
        except Exception:
            pass
        return None

    def _connect_live_update(self, widget):
            """Connect changes of a widget to live-update the currently selected operation."""
            if widget is None:
                return
            from PyQt5 import QtWidgets

            def _safe_connect(signal):
                try:
                    signal.connect(self._on_param_changed)
                except Exception:
                    pass

            if isinstance(widget, QtWidgets.QComboBox):
                _safe_connect(widget.currentIndexChanged)
            elif isinstance(widget, QtWidgets.QAbstractSpinBox):
                _safe_connect(widget.valueChanged)
            elif isinstance(widget, QtWidgets.QCheckBox):
                _safe_connect(widget.toggled)
            elif isinstance(widget, QtWidgets.QLineEdit):
                _safe_connect(widget.textChanged)

    def _on_param_changed(self, *args):
        """Called whenever a parameter field changes; updates op + preview."""
        if getattr(self, "_ui_loading", False):
            return
        row = -1
        try:
            if self.listOperations:
                row = self.listOperations.currentRow()
        except Exception:
            row = -1
        if row < 0:
            return
        try:
            self._update_selected_operation(row)
        except Exception as e:
            print(f"[LatheEasyStep] _on_param_changed: update failed: {e}")

    def _connect_signals(self):
            # Stelle sicher, dass die Kern-Widgets vorhanden sind, bevor wir Signale verbinden
            self._ensure_core_widgets()
            if self.tab_params is None:
                self.tab_params = self._get_widget_by_name("tabParams")

            self._connect_button_once(self.btn_add, self._handle_add_operation, "_btn_add_connected")
            self._connect_button_once(self.btn_delete, self._handle_delete_operation, "_btn_delete_connected")
            self._connect_button_once(self.btn_move_up, self._handle_move_up, "_btn_move_up_connected")
            self._connect_button_once(self.btn_move_down, self._handle_move_down, "_btn_move_down_connected")
            self._connect_button_once(self.btn_new_program, self._handle_new_program, "_btn_new_program_connected")
            self._connect_button_once(self.btn_generate, self._handle_generate_gcode, "_btn_generate_connected")
            self._connect_button_once(self.btn_load_tool_table, self._handle_load_tool_table, "_btn_load_tool_table_connected")
            self._connect_button_once(self.btn_save_program, self._handle_save_program, "_btn_save_program_connected")
            self._connect_button_once(self.btn_load_program, self._handle_load_program, "_btn_load_program_connected")
            if self.list_ops and not getattr(self, "_list_ops_connected", False):
                self.list_ops.currentRowChanged.connect(self._handle_selection_change)
                self._list_ops_connected = True
            if self.list_ops and not getattr(self, "_list_ops_double_click_connected", False):
                self.list_ops.itemDoubleClicked.connect(self._on_step_double_clicked)
                self._list_ops_double_click_connected = True
            if self.list_ops and not getattr(self, "_list_ops_click_connected", False):
                self.list_ops.clicked.connect(self._mark_operation_user_selected)
                self._list_ops_click_connected = True
            if self.tab_params and not getattr(self, "_tab_params_connected", False):
                self.tab_params.currentChanged.connect(self._handle_tab_changed)
                self._tab_params_connected = True
            if self.parting_mode and not getattr(self, "_parting_mode_connected", False):
                self.parting_mode.currentIndexChanged.connect(
                    self._update_parting_mode_visibility
                )
                self._parting_mode_connected = True

            # Tool combo previews
            tool_combos = ["face_tool", "drill_tool", "groove_tool", "thread_tool", "parting_tool"]
            for combo_name in tool_combos:
                combo = getattr(self, combo_name, None)
                if combo and not getattr(self, f"_{combo_name}_connected", False):
                    combo.currentIndexChanged.connect(self._update_tool_previews)
                    setattr(self, f"_{combo_name}_connected", True)

            # Parameterfelder
            for widgets in self.param_widgets.values():
                for widget in widgets.values():
                    if widget is None:
                        continue
                    if widget in self._connected_param_widgets:
                        continue
                    if isinstance(widget, QtWidgets.QComboBox):
                        widget.currentIndexChanged.connect(self._handle_param_change)
                    elif isinstance(widget, QtWidgets.QAbstractButton):
                        widget.toggled.connect(self._handle_param_change)
                    else:
                        widget.valueChanged.connect(self._handle_param_change)
                    self._connected_param_widgets.add(widget)

            # Form-Logik (Einheiten / Rohteilform / Rückzug)
            if self.program_unit and self.program_unit not in self._connected_global_widgets:
                self.program_unit.currentIndexChanged.connect(self._handle_global_change)
                self._connected_global_widgets.add(self.program_unit)
            if self.program_shape and self.program_shape not in self._connected_global_widgets:
                self.program_shape.currentIndexChanged.connect(self._handle_global_change)
                self._connected_global_widgets.add(self.program_shape)
            if self.program_retract_mode and self.program_retract_mode not in self._connected_global_widgets:
                self.program_retract_mode.currentIndexChanged.connect(self._handle_global_change)
                self._connected_global_widgets.add(self.program_retract_mode)
            if self.program_has_subspindle and self.program_has_subspindle not in self._connected_global_widgets:
                self.program_has_subspindle.toggled.connect(self._update_subspindle_visibility)
                self._connected_global_widgets.add(self.program_has_subspindle)
            self._apply_language_texts()
            lang_combo = self._get_widget_by_name(LANGUAGE_WIDGET_NAME)
            if lang_combo and not getattr(self, "_language_connected", False):
                lang_combo.currentIndexChanged.connect(self._handle_language_change)
                self._language_connected = True
            # --- Live update + visibility for Planen (Face) ---
            try:
                if getattr(self, "face_mode", None):
                    self.face_mode.currentIndexChanged.connect(lambda *_: self._update_face_visibility())
                if getattr(self, "face_edge_type", None):
                    self.face_edge_type.currentIndexChanged.connect(lambda *_: self._update_face_visibility())
            except Exception:
                pass
            # --- Live update + visibility for Bohren (Drill) ---
            try:
                if getattr(self, "drill_mode", None):
                    self.drill_mode.currentIndexChanged.connect(lambda *_: self._update_drill_visibility())
            except Exception:
                pass

            # Live-update operation model + preview when parameters change
            for w in [
                # Face (Planen)
                getattr(self, "face_start_z", None), getattr(self, "face_end_z", None),
                getattr(self, "face_stepover", None), getattr(self, "face_doc", None),
                getattr(self, "face_allowance_x", None), getattr(self, "face_allowance_z", None),
                getattr(self, "face_finish_allow_x", None), getattr(self, "face_finish_allow_z", None),
                getattr(self, "face_rpm", None), getattr(self, "face_feed", None),
                getattr(self, "face_plunge", None), getattr(self, "face_retract", None),
                getattr(self, "face_mode", None), getattr(self, "face_finish_direction", None),
                getattr(self, "face_edge_type", None), getattr(self, "face_edge_size", None),
                getattr(self, "face_tool", None), getattr(self, "face_coolant", None),
            ]:
                self._connect_live_update(w)



    def _current_language_code(self) -> str:
        combo = self._get_widget_by_name(LANGUAGE_WIDGET_NAME)
        if combo is None:
            return DEFAULT_LANGUAGE
        return "en" if combo.currentIndex() == 1 else "de"

    def _handle_language_change(self, *_args):
        self._apply_language_texts()
        self._thread_standard_populated = False
        self._setup_thread_helpers()

    def _apply_language_texts(self):
        lang = self._current_language_code()
        for name, translations in TEXT_TRANSLATIONS.items():
            widget = self._get_widget_by_name(name)
            if widget is None:
                continue
            text = translations.get(lang)
            if text is not None:
                try:
                    widget.setText(text)
                except Exception:
                    pass
        self._apply_combo_translations(lang)
        self._handle_global_change()
        self._apply_tab_titles(lang)
        self._apply_button_translations(lang)
        # Thread tooltips (localized)
        try:
            self._apply_thread_tooltips(lang)
        except Exception:
            pass
        try:
            self._apply_parting_tooltips(lang)
        except Exception:
            pass
        try:
            self._apply_groove_tooltips(lang)
        except Exception:
            pass

    def _apply_combo_translations(self, lang: str):
        for name, options in COMBO_OPTION_TRANSLATIONS.items():
            widget = self._get_widget_by_name(name)
            if widget is None or lang not in options:
                continue
            current_index = widget.currentIndex()
            widget.blockSignals(True)
            widget.clear()
            for entry in options[lang]:
                widget.addItem(entry)
            widget.setCurrentIndex(max(0, min(current_index, widget.count() - 1)))
            widget.blockSignals(False)
        self._setup_parting_slice_strategy_items()

    def _apply_tab_titles(self, lang: str):
        tab_widget = self._find_panel_tab_widget() or self.tab_params
        if tab_widget is None:
            return
        self.tab_params = tab_widget
        count = tab_widget.count()
        for idx in range(count):
            title = None
            translations = None
            tab_widget_page = tab_widget.widget(idx)
            if tab_widget_page is not None:
                tab_name = tab_widget_page.objectName()
                translations = TAB_TRANSLATIONS.get(tab_name)
            if translations is None and idx < len(TAB_ORDER):
                translations = TAB_TRANSLATIONS.get(TAB_ORDER[idx])
            if translations:
                title = translations.get(lang)
            if title is None:
                current_text = self.tab_params.tabText(idx).strip()
                for translations in TAB_TRANSLATIONS.values():
                    if current_text in translations.values():
                        title = translations.get(lang)
                        break
            if title:
                try:
                    self.tab_params.setTabText(idx, title)
                except Exception:
                    pass

    def _apply_button_translations(self, lang: str):
        for name, translations in BUTTON_TRANSLATIONS.items():
            button = self._get_widget_by_name(name)
            if button is None:
                continue
            text = translations.get(lang)
            if text is not None:
                try:
                    button.setText(text)
                except Exception:
                    pass

        # Planen-spezifische Logik
        if getattr(self, "face_mode", None) and self.face_mode not in self._connected_param_widgets:
            self.face_mode.currentIndexChanged.connect(self._update_face_visibility)
            self._connected_param_widgets.add(self.face_mode)
        if getattr(self, "face_edge_type", None) and self.face_edge_type not in self._connected_param_widgets:
            self.face_edge_type.currentIndexChanged.connect(self._update_face_visibility)
            self._connected_param_widgets.add(self.face_edge_type)

        # Abspan-spezifische Logik
        if getattr(self, "parting_contour", None) and not getattr(self, "_parting_contour_connected", False):
            self.parting_contour.currentIndexChanged.connect(self._update_parting_ready_state)
            self.parting_contour.editTextChanged.connect(self._update_parting_ready_state)
            self._parting_contour_connected = True

        self._connect_contour_signals()

    def _connect_contour_signals(self):
        """Verbindet alle Kontur-Widgets nur einmal."""
        self._ensure_contour_widgets()

    def _apply_thread_tooltips(self, lang: str):
        """Setzt Tooltips für bekannte Thread-Widgets gemäß Sprache."""
        for name, translations in THREAD_TOOLTIP_TRANSLATIONS.items():
            widget = self._get_widget_by_name(name)
            if widget is None:
                continue
            text = translations.get(lang) or translations.get("de")
            try:
                widget.setToolTip(text)
            except Exception:
                pass
        for btn_attr, handler, flag in (
            ("contour_add_segment", self._handle_contour_add_segment, "_contour_add_connected"),
            ("contour_delete_segment", self._handle_contour_delete_segment, "_contour_delete_connected"),
            ("contour_move_up", self._handle_contour_move_up, "_contour_move_up_connected"),
            ("contour_move_down", self._handle_contour_move_down, "_contour_move_down_connected"),
        ):
            btn = getattr(self, btn_attr, None)
            if btn and not getattr(self, flag, False):
                connected = False
                try:
                    btn.clicked.connect(handler, QtCore.Qt.UniqueConnection)
                    connected = True
                except TypeError:
                    pass
                except Exception:
                    pass
                if not connected:
                    try:
                        btn.clicked.disconnect(handler)
                    except Exception:
                        pass
                    try:
                        btn.clicked.connect(handler)
                        connected = True
                    except Exception:
                        connected = False
                if connected:
                    setattr(self, flag, True)

        if getattr(self, "contour_segments", None) and not getattr(self, "_contour_table_connected", False):
            self.contour_segments.itemChanged.connect(self._handle_contour_table_change)
            self.contour_segments.currentCellChanged.connect(self._handle_contour_row_select)
            self._contour_table_connected = True

    def _apply_parting_tooltips(self, lang: str):
        """Setzt Tooltips für bekannte Abspanen-Widgets gemäß Sprache."""
        for name, translations in PARTING_TOOLTIP_TRANSLATIONS.items():
            widget = self._get_widget_by_name(name)
            if widget is None:
                continue
            text = translations.get(lang) or translations.get("de")
            try:
                widget.setToolTip(text)
                try:
                    widget.setWhatsThis(text)
                except Exception:
                    # some widgets may not implement setWhatsThis
                    pass
            except Exception:
                pass
            self._contour_table_connected = True

    def _apply_groove_tooltips(self, lang: str):
        """Setzt Tooltips für bekannte Nut-Widgets gemäß Sprache."""
        for name, translations in GROOVE_TOOLTIP_TRANSLATIONS.items():
            widget = self._get_widget_by_name(name)
            if widget is None:
                continue
            text = translations.get(lang) or translations.get("de")
            try:
                widget.setToolTip(text)
                try:
                    widget.setWhatsThis(text)
                except Exception:
                    pass
            except Exception:
                pass

        if getattr(self, "contour_start_x", None) and not getattr(self, "_contour_start_x_connected", False):
            self.contour_start_x.valueChanged.connect(self._update_contour_preview_temp)
            self._contour_start_x_connected = True
        if getattr(self, "contour_start_z", None) and not getattr(self, "_contour_start_z_connected", False):
            self.contour_start_z.valueChanged.connect(self._update_contour_preview_temp)
            self._contour_start_z_connected = True
        if getattr(self, "contour_name", None) and not getattr(self, "_contour_name_connected", False):
            self.contour_name.textChanged.connect(self._update_contour_preview_temp)
            self.contour_name.textChanged.connect(self._update_parting_contour_choices)
            self._contour_name_connected = True

        if getattr(self, "contour_edge_type", None) and not getattr(self, "_contour_edge_type_connected", False):
            self.contour_edge_type.currentIndexChanged.connect(self._handle_contour_edge_change)
            self._contour_edge_type_connected = True
        if getattr(self, "contour_edge_size", None) and not getattr(self, "_contour_edge_size_connected", False):
            self.contour_edge_size.valueChanged.connect(self._handle_contour_edge_change)
            self._contour_edge_size_connected = True

    # ---- Abspan-Helfer ----------------------------------------------
    def _available_contour_names(self) -> List[str]:
        names: List[str] = []
        contour_idx = 0
        for op in self.model.operations:
            if op is None:
                continue
            if op.op_type != OpType.CONTOUR:
                try:
                    print(
                        f"[LatheEasyStep][debug] contour-scan skip op type {op.op_type}"
                    )
                except Exception:
                    pass
                continue
            name = self._contour_name_or_fallback(op, contour_idx)
            if name and name not in names:
                names.append(name)
            contour_idx += 1
        if getattr(self, "contour_name", None):
            live_name = self.contour_name.text().strip()
            if not live_name:
                # Wenn der Nutzer noch keinen Namen vergeben hat, aber bereits
                # Segmente eingetragen sind, vergeben wir einen Fallback-Namen,
                # damit die Kontur im Abspan-Tab auswählbar wird.
                if getattr(self, "contour_segments", None) and self.contour_segments.rowCount() > 0:
                    live_name = self._fallback_contour_name(self._contour_count())
                    try:
                        self.contour_name.blockSignals(True)
                        self.contour_name.setText(live_name)
                    finally:
                        self.contour_name.blockSignals(False)
            if live_name and live_name not in names:
                names.append(live_name)
        return names

    def _current_parting_contour_name(self) -> str:
        """Gibt den aktuell ausgewählten Kontur-Namen im Abspan-Tab zurück."""
        if getattr(self, "parting_contour", None) is None:
            self.parting_contour = self._get_widget_by_name("parting_contour")
        if getattr(self, "parting_contour", None) is None:
            return ""
        return self.parting_contour.currentText().strip()

    def _debug_contour_state(self, context: str = ""):
        """Zusätzliche Debug-Ausgabe für die Kontur-Erkennung im Abspan-Tab."""
        prefix = f"[LatheEasyStep][debug] parting contour ({context})" if context else "[LatheEasyStep][debug] parting contour"
        try:
            op_infos = []
            contour_idx = 0
            for idx, op in enumerate(self.model.operations):
                if op.op_type != OpType.CONTOUR:
                    continue
                name = self._contour_name_or_fallback(op, contour_idx)
                segs = op.params.get("segments") if isinstance(op.params, dict) else None
                seg_count = len(segs) if isinstance(segs, list) else "n/a"
                path_len = len(op.path) if getattr(op, "path", None) else 0
                op_infos.append(
                    f"op#{idx} contour_idx={contour_idx} name='{name}' segments={seg_count} path_len={path_len}"
                )
                contour_idx += 1

            live_name = self.contour_name.text().strip() if getattr(self, "contour_name", None) else ""
            live_rows = self.contour_segments.rowCount() if getattr(self, "contour_segments", None) else 0
            available = self._available_contour_names()
            print(prefix)
            print(f"  ops: {op_infos if op_infos else 'keine Kontur-Operationen'}")
            print(f"  live contour widget name='{live_name}' rows={live_rows}")
            print(f"  available names for parting: {available}")
            if getattr(self, "parting_contour", None):
                current = self.parting_contour.currentText().strip()
                print(f"  parting combo current text='{current}' editable={self.parting_contour.isEditable()}")
        except Exception as exc:
            print(f"[LatheEasyStep][debug] parting contour debug failed: {exc}")

    def _resolve_contour_path(self, contour_name: str) -> List[Tuple[float, float]]:
        if not contour_name:
            return []
        contour_idx = 0
        for op in self.model.operations:
            if op.op_type != OpType.CONTOUR:
                continue
            name = self._contour_name_or_fallback(op, contour_idx)
            if name != contour_name:
                contour_idx += 1
                continue
            if not op.path:
                self.model.update_geometry(op)
            try:
                return list(op.path or [])
            except Exception:
                return []
            finally:
                contour_idx += 1
        # Fallback: aktuelle Kontur-Eingabe verwenden, auch wenn noch keine Operation
        if (
            getattr(self, "contour_name", None)
            and getattr(self, "contour_segments", None)
            and self.contour_name.text().strip() == contour_name
        ):
            try:
                return build_contour_path(
                    {
                        "start_x": self.contour_start_x.value()
                        if getattr(self, "contour_start_x", None)
                        else 0.0,
                        "start_z": self.contour_start_z.value()
                        if getattr(self, "contour_start_z", None)
                        else 0.0,
                        "coord_mode": self.contour_coord_mode.currentIndex()
                        if getattr(self, "contour_coord_mode", None)
                        else 0,
                        "segments": self._collect_contour_segments(),
                    }
                )
            except Exception:
                return []
        return []

    def _update_parting_contour_choices(self):
        """Befüllt die Kontur-Auswahl im Abspan-Tab dynamisch."""
        if getattr(self, "parting_contour", None) is None:
            self.parting_contour = self._get_widget_by_name("parting_contour")
        if getattr(self, "parting_contour", None) is None:
            print("[LatheEasyStep][debug] parting_contour widget not found -> skip refresh")
            return

        self._debug_contour_state("before refresh")
        names = self._available_contour_names()
        current = self.parting_contour.currentText().strip()
        self.parting_contour.blockSignals(True)
        self.parting_contour.clear()
        for name in names:
            self.parting_contour.addItem(name)
        if current:
            self.parting_contour.setCurrentText(current)
        elif names:
            self.parting_contour.setCurrentIndex(0)
        self.parting_contour.blockSignals(False)
        self._update_parting_ready_state()
        self._debug_contour_state("after refresh")

    def _update_parting_ready_state(self, *args, **kwargs):
        if self.btn_add is None:
            return
        if self._current_op_type() != OpType.ABSPANEN:
            self.btn_add.setEnabled(True)
            return
        if getattr(self, "parting_contour", None) is None:
            self.parting_contour = self._get_widget_by_name("parting_contour")
        if getattr(self, "parting_contour", None) is None:
            self.btn_add.setEnabled(False)
            return
        available = self._available_contour_names()
        name = self._current_parting_contour_name()
        ready = bool(name) and name in available
        self.btn_add.setEnabled(ready)

    def _update_parting_mode_visibility(self):
        """Versteckt Schrupp-spezifische Felder beim Schlichten."""

        mode_idx = self.parting_mode.currentIndex() if self.parting_mode else 0
        show_roughing = mode_idx == 0
        # Note: the Slicing Step widget is intentionally hidden because the
        # `slice_step` value is now auto-derived from `depth_per_pass` by
        # default. We keep the Slicing Strategy visible but hide the explicit
        # numeric entry to avoid confusion.
        for widget in (
            self.label_parting_depth,
            self.parting_depth_per_pass,
            self.label_parting_pause,
            self.parting_pause_enabled,
            self.label_parting_pause_distance,
            self.parting_pause_distance,
            self.label_parting_slice_strategy,
            self.parting_slice_strategy,
            # slice_step intentionally omitted from visibility toggling
            self.label_parting_allow_undercut,
            self.parting_allow_undercut,
        ):
            if widget is not None:
                widget.setVisible(show_roughing)

        # Ensure the explicit Slicing Step field is always hidden because the
        # slice step is auto-managed; hide both label and input if present.
        for hidden_widget in (getattr(self, "label_parting_slice_step", None), getattr(self, "parting_slice_step", None)):
            if hidden_widget is not None:
                hidden_widget.setVisible(False)

    def _handle_tab_changed(self, *_args, **_kwargs):
        """Aktualisiert Abspan-Felder beim Tab-Wechsel."""
        self._update_parting_contour_choices()
        self._update_parting_ready_state()

    def _fallback_contour_name(self, idx: int) -> str:
        return f"Kontur {idx + 1}"

    def _contour_count(self) -> int:
        return sum(1 for op in self.model.operations if op.op_type == OpType.CONTOUR)

    def _contour_name_or_fallback(self, op: Operation, idx: int) -> str:
        name = str(op.params.get("name") or "").strip()
        if not name:
            name = self._fallback_contour_name(idx)
            try:
                op.params["name"] = name
            except Exception:
                pass
        return name

    def _contour_sequence_index(self, target: Operation) -> int | None:
        """Zählt nur Kontur-Operationen und gibt deren Reihenindex zurück."""
        idx = 0
        for op in self.model.operations:
            if op.op_type != OpType.CONTOUR:
                continue
            if op is target:
                return idx
            idx += 1
        return None

    # ---- Helfer -------------------------------------------------------
    def _current_op_type(self) -> str:
        if self.tab_params is None:
            self.tab_params = self._get_widget_by_name("tabParams")
        idx = self.tab_params.currentIndex() if self.tab_params else 1  # Default=Planen
        mapping = {
            0: OpType.PROGRAM_HEADER,  # Programmkopf
            1: OpType.FACE,
            2: OpType.CONTOUR,
            3: OpType.ABSPANEN,
            4: OpType.THREAD,
            5: OpType.GROOVE,
            6: OpType.DRILL,
            7: OpType.KEYWAY,
        }
        return mapping.get(idx, OpType.FACE)


    def _widget_get_value(self, widget):
        """Best-effort value extraction for common Qt widgets used in LatheEasyStep."""
        if widget is None:
            return None
        try:
            # Spin boxes
            if hasattr(widget, "value"):
                return widget.value()
            # Line edits
            if hasattr(widget, "text"):
                t = (widget.text() or "").strip()
                if t == "":
                    return None
                try:
                    return float(t.replace(",", "."))
                except Exception:
                    return None
        except Exception:
            return None
        return None

    def _widget_set_value(self, widget, value):
        """Best-effort value setter for common Qt widgets used in LatheEasyStep."""
        if widget is None or value is None:
            return
        try:
            if hasattr(widget, "setValue"):
                widget.setValue(value)
                return
            if hasattr(widget, "setText"):
                widget.setText(str(value))
                return
        except Exception:
            return

    def _collect_params(self, op_type: str) -> Dict[str, object]:
        widgets = self.param_widgets.get(op_type, {})
        params: Dict[str, object] = {}
        for key, widget in widgets.items():
            if widget is None:
                continue
            try:
                if isinstance(widget, QtWidgets.QSpinBox):
                    params[key] = float(widget.value())
                elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                    params[key] = float(widget.value())
                elif isinstance(widget, QtWidgets.QComboBox):
                    if key == "slice_strategy":
                        idx = widget.currentIndex()
                        data = widget.itemData(idx, QtCore.Qt.UserRole)
                        if isinstance(data, (int, float)):
                            params[key] = int(float(data))
                        else:
                            params[key] = idx + 1
                    else:
                        data = widget.currentData()
                        if data is not None:
                            params[key] = data
                        else:
                            params[key] = float(widget.currentIndex())
                elif isinstance(widget, QtWidgets.QLineEdit):
                    text = widget.text().strip()
                    if text == "":
                        continue
                    # try float, else keep as string
                    try:
                        params[key] = float(text.replace(",", "."))
                    except Exception:
                        params[key] = text
                elif isinstance(widget, QtWidgets.QAbstractButton):
                    params[key] = float(widget.isChecked())
                else:
                    # Fallback: only record if we can safely read something
                    if hasattr(widget, "value"):
                        params[key] = float(widget.value())
                    elif hasattr(widget, "text"):
                        text = str(widget.text()).strip()
                        if text != "":
                            params[key] = text
            except Exception:
                # Never let a broken widget mapping wipe the whole params dict
                continue
        # Kontur-Segmente separat aus Tabelle einsammeln
        if op_type == OpType.CONTOUR:
            params["segments"] = self._collect_contour_segments()
            if getattr(self, "contour_name", None):
                name = self.contour_name.text().strip()
                if not name:
                    name = self._fallback_contour_name(self._contour_count())
                    # UI optional anreichern, damit Nutzer den vergebenen Namen sieht
                    try:
                        self.contour_name.setText(name)
                    except Exception:
                        pass
                params["name"] = name
        elif op_type == OpType.ABSPANEN:
            contour_name = self._current_parting_contour_name()
            params["contour_name"] = contour_name
            params["source_path"] = self._resolve_contour_path(contour_name)
        elif op_type == OpType.FACE:
            # Defaults für FACE, da slicer.py keine harten Defaults hat
            defaults = {
                "retract": 0.5,
                "depth_max": 0.4,
                "feed": 0.2,
                "spindle": 1300.0,
                "tool": 1,
                "mode": 0,
                "edge_type": 0,
                "edge_size": 0.0,
                "finish_allow_z": 0.05,
                "start_x": 40.0,
                "start_z": 1.0,
                "end_x": -1.0,
                "end_z": 0.0,
                "coolant": False,
            }
            for key, default in defaults.items():
                if key not in params or params[key] is None or params[key] == "":
                    params[key] = default
        return params
    def _collect_program_header(self) -> Dict[str, object]:
        """Sammelt alle Programmkopf-Parameter für Kommentare/G-Code."""
        # Fehlende Widgets nachladen, falls sie zum Zeitpunkt der Initialisierung
        # noch nicht gefunden wurden (z. B. wegen verzögertem UI-Aufbau).
        if self.program_npv is None:
            self.program_npv = self._get_widget_by_name("program_npv")
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()
        if self.program_shape is None:
            self.program_shape = self._find_shape_combo()
        if self.program_retract_mode is None:
            self.program_retract_mode = self._get_widget_by_name("program_retract_mode")
        if self.program_s1 is None:
            self.program_s1 = self._get_widget_by_name("program_s1")
        if self.program_s3 is None:
            self.program_s3 = self._get_widget_by_name("program_s3")
        if self.program_has_subspindle is None:
            self.program_has_subspindle = self._get_widget_by_name("program_has_subspindle")
        if self.program_xt is None:
            self.program_xt = self._get_widget_by_name("program_xt")
        if self.program_zt is None:
            self.program_zt = self._get_widget_by_name("program_zt")
        if self.program_sc is None:
            self.program_sc = self._get_widget_by_name("program_sc")
        if self.program_name is None:
            self.program_name = self._get_widget_by_name("program_name")
        if self.program_xa is None:
            self.program_xa = self._get_widget_by_name("program_xa")
        if self.program_xi is None:
            self.program_xi = self._get_widget_by_name("program_xi")
        if self.program_za is None:
            self.program_za = self._get_widget_by_name("program_za")
        if self.program_zi is None:
            self.program_zi = self._get_widget_by_name("program_zi")
        if self.program_zb is None:
            self.program_zb = self._get_widget_by_name("program_zb")
        if self.program_w is None:
            self.program_w = self._get_widget_by_name("program_w")
        if self.program_l is None:
            self.program_l = self._get_widget_by_name("program_l")
        if self.program_n is None:
            self.program_n = self._get_widget_by_name("program_n")
        if self.program_sw is None:
            self.program_sw = self._get_widget_by_name("program_sw")
        if self.program_xra is None:
            self.program_xra = self._get_widget_by_name("program_xra")
        if self.program_xri is None:
            self.program_xri = self._get_widget_by_name("program_xri")
        if self.program_zra is None:
            self.program_zra = self._get_widget_by_name("program_zra")
        if self.program_zri is None:
            self.program_zri = self._get_widget_by_name("program_zri")
        if self.program_xra_absolute is None:
            self.program_xra_absolute = self._get_widget_by_name("program_xra_absolute")
        if self.program_xri_absolute is None:
            self.program_xri_absolute = self._get_widget_by_name("program_xri_absolute")
        if self.program_zra_absolute is None:
            self.program_zra_absolute = self._get_widget_by_name("program_zra_absolute")
        if self.program_zri_absolute is None:
            self.program_zri_absolute = self._get_widget_by_name("program_zri_absolute")

        header: Dict[str, object] = {}
        if self.program_npv:
            header["npv"] = self.program_npv.currentText().strip()
        if self.program_unit:
            header["unit"] = self.program_unit.currentText().strip()
        if self.program_shape:
            header["shape"] = self.program_shape.currentText().strip()

        def _val(widget):
            if widget is None:
                return None
            if hasattr(widget, "value") and callable(getattr(widget, "value")):
                try:
                    return float(widget.value())
                except Exception:
                    return None
            if hasattr(widget, "text") and callable(getattr(widget, "text")):
                t = widget.text().strip()
                if not t:
                    return None
                try:
                    return float(t.replace(",", "."))
                except Exception:
                    return None
            return None

        # Rohteilabmessungen / Spannmaße
        header["xa"] = _val(self.program_xa)
        header["xi"] = _val(self.program_xi)
        header["za"] = _val(self.program_za)
        header["zi"] = _val(self.program_zi)
        header["zb"] = _val(self.program_zb)
        header["w"] = _val(self.program_w)
        header["l"] = _val(self.program_l)
        header["n_edges"] = _val(self.program_n)
        header["sw"] = _val(self.program_sw)

        # Rückzug/Ebenen
        header["retract_mode"] = (
            self.program_retract_mode.currentText().strip()
            if self.program_retract_mode
            else ""
        )
        header["xra"] = _val(self.program_xra)
        header["xri"] = _val(self.program_xri)
        header["zra"] = _val(self.program_zra)
        header["zri"] = _val(self.program_zri)

        # Absolute vs incremental flags for the retract/tool positions. If the
        # checkbox widget is missing, default to False (incremental) as per
        # new default UX (user prefers entering incremental deltas).
        header["xra_absolute"] = bool(self.program_xra_absolute.isChecked()) if self.program_xra_absolute else False
        header["xri_absolute"] = bool(self.program_xri_absolute.isChecked()) if self.program_xri_absolute else False
        header["zra_absolute"] = bool(self.program_zra_absolute.isChecked()) if self.program_zra_absolute else False
        header["zri_absolute"] = bool(self.program_zri_absolute.isChecked()) if self.program_zri_absolute else False
        header["xt_absolute"] = bool(self.program_xt_absolute.isChecked()) if self.program_xt_absolute else False
        header["zt_absolute"] = bool(self.program_zt_absolute.isChecked()) if self.program_zt_absolute else False

        # Werkzeugwechsel-/Sicherheitspositionen
        header["xt"] = _val(self.program_xt)
        header["zt"] = _val(self.program_zt)
        header["sc"] = _val(self.program_sc)

        if self.program_name:
            header["program_name"] = self.program_name.text().strip()

        # Drehzahlbegrenzung (S3 nur, wenn Gegenspindel aktiv)
        header["has_subspindle"] = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
        header["s1_max"] = float(self.program_s1.value()) if self.program_s1 else 0.0
        if header["has_subspindle"]:
            header["s3_max"] = float(self.program_s3.value()) if self.program_s3 else 0.0
        else:
            header["s3_max"] = 0.0

        return header

    def _tool_change_position_lines(self, header: Dict[str, object]) -> List[str]:
        """Generiert G-Code zum Anfahren der Werkzeugwechselposition (XT/ZT).
        
        Berücksichtigt absolute/inkrementale Flags:
        - absolute: WCS (Normal Peek Value) verwenden
        - inkremental: Maschinenkoordinaten (G53) verwenden
        """
        xt = float(header.get("xt", 0.0))
        zt = float(header.get("zt", 0.0))
        xt_abs = bool(header.get("xt_absolute", False))
        zt_abs = bool(header.get("zt_absolute", False))

        lines: List[str] = []
        
        # Wenn beide absolut: komplett im WCS
        if xt_abs and zt_abs:
            lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
            return lines
        
        # Wenn beide inkremental: G53 verwenden
        if not xt_abs and not zt_abs:
            lines.append(f"G53 G0 X{xt:.3f} Z{zt:.3f}")
            return lines
        
        # Mischfall: X absolut, Z inkremental (oder umgekehrt)
        # Erst G53 für inkrementale Achsen
        g53_parts = []
        if not xt_abs:
            g53_parts.append(f"X{xt:.3f}")
        if not zt_abs:
            g53_parts.append(f"Z{zt:.3f}")
        if g53_parts:
            lines.append(f"G53 G0 {' '.join(g53_parts)}")
        
        # Dann WCS für absolute Achsen
        wcs_parts = []
        if xt_abs:
            wcs_parts.append(f"X{xt:.3f}")
        if zt_abs:
            wcs_parts.append(f"Z{zt:.3f}")
        if wcs_parts:
            lines.append(f"G0 {' '.join(wcs_parts)}")
        
        return lines

    def _collect_contour_segments(self) -> List[Dict[str, object]]:
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

            mode_raw = mode_item.text().strip().lower() if mode_item else "xz"
            if mode_raw.startswith("xz"):
                mode = "xz"
            elif mode_raw.startswith("x"):
                mode = "x"
            elif mode_raw.startswith("z"):
                mode = "z"
            else:
                mode = "xz"

            # Edge type text (German/English): prefer combo widget if present
            edge_txt = ""
            try:
                if edge_widget is not None and hasattr(edge_widget, "currentText"):
                    edge_txt = str(edge_widget.currentText()).strip().lower()
                elif edge_item is not None and edge_item.text():
                    edge_txt = edge_item.text().strip().lower()
            except Exception:
                edge_txt = ""
            if not edge_txt:
                edge_txt = "keine"
            
            # Accept common German/English labels
            if edge_txt.startswith(("f", "c")):  # Fase / Chamfer
                edge = "chamfer"
            elif edge_txt.startswith(("r", "ra")):  # Radius
                edge = "radius"
            else:
                edge = "none"
            

            # Bogen-Seite (Auto/Außen/Innen) – nur relevant bei Radius
            arc_txt = ""
            try:
                if arc_side_widget is not None and hasattr(arc_side_widget, "currentText"):
                    arc_txt = str(arc_side_widget.currentText()).strip().lower()
                elif arc_side_item is not None and arc_side_item.text():
                    arc_txt = arc_side_item.text().strip().lower()
            except Exception:
                arc_txt = ""

            arc_side = normalize_arc_side(arc_txt)

            def _to_float(item):
                try:
                    txt = item.text().replace(",", ".")
                    return float(txt)
                except Exception:
                    return 0.0

            x_text = x_item.text().strip() if x_item and x_item.text() else ""
            z_text = z_item.text().strip() if z_item and z_item.text() else ""

            segments.append(
                {
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
            )

        return segments

    def _write_contour_row(self, row: int, edge_text: str | None = None, edge_size: float | None = None, arc_text: str | None = None):
        """Schreibt Kante/Maß in die aktuelle Tabellenzeile und hält Typ/X/Z unberührt."""
        table = self.contour_segments
        if table is None or row < 0 or row >= table.rowCount():
            return
        item_cls = QtWidgets.QTableWidgetItem
        if edge_text is not None:
                    w_edge = table.cellWidget(row, 3)
                    if w_edge is None or not hasattr(w_edge, 'findText'):
                        # fallback: plain item text
                        table.setItem(row, 3, item_cls(str(edge_text)))
                    else:
                        idx = w_edge.findText(str(edge_text))
                        if idx >= 0:
                            w_edge.setCurrentIndex(idx)
        
                    # Radius size in Spalte 4
                    if edge_size is not None:
                        table.setItem(row, 4, item_cls(f"{float(edge_size):.3f}"))
        # Arc dropdown in Spalte 5 (wenn vorhanden)
        try:
            w = table.cellWidget(row, 5)
            if w is not None and hasattr(w, "setEnabled"):
                # nur aktiv bei Radius
                edge_now = (edge_text if edge_text is not None else (table.item(row, 3).text() if table.item(row,3) else ""))
                w.setEnabled(str(edge_now).lower().startswith("r"))
                if arc_text is not None and hasattr(w, "findText"):
                    idx = w.findText(arc_text, QtCore.Qt.MatchFixedString)
                    if idx >= 0:
                        w.setCurrentIndex(idx)
        except Exception:
            pass

    def _load_params_to_form(self, op: Operation):
        if op.op_type == OpType.PROGRAM_HEADER:
            self._load_program_header_to_form(op.params)
            return
        widgets = self.param_widgets.get(op.op_type, {})
        for key, widget in widgets.items():
            if widget is None or key not in op.params:
                continue
            widget.blockSignals(True)
            val = op.params[key]
            if isinstance(widget, QtWidgets.QComboBox):
                handled = False
                if key == "slice_strategy":
                    handled = self._select_slice_strategy_index(widget, val)
                if not handled:
                    try:
                        widget.setCurrentIndex(int(val))
                    except Exception:
                        try:
                            txt = str(val).strip()
                            idx = widget.findText(txt)
                            if idx >= 0:
                                widget.setCurrentIndex(idx)
                        except Exception:
                            pass
            elif isinstance(widget, QtWidgets.QAbstractButton):
                widget.setChecked(bool(val))
            else:
                try:
                    if isinstance(widget, QtWidgets.QSpinBox):
                        widget.setValue(int(val))
                    else:
                        widget.setValue(val)
                except Exception:
                    try:
                        widget.setValue(float(val))
                    except Exception:
                        pass
            widget.blockSignals(False)

        if op.op_type == OpType.CONTOUR:
            self._ensure_contour_widgets()
            self._init_contour_table()

            if getattr(self, "contour_name", None):
                try:
                    self.contour_name.blockSignals(True)
                    self.contour_name.setText(str(op.params.get("name") or "").strip())
                finally:
                    self.contour_name.blockSignals(False)

            table = getattr(self, "contour_segments", None)
            if table is not None:
                segs = op.params.get("segments") or []
                table.blockSignals(True)
                table.setRowCount(0)

                def _mode_to_text(m: str) -> str:
                    m = (m or "xz").lower()
                    if m == "x":
                        return "X"
                    if m == "z":
                        return "Z"
                    return "XZ"

                def _edge_to_text(e: str) -> str:
                    e = (e or "none").lower()
                    if e in ("chamfer", "fase"):
                        return "Fase"
                    if e == "radius":
                        return "Radius"
                    return "Keine"

                for r, seg in enumerate(segs):
                    table.insertRow(r)
                    mode_txt = _mode_to_text(seg.get("mode"))
                    x_empty = bool(seg.get("x_empty", False))
                    z_empty = bool(seg.get("z_empty", False))
                    x_val = "" if x_empty else f"{float(seg.get('x', 0.0)):.3f}"
                    z_val = "" if z_empty else f"{float(seg.get('z', 0.0)):.3f}"
                    edge_txt = _edge_to_text(seg.get("edge"))
                    size_val = f"{float(seg.get('edge_size', 0.0) or 0.0):.3f}"

                    def _mk(text: str) -> QtWidgets.QTableWidgetItem:
                        it = QtWidgets.QTableWidgetItem(text)
                        try:
                            it.setFlags(
                                QtCore.Qt.ItemIsSelectable
                                | QtCore.Qt.ItemIsEnabled
                                | QtCore.Qt.ItemIsEditable
                            )
                        except Exception:
                            pass
                        return it

                    table.setItem(r, 0, _mk(mode_txt))
                    table.setItem(r, 1, _mk(x_val))
                    table.setItem(r, 2, _mk(z_val))
                    table.setItem(r, 3, _mk(edge_txt))
                    table.setItem(r, 4, _mk(size_val))

                table.blockSignals(False)
                if table.rowCount() > 0:
                    table.setCurrentCell(0, 0)

            self._contour_row_user_selected = False
            self._sync_contour_edge_controls()
            self._update_contour_preview_temp()
            self._update_parting_contour_choices()
            self._update_parting_ready_state()
            return

        if op.op_type == OpType.ABSPANEN and getattr(self, "parting_contour", None):
            name = str(op.params.get("contour_name") or "")
            self.parting_contour.blockSignals(True)
            self.parting_contour.setCurrentText(name)
            self.parting_contour.blockSignals(False)
            self._update_parting_ready_state()
            self._update_parting_mode_visibility()

    def _load_program_header_to_form(self, params: Dict[str, object]):
        if not isinstance(params, dict):
            return
        self._collect_program_header()

        def _set_combo(widget, value):
            if widget is None or value is None:
                return
            try:
                idx = widget.findText(str(value))
            except Exception:
                return
            if idx >= 0:
                widget.blockSignals(True)
                widget.setCurrentIndex(idx)
                widget.blockSignals(False)

        def _set_value(widget, value):
            if widget is None or value is None:
                return
            widget.blockSignals(True)
            try:
                if isinstance(widget, QtWidgets.QSpinBox):
                    widget.setValue(int(float(value)))
                else:
                    widget.setValue(float(value))
            except Exception:
                try:
                    widget.setValue(float(value))
                except Exception:
                    pass
            finally:
                widget.blockSignals(False)

        _set_combo(self.program_npv, params.get("npv"))
        _set_combo(self.program_unit, params.get("unit"))
        _set_combo(self.program_shape, params.get("shape"))
        _set_combo(self.program_retract_mode, params.get("retract_mode"))

        _set_value(self.program_xa, params.get("xa"))
        _set_value(self.program_xi, params.get("xi"))
        _set_value(self.program_za, params.get("za"))
        _set_value(self.program_zi, params.get("zi"))
        _set_value(self.program_zb, params.get("zb"))
        _set_value(self.program_xra, params.get("xra"))
        _set_value(self.program_xri, params.get("xri"))
        _set_value(self.program_zra, params.get("zra"))
        _set_value(self.program_zri, params.get("zri"))

        # Retract absolute/incremental flags
        if self.program_xra_absolute is not None:
            self.program_xra_absolute.blockSignals(True)
            self.program_xra_absolute.setChecked(bool(params.get("xra_absolute")))
            self.program_xra_absolute.blockSignals(False)
        if self.program_xri_absolute is not None:
            self.program_xri_absolute.blockSignals(True)
            self.program_xri_absolute.setChecked(bool(params.get("xri_absolute")))
            self.program_xri_absolute.blockSignals(False)
        if self.program_zra_absolute is not None:
            self.program_zra_absolute.blockSignals(True)
            self.program_zra_absolute.setChecked(bool(params.get("zra_absolute")))
            self.program_zra_absolute.blockSignals(False)
        if self.program_zri_absolute is not None:
            self.program_zri_absolute.blockSignals(True)
            self.program_zri_absolute.setChecked(bool(params.get("zri_absolute")))
            self.program_zri_absolute.blockSignals(False)

        _set_value(self.program_w, params.get("w"))
        _set_value(self.program_xt, params.get("xt"))
        _set_value(self.program_zt, params.get("zt"))
        _set_value(self.program_sc, params.get("sc"))
        _set_value(self.program_s1, params.get("s1"))
        _set_value(self.program_s3, params.get("s3"))

        if self.program_has_subspindle is not None:
            self.program_has_subspindle.blockSignals(True)
            self.program_has_subspindle.setChecked(bool(params.get("has_subspindle")))
            self.program_has_subspindle.blockSignals(False)

        if self.program_name is not None:
            self.program_name.blockSignals(True)
            self.program_name.setText(str(params.get("program_name") or ""))
            self.program_name.blockSignals(False)

        self._apply_unit_suffix()
        self._update_program_visibility()
        self._update_retract_visibility()
        self._update_subspindle_visibility()

    def _set_preview_paths(
        self,
        paths: List[List[Tuple[float, float]]],
        active_index: int | None = None,
        include_contour_preview: bool = True,
    ) -> None:
        """Aktualisiert Haupt- und optional den Kontur-Tab-Preview.

        Achtung: Je nach LinuxCNC/QTvcp-Version gibt es unterschiedliche
        Signaturen von LathePreviewWidget.set_paths().
        """

        self._ensure_preview_widgets()

        # main preview
        if self.preview:
            try:
                # Newer signature: set_paths(paths, active_index=None)
                # Collision check against worklimit (Bearbeitungsmaß in Z)
                collision = False
                try:
                    zb = None
                    for prim_list in paths:
                        for pr in prim_list:
                            if pr.get("role") == "worklimit" and pr.get("type") == "line":
                                # vertical line: p1=(x,z) p2=(x,z)
                                zb = float(pr.get("p1", (0.0, 0.0))[1])
                                break
                        if zb is not None:
                            break
                    if zb is not None:
                        min_z = None
                        for prim_list in paths:
                            for pr in prim_list:
                                role = pr.get("role")
                                if role in ("stock", "retract", "worklimit"):
                                    continue
                                t = pr.get("type")
                                if t == "polyline":
                                    for x, z in pr.get("points", []):
                                        if min_z is None or z < min_z:
                                            min_z = z
                                elif t == "line":
                                    for x, z in (pr.get("p1"), pr.get("p2")):
                                        if min_z is None or z < min_z:
                                            min_z = z
                        if min_z is not None and min_z < zb - 1e-6:
                            collision = True
                except Exception:
                    collision = False
                if hasattr(self.preview, "set_collision"):
                    self.preview.set_collision(collision)
                self.preview.set_paths(paths, active_index)
            except TypeError:
                # Older signature: set_paths(paths)
                self.preview.set_paths(paths)

        # slice preview (if enabled)
        if self.preview_slice and getattr(self.preview_slice, "isVisible", lambda: False)():
            try:
                self.preview_slice.set_view_mode("slice")
            except Exception:
                pass
            try:
                if self.preview:
                    self.preview_slice.set_slice_z(getattr(self.preview, "slice_z", 0.0))
                else:
                    self.preview_slice.set_slice_z(0.0)
            except Exception:
                pass
            try:
                self.preview_slice.set_paths(paths, active_index)
            except TypeError:
                self.preview_slice.set_paths(paths)
        # contour preview tab (if present)
        if include_contour_preview and self.contour_preview:
            try:
                self.contour_preview.set_paths(paths, active_index)
            except TypeError:
                self.contour_preview.set_paths(paths)

    def _refresh_preview(self):
        # PATCH: allow preview to work even if only contourPreview exists.
        if self.preview is None or self.contour_preview is None:
            self._ensure_preview_widgets()
        if self.preview is None and self.contour_preview is None:
            return
        paths: List[List[Tuple[float, float]]] = []

        # Kontur-Eingabe immer mitzeigen, wenn wir auf dem Kontur-Tab sind oder keine Ops existieren
        if self.contour_start_x or self.contour_segments:
            params: Dict[str, object] = {
                "start_x": self.contour_start_x.value() if self.contour_start_x else 0.0,
                "start_z": self.contour_start_z.value() if self.contour_start_z else 0.0,
                "coord_mode": self.contour_coord_mode.currentIndex() if getattr(self, "contour_coord_mode", None) else 0,
                "segments": self._collect_contour_segments(),
            }
            paths.append(build_contour_path(params))

        # vorhandene Operationen hinzufügen
        if self.model.operations:
            paths.extend([op.path for op in self.model.operations if op.path])
            active = self.list_ops.currentRow() if self.list_ops else -1
        else:
            active = -1

        # Raw stock outline + retract planes as thin references (program header only).
        prog = self._collect_program_header() or {}
        try:
            inserts = 0
            stock_primitives = build_stock_outline(prog)
            if stock_primitives:
                paths.insert(0, stock_primitives)
                inserts += 1

            retract_primitives = build_retract_primitives(prog)
            if retract_primitives:
                # keep retract just above stock in drawing order
                paths.insert(inserts, retract_primitives)
                inserts += 1


            # workpiece stick-out / chuck collision limit (Bearbeitungsmaß)
            worklimit_primitives = build_worklimit_primitives(prog, stock_primitives or [])
            if worklimit_primitives:
                paths.insert(inserts, worklimit_primitives)
                inserts += 1

            if active is not None and active >= 0 and inserts:
                active += inserts
        except Exception as exc:
            print("[LatheEasyStep] stock/retract preview ERROR:", exc)

        # falls gar nichts vorhanden, leere Liste übergeben -> Achsenkreuz
        self._set_preview_paths(paths, active, include_contour_preview=True)

    def _refresh_operation_list(self, select_index: int | None = None):
        """Synchronisiert die linke Operationsliste mit dem internen Modell."""
        root = self.root_widget or self._find_root_widget()

        # Alle ListWidgets einsammeln, die potentiell die Operationsliste darstellen.
        list_widgets: list[QtWidgets.QListWidget] = []
        if self.list_ops:
            list_widgets.append(self.list_ops)
        if root:
            for w in root.findChildren(QtWidgets.QListWidget):
                if w not in list_widgets:
                    list_widgets.append(w)

        if not list_widgets:
            self._update_parting_contour_choices()
            return

        # Für alle gefundenen Listen identisch updaten.
        for lst in list_widgets:
            current = lst.currentRow()
            lst.blockSignals(True)
            self._op_row_user_selected = False
            lst.clear()
            for i, op in enumerate(self.model.operations):
                lst.addItem(self._describe_operation(op, i + 1))

            if select_index is None:
                target_idx = current
            else:
                target_idx = select_index
            if target_idx is None:
                target_idx = -1

            if 0 <= target_idx < lst.count():
                lst.setCurrentRow(target_idx)
            elif lst.count() > 0:
                lst.setCurrentRow(lst.count() - 1)
            lst.blockSignals(False)
            try:
                items = [lst.item(i).text() for i in range(lst.count())]
                print(
                    f"[LatheEasyStep][debug] list '{lst.objectName()}' "
                    f"count={lst.count()} items={items} vis={lst.isVisible()} "
                    f"size={lst.size()}"
                )
                # Sichtbarkeit erzwingen – eigener Style gegen dunkle QSS
                lst.setStyleSheet(
                    "QListWidget { background: #f5f5f5; color: #000000; }"
                    "QListWidget::item:selected { background: #4fa3f7; color: #ffffff; }"
                )
                lst.show()
                lst.raise_()
                lst.setMinimumWidth(220)
            except Exception:
                pass
            try:
                lst.repaint()
                lst.update()
                lst.scrollToBottom()
            except Exception:
                pass

        # list_ops-Referenz auf das erste (sichtbare) ListWidget setzen, falls bisher None
        if self.list_ops is None and list_widgets:
            self.list_ops = list_widgets[0]
        self._update_parting_contour_choices()

    def _ensure_preview_widgets(self):
        """Versucht fehlende Preview-Widget-Referenzen aus dem UI zu holen.

        Wichtig: In QTvcp/QtDesigner kann ein Widget zwar als "previewWidget" existieren,
        aber (durch Promotion/Loader) nicht als exakt dieselbe Python-Klasse erkannt werden.
        Deshalb suchen wir zuerst typbasiert und fallen dann auf Objektname+Methoden ab.
        """
        root = self.root_widget or self._find_root_widget()
        if not root:
            return

        def _accept_as_preview(w):
            return w is not None and (hasattr(w, "set_primitives") or hasattr(w, "set_paths"))

        # 1) Primär: typbasiert (wenn die Klasse wirklich identisch ist)
        if self.preview is None:
            w = root.findChild(LathePreviewWidget, "previewWidget")
            if _accept_as_preview(w):
                self.preview = w
        if self.contour_preview is None:
            w = root.findChild(LathePreviewWidget, "contourPreview")
            if _accept_as_preview(w):
                self.contour_preview = w

        # 2) Fallback: nur nach Objektname (wenn Klassentyp nicht matcht)
        if self.preview is None:
            w = root.findChild(QtWidgets.QWidget, "previewWidget")
            if _accept_as_preview(w):
                self.preview = w
        if self.contour_preview is None:
            w = root.findChild(QtWidgets.QWidget, "contourPreview")
            if _accept_as_preview(w):
                self.contour_preview = w

        # Keine automatische "reuse contourPreview"-Logik mehr:
        # Das hat in manchen UIs die Planen-Vorschau unsichtbar gemacht (anderer Tab).
    def _mark_operation_user_selected(self, *args, **kwargs):
        self._op_row_user_selected = True

    def _update_selected_operation(self, *, force: bool = False):
        if self.list_ops is None:
            return
        if not force and not self._op_row_user_selected:
            return
        idx = self.list_ops.currentRow()
        if idx < 0 or idx >= len(self.model.operations):
            return
        op = self.model.operations[idx]
        if op.op_type == OpType.PROGRAM_HEADER:
            op.params = self._collect_program_header()
        else:
            op.params = self._collect_params(op.op_type)
        self.model.update_geometry(op)
        description = self._describe_operation(op, idx + 1)
        if self.list_ops:
            item = self.list_ops.item(idx)
            if item:
                item.setText(description)
        op.params["comment"] = description
        self._refresh_preview()
        if op.op_type == OpType.CONTOUR:
            self._update_parting_contour_choices()

    # ---- Button-Handler -----------------------------------------------
    def _handle_add_operation(self):
        # Sicherheitsnetz: Widgets nachziehen, falls sie erst später verfügbar sind
        self._ensure_core_widgets()
        self._force_attach_core_widgets()
        # Schutz gegen doppelte Auslösung (UI kann Click-Events doppelt feuern)
        if getattr(self, "_adding_operation", False):
            return
        now = time.monotonic()
        last = getattr(self, "_last_add_operation_ts", 0.0)
        if now - last < 0.8:
            return
        self._last_add_operation_ts = now
        self._adding_operation = True
        try:
            try:
                print("[LatheEasyStep] add operation triggered")
            except Exception:
                pass
            op_type = self._current_op_type()
            if op_type == OpType.PROGRAM_HEADER:
                params = self._collect_program_header()
                # nur einen Programmkopf zulassen -> ersetzen oder neu hinzufügen
                for i, existing in enumerate(self.model.operations):
                    if existing.op_type == OpType.PROGRAM_HEADER:
                        existing.params = params
                        if self.list_ops:
                            item = self.list_ops.item(i)
                            if item:
                                item.setText(self._describe_operation(existing, i + 1))
                            self.list_ops.setCurrentRow(i)
                        self._refresh_preview()
                        return
                # noch kein Programmkopf: vorne einfügen
                op = Operation(op_type, params)
                self.model.update_geometry(op)
                self.model.operations.insert(0, op)
                self._refresh_operation_list(select_index=0)
                self._refresh_preview()
            else:
                params = self._collect_params(op_type)
                if op_type == OpType.ABSPANEN:
                    contour_name = self._current_parting_contour_name()
                    contour_path = self._resolve_contour_path(contour_name)
                    if not contour_name or not contour_path:
                        print("[LatheEasyStep] Abspanen benötigt eine vorhandene Kontur-Auswahl")
                        self._update_parting_ready_state()
                        return
                    params["contour_name"] = contour_name
                    params["source_path"] = contour_path
                op = Operation(op_type, params)
                self.model.update_geometry(op)
                self.model.add_operation(op)
                try:
                    debug_ops = [f"{i}:{o.op_type}" for i, o in enumerate(self.model.operations)]
                    print(f"[LatheEasyStep][debug] operations now: {debug_ops}")
                except Exception:
                    pass

                self._refresh_operation_list(select_index=len(self.model.operations) - 1)
                self._refresh_preview()
                # Abspan-Auswahl sofort auffrischen, damit neue Konturen unmittelbar
                # auswählbar sind.
                self._update_parting_contour_choices()
                self._update_parting_ready_state()
        finally:
            self._adding_operation = False

    def _handle_delete_operation(self):
        if self._deleting:
            return
        self._deleting = True
        try:
            if self.list_ops is None:
                return
            idx = self.list_ops.currentRow()
            if idx < 0:
                return
            if idx == 0:
                parent = self.root_widget or self._find_root_widget()
                QtWidgets.QMessageBox.warning(parent, "Löschen", "Der Programmkopf kann nicht gelöscht werden.")
                return
            self.model.remove_operation(idx)
            self._refresh_operation_list(select_index=min(idx, len(self.model.operations) - 1))
            self._refresh_preview()
            self._update_parting_contour_choices()
        finally:
            self._deleting = False

    def _selected_operation_index(self) -> int:
        if self.list_ops is None:
            return -1
        idx = self.list_ops.currentRow()
        if 0 <= idx < len(self.model.operations):
            return idx
        return -1

    def _operation_to_step_data(self, op: Operation) -> Dict[str, object]:
        data = {
            "op_type": op.op_type,
            "params": op.params,
        }
        # Support both legacy point paths and new primitive paths
        if op.path and isinstance(op.path[0], dict):
            data["primitives"] = op.path
        else:
            data["path"] = [[float(x), float(z)] for x, z in (op.path or [])]
        return data

    def _step_data_to_operation(self, data: Dict[str, object]) -> Operation | None:
        if not isinstance(data, dict):
            return None
        op_type = str(data.get("op_type") or OpType.FACE)
        params_raw = data.get("params") or {}
        if not isinstance(params_raw, dict):
            params_raw = {}
        params = {str(key): value for key, value in params_raw.items()}        # New format: prefer primitives (arc/line) over sampled points
        if isinstance(data.get("primitives"), list) and data.get("primitives"):
            prim = data.get("primitives") or []
            return Operation(op_type, params, list(prim))

        # Legacy format: point list
        path_data = data.get("path") or []
        path: List[Tuple[float, float]] = []
        for entry in path_data:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                try:
                    x = float(entry[0])
                    z = float(entry[1])
                except Exception:
                    continue
                path.append((x, z))
        return Operation(op_type, params, path)

    def _insert_loaded_operation(self, op: Operation):
        self.model.update_geometry(op)
        self.model.add_operation(op)
        idx = len(self.model.operations) - 1
        self._refresh_operation_list(select_index=idx)
        if self.list_ops:
            try:
                self.list_ops.setCurrentRow(idx)
            except Exception:
                pass
        self._refresh_preview()
        self._update_parting_contour_choices()
        self._handle_selection_change(idx)

    def _handle_save_step(self):
        if self._saving_step:
            return
        self._saving_step = True
        try:
            idx = self._selected_operation_index()
            if idx < 0:
                parent = self.root_widget or self._find_root_widget()
                QtWidgets.QMessageBox.warning(parent, "Step speichern", "Bitte zuerst eine Operation auswählen.")
                return
            parent = self.root_widget or self._find_root_widget()
            start_dir = self._step_last_dir or QtCore.QDir.homePath()
            default_name = os.path.join(start_dir, "lathe_step.step.json")
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent,
                "Step speichern",
                default_name,
                STEP_FILE_FILTER,
            )
            if not file_path:
                return
            if not file_path.lower().endswith(".step.json"):
                file_path += ".step.json"
            try:
                self._update_selected_operation(force=True)
                op = self.model.operations[idx]
                warning = self._tool_orientation_mismatch(op)
                if warning:
                    QtWidgets.QMessageBox.warning(parent, "Werkzeuglage prüfen", warning)
                data = self._operation_to_step_data(op)
                with builtins.open(file_path, "w", encoding="utf-8") as handle:
                    json.dump(data, handle, indent=2)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(parent, "Step speichern", f"Step konnte nicht gespeichert werden:\n{exc}")
                return
            self._step_last_dir = os.path.dirname(file_path)
            QtWidgets.QMessageBox.information(parent, "Step speichern", f"Step wurde nach '{file_path}' geschrieben.")
        finally:
            self._saving_step = False

    def _operation_side_hint(self, op: Operation) -> str | None:
        """Return 'outside' or 'inside' for operations that expose a side/orientation choice."""
        params = op.params or {}
        if op.op_type == OpType.FACE:
            try:
                idx = int(float(params.get("finish_direction", 0)))
            except Exception:
                idx = 0
            return "outside" if idx == 0 else "inside"
        if op.op_type == OpType.GROOVE:
            try:
                idx = int(float(params.get("lage", 0)))
            except Exception:
                idx = 0
            if idx == 0:
                return "outside"
            if idx == 1:
                return "inside"
        if op.op_type == OpType.ABSPANEN:
            try:
                idx = int(float(params.get("side", 0)))
            except Exception:
                idx = 0
            return "outside" if idx == 0 else "inside"
        if op.op_type == OpType.THREAD:
            try:
                idx = int(float(params.get("orientation", 0)))
            except Exception:
                idx = 0
            return "outside" if idx == 0 else "inside"
        return None

    def _tool_comment_side_hint(self, comment: str) -> str | None:
        if not comment:
            return None
        normalized = re.sub(r"[^a-z0-9]+", " ", comment.lower())
        words = normalized.split()
        inside_words = {"innen", "inside", "inner", "id"}
        outside_words = {"außen", "aussen", "outside", "outer", "od"}
        if any(word in inside_words for word in words):
            return "inside"
        if any(word in outside_words for word in words):
            return "outside"
        return None

    def _tool_orientation_mismatch(self, op: Operation) -> str | None:
        hint = self._operation_side_hint(op)
        if not hint:
            return None
        try:
            tool_num = int(float(op.params.get("tool", 0)))
        except Exception:
            tool_num = 0
        if tool_num <= 0:
            return None
        tool = self.tools.get(tool_num)
        if not tool:
            return None
        comment_hint = self._tool_comment_side_hint(tool.comment)
        if comment_hint and comment_hint != hint:
            detail = tool.comment or tool.iso_code or ""
            if detail:
                detail = f" ({detail})"
            return (
                f"Tool T{tool.toolno:02d} scheint für {comment_hint} zu sein"
                f", die Operation wirkt aber wie {hint}{detail}."
            )
        return None

    def _collect_tool_orientation_warnings(self) -> List[str]:
        warnings: List[str] = []
        for idx, op in enumerate(self.model.operations):
            message = self._tool_orientation_mismatch(op)
            if message:
                warnings.append(f"Schritt {idx+1}: {message}")
        return warnings

    def _radius_warning_details(self) -> List[Dict[str, object]]:
        details: List[Dict[str, object]] = []
        for idx, op in enumerate(self.model.operations):
            if op.op_type != OpType.ABSPANEN:
                continue
            tool_value = op.params.get("tool")
            try:
                tool_num = int(float(tool_value)) if tool_value is not None else 0
            except Exception:
                tool_num = 0
            if tool_num <= 0:
                continue
            tool = self.tools.get(tool_num)
            radius = tool.radius_mm if tool else 0.0
            if radius <= 0.0:
                comment = tool.comment if tool and tool.comment else "kein Kommentar"
                message = (
                    f"Step {idx+1}: Tool T{tool_num:02d} ({comment}) hat keinen bekannten Radius → Kompensation (G41.1/G42.1) wird deaktiviert."
                )
                details.append(
                    {"idx": idx, "op": op, "tool_num": tool_num, "message": message}
                )
        return details

    def _handle_load_step(self):
        if self._loading_step:
            return
        self._loading_step = True
        try:
            parent = self.root_widget or self._find_root_widget()
            start_dir = self._step_last_dir or QtCore.QDir.homePath()
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent,
                "Step laden",
                start_dir,
                STEP_FILE_FILTER,
            )
            if not file_path:
                return
            try:
                with builtins.open(file_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(parent, "Step laden", f"Step konnte nicht geöffnet werden:\n{exc}")
                return

            op = self._step_data_to_operation(data)
            if op is None:
                QtWidgets.QMessageBox.warning(parent, "Step laden", "Die ausgewählte Datei enthält keinen gültigen Step.")
                return

            self._insert_loaded_operation(op)
            self._step_last_dir = os.path.dirname(file_path)
            self._update_parting_ready_state()

        
            # Einstich/Abstich-Tab: Lage/Bezugspunkt-Grafiken + Ein-/Ausblenden
            self._setup_groove_tab_ui()
        finally:
            self._loading_step = False

    def _handle_save_program(self):
        """Speichert das komplette Programm (Header + alle Operations) als JSON."""
        try:
            parent = self.root_widget or self._find_root_widget()
            default_dir = QtCore.QDir.homePath()
            
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                parent,
                "Programm speichern",
                default_dir,
                "LatheEasyStep Dateien (*.lse);;Alle Dateien (*)",
            )
            if not file_path:
                return
            
            # Ensure .lse extension
            if not file_path.lower().endswith(".lse"):
                file_path += ".lse"
            
            # Collect header
            header = self._collect_program_header()
            
            # Collect all operations as dicts
            ops_data = []
            for op in self.model.operations:
                op_dict = {
                    "op_type": op.op_type,
                    "params": dict(op.params),  # deepcopy dict
                    "path": op.path,  # may be empty or contain points/primitives
                    "title": op.params.get("title", ""),
                }
                ops_data.append(op_dict)
            
            # Build complete program structure
            program_data = {
                "version": 1,
                "header": header,
                "operations": ops_data,
            }
            
            # Write JSON
            with builtins.open(file_path, "w", encoding="utf-8") as f:
                json.dump(program_data, f, indent=2, default=str)
            
            QtWidgets.QMessageBox.information(
                parent,
                "Programm gespeichert",
                f"Programm gespeichert unter:\n{file_path}",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                parent or None,
                "Fehler beim Speichern",
                f"Programm konnte nicht gespeichert werden:\n{e}",
            )

    def _handle_load_program(self):
        """Lädt ein komplettes Programm (Header + Operations) aus JSON."""
        try:
            parent = self.root_widget or self._find_root_widget()
            default_dir = QtCore.QDir.homePath()
            
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent,
                "Programm laden",
                default_dir,
                "LatheEasyStep Dateien (*.lse);;Alle Dateien (*)",
            )
            if not file_path:
                return
            
            # Load JSON
            with builtins.open(file_path, "r", encoding="utf-8") as f:
                program_data = json.load(f)
            
            if program_data.get("version") != 1:
                QtWidgets.QMessageBox.warning(
                    parent,
                    "Programm laden",
                    "Ungültiges Dateiformat oder nicht unterstützte Version.",
                )
                return
            
            # Clear current operations
            self.model.operations.clear()
            self._op_row_user_selected = False
            
            # Load header values into UI
            header = program_data.get("header", {})
            self._apply_header_to_ui(header)
            
            # Load operations
            ops_data = program_data.get("operations", [])
            for op_dict in ops_data:
                op = Operation(
                    op_type=op_dict.get("op_type", ""),
                    params=dict(op_dict.get("params", {})),
                    path=op_dict.get("path", []),
                )
                self.model.add_operation(op)
            
            # Refresh UI
            self._refresh_operation_list(select_index=-1)
            self._refresh_preview()
            
            QtWidgets.QMessageBox.information(
                parent,
                "Programm geladen",
                f"Programm mit {len(ops_data)} Steps geladen.",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                parent or None,
                "Fehler beim Laden",
                f"Programm konnte nicht geladen werden:\n{e}",
            )

    def _apply_header_to_ui(self, header: Dict[str, object]):
        """Setzt Header-Werte in UI-Widgets."""
        def _set_widget_value(widget, value):
            if widget is None or value is None:
                return
            try:
                if hasattr(widget, "setValue") and isinstance(value, (int, float)):
                    widget.setValue(float(value))
                elif hasattr(widget, "setCurrentText") and isinstance(value, str):
                    widget.setCurrentText(str(value))
                elif hasattr(widget, "setChecked"):
                    widget.setChecked(bool(value))
            except Exception:
                pass
        
        # Apply header values
        _set_widget_value(self.program_xt, header.get("xt"))
        _set_widget_value(self.program_zt, header.get("zt"))
        _set_widget_value(self.program_name, header.get("program_name"))
        _set_widget_value(self.program_xa, header.get("xa"))
        _set_widget_value(self.program_xi, header.get("xi"))
        _set_widget_value(self.program_za, header.get("za"))
        _set_widget_value(self.program_zi, header.get("zi"))
        _set_widget_value(self.program_zb, header.get("zb"))
        _set_widget_value(self.program_xra, header.get("xra"))
        _set_widget_value(self.program_xri, header.get("xri"))
        _set_widget_value(self.program_zra, header.get("zra"))
        _set_widget_value(self.program_zri, header.get("zri"))
        _set_widget_value(self.program_sc, header.get("sc"))
        _set_widget_value(self.program_s1, header.get("s1_max"))
        _set_widget_value(self.program_s3, header.get("s3_max"))
        _set_widget_value(self.program_npv, header.get("npv"))
        _set_widget_value(self.program_unit, header.get("unit"))
        _set_widget_value(self.program_shape, header.get("shape"))
        _set_widget_value(self.program_retract_mode, header.get("retract_mode"))
        
        # Absolute flags
        if self.program_xt_absolute:
            self.program_xt_absolute.setChecked(bool(header.get("xt_absolute", False)))
        if self.program_zt_absolute:
            self.program_zt_absolute.setChecked(bool(header.get("zt_absolute", False)))
        if self.program_xra_absolute:
            self.program_xra_absolute.setChecked(bool(header.get("xra_absolute", False)))
        if self.program_xri_absolute:
            self.program_xri_absolute.setChecked(bool(header.get("xri_absolute", False)))
        if self.program_zra_absolute:
            self.program_zra_absolute.setChecked(bool(header.get("zra_absolute", False)))
        if self.program_zri_absolute:
            self.program_zri_absolute.setChecked(bool(header.get("zri_absolute", False)))
        if self.program_has_subspindle:
            self.program_has_subspindle.setChecked(bool(header.get("has_subspindle", False)))

    def _on_step_double_clicked(self, item):
        """Doppelklick auf Step: Tab öffnen und Daten anzeigen."""
        try:
            index = self.list_ops.row(item)
            if index < 0 or index >= len(self.model.operations):
                return
            
            op = self.model.operations[index]
            
            # Map op_type to tab name
            tab_map = {
                OpType.PROGRAM_HEADER: "tabProgram",
                OpType.FACE: "tabFace",
                OpType.CONTOUR: "tabContour",
                OpType.ABSPANEN: "tabParting",
                OpType.THREAD: "tabThread",
                OpType.GROOVE: "tabGroove",
                OpType.DRILL: "tabDrill",
                OpType.KEYWAY: "tabKeyway",
            }
            
            tab_name = tab_map.get(op.op_type)
            if tab_name and self.tab_params:
                # Find tab index by name
                for i in range(self.tab_params.count()):
                    if self.tab_params.widget(i).objectName() == tab_name:
                        self.tab_params.setCurrentIndex(i)
                        break
            
            # Load operation data into UI
            self._load_operation_into_widgets(op)
        except Exception as e:
            print(f"[LatheEasyStep] _on_step_double_clicked: {e}")

    def _handle_move_up(self):
        if self._moving_up:
            return
        self._moving_up = True
        try:
            if self.list_ops is None:
                return
            idx = self.list_ops.currentRow()
            if idx <= 0:
                return
            self.model.move_up(idx)
            self._refresh_operation_list(select_index=idx - 1)
            self._refresh_preview()
        finally:
            self._moving_up = False

    def _handle_move_down(self):
        if self._moving_down:
            return
        self._moving_down = True
        try:
            if self.list_ops is None:
                return
            idx = self.list_ops.currentRow()
            if idx < 0 or idx >= self.list_ops.count() - 1:
                return
            self.model.move_down(idx)
            self._refresh_operation_list(select_index=idx + 1)
            self._refresh_preview()
        finally:
            self._moving_down = False

    def _init_contour_table(self):
        """Sorgt für Spalten/Headers in der Kontur-Tabelle."""
        table = self.contour_segments
        if table is None:
            return
        # immer sicherstellen, dass 5 Spalten und Header vorhanden sind
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Typ", "X", "Z", "Kante", "Maß", "Bogen"])
        try:
            table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
            table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        except Exception:
            pass
        try:
            header = table.horizontalHeader()
            header.setStretchLastSection(True)
        except Exception:
            pass
        try:
            table.setStyleSheet(
                "QTableWidget { background: #f5f5f5; color: #000000; gridline-color: #808080; }"
                "QHeaderView::section { background: #d0d0d0; color: #000000; }"
                "QTableWidget::item { color: #000000; background: #ffffff; }"
            )
            table.setAlternatingRowColors(True)
            table.setShowGrid(True)
        except Exception:
            pass
        try:
            widths = [60, 80, 80, 80, 80, 80]
            for i, w in enumerate(widths):
                table.setColumnWidth(i, w)
        except Exception:
            pass

    # ---- Kontur: Segment-Tabelle --------------------------------------
    def _handle_contour_add_segment(self):
        self._ensure_contour_widgets()
        table = self.contour_segments
        if table is None:
            return

        self._init_contour_table()

        row = table.rowCount()
        existing_segments = self._collect_contour_segments()
        x0 = self.contour_start_x.value() if self.contour_start_x else 0.0
        z0 = self.contour_start_z.value() if self.contour_start_z else 0.0

        last_x = float(existing_segments[-1].get("x", x0)) if existing_segments else x0
        last_z = float(existing_segments[-1].get("z", z0)) if existing_segments else z0
        default_x = last_x
        default_z = last_z

        table.insertRow(row)

        item_cls = QtWidgets.QTableWidgetItem
        def _mk_item(text: str) -> QtWidgets.QTableWidgetItem:
            it = item_cls(text)
            try:
                it.setFlags(
                    QtCore.Qt.ItemIsSelectable
                    | QtCore.Qt.ItemIsEnabled
                    | QtCore.Qt.ItemIsEditable
                )
            except Exception:
                pass
            try:
                it.setForeground(QtGui.QBrush(QtGui.QColor("#000000")))
                it.setBackground(QtGui.QBrush(QtGui.QColor("#ffffff")))
            except Exception:
                pass
            return it

        table.setItem(row, 0, _mk_item("XZ"))
        # X/Z sichtbar vorbelegen (letzter Wert oder Startwert)
        table.setItem(row, 1, _mk_item(f"{default_x:.3f}"))
        table.setItem(row, 2, _mk_item(f"{default_z:.3f}"))

        # Vorlage verwenden (Kante/Maß)
        edge_text = self._contour_edge_template_text
        edge_size = (
            self._contour_edge_template_size
            if edge_text.lower().startswith(("f", "r"))
            else 0.0
        )
        table.setItem(row, 3, _mk_item(edge_text))
        table.setItem(row, 4, _mk_item(f"{edge_size:.3f}"))

        # Bogen-Seite (nur relevant bei Radius) – Dropdown pro Zeile
        arc_text = getattr(self, "_contour_arc_template_text", "Auto")
        arc_combo = QtWidgets.QComboBox()
        arc_combo.addItems(["Auto", "Außen", "Innen"])
        idx = arc_combo.findText(arc_text, QtCore.Qt.MatchFixedString)
        arc_combo.setCurrentIndex(idx if idx >= 0 else 0)
        # nur aktiv wenn Radius
        arc_combo.setEnabled(edge_text.lower().startswith("r"))
        arc_combo.currentIndexChanged.connect(self._handle_contour_table_change)
        table.setCellWidget(row, 5, arc_combo)


        table.setCurrentCell(row, 0)
        try:
            table.setRowHeight(row, 22)
        except Exception:
            pass
        # Sichtbarkeit sicherstellen
        try:
            table.show()
            table.raise_()
        except Exception:
            pass
        try:
            cells = []
            for r in range(table.rowCount()):
                cells.append(
                    [table.item(r, c).text() if table.item(r, c) else "" for c in range(table.columnCount())]
                )
            print(f"[LatheEasyStep][debug] contour rows={table.rowCount()} data={cells}")
        except Exception:
            pass
        # neuer Datensatz -> Vorlage-Modus, nicht automatisch Zeile editieren
        self._contour_row_user_selected = False
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_delete_segment(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)
            self._update_selected_operation()
            self._update_contour_preview_temp()
            self._sync_contour_edge_controls()

    def _handle_contour_move_up(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row <= 0:
            return
        table.insertRow(row - 1)
        for col in range(table.columnCount()):
            item = table.takeItem(row + 1, col)
            table.setItem(row - 1, col, item)
            try:
                w = table.cellWidget(row + 1, col)
                if w is not None:
                    table.removeCellWidget(row + 1, col)
                    table.setCellWidget(row - 1, col, w)
            except Exception:
                pass
        table.removeRow(row + 1)
        table.setCurrentCell(row - 1, 0)
        self._update_selected_operation()
        self._update_contour_preview_temp()

    def _handle_contour_move_down(self):
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        if row < 0 or row >= table.rowCount() - 1:
            return
        table.insertRow(row + 2)
        for col in range(table.columnCount()):
            item = table.takeItem(row, col)
            table.setItem(row + 2, col, item)
            try:
                w = table.cellWidget(row, col)
                if w is not None:
                    table.removeCellWidget(row, col)
                    table.setCellWidget(row + 2, col, w)
            except Exception:
                pass
        table.removeRow(row)
        table.setCurrentCell(row + 1, 0)
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_table_change(self, *args, **kwargs):
        """Aktualisiert die aktive Operation, wenn die Segmenttabelle editiert wird."""
        self._update_selected_operation()
        self._update_contour_preview_temp()
        self._sync_contour_edge_controls()

    def _handle_contour_row_select(self, *args, **kwargs):
        table = self.contour_segments
        self._contour_row_user_selected = bool(table and table.currentRow() >= 0)
        self._sync_contour_edge_controls()

    def _handle_contour_edge_change(self, *args, **kwargs):
        """
        Kante/Kantenmaß:
        - wenn eine Zeile ausgewählt ist, wird diese Zeile geändert
        - ansonsten wird nur die Vorlage für das nächste Segment aktualisiert
        """
        edge_text = self.contour_edge_type.currentText() if self.contour_edge_type else ""
        edge_size = self.contour_edge_size.value() if self.contour_edge_size else 0.0

        # Vorlage immer merken – zählt für das nächste Segment+
        self._contour_edge_template_text = edge_text
        self._contour_edge_template_size = edge_size

        table = self.contour_segments
        if table is not None and table.currentRow() >= 0:
            # Benutzer bearbeitet aktiv eine Tabellenzeile
            self._write_contour_row(table.currentRow(), edge_text=edge_text, edge_size=edge_size)
            self._update_selected_operation()
            self._update_contour_preview_temp()

        # Anzeige/Eingaben nachziehen (zeigt entweder Zeile oder Vorlage)
        self._sync_contour_edge_controls()

    def _update_contour_preview_temp(self):

        try:
            segs = self._collect_contour_segments()
            if not segs:
                self._set_preview_paths([])
                return

            params = {
                "start_x": getattr(self, "contour_start_x", None).value()
                if getattr(self, "contour_start_x", None)
                else 0.0,
                "start_z": getattr(self, "contour_start_z", None).value()
                if getattr(self, "contour_start_z", None)
                else 0.0,
                "coord_mode": getattr(self, "contour_coord_mode", None).currentIndex()
                if getattr(self, "contour_coord_mode", None)
                else 0,
                "segments": segs,
            }
            errs = validate_contour_segments_for_profile(params)
            if errs:
                print("[LatheEasyStep][contour][INVALID]")
                for err in errs:
                    print("  -", err)
                self._set_preview_paths([])
                return

            primitives = build_contour_path(params)
            self._set_preview_paths([primitives])
        except Exception as e:
            print("[LatheEasyStep] _update_contour_preview_temp ERROR:", e)
            self._set_preview_paths([])

    def _sync_contour_edge_controls(self):
        """Synchronisiert Kante/Maß-Eingabe mit der aktuellen Tabellenzeile und blendet Felder."""
        table = self.contour_segments
        if table is None:
            return
        row = table.currentRow()
        edge_txt = self._contour_edge_template_text
        size_val = self._contour_edge_template_size

        # Nur wenn der Benutzer aktiv eine Zeile ausgewählt hat, zeigen wir deren Werte
        if row >= 0:
            edge_item = table.item(row, 3)
            size_item = table.item(row, 4)
            # Edge type can be a QComboBox cell widget (preferred) or a text item
            edge_widget = table.cellWidget(row, 3)
            arc_side_item = table.item(row, 5)
            arc_side_widget = table.cellWidget(row, 5)
            if edge_item and edge_item.text():
                edge_txt = edge_item.text().strip()
            if size_item and size_item.text():
                try:
                    size_val = float(size_item.text())
                except Exception:
                    size_val = 0.0

        # Edge combo
        if self.contour_edge_type:
            idx = self.contour_edge_type.findText(edge_txt, QtCore.Qt.MatchFixedString)
            if idx < 0:
                idx = 0
            self.contour_edge_type.blockSignals(True)
            self.contour_edge_type.setCurrentIndex(idx)
            self.contour_edge_type.blockSignals(False)

        # Edge size Steuerung: Feld bleibt sichtbar; enable nur bei Fase/Radius
        edge_txt_ctrl = self.contour_edge_type.currentText() if self.contour_edge_type else edge_txt
        enable_size = edge_txt_ctrl.lower().startswith("f") or edge_txt_ctrl.lower().startswith("r")
        if self.label_contour_edge_size:
            self.label_contour_edge_size.setVisible(True)
            self.label_contour_edge_size.setEnabled(True)
        if self.contour_edge_size:
            self.contour_edge_size.blockSignals(True)
            self.contour_edge_size.setVisible(True)
            self.contour_edge_size.setEnabled(enable_size)
            self.contour_edge_size.setValue(size_val)
            self.contour_edge_size.blockSignals(False)

    def _handle_new_program(self):
        if self._creating_new_program:
            return
        self._creating_new_program = True
        try:
            self.model.operations.clear()
            self._op_row_user_selected = False
            self._refresh_operation_list(select_index=-1)
            self._refresh_preview()
        finally:
            self._creating_new_program = False

    def _handle_generate_gcode(self):
        """G-Code erzeugen, Datei schreiben und Benutzer informieren."""
        if self._generating_gcode:
            return
        self._generating_gcode = True
        try:
            header = self._collect_program_header()

            default_filepath = self._build_program_filepath(header.get("program_name", ""))
            os.makedirs(os.path.dirname(default_filepath), exist_ok=True)
            filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
                self.root_widget,
                "G-Code speichern",
                default_filepath,
                "G-Code Dateien (*.ngc);;Alle Dateien (*)"
            )
            if not filepath:
                return  # User cancelled

            self.model.program_settings = header
            self.model.program_settings["tools"] = self.tools
            self.model.spindle_speed_max = float(header.get("s1_max") or 0.0)

            unique_tools = set()
            for op in self.model.operations:
                if op.op_type == OpType.PROGRAM_HEADER:
                    continue
                try:
                    val = op.params.get("tool")
                    tool_val = int(float(val)) if val is not None else 0
                except Exception:
                    tool_val = 0
                if tool_val > 0:
                    unique_tools.add(tool_val)
            if len(unique_tools) >= 2:
                xt = header.get("xt")
                zt = header.get("zt")
                if xt is None or zt is None:
                    QtWidgets.QMessageBox.warning(
                        self.root_widget or None,
                        "Werkzeugwechselposition fehlt",
                        "Bitte XT und ZT im Programm-Tab eintragen, da mehrere Werkzeuge verwendet werden.",
                    )
                    if self.program_xt:
                        try:
                            self.program_xt.setFocus()
                        except Exception:
                            pass
                    return

            warnings = self._collect_tool_orientation_warnings()
            if warnings:
                preview = "\n".join(warnings[:5])
                if len(warnings) > 5:
                    preview += f"\n... und {len(warnings) - 5} weitere Schritte"
                QtWidgets.QMessageBox.warning(
                    self.root_widget or None,
                    "Werkzeuglage prüfen",
                    f"Bitte prüfen Sie die Werkzeugauswahl:\n{preview}",
                )
            radius_details = self._radius_warning_details()
            if radius_details:
                preview = "\n".join(detail["message"] for detail in radius_details[:5])
                if len(radius_details) > 5:
                    preview += f"\n... und {len(radius_details) - 5} weitere Schritte"
                resp = QtWidgets.QMessageBox.warning(
                    self.root_widget or None,
                    "Nasenradius fehlt",
                    f"{preview}\n\nTrotzdem ohne Nose Compensation fortfahren?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )
                nose_disabled = resp != QtWidgets.QMessageBox.Yes
                for detail in radius_details:
                    op = detail["op"]
                    op.params["nose_comp_disabled"] = nose_disabled
                    if nose_disabled:
                        op.params["nose_comp_reason"] = detail["message"]
                    else:
                        op.params.pop("nose_comp_reason", None)
            
            # Build header + footer lines with toolchange positions
            header_lines = self._tool_change_position_lines(header)
            footer_lines = self._tool_change_position_lines(header)
            self.model.program_settings["header_lines"] = header_lines
            self.model.program_settings["footer_lines"] = footer_lines
            
            lines = self.model.generate_gcode()
            with builtins.open(filepath, "w") as f:
                f.write("\n".join(lines))
            open_fn = getattr(Action, "CALLBACK_OPEN_PROGRAM", None)
            if callable(open_fn):
                open_fn(filepath)
            else:
                QtWidgets.QMessageBox.information(
                    self.root_widget or None,
                    "LatheEasyStep",
                    f"Programm gespeichert unter:\n{filepath}\n"
                    "Automatisches Öffnen ist nicht verfügbar.",
                )
                print(f"[LatheEasyStep] Hinweis: Programm geschrieben nach {filepath}, automatisches Öffnen nicht verfügbar")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.root_widget or None,
                "LatheEasyStep",
                f"Fehler beim Erzeugen des Programms:\n{e}",
            )
        finally:
            self._generating_gcode = False
        return

    def _handle_load_tool_table(self):
        """Tool table laden und Werkzeug-Dropdowns füllen."""
        try:
            settings = QtCore.QSettings()
            last_path = settings.value("LatheEasyStep/ToolTablePath", "", type=str) or ""
            default_path = last_path or os.path.expanduser("~/linuxcnc/configs")
            filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.root_widget,
                "Werkzeugtabelle laden",
                default_path,
                "tool.tbl (*.tbl);;Tool Table Dateien (*.tbl);;Alle Dateien (*)"
            )
            if not filepath:
                return  # User cancelled

            tools, missing_iso = self._parse_tool_table(filepath)
            self.tools = tools
            self._missing_iso_tools = missing_iso
            self._populate_tool_combos(tools)
            self._update_tool_previews()

            if self.tool_table_path:
                self.tool_table_path.setText(filepath)
                self.tool_table_path.setCursorPosition(0)
            if self.lbl_tool_table_path:
                self.lbl_tool_table_path.setText(filepath)

            settings.setValue("LatheEasyStep/ToolTablePath", filepath)
            QtWidgets.QMessageBox.information(
                self.root_widget or None,
                "LatheEasyStep",
                f"Werkzeugtabelle geladen: {len(tools)} Werkzeuge gefunden.",
            )
            if missing_iso:
                formatted = ", ".join(f"T{num:02d}" for num in missing_iso)
                QtWidgets.QMessageBox.information(
                    self.root_widget or None,
                    "ISO fehlt",
                    f"ISO-Code/Radius konnte für die folgenden Werkzeuge nicht ermittelt werden (optional):\n{formatted}",
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.root_widget or None,
                "LatheEasyStep",
                f"Fehler beim Laden der Werkzeugtabelle:\n{e}",
            )

    def _parse_tool_table(self, filepath: str) -> tuple[Dict[int, Tool], List[int]]:
        """Parse LinuxCNC tool table file and return structured tool info plus ISO warnings."""
        tools: Dict[int, Tool] = {}
        duplicates: set[int] = set()
        missing_iso: List[int] = []

        with builtins.open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                raw = line.strip()
                if not raw or raw.startswith(";") or raw.startswith("#"):
                    continue
                left, _, comment = raw.partition(";")
                left = left.strip()
                comment = comment.strip()
                if not left:
                    continue

                tokens = left.split()
                token_map: Dict[str, str] = {}
                for token in tokens:
                    if len(token) < 2:
                        continue
                    key = token[0].upper()
                    value = token[1:]
                    if not value:
                        continue
                    token_map.setdefault(key, value)

                if "T" not in token_map or "P" not in token_map:
                    continue
                try:
                    toolno = int(float(token_map["T"]))
                except Exception:
                    continue
                if toolno <= 0 or toolno >= 10000:
                    continue
                if toolno in tools:
                    duplicates.add(toolno)
                    continue
                try:
                    pocket = int(float(token_map.get("P", "0")))
                except Exception:
                    pocket = 0
                try:
                    diameter = float(token_map.get("D", "0"))
                except Exception:
                    diameter = 0.0

                orientation = None
                q_value = token_map.get("Q")
                if q_value is not None:
                    try:
                        orientation = int(float(q_value))
                    except Exception:
                        orientation = None

                iso_code, iso_size, radius = self._extract_iso_from_comment(comment)
                if not iso_code:
                    missing_iso.append(toolno)
                radius_value = float(radius or 0.0)
                radius_source = "ISO" if radius_value > 0 else None
                if radius_value <= 0 and diameter > 0 and diameter <= 5.0:
                    radius_value = diameter
                    radius_source = "D"
                kind = self._tool_kind_from_orientation(orientation)
                tool = Tool(
                    t=toolno,
                    p=pocket,
                    d=diameter,
                    q=orientation,
                    comment=comment,
                    iso_code=iso_code,
                    iso_size=iso_size,
                    radius_mm=radius_value,
                    kind=kind,
                    radius_source=radius_source,
                )
                tools[toolno] = tool

        if missing_iso:
            formatted = ", ".join(f"T{num:02d}" for num in sorted(set(missing_iso)))
            print(f"[LatheEasyStep] Hinweis: ISO/Radius fehlt bei: {formatted} (optional)")
        if duplicates:
            print(f"[LatheEasyStep] Tool-Tabelle: Duplikate ignoriert für {', '.join(f'T{num:02d}' for num in sorted(duplicates))}")

        return tools, sorted(set(missing_iso))

    def _extract_iso_from_comment(self, comment: str) -> tuple[str | None, str | None, float | None]:
        if not comment:
            return None, None, None
        text = comment.upper()
        for match in _ISO_PATTERN.finditer(text):
            prefix = match.group(1)
            radius_digits = match.group(2)
            iso_candidate = prefix + radius_digits
            digits_only = re.sub(r"[^0-9]", "", iso_candidate)
            if len(digits_only) < 4:
                continue
            size_code = digits_only[:4]
            try:
                radius = int(radius_digits) / 10.0
            except Exception:
                radius = None
            return iso_candidate, size_code, radius
        return None, None, None

    def _tool_kind_from_orientation(self, orientation: int | None) -> str:
        if orientation is None:
            return "turning"
        return _TOOL_KIND_BY_ORIENTATION.get(orientation, "parting")

    def _populate_tool_combos(self, tools: Dict[int, Tool]):
        """Populate all tool comboboxes with the same set of tools (no filtering)."""
        self.tools = tools
        if tools:
            self._loaded_tools = tools
        sorted_tools = sorted(tools.values(), key=lambda t: t.t)
        if sorted_tools:
            items = []
            for tool in sorted_tools:
                extras = []
                if tool.d and tool.d > 0:
                    extras.append(f"⌀{tool.d:.2f}".rstrip("0").rstrip(".") if tool.d % 1 else f"⌀{int(tool.d)}")
                if tool.radius_mm and tool.radius_mm > 0:
                    extras.append(f"R{tool.radius_mm:.2f}".rstrip("0").rstrip("."))
                label_parts = [f"T{tool.t:02d}"]
                comment = (tool.comment or "").strip()
                if tool.iso_code:
                    label_parts.append(tool.iso_code)
                elif comment:
                    label_parts.append(comment.split(";")[0].strip())
                if extras:
                    label_parts.append(f"({' '.join(extras)})")
                items.append((tool.t, " – ".join(label_parts)))
        else:
            items = []

        combo_names = [
            "face_tool",
            "drill_tool",
            "groove_tool",
            "thread_tool",
            "parting_tool",
        ]
        for combo_name in combo_names:
            combo = getattr(self, combo_name, None)
            if combo is None:
                combo = self._get_widget_by_name(combo_name)
            if combo is None or not hasattr(combo, "clear"):
                continue

            previous = combo.currentData() if hasattr(combo, "currentData") else None
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("— Werkzeug wählen —", 0)
            for tool_no, text in items:
                combo.addItem(text, tool_no)

            if previous is not None:
                idx = combo.findData(previous)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _tool_combo_label(self, tool: Tool, max_comment: int = 32) -> str:
        """Return a short label used inside tool dropdowns."""
        comment = (tool.comment or "").strip() or "kein Kommentar"
        if len(comment) > max_comment:
            comment = comment[: max_comment - 1].rstrip() + "…"
        diameter = f"{tool.d:.2f}".rstrip("0").rstrip(".")
        diameter = diameter if diameter else "0"
        return f"T{tool.t:02d} – {comment} ({diameter} mm)"

    def _update_tool_previews(self):
        """Update tool preview images for all tool combos."""
        tool_combos = ["face_tool", "drill_tool", "groove_tool", "thread_tool", "parting_tool"]

        for combo_name in tool_combos:
            combo = getattr(self, combo_name, None)
            img_label = getattr(self, combo_name + "_img", None)
            if combo is None or img_label is None:
                continue
            
            tool_num = combo.currentData()
            tool_num = int(tool_num) if tool_num is not None else 0
            tool = self.tools.get(tool_num)
            if tool:
                pixmap = self._render_tool_preview(tool)
                img_label.setPixmap(pixmap)
                img_label.setText("")
            else:
                img_label.setPixmap(QtGui.QPixmap())
                img_label.setText("Kein Werkzeug")

    def _render_tool_preview(self, tool: Tool) -> QtGui.QPixmap:
        """Render a simple tool preview using the parsed tool metadata."""
        size = 140
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor("#f4f7fb"))

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        center_x = size / 2
        center_y = size / 2 - 6
        margin = 12

        # draw axes
        axis_pen = QtGui.QPen(QtGui.QColor("#63707c"))
        axis_pen.setWidth(1)
        painter.setPen(axis_pen)
        painter.drawLine(margin, center_y, size - margin, center_y)
        painter.drawLine(center_x, margin, center_x, size - margin)
        painter.setFont(QtGui.QFont("Arial", 8))
        painter.drawText(size - margin + 4, center_y - 2, "X")
        painter.drawText(center_x + 2, margin - 2, "Z")

        # tool body dimensions
        tool_span = max(tool.d, 1.0)
        scale = max((size - margin * 2) / max(tool_span * 1.4, 1.0), 0.5)
        body_height = tool_span * 0.35
        tip_depth = tool_span * 0.6
        base_half = tool_span * 0.5

        tip_y = body_height - tip_depth

        polygon = QtGui.QPolygonF(
            [
                QtCore.QPointF(-base_half, body_height),
                QtCore.QPointF(base_half, body_height),
                QtCore.QPointF(base_half * 0.35, body_height - tool_span * 0.45),
                QtCore.QPointF(0, tip_y),
                QtCore.QPointF(-base_half * 0.35, body_height - tool_span * 0.45),
            ]
        )

        orientation_angle = self._tool_orientation_angle(tool.orientation)

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(orientation_angle)
        painter.scale(scale, scale)
        painter.setPen(QtGui.QPen(QtGui.QColor("#2c3e50"), 0))
        painter.setBrush(QtGui.QColor("#e76f51"))
        painter.drawPolygon(polygon)

        if tool.radius_mm and tool.radius_mm > 0:
            nose_radius = max(tool.radius_mm, tool_span * 0.08)
            circle_pen = QtGui.QPen(QtGui.QColor("#1d3557"))
            circle_pen.setWidthF(0.3)
            painter.setPen(circle_pen)
            painter.setBrush(QtGui.QColor("#f4a261"))
            painter.drawEllipse(QtCore.QPointF(0, tip_y), nose_radius, nose_radius)
        painter.restore()

        painter.setPen(QtGui.QColor("#1c1e26"))
        info_text = f"T{tool.t:02d}"
        if tool.iso_code:
            info_text += f" · {tool.iso_code}"
        painter.drawText(margin, size - margin + 6, info_text)
        if tool.orientation is not None:
            painter.drawText(size - margin - 32, size - margin + 6, f"Q{tool.orientation}")

        painter.end()
        return pixmap

    def _tool_orientation_angle(self, orientation: int | None) -> float:
        if orientation is None:
            return 0.0
        return (orientation % 8) * 45.0

    def _build_program_filepath(self, name_raw: str | None) -> str:
        base = (name_raw or "").strip()
        if not base:
            base = "conv_lathe"

        # Dateinamen säubern: Nur Buchstaben/Ziffern/_/- behalten, Leerzeichen -> _
        base = base.replace(" ", "_")
        base = re.sub(r"[^A-Za-z0-9_\-]", "", base)
        if not base:
            base = "conv_lathe"

        filename = base if base.lower().endswith(".ngc") else f"{base}.ngc"
        return os.path.expanduser(os.path.join("~/linuxcnc/nc_files", filename))

    def _handle_param_change(self):
        """Generic handler for parameter widgets (spinboxes, combos, checkboxes, lineedits)."""
        try:
            w = self.sender()
        except Exception:
            return
        if w is None:
            return

        # Determine current operation
        idx = -1
        try:
            if self.list_ops is not None:
                idx = int(self.list_ops.currentRow())
        except Exception:
            idx = -1

        if idx < 0 or idx >= len(self.model.operations):
            return

        op = self.model.operations[idx]
        if op.params is None:
            op.params = {}

        name = getattr(w, "objectName", lambda: "")()
        if not name:
            return

        # Read widget value
        val = None
        try:
            # QComboBox
            if hasattr(w, "currentText") and hasattr(w, "currentIndex"):
                # Prefer itemData if present (but fall back to text)
                try:
                    data = w.itemData(w.currentIndex())
                    val = data if data is not None else w.currentText()
                except Exception:
                    val = w.currentText()
            # QCheckBox
            elif hasattr(w, "isChecked"):
                val = bool(w.isChecked())
            # Spin boxes
            elif hasattr(w, "value"):
                val = float(w.value())
            # Line edit
            elif hasattr(w, "text"):
                val = str(w.text())
        except Exception:
            return

        # Do NOT write widget.objectName() directly into op.params.
        # The authoritative mapping is built by _collect_params(op_type),
        # so we rebuild the selected operation from the UI and refresh geometry/preview.
        try:
            self._update_selected_operation(force=True)
        except Exception:
            pass
        return


    def _handle_selection_change(self, row: int):
        self._ui_loading = True
        self._op_row_user_selected = bool(
            self.list_ops
            and (self.list_ops.hasFocus() or self._op_row_user_selected)
        )
        if row < 0 or row >= len(self.model.operations):
            return
        op = self.model.operations[row]
        if self.tab_params:
            type_to_tab = {
                OpType.PROGRAM_HEADER: 0,
                OpType.FACE: 1,
                OpType.CONTOUR: 2,
                OpType.ABSPANEN: 3,
                OpType.THREAD: 4,
                OpType.GROOVE: 5,
                OpType.DRILL: 6,
                OpType.KEYWAY: 7,
            }
            self.tab_params.setCurrentIndex(type_to_tab.get(op.op_type, 1))
        self._load_params_to_form(op)
        # keep dynamic UI bits in sync
        try:
            if op.op_type == OpType.FACE:
                self._update_face_visibility()
        except Exception:
            pass
        try:
            self._update_retract_visibility()
        except Exception:
            pass
        self._refresh_preview()
        self._ui_loading = False


    def _handle_global_change(self, *args, **kwargs):
        print("[LatheEasyStep] _handle_global_change() called")
        self._apply_unit_suffix()
        self._update_program_visibility()
        self._update_retract_visibility()
        self._update_subspindle_visibility()
        self._update_face_visibility()

    # ---- Form-Optik ---------------------------------------------------
    def _apply_unit_suffix(self):
        """Einheit mm/inch im gesamten Panel sichtbar umschalten."""

        # Falls aus irgendeinem Grund noch keine Combo referenziert ist:
        if self.program_unit is None:
            self.program_unit = self._find_unit_combo()
            if self.program_unit is None:
                print("[LatheEasyStep] _apply_unit_suffix: no unit combo, abort")
                return

        idx = self.program_unit.currentIndex()
        unit = "mm" if idx == 0 else "inch"

        unit_suffix = f" {unit}"
        feed_suffix = f" {unit}/U"

        # Root-Widget bestimmen
        root = self.root_widget or self.program_unit.window()
        if root is None:
            print("[LatheEasyStep] _apply_unit_suffix: no root widget")
            return

        print(f"[LatheEasyStep] _apply_unit_suffix(): unit={unit}, root={root.objectName()}")

        # --- 1) Alle DoubleSpinBoxen im Fenster behandeln ---
        for sb in root.findChildren(QtWidgets.QDoubleSpinBox):
            name = sb.objectName()

            # Drehzahlfelder S1/S3 nicht anfassen
            if name in ("program_s1", "program_s3") or "spindle" in name.lower():
                continue

            if "feed" in name.lower():
                sb.setSuffix(feed_suffix)
            else:
                sb.setSuffix(unit_suffix)

        # --- 2) Beschriftungstexte: Einheiten komplett entfernen (nur einmal) ---
        if not hasattr(self, "_labels_cleaned") or not self._labels_cleaned:
            for lbl in root.findChildren(QtWidgets.QLabel):
                text = lbl.text()
                # nur Labels anfassen, die überhaupt Klammern mit Einheit haben
                if "(" in text and ")" in text and any(u in text for u in ("mm", "inch", "/U")):
                    prefix = text.split("(", 1)[0].rstrip()
                    lbl.setText(prefix)
            self._labels_cleaned = True

        # Fenstertitel markieren, damit man sofort sieht, dass was passiert
        win = root.window()
        try:
            old_title = win.windowTitle()
            win.setWindowTitle(f"{old_title.split('[')[0].strip()} [{unit}]")
        except Exception:
            pass

    def _update_program_visibility(self, shape=None):
        """Zeigt/verbirgt Programmpfelder abhängig von der Rohteilform."""

        # aktuelle Form ermitteln (Index-basiert für sprachunabhängige Labels)
        shape_idx = None
        if hasattr(self, "program_shape") and self.program_shape is not None:
            try:
                shape_idx = int(self.program_shape.currentIndex())
            except Exception:
                shape_idx = None

        if shape is None:
            if shape_idx is not None and shape_idx >= 0:
                shape = shape_idx
            elif hasattr(self, "program_shape") and self.program_shape is not None:
                shape = self.program_shape.currentText()

        if shape is None or shape == "":
            print("[LatheEasyStep] _update_program_visibility: keine Form")
            return

        # Normalisieren: Index (sprachneutral) oder Text (Fallback)
        shape_key = None
        if isinstance(shape, int):
            shape_map = {0: "zylinder", 1: "rohr", 2: "rechteck", 3: "n-eck"}
            shape_key = shape_map.get(shape)
            shape_text = shape_key or str(shape)
        else:
            shape_text = str(shape)
            shape_key = shape_text.strip().lower()

        print(f"[LatheEasyStep] _update_program_visibility(): shape='{shape_text}'")

        # Root-Widget wie in _apply_unit_suffix benutzen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if root is None:
            print("[LatheEasyStep] _update_program_visibility: kein root_widget")
            return

        def _w(objname: str):
            if not getattr(self, "widgets", None):
                self.widgets = {}
            w = self.widgets.get(objname)
            if w is None and hasattr(self, "_get_widget_by_name"):
                try:
                    w = self._get_widget_by_name(objname)
                except Exception:
                    w = None
                if w is not None:
                    self.widgets[objname] = w
            return w

        widgets = {
            "label_xa": _w("label_prog_xa"),
            "xa": _w("program_xa"),
            "label_xi": _w("label_prog_xi"),
            "xi": _w("program_xi"),
            "label_w": _w("label_prog_w"),
            "w": _w("program_w"),
            "label_l": _w("label_prog_l"),
            "l": _w("program_l"),
            "label_n": _w("label_prog_n"),
            "n": _w("program_n"),
            "label_sw": _w("label_prog_sw"),
            "sw": _w("program_sw"),
        }

        # shape_key wurde oben bereits validiert / normalisiert
        shape_norm = (shape_key or "").strip().lower()

        show_xa = shape_norm in ("zylinder", "rohr")
        show_xi = shape_norm == "rohr"
        show_w = shape_norm == "rechteck"
        show_l = shape_norm == "rechteck"
        show_n = shape_norm in ("n-eck", "ne-eck", "n-eck ")
        show_sw = show_n

        def set_vis(key, visible):
            w = widgets.get(key)
            if w is not None:
                w.setVisible(bool(visible))

        set_vis("label_xa", show_xa); set_vis("xa", show_xa)
        set_vis("label_xi", show_xi); set_vis("xi", show_xi)
        set_vis("label_w", show_w); set_vis("w", show_w)
        set_vis("label_l", show_l); set_vis("l", show_l)
        set_vis("label_n", show_n); set_vis("n", show_n)
        set_vis("label_sw", show_sw); set_vis("sw", show_sw)

    def _update_retract_visibility(self, widget=None, mode_in=None):
        """Zeigt/verbirgt Rückzugsebenen abhängig vom Rückzug-Modus."""

        combo = self.program_retract_mode
        if isinstance(widget, QtWidgets.QComboBox):
            combo = widget

        if combo is None:
            print("[LatheEasyStep] _update_retract_visibility: kein Combo / Modus")
            return

        idx = combo.currentIndex()
        if isinstance(mode_in, (int, float)):
            idx = int(mode_in)

        print(f"[LatheEasyStep] _update_retract_visibility(): widget={combo}, index={idx}")

        # Root-Widget wie in _update_program_visibility benutzen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if root is None:
            print("[LatheEasyStep] _update_retract_visibility: kein root_widget")
            return

        def show(name: str, visible: bool):
            w = None
            if hasattr(self, "_get_widget_by_name"):
                try:
                    w = self._get_widget_by_name(name)
                except Exception:
                    w = None
            if w is None and root is not None:
                try:
                    w = root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
                except Exception:
                    w = None
            if w is None:
                print(f"[LatheEasyStep] _update_retract_visibility: widget '{name}' nicht gefunden")
                return
            w.setVisible(visible)

        # alle Rückzugs-Widgets erst mal ausblenden
        all_widgets = [
            "label_prog_xra", "program_xra",
            "program_xra_absolute",
            "label_prog_xri", "program_xri",
            "program_xri_absolute",
            "label_prog_zra", "program_zra",
            "program_zra_absolute",
            "label_prog_zri", "program_zri",
            "program_zri_absolute",
            "label_retract_hint",
        ]
        for name in all_widgets:
            show(name, False)

        if idx == 0:
            show("label_prog_xra", True)
            show("program_xra", True)
            show("program_xra_absolute", True)
            show("label_prog_zra", True)
            show("program_zra", True)
            show("program_zra_absolute", True)
            show("label_retract_hint", True)
        elif idx == 1:
            show("label_prog_xra", True)
            show("program_xra", True)
            show("program_xra_absolute", True)
            show("label_prog_zra", True)
            show("program_zra", True)
            show("program_zra_absolute", True)
            show("label_prog_xri", True)
            show("program_xri", True)
            show("program_xri_absolute", True)
            show("label_retract_hint", True)
        else:
            for name in all_widgets:
                show(name, True)

    def _update_subspindle_visibility(self, *args, **kwargs):
        """Blendet S3-Felder aus/ein, wenn eine Gegenspindel vorhanden ist."""
        if getattr(self, "program_has_subspindle", None) is None and hasattr(self, "_get_widget_by_name"):
            try:
                self.program_has_subspindle = self._get_widget_by_name("program_has_subspindle")
            except Exception:
                self.program_has_subspindle = None
        if getattr(self, "label_prog_s3", None) is None and hasattr(self, "_get_widget_by_name"):
            try:
                self.label_prog_s3 = self._get_widget_by_name("label_prog_s3")
            except Exception:
                self.label_prog_s3 = None
        if getattr(self, "program_s3", None) is None and hasattr(self, "_get_widget_by_name"):
            try:
                self.program_s3 = self._get_widget_by_name("program_s3")
            except Exception:
                self.program_s3 = None

        has_sub = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
        print(f"[LatheEasyStep] _update_subspindle_visibility(): has_sub={has_sub}")

        # Falls Referenzen fehlen, per findChild nachholen
        root = self.root_widget or self._find_root_widget() or getattr(self, "w", None)
        if self.label_prog_s3 is None and root:
            self.label_prog_s3 = root.findChild(QtWidgets.QWidget, "label_prog_s3")
        if self.program_s3 is None and root:
            self.program_s3 = root.findChild(QtWidgets.QWidget, "program_s3")

        if self.label_prog_s3:
            self.label_prog_s3.setVisible(has_sub)
        else:
            print("[LatheEasyStep] _update_subspindle_visibility: label_prog_s3 not found")

        if self.program_s3:
            self.program_s3.setVisible(has_sub)
        else:
            print("[LatheEasyStep] _update_subspindle_visibility: program_s3 not found")

    def _update_face_visibility(self):
        """Show/hide face (Planen) UI elements depending on mode and edge type.

        The UI differs between installations: some .ui versions have a single
        'face_edge_size' field, others separate 'face_chamfer'/'face_radius'.
        This function supports both.
        """
        try:
            root = self.w.get('MainWindow', None)
        except Exception:
            root = None

        # locate widgets lazily (embedded panels sometimes are not ready at init)
        if root is not None:
            if getattr(self, 'label_face_mode', None) is None:
                self.label_face_mode = root.findChild(QtWidgets.QLabel, "label_face_mode")
            if getattr(self, 'face_mode', None) is None:
                self.face_mode = root.findChild(QtWidgets.QComboBox, "face_mode")
            if getattr(self, 'label_face_finish_direction', None) is None:
                self.label_face_finish_direction = root.findChild(QtWidgets.QLabel, "label_face_finish_direction")
            if getattr(self, 'face_finish_direction', None) is None:
                self.face_finish_direction = root.findChild(QtWidgets.QComboBox, "face_finish_direction")
            if getattr(self, 'label_face_edge_type', None) is None:
                self.label_face_edge_type = root.findChild(QtWidgets.QLabel, "label_face_edge_type")
            if getattr(self, 'face_edge_type', None) is None:
                self.face_edge_type = root.findChild(QtWidgets.QComboBox, "face_edge_type")

            # generic edge size field (some UIs)
            if getattr(self, 'label_face_edge_size', None) is None:
                self.label_face_edge_size = root.findChild(QtWidgets.QLabel, "label_face_edge_size")
            if getattr(self, 'face_edge_size', None) is None:
                self.face_edge_size = root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_size")

            # separate chamfer / radius fields (other UIs)
            if getattr(self, 'label_face_chamfer', None) is None:
                self.label_face_chamfer = (
                    root.findChild(QtWidgets.QLabel, "label_face_chamfer")
                    or root.findChild(QtWidgets.QLabel, "label_face_fase")
                    or root.findChild(QtWidgets.QLabel, "label_face_edge_chamfer")
                )
            if getattr(self, 'face_chamfer', None) is None:
                self.face_chamfer = (
                    root.findChild(QtWidgets.QDoubleSpinBox, "face_chamfer")
                    or root.findChild(QtWidgets.QDoubleSpinBox, "face_fase")
                    or root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_chamfer")
                )

            if getattr(self, 'label_face_radius', None) is None:
                self.label_face_radius = (
                    root.findChild(QtWidgets.QLabel, "label_face_radius")
                    or root.findChild(QtWidgets.QLabel, "label_face_edge_radius")
                )
            if getattr(self, 'face_radius', None) is None:
                self.face_radius = (
                    root.findChild(QtWidgets.QDoubleSpinBox, "face_radius")
                    or root.findChild(QtWidgets.QDoubleSpinBox, "face_edge_radius")
                )

        # nothing to do if essential widgets are missing
        if getattr(self, 'face_mode', None) is None or getattr(self, 'face_edge_type', None) is None:
            return

        mode_text = (self.face_mode.currentText() or "").strip().lower()
        finish_visible = ("schlichten" in mode_text) or ("finish" in mode_text)
        if getattr(self, 'label_face_finish_direction', None) is not None:
            self.label_face_finish_direction.setVisible(finish_visible)
        if getattr(self, 'face_finish_direction', None) is not None:
            self.face_finish_direction.setVisible(finish_visible)

        # edge type: 0=none, 1=chamfer/fase, 2=radius (as in UI lists)
        edge_text = (self.face_edge_type.currentText() or "").strip().lower()
        is_chamfer = ("fase" in edge_text) or ("chamfer" in edge_text)
        is_radius = ("radius" in edge_text)
        edge_visible = is_chamfer or is_radius

        # hide everything first
        for w in (
            getattr(self, 'label_face_edge_size', None),
            getattr(self, 'face_edge_size', None),
            getattr(self, 'label_face_chamfer', None),
            getattr(self, 'face_chamfer', None),
            getattr(self, 'label_face_radius', None),
            getattr(self, 'face_radius', None),
        ):
            if w is not None:
                w.setVisible(False)

        if not edge_visible:
            return

        # prefer dedicated widgets if present
        if is_chamfer and getattr(self, 'face_chamfer', None) is not None:
            if getattr(self, 'label_face_chamfer', None) is not None:
                self.label_face_chamfer.setVisible(True)
            self.face_chamfer.setVisible(True)
            return

        if is_radius and getattr(self, 'face_radius', None) is not None:
            if getattr(self, 'label_face_radius', None) is not None:
                self.label_face_radius.setVisible(True)
            self.face_radius.setVisible(True)
            return

        # fallback to generic edge_size widget
        if getattr(self, 'label_face_edge_size', None) is not None:
            self.label_face_edge_size.setVisible(True)
            try:
                self.label_face_edge_size.setText("Fase:" if is_chamfer else "Radius:")
            except Exception:
                pass
        if getattr(self, 'face_edge_size', None) is not None:
            self.face_edge_size.setVisible(True)

    def _update_drill_visibility(self):
        """Show/hide drill UI elements depending on mode."""
        try:
            root = self.w.get('MainWindow', None)
        except Exception:
            root = None

        # locate widgets lazily
        if root is not None:
            if getattr(self, 'drill_mode', None) is None:
                self.drill_mode = root.findChild(QtWidgets.QComboBox, "drill_mode")
            if getattr(self, 'label_drill_dwell', None) is None:
                self.label_drill_dwell = root.findChild(QtWidgets.QLabel, "label_drill_dwell")
            if getattr(self, 'drill_dwell', None) is None:
                self.drill_dwell = root.findChild(QtWidgets.QDoubleSpinBox, "drill_dwell")
            if getattr(self, 'label_drill_peck_depth', None) is None:
                self.label_drill_peck_depth = root.findChild(QtWidgets.QLabel, "label_drill_peck_depth")
            if getattr(self, 'drill_peck_depth', None) is None:
                self.drill_peck_depth = root.findChild(QtWidgets.QDoubleSpinBox, "drill_peck_depth")

        if getattr(self, 'drill_mode', None) is None:
            return

        mode_text = (self.drill_mode.currentText() or "").strip()
        dwell_visible = "G82" in mode_text
        peck_visible = ("G83" in mode_text) or ("G73" in mode_text)

        if getattr(self, 'label_drill_dwell', None) is not None:
            self.label_drill_dwell.setVisible(dwell_visible)
        if getattr(self, 'drill_dwell', None) is not None:
            self.drill_dwell.setVisible(dwell_visible)

        if getattr(self, 'label_drill_peck_depth', None) is not None:
            self.label_drill_peck_depth.setVisible(peck_visible)
        if getattr(self, 'drill_peck_depth', None) is not None:
            self.drill_peck_depth.setVisible(peck_visible)

    def _describe_operation(self, op, number=None):
        def wrap(s):
            return f"{int(number)}. {s}" if number is not None else s
        """Return a short human readable description for the operations list."""
        try:
            t = op.op_type
            p = op.params or {}
        except Exception:
            return str(op)

        def fnum(v, nd=1):
            try:
                return f"{float(v):.{nd}f}"
            except Exception:
                return str(v)

        if t == OpType.PROGRAM_HEADER:
            wcs = str(p.get("wcs", "G54")).upper()
            return wrap(f"Programmkopf ({wcs})")
        if t == OpType.FACE:
            mode = p.get("mode", "schruppen")
            # robust: older saved STEP files may store mode as numeric (e.g. 0.0/1.0)
            if isinstance(mode, (int, float)):
                mode = {0: "schruppen", 1: "schlichten", 2: "schruppen + schlichten"}.get(int(mode), "schruppen")
            if mode is None:
                mode = "schruppen"
            mode = str(mode)
            z_start = p.get("z_start", 0.0)
            z_end = p.get("z_end", 0.0)
            coolant = " mit Kühlung" if p.get("coolant") else ""
            tool = p.get("tool", "T01")
            return wrap(f"Planen {mode.title()} (Z {fnum(z_start)}→{fnum(z_end)}){coolant} ({tool})")
        if t == OpType.CONTOUR:
            side = p.get("side", "außen")
            mode = p.get("mode", "schruppen")
            tool = p.get("tool", "T01")
            return wrap(f"Kontur {mode} ({side}) ({tool})")
        if t == OpType.DRILL:
            depth = p.get("depth", 0.0)
            z0 = p.get("z0", 0.0)
            mode = p.get("mode", "normal")
            tool = p.get("tool", "T01")
            return wrap(f"Bohren {mode} (Z {fnum(z0)}→{fnum(depth)}) ({tool})")
        if t == OpType.GROOVE:
            z = p.get("z", 0.0)
            width = p.get("width", 0.0)
            tool = p.get("tool", "T01")
            return wrap(f"Einstechen (Z {fnum(z)}; B {fnum(width)}) ({tool})")
        if t == OpType.THREAD:
            pitch = p.get("pitch", 0.0)
            z0 = p.get("z0", 0.0)
            z1 = p.get("z1", 0.0)
            orient = p.get("orientation", "aussengewinde")
            tool = p.get("tool", "T01")
            return wrap(f"Gewinde {orient} (P {fnum(pitch,2)}; Z {fnum(z0)}→{fnum(z1)}) ({tool})")
        if t == OpType.ABSPANEN:
            contour_name = p.get("contour_name", "unbekannt")
            strategy = p.get("slice_strategy", "parallel_z")
            tool = p.get("tool", "T01")
            return wrap(f"Abspanen ({contour_name}, {strategy}) ({tool})")
        # fallback
        return wrap(f"{t}: {p}")
    def _renumber_operations(self):
        if self.list_ops is None:
            return
        for i in range(self.list_ops.count()):
            item = self.list_ops.item(i)
            op = self.model.operations[i]
            item.setText(self._describe_operation(op, i + 1))

    # ---- QtVCP user command hook (leer) -------------------------------
    def call_user_command_(self, command_file: str | None):
        # Wird von QtVCP erwartet, hier aber bewusst leer gehalten.
        return



    def _setup_groove_tab_ui(self):
        # Widgets aus dem Panel (Root heißt 'easystep' – daher immer über self.w / _get_widget_by_name suchen)
        try:
            self.groove_lage = self._get_widget_by_name("groove_lage")
            self.groove_ref = self._get_widget_by_name("groove_ref")
            self.groove_use_tool_width = self._get_widget_by_name("groove_use_tool_width")
            self.groove_cutting_width = self._get_widget_by_name("groove_cutting_width")
            self.groove_lage_img = self._get_widget_by_name("groove_lage_img")
            self.groove_ref_img = self._get_widget_by_name("groove_ref_img")
            self.groove_width = self._get_widget_by_name("groove_width")
        except Exception:
            return

        # Falls Tab in alter UI ohne diese Elemente läuft: einfach raus
        if not all([self.groove_ref, self.groove_ref_img, self.groove_use_tool_width, self.groove_cutting_width]):
            return

        # Signale
        try:
            self.groove_ref.currentIndexChanged.connect(self._update_groove_tab_ui)
        except Exception:
            pass
        try:
            self.groove_use_tool_width.toggled.connect(self._update_groove_tab_ui)
        except Exception:
            pass
        try:
            self.groove_width.valueChanged.connect(self._update_groove_tab_ui)
        except Exception:
            pass
        try:
            # Lage: Plan-Einstich ist in diesem Panel noch nicht als eigener Zyklus umgesetzt -> Auswahl ausblenden/auf Längs fixieren
            if self.groove_lage is not None:
                self.groove_lage.currentIndexChanged.connect(self._update_groove_tab_ui)
        except Exception:
            pass

        self._update_groove_tab_ui()

    def _update_groove_tab_ui(self):
        """Nur einblenden, was wirklich benötigt wird (ähnlich ShopTurn 5.3.2)."""
        try:
            # Werkzeugbreite separat?
            use_tw = bool(self.groove_use_tool_width.isChecked()) if self.groove_use_tool_width else False
            if self.groove_cutting_width:
                self.groove_cutting_width.setVisible(use_tw)
            lbl = self._get_widget_by_name("label_groove_cutting_width")
            if lbl:
                lbl.setVisible(use_tw)

            # Lage bestimmt nur Anzeige/Erklärung (G-Code bleibt unverändert)
            idx = int(self.groove_lage.currentIndex()) if self.groove_lage is not None else 0

            # Z0-Label je nach Lage etwas eindeutiger benennen (nur UI)
            lbl_z = self._get_widget_by_name("label_23")  # Label zu groove_z
            if lbl_z:
                if idx in (0, 1):
                    lbl_z.setText("Z0 Bezugspunkt (abs)")
                else:
                    # Stirn: Richtung wird über Lage gewählt (Z−/Z+)
                    lbl_z.setText("Z0 Bezugspunkt (abs)")

            # Grafiken aktualisieren
            self._render_groove_diagrams()

            # Preview aktualisieren
            self._refresh_preview()
        except Exception:
            pass

    def _render_groove_diagrams(self):

        """Sehr einfache Grafiken (ohne externe Dateien) für Lage/Bezugspunkt."""
        try:
            from PyQt5 import QtGui, QtCore

            def _mk_pix(w: int, h: int) -> QtGui.QPixmap:
                pm = QtGui.QPixmap(w, h)
                pm.fill(QtCore.Qt.transparent)
                return pm
            # Lage – 4 Varianten: Mantel außen/innen, Stirn vorne/hinten
            if self.groove_lage_img is not None:
                pm = _mk_pix(180, 70)
                p = QtGui.QPainter(pm)
                p.setRenderHint(QtGui.QPainter.Antialiasing, True)

                pen = QtGui.QPen(QtCore.Qt.white)
                pen.setWidth(2)
                p.setPen(pen)

                # Achsen (Z rechts, X nach oben)
                p.drawLine(30, 55, 165, 55)  # Z
                p.drawLine(30, 55, 30, 10)   # X
                p.drawText(168, 58, "Z")
                p.drawText(22, 12, "X")

                idx = int(self.groove_lage.currentIndex()) if self.groove_lage is not None else 0

                # Werkstück-Skizze + Nut
                if idx in (0, 1):
                    if idx == 1:
                        # Mantel innen (ID): nur die ID-Kante zeigen (keine zusätzliche Ø-Linie)
                        p.drawLine(40, 40, 160, 40)  # ID
                        p.drawText(42, 43, "ID")
                        # Nut innen: beginnt an der ID und geht in das Material (Richtung größerer Ø)
                        p.drawRect(95, 40, 18, -12)
                    else:
                        # Mantel außen (OD)
                        p.drawLine(40, 25, 160, 25)     # OD
                        p.drawText(42, 22, "OD")
                        # Nut außen
                        p.drawRect(95, 25, 18, 18)
                else:
                    # Stirn: senkrechte Linie als Stirnfläche, Pfeilrichtung für Z−/Z+
                    p.drawLine(80, 15, 80, 55)  # Stirn
                    p.drawText(84, 22, "Stirn")
                    # Nut als kleines Rechteck in die Stirn
                    p.drawRect(80, 30, 20, 12)
                    # Richtung
                    if idx == 2:
                        # Hauptspindel: Z− (symbolisch nach links)
                        p.drawLine(130, 20, 95, 20)
                        p.drawLine(95, 20, 103, 16)
                        p.drawLine(95, 20, 103, 24)
                        p.drawText(118, 16, "Z−")
                    else:
                        # Gegenspindel: Z+ (symbolisch nach rechts)
                        p.drawLine(95, 20, 130, 20)
                        p.drawLine(130, 20, 122, 16)
                        p.drawLine(130, 20, 122, 24)
                        p.drawText(118, 16, "Z+")

                p.end()
                self.groove_lage_img.setPixmap(pm)

            # Bezugspunkt-Grafik (Z0: Mitte/Linke/Rechte Flanke)
            if self.groove_ref_img is not None:
                pm = _mk_pix(180, 70)
                p = QtGui.QPainter(pm)
                p.setRenderHint(QtGui.QPainter.Antialiasing, True)

                # Grundlinie (Z)
                p.drawLine(20, 55, 170, 55)
                p.drawText(172, 58, "Z")

                # Nutbreite als Balken
                left = 60
                right = 140
                top = 28
                p.drawRect(left, top, right - left, 18)

                ref = 0
                try:
                    ref = int(self.groove_ref.currentIndex()) if self.groove_ref is not None else 0
                except Exception:
                    ref = 0

                if ref == 1:  # linke Flanke
                    z0x = left
                elif ref == 2:  # rechte Flanke
                    z0x = right
                else:  # mitte
                    z0x = (left + right) // 2

                # Z0 Marker
                p.drawLine(z0x, 15, z0x, 65)
                p.drawText(z0x + 2, 14, "Z0")
                p.end()
                self.groove_ref_img.setPixmap(pm)
        except Exception:
            pass


def get_handlers(halcomp, widgets, paths):
    return [HandlerClass(halcomp, widgets, paths)]



# === Safety patch: ensure optional callbacks exist (generated by ChatGPT) ===
# This keeps the panel from crashing if a UI file lacks certain buttons/signals.
try:
    HandlerClass  # noqa: F821
except Exception:
    HandlerClass = None

def _les_noop(self, *args, **kwargs):
    return None

if HandlerClass is not None:
    _missing_ok = [
        # button callbacks (may be absent in some UI variants)
        '_handle_add_operation',
        '_handle_delete_operation',
        '_handle_move_up',
        '_handle_move_down',
        '_handle_global_change',
        '_apply_unit_suffix',  # internal helper in some versions
    ]
    for _n in _missing_ok:
        if not hasattr(HandlerClass, _n):
            setattr(HandlerClass, _n, _les_noop)
