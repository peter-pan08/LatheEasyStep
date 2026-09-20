from __future__ import annotations

import json
import tempfile
import os
import re
from copy import deepcopy
from typing import Callable, Dict, List, Tuple

from .model import OpType, Operation
from .numeric import validate_finite_data

STEP_FILE_PATH_KEY = "__step_file_path"
PROGRAM_FILE_PATH_KEY = "__program_file_path"
GCODE_FILE_PATH_KEY = "__gcode_file_path"

# LES-053: zentrale, einzige Quelle der aktuellen Programm-/Step-Dateiformat-
# version. Programm- und Step-Dateien teilen sich denselben Versionszaehler
# und dieselbe Migrationskette (_MIGRATIONS) - eine Step-Datei ist inhaltlich
# dieselbe Operation-Form wie ein Eintrag in operations[] einer Programmdatei.
CURRENT_FORMAT_VERSION = 2


def _migrate_v1_to_v2(payload: Dict[str, object]) -> Dict[str, object]:
    """v1 -> v2: LES-032-Werkzeug-Snapshot (params["tool_snapshot"]) wird ab
    hier von Speicherpfaden optional geschrieben und beim Laden ausgewertet.
    Rein additiv fuer bestehende Daten - kein Feld wird umbenannt, entfernt
    oder umgedeutet. Migriert v1-Operationen bekommen ABSICHTLICH keinen
    nachtraeglich aus der aktuell geladenen Tooltable erzeugten Snapshot:
    zum Migrationszeitpunkt ist nicht bekannt, welche Werkzeugmerkmale beim
    urspruenglichen Speichern tatsaechlich galten - ein jetzt erzeugter
    Snapshot waere kein Schnappschuss der Vergangenheit, sondern ein
    erfundener Wert. Operationen ohne Snapshot werden von der Vergleichs-
    pruefung (`checks.py::_check_tool_matches_snapshot`) uebersprungen."""
    migrated = deepcopy(payload)
    migrated["version"] = 2
    return migrated


_MIGRATIONS: Dict[int, Callable[[Dict[str, object]], Dict[str, object]]] = {
    1: _migrate_v1_to_v2,
    # 2: _migrate_v2_to_v3,  # zukuenftig hier ergaenzen, sequenziell verkettet
}


def _migrate_to_current(payload: Dict[str, object], *, label: str) -> Dict[str, object]:
    """Einziger Einstiegspunkt fuer Formatversionspruefung/-migration -
    keine Formaterkennung anhand vorhandener Felder an anderer Stelle im
    Loadpfad. Arbeitet ausschliesslich auf Kopien (`deepcopy` in jedem
    Migrationsschritt); `payload` selbst wird nie veraendert."""
    version = payload.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise ValueError(f"{label}: fehlende oder ungültige Formatversion.")
    if version < 1:
        raise ValueError(f"{label}: ungültige Formatversion {version}.")
    if version > CURRENT_FORMAT_VERSION:
        raise ValueError(
            f"{label}: Version {version} ist neuer als die unterstützte Version "
            f"{CURRENT_FORMAT_VERSION} - bitte LatheEasyStep aktualisieren."
        )
    current = payload
    while current["version"] < CURRENT_FORMAT_VERSION:
        step = _MIGRATIONS.get(current["version"])
        if step is None:
            raise ValueError(f"{label}: keine Migration von Version {current['version']} verfügbar.")
        current = step(current)
    return current


def normalized_file_path(file_path: str | None) -> str | None:
    if not file_path:
        return None
    try:
        return os.path.abspath(os.path.expanduser(str(file_path)))
    except Exception:
        return str(file_path)


def step_file_path(op: Operation) -> str | None:
    params = getattr(op, "params", {}) or {}
    return normalized_file_path(params.get(STEP_FILE_PATH_KEY))


def set_step_file_path(op: Operation, file_path: str) -> None:
    op.params[STEP_FILE_PATH_KEY] = normalized_file_path(file_path)


def step_filename_stem(op: Operation, index_hint: int | None = None) -> str:
    params = getattr(op, "params", {}) or {}
    base = str(params.get("name") or params.get("contour_name") or op.op_type or "step").strip()
    if not base:
        base = "step"
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("._") or "step"
    if index_hint is not None:
        return f"{index_hint:02d}_{base}"
    return base


def program_file_meta(
    operations: List[Operation],
    current_program_path: str | None,
    current_gcode_path: str | None,
) -> Dict[str, object]:
    meta: Dict[str, object] = {}
    program_path = normalized_file_path(current_program_path)
    gcode_path = normalized_file_path(current_gcode_path)
    if program_path:
        meta[PROGRAM_FILE_PATH_KEY] = program_path
    if gcode_path:
        meta[GCODE_FILE_PATH_KEY] = gcode_path
    step_files = []
    for idx, op in enumerate(operations or []):
        if getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
            continue
        step_files.append(
            {
                "index": idx,
                "op_type": getattr(op, "op_type", ""),
                "path": step_file_path(op),
            }
        )
    if step_files:
        meta["step_files"] = step_files
    return meta


def parse_program_payload(
    program_data: Dict[str, object],
    file_path: str,
) -> Tuple[Dict[str, object], List[Dict[str, object]], str | None, str | None]:
    """Gueltige `.lse`-Programme hatten schon vor Format v2 immer ein
    "version"-Feld (siehe `persistence.py::build_program_data()`) - anders
    als bei Step-Dateien (siehe `parse_step_payload()`) wird eine fehlende
    Version hier NICHT stillschweigend angenommen, sondern abgelehnt."""
    validate_finite_data(program_data, "Programmdatei")
    program_data = _migrate_to_current(program_data, label="Programmdatei")
    header = program_data.get("header", {})
    if not isinstance(header, dict):
        header = {}
    meta = program_data.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}
    operations = program_data.get("operations", [])
    if not isinstance(operations, list):
        operations = []
    program_path = normalized_file_path(meta.get(PROGRAM_FILE_PATH_KEY) or file_path)
    gcode_path = normalized_file_path(meta.get(GCODE_FILE_PATH_KEY))
    return header, operations, program_path, gcode_path


def parse_step_payload(data: Dict[str, object]) -> Dict[str, object]:
    """Zentraler Ladeweg fuer Step-Dateien (LES-053), analog zu
    `parse_program_payload()`. Eine fehlende "version" wird - ausdruecklich
    und ausschliesslich fuer Step-Dateien, nicht fuer Programmdateien -
    als historisches Step-v1 behandelt: das ist das einzige Step-Dateiformat,
    das je geschrieben wurde (vor LES-053 gab es dort ueberhaupt kein
    Versionsfeld), keine Formaterkennung anhand anderer vorhandener Felder."""
    validate_finite_data(data, "Step-Datei")
    if "version" not in data:
        data = deepcopy(data)
        data["version"] = 1
    return _migrate_to_current(data, label="Step-Datei")


def atomic_write_json(file_path, data, *, default=None):
    """Replace one JSON file only after complete serialization and close."""
    directory = os.path.dirname(os.path.abspath(file_path))
    fd, temporary_path = tempfile.mkstemp(prefix=".lathe-easystep-", suffix=".json", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, default=default, allow_nan=False)
        os.replace(temporary_path, file_path)
    except Exception:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise
