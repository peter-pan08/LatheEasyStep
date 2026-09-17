from __future__ import annotations

from qtpy import QtCore, QtWidgets
from .ui_advanced import ensure_advanced_widgets
from .ui_split import load_split_tab_uis, load_step_management_uis, load_preview_uis

_WORKSPACE_SPLITTER_SETTINGS_KEY = "LatheEasyStep/WorkspaceSplitterSizes"
_PREVIEW_PARAMS_SPLITTER_SETTINGS_KEY = "LatheEasyStep/PreviewParamsSplitterSizes"


def _parse_saved_splitter_sizes(raw, count):
    """Parse a ","-joined size list, rejecting anything that could not have
    come from `_persist_splitter_sizes()` below (wrong count, non-positive
    values) instead of letting a corrupted/foreign setting reach setSizes()."""
    if not raw:
        return None
    try:
        sizes = [int(part) for part in str(raw).split(",")]
    except (TypeError, ValueError):
        return None
    if len(sizes) != count or any(size <= 0 for size in sizes):
        return None
    return sizes


def _restore_splitter_sizes(splitter, settings_key, minimums) -> None:
    """Apply a previously saved size list if present and still plausible for
    the current widget tree; otherwise leave the caller's own default sizes
    (already applied via setSizes() before this runs) untouched - that
    default IS the robust fallback."""
    try:
        settings = QtCore.QSettings()
        raw = settings.value(settings_key, "", type=str)
    except Exception:
        return
    sizes = _parse_saved_splitter_sizes(raw, len(minimums))
    if sizes is None:
        return
    if any(size < minimum for size, minimum in zip(sizes, minimums)):
        return
    try:
        splitter.setSizes(sizes)
    except Exception:
        pass


def _persist_splitter_sizes(splitter, settings_key) -> None:
    try:
        settings = QtCore.QSettings()
        settings.setValue(settings_key, ",".join(str(size) for size in splitter.sizes()))
    except Exception:
        pass


