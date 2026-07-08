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
import logging
from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.tools import Tool, parse_tool_table, extract_iso_from_comment, tool_kind_from_orientation
from lathe_easystep.persistence import (
    build_program_data as build_program_data_payload,
    operation_to_step_data,
    step_data_to_operation,
)
from lathe_easystep.storage import (
    GCODE_FILE_PATH_KEY,
    PROGRAM_FILE_PATH_KEY,
    STEP_FILE_PATH_KEY,
    normalized_file_path,
    parse_program_payload,
    program_file_meta,
    set_step_file_path,
    step_file_path,
    step_filename_stem,
)
from lathe_easystep.ui_program import (
    apply_program_header_to_handler,
    sync_form_to_operation,
)
from lathe_easystep.ui_operations import load_operation_params_to_form
from lathe_easystep.ui_preview import (
    apply_preview_paths,
    ensure_preview_widgets,
    on_toggle_slice_view,
    refresh_preview,
    setup_slice_view,
    sync_slice_widget,
)
from lathe_easystep.ui_params import setup_param_maps
from lathe_easystep.ui_selection import (
    handle_selection_change,
    handle_tab_changed,
    on_step_double_clicked,
)
from lathe_easystep.ui_contour import (
    available_contour_names,
    current_parting_contour_name,
    debug_contour_state,
    handle_contour_add_segment,
    handle_contour_delete_segment,
    handle_contour_edge_change,
    handle_contour_move_down,
    handle_contour_move_up,
    handle_contour_row_select,
    handle_contour_table_change,
    init_contour_table,
    resolve_contour_path,
    sync_contour_edge_controls,
    update_contour_preview_temp,
    update_parting_contour_choices,
    update_parting_mode_visibility,
    update_parting_ready_state,
)
from lathe_easystep.ui_groove import render_groove_diagrams, setup_groove_tab_ui, update_groove_tab_ui
from lathe_easystep.ui_visibility import (
    apply_chuck_safety_preset,
    apply_machine_profile_preset,
    apply_unit_suffix,
    chuck_size_mm,
    handle_global_change,
    update_drill_visibility,
    update_face_visibility,
    update_program_visibility,
    update_retract_visibility,
    update_subspindle_visibility,
)
from lathe_easystep.ui_flow import (
    build_gcode_lines,
    describe_operation,
    handle_generate_gcode,
    handle_move_down,
    handle_move_up,
    handle_new_program,
    renumber_operations,
)
from lathe_easystep.tool_logic import (
    build_insert_geometry,
    build_program_filepath,
    collect_tool_orientation_warnings,
    infer_insert_profile,
    infer_insert_shape_key,
    operation_side_hint,
    radius_warning_details,
    render_tool_preview,
    tool_combo_label,
    tool_comment_side_hint,
    tool_holder_angle,
    tool_orientation_angle,
    tool_orientation_mismatch,
)
from lathe_easystep.ui_persistence import (
    build_program_data,
    handle_load_program,
    handle_load_step,
    handle_save_changes,
    handle_save_program,
    handle_save_step,
    write_gcode_file,
    write_program_file,
)
from lathe_easystep.ui_tools import (
    apply_tool_preview_calibration_settings_to_controls,
    auto_load_tool_table,
    ensure_tool_preview_calibration_controls,
    ensure_tool_preview_widgets,
    handle_load_tool_table,
    on_tool_preview_calibration_changed,
    populate_tool_combos,
    render_tool_placeholder,
    reposition_tool_preview_widgets,
    style_tool_preview_label,
    tool_number_from_combo,
    update_tool_previews,
)
from lathe_easystep.ui_widgets import ensure_core_widgets
from lathe_easystep.ui_lifecycle import bootstrap_widget_refs, finalize_ui_ready
from lathe_easystep.ui_signals import (
    connect_core_signals,
    connect_global_form_signals,
    connect_language_signal,
    connect_list_ops_signals,
    connect_mode_visibility_signals,
    connect_param_change_signals,
    connect_resolver_fallbacks,
    connect_tool_preview_signals,
    prepare_signal_connection_context,
)

# Module logger for non-instantiated contexts
_LOGGER = logging.getLogger(__name__)


