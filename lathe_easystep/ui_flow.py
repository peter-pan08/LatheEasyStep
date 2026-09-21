from __future__ import annotations

import os
import re
import time

from qtvcp.core import Action
from qtpy import QtCore, QtWidgets

from .gcode_utils import is_internal_side, is_left_hand
from .model import Operation, OpType
from .comments import is_generated_comment, update_auto_comment
from .ui_helpers import translate as _tr
from .ui_messages import format_user_error, parse_error_location
from .ui_step_list_view import StepListView

_ERROR_HIGHLIGHT_STYLE = "border: 2px solid #d9534f; background-color: #fff3f3;"

_looks_like_generated_step_comment = is_generated_comment
_ERROR_HIGHLIGHT_DURATION_MS = 4000


def _flash_error_highlight(widget) -> None:
    try:
        original = widget.styleSheet()
    except Exception:
        return
    try:
        widget.setStyleSheet(_ERROR_HIGHLIGHT_STYLE)
        QtCore.QTimer.singleShot(_ERROR_HIGHLIGHT_DURATION_MS, lambda: widget.setStyleSheet(original))
    except Exception:
        pass


def jump_to_error_location(handler, exc: Exception) -> None:
    """Springt beim Fehlschlagen der G-Code-Erzeugung automatisch zum
    betroffenen Step und Reiter und hebt das fehlerhafte Feld kurz hervor,
    damit der Nutzer genau sieht, was zu aendern ist."""
    location = parse_error_location(exc)
    op_number = location.get("op_number")
    op_type = location.get("op_type")
    field_key = location.get("field_key")
    try:
        handler._log(f"[LatheEasyStep][debug] jump_to_error_location: {location}", level="debug")
    except Exception:
        pass
    if not op_number:
        return
    list_ops = getattr(handler, "list_ops", None)
    if list_ops is None:
        return
    row = op_number - 1
    try:
        count = list_ops.count()
    except Exception:
        return
    if row < 0 or row >= count:
        return
    try:
        list_ops.setCurrentRow(row)
        handler._handle_selection_change(row)
    except Exception:
        return
    if not field_key or not op_type:
        return
    widgets = getattr(handler, "param_widgets", None) or {}
    widget = widgets.get(op_type, {}).get(field_key)
    if widget is None:
        return
    try:
        widget.setFocus()
    except Exception:
        pass
    _flash_error_highlight(widget)


def _translate_value(handler, prefix: str, value) -> str:
    normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not normalized:
        return ""
    text = _tr(handler, f"{prefix}.{normalized}")
    return value if text == f"{prefix}.{normalized}" else text


def tool_change_position_lines(header: dict[str, object]) -> list[str]:
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

    lines: list[str] = []

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


def build_gcode_lines(handler):
    if not handler._tool_table.tools:
        try:
            handler._auto_load_tool_table()
        except Exception:
            pass
    header = handler._collect_program_header()
    handler.model.program_settings = header
    handler.model.program_settings["tools"] = handler._tool_table.tools
    handler.model.spindle_speed_max = float(header.get("s1_max") or 0.0)
    unique_tools = set()
    for op in handler.model.operations:
        if op.op_type == OpType.PROGRAM_HEADER:
            continue
        try:
            val = op.params.get("tool")
            tool_val = int(float(val)) if val is not None else 0
        except Exception:
            tool_val = 0
        if tool_val > 0:
            unique_tools.add(tool_val)
    if unique_tools:
        xt = header.get("xt")
        zt = header.get("zt")
        if xt is None or zt is None:
            raise ValueError("Bitte XT und ZT im Programm-Tab eintragen, da ein Werkzeugwechsel ausgegeben wird.")
    header_lines = tool_change_position_lines(header)
    footer_lines = tool_change_position_lines(header)
    handler.model.program_settings["header_lines"] = header_lines
    handler.model.program_settings["footer_lines"] = footer_lines
    return handler.model.generate_gcode()