def bootstrap_widget_refs(handler) -> None:
    """Initialize widget reference attributes early so startup code can safely probe them."""
    panel_root = getattr(handler.w, "easystep", None) or handler.w

    def find(name, cls=None):
        widget = getattr(handler.w, name, None)
        if widget is not None:
            return widget
        try:
            if cls is None:
                return panel_root.findChild(QtCore.QObject, name)
            return panel_root.findChild(cls, name)
        except Exception:
            return None

    handler.preview_slice = find("previewSliceWidget", QtWidgets.QWidget)
    handler.btn_slice_view = find("btn_slice_view", QtWidgets.QAbstractButton)
    if handler.btn_slice_view is None:
        try:
            for button in panel_root.findChildren(QtWidgets.QAbstractButton):
                text = (button.text() or "").lower()
                if getattr(button, "isCheckable", lambda: False)() and ("schnitt" in text or "seiten" in text):
                    handler.btn_slice_view = button
                    break
        except Exception:
            pass
    handler.contour_preview = getattr(handler.w, "contourPreview", None)
    handler.list_ops = getattr(handler.w, "listOperations", None)
    handler.tab_params = getattr(handler.w, "tabParams", None)
    if handler.tab_params is not None:
        try:
            handler.tab_params.setCurrentIndex(1)
        except Exception:
            pass

    def resolve_widget(name: str):
        widget = getattr(handler.w, name, None)
        if widget is not None:
            return widget
        widget = handler._find_any_widget(name)
        if widget is not None:
            handler._log(f"[LatheEasyStep] resolved '{name}' via global search", level="info")
        return widget

    def resolve_or_defer_local(attr_name: str, name: str):
        try:
            ui_ready = getattr(handler.w, "ui_ready", False)
        except Exception:
            ui_ready = False
        if not ui_ready:
            return None
        widget = getattr(handler.w, name, None)
        if widget is not None:
            setattr(handler, attr_name, widget)
            return widget
        try:
            widget = handler._find_any_widget(name)
        except Exception:
            widget = None
        setattr(handler, attr_name, widget)
        return widget

    handler.btn_add = resolve_or_defer_local("btn_add", "btnAdd")
    handler.btn_delete = resolve_or_defer_local("btn_delete", "btnDelete")
    handler.btn_move_up = resolve_or_defer_local("btn_move_up", "btnMoveUp")
    handler.btn_move_down = resolve_or_defer_local("btn_move_down", "btnMoveDown")
    handler.btn_new_program = resolve_or_defer_local("btn_new_program", "btnNewProgram")
    handler.btn_generate = resolve_or_defer_local("btn_generate", "btnGenerate")
    handler.btn_save_changes = resolve_or_defer_local("btn_save_changes", "btnSaveChanges")

    handler.tab_program = resolve_widget("tabProgram")
    handler.program_language = resolve_widget("program_language")
    handler.program_unit = resolve_widget("program_unit")
    handler.program_shape = resolve_widget("program_shape")
    handler.program_retract_mode = resolve_widget("program_retract_mode")
    handler.program_has_subspindle = resolve_widget("program_has_subspindle")

    for attr_name in (
        "program_xa", "program_xi", "label_prog_xi", "program_za", "program_zi", "program_zb",
        "program_w", "label_prog_w", "program_l", "label_prog_l", "program_n", "label_prog_n",
        "program_sw", "label_prog_sw", "program_xt", "program_zt", "program_sc",
        "program_machine_profile", "program_chuck_size", "program_chuck_part_type",
        "program_chuck_grip_mode", "program_chuck_profile", "program_chuck_x_min",
        "program_chuck_x_max", "program_chuck_z_limit", "program_name", "program_xra",
        "label_prog_xra", "program_xri", "label_prog_xri", "program_zra", "label_prog_zra",
        "program_zri", "label_prog_zri", "program_xra_absolute", "program_xri_absolute",
        "program_zra_absolute", "program_zri_absolute", "program_xt_absolute",
        "program_zt_absolute", "program_s1", "label_prog_s1", "program_s3", "label_prog_s3",
        "program_spindle", "program_tool", "program_npv", "program_spindle_mode",
        "program_spindle_max_rpm", "program_park_mode", "program_toolchange_coords",
        "program_park_coords", "program_park_x", "program_park_z",
        "program_park_sequential", "program_optional_stop_toolchange", "program_preview_warnings",
        "face_mode", "face_edge_type",
        "label_face_edge_size", "face_edge_size", "label_face_finish_allow_x",
        "face_finish_allow_x", "label_face_finish_allow_z", "face_finish_allow_z",
        "label_face_depth_max", "face_depth_max", "label_face_pause", "face_pause_enabled",
        "label_face_pause_distance", "face_pause_distance", "contour_start_x",
        "contour_start_z", "contour_name", "contour_segments", "contour_add_segment",
        "contour_delete_segment", "contour_move_up", "contour_move_down", "contour_edge_type",
        "label_contour_edge_size", "contour_edge_size", "parting_contour", "parting_side",
        "parting_tool", "parting_spindle", "parting_feed", "parting_depth_per_pass",
        "parting_mode", "parting_pause_enabled", "parting_pause_distance",
        "label_parting_slice_strategy", "parting_slice_strategy", "label_parting_slice_step",
        "parting_slice_step", "label_parting_allow_undercut", "parting_allow_undercut",
        "label_parting_depth", "label_parting_pause", "label_parting_pause_distance",
        "parting_undercut_mode", "parting_output_preference", "parting_undercut_tool",
        "parting_undercut_spindle", "parting_undercut_feed", "parting_optional_stop_before_undercut",
        "thread_standard", "thread_orientation", "thread_hand", "thread_tool", "thread_spindle",
        "thread_major_diameter", "thread_pitch", "thread_length", "thread_start_z", "thread_passes",
        "thread_safe_z", "thread_depth", "thread_peak_offset", "thread_first_depth",
        "thread_retract_r", "thread_infeed_q", "thread_spring_passes", "thread_e",
        "thread_relief_mode", "thread_relief_norm", "thread_optional_stop_before",
        "thread_l", "btn_thread_preset", "tool_table_path", "lbl_tool_table_path",
        "groove_process_type", "label_groove_process_type", "label_dirty_status",
        "key_mode", "key_radial_side", "key_tool", "key_coolant", "key_slot_count",
        "key_slot_start_angle", "key_slot_angle_step", "key_start_diameter", "key_start_z",
        "key_nut_length", "key_nut_depth", "key_cutting_width", "key_top_clearance",
        "key_depth_per_pass", "key_plunge_feed", "key_use_c_axis", "key_use_c_axis_switch",
        "key_c_axis_switch_p",
    ):
        setattr(handler, attr_name, getattr(handler.w, attr_name, None))

    handler._contour_edge_template_data = "none"
    handler._contour_edge_template_size = 0.0
    handler._contour_arc_template_data = "auto"
    handler._contour_row_user_selected = False
    handler._op_row_user_selected = False
    handler._setup_parting_slice_strategy_items()
    if handler.label_parting_slice_step is not None:
        try:
            handler.label_parting_slice_step.setVisible(False)
        except Exception:
            pass
    if handler.parting_slice_step is not None:
        try:
            handler.parting_slice_step.setVisible(False)
        except Exception:
            pass

    handler.root_widget = handler._find_root_widget()
    handler._setup_resolver()
    handler._unit_last_index = -1