_INSERT_SHAPE_KEYS = {"C", "D", "V", "S", "T", "W", "R"}


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
DRILL_MODE_LABELS: Tuple[str, str, str, str, str] = (
    "G81 Bohren",
    "G82 Bohren mit Verweilzeit",
    "G83 Tieflochbohren",
    "G73 Spanbruchbohren",
    "G84 Gewindebohren",
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


def _looks_like_panel_widget(widget: QtWidgets.QWidget | None) -> bool:
    """Return True when a widget is the actual LatheEasyStep panel root."""
    if widget is None:
        return False
    try:
        has_ops = widget.findChild(QtWidgets.QWidget, "listOperations", QtCore.Qt.FindChildrenRecursively) is not None
        has_tabs = widget.findChild(QtWidgets.QWidget, "tabParams", QtCore.Qt.FindChildrenRecursively) is not None
        return bool(has_ops and has_tabs)
    except Exception:
        return False
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
    "label_prog_chuck_size": {"de": "Spannfutter", "en": "Chuck Size"},
    "label_prog_machine_profile": {"de": "Maschinenprofil", "en": "Machine Profile"},
    "label_prog_chuck_part_type": {"de": "Werkstücktyp", "en": "Workpiece Type"},
    "label_prog_chuck_grip_mode": {"de": "Spannart", "en": "Clamping Mode"},
    "label_prog_chuck_profile": {"de": "Spannprofil", "en": "Chuck Profile"},
    "label_prog_chuck_x_min": {"de": "No-Go X min (mm)", "en": "No-go X min (mm)"},
    "label_prog_chuck_x_max": {"de": "No-Go X max (mm)", "en": "No-go X max (mm)"},
    "label_prog_chuck_z_limit": {"de": "No-Go Z Grenze (mm)", "en": "No-go Z limit (mm)"},
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
    "label_parting_finish_allow_x": {"de": "Schlichtaufmaß X", "en": "Finish Allow. X"},
    "label_parting_finish_allow_z": {"de": "Schlichtaufmaß Z", "en": "Finish Allow. Z"},

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
    "label_key_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_key_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_32": {"de": "Nutanzahl", "en": "Slot Count"},
    "label_33": {"de": "Startwinkel (°)", "en": "Start Angle (°)"},
    "label_key_slot_angle_step": {"de": "Winkelversatz (°)", "en": "Angle Offset (°)"},
    "label_34": {"de": "Startdurchmesser", "en": "Start Diameter"},
    "label_35": {"de": "Start Z", "en": "Start Z"},
    "label_36": {"de": "Nutlänge", "en": "Slot Length"},
    "label_37": {"de": "Nuttiefe", "en": "Slot Depth"},
    "label_key_slot_width": {"de": "Nutbreite", "en": "Slot Width"},
    "label_key_cutting_width": {"de": "Schneidenbreite", "en": "Cutting Width"},
    "label_38": {"de": "Kopffreiheit (aktuell ohne Wirkung)", "en": "Top Clearance (currently unused)"},
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
    "btnSaveChanges": {"de": "Aenderungen speichern", "en": "Save Changes"},
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
    "program_chuck_size": {
        "de": ["Kein Futter", "80 mm", "100 mm", "125 mm", "160 mm", "200 mm", "250 mm"],
        "en": ["No Chuck", "80 mm", "100 mm", "125 mm", "160 mm", "200 mm", "250 mm"],
    },
    "program_machine_profile": {
        "de": ["Manuell", "Werkstatt 125 Standard", "Werkstatt 100 Soft", "Werkstatt 200 Innen"],
        "en": ["Manual", "Shop 125 Standard", "Shop 100 Soft", "Shop 200 Boring"],
    },
    "program_chuck_part_type": {
        "de": ["Welle (Vollmaterial)", "Rohr"],
        "en": ["Shaft (solid)", "Tube"],
    },
    "program_chuck_grip_mode": {
        "de": ["Außen gespannt", "Innen gespannt"],
        "en": ["Outside grip", "Inside grip"],
    },
    "program_chuck_profile": {
        "de": ["3-Backen Standard", "Softjaws", "Innenausdrehen"],
        "en": ["3-jaw standard", "Soft jaws", "Boring setup"],
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
    "drill_mode": {
        "de": ["G81 Bohren", "G82 Bohren mit Verweilzeit", "G83 Tieflochbohren", "G73 Spanbruchbohren", "G84 Gewindebohren"],
        "en": ["G81 Drilling", "G82 Drill with Dwell", "G83 Peck Drilling", "G73 Chip Break Drilling", "G84 Tapping"],
    },
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


CHUCK_PRESETS: Dict[int, Dict[str, float]] = {
    80: {"jaw_depth_z": 18.0, "jaw_band": 12.0, "sc": 1.5},
    100: {"jaw_depth_z": 22.0, "jaw_band": 14.0, "sc": 2.0},
    125: {"jaw_depth_z": 26.0, "jaw_band": 16.0, "sc": 2.5},
    160: {"jaw_depth_z": 32.0, "jaw_band": 20.0, "sc": 3.0},
    200: {"jaw_depth_z": 38.0, "jaw_band": 24.0, "sc": 3.5},
    250: {"jaw_depth_z": 45.0, "jaw_band": 28.0, "sc": 4.0},
}

CHUCK_PROFILE_MODIFIERS: Dict[int, Dict[str, float]] = {
    0: {"jaw_depth_mul": 1.00, "jaw_band_mul": 1.00, "sc_add": 0.0},   # 3-Backen Standard
    1: {"jaw_depth_mul": 0.75, "jaw_band_mul": 0.80, "sc_add": -0.3},  # Softjaws
    2: {"jaw_depth_mul": 1.20, "jaw_band_mul": 1.30, "sc_add": 0.8},   # Innenausdrehen
}

MACHINE_CHUCK_PROFILE_PRESETS: Dict[int, Dict[str, int]] = {
    1: {"chuck_size_idx": 3, "part_type_idx": 0, "grip_mode_idx": 0, "chuck_profile_idx": 0},
    2: {"chuck_size_idx": 2, "part_type_idx": 0, "grip_mode_idx": 0, "chuck_profile_idx": 1},
    3: {"chuck_size_idx": 5, "part_type_idx": 1, "grip_mode_idx": 1, "chuck_profile_idx": 2},
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
    "parting_finish_allow_x": {
        "de": "Radialer Schlichtzuschlag beim Schruppen",
        "en": "Radial finish allowance during roughing",
    },
    "parting_finish_allow_z": {
        "de": "Axialer Schlichtzuschlag beim Schruppen",
        "en": "Axial finish allowance during roughing",
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
        self.front_program: Dict[str, object] = {}
        self.front_operation: Operation | None = None
        self._blink_timer.timeout.connect(self._on_blink_timer)
        self.setMinimumHeight(200)
        self._base_span = 10.0  # Default 10x10 mm viewport

    def _x_to_display(self, x_val: float) -> float:
        """Map stored X values (diameter programming) to displayed X values (radius)."""
        try:
            x_num = float(x_val)
        except Exception:
            return 0.0
        return x_num * 0.5 if getattr(self, "x_is_diameter", False) else x_num


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
        hits = self._interp_x_hits_at_z(path, z)
        if not hits:
            return None
        return min(hits)

    def _interp_x_hits_at_z(self, path, z: float):
        if not path or len(path) < 2:
            return []
        hits = []
        for (x1, z1), (x2, z2) in zip(path[:-1], path[1:]):
            if abs(z2 - z1) < 1e-9:
                if abs(z - z1) < 1e-6:
                    hits.append(x1); hits.append(x2)
                continue
            if (z1 <= z <= z2) or (z2 <= z <= z1):
                t = (z - z1) / (z2 - z1)
                hits.append(x1 + t * (x2 - x1))
        uniq: List[float] = []
        for val in sorted(float(h) for h in hits):
            if not uniq or abs(val - uniq[-1]) > 1e-6:
                uniq.append(val)
        return uniq

    def _paint_slice_view(self, painter: QtGui.QPainter):
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        diam = None
        if self.paths:
            idx = self.active_index if self.active_index is not None else 0
            idx = max(0, min(idx, len(self.paths) - 1))
            path = self.paths[idx]
            if path and isinstance(path[0], (list, tuple)):
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

    def set_front_context(self, program: Dict[str, object] | None = None, operation: Operation | None = None):
        self.front_program = dict(program or {})
        self.front_operation = operation
        self.update()

    def _path_hits_at_slice(self, path) -> List[float]:
        if not path:
            return []
        if isinstance(path[0], dict):
            try:
                path = self.primitives_to_points(path)
            except Exception:
                return []
        return self._interp_x_hits_at_z(path, self.slice_z)

    def _front_program_operations(self) -> List[Operation]:
        ops = getattr(self, "front_program", {}).get("__operations")
        if isinstance(ops, list):
            return [op for op in ops if isinstance(op, Operation)]
        op = getattr(self, "front_operation", None)
        return [op] if isinstance(op, Operation) else []

    def _front_operation_side(self, op: Operation) -> str | None:
        params = getattr(op, "params", {}) or {}
        if op.op_type in (OpType.DRILL, OpType.BORE):
            return "inside"
        if op.op_type == OpType.GROOVE:
            try:
                return "inside" if int(float(params.get("lage", 0) or 0)) == 1 else "outside"
            except Exception:
                return "outside"
        if op.op_type == OpType.THREAD:
            try:
                return "inside" if int(float(params.get("orientation", 0) or 0)) == 1 else "outside"
            except Exception:
                return "outside"
        if op.op_type == OpType.ABSPANEN:
            try:
                return "inside" if int(float(params.get("side", 0) or 0)) == 1 else "outside"
            except Exception:
                return "outside"
        if op.op_type == OpType.KEYWAY:
            return None
        return "outside"

    def _front_active_diameters(self) -> List[float]:
        prog = getattr(self, "front_program", {}) or {}
        try:
            stock_od = abs(float(prog.get("xa", 0.0) or 0.0))
        except Exception:
            stock_od = 0.0
        try:
            stock_id = abs(float(prog.get("xi", 0.0) or 0.0))
        except Exception:
            stock_id = 0.0

        outer_dia = stock_od if stock_od > 1e-6 else None
        inner_dia = stock_id if stock_id > 1e-6 else None

        ops = self._front_program_operations()
        if not ops and self.paths:
            idx = self.active_index if self.active_index is not None else 0
            idx = max(0, min(idx, len(self.paths) - 1))
            return [abs(d) for d in self._path_hits_at_slice(self.paths[idx]) if abs(d) > 1e-6]

        for op in ops:
            if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
                continue
            if getattr(op, "op_type", None) == OpType.KEYWAY:
                continue
            hits = [abs(d) for d in self._path_hits_at_slice(getattr(op, "path", []) or []) if abs(d) > 1e-6]
            if not hits:
                continue
            side = self._front_operation_side(op)
            if side == "inside":
                cand = max(hits)
                inner_dia = cand if inner_dia is None else max(inner_dia, cand)
            else:
                cand = min(hits)
                outer_dia = cand if outer_dia is None else min(outer_dia, cand)

        result: List[float] = []
        if outer_dia is not None and outer_dia > 1e-6:
            result.append(outer_dia)
        if inner_dia is not None and inner_dia > 1e-6 and (outer_dia is None or inner_dia < outer_dia + 1e-6):
            result.append(inner_dia)
        return result

    def _front_reference_diameter(self) -> float:
        prog = getattr(self, "front_program", {}) or {}
        candidates: List[float] = []

        for key in ("xa", "xi"):
            try:
                val = abs(float(prog.get(key, 0.0) or 0.0))
            except Exception:
                val = 0.0
            if val > 1e-6:
                candidates.append(val)

        for op in self._front_program_operations():
            if op is None or getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
                continue
            path = getattr(op, "path", None) or []
            if not path:
                continue
            if isinstance(path[0], dict):
                try:
                    pts = self.primitives_to_points(path)
                except Exception:
                    pts = []
            else:
                pts = path
            for pt in pts:
                try:
                    dia = abs(float(pt[0]))
                except Exception:
                    continue
                if dia > 1e-6:
                    candidates.append(dia)

            if getattr(op, "op_type", None) == OpType.KEYWAY:
                params = getattr(op, "params", {}) or {}
                try:
                    start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
                    nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
                    radial_side = int(float(params.get("radial_side", 0) or 0))
                except Exception:
                    continue
                if start_dia > 1e-6:
                    candidates.append(start_dia)
                    if radial_side != 0 and nut_depth > 1e-6:
                        candidates.append(start_dia + (2.0 * nut_depth))

        return max(candidates, default=10.0)

    def _draw_front_keyway_overlay(self, painter: QtGui.QPainter, center: QtCore.QPointF, scale: float):
        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 120, 120), 2))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80, 80)))
        samples = 14

        for op in self._front_program_operations():
            if op is None or getattr(op, "op_type", None) != OpType.KEYWAY:
                continue
            params = getattr(op, "params", {}) or {}
            try:
                mode = int(float(params.get("mode", 0)))
            except Exception:
                mode = 0
            if mode != 0:
                continue

            try:
                start_dia = abs(float(params.get("start_x_dia", 0.0) or 0.0))
                nut_depth = abs(float(params.get("nut_depth", 0.0) or 0.0))
                slot_width = abs(float(params.get("slot_width", params.get("cutting_width", 0.0)) or 0.0))
                radial_side = int(float(params.get("radial_side", 0) or 0))
            except Exception:
                continue

            bounds = keyway_slice_bounds(params)
            if bounds is None:
                continue
            z_min, z_max = bounds
            if self.slice_z < z_min - 1e-6 or self.slice_z > z_max + 1e-6 or start_dia <= 0.0:
                continue

            base_radius = start_dia * 0.5
            if radial_side == 0:
                slot_outer_radius = base_radius
                slot_inner_radius = max(0.0, base_radius - nut_depth)
            else:
                slot_inner_radius = base_radius
                slot_outer_radius = base_radius + nut_depth

            if slot_outer_radius <= 1e-9:
                continue

            if slot_width > 0.0:
                half_opening = max(math.radians(2.0), min(math.radians(40.0), slot_width / max(slot_outer_radius, 1e-6)))
            else:
                half_opening = math.radians(6.0)

            for a_mid in build_keyway_slot_angles(params):
                a0 = a_mid - half_opening
                a1 = a_mid + half_opening
                poly = QtGui.QPolygonF()
                for i in range(samples + 1):
                    ang = a0 + ((a1 - a0) * i / samples)
                    x_off, y_off = front_view_polar_to_cartesian(ang, slot_outer_radius * scale)
                    poly.append(QtCore.QPointF(
                        center.x() + x_off,
                        center.y() + y_off,
                    ))
                for i in range(samples, -1, -1):
                    ang = a0 + ((a1 - a0) * i / samples)
                    x_off, y_off = front_view_polar_to_cartesian(ang, slot_inner_radius * scale)
                    poly.append(QtCore.QPointF(
                        center.x() + x_off,
                        center.y() + y_off,
                    ))
                painter.drawPolygon(poly)
        painter.restore()

    def _paint_front_view(self, painter: QtGui.QPainter):
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        def _float(value: object, default: float = 0.0) -> float:
            try:
                if value is None:
                    return default
                return float(value)
            except Exception:
                return default

        prog = getattr(self, "front_program", {}) or {}
        stock_od = abs(_float(prog.get("xa"), 0.0))
        stock_id = abs(_float(prog.get("xi"), 0.0))
        active_diams = [abs(d) for d in self._front_active_diameters() if abs(d) > 1e-6]
        outer_dia = active_diams[0] if active_diams else 0.0
        inner_dia = active_diams[1] if len(active_diams) > 1 else 0.0

        max_diameter = max(self._front_reference_diameter(), 10.0)
        r = self.rect().adjusted(20, 20, -20, -36)
        center = QtCore.QPointF(float(r.center().x()), float(r.center().y()))
        scale = min(r.width(), r.height()) / max(max_diameter * 1.15, 1e-6)

        painter.setPen(QtGui.QPen(QtGui.QColor(70, 70, 70), 1))
        painter.drawLine(QtCore.QPointF(r.left(), center.y()), QtCore.QPointF(r.right(), center.y()))
        painter.drawLine(QtCore.QPointF(center.x(), r.top()), QtCore.QPointF(center.x(), r.bottom()))

        if stock_od > 1e-6:
            painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150), 1, QtCore.Qt.DashLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (stock_od * 0.5) * scale
            painter.drawEllipse(center, rad, rad)
        if stock_id > 1e-6 and stock_id < stock_od:
            painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 110), 1, QtCore.Qt.DashLine))
            rad = (stock_id * 0.5) * scale
            painter.drawEllipse(center, rad, rad)

        if outer_dia > 1e-6:
            painter.save()
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 80, 80, 70)))
            painter.drawEllipse(center, (outer_dia * 0.5) * scale, (outer_dia * 0.5) * scale)
            if inner_dia > 1e-6 and inner_dia < outer_dia:
                painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
                painter.drawEllipse(center, (inner_dia * 0.5) * scale, (inner_dia * 0.5) * scale)
            painter.restore()

        self._draw_front_keyway_overlay(painter, center, scale)

        for idx, diameter in enumerate(active_diams):
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 80, 80) if idx == 0 else QtGui.QColor(255, 170, 70), 2))
            painter.setBrush(QtCore.Qt.NoBrush)
            rad = (diameter * 0.5) * scale
            painter.drawEllipse(center, rad, rad)

        painter.setPen(QtGui.QPen(QtCore.Qt.white, 1))
        painter.drawText(10, self.height() - 10, f"Vorderansicht bei Z = {self.slice_z:.3f} mm")
        if active_diams:
            painter.drawText(10, 16, "D final: " + ", ".join(f"{d:.3f}" for d in active_diams[:3]))
        painter.drawText(10, 32, f"D max: {max_diameter:.3f}")

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
        # All X values in primitives are DIAMETER (LinuxCNC lathe convention).
        # The fillet arc is a circle in physical (radius) space, so we must
        # convert X to radius for correct geometry (angles, distances).
        x1, z1 = p1[0] / 2.0, p1[1]
        x2, z2 = p2[0] / 2.0, p2[1]
        xc, zc = c[0] / 2.0, c[1]
        r1 = math.hypot(x1 - xc, z1 - zc)
        r2 = math.hypot(x2 - xc, z2 - zc)
        if r1 <= 1e-9 or abs(r1 - r2) > 1e-3:
            return [p1, p2]
        a1 = math.atan2(z1 - zc, x1 - xc)
        a2 = math.atan2(z2 - zc, x2 - xc)
        # The primitive's ccw flag follows LinuxCNC G18 complex(Z,X)
        # convention, but atan2(z,x) measures angle from X toward Z
        # — opposite rotation sense.  Invert the sweep direction so
        # the preview arc matches the physical fillet.
        if not ccw:          # G-code CW (G2) → preview CCW sweep
            if a2 <= a1:
                a2 += 2 * math.pi
        else:                # G-code CCW (G3) → preview CW sweep
            if a2 >= a1:
                a2 -= 2 * math.pi
        pts = []
        for k in range(steps + 1):
            t = k / steps
            a = a1 + (a2 - a1) * t
            # Sample in radius-space, convert X back to diameter
            pts.append(((xc + r1 * math.cos(a)) * 2.0, zc + r1 * math.sin(a)))
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
        if getattr(self, "view_mode", "side") == "front":
            try:
                self._paint_front_view(painter)
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
                x_draw = self._x_to_display(xv)
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
                x_draw = self._x_to_display(x_val)
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_draw - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            def to_screen_display(x_display: float, z_val: float) -> QtCore.QPointF:
                x_pix = rect.left() + (z_val - min_z) * scale
                z_pix = rect.bottom() - (x_display - min_x) * scale
                return QtCore.QPointF(x_pix, z_pix)

            # optional slice indicator (selected Z)
            if getattr(self, "slice_enabled", False) and getattr(self, "view_mode", "side") == "side":
                try:
                    zline = float(getattr(self, "slice_z", 0.0))
                    p1 = to_screen_display(min_x, zline)
                    p2 = to_screen_display(max_x, zline)
                    pen = QtGui.QPen(QtGui.QColor(255, 180, 0), 2, QtCore.Qt.DashLine)
                    painter.setPen(pen)
                    painter.drawLine(p1, p2)
                    label = f"Schnitt Z {zline:.3f}"
                    text_pos = QtCore.QPointF(min(p1.x() + 8, rect.right() - 90), rect.top() + 16)
                    painter.setPen(QtGui.QPen(QtGui.QColor(255, 220, 120), 1))
                    painter.drawText(text_pos, label)
                except Exception:
                    pass

            # Achsen und Skala (außen: links/unten)
            painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 1))
            axis_x_val = 0.0 if min_x <= 0.0 <= max_x else min_x
            axis_z_val = 0.0 if min_z <= 0.0 <= max_z else min_z
            x_axis = to_screen_display(axis_x_val, min_z)
            x_axis_end = to_screen_display(axis_x_val, max_z)
            z_axis = to_screen_display(min_x, axis_z_val)
            z_axis_end = to_screen_display(max_x, axis_z_val)
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
                pt = to_screen_display(axis_x_val, val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x(), pt.y() - 4, pt.x(), pt.y() + 2))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 6, pt.y() + 14), f"{val:.0f}")
                val += step_z

            # X-Ticks (vertikal links/rechts)
            step_x = nice_step(max_x - min_x)
            val = (min_x // step_x) * step_x
            while val <= max_x:
                pt = to_screen_display(val, axis_z_val)
                painter.setPen(tick_pen)
                painter.drawLine(QtCore.QLineF(pt.x() - 2, pt.y(), pt.x() + 4, pt.y()))
                painter.setPen(font_pen)
                painter.drawText(QtCore.QPointF(pt.x() - 28, pt.y() + 4), f"{val:.0f}")
                val += step_x

            # Achsbeschriftungen
            painter.setPen(font_pen)
            painter.drawText(QtCore.QPointF(rect.right() - 20, z_axis.y() - 6), "Z")
            painter.drawText(QtCore.QPointF(x_axis.x() + 6, rect.top() + 12), "X/R")
            draw_order = [idx for idx in range(len(self.paths)) if idx != self.active_index]
            if self.active_index is not None and 0 <= self.active_index < len(self.paths):
                draw_order.append(self.active_index)

            for idx in draw_order:
                path = self.paths[idx]
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
                elif role == "chuck_nogo":
                    # chuck safety no-go area
                    color = QtGui.QColor(200, 60, 220)
                    width = 1
                    style = QtCore.Qt.DashDotLine
                else:
                    color = QtGui.QColor("lime") if idx != self.active_index else QtGui.QColor("red")
                    width = 2 if idx != self.active_index else 3
                    style = QtCore.Qt.SolidLine

                pen = QtGui.QPen(color, width)
                pen.setStyle(style)
                painter.setPen(pen)

                # Primitive mode (dict primitives from build_*_outline helpers)
                if isinstance(path[0], dict):
                    # NOTE: do NOT connect independent primitives with a single polyline.
                    # For retract planes this would create confusing diagonal "links" between separate helper lines.
                    if role in ("retract", "stock", "worklimit", "chuck_nogo"):
                        if role == "chuck_nogo":
                            region_pts: List[Tuple[float, float]] = []
                            for prim in path:
                                if not isinstance(prim, dict) or prim.get("type") != "line":
                                    continue
                                p1 = prim.get("p1")
                                p2 = prim.get("p2")
                                if p1 and len(p1) >= 2:
                                    try:
                                        region_pts.append((float(p1[0]), float(p1[1])))
                                    except Exception:
                                        pass
                                if p2 and len(p2) >= 2:
                                    try:
                                        region_pts.append((float(p2[0]), float(p2[1])))
                                    except Exception:
                                        pass
                            if region_pts:
                                rx_min = min(p[0] for p in region_pts)
                                rx_max = max(p[0] for p in region_pts)
                                rz_min = min(p[1] for p in region_pts)
                                rz_max = max(p[1] for p in region_pts)
                                fill_poly = QtGui.QPolygonF([
                                    to_screen(rx_min, rz_min),
                                    to_screen(rx_min, rz_max),
                                    to_screen(rx_max, rz_max),
                                    to_screen(rx_max, rz_min),
                                ])
                                painter.save()
                                painter.setPen(QtCore.Qt.NoPen)
                                painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 60, 220, 55)))
                                painter.drawPolygon(fill_poly)
                                painter.restore()
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
                        ("Aktiv", QtGui.QPen(QtGui.QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)),
                        ("Rohteil", QtGui.QPen(QtGui.QColor(180, 180, 180), 1, QtCore.Qt.SolidLine)),
                        ("Rückzug", QtGui.QPen(QtGui.QColor(0, 255, 255), 1, QtCore.Qt.DashLine)),
                        ("Bearbeitungslinie", QtGui.QPen(QtGui.QColor(255, 0, 0), 1, QtCore.Qt.DashLine)),
                        ("Futter-Sperrzone", QtGui.QPen(QtGui.QColor(200, 60, 220), 1, QtCore.Qt.DashDotLine)),
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
    """Build the resulting contour for a facing operation.

    Preview rule:
      - show only the programmed target contour
      - do not show approach, retract or tool motion
    """
    # Check if a custom path is provided
    if "path" in params and params["path"]:
        path_data = params["path"]
        if isinstance(path_data, list) and path_data:
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

    # Show only the final face contour at the target plane.
    path.append((x_inner, z_end))

    # Apply edge at outer corner (x_outer, z_end)
    if edge_type == 1 and edge_size > 0.0:
        # 45° chamfer: edge_size is in physical mm.  Since X is diameter,
        # moving edge_size radially = 2*edge_size in diameter coordinates.
        # This matches the G-code generator in slicer.py which uses
        # start_x - 2.0 * edge_size.
        path.append((max(x_inner, x_outer - 2.0 * edge_size), z_end))
        path.append((x_outer, z_end - edge_size))
        # NOTE: do NOT append (x_outer, z_end) or close back -> that caused the unwanted return line.

    elif edge_type == 2 and edge_size > 0.0:
        # Quarter-circle from face plane to OD.  edge_size is physical mm
        # (radius), but X values are diameter.  Compute in radius-space,
        # then convert X back to diameter for the path.
        import math
        x_outer_r = x_outer / 2.0
        x_inner_r = x_inner / 2.0
        x0_r = max(x_inner_r, x_outer_r - edge_size)
        path.append((x0_r * 2.0, z_end))    # tangent start on face plane
        cx_r = x_outer_r - edge_size          # center X in radius-space
        cz = z_end - edge_size                # center Z (same in both)
        segments = 10
        # a: 90°..0° (start at face plane, end at OD line)
        for i in range(1, segments + 1):
            a = (math.pi / 2.0) * (1.0 - (i / segments))
            x_r = cx_r + edge_size * math.cos(a)
            z = cz + edge_size * math.sin(a)
            path.append((x_r * 2.0, z))       # convert X back to diameter
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
        elif isinstance(prim, dict) and prim.get("type") == "line":
            for pt in (prim.get("p1"), prim.get("p2")):
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


