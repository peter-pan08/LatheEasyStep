from __future__ import annotations

import builtins
import json
import os

from qtpy import QtCore, QtWidgets

from .model import OpType
from .ui_helpers import translate as _tr
from .persistence import build_program_data as build_program_data_payload
from .storage import parse_program_payload
from .ui_messages import format_user_error


def build_program_data(handler):
    handler._update_selected_operation(force=True)
    # Abgeleitete Geometrie (u. a. ABSPANEN.source_path) wird bisher nur beim
    # Laden ueber _rebuild_all_operation_geometry() aufgefrischt. Wurde eine
    # Kontur bearbeitet, ohne dass jeder darauf verweisende Abspanen-Step
    # zwischenzeitlich erneut ausgewaehlt wurde, landete beim Speichern
    # weiterhin die veraltete Kontur im gespeicherten Programm (Vorschau in der
    # "alle Steps"-Uebersicht zeigt dann eine andere Kontur als die aktuell
    # gespeicherten Segmente). Vor jedem Speichern ebenfalls auffrischen.
    handler._rebuild_all_operation_geometry()
    header = handler._collect_program_header()
    return build_program_data_payload(
        handler.model.operations,
        header,
        handler._program_file_meta(),
    )


def write_program_file(handler, file_path: str) -> None:
    program_path = handler._normalized_file_path(file_path) or file_path
    previous_program_path = handler._current_program_path
    handler._current_program_path = program_path
    parent = handler.root_widget or handler._find_root_widget()
    settings = QtCore.QSettings()
    base_dir = os.path.dirname(program_path)
    for idx, op in enumerate(handler.model.operations):
        if op.op_type == OpType.PROGRAM_HEADER:
            continue
        if not handler._ensure_step_file_link(
            op,
            index_hint=idx,
            parent=parent,
            settings=settings,
            base_dir=base_dir,
        ):
            raise ValueError("Programmspeichern abgebrochen: fuer mindestens einen Step fehlt eine Step-Datei.")
    program_data = handler._build_program_data()
    with builtins.open(program_path, "w", encoding="utf-8") as handle:
        json.dump(program_data, handle, indent=2, default=str)
    handler._current_program_path = program_path if program_path else previous_program_path