def finalize_ui_ready(handler) -> None:
    """Run the late UI binding pass after the panel widget tree exists."""
    handler._startup_mark("_finalize_ui_ready enter")
    if not getattr(handler, "w", None):
        handler._log("[LatheEasyStep] _finalize_ui_ready: widgets not ready (no program_unit) - deferring", level="info")
        return

    if getattr(handler, "_ui_finalized", False):
        return
    if getattr(handler, "_finalize_ui_ready_running", False):
        return
    handler._finalize_ui_ready_running = True
    handler._finalize_pass = getattr(handler, "_finalize_pass", 0) + 1
    handler._log(f"[LatheEasyStep] _finalize_ui_ready pass {handler._finalize_pass}", level="info")
    try:
        try:
            handler.root_widget = getattr(handler, "root_widget", None) or handler._find_root_widget()
            handler._startup_mark("_finalize_ui_ready: load_split_tab_uis begin")
            load_split_tab_uis(handler)
            handler._startup_mark("_finalize_ui_ready: load_split_tab_uis end")
            handler._startup_mark("_finalize_ui_ready: load_step_management_uis begin")
            load_step_management_uis(handler)
            handler._startup_mark("_finalize_ui_ready: load_step_management_uis end")
            handler._startup_mark("_finalize_ui_ready: load_preview_uis begin")
            load_preview_uis(handler)
            handler._startup_mark("_finalize_ui_ready: load_preview_uis end")
            handler.root_widget = getattr(handler, "root_widget", None) or handler._find_root_widget()
            _install_workspace_splitter(handler)
        except Exception as exc:
            handler._log(f"[LatheEasyStep] split UI load failed: {exc}", level="warning")
        try:
            handler._startup_mark("_finalize_ui_ready: register_known_widgets begin")
            handler._register_known_widgets()
            handler._rebuild_widget_name_cache()
            handler._startup_mark("_finalize_ui_ready: register_known_widgets end")
        except Exception:
            pass

        handler._startup_mark("_finalize_ui_ready: ensure_core_widgets begin")
        handler._ensure_core_widgets()
        handler._startup_mark("_finalize_ui_ready: ensure_core_widgets end")
        handler._startup_mark("_finalize_ui_ready: ensure_advanced_widgets begin")
        ensure_advanced_widgets(handler)
        handler._startup_mark("_finalize_ui_ready: ensure_advanced_widgets end")
        # The widget tree is complete now.  Signal setup and presentation use
        # hundreds of name lookups; a fresh authoritative index prevents every
        # absent optional name from scanning the full embedded QtDragon tree.
        handler._rebuild_widget_name_cache()
        handler._widget_name_cache_authoritative = True
        try:
            # ensure_advanced_widgets() legt Spindelmodus-/Schnittgeschwindigkeits-
            # Felder dynamisch an (Qt-Widgets sind nach dem Erzeugen standardmaessig
            # sichtbar) - ohne diesen Aufruf blieben z. B. Drehzahl- UND
            # Schnittgeschwindigkeitsfeld gleichzeitig sichtbar, bis zufaellig eine
            # andere Aktion (Reiterwechsel, globale Aenderung) die Korrektur ausloest
            # (realer Bugreport: "es darf nur einer der beiden Werte sichtbar sein").
            handler._update_spindle_mode_visibility()
        except Exception:
            pass
        try:
            if handler.root_widget is not None:
                handler.root_widget.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips, True)
                top = handler.root_widget.window()
                if top is not None and top is not handler.root_widget:
                    top.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips, True)
        except Exception:
            pass
        try:
            handler._startup_mark("_finalize_ui_ready: dock_preview_above_scroll begin")
            _dock_preview_above_scroll(handler)
            handler._startup_mark("_finalize_ui_ready: dock_preview_above_scroll end")
        except Exception:
            pass
        if handler.tab_params is not None and handler.tab_params.currentIndex() == 0:
            try:
                handler.tab_params.setCurrentIndex(1)
            except Exception:
                pass
        handler._startup_mark("_finalize_ui_ready: force_attach_core_widgets begin")
        handler._force_attach_core_widgets()
        handler._startup_mark("_finalize_ui_ready: force_attach_core_widgets end")
        if handler.list_ops is None:
            handler.list_ops = handler._find_any_widget("listOperations")
        if handler.list_ops is None:
            # Letzter Rueckfall: bis zu 5s per QTimer-Polling erneut versuchen
            # (ueber die drei festen Durchlaeufe von _finalize_ui_ready hinaus),
            # falls listOperations im Embed-Fall besonders spaet realisiert wird.
            handler._connect_resolver_fallbacks()
        handler.tab_params = handler.tab_params or handler._find_any_widget("tabParams")
        handler.btn_add = handler.btn_add or handler._find_any_widget("id:34721") or handler._find_any_widget("btnAdd")
        handler.btn_delete = handler.btn_delete or handler._find_any_widget("btnDelete")
        handler.btn_move_up = handler.btn_move_up or handler._find_any_widget("btnMoveUp")
        handler.btn_move_down = handler.btn_move_down or handler._find_any_widget("btnMoveDown")
        handler.btn_new_program = handler.btn_new_program or handler._find_any_widget("btnNewProgram")
        handler.btn_generate = handler.btn_generate or handler._find_any_widget("id:34722") or handler._find_any_widget("btnGenerate")
        if handler.btn_add is None:
            handler.btn_add = handler._get_widget_by_name("btnAdd")
        if handler.btn_generate is None:
            handler.btn_generate = handler._get_widget_by_name("btnGenerate")
        if getattr(handler, "btn_save_program", None) is None:
            handler.btn_save_program = getattr(handler, "btn_save_program", None) or handler._find_any_widget("id:34724") or handler._find_any_widget("btnSaveProgram")
        if handler.btn_save_step is None:
            handler.btn_save_step = handler._get_widget_by_name("btn_save_step")
        if handler.btn_load_step is None:
            handler.btn_load_step = handler._get_widget_by_name("btn_load_step")
        handler.contour_add_segment = handler.contour_add_segment or handler._find_any_widget("contour_add_segment")
        handler.contour_delete_segment = handler.contour_delete_segment or handler._find_any_widget("contour_delete_segment")
        handler.contour_move_up = handler.contour_move_up or handler._find_any_widget("contour_move_up")
        handler.contour_move_down = handler.contour_move_down or handler._find_any_widget("contour_move_down")
        handler._startup_mark("_finalize_ui_ready: ensure_contour_widgets begin")
        handler._ensure_contour_widgets()
        handler._init_contour_table()
        handler._startup_mark("_finalize_ui_ready: ensure_contour_widgets end")
        try:
            handler._log(f"[LatheEasyStep] core widgets FIX: add={handler.btn_add} del={handler.btn_delete} list={handler.list_ops}", level="info")
        except Exception:
            pass
        handler._startup_mark("_finalize_ui_ready: ensure_preview_widgets begin")
        handler._ensure_preview_widgets()
        handler._setup_slice_view()
        handler._startup_mark("_finalize_ui_ready: ensure_preview_widgets end")
        handler._startup_mark("_finalize_ui_ready: connect_core_signals begin")
        handler._connect_core_signals()
        handler._startup_mark("_finalize_ui_ready: connect_core_signals end")
        try:
            handler._startup_mark("_finalize_ui_ready: connect_remaining_signals begin")
            handler._startup_mark("_finalize_ui_ready: connect_param_change_signals begin")
            handler._connect_param_change_signals()
            handler._startup_mark("_finalize_ui_ready: connect_param_change_signals end")
            handler._startup_mark("_finalize_ui_ready: connect_global_form_signals begin")
            handler._connect_global_form_signals()
            handler._startup_mark("_finalize_ui_ready: connect_global_form_signals end")
            handler._startup_mark("_finalize_ui_ready: connect_language_signal begin")
            handler._connect_language_signal()
            handler._startup_mark("_finalize_ui_ready: connect_language_signal end")
            handler._startup_mark("_finalize_ui_ready: connect_tool_preview_signals begin")
            handler._connect_tool_preview_signals()
            handler._startup_mark("_finalize_ui_ready: connect_tool_preview_signals end")
            handler._startup_mark("_finalize_ui_ready: connect_mode_visibility_signals begin")
            handler._connect_mode_visibility_signals()
            handler._startup_mark("_finalize_ui_ready: connect_mode_visibility_signals end")
            handler._startup_mark("_finalize_ui_ready: connect_remaining_signals end")
        except Exception as exc:
            handler._log(f"[LatheEasyStep] finalize signal setup failed: {exc}", level="warning")
        handler._ensure_core_widgets()

        handler._startup_mark("_finalize_ui_ready: update_parting_choices begin")
        handler._update_parting_contour_choices()
        handler._update_parting_ready_state()
        handler._startup_mark("_finalize_ui_ready: update_parting_choices end")
        try:
            handler._startup_mark("_finalize_ui_ready: presentation: apply_tab_titles begin")
            handler._apply_tab_titles(handler._current_language_code())
            handler._startup_mark("_finalize_ui_ready: presentation: apply_tab_titles end")
            handler._startup_mark("_finalize_ui_ready: presentation: handle_global_change begin")
            handler._handle_global_change()
            handler._startup_mark("_finalize_ui_ready: presentation: handle_global_change end")
            handler._startup_mark("_finalize_ui_ready: presentation: apply_language_texts begin")
            handler._apply_language_texts()
            handler._startup_mark("_finalize_ui_ready: presentation: apply_language_texts end")
        except Exception as exc:
            handler._log(f"[LatheEasyStep] UI presentation failed: {exc}", level="warning")
        for name in ("program_xt_absolute", "program_zt_absolute"):
            widget = handler._get_widget_by_name(name)
            if widget is not None:
                try:
                    widget.setVisible(False)
                except Exception:
                    pass
        try:
            if getattr(handler, "w", None) is not None:
                try:
                    setattr(handler.w, "ui_ready", True)
                except Exception:
                    try:
                        handler.w.setProperty("ui_ready", True)
                    except Exception:
                        pass
        except Exception:
            pass

        critical_ok = all([
            handler.list_ops is not None,
            handler.btn_add is not None,
            handler.btn_generate is not None,
            handler.tab_params is not None,
        ])
        if critical_ok:
            handler._ui_finalized = True
            handler._startup_complete = True
            handler._startup_in_progress = False
            handler._log(
                f'[LatheEasyStep] _finalize_ui_ready DONE after pass {getattr(handler, "_finalize_pass", "?")} — '
                f'all critical widgets found, skipping further passes',
                level="info",
            )
            handler._startup_mark("_finalize_ui_ready critical done")
        else:
            missing = [name for name, widget in [
                ("list_ops", handler.list_ops), ("btn_add", handler.btn_add),
                ("btn_generate", handler.btn_generate), ("tab_params", handler.tab_params),
            ] if widget is None]
            handler._log(
                f'[LatheEasyStep] _finalize_ui_ready pass {getattr(handler, "_finalize_pass", "?")} — '
                f'still missing: {missing}, will retry on next timer',
                level="info",
            )
    finally:
        handler._finalize_ui_ready_running = False