def handle_add_operation(handler) -> None:
    # Sicherheitsnetz: Widgets nachziehen, falls sie erst spaeter verfuegbar sind
    handler._ensure_core_widgets()
    handler._force_attach_core_widgets()
    if not handler._tool_table.tools:
        try:
            handler._auto_load_tool_table()
        except Exception:
            pass
    # Schutz gegen doppelte Ausloesung (UI kann Click-Events doppelt feuern)
    if handler._runtime.adding_operation:
        return
    now = time.monotonic()
    if now - handler._runtime.last_add_operation_ts < 0.8:
        return
    handler._runtime.last_add_operation_ts = now
    handler._runtime.adding_operation = True
    try:
        try:
            handler._log("[LatheEasyStep] add operation triggered", level="info")
        except Exception:
            pass
        op_type = handler._current_op_type()
        if op_type == OpType.PROGRAM_HEADER:
            params = handler._collect_program_header()
            # nur einen Programmkopf zulassen -> ersetzen oder neu hinzufuegen
            for i, existing in enumerate(handler.model.operations):
                if existing.op_type == OpType.PROGRAM_HEADER:
                    # SICHERHEITSFUND 2026-09-20 (LES-052 Abschnitt 3, Fund
                    # 3b): anders als beim Neu-Einfuegen unten (das
                    # update_geometry() VOR dem Insert aufruft) fehlte hier
                    # jede Validierung - existing.params wurde ungeprueft
                    # uebernommen. Erst auf einem noch nicht uebernommenen
                    # Kandidaten validieren, damit ein ungueltiger Wert den
                    # bestehenden Kopf unveraendert laesst (wirft weiter,
                    # gleiches Verhalten wie der Insert-Zweig).
                    candidate = Operation(op_type, params)
                    handler.model.update_geometry(candidate)
                    existing.params = params
                    try:
                        handler._mark_dirty(program=True)
                    except Exception:
                        pass
                    if handler.list_ops:
                        item = handler.list_ops.item(i)
                        if item:
                            item.setText(handler._describe_operation(existing, i + 1))
                        handler.list_ops.setCurrentRow(i)
                    handler._refresh_preview()
                    return
            # noch kein Programmkopf: vorne einfuegen
            op = Operation(op_type, params)
            handler.model.update_geometry(op)
            handler.model.operations.insert(0, op)
            try:
                handler._reindex_dirty_operations_after_insert(0)
            except Exception:
                pass
            # SICHERHEITSFUND 2026-09-20 (LES-052 Abschnitt 3, Fund 3): das
            # ist der einzige Weg, wie ein neues Programm ueberhaupt seinen
            # ersten Programmkopf bekommt - bisher wurde hier nie dirty
            # markiert.
            try:
                handler._mark_program_structure_dirty()
            except Exception:
                pass
            handler._refresh_operation_list(select_index=0)
            handler._refresh_preview()
        else:
            params = handler._collect_params(op_type)
            if op_type == OpType.ABSPANEN:
                contour_name = handler._current_parting_contour_name()
                contour_path = handler._resolve_contour_path(contour_name)
                if not contour_name or not contour_path:
                    handler._log("[LatheEasyStep] Abspanen benoetigt eine vorhandene Kontur-Auswahl", level="info")
                    handler._update_parting_ready_state()
                    return
                params["contour_name"] = contour_name
                params["source_path"] = contour_path
            op = Operation(op_type, params)
            handler.model.update_geometry(op)
            parent = handler.root_widget or handler._find_root_widget()
            settings = QtCore.QSettings()
            next_index = len(handler.model.operations)
            if any(existing.op_type == OpType.PROGRAM_HEADER for existing in handler.model.operations):
                next_index += 1
            if not handler._ensure_step_file_link(
                op,
                index_hint=next_index,
                parent=parent,
                settings=settings,
            ):
                handler._log("[LatheEasyStep] add operation cancelled: no step file selected", level="info")
                return
            handler.model.add_operation(op)
            # Kommentar leer -> Erstbefuellung; sieht er bereits wie eine
            # maschinell nummerierte Beschreibung aus -> Nummer auffrischen
            # (gleiche Regel wie _insert_loaded_operation(), LES-023). Ein
            # bewusst individueller Kommentar bleibt unangetastet.
            if _looks_like_generated_step_comment(op.params.get("comment")):
                update_auto_comment(op, handler._describe_operation(op, len(handler.model.operations)))
            try:
                handler._mark_program_structure_dirty(operation_indices={len(handler.model.operations) - 1})
            except Exception:
                pass
            try:
                debug_ops = [f"{i}:{o.op_type}" for i, o in enumerate(handler.model.operations)]
                handler._log(f"[LatheEasyStep][debug] operations now: {debug_ops}", level="debug")
            except Exception:
                pass

            handler._refresh_operation_list(select_index=len(handler.model.operations) - 1)
            handler._refresh_preview()
            handler._update_parting_ready_state()
    finally:
        handler._runtime.adding_operation = False


