from __future__ import annotations

import os

from qtvcp.core import Action
from qtpy import QtCore, QtWidgets

from .model import OpType


def build_gcode_lines(handler):
    if not handler.tools:
        try:
            handler._auto_load_tool_table()
        except Exception:
            pass
    header = handler._collect_program_header()
    handler.model.program_settings = header
    handler.model.program_settings["tools"] = handler.tools
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
    if len(unique_tools) >= 2:
        xt = header.get("xt")
        zt = header.get("zt")
        if xt is None or zt is None:
            raise ValueError("Bitte XT und ZT im Programm-Tab eintragen, da mehrere Werkzeuge verwendet werden.")
    header_lines = handler._tool_change_position_lines(header)
    footer_lines = handler._tool_change_position_lines(header)
    handler.model.program_settings["header_lines"] = header_lines
    handler.model.program_settings["footer_lines"] = footer_lines
    return handler.model.generate_gcode()


def handle_move_up(handler):
    if handler._moving_up:
        return
    handler._moving_up = True
    try:
        if handler.list_ops is None:
            return
        idx = handler.list_ops.currentRow()
        if idx <= 0:
            return
        handler.model.move_up(idx)
        handler._refresh_operation_list(select_index=idx - 1)
        handler._refresh_preview()
    finally:
        handler._moving_up = False


def handle_move_down(handler):
    if handler._moving_down:
        return
    handler._moving_down = True
    try:
        if handler.list_ops is None:
            return
        idx = handler.list_ops.currentRow()
        if idx < 0 or idx >= handler.list_ops.count() - 1:
            return
        handler.model.move_down(idx)
        handler._refresh_operation_list(select_index=idx + 1)
        handler._refresh_preview()
    finally:
        handler._moving_down = False


def handle_new_program(handler):
    if handler._creating_new_program:
        return
    handler._creating_new_program = True
    try:
        handler.model.operations.clear()
        handler._current_program_path = None
        handler._current_gcode_path = None
        handler._op_row_user_selected = False
        handler._refresh_operation_list(select_index=-1)
        handler._refresh_preview()
    finally:
        handler._creating_new_program = False


def handle_generate_gcode(handler):
    if handler._generating_gcode:
        return
    handler._generating_gcode = True
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
            "G-Code speichern",
            default_filepath,
            "G-Code Dateien (*.ngc);;Alle Dateien (*)",
        )
        if not filepath:
            return
        handler._update_selected_operation(force=True)
        handler._write_gcode_file(filepath)
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
                "LatheEasyStep",
                f"Programm gespeichert unter:\n{filepath}\nAutomatisches Öffnen ist nicht verfügbar.",
            )
            handler._log(f"[LatheEasyStep] Hinweis: Programm geschrieben nach {filepath}, automatisches Öffnen nicht verfügbar", level="info")
    except Exception as exc:
        QtWidgets.QMessageBox.critical(
            handler.root_widget or None,
            "LatheEasyStep",
            f"Fehler beim Erzeugen des Programms:\n{exc}",
        )
    finally:
        handler._generating_gcode = False


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
        return wrap(f"Programmkopf ({wcs})")
    if t == OpType.FACE:
        mode = p.get("mode", "schruppen")
        if isinstance(mode, (int, float)):
            mode = {0: "schruppen", 1: "schlichten", 2: "schruppen + schlichten"}.get(int(mode), "schruppen")
        mode = "schruppen" if mode is None else str(mode)
        z_start = p.get("z_start", 0.0)
        z_end = p.get("z_end", 0.0)
        coolant = " mit Kühlung" if p.get("coolant") else ""
        tool = p.get("tool", "T01")
        return wrap(f"Planen {mode.title()} (Z {fnum(z_start)}→{fnum(z_end)}){coolant} ({tool})")
    if t == OpType.CONTOUR:
        return wrap(f"Kontur {p.get('mode', 'schruppen')} ({p.get('side', 'außen')}) ({p.get('tool', 'T01')})")
    if t == OpType.DRILL:
        return wrap(f"Bohren {p.get('mode', 'normal')} (Z {fnum(p.get('z0', 0.0))}→{fnum(p.get('depth', 0.0))}) ({p.get('tool', 'T01')})")
    if t == OpType.GROOVE:
        return wrap(f"Einstechen (Z {fnum(p.get('z', 0.0))}; B {fnum(p.get('width', 0.0))}) ({p.get('tool', 'T01')})")
    if t == OpType.THREAD:
        return wrap(f"Gewinde {p.get('orientation', 'aussengewinde')} (P {fnum(p.get('pitch', 0.0),2)}; Z {fnum(p.get('z0', 0.0))}→{fnum(p.get('z1', 0.0))}) ({p.get('tool', 'T01')})")
    if t == OpType.ABSPANEN:
        return wrap(f"Abspanen ({p.get('contour_name', 'unbekannt')}, {p.get('slice_strategy', 'parallel_z')}) ({p.get('tool', 'T01')})")
    if t == OpType.KEYWAY:
        slot_count = int(float(p.get("slot_count", 1) or 1))
        return wrap(f"Keilnut ({slot_count}x ab Z {fnum(p.get('start_z', 0.0))}) ({p.get('tool', 'T01')})")
    return wrap(f"{t}: {p}")


def renumber_operations(handler):
    if handler.list_ops is None:
        return
    for i in range(handler.list_ops.count()):
        item = handler.list_ops.item(i)
        op = handler.model.operations[i]
        item.setText(handler._describe_operation(op, i + 1))