def _dock_preview_above_scroll(handler) -> None:
    if getattr(handler, "_preview_docked", False):
        return
    root = getattr(handler, "root_widget", None) or handler._find_root_widget()
    if root is None:
        return
    scroll = root.findChild(QtWidgets.QScrollArea, "scrollParams", QtCore.Qt.FindChildrenRecursively)
    preview = root.findChild(QtWidgets.QWidget, "previewWidget", QtCore.Qt.FindChildrenRecursively)
    preview_slice = root.findChild(QtWidgets.QWidget, "previewSliceWidget", QtCore.Qt.FindChildrenRecursively)
    button = root.findChild(QtWidgets.QAbstractButton, "btn_slice_view", QtCore.Qt.FindChildrenRecursively)
    reset_button = root.findChild(QtWidgets.QAbstractButton, "btn_reset_view", QtCore.Qt.FindChildrenRecursively)
    if scroll is None or preview is None or preview_slice is None:
        return
    right_layout = scroll.parentWidget().layout() if scroll.parentWidget() is not None else None
    if right_layout is None or right_layout.indexOf(preview) >= 0:
        return
    container = root.findChild(QtWidgets.QWidget, "previewDockContainer", QtCore.Qt.FindChildrenRecursively)
    if container is None:
        # LES-024: previewWidget/previewSliceWidget/btn_slice_view koennen
        # heute aus einem eigenen Panel-Modul (ui_parts/previewPanel.ui,
        # geladen in einen anfangs leeren "previewPanel"-Container im
        # Scroll-Bereich) stammen. Nach dem Reparenting unten bleibt dieser
        # Container leer im Scroll-Bereich zurueck - ohne Kollabieren
        # beansprucht er weiterhin Platz in dessen Layout und verschiebt
        # dadurch sichtbar die Groesse der angedockten Vorschau (real per
        # Screenshot-Vergleich gefunden, siehe TODO.md LES-024).
        old_parent = preview.parentWidget()

        container = QtWidgets.QWidget(scroll.parentWidget())
        container.setObjectName("previewDockContainer")
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        dock_layout = QtWidgets.QVBoxLayout(container)
        dock_layout.setContentsMargins(0, 0, 0, 0)
        dock_layout.setSpacing(6)
        if button is not None or reset_button is not None:
            controls = QtWidgets.QHBoxLayout()
            controls.addStretch(1)
            if reset_button is not None:
                controls.addWidget(reset_button)
            if button is not None:
                controls.addWidget(button)
            dock_layout.addLayout(controls)
        preview_row = QtWidgets.QHBoxLayout()
        preview_row.setContentsMargins(0, 0, 0, 0)
        preview_row.setSpacing(8)
        preview_row.addWidget(preview, 3)
        preview_row.addWidget(preview_slice, 2)
        dock_layout.addLayout(preview_row)
        try:
            preview.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            preview_slice.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            preview.setMinimumHeight(140)
            preview_slice.setMinimumHeight(140)
            preview_slice.setMinimumWidth(240)
        except Exception:
            pass
        # LES-050: Vorschau und Parameterbereich werden durch einen vertikalen
        # Splitter getrennt. Die Vorschau bleibt oben, kann aber nun fuer eine
        # Detailpruefung vergroessert oder zugunsten der Parameter verkleinert
        # werden.
        splitter = root.findChild(QtWidgets.QSplitter, "previewParamsSplitter", QtCore.Qt.FindChildrenRecursively)
        if splitter is None:
            scroll_index = right_layout.indexOf(scroll)
            right_layout.removeWidget(scroll)
            splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, scroll.parentWidget())
            splitter.setObjectName("previewParamsSplitter")
            splitter.setChildrenCollapsible(False)
            splitter.addWidget(container)
            splitter.addWidget(scroll)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 1)
            right_layout.insertWidget(max(0, scroll_index), splitter, 1)
            splitter.setSizes([180, 520])
            # LES-050: gemerkte Aufteilung aus einer frueheren Sitzung
            # wiederherstellen, falls plausibel - sonst bleibt es bei der
            # sicheren Standardaufteilung oben.
            _restore_splitter_sizes(splitter, _PREVIEW_PARAMS_SPLITTER_SETTINGS_KEY, (140, 100))
            splitter.splitterMoved.connect(
                lambda *_args: _persist_splitter_sizes(splitter, _PREVIEW_PARAMS_SPLITTER_SETTINGS_KEY)
            )
        try:
            # addWidget() above already reparented preview/preview_slice/
            # button away from old_parent (Qt removes a widget from its
            # previous layout automatically). Only a leftover spacer item
            # (no QWidget) can remain. Merely hiding the now-empty widget
            # was NOT enough (real screenshot comparison, LES-024): its
            # outer shell container (previewPanel) still occupied a
            # QVBoxLayout item slot in the scroll area, and that leftover
            # inter-item spacing was enough to shift how much height the
            # docked preview vs. the tab area received (140px vs 220px in
            # testing) - so the empty container must be fully REMOVED from
            # its parent layout, not just hidden.
            if (
                old_parent is not None
                and old_parent is not container
                and old_parent is not scroll
                and not old_parent.findChildren(QtWidgets.QWidget)
            ):
                empty_shell = old_parent.parentWidget()
                target = empty_shell if empty_shell is not None and empty_shell is not scroll else old_parent
                grandparent = target.parentWidget()
                parent_layout = grandparent.layout() if grandparent is not None else None
                if parent_layout is not None:
                    parent_layout.removeWidget(target)
                target.setParent(None)
                target.deleteLater()
        except Exception:
            pass
    handler._preview_docked = True


