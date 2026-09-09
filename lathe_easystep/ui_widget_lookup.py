"""Widget-Bootstrapping: robuste Widget-Suche/-Auflösung fuer QtVCP-Embedding.

Ausgelagert aus HandlerClass (LES-020). Reine Widget-Lookup-Mechanik ohne
fachliche Logik - Registrierung bekannter Widgets, Resolver-Setup, tolerante
Namensaufloesung mit Caching/Scoring und Polling-Fallback fuer verspaetet
eingebettete Panels. Jede Funktion nimmt den Handler (self) als ersten
Parameter entgegen und wird vom Handler nur ueber duenne, gleichnamige
Wrapper-Methoden aufgerufen (siehe HandlerClass._get_widget_by_name() etc.) -
Aufrufstellen im Handler bleiben dadurch unveraendert.
"""

from __future__ import annotations

import re
from typing import Dict, List

from qtpy import QtCore, QtWidgets

from .preview_widget import LathePreviewWidget
from .ui_registry import PANEL_WIDGET_NAMES, TAB_TRANSLATIONS, _looks_like_panel_widget
from .widget_resolver import WidgetResolver, _qname


def register_known_widgets(self):
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
        "program_language",
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
        "thread_hand",
        "thread_standard",
        "thread_major_diameter",
        "thread_pitch",
        "thread_length",
        "thread_start_z",
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

def process_deferred_lookups(self):
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

def setup_resolver(self):
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

def resolve_core_widgets_strict(self):
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
        ("program_language", "program_language", QtWidgets.QComboBox),
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
        ("thread_hand", "thread_hand", QtWidgets.QComboBox),
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
        ("thread_start_z", "thread_start_z", QtWidgets.QDoubleSpinBox),
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
        ("label_thread_hand", "label_thread_hand", QtWidgets.QLabel),
        ("label_thread_standard", "label_thread_standard", QtWidgets.QLabel),
        ("label_thread_tool", "label_thread_tool", QtWidgets.QLabel),
        ("label_thread_spindle", "label_thread_spindle", QtWidgets.QLabel),
        ("label_thread_coolant", "label_thread_coolant", QtWidgets.QLabel),
        ("label_thread_major_diameter", "label_thread_major_diameter", QtWidgets.QLabel),
        ("label_thread_pitch", "label_thread_pitch", QtWidgets.QLabel),
        ("label_thread_length", "label_thread_length", QtWidgets.QLabel),
        ("label_thread_start_z", "label_thread_start_z", QtWidgets.QLabel),
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

def ensure_list_ops_type(self):
    if self.list_ops is not None and not isinstance(self.list_ops, QtWidgets.QListWidget):
        try:
            self.LOG.warning(
                f"[LatheEasyStep] list_ops has wrong type: {_qname(self.list_ops)}; resetting to None"
            )
        except Exception:
            self._log(f"[LatheEasyStep] list_ops has wrong type: {_qname(self.list_ops)}; resetting to None", level="info")
        self.list_ops = None

def force_attach_core_widgets(self):
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

def find_root_widget(self):
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

def find_any_widget(self, obj_name: str):
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
                for w in r.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindChildrenRecursively):
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

def find_panel_tab_widget(self) -> QtWidgets.QTabWidget | None:
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

def panel_from_widget(self, widget: QtWidgets.QWidget | None):
    """Hilfsfunktion: finde den Panel-Elternteil zu einem Widget."""
    while widget:
        try:
            if widget.objectName() in PANEL_WIDGET_NAMES:
                return widget
        except Exception:
            pass
        widget = widget.parentWidget()
    return None

def find_unit_combo(self):
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

def find_shape_combo(self):
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

def rebuild_widget_name_cache(self):
    """Build an objectName cache for the current panel subtree."""
    root = self.root_widget or self._find_root_widget()
    cache: Dict[str, List[QtWidgets.QWidget]] = {}
    if root is not None:
        try:
            widgets = [root]
            widgets.extend(root.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindChildrenRecursively))
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

def cache_named_widget(self, widget: QtWidgets.QWidget | None):
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

def widgets_by_name(self, name: str) -> List[QtWidgets.QWidget]:
    if not name:
        return []
    if not hasattr(self, "_widget_name_cache") or not getattr(self, "_widget_name_cache", None):
        try:
            self._rebuild_widget_name_cache()
        except Exception:
            pass
    widgets = list((getattr(self, "_widget_name_cache", {}) or {}).get(name, []))
    if widgets:
        return widgets
    widget = self._get_widget_by_name(name)
    return [widget] if widget is not None else []

def get_widget_by_name(self, name: str) -> QtWidgets.QWidget | None:
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
            wants_preview = "preview" in lname or "contourpreview" in lname
            alternates = set()
            if "preview" in lname and "contour" in lname:
                alternates.add(lname.replace("preview", "contour"))
                alternates.add(lname.replace("contour", "preview"))
            elif wants_preview:
                alternates.add(lname.replace("preview", "contour"))
            elif "contour" in lname:
                alternates.add(lname.replace("contour", "preview"))

            if alternates or wants_preview:
                for w in root.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindChildrenRecursively):
                    try:
                        on = (w.objectName() or "").lower()
                    except Exception:
                        on = ""
                    if on and any(alt == on for alt in alternates):
                        return w
                    if not wants_preview:
                        continue
                    try:
                        clsname = ""
                        mo = getattr(w, "metaObject", None)
                        if callable(mo):
                            try:
                                clsname = w.metaObject().className() or ""
                            except Exception:
                                clsname = w.__class__.__name__
                        else:
                            clsname = w.__class__.__name__
                        if clsname and "lathepreview" in clsname.lower():
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

def poll_for_widget(self, name: str, attempts_left: int):
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

def find_widget_immediate(self, name: str) -> QtWidgets.QWidget | None:
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

def connect_button_signal(self, button: QtWidgets.QPushButton, name: str):
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