def build_chuck_nogo_primitives(program: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Vorschau-Rechteck für die Futter-Sperrzone (No-Go-Bereich)."""
    def _sf(v: Any, default: float | None = None) -> float | None:
        try:
            if v is None:
                return default
            if isinstance(v, str):
                vv = v.strip().replace(",", ".")
                return float(vv) if vv else default
            return float(v)
        except Exception:
            return default

    x_min = _sf(program.get("chuck_no_go_x_min"), None)
    x_max = _sf(program.get("chuck_no_go_x_max"), None)
    z_lim = _sf(program.get("chuck_no_go_z_limit"), None)
    if x_min is None or x_max is None or z_lim is None:
        return []

    lo = min(float(x_min), float(x_max))
    hi = max(float(x_min), float(x_max))
    if hi - lo <= 1e-6:
        return []

    za = _sf(program.get("za"), 0.0) or 0.0
    zi = _sf(program.get("zi"), 0.0) or 0.0
    span = max(10.0, 0.20 * max(abs(za - zi), 1.0))

    if float(z_lim) <= float(za):
        z_far = min(float(zi), float(z_lim)) - span
        z0 = z_far
        z1 = float(z_lim)
    else:
        z_far = max(float(zi), float(z_lim)) + span
        z0 = float(z_lim)
        z1 = z_far

    return [
        {"type": "line", "p1": (lo, z0), "p2": (hi, z0), "role": "chuck_nogo"},
        {"type": "line", "p1": (hi, z0), "p2": (hi, z1), "role": "chuck_nogo"},
        {"type": "line", "p1": (hi, z1), "p2": (lo, z1), "role": "chuck_nogo"},
        {"type": "line", "p1": (lo, z1), "p2": (lo, z0), "role": "chuck_nogo"},
    ]


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
    """Build the resulting contour for a thread operation.

    The preview shows only the target geometry of the threaded zone, not the
    pass sequence of the tool.
    """
    major = float(params.get("major_diameter", 0.0) or 0.0)
    pitch = max(0.1, float(params.get("pitch", 1.5) or 1.5))
    length = abs(float(params.get("length", 0.0) or 0.0))
    orientation = int(params.get("orientation", 0))
    internal = (orientation == 1)

    # Thread depth (K) — same formula as gcode_for_thread
    raw_td = params.get("thread_depth")
    if isinstance(raw_td, (int, float)) and raw_td > 0:
        thread_depth = float(raw_td)
    else:
        thread_depth = pitch * 0.6134

    if length <= 1e-9:
        return []

    if internal:
        bore_dia = major - 2.0 * thread_depth
        root_dia = max(bore_dia, major)
        crest_dia = min(bore_dia, major)
    else:
        crest_dia = max(0.0, major)
        root_dia = max(0.0, major - 2.0 * thread_depth)

    if abs(root_dia - crest_dia) <= 1e-9:
        return [(crest_dia, 0.0), (crest_dia, -length)]

    path: List[Tuple[float, float]] = []
    path.append((crest_dia, 0.0))

    teeth = max(1, int(math.ceil(length / pitch)))
    z = 0.0
    for _ in range(teeth):
        z_mid = max(-length, z - (pitch * 0.5))
        z_next = max(-length, z - pitch)
        path.append((root_dia, z_mid))
        path.append((crest_dia, z_next))
        z = z_next
        if z <= -length + 1e-9:
            break

    if path[-1][1] > -length:
        path.append((root_dia, -length))

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
    """Build the resulting contour for a drill operation.

    The preview shows only the final drilled bore shape, without approach,
    retract or tool motion.
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

    diameter = max(0.0, diameter)

    # into material => negative Z
    if depth > 0:
        depth = -abs(depth)

    # If no diameter, show only the target axis/depth.
    if diameter <= 1e-9:
        return [
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
        (0.0, 0.0),               # axis at the surface
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
        bottom_z = start_z - nut_length
        final_dia = start_dia + rad_sign * 2 * nut_depth
        return [
            (start_dia, start_z),
            (start_dia, bottom_z),
            (final_dia, bottom_z),
            (final_dia, start_z),
        ]

    # face mode
    top_x = start_dia
    inner_x = start_dia - 2 * nut_length
    back_z = start_z - nut_depth
    return [
        (top_x, start_z),
        (inner_x, start_z),
        (inner_x, back_z),
        (top_x, back_z),
    ]


def build_keyway_slot_angles(params: Dict[str, object]) -> List[float]:
    """Return the center angle of each slot in radians for keyway front preview."""
    try:
        slot_count = max(1, int(float(params.get("slot_count", 1) or 1)))
    except Exception:
        slot_count = 1
    try:
        start_angle_deg = float(params.get("slot_start_angle", 0.0) or 0.0)
    except Exception:
        start_angle_deg = 0.0
    try:
        step_deg = float(params.get("slot_angle_step", 0.0) or 0.0)
    except Exception:
        step_deg = 0.0

    if abs(step_deg) <= 1e-9:
        step_deg = 360.0 / float(slot_count)

    return [math.radians(start_angle_deg + (slot_idx * step_deg)) for slot_idx in range(slot_count)]


def front_view_polar_to_cartesian(angle_rad: float, radius: float) -> tuple[float, float]:
    """Map front-view angles to screen-space coordinates.

    Front view uses a clock-face convention: 0 degrees is at 12 o'clock and
    angles increase clockwise, so 90 degrees lands at 3 o'clock.
    """
    return (math.sin(angle_rad) * radius, -math.cos(angle_rad) * radius)


def keyway_slice_bounds(params: Dict[str, object]) -> tuple[float, float] | None:
    """Return the usable Z range for axial keyway front-view slices."""
    try:
        mode = int(float(params.get("mode", 0) or 0))
    except Exception:
        mode = 0
    if mode != 0:
        return None
    try:
        z_start = float(params.get("start_z", 0.0) or 0.0)
        nut_length = abs(float(params.get("nut_length", 0.0) or 0.0))
    except Exception:
        return None
    z_min = min(z_start, z_start - nut_length)
    z_max = max(z_start, z_start - nut_length)
    return (z_min, z_max)


def default_slice_z_for_operation(op: Operation | None) -> float | None:
    """Choose a meaningful default slice position for front preview widgets."""
    if op is None:
        return None
    if getattr(op, "op_type", None) == OpType.KEYWAY:
        bounds = keyway_slice_bounds(getattr(op, "params", {}) or {})
        if bounds is not None:
            return (bounds[0] + bounds[1]) * 0.5
        try:
            return float((getattr(op, "params", {}) or {}).get("start_z", 0.0) or 0.0)
        except Exception:
            return 0.0

    path = getattr(op, "path", None) or []
    if path and isinstance(path[0], tuple):
        try:
            z_vals = [float(z) for _, z in path]
            return (min(z_vals) + max(z_vals)) * 0.5
        except Exception:
            return None
    return None


def build_groove_preview_path(params: Dict[str, float]) -> List[Tuple[float, float]]:
    """Build the programmed groove contour for preview from the mask values."""
    diameter = float(params.get("diameter", 0.0) or 0.0)
    width = abs(float(params.get("width", 0.0) or 0.0))
    depth = abs(float(params.get("depth", 0.0) or 0.0))
    z0 = float(params.get("z", 0.0) or 0.0)
    mode = int(params.get("mode", params.get("groove_mode", -1)) or -1)
    ref = int(params.get("ref", 0) or 0)
    lage = int(params.get("lage", 0) or 0)

    if mode not in (0, 1):
        mode = 0 if lage in (0, 1) else 1

    if mode == 0:
        if ref == 1:
            z_left = z0
            z_right = z0 + width
        elif ref == 2:
            z_right = z0
            z_left = z0 - width
        else:
            z_left = z0 - (width / 2.0)
            z_right = z0 + (width / 2.0)

        diameter_delta = 2.0 * depth
        x_bottom = diameter + diameter_delta if lage == 1 else diameter - diameter_delta
        return [
            (diameter, z_left),
            (x_bottom, z_left),
            (x_bottom, z_right),
            (diameter, z_right),
        ]

    if ref == 1:
        x_near = diameter
        x_far = diameter + width
    elif ref == 2:
        x_near = diameter - width
        x_far = diameter
    else:
        x_near = diameter - (width / 2.0)
        x_far = diameter + (width / 2.0)

    z_bottom = z0 + depth if lage == 3 else z0 - depth
    return [
        (x_near, z0),
        (x_near, z_bottom),
        (x_far, z_bottom),
        (x_far, z0),
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
                # ---- Fillet must be computed in RADIUS (physical) space ----
                # X values in pts are diameter (LinuxCNC lathe convention).
                # G2/G3 arcs trace circles in the physical XZ plane where
                # X is the actual radial distance, so all geometry (angles,
                # tangent lengths, center) must use radius = diameter / 2.
                p0_r = (p0[0] / 2.0, p0[1])
                p1_r = (p1[0] / 2.0, p1[1])
                p2_r = (p2[0] / 2.0, p2[1])
                # Directions from corner to previous/next point (radius space)
                u1, l1 = _norm(_v(p1_r, p0_r))   # incoming dir (from corner back)
                u2, l2 = _norm(_v(p1_r, p2_r))   # outgoing dir
                if l1 > 1e-9 and l2 > 1e-9:
                    cosang = max(-1.0, min(1.0, _dot(u1, u2)))
                    ang = math.acos(cosang)
                    # if nearly straight, skip edge
                    if ang > 1e-6 and abs(math.pi - ang) > 1e-6:
                        # desired radius (physical mm), with clamp if geometry is too short
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
                            # tangent points in radius space
                            pt1_r = (p1_r[0] + u1[0] * t, p1_r[1] + u1[1] * t)
                            pt2_r = (p1_r[0] + u2[0] * t, p1_r[1] + u2[1] * t)

                            n1 = _perp_ccw(u1)
                            n2 = _perp_ccw(u2)

                            # compute possible centers by intersecting offset normals
                            tol = max(0.01, r * 0.01)
                            candidates = []
                            for s1 in (1.0, -1.0):
                                c1 = (pt1_r[0] + n1[0] * r * s1, pt1_r[1] + n1[1] * r * s1)
                                for s2 in (1.0, -1.0):
                                    c2 = (pt2_r[0] + n2[0] * r * s2, pt2_r[1] + n2[1] * r * s2)
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
                                best_r = None
                                best_score = -1e9
                                for c in candidates:
                                    dx = c[0] - p1_r[0]
                                    dz = c[1] - p1_r[1]
                                    score = dx * bx + dz * bz  # projection on bisector
                                    if arc_side == "inner" and score < 0:
                                        continue
                                    if arc_side == "outer" and score > 0:
                                        continue
                                    if abs(score) > best_score:
                                        best_score = abs(score)
                                        best_r = c
                                if best_r is None:
                                    best_r = candidates[0]

                                # Convert back to diameter for G-code emission
                                pt1_d = (pt1_r[0] * 2.0, pt1_r[1])
                                pt2_d = (pt2_r[0] * 2.0, pt2_r[1])
                                best_d = (best_r[0] * 2.0, best_r[1])

                                _emit_line(cur, pt1_d)
                                # determine CW/CCW using radius-space vectors
                                # _cross() uses (X, Z) order but LinuxCNC G18
                                # defines CW/CCW in the (Z, X) plane (looking
                                # from +Y).  The sign of the cross product is
                                # therefore inverted: negative _cross → CCW (G3),
                                # positive _cross → CW (G2).
                                v1 = (pt1_r[0] - best_r[0], pt1_r[1] - best_r[1])
                                v2 = (pt2_r[0] - best_r[0], pt2_r[1] - best_r[1])
                                ccw = _cross(v1, v2) < 0.0
                                _emit_arc(pt1_d, pt2_d, best_d, ccw)
                                cur = pt2_d
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
            # Fillet is computed in RADIUS (physical) space because G2/G3 arcs
            # must be true circles.  Convert X from diameter to radius.
            import math
            p0_r = (p0[0] / 2.0, p0[1])
            p1_r = (p1[0] / 2.0, p1[1])
            p2_r = (p2[0] / 2.0, p2[1])
            v1_r = (p0_r[0] - p1_r[0], p0_r[1] - p1_r[1])
            v2_r = (p2_r[0] - p1_r[0], p2_r[1] - p1_r[1])
            l1_r = vlen(v1_r)
            l2_r = vlen(v2_r)
            if l1_r < 1e-9 or l2_r < 1e-9:
                errors.append(f"Zeile {i+1}: Segmentlänge zu klein für Radius.")
                continue
            cosang = (v1_r[0] * v2_r[0] + v1_r[1] * v2_r[1]) / (l1_r * l2_r)
            cosang = max(-1.0, min(1.0, cosang))
            ang = math.acos(cosang)
            # For a fillet of radius r, the tangent points are at distance t = r / tan(ang/2)
            t = ev / math.tan(ang / 2.0)
            if t >= l1_r or t >= l2_r:
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


class WidgetResolveError(RuntimeError):
    pass


def _qname(obj):
    try:
        return obj.metaObject().className()
    except Exception:
        return type(obj).__name__


def _path_to_root(w, max_up=25):
    """Debug helper: show parent chain up to root."""
    parts = []
    cur = w
    for _ in range(max_up):
        if cur is None:
            break
        on = getattr(cur, "objectName", lambda: "")()
        parts.append(f"{_qname(cur)}('{on}')")
        cur = cur.parent()
    return " <- ".join(parts)


def _pick_best_root(widgets):
    """
    Try to select a usable root from widgets/handler context.
    Priority:
      1) nearest panel/root marker in parent tree
      2) first QMainWindow/QDialog in parent tree
      3) the first passed widget
    """
    for w in widgets:
        cur = w
        for _ in range(30):
            if cur is None:
                break
            try:
                if cur.objectName() in PANEL_WIDGET_NAMES:
                    if cur.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(cur):
                        pass
                    else:
                        return cur
            except Exception:
                pass
            try:
                if _looks_like_panel_widget(cur):
                    return cur
            except Exception:
                pass
            if isinstance(cur, QtWidgets.QMainWindow):
                return cur
            if isinstance(cur, QtWidgets.QDialog):
                return cur
            cur = cur.parent()

    for w in widgets:
        if w is not None:
            return w

    return None


class WidgetResolver:
    """
    Central widget resolver:
      - resolve(): strict, type-safe, collision-aware
      - try_resolve(): returns None instead of exception
      - resolve_later(): retry via QTimer (embed/timing robust)
    """

    def __init__(self, *, root=None, widgets=None, logger=None):
        self.logger = logger
        self.root = root
        self.widgets = list(widgets) if widgets else []

        if self.root is None:
            self.root = _pick_best_root(self.widgets)

    def _log(self, level, msg):
        if self.logger:
            fn = getattr(self.logger, level, None)
            if callable(fn):
                fn(msg)
                return

        # Reduce noisy warnings when the resolver root is a generic MainWindow/VCPWindow
        # but the actual embedded panel is present in the widget list. In that case
        # many early lookups will naturally fail against the host window; degrade
        # warnings to debug to avoid flooding the startup log.
        try:
            root_name = getattr(self.root, "objectName", lambda: "")()
            if level == "warning" and root_name in ("MainWindow", "VCPWindow"):
                for w in (self.widgets or []):
                    try:
                        if getattr(w, "objectName", lambda: "")() in PANEL_WIDGET_NAMES:
                            level = "debug"
                            break
                    except Exception:
                        continue
        except Exception:
            pass

        # If any of the known roots/widgets is the panel and it has not yet been
        # marked as `ui_ready`, demote warnings to debug to avoid spurious
        # "not found" messages during early startup when the embedded UI
        # is still being constructed.
        try:
            for candidate in ([self.root] + (self.widgets or [])):
                if candidate is None:
                    continue
                ui_ready = getattr(candidate, "ui_ready", None)
                if ui_ready is False and level in ("warning", "debug"):
                    # completely suppress non-error logs until UI is ready
                    return
        except Exception:
            pass

        # Prefer explicit logger if provided, otherwise use module logger.
        logger = self.logger if self.logger is not None else _LOGGER

        # Resolve to a callable logging function (debug/info/warning/error).
        log_fn = getattr(logger, level, None)
        if not callable(log_fn):
            log_fn = getattr(logger, "debug", None)

        # Emit log via logger; swallow any logging errors to avoid startup failures.
        try:
            if callable(log_fn):
                log_fn(f"[WidgetResolver][{level.upper()}] {msg}")
        except Exception:
            # Best-effort fallback: do nothing to avoid noisy prints during startup.
            pass

    def _candidates(self, cls, name=None, *, root=None):
        roots = []
        if root is not None:
            roots.append(root)
        if self.root is not None and self.root not in roots:
            roots.append(self.root)

        for w in self.widgets:
            if w is not None and w not in roots:
                roots.append(w)

        found = []
        # If name is an idx lookup (id:NN or digits), search by dynamic property 'idx'
        maybe_id = None
        try:
            if isinstance(name, str):
                if name.startswith("id:"):
                    maybe_id = name.split(":", 1)[1]
                elif name.isdigit():
                    maybe_id = name
        except Exception:
            maybe_id = None
        if maybe_id is not None:
            try:
                iid = int(maybe_id)
                for r in roots:
                    try:
                        for w in r.findChildren(cls, QtCore.Qt.FindChildrenRecursively):
                            try:
                                val = w.property("idx")
                                if val is None:
                                    continue
                                if (isinstance(val, int) and val == iid) or (isinstance(val, str) and val.isdigit() and int(val) == iid):
                                    found.append(w)
                            except Exception:
                                continue
                    except Exception:
                        continue
            except Exception:
                pass

        for r in roots:
            if r is None:
                continue
            if name:
                c = r.findChildren(cls, name, QtCore.Qt.FindChildrenRecursively)
            else:
                c = r.findChildren(cls, QtCore.Qt.FindChildrenRecursively)
            found.extend(c)

        for w in self.widgets:
            if w is None:
                continue
            if name:
                c = w.findChildren(cls, name, QtCore.Qt.FindChildrenRecursively)
            else:
                c = w.findChildren(cls, QtCore.Qt.FindChildrenRecursively)
            found.extend(c)

        uniq = []
        seen = set()
        for x in found:
            key = int(x.winId()) if hasattr(x, "winId") else id(x)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(x)
        return uniq

    def resolve(
        self,
        cls,
        name,
        *,
        root=None,
        required=True,
        allow_multiple=False,
        prefer_visible=True,
        debug_context=False,
    ):
        if not issubclass(cls, QtCore.QObject):
            raise ValueError("cls must be a Qt QObject subclass")

        cands = self._candidates(cls, name=name, root=root)

        if len(cands) == 0:
            msg = f"Widget '{name}' ({cls.__name__}) not found."
            if debug_context:
                msg += f" root={_qname(self.root) if self.root else None}"
            if required:
                raise WidgetResolveError(msg)
            self._log("warning", msg)
            return None

        if len(cands) > 1 and not allow_multiple:
            details = []
            for i, w in enumerate(cands[:10]):
                details.append(
                    f"  [{i}] {_qname(w)} name='{w.objectName()}' visible={getattr(w,'isVisible',lambda:None)()} "
                    f"enabled={getattr(w,'isEnabled',lambda:None)()} path={_path_to_root(w)}"
                )
            msg = (
                f"objectName collision for '{name}' ({cls.__name__}): {len(cands)} matches.\n"
                + "\n".join(details)
            )
            raise WidgetResolveError(msg)

        if len(cands) == 1:
            return cands[0]

        if prefer_visible:
            vis = [w for w in cands if getattr(w, "isVisible", lambda: False)()]
            if len(vis) == 1:
                return vis[0]
            en = [w for w in cands if getattr(w, "isEnabled", lambda: False)()]
            if len(en) == 1:
                return en[0]
            self._log("warning", f"Multiple matches for '{name}', selecting first after visibility heuristic.")
            return (vis or en or cands)[0]

        self._log("warning", f"Multiple matches for '{name}', selecting first (no heuristic).")
        return cands[0]

    def try_resolve(self, cls, name, **kwargs):
        try:
            return self.resolve(cls, name, required=False, **kwargs)
        except WidgetResolveError as e:
            self._log("warning", str(e))
            return None

    def resolve_later(
        self,
        cls,
        name,
        callback,
        *,
        root=None,
        interval_ms=100,
        timeout_ms=3000,
        allow_multiple=False,
        prefer_visible=True,
        debug_context=False,
    ):
        start = QtCore.QElapsedTimer()
        start.start()

        def _tick():
            try:
                w = self.resolve(
                    cls,
                    name,
                    root=root,
                    required=True,
                    allow_multiple=allow_multiple,
                    prefer_visible=prefer_visible,
                    debug_context=debug_context,
                )
                callback(w, None)
            except WidgetResolveError as e:
                if start.elapsed() >= timeout_ms:
                    callback(None, e)
                else:
                    QtCore.QTimer.singleShot(interval_ms, _tick)

        _tick()


class HandlerClass:
    def _register_known_widgets(self):
        """
        Find commonly-used widgets inside the embedded panel and register them
        as attributes on the panel root (`self.w`). If a found widget has no
        objectName set, give it the expected name so future lookups are fast
        and unambiguous.
        """
        panel_root = self.w
        if panel_root is None:
            return

        known = [
            "btnAdd",
            "btnDelete",
            "btnMoveUp",
            "btnMoveDown",
            "btnNewProgram",
            "btnGenerate",
            "btnSaveStep",
            "btnLoadStep",
            "btnSaveProgram",
            "btnLoadProgram",
            "btnLoadToolTable",
            "contour_segments",
            "previewWidget",
            "contourPreview",
            "previewSliceWidget",
            "btn_slice_view",
            "program_unit",
            "program_shape",
            "program_retract_mode",
            "program_has_subspindle",
            "program_xa",
            "program_xi",
            "program_za",
            "program_zi",
            "program_zb",
            "program_w",
            "program_l",
            "program_n",
            "program_sw",
            "program_xt",
            "program_zt",
            "program_sc",
            "program_machine_profile",
            "program_chuck_size",
            "program_chuck_part_type",
            "program_chuck_grip_mode",
            "program_chuck_profile",
            "program_chuck_x_min",
            "program_chuck_x_max",
            "program_chuck_z_limit",
            "program_name",
            "program_xra",
            "program_xri",
            "program_zra",
            "program_zri",
            "program_xra_absolute",
            "program_xri_absolute",
            "program_zra_absolute",
            "program_zri_absolute",
            "program_xt_absolute",
            "program_zt_absolute",
            "program_s1",
            "program_s3",
            "face_mode",
            "face_edge_type",
            "face_edge_size",
            "face_start_x",
            "face_start_z",
            "face_end_x",
            "face_end_z",
            "face_depth_max",
            "face_pause_enabled",
            "face_pause_distance",
            "face_finish_allow_x",
            "face_finish_allow_z",
            "thread_tool",
            "thread_spindle",
            "thread_coolant",
            "thread_orientation",
            "thread_standard",
            "thread_major_diameter",
            "thread_pitch",
            "thread_length",
            "thread_passes",
            "thread_safe_z",
            "thread_depth",
            "thread_first_depth",
            "thread_peak_offset",
            "thread_retract_r",
            "thread_infeed_q",
        ]

        for name in known:
            try:
                w = getattr(panel_root, name, None)
                if w is None:
                    try:
                        w = panel_root.findChild(QtCore.QObject, name)
                    except Exception:
                        w = None
                if w is None:
                    continue
                # ensure objectName for unambiguous findChildren
                try:
                    if not getattr(w, "objectName", lambda: "")():
                        w.setObjectName(name)
                except Exception:
                    pass
                # attach to root for direct attribute access
                try:
                    setattr(self.w, name, w)
                except Exception:
                    pass
            except Exception:
                continue

    def _process_deferred_lookups(self):
        """Abarbeiten aller in `self._deferred_lookup_queue` gesammelten Lookup-Anfragen.
        Wird in `_finalize_ui_ready()` aufgerufen, nachdem `ui_ready` True gesetzt wurde.
        """
        if not getattr(self, '_deferred_lookup_queue', None):
            return
        queue = list(self._deferred_lookup_queue)
        self._deferred_lookup_queue.clear()
        for item in queue:
            try:
                attr_name, name, cls, debug_context = item
            except Exception:
                continue
            try:
                w = getattr(self.w, name, None)
            except Exception:
                w = None
            if w is None:
                try:
                    w = self._find_any_widget(name)
                except Exception:
                    w = None
            try:
                setattr(self, attr_name, w)
            except Exception:
                pass
            if w is not None and debug_context and getattr(self, "_verbose_widget_logs", False):
                try:
                    self._log(f"[LatheEasyStep] deferred-resolved '{name}' -> {attr_name}", level="debug")
                except Exception:
                    pass

    def __init__(self, halcomp, widgets, paths):
        self.hal = halcomp
        self.w = widgets
        # Restrict all lookups to the panel subtree. The handler may receive
        # either the panel widget itself or the host container that embeds it.
        self._main_window = widgets
        panel_root = None
        try:
            if isinstance(self._main_window, QtWidgets.QWidget):
                current = self._main_window
                while current is not None:
                    try:
                        if current.objectName() in PANEL_WIDGET_NAMES:
                            if current.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(current):
                                pass
                            else:
                                panel_root = current
                                break
                        elif _looks_like_panel_widget(current):
                            panel_root = current
                            break
                    except Exception:
                        pass
                    current = current.parentWidget()
        except Exception:
            panel_root = None

        if panel_root is None:
            try:
                if hasattr(self._main_window, "findChild"):
                    for panel_name in PANEL_WIDGET_NAMES:
                        panel_root = self._main_window.findChild(QtWidgets.QWidget, panel_name)
                        if panel_root is not None:
                            if panel_root.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(panel_root):
                                panel_root = None
                                continue
                            break
            except Exception:
                panel_root = None

        if panel_root is None:
            panel_root = self.w

        self.root_widget = panel_root

        self.w = panel_root
        # mark UI as not-ready until finalize passes have completed
        try:
            if self.w is not None:
                try:
                    setattr(self.w, "ui_ready", False)
                except Exception:
                    try:
                        self.w.setProperty("ui_ready", False)
                    except Exception:
                        pass
        except Exception:
            pass
        # Register known widgets early to avoid repeated global searches
        try:
            self._register_known_widgets()
        except Exception:
            pass
        self.paths = paths
        self.model = ProgramModel()
        # self.root_widget wurde oben gesetzt
        self.tools: Dict[int, Tool] = {}  # loaded tool table
        self._loaded_tools: Dict[int, Tool] | None = None  # cache for repopulating combos after deferred widgets
        self._missing_iso_tools: List[int] = []
        self.param_widgets: Dict[str, Dict[str, QtWidgets.QWidget]] = {}
        self._connected_param_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()
        self._connected_global_widgets: WeakSet[QtWidgets.QWidget] = WeakSet()
        self._thread_standard_populated = False
        self._thread_standard_signal_connected = False
        self._thread_applying_standard = False
        self._startup_complete = False
        self._startup_in_progress = False
        self._parting_choices_initialized = False
        self._post_start_init_scheduled = False
        self._post_start_init_done = False
        self._post_start_init_steps = []
        self._widget_name_cache: Dict[str, List[QtWidgets.QWidget]] = {}
        self._startup_epoch = time.monotonic()
        self._startup_heartbeat_scheduled = False
        self._step_last_dir: str | None = None
        self._last_dialog_dir: str | None = None
        self._current_program_path: str | None = None
        self._current_gcode_path: str | None = None
        self._loading_step = False
        self._deleting = False
        self._saving_step = False
        self._saving_changes = False
        self._moving_up = False
        self._moving_down = False
        self._generating_gcode = False
        self._creating_new_program = False

        # zentrale Widgets
        self.preview = getattr(self.w, "previewWidget", None)
        self.preview_slice = getattr(self.w, "previewSliceWidget", None)
        self.btn_slice_view = getattr(self.w, "btn_slice_view", None)
        self.contour_preview = getattr(self.w, "contourPreview", None)
        # Queue für nachträgliche Widget-Suchen, bis das Panel vollständig geladen ist
        self._deferred_lookup_queue: List[Tuple[str, str, object, bool]] = []
        self._verbose_widget_logs = False
        self._bootstrap_widget_refs()

    def _dialog_start_dir(self, settings: QtCore.QSettings, *keys: str) -> str:
        """Return the most relevant start directory for file dialogs."""
        candidates: List[str | None] = []
        for key in keys:
            if key:
                try:
                    candidates.append(settings.value(key, "", type=str) or "")
                except Exception:
                    candidates.append("")
        candidates.append(getattr(self, "_step_last_dir", None))
        candidates.append(getattr(self, "_last_dialog_dir", None))
        candidates.append(QtCore.QDir.homePath())

        for candidate in candidates:
            if not candidate:
                continue
            candidate = os.path.expanduser(str(candidate))
            if os.path.isdir(candidate):
                return candidate
            parent = os.path.dirname(candidate)
            if parent and os.path.isdir(parent):
                return parent
        return QtCore.QDir.homePath()

    def _remember_dialog_path(self, settings: QtCore.QSettings, file_path: str, *keys: str) -> None:
        """Persist the last used directory for subsequent open/save dialogs."""
        if not file_path:
            return
        directory = os.path.dirname(os.path.abspath(os.path.expanduser(file_path)))
        self._last_dialog_dir = directory
        self._step_last_dir = directory
        for key in keys:
            if key:
                try:
                    settings.setValue(key, directory)
                except Exception:
                    pass
        return

    def _normalized_file_path(self, file_path: str | None) -> str | None:
        return normalized_file_path(file_path)

    def _step_file_path(self, op: Operation) -> str | None:
        return step_file_path(op)

    def _set_step_file_path(self, op: Operation, file_path: str) -> None:
        set_step_file_path(op, file_path)

    def _step_filename_stem(self, op: Operation, index_hint: int | None = None) -> str:
        return step_filename_stem(op, index_hint=index_hint)

    def _write_step_file(self, op: Operation, file_path: str) -> str:
        normalized = self._normalized_file_path(file_path) or file_path
        self._set_step_file_path(op, normalized)
        data = self._operation_to_step_data(op)
        with builtins.open(normalized, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        return normalized

    def _ensure_step_file_link(
        self,
        op: Operation,
        *,
        index_hint: int | None = None,
        parent=None,
        settings=None,
        base_dir: str | None = None,
        force_create: bool = False,
    ) -> bool:
        current = self._step_file_path(op)
        if current and not force_create:
            return True

        if settings is None:
            settings = QtCore.QSettings()
        start_dir = base_dir or self._dialog_start_dir(
            settings,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        default_name = self._step_filename_stem(op, index_hint=index_hint) + ".step.json"
        default_path = os.path.join(start_dir, default_name)
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            "Step-Datei anlegen",
            default_path,
            STEP_FILE_FILTER,
        )
        if not file_path:
            return False
        if not file_path.lower().endswith(".step.json"):
            file_path += ".step.json"
        normalized = self._write_step_file(op, file_path)
        self._remember_dialog_path(
            settings,
            normalized,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        return True

    def _program_file_meta(self) -> Dict[str, object]:
        return program_file_meta(
            list(getattr(self.model, "operations", []) or []),
            self._current_program_path,
            self._current_gcode_path,
        )

    def _bootstrap_widget_refs(self) -> None:
        bootstrap_widget_refs(self)

    def _startup_mark(self, label: str):
        try:
            delta = time.monotonic() - getattr(self, "_startup_epoch", time.monotonic())
            self._log(f"[LatheEasyStep][startup +{delta:0.3f}s] {label}", level="info")
        except Exception:
            pass

    def _schedule_startup_heartbeats(self):
        return

    # ---- interne Helfer zur Widget-Suche ------------------------------
    def _setup_resolver(self):
        widget_list = []
        try:
            if hasattr(self, "w") and self.w is not None:
                widget_list.append(self.w)
        except Exception:
            pass
        if self.root_widget is not None and self.root_widget not in widget_list:
            widget_list.append(self.root_widget)
        self._resolver = WidgetResolver(
            root=getattr(self, "root_widget", None),
            widgets=widget_list,
            logger=getattr(self, "LOG", None),
        )

    def _log(self, *parts, level: str | None = None):
        msg = " ".join(str(p) for p in parts)
        if level is None:
            level = "info"
            lowered = msg.lower()
            if "[debug]" in msg:
                level = "debug"
            elif "[critical]" in lowered or " error" in lowered or "error:" in lowered:
                level = "error"
            elif "warn" in lowered:
                level = "warning"
        try:
            logger = getattr(self, "LOG", None)
            if logger:
                fn = getattr(logger, level, None)
                if callable(fn):
                    fn(msg)
                    return
        except Exception:
            pass
        print(msg)

    def _resolve_core_widgets_strict(self):
        if not hasattr(self, "_resolver"):
            self._setup_resolver()

        mapping = [
            ("list_ops", "listOperations", QtWidgets.QListWidget),
            ("tab_params", "tabParams", QtWidgets.QTabWidget),
            ("btn_add", "btnAdd", QtWidgets.QPushButton),
            ("btn_delete", "btnDelete", QtWidgets.QPushButton),
            ("btn_move_up", "btnMoveUp", QtWidgets.QPushButton),
            ("btn_move_down", "btnMoveDown", QtWidgets.QPushButton),
            ("btn_new_program", "btnNewProgram", QtWidgets.QPushButton),
            ("btn_generate", "btnGenerate", QtWidgets.QPushButton),
            ("btn_save_changes", "btnSaveChanges", QtWidgets.QPushButton),
            ("btn_save_step", "btnSaveStep", QtWidgets.QPushButton),
            ("btn_load_step", "btnLoadStep", QtWidgets.QPushButton),
            ("btn_save_program", "btnSaveProgram", QtWidgets.QPushButton),
            ("btn_load_program", "btnLoadProgram", QtWidgets.QPushButton),
            ("btn_load_tool_table", "btnLoadToolTable", QtWidgets.QPushButton),
            ("contour_segments", "contour_segments", QtWidgets.QTableWidget),
            ("preview", "previewWidget", LathePreviewWidget),
            ("contour_preview", "contourPreview", LathePreviewWidget),
            ("preview_slice", "previewSliceWidget", QtWidgets.QWidget),
            ("program_unit", "program_unit", QtWidgets.QComboBox),
            ("program_shape", "program_shape", QtWidgets.QComboBox),
            ("program_retract_mode", "program_retract_mode", QtWidgets.QComboBox),
            ("program_has_subspindle", "program_has_subspindle", QtWidgets.QCheckBox),
            ("program_xa", "program_xa", QtWidgets.QDoubleSpinBox),
            ("program_xi", "program_xi", QtWidgets.QDoubleSpinBox),
            ("program_za", "program_za", QtWidgets.QDoubleSpinBox),
            ("program_zi", "program_zi", QtWidgets.QDoubleSpinBox),
            ("program_zb", "program_zb", QtWidgets.QDoubleSpinBox),
            ("program_w", "program_w", QtWidgets.QDoubleSpinBox),
            ("program_l", "program_l", QtWidgets.QDoubleSpinBox),
            ("program_n", "program_n", QtWidgets.QSpinBox),
            ("program_sw", "program_sw", QtWidgets.QDoubleSpinBox),
            ("program_xt", "program_xt", QtWidgets.QDoubleSpinBox),
            ("program_zt", "program_zt", QtWidgets.QDoubleSpinBox),
            ("program_sc", "program_sc", QtWidgets.QDoubleSpinBox),
            ("program_machine_profile", "program_machine_profile", QtWidgets.QComboBox),
            ("program_chuck_size", "program_chuck_size", QtWidgets.QComboBox),
            ("program_chuck_part_type", "program_chuck_part_type", QtWidgets.QComboBox),
            ("program_chuck_grip_mode", "program_chuck_grip_mode", QtWidgets.QComboBox),
            ("program_chuck_profile", "program_chuck_profile", QtWidgets.QComboBox),
            ("program_chuck_x_min", "program_chuck_x_min", QtWidgets.QDoubleSpinBox),
            ("program_chuck_x_max", "program_chuck_x_max", QtWidgets.QDoubleSpinBox),
            ("program_chuck_z_limit", "program_chuck_z_limit", QtWidgets.QDoubleSpinBox),
            ("program_name", "program_name", QtWidgets.QLineEdit),
            ("program_xra", "program_xra", QtWidgets.QDoubleSpinBox),
            ("program_xri", "program_xri", QtWidgets.QDoubleSpinBox),
            ("program_zra", "program_zra", QtWidgets.QDoubleSpinBox),
            ("program_zri", "program_zri", QtWidgets.QDoubleSpinBox),
            ("program_xra_absolute", "program_xra_absolute", QtWidgets.QCheckBox),
            ("program_xri_absolute", "program_xri_absolute", QtWidgets.QCheckBox),
            ("program_zra_absolute", "program_zra_absolute", QtWidgets.QCheckBox),
            ("program_zri_absolute", "program_zri_absolute", QtWidgets.QCheckBox),
            ("program_xt_absolute", "program_xt_absolute", QtWidgets.QCheckBox),
            ("program_zt_absolute", "program_zt_absolute", QtWidgets.QCheckBox),
            ("program_s1", "program_s1", QtWidgets.QDoubleSpinBox),
            ("program_s3", "program_s3", QtWidgets.QDoubleSpinBox),
            ("label_prog_xi", "label_prog_xi", QtWidgets.QLabel),
            ("label_prog_w", "label_prog_w", QtWidgets.QLabel),
            ("label_prog_l", "label_prog_l", QtWidgets.QLabel),
            ("label_prog_n", "label_prog_n", QtWidgets.QLabel),
            ("label_prog_sw", "label_prog_sw", QtWidgets.QLabel),
            ("label_prog_xra", "label_prog_xra", QtWidgets.QLabel),
            ("label_prog_xri", "label_prog_xri", QtWidgets.QLabel),
            ("label_prog_zra", "label_prog_zra", QtWidgets.QLabel),
            ("label_prog_zri", "label_prog_zri", QtWidgets.QLabel),
            ("label_prog_s1", "label_prog_s1", QtWidgets.QLabel),
            ("label_prog_s3", "label_prog_s3", QtWidgets.QLabel),
            ("thread_standard", "thread_standard", QtWidgets.QComboBox),
            ("thread_orientation", "thread_orientation", QtWidgets.QComboBox),
            ("thread_spindle", "thread_spindle", QtWidgets.QDoubleSpinBox),
            ("thread_depth", "thread_depth", QtWidgets.QDoubleSpinBox),
            ("thread_first_depth", "thread_first_depth", QtWidgets.QDoubleSpinBox),
            ("thread_peak_offset", "thread_peak_offset", QtWidgets.QDoubleSpinBox),
            ("thread_retract_r", "thread_retract_r", QtWidgets.QDoubleSpinBox),
            ("thread_infeed_q", "thread_infeed_q", QtWidgets.QDoubleSpinBox),
            ("thread_spring_passes", "thread_spring_passes", QtWidgets.QSpinBox),
            ("thread_e", "thread_e", QtWidgets.QDoubleSpinBox),
            ("thread_l", "thread_l", QtWidgets.QSpinBox),
            ("parting_mode", "parting_mode", QtWidgets.QComboBox),
            ("contour_name", "contour_name", QtWidgets.QLineEdit),
            ("contour_start_x", "contour_start_x", QtWidgets.QDoubleSpinBox),
            ("contour_start_z", "contour_start_z", QtWidgets.QDoubleSpinBox),
            ("contour_edge_type", "contour_edge_type", QtWidgets.QComboBox),
            ("contour_edge_size", "contour_edge_size", QtWidgets.QDoubleSpinBox),
            ("contour_add_segment", "contour_add_segment", QtWidgets.QPushButton),
            ("contour_delete_segment", "contour_delete_segment", QtWidgets.QPushButton),
            ("contour_move_up", "contour_move_up", QtWidgets.QPushButton),
            ("contour_move_down", "contour_move_down", QtWidgets.QPushButton),
            ("face_mode", "face_mode", QtWidgets.QComboBox),
            ("face_edge_type", "face_edge_type", QtWidgets.QComboBox),
            ("face_edge_size", "face_edge_size", QtWidgets.QDoubleSpinBox),
            ("face_start_x", "face_start_x", QtWidgets.QDoubleSpinBox),
            ("face_start_z", "face_start_z", QtWidgets.QDoubleSpinBox),
            ("face_end_x", "face_end_x", QtWidgets.QDoubleSpinBox),
            ("face_end_z", "face_end_z", QtWidgets.QDoubleSpinBox),
            ("face_depth_max", "face_depth_max", QtWidgets.QDoubleSpinBox),
            ("label_face_edge_size", "label_face_edge_size", QtWidgets.QLabel),
            ("label_face_finish_allow_x", "label_face_finish_allow_x", QtWidgets.QLabel),
            ("label_face_finish_allow_z", "label_face_finish_allow_z", QtWidgets.QLabel),
            ("label_face_depth_max", "label_face_depth_max", QtWidgets.QLabel),
            ("label_face_pause", "label_face_pause", QtWidgets.QLabel),
            ("label_face_pause_distance", "label_face_pause_distance", QtWidgets.QLabel),
            ("face_pause_enabled", "face_pause_enabled", QtWidgets.QCheckBox),
            ("face_pause_distance", "face_pause_distance", QtWidgets.QDoubleSpinBox),
            ("face_finish_allow_x", "face_finish_allow_x", QtWidgets.QDoubleSpinBox),
            ("face_finish_allow_z", "face_finish_allow_z", QtWidgets.QDoubleSpinBox),
            ("drill_mode", "drill_mode", QtWidgets.QComboBox),
            ("label_drill_dwell", "label_drill_dwell", QtWidgets.QLabel),
            ("label_drill_peck_depth", "label_drill_peck_depth", QtWidgets.QLabel),
            ("drill_dwell", "drill_dwell", QtWidgets.QDoubleSpinBox),
            ("drill_peck_depth", "drill_peck_depth", QtWidgets.QDoubleSpinBox),
            ("parting_contour", "parting_contour", QtWidgets.QComboBox),
            ("parting_side", "parting_side", QtWidgets.QComboBox),
            ("parting_tool", "parting_tool", QtWidgets.QComboBox),
            ("parting_spindle", "parting_spindle", QtWidgets.QDoubleSpinBox),
            ("parting_feed", "parting_feed", QtWidgets.QDoubleSpinBox),
            ("parting_depth_per_pass", "parting_depth_per_pass", QtWidgets.QDoubleSpinBox),
            ("parting_pause_enabled", "parting_pause_enabled", QtWidgets.QCheckBox),
            ("parting_pause_distance", "parting_pause_distance", QtWidgets.QDoubleSpinBox),
            ("label_parting_slice_strategy", "label_parting_slice_strategy", QtWidgets.QLabel),
            ("parting_slice_strategy", "parting_slice_strategy", QtWidgets.QComboBox),
            ("label_parting_slice_step", "label_parting_slice_step", QtWidgets.QLabel),
            ("parting_slice_step", "parting_slice_step", QtWidgets.QDoubleSpinBox),
            ("label_parting_allow_undercut", "label_parting_allow_undercut", QtWidgets.QLabel),
            ("parting_allow_undercut", "parting_allow_undercut", QtWidgets.QCheckBox),
            ("label_parting_finish_allow_x", "label_parting_finish_allow_x", QtWidgets.QLabel),
            ("parting_finish_allow_x", "parting_finish_allow_x", QtWidgets.QDoubleSpinBox),
            ("label_parting_finish_allow_z", "label_parting_finish_allow_z", QtWidgets.QLabel),
            ("parting_finish_allow_z", "parting_finish_allow_z", QtWidgets.QDoubleSpinBox),
            ("label_parting_depth", "label_parting_depth", QtWidgets.QLabel),
            ("label_parting_pause", "label_parting_pause", QtWidgets.QLabel),
            ("label_parting_pause_distance", "label_parting_pause_distance", QtWidgets.QLabel),
            ("thread_tool", "thread_tool", QtWidgets.QComboBox),
            ("thread_major_diameter", "thread_major_diameter", QtWidgets.QDoubleSpinBox),
            ("thread_pitch", "thread_pitch", QtWidgets.QDoubleSpinBox),
            ("thread_length", "thread_length", QtWidgets.QDoubleSpinBox),
            ("label_prog_npv", "label_prog_npv", QtWidgets.QLabel),
            ("label_prog_unit", "label_prog_unit", QtWidgets.QLabel),
            ("label_prog_shape", "label_prog_shape", QtWidgets.QLabel),
            ("label_prog_xa", "label_prog_xa", QtWidgets.QLabel),
            ("label_prog_za", "label_prog_za", QtWidgets.QLabel),
            ("label_prog_zi", "label_prog_zi", QtWidgets.QLabel),
            ("label_prog_zb", "label_prog_zb", QtWidgets.QLabel),
            ("label_prog_retract_mode", "label_prog_retract_mode", QtWidgets.QLabel),
            ("label_prog_xt", "label_prog_xt", QtWidgets.QLabel),
            ("label_prog_zt", "label_prog_zt", QtWidgets.QLabel),
            ("label_prog_sc", "label_prog_sc", QtWidgets.QLabel),
            ("label_prog_name", "label_prog_name", QtWidgets.QLabel),
            ("label_language", "label_language", QtWidgets.QLabel),
            ("label_face_start_x", "label_face_start_x", QtWidgets.QLabel),
            ("label_face_start_z", "label_face_start_z", QtWidgets.QLabel),
            ("label_face_end_x", "label_face_end_x", QtWidgets.QLabel),
            ("label_face_end_z", "label_face_end_z", QtWidgets.QLabel),
            ("label_face_mode", "label_face_mode", QtWidgets.QLabel),
            ("label_face_finish_direction", "label_face_finish_direction", QtWidgets.QLabel),
            ("label_face_edge_type", "label_face_edge_type", QtWidgets.QLabel),
            ("label_face_chamfer", "label_face_chamfer", QtWidgets.QLabel),
            ("label_face_fase", "label_face_fase", QtWidgets.QLabel),
            ("label_face_edge_chamfer", "label_face_edge_chamfer", QtWidgets.QLabel),
            ("label_face_radius", "label_face_radius", QtWidgets.QLabel),
            ("label_face_edge_radius", "label_face_edge_radius", QtWidgets.QLabel),
            ("label_face_spindle", "label_face_spindle", QtWidgets.QLabel),
            ("label_face_tool", "label_face_tool", QtWidgets.QLabel),
            ("label_face_coolant", "label_face_coolant", QtWidgets.QLabel),
            ("label_3", "label_3", QtWidgets.QLabel),
            ("label_4", "label_4", QtWidgets.QLabel),
            ("label_drill_tool", "label_drill_tool", QtWidgets.QLabel),
            ("label_drill_spindle", "label_drill_spindle", QtWidgets.QLabel),
            ("label_drill_coolant", "label_drill_coolant", QtWidgets.QLabel),
            ("label_drill_mode", "label_drill_mode", QtWidgets.QLabel),
            ("label_26", "label_26", QtWidgets.QLabel),
            ("label_27", "label_27", QtWidgets.QLabel),
            ("label_28", "label_28", QtWidgets.QLabel),
            ("label_29", "label_29", QtWidgets.QLabel),
            ("label_parting_contour", "label_parting_contour", QtWidgets.QLabel),
            ("label_parting_side", "label_parting_side", QtWidgets.QLabel),
            ("label_parting_tool", "label_parting_tool", QtWidgets.QLabel),
            ("label_parting_spindle", "label_parting_spindle", QtWidgets.QLabel),
            ("label_parting_coolant", "label_parting_coolant", QtWidgets.QLabel),
            ("label_parting_feed", "label_parting_feed", QtWidgets.QLabel),
            ("label_parting_mode", "label_parting_mode", QtWidgets.QLabel),
            ("label_thread_orientation", "label_thread_orientation", QtWidgets.QLabel),
            ("label_thread_standard", "label_thread_standard", QtWidgets.QLabel),
            ("label_thread_tool", "label_thread_tool", QtWidgets.QLabel),
            ("label_thread_spindle", "label_thread_spindle", QtWidgets.QLabel),
            ("label_thread_coolant", "label_thread_coolant", QtWidgets.QLabel),
            ("label_thread_major_diameter", "label_thread_major_diameter", QtWidgets.QLabel),
            ("label_thread_pitch", "label_thread_pitch", QtWidgets.QLabel),
            ("label_thread_length", "label_thread_length", QtWidgets.QLabel),
            ("label_thread_passes", "label_thread_passes", QtWidgets.QLabel),
            ("label_thread_safe_z", "label_thread_safe_z", QtWidgets.QLabel),
            ("label_thread_depth", "label_thread_depth", QtWidgets.QLabel),
            ("label_thread_first_depth", "label_thread_first_depth", QtWidgets.QLabel),
            ("label_thread_peak_offset", "label_thread_peak_offset", QtWidgets.QLabel),
            ("label_thread_retract_r", "label_thread_retract_r", QtWidgets.QLabel),
            ("label_thread_infeed_q", "label_thread_infeed_q", QtWidgets.QLabel),
            ("label_thread_spring_passes", "label_thread_spring_passes", QtWidgets.QLabel),
            ("label_thread_e", "label_thread_e", QtWidgets.QLabel),
            ("label_thread_l", "label_thread_l", QtWidgets.QLabel),
            ("label_contour_start_x", "label_contour_start_x", QtWidgets.QLabel),
            ("label_contour_start_z", "label_contour_start_z", QtWidgets.QLabel),
            ("label_contour_coord_mode", "label_contour_coord_mode", QtWidgets.QLabel),
            ("label_contour_name", "label_contour_name", QtWidgets.QLabel),
            ("label_contour_edge_type", "label_contour_edge_type", QtWidgets.QLabel),
            ("label_retract_hint", "label_retract_hint", QtWidgets.QLabel),
            ("label_groove_cutting_width", "label_groove_cutting_width", QtWidgets.QLabel),
            ("label_23", "label_23", QtWidgets.QLabel),
            ("btn_slice_view", "btn_slice_view", QtWidgets.QAbstractButton),
            ("btn_thread_preset", "btn_thread_preset", QtWidgets.QPushButton),
            ("groove_tool", "groove_tool", QtWidgets.QComboBox),
            ("groove_spindle", "groove_spindle", QtWidgets.QDoubleSpinBox),
            ("groove_coolant", "groove_coolant", QtWidgets.QComboBox),
            ("groove_diameter", "groove_diameter", QtWidgets.QDoubleSpinBox),
            ("groove_width", "groove_width", QtWidgets.QDoubleSpinBox),
            ("groove_ref", "groove_ref", QtWidgets.QComboBox),
            ("groove_lage", "groove_lage", QtWidgets.QComboBox),
            ("groove_use_tool_width", "groove_use_tool_width", QtWidgets.QCheckBox),
            ("groove_cutting_width", "groove_cutting_width", QtWidgets.QDoubleSpinBox),
            ("groove_depth", "groove_depth", QtWidgets.QDoubleSpinBox),
            ("groove_z", "groove_z", QtWidgets.QDoubleSpinBox),
            ("groove_feed", "groove_feed", QtWidgets.QDoubleSpinBox),
            ("groove_step_a", "groove_step_a", QtWidgets.QDoubleSpinBox),
            ("groove_overlap", "groove_overlap", QtWidgets.QDoubleSpinBox),
            ("groove_retract", "groove_retract", QtWidgets.QDoubleSpinBox),
            ("groove_finish", "groove_finish", QtWidgets.QDoubleSpinBox),
            ("groove_sweep_feed", "groove_sweep_feed", QtWidgets.QDoubleSpinBox),
            ("groove_chip_amp", "groove_chip_amp", QtWidgets.QDoubleSpinBox),
            ("groove_chip_n", "groove_chip_n", QtWidgets.QSpinBox),
            ("groove_safe_z", "groove_safe_z", QtWidgets.QDoubleSpinBox),
            ("groove_reduced_feed_start_x", "groove_reduced_feed_start_x", QtWidgets.QDoubleSpinBox),
            ("groove_reduced_feed", "groove_reduced_feed", QtWidgets.QDoubleSpinBox),
            ("groove_reduced_rpm", "groove_reduced_rpm", QtWidgets.QDoubleSpinBox),
            ("groove_lage_img", "groove_lage_img", QtWidgets.QLabel),
            ("groove_ref_img", "groove_ref_img", QtWidgets.QLabel),
            ("key_mode", "key_mode", QtWidgets.QComboBox),
            ("key_radial_side", "key_radial_side", QtWidgets.QComboBox),
            ("key_tool", "key_tool", QtWidgets.QComboBox),
            ("key_coolant", "key_coolant", QtWidgets.QComboBox),
            ("key_slot_count", "key_slot_count", QtWidgets.QSpinBox),
            ("key_slot_start_angle", "key_slot_start_angle", QtWidgets.QDoubleSpinBox),
            ("key_slot_angle_step", "key_slot_angle_step", QtWidgets.QDoubleSpinBox),
            ("key_start_diameter", "key_start_diameter", QtWidgets.QDoubleSpinBox),
            ("key_start_z", "key_start_z", QtWidgets.QDoubleSpinBox),
            ("key_nut_length", "key_nut_length", QtWidgets.QDoubleSpinBox),
            ("key_nut_depth", "key_nut_depth", QtWidgets.QDoubleSpinBox),
            ("key_slot_width", "key_slot_width", QtWidgets.QDoubleSpinBox),
            ("key_cutting_width", "key_cutting_width", QtWidgets.QDoubleSpinBox),
            ("key_top_clearance", "key_top_clearance", QtWidgets.QDoubleSpinBox),
            ("key_depth_per_pass", "key_depth_per_pass", QtWidgets.QDoubleSpinBox),
            ("key_plunge_feed", "key_plunge_feed", QtWidgets.QDoubleSpinBox),
            ("key_use_c_axis", "key_use_c_axis", QtWidgets.QCheckBox),
            ("key_use_c_axis_switch", "key_use_c_axis_switch", QtWidgets.QCheckBox),
            ("key_c_axis_switch_p", "key_c_axis_switch_p", QtWidgets.QDoubleSpinBox),
            ("label_groove_tool", "label_groove_tool", QtWidgets.QLabel),
            ("label_groove_spindle", "label_groove_spindle", QtWidgets.QLabel),
            ("label_groove_coolant", "label_groove_coolant", QtWidgets.QLabel),
            ("label_key_tool", "label_key_tool", QtWidgets.QLabel),
            ("label_key_slot_angle_step", "label_key_slot_angle_step", QtWidgets.QLabel),
            ("label_20", "label_20", QtWidgets.QLabel),
            ("label_21", "label_21", QtWidgets.QLabel),
            ("label_22", "label_22", QtWidgets.QLabel),
            ("label_24", "label_24", QtWidgets.QLabel),
            ("label_25", "label_25", QtWidgets.QLabel),
            ("label_groove_reduced_feed_start_x", "label_groove_reduced_feed_start_x", QtWidgets.QLabel),
            ("label_groove_reduced_feed", "label_groove_reduced_feed", QtWidgets.QLabel),
            ("label_groove_reduced_rpm", "label_groove_reduced_rpm", QtWidgets.QLabel),
            ("label_groove_step_a", "label_groove_step_a", QtWidgets.QLabel),
            ("label_groove_overlap", "label_groove_overlap", QtWidgets.QLabel),
            ("label_groove_retract", "label_groove_retract", QtWidgets.QLabel),
            ("label_groove_finish", "label_groove_finish", QtWidgets.QLabel),
            ("label_groove_sweep_feed", "label_groove_sweep_feed", QtWidgets.QLabel),
            ("label_groove_chip_amp", "label_groove_chip_amp", QtWidgets.QLabel),
            ("label_groove_chip_n", "label_groove_chip_n", QtWidgets.QLabel),
            ("label_30", "label_30", QtWidgets.QLabel),
            ("label_31", "label_31", QtWidgets.QLabel),
            ("label_key_coolant", "label_key_coolant", QtWidgets.QLabel),
            ("label_32", "label_32", QtWidgets.QLabel),
            ("label_33", "label_33", QtWidgets.QLabel),
            ("label_34", "label_34", QtWidgets.QLabel),
            ("label_35", "label_35", QtWidgets.QLabel),
            ("label_36", "label_36", QtWidgets.QLabel),
            ("label_37", "label_37", QtWidgets.QLabel),
            ("label_key_slot_width", "label_key_slot_width", QtWidgets.QLabel),
            ("label_key_cutting_width", "label_key_cutting_width", QtWidgets.QLabel),
            ("label_38", "label_38", QtWidgets.QLabel),
            ("label_39", "label_39", QtWidgets.QLabel),
            ("label_40", "label_40", QtWidgets.QLabel),
            ("label_41", "label_41", QtWidgets.QLabel),
            ("label_42", "label_42", QtWidgets.QLabel),
            ("label_43", "label_43", QtWidgets.QLabel),
        ]

        for attr, obj_name, cls in mapping:
            if getattr(self, attr, None) is not None:
                continue
            try:
                ui_ready = getattr(self.w, "ui_ready", False)
            except Exception:
                ui_ready = False
            if not ui_ready:
                # Panel not ready; defer the lookup until _finalize_ui_ready
                self._deferred_lookup_queue.append((attr, obj_name, cls, False))
                continue
            w = self._resolver.try_resolve(cls, obj_name, debug_context=True)
            if w is not None:
                setattr(self, attr, w)

    def _ensure_list_ops_type(self):
        if self.list_ops is not None and not isinstance(self.list_ops, QtWidgets.QListWidget):
            try:
                self.LOG.warning(
                    f"[LatheEasyStep] list_ops has wrong type: {_qname(self.list_ops)}; resetting to None"
                )
            except Exception:
                self._log(f"[LatheEasyStep] list_ops has wrong type: {_qname(self.list_ops)}; resetting to None", level="info")
            self.list_ops = None

    def _force_attach_core_widgets(self):
        """Robuste Suche nach Liste/Buttons direkt im Panel-Baum und erneutes Verbinden."""
        root = self._find_root_widget()
        search_roots = [root] if root else []

        def _grab(name: str, cls):
            for r in search_roots:
                obj = r.findChild(cls, name, QtCore.Qt.FindChildrenRecursively)
                if obj:
                    return obj
                obj = r.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
                if obj:
                    return obj
            return None

        self.list_ops = self.list_ops or _grab("listOperations", QtWidgets.QListWidget)
        self._ensure_list_ops_type()
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
                        if widget.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(widget):
                            pass
                        else:
                            return widget
                    elif _looks_like_panel_widget(widget):
                        return widget
                except Exception:
                    pass
                widget = widget.parentWidget()
            return None

        direct = getattr(self, "root_widget", None)
        if isinstance(direct, QtWidgets.QWidget):
            panel = _panel_from(direct)
            if panel is not None:
                return panel

        if isinstance(self.w, QtWidgets.QWidget):
            panel = _panel_from(self.w)
            if panel is not None:
                return panel
            for panel_name in PANEL_WIDGET_NAMES:
                try:
                    cand = self.w.findChild(QtWidgets.QWidget, panel_name, QtCore.Qt.FindChildrenRecursively)
                except Exception:
                    cand = None
                if cand is not None:
                    if cand.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(cand):
                        continue
                    return cand

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
        return None

    def _find_any_widget(self, obj_name: str):
        """Globale Suche per objectName in allen Widgets (embedded-sicher mit erweiterten Fallbacks)."""
        # Support lookup by numeric idx property: "id:34724" or just "34724"
        maybe_id = None
        try:
            if isinstance(obj_name, str):
                if obj_name.startswith("id:"):
                    maybe_id = obj_name.split(":", 1)[1]
                elif obj_name.isdigit():
                    maybe_id = obj_name
        except Exception:
            maybe_id = None
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

        for r in roots:
            if maybe_id is not None:
                try:
                    iid = int(maybe_id)
                    for w in r.findChildren(QtWidgets.QWidget, QtCore.Qt.FindChildrenRecursively):
                        try:
                            val = w.property("idx")
                            if val is None:
                                continue
                            if (isinstance(val, int) and val == iid) or (isinstance(val, str) and val.isdigit() and int(val) == iid):
                                return w
                        except Exception:
                            continue
                except Exception:
                    pass
            obj = r.findChild(QtCore.QObject, obj_name, QtCore.Qt.FindChildrenRecursively)
            if obj:
                return obj

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
                self._log(f"[LatheEasyStep] using '{name}' as program_unit combo", level="info")
                return obj

        self._log("[LatheEasyStep] no unit combo found via widgets", level="info")

        root = self.root_widget or self._find_root_widget()
        if root is not None:
            for combo in root.findChildren(QtWidgets.QComboBox):
                texts = [combo.itemText(i).strip().lower() for i in range(combo.count())]
                txt = " ".join(texts)
                if ("mm" in texts and ("inch" in texts or "in" in txt)) or (
                    "metric" in txt and "imperial" in txt
                ):
                    combo_name = combo.objectName() or "anonymous"
                    self._log(
                        f"[LatheEasyStep] using tree-scan combo '{combo_name}' as program_unit", level="info")
                    return combo

        return None

    def _find_shape_combo(self):
        """Find the stock-shape combo within the panel."""
        root = self.root_widget or self._find_root_widget()
        if root is None:
            return None

        explicit = root.findChild(QtWidgets.QComboBox, "program_shape", QtCore.Qt.FindChildrenRecursively)
        if explicit is not None:
            self.program_shape = explicit
            return explicit

        for combo in root.findChildren(QtWidgets.QComboBox):
            texts = [combo.itemText(i).strip().lower() for i in range(combo.count())]
            if any(t in texts for t in ("zylinder", "rohr", "rechteck", "n-eck")):
                self.program_shape = combo
                return combo

        return None

    def _rebuild_widget_name_cache(self):
        """Build an objectName cache for the current panel subtree."""
        root = self.root_widget or self._find_root_widget()
        cache: Dict[str, List[QtWidgets.QWidget]] = {}
        if root is not None:
            try:
                widgets = [root]
                widgets.extend(root.findChildren(QtWidgets.QWidget, QtCore.Qt.FindChildrenRecursively))
                for widget in widgets:
                    try:
                        obj_name = widget.objectName()
                    except Exception:
                        obj_name = ""
                    if not obj_name:
                        continue
                    cache.setdefault(obj_name, []).append(widget)
            except Exception:
                pass
        self._widget_name_cache = cache

    def _cache_named_widget(self, widget: QtWidgets.QWidget | None):
        if widget is None:
            return
        try:
            obj_name = widget.objectName()
        except Exception:
            obj_name = ""
        if not obj_name:
            return
        bucket = self._widget_name_cache.setdefault(obj_name, [])
        if widget not in bucket:
            bucket.append(widget)

    def _get_widget_by_name(self, name: str) -> QtWidgets.QWidget | None:
        """Robuste Widget-Auflösung mit erweiterten Fallbacks für embedded Panel.

        Wichtig: Für Parametereinsammeln muss das *richtige* Widget gefunden werden.
        Daher: erst exakte Matches, dann tolerante Matches (z.B. 'foo_2'), dabei
        bevorzugt Eingabewidgets (Spin/DoubleSpin/Combo/LineEdit/Check/Radio).
        """

        def _panel_scope_root() -> QtWidgets.QWidget | None:
            tab = getattr(self, "tab_params", None)
            if tab is None:
                try:
                    tab = getattr(self, "root_widget", None)
                    if tab is not None:
                        tab = tab.findChild(QtWidgets.QWidget, "tabParams", QtCore.Qt.FindChildrenRecursively)
                except Exception:
                    tab = None
            if tab is not None:
                probe = tab
                while probe is not None:
                    try:
                        has_tabs = probe.findChild(QtWidgets.QWidget, "tabParams", QtCore.Qt.FindChildrenRecursively) is not None
                        has_ops = probe.findChild(QtWidgets.QWidget, "listOperations", QtCore.Qt.FindChildrenRecursively) is not None
                        if has_tabs and has_ops:
                            return probe
                    except Exception:
                        pass
                    try:
                        probe = probe.parentWidget()
                    except Exception:
                        probe = None
            try:
                return getattr(self, "root_widget", None) or self._find_root_widget()
            except Exception:
                return None

        scope_root = _panel_scope_root()

        def _is_descendant_of_scope(w: QtWidgets.QWidget | None) -> bool:
            if w is None or scope_root is None:
                return False
            while w is not None:
                if w is scope_root:
                    return True
                try:
                    w = w.parentWidget()
                except Exception:
                    w = None
            return False

        # 1) direct attribute (fast path)
        widget_root = getattr(self, "w", None)
        widget = getattr(widget_root, name, None) if widget_root is not None else None
        if widget is not None and _is_descendant_of_scope(widget):
            return widget

        preferred_types = tuple(
            t for t in (
                getattr(QtWidgets, "QDoubleSpinBox", None),
                getattr(QtWidgets, "QSpinBox", None),
                getattr(QtWidgets, "QComboBox", None),
                getattr(QtWidgets, "QLineEdit", None),
                getattr(QtWidgets, "QCheckBox", None),
                getattr(QtWidgets, "QRadioButton", None),
                getattr(QtWidgets, "QAbstractButton", None),
                getattr(QtWidgets, "QTableWidget", None),
                getattr(QtWidgets, "QListWidget", None),
            )
            if t is not None
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
                panel_score = 0 if _is_descendant_of_scope(w) else 10
            except Exception:
                panel_score = 10
            return exact + suffix_ok + type_score + panel_score

        # Helper: check if a widget is inside our panel
        # (kept as separate method to avoid nested closure issues)
        if not hasattr(self, "_is_widget_in_our_panel"):
            def _is_widget_in_our_panel(w: QtWidgets.QWidget) -> bool:
                return _is_descendant_of_scope(w)
            self._is_widget_in_our_panel = _is_widget_in_our_panel  # type: ignore

        cached = getattr(self, "_widget_name_cache", {}).get(name, [])
        if cached:
            try:
                candidates = [w for w in cached if w is not None]
                if candidates:
                    candidates.sort(key=_score)
                    return candidates[0]
            except Exception:
                pass

        # 2) Exact match inside current root widget
        root = self.root_widget or self._find_root_widget()
        if root is not None:
            try:
                widget = root.findChild(QtWidgets.QWidget, name, QtCore.Qt.FindChildrenRecursively)
                if widget is not None:
                    self._cache_named_widget(widget)
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
                    self._cache_named_widget(candidates[0])
                    return candidates[0]
            except Exception:
                pass

        # 3) Heuristics for custom preview widgets or swapped objectNames
        # Some custom widgets (LathePreviewWidget) or nested UI files may use
        # alternative objectNames like 'previewContour' instead of 'contourPreview'.
        try:
            if root is not None:
                lname = (name or "").lower()
                # try common alternates: swap 'preview' <-> 'contour'
                alternates = set()
                if 'preview' in lname and 'contour' in lname:
                    alternates.add(lname.replace('preview', 'contour'))
                    alternates.add(lname.replace('contour', 'preview'))
                else:
                    if 'preview' in lname:
                        alternates.add(lname.replace('preview', 'contour'))
                    if 'contour' in lname:
                        alternates.add(lname.replace('contour', 'preview'))

                # scan only widgets inside the panel root
                for w in root.findChildren(QtWidgets.QWidget, QtCore.Qt.FindChildrenRecursively):
                    try:
                        on = (w.objectName() or "").lower()
                    except Exception:
                        on = ""
                    # objectName alternate match
                    if on and any(alt == on for alt in alternates):
                        return w

                    # class-name based detection for preview widgets
                    try:
                        # PyQt: metaObject().className() is reliable for custom widgets
                        clsname = ""
                        mo = getattr(w, 'metaObject', None)
                        if callable(mo):
                            try:
                                clsname = w.metaObject().className() or ""
                            except Exception:
                                clsname = w.__class__.__name__
                        else:
                            clsname = w.__class__.__name__
                        if clsname and 'lathepreview' in clsname.lower():
                            return w
                    except Exception:
                        pass
        except Exception:
            pass

        # 5) ENHANCED: Polling only after ui_ready (before that, deferred queue handles lookups).
        # This avoids spawning many timers during early embedded startup.
        try:
            ui_ready = bool(getattr(self.w, "ui_ready", False))
        except Exception:
            ui_ready = False
        if ui_ready:
            if not hasattr(self, "_deferred_widgets"):
                self._deferred_widgets = set()
            if name not in self._deferred_widgets:
                self._deferred_widgets.add(name)
                # Shorter polling window: 12 * 120ms ~= 1.44s (instead of 3s)
                QtCore.QTimer.singleShot(120, lambda: self._poll_for_widget(name, 12))

        return None
    
    def _poll_for_widget(self, name: str, attempts_left: int):
        """Pollt für ein Widget, das bei der ersten Suche nicht gefunden wurde."""
        if attempts_left <= 0:
            if getattr(self, "_verbose_widget_logs", False):
                self._log(f"[LatheEasyStep] gave up polling for widget '{name}'", level="debug")
            return
        
        # Try to find the widget again
        widget = self._find_widget_immediate(name)
        if widget is not None:
            # Found it! Set the attribute and connect signals if it's a button
            setattr(self, name, widget)
            if getattr(self, "_verbose_widget_logs", False):
                self._log(f"[LatheEasyStep] found deferred widget '{name}': {widget}", level="debug")
            
            # If it's a button, try to connect its signal
            if isinstance(widget, QtWidgets.QPushButton):
                self._connect_button_signal(widget, name)
            
            # Update UI state if needed
            self._update_ui_after_widget_found(name, widget)
            return
        
        # Not found yet, schedule next poll
        QtCore.QTimer.singleShot(120, lambda: self._poll_for_widget(name, attempts_left - 1))
    
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

        return None
    
    def _connect_button_signal(self, button: QtWidgets.QPushButton, name: str):
        """Verbindet das Signal eines gefundenen Buttons mit UniqueConnection-Schutz."""
        handler = None
        if name == "btnAdd":
            handler = self._handle_add_operation
        elif name == "btnDelete":
            handler = self._handle_delete_operation
        elif name == "btnMoveUp":
            handler = self._handle_move_up
        elif name == "btnMoveDown":
            handler = self._handle_move_down
        elif name == "btnNewProgram":
            handler = self._handle_new_program
        elif name == "btnGenerate":
            handler = self._handle_generate_gcode
        elif name == "btnSaveChanges":
            handler = self._handle_save_changes
        elif name == "btn_save_step":
            handler = self._handle_save_step
        elif name == "btn_load_step":
            handler = self._handle_load_step
        elif name == "btn_thread_preset":
            handler = self._apply_thread_preset_force
        elif name == "contour_add_segment":
            handler = self._handle_contour_add_segment
        elif name == "contour_delete_segment":
            handler = self._handle_contour_delete_segment
        elif name == "contour_move_up":
            handler = self._handle_contour_move_up
        elif name == "contour_move_down":
            handler = self._handle_contour_move_down
        
        if handler is None:
            return
        
        try:
            # Try UniqueConnection first to prevent double-binding
            button.clicked.connect(handler, QtCore.Qt.UniqueConnection)
            self._log(f"[LatheEasyStep] connected signal for deferred button '{name}' (UniqueConnection)", level="info")
        except TypeError:
            # Qt version may not support UniqueConnection; ignore
            self._log(f"[LatheEasyStep] UniqueConnection not supported for button '{name}', trying standard connect", level="debug")
        except Exception as e:
            self._log(f"[LatheEasyStep] failed to connect signal for button '{name}': {e}", level="error")
    
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
                'face_tool', 'thread_tool', 'groove_tool', 'drill_tool', 'parting_tool', 'key_tool',
                'contour_tool', 'taper_tool', 'boring_tool'
            }:
                self._populate_tool_combos(self._loaded_tools)
                self._update_tool_previews()
            if name in {
                'face_tool_img', 'thread_tool_img', 'groove_tool_img', 'drill_tool_img', 'parting_tool_img'
            }:
                self._update_tool_previews()
        except Exception as e:
            self._log(f"[LatheEasyStep] error updating UI after finding '{name}': {e}", level="error")
    
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
                    
            self._log("[LatheEasyStep] forced visibility updates for embedded mode", level="info")
        except Exception as e:
            self._log(f"[LatheEasyStep] error in force visibility updates: {e}", level="error")
    
    def _setup_slice_view(self):
        setup_slice_view(self)

    def _suggest_slice_z_for_preview(self, op: Operation | None = None) -> float | None:
        if op is None and self.preview is not None:
            op = getattr(self.preview, "front_operation", None)
        return default_slice_z_for_operation(op)

    def _ensure_slice_z_matches_operation(self, op: Operation | None) -> None:
        if self.preview is None or op is None:
            return
        suggested = self._suggest_slice_z_for_preview(op)
        if suggested is None:
            return
        if getattr(op, "op_type", None) == OpType.KEYWAY:
            bounds = keyway_slice_bounds(getattr(op, "params", {}) or {})
            if bounds is not None:
                current = float(getattr(self.preview, "slice_z", 0.0) or 0.0)
                if bounds[0] - 1e-6 <= current <= bounds[1] + 1e-6:
                    return
        try:
            self.preview.set_slice_z(suggested, emit=True)
        except Exception:
            pass

    def _on_toggle_slice_view(self, checked: bool):
        on_toggle_slice_view(self, checked)

    def _on_slice_changed(self, z_val: float):
        self._current_slice_z = float(z_val)
        self._sync_slice_widget()

    def _sync_slice_widget(self):
        sync_slice_widget(self)

    def initialized__(self):
        """Wird aufgerufen, wenn QtVCP die UI komplett aufgebaut hat."""
        self._startup_mark("initialized__ begin")
        root = self.root_widget or self._find_root_widget()
        if not _looks_like_panel_widget(root):
            search_hosts = [
                getattr(self, "w", None),
                getattr(self, "_main_window", None),
                root,
            ]
            for host in search_hosts:
                if not isinstance(host, QtWidgets.QWidget):
                    continue
                if _looks_like_panel_widget(host):
                    root = host
                    break
                for panel_name in PANEL_WIDGET_NAMES:
                    try:
                        cand = host.findChild(QtWidgets.QWidget, panel_name, QtCore.Qt.FindChildrenRecursively)
                    except Exception:
                        cand = None
                    if _looks_like_panel_widget(cand):
                        root = cand
                        break
                if _looks_like_panel_widget(root):
                    break
        if root is None:
            return
        self.w = root
        self.root_widget = root
        self._rebuild_widget_name_cache()

        # Ignore provisional embed instances that do not yet own the actual panel UI.
        if not _looks_like_panel_widget(root):
            return

        if self._startup_in_progress:
            return
        self._startup_in_progress = True
        self._schedule_startup_heartbeats()
        self._setup_slice_view()
        # Eindeutige "idx" Dynamic-Properties vergeben (unabhängig von Label-Texten).
        # Wenn eine Mapping-Datei 'widget_ids.json' vorhanden ist, verwenden
        # wir die numerischen IDs daraus; andernfalls setzen wir einen
        # Fallback-Wert (objectName) als idx, damit bestehende Logik weiter funktioniert.
        try:
            # lade optionales Mapping aus widget_ids.json
            import json
            import os
            mapping = {}
            mapping_path = None
            try:
                base = os.path.dirname(__file__)
                mapping_path = os.path.join(base, "widget_ids.json")
                if os.path.exists(mapping_path):
                    with open(mapping_path, "r", encoding="utf-8") as mf:
                        mapping = json.load(mf) or {}
                        # mapping expected as {"objectName": 34724, ...}
            except Exception:
                mapping = {}

            from PyQt5.QtWidgets import QWidget
            # Restrict the idx map to the panel subtree. Anonymous host-GUI
            # widgets must not be scanned or persisted here.
            try:
                all_widgets = list(self.w.findChildren(QWidget))
            except Exception:
                all_widgets = list(self.w.findChildren(QWidget))

            panel_names = {
                getattr(w, "objectName", lambda: "")() or ""
                for w in all_widgets
            }
            panel_names.discard("")

            # Determine start id (avoid clashing with any provided mapping)
            next_id = 10000
            try:
                existing_ids = [
                    int(v)
                    for k, v in mapping.items()
                    if k in panel_names and (isinstance(v, int) or (isinstance(v, str) and str(v).isdigit()))
                ]
                if existing_ids:
                    next_id = max(next_id, max(existing_ids) + 1)
            except Exception:
                pass

            # Persist only names that actually belong to the current panel.
            out_map = {
                k: v for k, v in mapping.items()
                if k in panel_names
            }

            for _w in all_widgets:
                try:
                    # Skip if widget already carries an idx property
                    cur = _w.property("idx")
                    if cur is not None:
                        continue
                    name = getattr(_w, "objectName", lambda: "")() or ""
                    if not name:
                        continue
                    if name in out_map:
                        wid = out_map[name]
                    else:
                        wid = next_id
                        next_id += 1
                        out_map[name] = wid
                    try:
                        _w.setProperty("idx", int(wid))
                    except Exception:
                        try:
                            _w.setProperty("idx", str(wid))
                        except Exception:
                            pass
                except Exception:
                    continue

            # Persist mapping back to widget_ids.json so future runs are stable
            try:
                if mapping_path:
                    with open(mapping_path, "w", encoding="utf-8") as mf:
                        json.dump(out_map, mf, indent=2, ensure_ascii=False)
            except Exception:
                pass
        except Exception:
            pass

        # Jetzt ist die Widget-Hierarchie sicher fertig -> Combos suchen

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
            self._log(
                f"[LatheEasyStep] retract combo found: "
                f"{self.program_retract_mode.objectName()}, "
                f"items={items}, "
                f"current='{self.program_retract_mode.currentText()}'", level="info")
            # Signal hier (spät) sicher verbinden
            self.program_retract_mode.currentIndexChanged.connect(self._handle_global_change)
        else:
            pass

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

        # PATCH: If the UI does not provide dedicated face_* widgets, reuse contour_* widgets.
        # This fixes "keine/fase/radius" switching and enables the edge size input for facing.
        if self.face_edge_type is None and getattr(self, "contour_edge_type", None) is not None:
            self.face_edge_type = self.contour_edge_type
        if getattr(self, "face_edge_size", None) is None and getattr(self, "contour_edge_size", None) is not None:
            self.face_edge_size = self.contour_edge_size
        if getattr(self, "face_edge_size_lbl", None) is None and getattr(self, "contour_edge_size_lbl", None) is not None:
            self.face_edge_size_lbl = self.contour_edge_size_lbl

        # einmal initial anwenden
        QtCore.QTimer.singleShot(0, self._apply_unit_suffix)
        QtCore.QTimer.singleShot(0, self._update_program_visibility)
        QtCore.QTimer.singleShot(0, self._update_retract_visibility)
        QtCore.QTimer.singleShot(0, self._update_subspindle_visibility)
        QtCore.QTimer.singleShot(0, self._update_face_visibility)
        QtCore.QTimer.singleShot(0, self._auto_load_tool_table)
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
            self._log("[LatheEasyStep] unit polling timer started", level="info")
        else:
            pass
        self._startup_mark("initialized__ end")

        # Jetzt sicherstellen, dass die Preview-Widgets referenziert sind
        # Die teuren Panel-Initialisierungen laufen gesammelt in
        # _finalize_ui_ready(), damit sie im Embed-Fall nicht doppelt laufen.
        # The embedded panel is started in a host environment (QTvcp embed).
        # Depending on timing, the first initialized__ can run before *all* widgets
        # are fully realized / named, so we do a few delayed passes.
        # The _finalize_ui_ready method has an early-out guard (_ui_finalized)
        # so subsequent timers are essentially no-ops once all critical widgets are found.
        QtCore.QTimer.singleShot(0, self._finalize_ui_ready)
        QtCore.QTimer.singleShot(500, self._finalize_ui_ready)
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
        finalize_ui_ready(self)

    def _schedule_post_start_init(self):
        """Disabled: startup follow-up work must happen lazily on demand."""
        self._post_start_init_scheduled = True
        self._post_start_init_done = True
        self._post_start_init_steps = []
        self._startup_mark("post_start_init disabled")

    def _post_start_init(self):
        """Deferred startup work that should not block the visible panel startup."""
        if getattr(self, "_post_start_init_done", False):
            return
        try:
            steps = getattr(self, "_post_start_init_steps", [])
            if not steps:
                self._post_start_init_done = True
                self._startup_mark("post_start_init complete")
                return
            step = steps.pop(0)
            self._startup_mark(f"post_start_init step {getattr(step, '__name__', 'unknown')} begin")
            step()
            self._startup_mark(f"post_start_init step {getattr(step, '__name__', 'unknown')} end")
        except Exception:
            pass
        if getattr(self, "_post_start_init_steps", []):
            QtCore.QTimer.singleShot(120, self._post_start_init)
        else:
            self._post_start_init_done = True
            self._startup_mark("post_start_init complete")

    def _post_start_init_step_prepare_signals(self):
        self._setup_param_maps()
        self._prepare_signal_connection_context()
        self._connect_resolver_fallbacks()

    def _post_start_init_step_param_signals(self):
        self._connect_param_change_signals()

    def _post_start_init_step_global_signals(self):
        self._connect_global_form_signals()

    def _post_start_init_step_language_signal(self):
        self._connect_language_signal()

    def _post_start_init_step_mode_signals(self):
        self._connect_mode_visibility_signals()

    def _post_start_init_step_live_update_signals(self):
        self._connect_tool_preview_signals()
        self._connect_live_update_signals()

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
        if getattr(self, "_verbose_widget_logs", False):
            try:
                names = []
                for c in candidates:
                    parent = c.parentWidget()
                    names.append(
                        f"{c.objectName()} vis={c.isVisible()} score={_score_table(c)} parent={parent.objectName() if parent else None}"
                    )
                self._log(f"[LatheEasyStep][debug] contour table candidates: {names}, chosen={getattr(self.contour_segments, 'objectName', lambda: None)() if self.contour_segments else None}", level="debug")
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
                self._log(f"[LatheEasyStep] _apply_thread_preset: profile={profile}, pitch={p}, changed={changed}", level="info")
            except Exception:
                pass
        finally:
            self._thread_applying_standard = False

    def _apply_thread_preset_force(self):
        """Handler: Preset hart anwenden (Button)."""
        try:
            self._log("[LatheEasyStep] btn_thread_preset clicked: applying preset force", level="info")
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
            self._log("[LatheEasyStep] debug: no root widget", level="debug")
            return
        btns = [w.objectName() for w in root.findChildren(QtWidgets.QPushButton)]
        lists = [w.objectName() for w in root.findChildren(QtWidgets.QListWidget)]
        self._log(f"[LatheEasyStep] debug root: {root.objectName()}", level="debug")
        self._log(f"[LatheEasyStep] debug buttons: {btns}", level="debug")
        self._log(f"[LatheEasyStep] debug list widgets: {lists}", level="debug")

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
        ensure_core_widgets(self)

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
            self._log(f"[LatheEasyStep] unit changed (poll) idx={idx}", level="info")
            self._apply_unit_suffix()
            self._update_program_visibility()
            self._update_retract_visibility()
            self._update_subspindle_visibility()
            self._update_face_visibility()

    # ---- Parameter-Mapping --------------------------------------------
    def _setup_param_maps(self):
        # Compatibility note for brittle source-level tests:
        # "finish_allow_x": self._get_widget_by_name("parting_finish_allow_x")
        # "finish_allow_z": self._get_widget_by_name("parting_finish_allow_z")
        setup_param_maps(self)

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
            if self.list_ops:
                row = self.list_ops.currentRow()
        except Exception:
            row = -1
        if row < 0:
            try:
                self._refresh_preview()
            except Exception:
                pass
            return
        try:
            self._update_selected_operation(force=True)
        except Exception as e:
            self._log(f"[LatheEasyStep] _on_param_changed: update failed: {e}", level="error")

    def _connect_signals(self):
            self._prepare_signal_connection_context()
            self._connect_core_signals()
            self._connect_resolver_fallbacks()
            self._connect_tool_preview_signals()
            self._connect_param_change_signals()
            self._connect_global_form_signals()
            self._connect_language_signal()
            self._connect_mode_visibility_signals()
            self._connect_live_update_signals()

    def _prepare_signal_connection_context(self):
            prepare_signal_connection_context(self)

    def _connect_resolver_fallbacks(self):
            connect_resolver_fallbacks(self)

    def _connect_tool_preview_signals(self):
            connect_tool_preview_signals(self)

    def _connect_param_change_signals(self):
            connect_param_change_signals(self)

    def _connect_global_form_signals(self):
            connect_global_form_signals(self)

    def _connect_language_signal(self):
            connect_language_signal(self)

    def _connect_mode_visibility_signals(self):
            connect_mode_visibility_signals(self)

    def _connect_live_update_signals(self):
            for w in [
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

    def _connect_list_ops_signals(self):
            connect_list_ops_signals(self)

    def _connect_core_signals(self):
            connect_core_signals(self)



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
            # Schutz für Embedded-Mode: generische Qt-Labelnamen wie label_32,
            # label_38 etc. kollidieren häufig mit Host-GUI-Widgets (z. B.
            # QtDragon Tool-Info). Diese Namen daher grundsätzlich nicht
            # automatisch überschreiben.
            if re.match(r"^label_\d+$", str(name or "")):
                continue
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
                    # Qt version may not support UniqueConnection; skip further connect attempt
                    connected = True  # Mark as attempted to avoid retry
                except Exception:
                    pass
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
        return available_contour_names(self)

    def _current_parting_contour_name(self) -> str:
        return current_parting_contour_name(self)

    def _debug_contour_state(self, context: str = ""):
        debug_contour_state(self, context)

    def _resolve_contour_path(self, contour_name: str) -> List[Tuple[float, float]]:
        return resolve_contour_path(self, contour_name)

    def _update_parting_contour_choices(self):
        update_parting_contour_choices(self)

    def _update_parting_ready_state(self, *args, **kwargs):
        update_parting_ready_state(self, *args, **kwargs)

    def _update_parting_mode_visibility(self):
        update_parting_mode_visibility(self)

    def _handle_tab_changed(self, *_args, **_kwargs):
        handle_tab_changed(self, *_args, **_kwargs)

    def _find_operation_index_by_type(self, op_type: str) -> int:
        for idx, op in enumerate(getattr(self.model, "operations", []) or []):
            if getattr(op, "op_type", None) == op_type:
                return idx
        return -1

    def _select_operation_for_current_tab(self, op_type: str) -> None:
        if self.list_ops is None:
            return
        current_idx = self.list_ops.currentRow()
        if 0 <= current_idx < len(self.model.operations):
            current_op = self.model.operations[current_idx]
            if getattr(current_op, "op_type", None) == op_type:
                return
        target_idx = self._find_operation_index_by_type(op_type)
        if target_idx < 0:
            return
        self.list_ops.blockSignals(True)
        try:
            self.list_ops.setCurrentRow(target_idx)
        finally:
            self.list_ops.blockSignals(False)
        self._handle_selection_change(target_idx)

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
        self._setup_param_maps()
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
        elif op_type == OpType.KEYWAY:
            defaults = {
                "tool": 1,
                "feed": 200.0,
                "plunge_feed": 200.0,
                "slot_count": 1,
                "slot_start_angle": 0.0,
                "slot_angle_step": 0.0,
                "slot_width": 3.0,
                "cutting_width": 3.0,
                "top_clearance": 1.0,
                "depth_per_pass": 0.1,
                "mode": 0,
                "radial_side": 0,
                "coolant": 0,
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
        if getattr(self, "program_machine_profile", None) is None:
            self.program_machine_profile = self._get_widget_by_name("program_machine_profile")
        if getattr(self, "program_chuck_size", None) is None:
            self.program_chuck_size = self._get_widget_by_name("program_chuck_size")
        if getattr(self, "program_chuck_part_type", None) is None:
            self.program_chuck_part_type = self._get_widget_by_name("program_chuck_part_type")
        if getattr(self, "program_chuck_grip_mode", None) is None:
            self.program_chuck_grip_mode = self._get_widget_by_name("program_chuck_grip_mode")
        if getattr(self, "program_chuck_profile", None) is None:
            self.program_chuck_profile = self._get_widget_by_name("program_chuck_profile")
        if getattr(self, "program_chuck_x_min", None) is None:
            self.program_chuck_x_min = self._get_widget_by_name("program_chuck_x_min")
        if getattr(self, "program_chuck_x_max", None) is None:
            self.program_chuck_x_max = self._get_widget_by_name("program_chuck_x_max")
        if getattr(self, "program_chuck_z_limit", None) is None:
            self.program_chuck_z_limit = self._get_widget_by_name("program_chuck_z_limit")
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
        if getattr(self, "program_machine_profile", None):
            header["machine_profile"] = self.program_machine_profile.currentText().strip()
        if getattr(self, "program_chuck_size", None):
            header["chuck_size"] = self.program_chuck_size.currentText().strip()
        if getattr(self, "program_chuck_part_type", None):
            header["chuck_part_type"] = self.program_chuck_part_type.currentText().strip()
        if getattr(self, "program_chuck_grip_mode", None):
            header["chuck_grip_mode"] = self.program_chuck_grip_mode.currentText().strip()
        if getattr(self, "program_chuck_profile", None):
            header["chuck_profile"] = self.program_chuck_profile.currentText().strip()
        header["chuck_no_go_x_min"] = _val(getattr(self, "program_chuck_x_min", None))
        header["chuck_no_go_x_max"] = _val(getattr(self, "program_chuck_x_max", None))
        header["chuck_no_go_z_limit"] = _val(getattr(self, "program_chuck_z_limit", None))

        if self.program_name:
            header["program_name"] = self.program_name.text().strip()

        # Drehzahlbegrenzung (S3 nur, wenn Gegenspindel aktiv)
        header["has_subspindle"] = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
        header["s1_max"] = float(self.program_s1.value()) if self.program_s1 else 0.0
        if header["has_subspindle"]:
            header["s3_max"] = float(self.program_s3.value()) if self.program_s3 else 0.0
        else:
            header["s3_max"] = 0.0

        cached = getattr(self, "_program_header_cache", None)
        if isinstance(cached, dict):
            merged = dict(cached)
            for key, value in header.items():
                if value is None:
                    continue
                if isinstance(value, str) and value == "":
                    continue
                merged[key] = value
            header = merged

        self._program_header_cache = dict(header)
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
        load_operation_params_to_form(self, op)

    def _load_program_header_to_form(self, params: Dict[str, object]):
        if not isinstance(params, dict):
            return
        self._program_header_cache = dict(params)
        self._collect_program_header()
        apply_program_header_to_handler(
            self,
            params,
            apply_chuck_preset_if_missing=False,
        )

    def _set_preview_paths(
        self,
        paths: List[List[Tuple[float, float]]],
        active_index: int | None = None,
        include_contour_preview: bool = True,
        program_context: Dict[str, object] | None = None,
        active_operation: Operation | None = None,
    ) -> None:
        """Aktualisiert Haupt- und optional den Kontur-Tab-Preview."""
        apply_preview_paths(
            self,
            paths,
            active_index=active_index,
            include_contour_preview=include_contour_preview,
            program_context=program_context,
            active_operation=active_operation,
        )

    def _refresh_preview(self):
        refresh_preview(
            self,
            build_contour_path=build_contour_path,
            build_face_path=build_face_path,
            build_thread_path=build_thread_path,
            build_groove_preview_path=build_groove_preview_path,
            build_drill_path=build_drill_path,
            build_keyway_path=build_keyway_path,
            build_abspanen_path=build_abspanen_path,
            build_stock_outline=build_stock_outline,
            build_retract_primitives=build_retract_primitives,
            build_worklimit_primitives=build_worklimit_primitives,
            build_chuck_nogo_primitives=build_chuck_nogo_primitives,
        )

    def _refresh_operation_list(self, select_index: int | None = None):
        """Synchronisiert die linke Operationsliste mit dem internen Modell."""
        if self.list_ops is not None:
            try:
                if self.list_ops.objectName() not in ("listOperations", "list_ops"):
                    self.list_ops = None
            except Exception:
                self.list_ops = None

        if self.list_ops is None:
            root = self.root_widget or self._find_root_widget()
            if root:
                for w in root.findChildren(QtWidgets.QListWidget):
                    if w.objectName() in ("listOperations", "list_ops"):
                        self.list_ops = w
                        break

        if self.list_ops is None:
            self._update_parting_contour_choices()
            return

        # Nur die Operations-Liste updaten (nicht andere QListWidgets).
        for lst in [self.list_ops]:
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
                if getattr(self, "_verbose_widget_logs", False):
                    items = [lst.item(i).text() for i in range(lst.count())]
                    self._log(
                        f"[LatheEasyStep][debug] list '{lst.objectName()}' "
                        f"count={lst.count()} items={items} vis={lst.isVisible()} "
                        f"size={lst.size()}", level="debug")
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
                # Zum selektierten Step scrollen, nicht immer ans Ende.
                sel_item = lst.item(lst.currentRow())
                if sel_item:
                    lst.scrollToItem(sel_item)
                elif lst.count() > 0:
                    lst.scrollToBottom()
            except Exception:
                pass

        self._update_parting_contour_choices()

    def _ensure_preview_widgets(self):
        ensure_preview_widgets(self, LathePreviewWidget, QtWidgets.QWidget)
    def _mark_operation_user_selected(self, *args, **kwargs):
        self._op_row_user_selected = True

    def _sync_form_to_operation(self, idx: int) -> None:
        sync_form_to_operation(self, idx)

    def _update_selected_operation(self, *, force: bool = False):
        if self.list_ops is None:
            return
        if not force and not self._op_row_user_selected:
            return
        idx = self.list_ops.currentRow()
        if idx < 0 or idx >= len(self.model.operations):
            return
        op = self.model.operations[idx]
        self._sync_form_to_operation(idx)
        self._refresh_preview()
        if op.op_type == OpType.CONTOUR:
            self._update_parting_contour_choices()

    # ---- Button-Handler -----------------------------------------------
    def _handle_add_operation(self):
        # Sicherheitsnetz: Widgets nachziehen, falls sie erst später verfügbar sind
        self._ensure_core_widgets()
        self._force_attach_core_widgets()
        if not self.tools:
            try:
                self._auto_load_tool_table()
            except Exception:
                pass
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
                self._log("[LatheEasyStep] add operation triggered", level="info")
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
                        self._log("[LatheEasyStep] Abspanen benötigt eine vorhandene Kontur-Auswahl", level="info")
                        self._update_parting_ready_state()
                        return
                    params["contour_name"] = contour_name
                    params["source_path"] = contour_path
                op = Operation(op_type, params)
                self.model.update_geometry(op)
                parent = self.root_widget or self._find_root_widget()
                settings = QtCore.QSettings()
                next_index = len(self.model.operations)
                if any(existing.op_type == OpType.PROGRAM_HEADER for existing in self.model.operations):
                    next_index += 1
                if not self._ensure_step_file_link(
                    op,
                    index_hint=next_index,
                    parent=parent,
                    settings=settings,
                ):
                    self._log("[LatheEasyStep] add operation cancelled: no step file selected", level="info")
                    return
                self.model.add_operation(op)
                try:
                    debug_ops = [f"{i}:{o.op_type}" for i, o in enumerate(self.model.operations)]
                    self._log(f"[LatheEasyStep][debug] operations now: {debug_ops}", level="debug")
                except Exception:
                    pass

                self._refresh_operation_list(select_index=len(self.model.operations) - 1)
                self._refresh_preview()
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
            self._log(
                f"[LatheEasyStep] delete: currentRow={idx}, "
                f"ops_count={len(self.model.operations)}",
                level="info",
            )
            if idx < 0 or idx >= len(self.model.operations):
                return
            if idx == 0:
                parent = self.root_widget or self._find_root_widget()
                QtWidgets.QMessageBox.warning(parent, "Löschen", "Der Programmkopf kann nicht gelöscht werden.")
                return
            self.model.remove_operation(idx)
            new_idx = min(idx, len(self.model.operations) - 1)
            self._refresh_operation_list(select_index=new_idx)
            self._refresh_preview()
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
        return operation_to_step_data(op)

    def _step_data_to_operation(self, data: Dict[str, object]) -> Operation | None:
        return step_data_to_operation(data)

    def _rebuild_all_operation_geometry(self) -> None:
        """Rebuild derived preview geometry from params for all operations.

        Stored `path` data in save files is only cached preview geometry.
        After preview logic changes, loaded programs must be regenerated from
        the authoritative parameters to avoid stale or mismatched contours.
        """
        if not getattr(self, "model", None):
            return

        for op in self.model.operations:
            if op.op_type == OpType.PROGRAM_HEADER:
                op.path = []
                continue
            if op.op_type == OpType.ABSPANEN:
                contour_name = str(op.params.get("contour_name") or "")
                op.params["source_path"] = self._resolve_contour_path(contour_name)
            try:
                self.model.update_geometry(op)
            except Exception as exc:
                self._log(f"[LatheEasyStep] geometry rebuild failed for {op.op_type}: {exc}", level="warning")

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
        self._handle_selection_change(idx)

    def _build_program_data(self) -> Dict[str, object]:
        return build_program_data(self)

    def _write_program_file(self, file_path: str) -> None:
        write_program_file(self, file_path)

    def _build_gcode_lines(self) -> List[str]:
        return build_gcode_lines(self)

    def _write_gcode_file(self, file_path: str) -> None:
        write_gcode_file(self, file_path)

    def _handle_save_step(self):
        handle_save_step(self, step_file_filter=STEP_FILE_FILTER)

    def _operation_side_hint(self, op: Operation) -> str | None:
        self.OpType = OpType
        return operation_side_hint(self, op)

    def _tool_comment_side_hint(self, comment: str) -> str | None:
        return tool_comment_side_hint(self, comment)

    def _tool_orientation_mismatch(self, op: Operation) -> str | None:
        return tool_orientation_mismatch(self, op)

    def _collect_tool_orientation_warnings(self) -> List[str]:
        return collect_tool_orientation_warnings(self)

    def _radius_warning_details(self) -> List[Dict[str, object]]:
        self.OpType = OpType
        return radius_warning_details(self)

    def _handle_load_step(self):
        handle_load_step(self, step_file_filter=STEP_FILE_FILTER)

    def _handle_save_program(self):
        handle_save_program(self)

    def _handle_load_program(self):
        handle_load_program(self)

    def _handle_save_changes(self):
        handle_save_changes(self)

    def _apply_header_to_ui(self, header: Dict[str, object]):
        """Setzt Header-Werte in UI-Widgets."""
        if isinstance(header, dict):
            self._program_header_cache = dict(header)
        apply_program_header_to_handler(
            self,
            header,
            apply_chuck_preset_if_missing=True,
        )

    def _on_step_double_clicked(self, item):
        on_step_double_clicked(self, item)

    def _handle_move_up(self):
        handle_move_up(self)

    def _handle_move_down(self):
        handle_move_down(self)

    def _init_contour_table(self):
        init_contour_table(self)

    # ---- Kontur: Segment-Tabelle --------------------------------------
    def _handle_contour_add_segment(self):
        handle_contour_add_segment(self)

    def _handle_contour_delete_segment(self):
        handle_contour_delete_segment(self)

    def _handle_contour_move_up(self):
        handle_contour_move_up(self)

    def _handle_contour_move_down(self):
        handle_contour_move_down(self)

    def _handle_contour_table_change(self, *args, **kwargs):
        handle_contour_table_change(self, *args, **kwargs)

    def _handle_contour_row_select(self, *args, **kwargs):
        handle_contour_row_select(self, *args, **kwargs)

    def _handle_contour_edge_change(self, *args, **kwargs):
        handle_contour_edge_change(self, *args, **kwargs)

    def _update_contour_preview_temp(self):
        update_contour_preview_temp(self)

    def _sync_contour_edge_controls(self):
        sync_contour_edge_controls(self)

    def _handle_new_program(self):
        handle_new_program(self)

    def _handle_generate_gcode(self):
        return handle_generate_gcode(self)

    def _handle_load_tool_table(self):
        handle_load_tool_table(self)

    def _auto_load_tool_table(self):
        auto_load_tool_table(self)

    def _parse_tool_table(self, filepath: str) -> tuple[Dict[int, Tool], List[int]]:
        """Parse LinuxCNC tool table file and return structured tool info plus ISO warnings."""
        return parse_tool_table(filepath, log=self._log)

    def _extract_iso_from_comment(self, comment: str) -> tuple[str | None, str | None, float | None]:
        return extract_iso_from_comment(comment)

    def _tool_kind_from_orientation(self, orientation: int | None) -> str:
        return tool_kind_from_orientation(orientation)

    def _populate_tool_combos(self, tools: Dict[int, Tool]):
        populate_tool_combos(self, tools)

    def _tool_combo_label(self, tool: Tool, max_comment: int = 32) -> str:
        return tool_combo_label(self, tool, max_comment)

    def _ensure_tool_preview_widgets(self):
        ensure_tool_preview_widgets(self)

    def _style_tool_preview_label(self, img_label: QtWidgets.QLabel):
        style_tool_preview_label(self, img_label)

    def _render_tool_placeholder(self, text: str) -> QtGui.QPixmap:
        return render_tool_placeholder(self, text)

    def _tool_number_from_combo(self, combo: QtWidgets.QComboBox | None) -> int:
        return tool_number_from_combo(self, combo)

    def _reposition_tool_preview_widgets(self):
        reposition_tool_preview_widgets(self)

    def _update_tool_previews(self):
        update_tool_previews(self)

    def _ensure_tool_preview_calibration_controls(self):
        ensure_tool_preview_calibration_controls(self)

    def _apply_tool_preview_calibration_settings_to_controls(self):
        offset_widget = getattr(self, "tool_preview_orient_offset", None)
        mirror_widget = getattr(self, "tool_preview_orient_mirror", None)
        apply_tool_preview_calibration_settings_to_controls(self, offset_widget, mirror_widget)

    def _on_tool_preview_calibration_changed(self):
        on_tool_preview_calibration_changed(self)

    def _render_tool_preview(self, tool: Tool) -> QtGui.QPixmap:
        return render_tool_preview(self, tool)

    def _infer_insert_shape_key(self, tool: Tool) -> str:
        self._INSERT_SHAPE_KEYS = _INSERT_SHAPE_KEYS
        return infer_insert_shape_key(self, tool)

    def _infer_insert_profile(self, tool: Tool) -> Dict[str, object]:
        return infer_insert_profile(self, tool)

    def _build_insert_geometry(
        self,
        shape_key: str,
        insert_size: float,
        family: str = "turning",
        handed: str = "neutral",
        groove_width_mm: float = 0.0,
    ) -> tuple[QtGui.QPolygonF | None, float]:
        return build_insert_geometry(self, shape_key, insert_size, family, handed, groove_width_mm)

    def _tool_orientation_angle(self, orientation: int | None) -> float:
        return tool_orientation_angle(self, orientation)

    def _tool_holder_angle(self, orientation: int | None, family: str, handed: str) -> float:
        return tool_holder_angle(self, orientation, family, handed)

    def _build_program_filepath(self, name_raw: str | None) -> str:
        return build_program_filepath(self, name_raw)

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
        handle_selection_change(self, row)


    def _handle_global_change(self, *args, **kwargs):
        handle_global_change(self, *args, **kwargs)

    def _apply_machine_profile_preset(self) -> None:
        self.MACHINE_CHUCK_PROFILE_PRESETS = MACHINE_CHUCK_PROFILE_PRESETS
        apply_machine_profile_preset(self)

    def _chuck_size_mm(self) -> int:
        return chuck_size_mm(self)

    def _apply_chuck_safety_preset(self) -> None:
        self.CHUCK_PRESETS = CHUCK_PRESETS
        self.CHUCK_PROFILE_MODIFIERS = CHUCK_PROFILE_MODIFIERS
        apply_chuck_safety_preset(self)

    # ---- Form-Optik ---------------------------------------------------
    def _apply_unit_suffix(self):
        apply_unit_suffix(self)

    def _update_program_visibility(self, shape=None):
        update_program_visibility(self, shape)

    def _update_retract_visibility(self, widget=None, mode_in=None):
        update_retract_visibility(self, widget, mode_in)

    def _update_subspindle_visibility(self, *args, **kwargs):
        update_subspindle_visibility(self, *args, **kwargs)

    def _update_face_visibility(self):
        update_face_visibility(self)

    def _update_drill_visibility(self):
        update_drill_visibility(self)

    def _describe_operation(self, op, number=None):
        return describe_operation(self, op, number)
    def _renumber_operations(self):
        renumber_operations(self)

    # ---- QtVCP user command hook (leer) -------------------------------
    def call_user_command_(self, command_file: str | None):
        # Wird von QtVCP erwartet, hier aber bewusst leer gehalten.
        return



    def _setup_groove_tab_ui(self):
        setup_groove_tab_ui(self)

    def _update_groove_tab_ui(self):
        update_groove_tab_ui(self)

    def _render_groove_diagrams(self):
        render_groove_diagrams(self)


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
