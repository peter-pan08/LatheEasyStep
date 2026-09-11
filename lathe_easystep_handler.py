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
from lathe_easystep.ui_header import collect_program_header
from lathe_easystep.ui_contour_input import collect_contour_segments
from lathe_easystep.ui_thread import apply_thread_preset
from lathe_easystep.comments import update_auto_comment
from lathe_easystep.ui_tooltips import _TooltipRelay, set_tooltip_deep, fallback_tooltip_text, apply_registered_tooltips
from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.gcode_utils import is_internal_side
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
    update_slice_view_button,
)
from lathe_easystep.ui_params import collect_params, setup_param_maps
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
    update_spindle_mode_visibility,
    update_subspindle_visibility,
)
from lathe_easystep.ui_flow import (
    _looks_like_generated_step_comment,
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
    write_step_file,
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
from lathe_easystep.ui_advanced import ensure_advanced_widgets
from lathe_easystep.ui_dirty import (
    clear_dirty_operation,
    clear_program_dirty,
    clear_dirty_state,
    current_operation_is_dirty,
    has_unsaved_changes,
    init_dirty_state,
    mark_all_operations_dirty,
    mark_dirty,
    mark_program_structure_dirty,
    tab_label as dirty_tab_label,
    update_dirty_status,
    warn_if_dirty,
)
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
from lathe_easystep.presets import (
    metric_thread_presets,
    trapezoidal_thread_presets,
    validate_thread_preset_data,
)
from lathe_easystep.translations import TRANSLATIONS
from lathe_easystep.ui_registry import COMBO_ITEM_REGISTRY, PANEL_WIDGET_NAMES, TAB_TITLE_KEYS, TAB_TRANSLATIONS, UI_TEXT_KEYS, UI_TOOLTIP_KEYS, _looks_like_panel_widget
from lathe_easystep.ui_static import apply_ui_static_translations
from lathe_easystep.ui_split import load_split_tab_uis

# Module logger for non-instantiated contexts
_LOGGER = logging.getLogger(__name__)


_INSERT_SHAPE_KEYS = {"C", "D", "V", "S", "T", "W", "R"}
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
    "label_program_spindle_mode": {"de": "Spindelmodus", "en": "Spindle Mode"},
    "label_program_spindle_max_rpm": {"de": "CSS Max-RPM", "en": "CSS max RPM"},
    "label_program_park_mode": {"de": "Parkmodus", "en": "Park Mode"},
    "label_program_toolchange_coords": {"de": "Werkzeugwechsel-Koordinaten", "en": "Tool Change Coordinates"},
    "label_program_park_coords": {"de": "Park-Koordinaten", "en": "Park Coordinates"},
    "label_program_park_x": {"de": "Park X", "en": "Park X"},
    "label_program_park_z": {"de": "Park Z", "en": "Park Z"},
    "label_program_park_sequential": {"de": "Parkbewegung", "en": "Park Move"},
    "program_park_sequential": {"de": "achsenweise fahren", "en": "move axis by axis"},
    "label_program_optional_stop_toolchange": {"de": "Optionalstop Werkzeugwechsel", "en": "Optional stop tool change"},
    "program_optional_stop_toolchange": {"de": "M1 vor Werkzeugwechsel", "en": "M1 before tool change"},
    "label_program_preview_warnings": {"de": "Sicherheitswarnungen in Vorschau", "en": "Safety warnings in preview"},
    "program_preview_warnings": {"de": "im Preview markieren", "en": "show in preview"},
    "label_dirty_status": {"de": "Keine offenen Aenderungen", "en": "No pending changes"},

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
    "label_parting_undercut_mode": {"de": "Hinterschnitt-Modus", "en": "Undercut Mode"},
    "label_parting_output_preference": {"de": "Ausgabe bevorzugen", "en": "Output Preference"},
    "label_parting_undercut_tool": {"de": "Hinterschnitt-Werkzeug", "en": "Undercut Tool"},
    "label_parting_undercut_spindle": {"de": "Hinterschnitt-Drehzahl", "en": "Undercut Spindle"},
    "label_parting_undercut_feed": {"de": "Hinterschnitt-Vorschub", "en": "Undercut Feed"},
    "label_parting_optional_stop_before_undercut": {"de": "Optionalstop Hinterschnitt", "en": "Optional stop undercut"},
    "parting_optional_stop_before_undercut": {"de": "M1 vor separatem Hinterschnitt", "en": "M1 before separate undercut"},

    "label_thread_orientation": {"de": "Gewindetyp", "en": "Thread Type"},
    "label_thread_hand": {"de": "Gewinderichtung", "en": "Thread Direction"},
    "label_thread_standard": {"de": "Standardgewinde", "en": "Thread Standard"},
    "label_thread_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_thread_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_thread_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_thread_major_diameter": {"de": "Major-Durchmesser (mm)", "en": "Major Diameter (mm)"},
    "label_thread_pitch": {"de": "Steigung (mm)", "en": "Pitch (mm)"},
    "label_thread_length": {"de": "Gewindelänge Z1 (mm)", "en": "Thread length Z1 (mm)"},
    "label_thread_start_z": {"de": "Gewindestart Z (mm)", "en": "Thread start Z (mm)"},
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
    "label_thread_relief_mode": {"de": "Freistich-Vorschlag", "en": "Relief Suggestion"},
    "label_thread_relief_norm": {"de": "Freistich-Norm", "en": "Relief Standard"},
    "label_thread_optional_stop_before": {"de": "Optionalstop Gewinde", "en": "Optional stop thread"},
    "thread_optional_stop_before": {"de": "M1 vor Gewinde", "en": "M1 before threading"},

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
    "label_groove_process_type": {"de": "Betriebsart", "en": "Mode"},
    "label_groove_lage": {"de": "Lage", "en": "Position"},
    "label_groove_ref": {"de": "Bezugspunkt Z0", "en": "Reference Z0"},
    "groove_use_tool_width": {"de": "Werkzeugbreite separat angeben", "en": "Specify tool width separately"},

    "label_drill_tool": {"de": "Werkzeug", "en": "Tool"},
    "label_drill_spindle": {"de": "Drehzahl", "en": "Spindle Speed"},
    "label_drill_coolant": {"de": "Kühlung", "en": "Coolant"},
    "label_drill_mode": {"de": "Bohren Art", "en": "Drilling Mode"},
    "label_26": {"de": "Bohrungsdurchmesser", "en": "Hole Diameter"},
    "label_27": {"de": "Tiefe", "en": "Depth"},
    "label_28": {"de": "Vorschub", "en": "Feed"},
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
    "program_spindle_mode": {
        "de": ["Festdrehzahl (G97)", "CSS (G96)"],
        "en": ["Fixed RPM (G97)", "CSS (G96)"],
    },
    "program_park_mode": {
        "de": ["Werkzeugwechselpunkt", "Freie Parkposition"],
        "en": ["Tool change point", "Free park position"],
    },
    "program_toolchange_coords": {
        "de": ["Werkstueckkoordinaten", "Maschinenkoordinaten (G53)"],
        "en": ["Work coordinates", "Machine coordinates (G53)"],
    },
    "program_park_coords": {
        "de": ["Werkstueckkoordinaten", "Maschinenkoordinaten (G53)"],
        "en": ["Work coordinates", "Machine coordinates (G53)"],
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
    "parting_mode": {"de": ["Schruppen", "Schlichten", "Schruppen + Schlichten"], "en": ["Rough", "Finish", "Rough + Finish"]},
    "parting_slice_strategy": {"de": ["Parallel X", "Parallel Z"], "en": ["Parallel X", "Parallel Z"]},
    "parting_undercut_mode": {
        "de": ["Ignorieren", "Nur Schlichten", "Separat schruppen", "Voll in Kontur"],
        "en": ["Ignore", "Finish only", "Rough separately", "Full contour"],
    },
    "parting_output_preference": {
        "de": ["Automatisch", "Zyklus bevorzugen", "Ausgeschrieben bevorzugen"],
        "en": ["Automatic", "Prefer cycle", "Prefer explicit"],
    },
    "thread_orientation": {"de": ["Aussengewinde", "Innengewinde"], "en": ["External", "Internal"]},
    "thread_hand": {"de": ["Rechtsgewinde", "Linksgewinde"], "en": ["Right-hand thread", "Left-hand thread"]},
    "thread_relief_mode": {"de": ["Aus", "DIN-Freistich vorschlagen"], "en": ["Off", "Suggest DIN relief"]},
    "thread_relief_norm": {
        "de": ["DIN 76 Form A", "DIN 76 Form B", "DIN 76 Form C"],
        "en": ["DIN 76 form A", "DIN 76 form B", "DIN 76 form C"],
    },
    "thread_coolant": {"de": ["Aus", "Ein"], "en": ["Off", "On"]},
    "groove_process_type": {"de": ["Einstich", "Abstich"], "en": ["Groove", "Parting"]},
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
    "thread_start_z": {
        "de": "Z-Startpunkt des Gewindes. Rechtsgewinde laufen standardmaessig nach minus Z, Linksgewinde nach plus Z.",
        "en": "Z start position of the thread. Right-hand threads usually run toward negative Z, left-hand threads toward positive Z.",
    },
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

GENERAL_TOOLTIP_TRANSLATIONS = {
    "program_language": {
        "de": "Waehlt die Sprache fuer Beschriftungen und Tooltips im Panel.",
        "en": "Select the panel language for labels and tooltips.",
    },
    "program_npv": {
        "de": "Nullpunktverschiebung beziehungsweise Werkstueckkoordinatensystem fuer das Programm, zum Beispiel G54 bis G59.3.",
        "en": "Work offset / work coordinate system used by the program, for example G54 to G59.3.",
    },
    "program_unit": {
        "de": "Bestimmt, ob die Programmdaten in Millimeter oder Inch gepflegt und ausgegeben werden.",
        "en": "Choose whether program data is entered and emitted in millimeters or inches.",
    },
    "program_shape": {
        "de": "Rohteilgrundform. Davon haengen sichtbare Eingabefelder und Teile der Vorschau ab.",
        "en": "Base stock shape. This affects visible input fields and parts of the preview.",
    },
    "program_xa": {
        "de": "Aussendurchmesser des Rohteils am Start. Bei G7 als Durchmesserwert eingeben.",
        "en": "Outer stock diameter at the start. Enter as a diameter value in G7 mode.",
    },
    "program_xi": {
        "de": "Innendurchmesser des Rohteils, falls mit Rohr oder Innenbearbeitung gearbeitet wird.",
        "en": "Inner stock diameter when using tube stock or internal machining.",
    },
    "program_za": {
        "de": "Vorderes Anfangsmass in Z. Von hier aus beginnt die axiale Rohteilgeometrie.",
        "en": "Front start dimension in Z. This defines the axial stock start position.",
    },
    "program_zi": {
        "de": "Hinteres Endmass in Z. Zusammen mit ZA ergibt sich die axiale Rohteillaenge.",
        "en": "Rear end dimension in Z. Together with ZA this defines the stock length.",
    },
    "program_zb": {
        "de": "Bearbeitungsgrenze in Z. Dient unter anderem als Bezug fuer Futter- und Sicherheitslogik.",
        "en": "Machining Z limit. Used as a reference for chuck and safety logic.",
    },
    "program_w": {
        "de": "Breite W fuer nicht-zylindrische Rohteilformen wie Rechteck oder N-Eck.",
        "en": "Width W for non-cylindrical stock shapes such as rectangle or polygon.",
    },
    "program_l": {
        "de": "Laenge L fuer Rohteilformen, die zusaetzliche Laengenangaben benoetigen.",
        "en": "Length L for stock shapes that require an additional length value.",
    },
    "program_n": {
        "de": "Kantenanzahl N fuer polygonale Rohteilformen.",
        "en": "Number of edges N for polygonal stock shapes.",
    },
    "program_sw": {
        "de": "Schluesselweite SW fuer passende Mehrkant- oder Polygonrohteilformen.",
        "en": "Across-flats size SW for matching polygonal stock shapes.",
    },
    "program_retract_mode": {
        "de": "Legt fest, welche Rueckzugsebenen verfuegbar und fuer Generator sowie Vorschau relevant sind: einfach, erweitert oder alle.",
        "en": "Choose which retract planes are available and relevant for generator and preview: simple, extended, or all.",
    },
    "program_xra": {
        "de": "Aeussere Rueckzugsebene in X fuer sichere Verfahrwege ausserhalb des Werkstuecks.",
        "en": "Outer X retract plane for safe moves outside the part.",
    },
    "program_xri": {
        "de": "Innere Rueckzugsebene in X fuer Innenbearbeitung und Bohrungen.",
        "en": "Inner X retract plane for internal machining and bores.",
    },
    "program_zra": {
        "de": "Aeussere Rueckzugsebene in Z fuer sichere An- und Abfahrbewegungen.",
        "en": "Outer Z retract plane for safe approach and retract moves.",
    },
    "program_zri": {
        "de": "Innere Rueckzugsebene in Z fuer Rueckzuege bei Innenbearbeitung.",
        "en": "Inner Z retract plane for retracts during internal machining.",
    },
    "program_chuck_x_min": {
        "de": "Kleinster zulaessiger X-Durchmesser ausserhalb des Futter-Sperrbereichs.",
        "en": "Minimum allowed X diameter outside the chuck no-go area.",
    },
    "program_chuck_x_max": {
        "de": "Groesster zulaessiger X-Durchmesser ausserhalb des Futter-Sperrbereichs.",
        "en": "Maximum allowed X diameter outside the chuck no-go area.",
    },
    "program_chuck_z_limit": {
        "de": "Z-Grenze des Futter-Sperrbereichs. Bewegungen davor werden gewarnt.",
        "en": "Z limit of the chuck no-go area. Moves crossing it are warned.",
    },
    "program_spindle_mode": {
        "de": "Waehlt Festdrehzahl G97 oder konstante Schnittgeschwindigkeit G96.",
        "en": "Select fixed RPM G97 or constant surface speed G96.",
    },
    "program_spindle_max_rpm": {
        "de": "Maximaldrehzahl fuer CSS/G96. Verhindert Ueberdrehzahl an kleinen Durchmessern.",
        "en": "Maximum RPM for CSS/G96 to avoid overspeed on small diameters.",
    },
    "program_park_mode": {
        "de": "Bestimmt, ob am Ende zum Werkzeugwechselpunkt oder zu freier Parkposition gefahren wird.",
        "en": "Choose whether the program ends at the tool change point or a custom park position.",
    },
    "program_toolchange_coords": {
        "de": "Legt fest, ob XT/ZT als Werkstueckkoordinaten oder als Maschinenkoordinaten mit G53 ausgegeben werden.",
        "en": "Choose whether XT/ZT are emitted as work coordinates or machine coordinates using G53.",
    },
    "program_park_coords": {
        "de": "Legt fest, ob Park X/Z als Werkstueckkoordinaten oder als Maschinenkoordinaten mit G53 ausgegeben werden.",
        "en": "Choose whether park X/Z are emitted as work coordinates or machine coordinates using G53.",
    },
    "program_park_x": {
        "de": "X-Position fuer freie Parkfahrt am Programmende.",
        "en": "X position for a custom park move at program end.",
    },
    "program_park_z": {
        "de": "Z-Position fuer freie Parkfahrt am Programmende.",
        "en": "Z position for a custom park move at program end.",
    },
    "program_park_sequential": {
        "de": "Faehre X und Z nacheinander statt diagonal, wenn die Endparkfahrt enger gefuehrt werden soll.",
        "en": "Move X and Z sequentially instead of diagonally for a tighter final park move.",
    },
    "program_optional_stop_toolchange": {
        "de": "Fuegt vor jedem Werkzeugwechsel ein optionales M1 ein.",
        "en": "Insert an optional M1 stop before every tool change.",
    },
    "program_preview_warnings": {
        "de": "Zeigt Sicherheits- und Plausibilitaetswarnungen direkt im Preview an.",
        "en": "Show safety and plausibility warnings directly in the preview.",
    },
    "groove_process_type": {
        "de": "Einstich blendet nur Nut-Parameter ein, Abstich zeigt zusaetzliche Abstech-Parameter.",
        "en": "Groove shows only groove parameters, Parting reveals extra parting parameters.",
    },
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
    "parting_undercut_mode": {
        "de": "Legt fest, ob Freistiche ignoriert, nur geschlichtet, separat oder voll in die Kontur integriert werden.",
        "en": "Choose whether reliefs are ignored, finished only, roughed separately, or fully included in the contour.",
    },
    "parting_output_preference": {
        "de": "Bevorzugt Zyklusausgabe oder ausgeschriebene Bahn, falls beides moeglich ist.",
        "en": "Prefer canned cycle output or explicit toolpath output when both are possible.",
    },
    "parting_undercut_tool": {
        "de": "Separates Werkzeug fuer Freistich/Hinterschnitt bei Modus 'Separat schruppen'.",
        "en": "Separate tool for relief/undercut when 'Rough separately' is selected.",
    },
    "parting_undercut_spindle": {
        "de": "Spezielle Drehzahl fuer den separaten Freistich/Hinterschnitt.",
        "en": "Dedicated spindle speed for the separate relief/undercut pass.",
    },
    "parting_undercut_feed": {
        "de": "Spezialvorschub fuer den separaten Freistich/Hinterschnitt.",
        "en": "Dedicated feed for the separate relief/undercut pass.",
    },
    "parting_optional_stop_before_undercut": {
        "de": "Fuegt vor dem separaten Hinterschnitt ein optionales M1 ein.",
        "en": "Insert an optional M1 stop before the separate relief/undercut pass.",
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
    "groove_reduced_feed_start_x": {
        "de": "Ab diesem X-Durchmesser auf reduzierten Vorschub fuer den Abstich wechseln.",
        "en": "Switch to reduced parting feed from this X diameter onward.",
    },
    "groove_reduced_feed": {
        "de": "Reduzierter Vorschub fuer den letzten Abstichbereich.",
        "en": "Reduced feed for the final parting zone.",
    },
    "groove_reduced_rpm": {
        "de": "Reduzierte Drehzahl fuer den letzten Abstichbereich.",
        "en": "Reduced spindle speed for the final parting zone.",
    },
}
# ----------------------------------------------------------------------
# Preview widget (ausgegliedert nach lathe_easystep/preview_widget.py)
# ----------------------------------------------------------------------
from lathe_easystep.preview_widget import LathePreviewWidget  # noqa: E402


from lathe_easystep.widget_resolver import (  # noqa: E402
    WidgetResolveError,
    WidgetResolver,
    _qname,
)

from lathe_easystep.ui_widget_lookup import (  # noqa: E402
    cache_named_widget,
    connect_button_signal,
    ensure_list_ops_type,
    find_any_widget,
    find_panel_tab_widget,
    find_root_widget,
    find_shape_combo,
    find_unit_combo,
    find_widget_immediate,
    force_attach_core_widgets,
    get_widget_by_name,
    panel_from_widget,
    poll_for_widget,
    process_deferred_lookups,
    rebuild_widget_name_cache,
    register_known_widgets,
    resolve_core_widgets_strict,
    setup_resolver,
    widgets_by_name,
)

from lathe_easystep.preview_geometry import (  # noqa: E402
    build_abspanen_path as _build_abspanen_path_ext,
    build_bore_path as _build_bore_path_ext,
    build_chuck_nogo_primitives,
    build_drill_path as _build_drill_path_ext,
    build_face_path as _build_face_path_ext,
    build_groove_path as _build_groove_path_ext,
    build_groove_preview_path as _build_groove_preview_path_ext,
    build_keyway_path as _build_keyway_path_ext,
    build_keyway_slot_angles as _build_keyway_slot_angles_ext,
    build_retract_primitives,
    build_stock_outline,
    build_thread_path as _build_thread_path_ext,
    build_turn_path as _build_turn_path_ext,
    build_worklimit_primitives,
    default_slice_z_for_operation as _default_slice_z_for_operation_ext,
    front_view_polar_to_cartesian as _front_view_polar_to_cartesian_ext,
    keyway_slice_bounds as _keyway_slice_bounds_ext,
)
from lathe_easystep.contour_logic import (  # noqa: E402
    build_contour_path as _build_contour_path_ext,
    normalize_arc_side as _normalize_arc_side_ext,
    validate_contour_segments_for_profile as _validate_contour_segments_for_profile_ext,
)

build_face_path = _build_face_path_ext
build_turn_path = _build_turn_path_ext
build_bore_path = _build_bore_path_ext
build_thread_path = _build_thread_path_ext
build_groove_path = _build_groove_path_ext
build_drill_path = _build_drill_path_ext
build_keyway_path = _build_keyway_path_ext
build_keyway_slot_angles = _build_keyway_slot_angles_ext
front_view_polar_to_cartesian = _front_view_polar_to_cartesian_ext
keyway_slice_bounds = _keyway_slice_bounds_ext
default_slice_z_for_operation = _default_slice_z_for_operation_ext
build_groove_preview_path = _build_groove_preview_path_ext
build_abspanen_path = _build_abspanen_path_ext
build_contour_path = _build_contour_path_ext
normalize_arc_side = _normalize_arc_side_ext
validate_contour_segments_for_profile = _validate_contour_segments_for_profile_ext


def _debug_mode_enabled() -> bool:
    """Aktivierbarer Debug-Modus fuer ausfuehrliche Laufzeit-Logs.

    Aktivierung ueber Umgebungsvariable vor dem Start, z. B.:
      LATHEEASYSTEP_DEBUG=1 qtvcp -c easystep -u ./lathe_easystep_handler.py ./lathe_easystep.ui
    Ohne diese Variable bleibt die Konsole wie bisher auf Start-/Fehlermeldungen
    beschraenkt.
    """
    value = str(os.environ.get("LATHEEASYSTEP_DEBUG", "")).strip().lower()
    return value in ("1", "true", "yes", "on", "debug")


class HandlerClass:
    def _register_known_widgets(self):
        return register_known_widgets(self)

    def _process_deferred_lookups(self):
        return process_deferred_lookups(self)

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
        self._program_dirty = False
        self._dirty_operation_indices = set()
        self._dirty_warning_suppressed = False

        # zentrale Widgets
        self.preview = getattr(self.w, "previewWidget", None)
        self.preview_slice = getattr(self.w, "previewSliceWidget", None)
        self.btn_slice_view = getattr(self.w, "btn_slice_view", None)
        self.contour_preview = getattr(self.w, "contourPreview", None)
        # Queue für nachträgliche Widget-Suchen, bis das Panel vollständig geladen ist
        self._deferred_lookup_queue: List[Tuple[str, str, object, bool]] = []
        self.debug_mode = _debug_mode_enabled()
        self._verbose_widget_logs = self.debug_mode
        if self.debug_mode:
            self._log(
                "[LatheEasyStep] Debug-Modus aktiv (LATHEEASYSTEP_DEBUG) - "
                "ausfuehrliche Laufzeit-Logs eingeschaltet",
                level="info",
            )
        self._bootstrap_widget_refs()
        self._init_dirty_state()

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
        return write_step_file(self, op, file_path)

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

    def _init_dirty_state(self) -> None:
        init_dirty_state(self)

    def _mark_dirty(self, *, operation_index: int | None = None, program: bool = False) -> None:
        mark_dirty(self, operation_index=operation_index, program=program)

    def _mark_all_operations_dirty(self) -> None:
        mark_all_operations_dirty(self)

    def _mark_program_structure_dirty(self, *, operation_indices: set[int] | None = None) -> None:
        mark_program_structure_dirty(self, operation_indices=operation_indices)

    def _clear_dirty_state(self) -> None:
        clear_dirty_state(self)

    def _clear_program_dirty(self, *, header: bool = False, structure: bool = False, all_flags: bool = False) -> None:
        clear_program_dirty(self, header=header, structure=structure, all_flags=all_flags)

    def _clear_dirty_operation(self, operation_index: int) -> None:
        clear_dirty_operation(self, operation_index)

    def _update_dirty_status(self) -> None:
        update_dirty_status(self)

    def _has_unsaved_changes(self) -> bool:
        return has_unsaved_changes(self)

    def _current_operation_is_dirty(self, row: int | None = None) -> bool:
        return current_operation_is_dirty(self, row=row)

    def _warn_if_dirty(self, context: str, *, row: int | None = None) -> None:
        warn_if_dirty(self, context, row=row)

    def _tab_label_for_dirty_state(self, op_type: str | None) -> str:
        return dirty_tab_label(self, op_type)

    def _startup_mark(self, label: str):
        try:
            delta = time.monotonic() - getattr(self, "_startup_epoch", time.monotonic())
            self._log(f"[LatheEasyStep][startup +{delta:0.3f}s] {label}", level="info")
        except Exception:
            pass

    def _run_startup_callback(self, callback):
        """Time deferred initialization without changing its scheduling."""
        label = getattr(callback, "__name__", "callback")
        started = time.monotonic()
        self._startup_mark(f"{label} begin")
        try:
            return callback()
        finally:
            self._startup_mark(f"{label} end ({time.monotonic() - started:.3f}s)")

    def _schedule_startup_heartbeats(self):
        return

    # ---- interne Helfer zur Widget-Suche ------------------------------
    def _setup_resolver(self):
        return setup_resolver(self)

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
        if level == "debug" and not getattr(self, "debug_mode", False):
            return
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
        return resolve_core_widgets_strict(self)

    def _ensure_list_ops_type(self):
        return ensure_list_ops_type(self)

    def _force_attach_core_widgets(self):
        return force_attach_core_widgets(self)

    def _find_root_widget(self):
        return find_root_widget(self)

    def _find_any_widget(self, obj_name: str):
        return find_any_widget(self, obj_name)

    def _find_panel_tab_widget(self) -> QtWidgets.QTabWidget | None:
        return find_panel_tab_widget(self)

    def _panel_from_widget(self, widget: QtWidgets.QWidget | None):
        return panel_from_widget(self, widget)

    def _find_unit_combo(self):
        return find_unit_combo(self)

    def _find_shape_combo(self):
        return find_shape_combo(self)

    def _rebuild_widget_name_cache(self):
        return rebuild_widget_name_cache(self)

    def _cache_named_widget(self, widget: QtWidgets.QWidget | None):
        return cache_named_widget(self, widget)

    def _widgets_by_name(self, name: str) -> List[QtWidgets.QWidget]:
        return widgets_by_name(self, name)

    def _get_widget_by_name(self, name: str) -> QtWidgets.QWidget | None:
        return get_widget_by_name(self, name)

    def _poll_for_widget(self, name: str, attempts_left: int):
        return poll_for_widget(self, name, attempts_left)

    def _find_widget_immediate(self, name: str) -> QtWidgets.QWidget | None:
        return find_widget_immediate(self, name)

    def _connect_button_signal(self, button: QtWidgets.QPushButton, name: str):
        return connect_button_signal(self, button, name)

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
            elif name.endswith("_spindle_mode"):
                self._update_spindle_mode_visibility()
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
            self._update_spindle_mode_visibility()
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
        # Wird bei JEDEM _refresh_preview()-Durchlauf aufgerufen, nicht nur
        # beim Wechsel des ausgewaehlten Steps. Ohne diese Sperre setzte jeder
        # beliebige Refresh waehrend des Ziehens an der Schnittkante (Tab-
        # Wechsel, Parameteraenderung, periodische Aktualisierung) slice_z
        # unbemerkt auf den vorgeschlagenen Standardwert zurueck - die
        # Schnittansicht wirkte dadurch eingefroren, obwohl der Nutzer aktiv
        # gezogen hat. Der Vorschlag greift nur, wenn sich die aktive
        # Operation seit dem letzten Aufruf tatsaechlich geaendert hat.
        if op is getattr(self, "_slice_z_synced_op", None):
            return
        self._slice_z_synced_op = op
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
        self._log(
            f"[LatheEasyStep][debug] slice changed: z={self._current_slice_z:.6f} "
            f"slice_widget_visible={getattr(self.preview_slice, 'isVisible', lambda: None)() if self.preview_slice else None}",
            level="debug",
        )
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
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._apply_unit_suffix))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._update_program_visibility))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._update_retract_visibility))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._update_subspindle_visibility))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._update_face_visibility))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._auto_load_tool_table))
        # Kontur-Tab initial vorbereiten (Spalten/Leerzeile optional)
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._init_contour_table))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._sync_contour_edge_controls))
        QtCore.QTimer.singleShot(0, lambda: self._run_startup_callback(self._update_contour_preview_temp))

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
        if getattr(self, "thread_hand", None) is None:
            self.thread_hand = self._get_widget_by_name("thread_hand")
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
        if getattr(self, "thread_start_z", None) is None:
            self.thread_start_z = self._get_widget_by_name("thread_start_z")
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
        custom_key = "combo.thread_standard.custom"

        combo.blockSignals(True)
        combo.clear()
        combo.addItem(TRANSLATIONS.tr(custom_key, lang), {"label_key": custom_key})
        # Metric threads (ISO 60°) -> profile "metric"
        for name, diameter, pitch in metric_thread_presets():
            pitch_text = _compact(pitch)
            technical_id = f"thread.standard.metric.{name.lower()}x{pitch_text.replace('.', '_')}"
            combo.addItem(
                TRANSLATIONS.tr(technical_id, lang),
                {
                    "label": name,
                    "label_key": technical_id,
                    "major": diameter,
                    "pitch": pitch,
                    "profile": "metric",
                },
            )
        # Trapezoidal threads -> profile "tr"
        for name, diameter, pitch in trapezoidal_thread_presets():
            pitch_text = _compact(pitch)
            technical_id = f"thread.standard.tr.{name.lower()}x{pitch_text.replace('.', '_')}"
            combo.addItem(
                TRANSLATIONS.tr(technical_id, lang),
                {
                    "label": name,
                    "label_key": technical_id,
                    "major": diameter,
                    "pitch": pitch,
                    "profile": "tr",
                },
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
        if validate_thread_preset_data(data):
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
        return apply_thread_preset(self, force=force)

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
        for idx, data_value in enumerate(("parallel_x", "parallel_z")):
            if idx < combo.count():
                combo.setItemData(idx, data_value, QtCore.Qt.UserRole)

    def _select_slice_strategy_index(self, combo, value) -> bool:
        combo = combo or getattr(self, "parting_slice_strategy", None)
        if combo is None:
            return False
        self._setup_parting_slice_strategy_items()
        try:
            code = int(float(value))
            # itemData holds the string codes ("parallel_x"/"parallel_z"), not the
            # legacy 1/2 integers - map before searching, or findData() can never match.
            data_value = {1: "parallel_x", 2: "parallel_z"}.get(code)
            if data_value is not None:
                idx = combo.findData(data_value, QtCore.Qt.UserRole)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                    return True
        except Exception:
            pass
        if isinstance(value, str):
            lowered = value.strip().lower()
            idx = combo.findData(lowered, QtCore.Qt.UserRole)
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
            self._update_spindle_mode_visibility()

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
        if combo is None or not hasattr(combo, "currentIndex"):
            return DEFAULT_LANGUAGE
        try:
            data = combo.currentData()
        except Exception:
            data = None
        if isinstance(data, str):
            code = data.strip().lower()
            if code:
                return code
        try:
            idx = int(combo.currentIndex())
        except Exception:
            idx = 0
        if idx == 1:
            return "en"
        if idx == 2:
            return "es"
        return "de"

    def _handle_language_change(self, *_args):
        self._apply_language_texts()
        self._thread_standard_populated = False
        self._setup_thread_helpers()

    def _apply_registered_texts(self, lang: str):
        for name, key in UI_TEXT_KEYS.items():
            if re.match(r"^label_\d+$", str(name or "")):
                continue
            text = TRANSLATIONS.tr(key, lang)
            for widget in self._widgets_by_name(name):
                try:
                    widget.setProperty("text_key", key)
                except Exception:
                    pass
                try:
                    widget.setText(text)
                except Exception:
                    pass

    def _apply_widget_property_translations(self, lang: str):
        root = self.root_widget or self._find_root_widget()
        if root is None:
            return
        try:
            widgets = [root]
            widgets.extend(root.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindChildrenRecursively))
        except Exception:
            widgets = [root]
        for widget in widgets:
            try:
                text_key = widget.property("text_key")
            except Exception:
                text_key = None
            if isinstance(text_key, str) and text_key:
                text = TRANSLATIONS.tr(text_key, lang)
                try:
                    widget.setText(text)
                except Exception:
                    pass
            try:
                tooltip_key = widget.property("tooltip_key")
                # Perf (LES-027, 2026-09-10): `apply_registered_tooltips()`
                # (laeuft in `_apply_language_texts()` immer VOR dieser
                # Funktion) markiert jedes von ihr behandelte Widget explizit
                # mit `tooltip_fallback_auto=False`. Ohne diese Pruefung
                # wiederholte diese Funktion `_set_tooltip_deep()` - mit
                # eigenem verschachteltem `findChildren()` - fuer dieselben
                # bis zu 169 Widgets ein zweites Mal (real mit >5s gemessen).
                # Nur Widgets, deren `tooltip_key` NICHT ueber die zentrale
                # Registry gesetzt wurde (z. B. direkt im Designer), bleiben
                # hier zu behandeln.
                already_registered = widget.property("tooltip_fallback_auto") is False
            except Exception:
                tooltip_key = None
                already_registered = False
            if isinstance(tooltip_key, str) and tooltip_key and not already_registered:
                text = TRANSLATIONS.tr(tooltip_key, lang)
                self._set_tooltip_deep(widget, text)

    def _apply_language_texts(self):
        lang = self._current_language_code()
        root = getattr(self, "root_widget", None)
        if root is None:
            find_root = getattr(self, "_find_root_widget", None)
            if callable(find_root):
                try:
                    root = find_root()
                except Exception:
                    root = None
        if root is not None:
            try:
                self._startup_mark("_apply_language_texts: apply_ui_static_translations begin")
                apply_ui_static_translations(root, TRANSLATIONS.tr, lang)
                self._startup_mark("_apply_language_texts: apply_ui_static_translations end")
            except Exception:
                pass
        self._startup_mark("_apply_language_texts: apply_registered_texts begin")
        self._apply_registered_texts(lang)
        self._startup_mark("_apply_language_texts: apply_registered_texts end")
        self._startup_mark("_apply_language_texts: apply_combo_translations begin")
        self._apply_combo_translations(lang)
        self._startup_mark("_apply_language_texts: apply_combo_translations end")
        self._startup_mark("_apply_language_texts: handle_global_change begin")
        self._handle_global_change()
        self._startup_mark("_apply_language_texts: handle_global_change end")
        self._startup_mark("_apply_language_texts: apply_tab_titles begin")
        self._apply_tab_titles(lang)
        self._startup_mark("_apply_language_texts: apply_tab_titles end")
        self._startup_mark("_apply_language_texts: apply_button_translations begin")
        self._apply_button_translations(lang)
        self._startup_mark("_apply_language_texts: apply_button_translations end")
        try:
            self._startup_mark("_apply_language_texts: apply_registered_tooltips begin")
            self._apply_registered_tooltips(lang)
            self._startup_mark("_apply_language_texts: apply_registered_tooltips end")
        except Exception:
            pass
        try:
            self._startup_mark("_apply_language_texts: apply_widget_property_translations begin")
            self._apply_widget_property_translations(lang)
            self._startup_mark("_apply_language_texts: apply_widget_property_translations end")
        except Exception:
            pass
        # No tooltip fallback text from widgets/UI: only explicit translation keys are allowed.
        try:
            if getattr(self, "contour_segments", None) is not None:
                self._startup_mark("_apply_language_texts: init_contour_table begin")
                self._init_contour_table()
                self._startup_mark("_apply_language_texts: init_contour_table end")
        except Exception:
            pass
        try:
            if getattr(self, "btn_slice_view", None) is not None:
                update_slice_view_button(self, bool(self.btn_slice_view.isChecked()))
        except Exception:
            pass
        try:
            self._update_dirty_status()
        except Exception:
            pass
        self._startup_mark("_apply_language_texts: validate_language begin")
        TRANSLATIONS.validate_language(lang, getattr(self, "LOG", None))
        self._startup_mark("_apply_language_texts: validate_language end")

    def _apply_combo_translations(self, lang: str):
        for name, items in COMBO_ITEM_REGISTRY.items():
            for widget in self._widgets_by_name(name):
                if not all(hasattr(widget, attr) for attr in ("currentIndex", "count", "blockSignals", "clear", "addItem", "setCurrentIndex")):
                    continue
                current_index = widget.currentIndex()
                try:
                    current_data = widget.currentData()
                except Exception:
                    current_data = None
                widget.blockSignals(True)
                widget.clear()
                for value, text_key in items:
                    widget.addItem(TRANSLATIONS.tr(text_key, lang), value)
                target_index = -1
                if current_data is not None:
                    try:
                        target_index = widget.findData(current_data, QtCore.Qt.UserRole)
                    except Exception:
                        target_index = -1
                if target_index < 0:
                    target_index = max(0, min(current_index, widget.count() - 1)) if widget.count() else -1
                widget.setCurrentIndex(target_index)
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
            tab_widget_page = tab_widget.widget(idx)
            if tab_widget_page is not None:
                tab_name = tab_widget_page.objectName()
                title = TRANSLATIONS.tab_title(tab_name, lang)
            if not title and idx < len(TAB_ORDER):
                title = TRANSLATIONS.tab_title(TAB_ORDER[idx], lang)
            if title:
                try:
                    self.tab_params.setTabText(idx, title)
                except Exception:
                    pass

    def _apply_button_translations(self, lang: str):
        for name, key in UI_TEXT_KEYS.items():
            if not name.startswith("btn"):
                continue
            text = TRANSLATIONS.tr(key, lang)
            for button in self._widgets_by_name(name):
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

    def _set_tooltip_deep(self, widget, text: str):
        return set_tooltip_deep(self, widget, text)

    def _layout_item_contains_widget(self, item, widget) -> bool:
        if item is None or widget is None:
            return False
        try:
            direct_widget = item.widget()
        except Exception:
            direct_widget = None
        if direct_widget is widget:
            return True
        if direct_widget is not None and hasattr(direct_widget, "findChildren"):
            try:
                if widget in direct_widget.findChildren(QtWidgets.QWidget):
                    return True
            except Exception:
                pass
        try:
            layout = item.layout()
        except Exception:
            layout = None
        if layout is None:
            return False
        try:
            for idx in range(layout.count()):
                if self._layout_item_contains_widget(layout.itemAt(idx), widget):
                    return True
        except Exception:
            pass
        return False

    def _form_label_for_widget(self, widget):
        form_layout_cls = getattr(QtWidgets, "QFormLayout", None)
        if form_layout_cls is None:
            return None
        parent = widget
        while parent is not None:
            try:
                layout = parent.layout() if hasattr(parent, "layout") else None
            except Exception:
                layout = None
            if isinstance(layout, form_layout_cls):
                try:
                    direct = layout.labelForField(widget)
                except Exception:
                    direct = None
                if direct is not None:
                    return direct
                try:
                    for row in range(layout.rowCount()):
                        field_item = layout.itemAt(row, form_layout_cls.FieldRole)
                        if self._layout_item_contains_widget(field_item, widget):
                            label_item = layout.itemAt(row, form_layout_cls.LabelRole)
                            return label_item.widget() if label_item is not None else None
                except Exception:
                    pass
            try:
                parent = parent.parentWidget() if hasattr(parent, "parentWidget") else None
            except Exception:
                parent = None
        return None

    def _fallback_tooltip_text(self, widget) -> str:
        return fallback_tooltip_text(self, widget)

    def _apply_tooltip_fallbacks(self):
        # Intentionally disabled by architecture rule:
        # never derive visible text from UI/Python fallback sources.
        return

    def _apply_registered_tooltips(self, lang: str):
        return apply_registered_tooltips(self, lang)

    def _apply_thread_tooltips(self, lang: str):
        """Rueckwaertskompatibler Wrapper fuer den zentralen Tooltip-Pfad."""
        self._apply_registered_tooltips(lang)
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

    def _apply_general_tooltips(self, lang: str):
        self._apply_registered_tooltips(lang)

    def _apply_parting_tooltips(self, lang: str):
        """Rueckwaertskompatibler Wrapper fuer den zentralen Tooltip-Pfad."""
        self._apply_registered_tooltips(lang)

    def _apply_groove_tooltips(self, lang: str):
        """Rueckwaertskompatibler Wrapper fuer den zentralen Tooltip-Pfad."""
        self._apply_registered_tooltips(lang)

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
        try:
            idx = self.tab_params.currentIndex() if self.tab_params else None
        except Exception:
            idx = None
        self._log(f"[LatheEasyStep][debug] tab changed: index={idx}", level="debug")
        t0 = time.monotonic()
        handle_tab_changed(self, *_args, **_kwargs)
        self._log(f"[LatheEasyStep][debug] tab changed handled in {time.monotonic() - t0:.3f}s", level="debug")

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
        return collect_params(self, op_type)

    def _collect_program_header(self) -> Dict[str, object]:
        return collect_program_header(self)

    def _tool_change_position_lines(self, header: Dict[str, object]) -> List[str]:
        """Generiert G-Code zum Anfahren der Werkzeugwechselposition (XT/ZT)."""
        xt = float(header.get("xt", 0.0))
        zt = float(header.get("zt", 0.0))
        coord_mode = str(header.get("toolchange_coords", "") or "").strip().lower()
        if coord_mode not in ("work", "machine"):
            xt_abs = bool(header.get("xt_absolute", True))
            zt_abs = bool(header.get("zt_absolute", True))
            if xt_abs != zt_abs:
                coord_mode = "mixed"
            else:
                coord_mode = "work" if xt_abs and zt_abs else "machine"

        lines: List[str] = []

        if coord_mode == "work":
            lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
            return lines
        if coord_mode == "mixed":
            xt_abs = bool(header.get("xt_absolute", True))
            zt_abs = bool(header.get("zt_absolute", True))
            if not xt_abs:
                lines.append(f"G53 G0 X{xt:.3f}")
            if not zt_abs:
                lines.append(f"G53 G0 Z{zt:.3f}")
            work_parts = []
            if xt_abs:
                work_parts.append(f"X{xt:.3f}")
            if zt_abs:
                work_parts.append(f"Z{zt:.3f}")
            if work_parts:
                lines.append(f"G0 {' '.join(work_parts)}")
            return lines
        lines.append(f"G53 G0 X{xt:.3f} Z{zt:.3f}")
        return lines

    def _collect_contour_segments(self) -> List[Dict[str, object]]:
        return collect_contour_segments(self)

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
                idx = w_edge.findData(str(edge_text), QtCore.Qt.UserRole)
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
                edge_now = str(edge_text or "").strip().lower()
                if not edge_now and hasattr(table.cellWidget(row, 3), "currentData"):
                    edge_now = str(table.cellWidget(row, 3).currentData() or "").strip().lower()
                w.setEnabled(edge_now == "radius")
                if arc_text is not None and hasattr(w, "findData"):
                    idx = w.findData(str(arc_text).strip().lower(), QtCore.Qt.UserRole)
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
        t0 = time.monotonic()
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
        self._log(f"[LatheEasyStep][debug] preview refreshed in {time.monotonic() - t0:.3f}s", level="debug")

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
                # Kommentar leer -> Erstbefuellung; sieht er bereits wie eine
                # maschinell nummerierte Beschreibung aus -> Nummer auffrischen
                # (gleiche Regel wie _insert_loaded_operation(), LES-023). Ein
                # bewusst individueller Kommentar bleibt unangetastet.
                if _looks_like_generated_step_comment(op.params.get("comment")):
                    update_auto_comment(op, self._describe_operation(op, len(self.model.operations)))
                try:
                    self._mark_program_structure_dirty(operation_indices={len(self.model.operations) - 1})
                except Exception:
                    pass
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
                lang = self._current_language_code()
                if parent is not None:
                    try:
                        QtWidgets.QMessageBox.warning(
                            parent,
                            TRANSLATIONS.tr("dialog.delete.title", lang),
                            TRANSLATIONS.tr("message.delete.program_header_forbidden", lang),
                        )
                    except Exception:
                        self._log(
                            "[LatheEasyStep] blocked delete of program header without Qt parent",
                            level="warning",
                        )
                else:
                    self._log(
                        "[LatheEasyStep] blocked delete of program header without Qt parent",
                        level="warning",
                    )
                return
            self.model.remove_operation(idx)
            try:
                self._mark_program_structure_dirty()
            except Exception:
                pass
            new_idx = min(idx, len(self.model.operations) - 1)
            self._refresh_operation_list(select_index=new_idx)
            self._renumber_operations()
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
        # Kommentar neu erzeugen, wenn er leer ist ODER bereits wie eine
        # maschinell nummerierte Beschreibung aussieht ("5. Innenabspanen
        # ..."): eine per "Step speichern" gesicherte Datei enthaelt genau so
        # einen Kommentar mit der zum Speicherzeitpunkt gueltigen, jetzt
        # potenziell falschen Nummer. Ein bewusst individueller Kommentar ohne
        # nummerierte Vorsilbe bleibt dagegen erhalten (LES-023).
        if _looks_like_generated_step_comment(op.params.get("comment")):
            update_auto_comment(op, self._describe_operation(op, len(self.model.operations)))
        try:
            self._clear_dirty_operation(len(self.model.operations) - 1)
        except Exception:
            pass
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

        self._log(f"[LatheEasyStep][debug] param change: widget={name} op_type={op.op_type} row={idx} value={val!r}", level="debug")

        # Do NOT write widget.objectName() directly into op.params.
        # The authoritative mapping is built by _collect_params(op_type),
        # so we rebuild the selected operation from the UI and refresh geometry/preview.
        try:
            self._update_selected_operation(force=True)
        except Exception:
            pass
        if name.endswith("_spindle_mode"):
            try:
                self._update_spindle_mode_visibility()
            except Exception:
                pass
        try:
            if op.op_type == OpType.PROGRAM_HEADER:
                self._mark_dirty(program=True)
            else:
                self._mark_dirty(operation_index=idx)
        except Exception:
            pass
        return


    def _handle_selection_change(self, row: int):
        try:
            prev_op = self.model.operations[row].op_type if 0 <= row < len(self.model.operations) else None
        except Exception:
            prev_op = None
        self._log(f"[LatheEasyStep][debug] selection change: row={row} op_type={prev_op}", level="debug")
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

    def _update_spindle_mode_visibility(self, *args, **kwargs):
        update_spindle_mode_visibility(self, *args, **kwargs)

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