def handle_delete_operation(handler) -> None:
    if handler._runtime.deleting:
        return
    handler._runtime.deleting = True
    try:
        if handler.list_ops is None:
            return
        idx = handler.list_ops.currentRow()
        handler._log(
            f"[LatheEasyStep] delete: currentRow={idx}, "
            f"ops_count={len(handler.model.operations)}",
            level="info",
        )
        if idx < 0 or idx >= len(handler.model.operations):
            return
        if idx == 0:
            parent = handler.root_widget or handler._find_root_widget()
            if parent is not None:
                try:
                    QtWidgets.QMessageBox.warning(
                        parent,
                        _tr(handler, "dialog.delete.title"),
                        _tr(handler, "message.delete.program_header_forbidden"),
                    )
                except Exception:
                    handler._log(
                        "[LatheEasyStep] blocked delete of program header without Qt parent",
                        level="warning",
                    )
            else:
                handler._log(
                    "[LatheEasyStep] blocked delete of program header without Qt parent",
                    level="warning",
                )
            return
        handler.model.remove_operation(idx)
        try:
            handler._reindex_dirty_operations_after_removal(idx)
        except Exception:
            pass
        try:
            handler._mark_program_structure_dirty()
        except Exception:
            pass
        new_idx = min(idx, len(handler.model.operations) - 1)
        handler._refresh_operation_list(select_index=new_idx)
        handler._renumber_operations()
        handler._refresh_preview()
    finally:
        handler._runtime.deleting = False


def refresh_operation_list(handler, select_index: int) -> None:
    """Synchronisiert die linke Operationsliste mit dem internen Modell."""
    if handler.list_ops is not None:
        try:
            if handler.list_ops.objectName() not in ("listOperations", "list_ops"):
                handler.list_ops = None
        except Exception:
            handler.list_ops = None

    if handler.list_ops is None:
        root = handler.root_widget or handler._find_root_widget()
        if root:
            for w in root.findChildren(QtWidgets.QListWidget):
                if w.objectName() in ("listOperations", "list_ops"):
                    handler.list_ops = w
                    break

    if handler.list_ops is None:
        handler._update_parting_contour_choices()
        return

    # Nur die Operations-Liste updaten (nicht andere QListWidgets).
    for lst in [handler.list_ops]:
        lst.blockSignals(True)
        handler._op_row_user_selected = False
        lst.clear()
        for i, op in enumerate(handler.model.operations):
            lst.addItem(handler._describe_operation(op, i + 1))

        if 0 <= select_index < lst.count():
            lst.setCurrentRow(select_index)
        elif lst.count() > 0:
            lst.setCurrentRow(lst.count() - 1)
        lst.blockSignals(False)
        try:
            if getattr(handler, "_verbose_widget_logs", False):
                items = [lst.item(i).text() for i in range(lst.count())]
                handler._log(
                    f"[LatheEasyStep][debug] list '{lst.objectName()}' "
                    f"count={lst.count()} items={items} vis={lst.isVisible()} "
                    f"size={lst.size()}", level="debug")
            # Sichtbarkeit erzwingen - eigener Style gegen dunkle QSS
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

    handler._update_parting_contour_choices()
    handler._update_save_step_button_state()
    handler._update_operation_action_button_states()