# Kompatibilitaet fuer externe Aufrufer und aeltere Tests. Die historische
# Funktion dockt heute bewusst oberhalb statt unterhalb des Scrollbereichs.
_dock_preview_below_scroll = _dock_preview_above_scroll


def _install_workspace_splitter(handler) -> None:
    """Replace the fixed Step/parameter columns with a horizontal splitter."""
    root = getattr(handler, "root_widget", None) or handler._find_root_widget()
    if root is None:
        return
    existing = root.findChild(QtWidgets.QSplitter, "workspaceSplitter", QtCore.Qt.FindChildrenRecursively)
    if existing is not None:
        return
    outer = root.findChild(QtWidgets.QHBoxLayout, "horizontalLayout", QtCore.Qt.FindChildrenRecursively)
    right_layout = root.findChild(QtWidgets.QVBoxLayout, "rightLayout", QtCore.Qt.FindChildrenRecursively)
    step_panel = root.findChild(QtWidgets.QWidget, "stepListPanel", QtCore.Qt.FindChildrenRecursively)
    if outer is None or right_layout is None or step_panel is None:
        return
    if outer.indexOf(step_panel) < 0 or outer.indexOf(right_layout) < 0:
        return

    while outer.count():
        outer.takeAt(0)
    right_layout.setParent(None)
    right_panel = QtWidgets.QWidget(root)
    right_panel.setObjectName("rightWorkspacePanel")
    # LES-050 Regressionsfund: 360/190 stammten aus der Zeit vor den
    # zweispaltigen Button-Grids (stepListPanel/stepActionsPanel, siehe
    # ui_parts/*.ui) und lagen unter deren tatsaechlichem minimumSizeHint -
    # die Buttons wurden dadurch unterhalb ihrer Textbreite zusammengepresst.
    # Werte an das gemessene minimumSizeHint der Grids angelehnt (mit etwas
    # Reserve fuer Schriftart-/Stilunterschiede ausserhalb des Offscreen-
    # Messlaufs).
    right_panel.setMinimumWidth(380)
    right_panel.setLayout(right_layout)
    step_panel.setMinimumWidth(330)

    splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, root)
    splitter.setObjectName("workspaceSplitter")
    splitter.setChildrenCollapsible(False)
    splitter.addWidget(step_panel)
    splitter.addWidget(right_panel)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    # LES-050 Regressionsfund (eingebettetes QtDragon-Panel): dessen
    # gemerkte Fenstergroesse kann der Tab-Flaeche weniger Breite geben, als
    # unsere Mindestbreite braucht (live beobachtet: 638px verfuegbar vs.
    # 710px benoetigt) - ohne Scroll-Wrapper wurde die zweite Button-Spalte
    # dabei nicht nur gequetscht, sondern komplett unsichtbar und nicht
    # klickbar abgeschnitten (die QtDragon-Tab-Seite selbst bietet keine
    # Scrollleiste). Eine QScrollArea macht den Splitter unabhaengig von der
    # tatsaechlichen Host-Breite erreichbar: passt der Host, wird nichts
    # sichtbar veraendert (widgetResizable liefert dieselbe Breite wie
    # zuvor); ist der Host schmaler als das Mindestmass, erscheint eine
    # horizontale Scrollleiste statt Inhalte zu verlieren.
    workspace_scroll = QtWidgets.QScrollArea(root)
    workspace_scroll.setObjectName("workspaceScrollArea")
    workspace_scroll.setWidgetResizable(True)
    workspace_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    workspace_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
    workspace_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    workspace_scroll.setWidget(splitter)
    outer.addWidget(workspace_scroll)
    splitter.setSizes([340, 700])
    # LES-050: gemerkte Aufteilung aus einer frueheren Sitzung
    # wiederherstellen, falls plausibel (mindestens so breit wie die
    # gemessenen Mindestbreiten der Button-Grids) - sonst bleibt es bei der
    # sicheren Standardaufteilung oben.
    _restore_splitter_sizes(
        splitter, _WORKSPACE_SPLITTER_SETTINGS_KEY,
        (step_panel.minimumWidth(), right_panel.minimumWidth()),
    )
    splitter.splitterMoved.connect(
        lambda *_args: _persist_splitter_sizes(splitter, _WORKSPACE_SPLITTER_SETTINGS_KEY)
    )
    # LES-050: das Gesamtfenster darf nicht schmaler werden, als beide
    # Splitterseiten zusammen an Mindestbreite brauchen - sonst wuerde der
    # Splitter selbst innerhalb seines eigenen Minimums wieder Buttontext
    # abschneiden muessen. +40px Reserve fuer Splitter-Griff/Aussenraender.
    #
    # REGRESSIONSFUND (eingebettetes QtDragon-Panel, 2026-09-15): hier auf
    # `root` selbst gesetzt, zwang das root dazu, breiter zu sein als sein
    # eigener Elterncontainer innerhalb der QtDragon-Tab-Flaeche (live
    # beobachtet: root auf 750px erzwungen, Elterncontainer aber nur 592px
    # breit) - und genau an dieser Grenze (root zu seinem Elter, NICHT
    # innerhalb unseres eigenen Splitters/der obigen QScrollArea) wurde ohne
    # jede Scrollmoeglichkeit abgeschnitten: die zweite Button-Spalte war
    # unsichtbar und nicht klickbar, obwohl die QScrollArea intern korrekt
    # auf "kein Ueberlauf" kam. `root.window()` ist im Standalone-Fall root
    # selbst (identisches Verhalten wie zuvor, WM erzwingt weiterhin ein
    # sinnvolles Minimum), im eingebetteten Fall dagegen QtDragons eigenes,
    # ohnehin schon deutlich breiteres Hauptfenster - dort wirkungslos (kein
    # erzwungenes Aufblasen von root mehr), sodass root auf die tatsaechlich
    # verfuegbare Host-Breite schrumpfen darf und die QScrollArea oben genau
    # dafuer greift.
    root.window().setMinimumWidth(step_panel.minimumWidth() + right_panel.minimumWidth() + 40)