def write_gcode_file(handler, file_path: str) -> None:
    gcode_path = handler._normalized_file_path(file_path) or file_path
    lines = handler._build_gcode_lines()
    with builtins.open(gcode_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    handler._current_gcode_path = gcode_path


def handle_save_step(handler, *, step_file_filter: str) -> None:
    if handler._saving_step:
        return
    handler._saving_step = True
    try:
        idx = handler._selected_operation_index()
        if idx < 0:
            parent = handler.root_widget or handler._find_root_widget()
            QtWidgets.QMessageBox.warning(parent, _tr(handler, "dialog.step.save.title"), _tr(handler, "message.step.select_operation_first"))
            return
        parent = handler.root_widget or handler._find_root_widget()
        settings = QtCore.QSettings()
        start_dir = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        default_name = os.path.join(start_dir, "lathe_step.step.json")
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            _tr(handler, "dialog.step.save.title"),
            default_name,
            step_file_filter,
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".step.json"):
            file_path += ".step.json"
        try:
            handler._update_selected_operation(force=True)
            op = handler.model.operations[idx]
            warning = handler._tool_orientation_mismatch(op)
            if warning:
                QtWidgets.QMessageBox.warning(parent, _tr(handler, "dialog.tool_orientation_check.title"), warning)
            handler._set_step_file_path(op, file_path)
            data = handler._operation_to_step_data(op)
            with builtins.open(file_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(parent, _tr(handler, "dialog.step.save.title"), format_user_error(handler, exc, fallback_title=_tr(handler, "message.step.save_failed")))
            return
        handler._remember_dialog_path(
            settings,
            file_path,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        QtWidgets.QMessageBox.information(parent, _tr(handler, "dialog.step.save.title"), _tr(handler, "message.step.saved", path=file_path))
        try:
            handler._clear_dirty_operation(idx)
            if (
                not handler._dirty_operation_indices
                and not getattr(handler, "_dirty_program_header", False)
                and getattr(handler, "_dirty_program_structure", False)
                and not handler._normalized_file_path(getattr(handler, "_current_program_path", None))
            ):
                handler._clear_program_dirty(structure=True)
        except Exception:
            pass
        try:
            gcode_path = handler._normalized_file_path(getattr(handler, "_current_gcode_path", None))
            if gcode_path and not handler._has_unsaved_changes():
                handler._write_gcode_file(gcode_path)
                handler._remember_dialog_path(
                    settings,
                    gcode_path,
                    "LatheEasyStep/GcodeLastDir",
                    "LatheEasyStep/LastDialogDir",
                )
        except Exception:
            pass
    finally:
        handler._saving_step = False


def handle_load_step(handler, *, step_file_filter: str) -> None:
    if handler._loading_step:
        return
    handler._loading_step = True
    try:
        parent = handler.root_widget or handler._find_root_widget()
        settings = QtCore.QSettings()
        start_dir = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent,
            _tr(handler, "dialog.step.load.title"),
            start_dir,
            step_file_filter,
        )
        if not file_path:
            return
        try:
            with builtins.open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(parent, _tr(handler, "dialog.step.load.title"), _tr(handler, "message.step.open_failed", error=exc))
            return

        op = handler._step_data_to_operation(data)
        if op is None:
            QtWidgets.QMessageBox.warning(parent, _tr(handler, "dialog.step.load.title"), _tr(handler, "message.step.invalid"))
            return
        handler._set_step_file_path(op, file_path)
        handler._insert_loaded_operation(op)
        handler._remember_dialog_path(
            settings,
            file_path,
            "LatheEasyStep/StepLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        handler._update_parting_ready_state()
        handler._setup_groove_tab_ui()
        try:
            handler._clear_dirty_state()
        except Exception:
            pass
    finally:
        handler._loading_step = False


def handle_save_program(handler) -> None:
    parent = handler.root_widget or handler._find_root_widget()
    try:
        settings = QtCore.QSettings()
        default_dir = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/ProgramLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent,
            _tr(handler, "dialog.program.save.title"),
            default_dir,
            _tr(handler, "dialog.program.filter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".lse"):
            file_path += ".lse"
        handler._write_program_file(file_path)
        handler._current_program_path = handler._normalized_file_path(file_path)
        handler._remember_dialog_path(
            settings,
            file_path,
            "LatheEasyStep/ProgramLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        QtWidgets.QMessageBox.information(
            parent,
            _tr(handler, "dialog.program.saved.title"),
            _tr(handler, "message.program.saved", path=file_path),
        )
        try:
            handler._program_dirty = False
            handler._update_dirty_status()
        except Exception:
            pass
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            parent or None,
            _tr(handler, "dialog.program.save_error.title"),
            format_user_error(handler, exc, fallback_title=_tr(handler, "message.program.save_failed")),
        )


def handle_load_program(handler) -> None:
    parent = handler.root_widget or handler._find_root_widget()
    try:
        settings = QtCore.QSettings()
        default_dir = handler._dialog_start_dir(
            settings,
            "LatheEasyStep/ProgramLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent,
            _tr(handler, "dialog.program.load.title"),
            default_dir,
            _tr(handler, "dialog.program.filter"),
        )
        if not file_path:
            return
        with builtins.open(file_path, "r", encoding="utf-8") as handle:
            program_data = json.load(handle)

        handler._remember_dialog_path(
            settings,
            file_path,
            "LatheEasyStep/ProgramLastDir",
            "LatheEasyStep/LastDialogDir",
        )
        try:
            header, ops_data, current_program_path, current_gcode_path = parse_program_payload(
                program_data,
                file_path,
            )
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(parent, _tr(handler, "dialog.program.load.title"), str(exc))
            return

        handler.model.operations.clear()
        handler._op_row_user_selected = False
        handler._active_form_operation_index = -1
        handler._load_program_header_to_form(header)
        handler._current_program_path = current_program_path
        handler._current_gcode_path = current_gcode_path

        for op_dict in ops_data:
            op = handler._step_data_to_operation(op_dict)
            if op is not None:
                handler.model.add_operation(op)

        handler._rebuild_all_operation_geometry()

        try:
            handler._auto_load_tool_table()
        except Exception:
            pass

        # Ausgangspunkt nach dem Laden ist immer der Programmkopf (Zeile 0),
        # nicht der erste fachliche Schritt - unabhaengig davon, wie viele
        # Operationen das geladene Programm enthaelt.
        selected_row = 0
        handler._refresh_operation_list(select_index=selected_row)
        if handler.list_ops is not None and 0 <= selected_row < handler.list_ops.count():
            try:
                handler.list_ops.setCurrentRow(selected_row)
            except Exception:
                pass
            handler._op_row_user_selected = False
            handler._handle_selection_change(selected_row)
        handler._refresh_preview()
        try:
            handler._clear_dirty_state()
        except Exception:
            pass
        QtWidgets.QMessageBox.information(
            parent,
            _tr(handler, "dialog.program.loaded.title"),
            _tr(handler, "message.program.loaded", count=len(ops_data)),
        )
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            parent or None,
            _tr(handler, "dialog.program.load_error.title"),
            format_user_error(handler, exc, fallback_title=_tr(handler, "message.program.load_failed")),
        )


def handle_save_changes(handler) -> None:
    if handler._saving_changes:
        return
    handler._saving_changes = True
    try:
        parent = handler.root_widget or handler._find_root_widget()
        settings = QtCore.QSettings()
        handler._update_selected_operation(force=True)
        handler._log(
            f"[LatheEasyStep] save_changes start: ops={len(handler.model.operations)} "
            f"program_path={handler._current_program_path!r} gcode_path={handler._current_gcode_path!r}",
            level="info",
        )

        saved_steps = 0
        linked_steps = 0
        dirty_step_indices = sorted(int(idx) for idx in getattr(handler, "_dirty_operation_indices", set()) if int(idx) >= 0)
        for idx in dirty_step_indices:
            if idx >= len(handler.model.operations):
                continue
            op = handler.model.operations[idx]
            if op.op_type == OpType.PROGRAM_HEADER:
                continue
            step_path = handler._step_file_path(op)
            handler._log(
                f"[LatheEasyStep] save_changes op#{idx+1} type={op.op_type} step_path={step_path!r}",
                level="info",
            )
            if not step_path:
                continue
            linked_steps += 1
            data = handler._operation_to_step_data(op)
            with builtins.open(step_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            handler._remember_dialog_path(
                settings,
                step_path,
                "LatheEasyStep/StepLastDir",
                "LatheEasyStep/LastDialogDir",
            )
            saved_steps += 1

        saved_program = False
        program_path = handler._normalized_file_path(handler._current_program_path)
        if program_path and handler._program_dirty:
            handler._write_program_file(program_path)
            handler._remember_dialog_path(
                settings,
                program_path,
                "LatheEasyStep/ProgramLastDir",
                "LatheEasyStep/LastDialogDir",
            )
            saved_program = True
        else:
            handler._log("[LatheEasyStep] save_changes: no linked or dirty program file", level="info")

        saved_gcode = False
        gcode_path = handler._normalized_file_path(handler._current_gcode_path)
        if gcode_path and (bool(dirty_step_indices) or handler._program_dirty):
            handler._write_gcode_file(gcode_path)
            handler._remember_dialog_path(
                settings,
                gcode_path,
                "LatheEasyStep/GcodeLastDir",
                "LatheEasyStep/LastDialogDir",
            )
            saved_gcode = True
        else:
            handler._log("[LatheEasyStep] save_changes: no linked or dirty gcode file", level="info")

        if not saved_steps and not saved_program and not saved_gcode:
            handler._log("[LatheEasyStep] save_changes: nothing linked to save", level="warning")
            QtWidgets.QMessageBox.information(
                parent,
                _tr(handler, "dialog.changes.save.title"),
                _tr(handler, "message.changes.nothing_linked"),
            )
            return

        messages = []
        if dirty_step_indices:
            messages.append(_tr(handler, "message.changes.steps_updated", count=saved_steps))
        else:
            messages.append(_tr(handler, "message.changes.steps_unchanged"))
        messages.append(_tr(handler, "message.changes.program_updated") if saved_program else _tr(handler, "message.changes.program_unchanged"))
        messages.append(_tr(handler, "message.changes.gcode_updated") if saved_gcode else _tr(handler, "message.changes.gcode_unchanged"))
        if saved_program and not linked_steps:
            messages.append(_tr(handler, "message.changes.steps_embedded_in_program"))
        handler._log(
            f"[LatheEasyStep] save_changes done: linked_steps={linked_steps} steps={saved_steps} "
            f"program={saved_program} gcode={saved_gcode}",
            level="info",
        )
        QtWidgets.QMessageBox.information(
            parent,
            _tr(handler, "dialog.changes.save.title"),
            "\n".join(messages),
        )
        try:
            handler._clear_dirty_state()
        except Exception:
            pass
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            handler.root_widget or None,
            _tr(handler, "dialog.changes.save.title"),
            format_user_error(handler, exc, fallback_title=_tr(handler, "message.changes.save_failed")),
        )
    finally:
        handler._saving_changes = False