def handle_param_change(handler) -> None:
    """Generic handler for parameter widgets (spinboxes, combos, checkboxes, lineedits)."""
    try:
        w = handler.sender()
    except Exception:
        return
    if w is None:
        return

    # Determine current operation
    idx = -1
    try:
        if handler.list_ops is not None:
            idx = int(handler.list_ops.currentRow())
    except Exception:
        idx = -1

    if idx < 0 or idx >= len(handler.model.operations):
        return

    op = handler.model.operations[idx]
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

    handler._log(f"[LatheEasyStep][debug] param change: widget={name} op_type={op.op_type} row={idx} value={val!r}", level="debug")

    # Do NOT write widget.objectName() directly into op.params.
    # The authoritative mapping is built by _collect_params(op_type),
    # so we rebuild the selected operation from the UI and refresh geometry/preview.
    try:
        handler._update_selected_operation(force=True)
    except Exception as exc:
        # SICHERHEITSFUND 2026-09-20 (LES-052 Abschnitt 3): _sync_form_to_
        # operation() rollt op.params bei einer ungueltigen Eingabe bereits
        # korrekt zurueck, bevor sie hier erneut geworfen wird - das darf
        # aber nicht lautlos zu "dirty" fuehren, obwohl inhaltlich nichts
        # uebernommen wurde, und das editierte Widget darf nicht auf dem
        # abgelehnten Wert stehen bleiben. Formular mit dem (bereits
        # zurueckgerollten) Modellzustand neu synchronisieren, dirty NICHT
        # markieren, bestehenden Dirty-Zustand unangetastet lassen.
        try:
            handler._log(f"[LatheEasyStep][debug] param change rejected: widget={name} op_type={op.op_type} row={idx}: {exc!r}", level="warning")
        except Exception:
            pass
        try:
            handler._load_params_to_form(op)
        except Exception:
            pass
        return
    if name.endswith("_spindle_mode"):
        try:
            handler._update_spindle_mode_visibility()
        except Exception:
            pass
    try:
        if op.op_type == OpType.PROGRAM_HEADER:
            handler._mark_dirty(program=True)
        else:
            handler._mark_dirty(operation_index=idx)
    except Exception:
        pass


def handle_move_up(handler):
    if handler._runtime.moving_up:
        return
    handler._runtime.moving_up = True
    try:
        step_list = StepListView(handler)
        if not step_list.is_bound():
            return
        idx = step_list.selected_row()
        if idx <= 0:
            return
        operations = getattr(handler.model, "operations", None)
        if operations is not None:
            if idx >= len(operations) or (
                getattr(operations[idx], "op_type", None) == OpType.PROGRAM_HEADER
                or getattr(operations[idx - 1], "op_type", None) == OpType.PROGRAM_HEADER
            ):
                return
        handler.model.move_up(idx)
        try:
            handler._swap_dirty_operation_indices(idx - 1, idx)
        except Exception:
            pass
        try:
            handler._mark_program_structure_dirty()
        except Exception:
            pass
        handler._refresh_operation_list(select_index=idx - 1)
        handler._renumber_operations()
        handler._refresh_preview()
    finally:
        handler._runtime.moving_up = False


def handle_move_down(handler):
    if handler._runtime.moving_down:
        return
    handler._runtime.moving_down = True
    try:
        step_list = StepListView(handler)
        if not step_list.is_bound():
            return
        idx = step_list.selected_row()
        if idx < 0 or idx >= step_list.count() - 1:
            return
        operations = getattr(handler.model, "operations", None)
        if operations is not None:
            if idx >= len(operations) or getattr(operations[idx], "op_type", None) == OpType.PROGRAM_HEADER:
                return
        handler.model.move_down(idx)
        try:
            handler._swap_dirty_operation_indices(idx, idx + 1)
        except Exception:
            pass
        try:
            handler._mark_program_structure_dirty()
        except Exception:
            pass
        handler._refresh_operation_list(select_index=idx + 1)
        handler._renumber_operations()
        handler._refresh_preview()
    finally:
        handler._runtime.moving_down = False


def handle_new_program(handler):
    if handler._runtime.creating_new_program:
        return
    handler._runtime.creating_new_program = True
    try:
        handler.model.operations.clear()
        handler._current_program_path = None
        handler._current_gcode_path = None
        handler._op_row_user_selected = False
        try:
            handler._clear_dirty_state()
        except Exception:
            pass
        try:
            # Werkzeugtabelle bleibt ueber "Neues Programm" hinweg geladen;
            # Combos ggf. erst jetzt verfuegbarer Reiter-Widgets werden mit
            # der bereits geladenen Tabelle aufgefrischt.
            if handler._tool_table.tools:
                handler._populate_tool_combos(handler._tool_table.tools)
        except Exception:
            pass
        handler._refresh_operation_list(select_index=-1)
        handler._refresh_preview()
    finally:
        handler._runtime.creating_new_program = False


def handle_generate_gcode(handler):
    if handler._runtime.generating_gcode:
        return
    handler._runtime.generating_gcode = True
    try:
        header = handler._collect_program_header()
        settings = QtCore.QSettings()
        default_filepath = handler._build_program_filepath(header.get("program_name", ""))
        dialog_dir = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/GcodeLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        default_filename = os.path.basename(default_filepath)
        default_filepath = os.path.join(dialog_dir, default_filename)
        os.makedirs(os.path.dirname(default_filepath), exist_ok=True)
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            handler.root_widget,
            _tr(handler, "dialog.gcode.save.title"),
            default_filepath,
            _tr(handler, "dialog.gcode.filter"),
        )
        if not filepath:
            return
        handler._log(f"[LatheEasyStep][debug] generate gcode: {len(handler.model.operations)} operations -> {filepath}", level="debug")
        t0 = time.monotonic()
        handler._update_selected_operation(force=True)
        handler._write_gcode_file(filepath)
        handler._log(f"[LatheEasyStep][debug] generate gcode finished in {time.monotonic() - t0:.3f}s", level="debug")
        handler._current_gcode_path = handler._normalized_file_path(filepath)
        handler._remember_dialog_path(
            settings,
            filepath,
            "LatheEasyStep/GcodeLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        open_fn = getattr(Action, "CALLBACK_OPEN_PROGRAM", None)
        if callable(open_fn):
            open_fn(filepath)
        else:
            QtWidgets.QMessageBox.information(
                handler.root_widget or None,
                _tr(handler, "dialog.app.title"),
                _tr(handler, "message.gcode.saved_no_auto_open", path=filepath),
            )
            handler._log(f"[LatheEasyStep] Hinweis: Programm geschrieben nach {filepath}, automatisches Öffnen nicht verfügbar", level="info")
    except Exception as exc:
        try:
            jump_to_error_location(handler, exc)
        except Exception:
            pass
        QtWidgets.QMessageBox.critical(
            handler.root_widget or None,
            _tr(handler, "dialog.app.title"),
            format_user_error(handler, exc, fallback_title=_tr(handler, "message.gcode.generate_failed")),
        )
    finally:
        handler._runtime.generating_gcode = False


def describe_operation(handler, op, number=None):
    def wrap(s):
        return f"{int(number)}. {s}" if number is not None else s
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
        return wrap(_tr(handler, "operation.program_header", wcs=wcs))
    if t == OpType.FACE:
        mode = p.get("mode", "schruppen")
        if isinstance(mode, (int, float)):
            mode = {0: "rough", 1: "finish", 2: "rough_finish"}.get(int(mode), "rough")
        mode = "rough" if mode is None else str(mode)
        mode = {
            "schruppen": "rough",
            "schlichten": "finish",
            "schruppen + schlichten": "rough_finish",
        }.get(mode.strip().lower(), mode)
        z_start = p.get("z_start", 0.0)
        z_end = p.get("z_end", 0.0)
        coolant = _tr(handler, "operation.face.coolant_suffix") if p.get("coolant") else ""
        tool = p.get("tool", "T01")
        mode_label = _tr(handler, f"operation.face.mode.{str(mode).replace(' ', '_').replace('+', '_')}")
        return wrap(_tr(handler, "operation.face", mode=mode_label, z_start=fnum(z_start), z_end=fnum(z_end), coolant=coolant, tool=tool))
    if t == OpType.CONTOUR:
        name = str(p.get("name") or "unbenannt").strip()
        return wrap(_tr(handler, "operation.contour", name=name))
    if t == OpType.DRILL:
        return wrap(
            _tr(
                handler,
                "operation.drill",
                mode=_translate_value(handler, "operation.drill.mode", p.get("mode", "normal")),
                z_start=fnum(p.get("z0", 0.0)),
                depth=fnum(p.get("depth", 0.0)),
                tool=p.get("tool", "T01"),
            )
        )
    if t == OpType.GROOVE:
        process_key = "operation.groove.parting" if str(p.get("process_type", "groove")).strip().lower() == "parting" else "operation.groove.groove"
        return wrap(_tr(handler, process_key, z=fnum(p.get("z", 0.0)), width=fnum(p.get("width", 0.0)), tool=p.get("tool", "T01")))
    if t == OpType.THREAD:
        relief = ""
        if str(p.get("relief_mode", "off")).strip().lower() in ("suggest", "suggest_din_relief"):
            relief = _tr(handler, "operation.thread.relief_suffix")
        thread_internal = is_internal_side(p.get("orientation", 0))
        thread_left_hand = is_left_hand(p.get("hand", 0))
        thread_type = _tr(handler, "operation.thread.type.internal") if thread_internal else _tr(handler, "operation.thread.type.external")
        hand = _tr(handler, "operation.thread.hand.left") if thread_left_hand else _tr(handler, "operation.thread.hand.right")
        start_z = float(p.get("thread_start_z", 0.0) or 0.0)
        length = abs(float(p.get("length", 0.0) or 0.0))
        end_z = start_z + ((1.0 if thread_left_hand else -1.0) * length)
        return wrap(
            _tr(
                handler,
                "operation.thread",
                thread_type=thread_type,
                hand=hand,
                pitch=fnum(p.get("pitch", 0.0), 2),
                z_start=fnum(start_z),
                z_end=fnum(end_z),
                relief=relief,
                tool=p.get("tool", "T01"),
            )
        )
    if t == OpType.ABSPANEN:
        relief = str(p.get("undercut_mode", "finish_only"))
        return wrap(
            _tr(
                handler,
                "operation.parting",
                contour=p.get("contour_name", "unknown"),
                strategy=_translate_value(handler, "operation.parting.strategy", p.get("slice_strategy", "parallel_z")),
                relief=_translate_value(handler, "operation.parting.relief", relief),
                tool=p.get("tool", "T01"),
            )
        )
    if t == OpType.KEYWAY:
        slot_count = int(float(p.get("slot_count", 1) or 1))
        return wrap(_tr(handler, "operation.keyway", slots=slot_count, start_z=fnum(p.get("start_z", 0.0)), tool=p.get("tool", "T01")))
    return wrap(f"{t}: {p}")


def renumber_operations(handler):
    """Refresh list numbers and generated descriptions, preserving user comments."""
    step_list = StepListView(handler)
    if not step_list.is_bound():
        return
    for i in range(step_list.count()):
        op = handler.model.operations[i]
        description = handler._describe_operation(op, i + 1)
        step_list.set_item_text(i, description)
        if op.op_type != OpType.PROGRAM_HEADER:
            update_auto_comment(op, description)
