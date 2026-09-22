from __future__ import annotations

from typing import Dict, List, Tuple

from .contour_features import normalize_relief_mode, resolve_din_relief
from .gcode_safety import validate_chuck_segment
from .gcode_utils import gcode_comment, is_internal_side, is_left_hand
from .model import OpType
from .presets import thread_preset_values


ValidationError = Tuple[int, str]  # (Elementindex, Beschreibung)

# ID-only-Vollaudit 2026-09-21: validate_program_setup() und ihre
# Hilfsfunktionen liefern seither KEINEN fertig lokalisierten Text mehr,
# sondern stabile, sprachunabhaengige Warnungen (Schluessel + Parameter).
# Grund: dieselben Ergebnisse werden technisch weiterverarbeitet (rund ein
# Dutzend Tests filtern/vergleichen Warnungen inhaltlich, z. B.
# tests/test_tool_kind_mismatch_check.py) - Domainlogik darf dafuer keine
# lokalisierten Saetze erzeugen, die je nach Sprache auseinanderlaufen.
# Uebersetzt wird erst an der jeweiligen Darstellungsgrenze
# (format_warning(), unten) ueber gcode_comment() - dieselbe Qt-freie
# .lng-Mechanik wie alle anderen G-Code-Kommentare, da validate_program_setup()
# Teil der Qt-freien Generatorpipeline ist (auch in gcode_program.py
# genutzt) und deshalb nicht auf translations.py/Qt zugreifen soll.
CheckWarning = Dict[str, object]  # {"key": str, "params": Dict[str, object]}


def _warn(warnings: List[CheckWarning], key: str, **params: object) -> None:
    warnings.append({"key": key, "params": params})


_PRESET_LABEL_KEYS = {
    "warning.thread_preset_pitch_mismatch",
    "warning.thread_preset_major_mismatch",
    "warning.thread_preset_field_conflicts",
}


def format_warning(warning: CheckWarning, lang: str | None = None) -> str:
    """Uebersetzt eine strukturierte Warnung in sichtbaren Text - an der
    Darstellungsgrenze (G-Code-Kommentar oder Vorschau-Statusbox), nicht in
    der Pruefungslogik selbst."""
    key = warning["key"]
    params = dict(warning.get("params") or {})
    if key in _PRESET_LABEL_KEYS and not params.get("label"):
        params["label"] = gcode_comment("warning.unnamed_preset_label", lang)
    if key == "warning.tool_radius_unknown" and not params.get("comment"):
        params["comment"] = gcode_comment("warning.no_tool_comment", lang)
    if key == "warning.tool_kind_mismatch":
        params["kind_label"] = gcode_comment(f"tool.kind.{params.pop('kind')}", lang)
        params["op_label"] = gcode_comment(f"optype.{params.pop('op_type')}", lang)
    elif key == "warning.thread_preset_field_conflicts":
        conflicts = params.pop("conflicts")
        params["conflicts"] = ", ".join(
            gcode_comment(
                "warning.thread_preset_field_conflict_item",
                lang,
                field=gcode_comment(f"field.{c['field_key']}", lang),
                actual=c["actual"],
                target=c["target"],
            )
            for c in conflicts
        )
    return gcode_comment(key, lang, **params)


def validate_contour(contour) -> List[ValidationError]:
    """Einfache Plausibilitätschecks für eine Kontur.

    Ziel:
      - Bei der Programmierung direkt sinnvolle Fehlermeldungen anzeigen.
      - Hier nur Minimalchecks, später erweiterbar.
    """
    errors: List[ValidationError] = []

    if contour.is_empty():
        errors.append((-1, "Kontur enthält keine Elemente."))

    for idx, elem in enumerate(contour.elements):
        elem_type = str(getattr(elem, "type", ""))
        if "ARC_CONCAVE" in elem_type or "ARC_CONVEX" in elem_type:
            if getattr(elem, "radius", None) is None:
                errors.append((idx, "Bogen ohne Radius definiert."))
            if getattr(elem, "cw", None) is None:
                errors.append((idx, "Bogen ohne Drehrichtung (G2/G3) definiert."))

    return errors


def _is_internal_machining_op(op_type: str, params: Dict[str, object]) -> bool:
    if op_type == "abspanen":
        return is_internal_side(params.get("side", 0))
    if op_type == "groove":
        return is_internal_side(params.get("lage", 0))
    if op_type == "thread":
        return is_internal_side(params.get("orientation", 0))
    return False


def _check_drill_before_internal_machining(operations: List[object], warnings: List[CheckWarning]) -> None:
    """Der Generator darf Operationen nicht eigenmaechtig umsortieren, aber ein
    Werkzeug, das in eine Bohrung einfahren soll (Innen-Abspanen/-Einstich/
    -Gewinde), braucht diese Bohrung bereits vorher - sonst faehrt es in
    Vollmaterial. Warnt, sobald eine Innenbearbeitung vor der ersten Bohrung
    (oder ganz ohne Bohrung) in der Ablaufreihenfolge steht."""
    first_drill_index: int | None = None
    for idx, op in enumerate(operations):
        if getattr(op, "op_type", "") == "drill":
            first_drill_index = idx
            break
    for idx, op in enumerate(operations):
        op_type = getattr(op, "op_type", "")
        params = getattr(op, "params", {}) or {}
        if not _is_internal_machining_op(op_type, params):
            continue
        if first_drill_index is None or idx < first_drill_index:
            comment = str(params.get("comment") or "").strip() or f"Operation {idx + 1}"
            _warn(warnings, "warning.drill_before_internal_machining", comment=comment)


# Schluessel, die zwei Operationen faelschlich als "verschieden" erscheinen
# liessen, obwohl sie fachlich identisch sind (Kommentar/Cache-/Herkunftsdaten,
# keine tatsaechlichen Bearbeitungsparameter).
_DUPLICATE_CHECK_IGNORED_KEYS = {
    "comment", "title", "__step_file_path",
    "source_path", "_contour_params", "_primitives", "path",
}


def _params_for_duplicate_compare(params: Dict[str, object]) -> tuple:
    items = tuple(
        sorted(
            (key, repr(value))
            for key, value in (params or {}).items()
            if key not in _DUPLICATE_CHECK_IGNORED_KEYS
        )
    )
    return items


def _check_duplicate_operations(operations: List[object], warnings: List[CheckWarning]) -> None:
    """Meldet fachlich identische Operationen (gleicher Typ, gleiche
    Bearbeitungsparameter) als Hinweis. Loescht oder aendert NICHTS automatisch
    - der Nutzer entscheidet, ob eine Mehrfachverwendung beabsichtigt ist."""
    seen: Dict[tuple, int] = {}
    for idx, op in enumerate(operations):
        op_type = getattr(op, "op_type", "")
        if op_type in ("program_header", "contour"):
            continue
        params = getattr(op, "params", {}) or {}
        key = (op_type, _params_for_duplicate_compare(params))
        first_idx = seen.get(key)
        if first_idx is not None:
            _warn(
                warnings,
                "warning.duplicate_operation",
                idx=idx + 1,
                first_idx=first_idx + 1,
                op_type=op_type,
            )
        else:
            seen[key] = idx


_OP_TYPE_EXPECTED_TOOL_KINDS: Dict[str, set] = {
    "face": {"turning"},
    "turn": {"turning"},
    "bore": {"turning", "drilling"},
    "abspanen": {"turning"},
    "thread": {"threading"},
    "groove": {"grooving", "parting"},
    "drill": {"drilling"},
}

def _check_tool_kind_matches_operation(operations: List[object], tools: Dict[int, object], warnings: List[CheckWarning]) -> None:
    """LES-028/LES-032: `Tool.kind` (aus der Q-Orientierung der Werkzeug-
    tabelle geparst - siehe `tools.py`) wurde bisher nirgends gegen den
    tatsaechlich verwendeten Operationstyp geprueft. Ein Werkzeug, dessen
    Q-Wert laut Tabelle z. B. auf ein Bohrwerkzeug hindeutet, konnte bisher
    unbemerkt einer Stech- oder Gewinde-Operation zugewiesen werden.

    Nur bei tatsaechlich gesetzter Q-Orientierung geprueft: `tool.orientation
    is None` liefert per `tool_kind_from_orientation()` den Fallback
    "turning" (keine echte Klassifikation, nur ein Default) und wuerde bei
    jedem Werkzeug ohne Q-Angabe in der Tabelle zu Falschmeldungen fuehren.
    Ebenso wird `kind == "parting"` (der Fallback fuer JEDEN nicht in der
    Zuordnungstabelle enthaltenen Q-Wert, keine gezielte Klassifikation)
    nicht als Widerspruch gewertet."""
    for idx, op in enumerate(operations):
        op_type = getattr(op, "op_type", "")
        expected_kinds = _OP_TYPE_EXPECTED_TOOL_KINDS.get(op_type)
        if not expected_kinds:
            continue
        params = getattr(op, "params", {}) or {}
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            tool_num = 0
        if tool_num <= 0:
            continue
        tool = tools.get(tool_num)
        if tool is None:
            continue
        orientation = getattr(tool, "orientation", None)
        if orientation is None:
            continue
        kind = getattr(tool, "kind", None)
        if not kind or kind == "parting" or kind in expected_kinds:
            continue
        _warn(
            warnings,
            "warning.tool_kind_mismatch",
            tool_num=tool_num,
            orientation=orientation,
            kind=kind,
            idx=idx + 1,
            op_type=op_type,
        )


_GROOVE_WIDTH_PARAM_KEYS = ("wtool", "W_tool", "tool_width", "cutting_width", "groove_cutting_width")


def _check_tool_width_matches_operation(operations: List[object], tools: Dict[int, object], warnings: List[CheckWarning]) -> None:
    """LES-032: `Tool.insert_width_mm` (aus dem ISO-Einstich-Einsatzcode im
    Kommentar abgeleitet, z. B. "MGMN200" -> 2,00 mm - siehe `tools.py`)
    wurde bisher nirgends gegen die manuell eingetragene Werkzeugbreite
    einer Stech-Operation geprueft; beide Werte konnten unbemerkt
    auseinanderlaufen. Nur geprueft, wenn die Operation die Werkzeugbreite
    tatsaechlich verwendet (`use_tool_width`) und sowohl ein manueller Wert
    als auch ein aus dem Kommentar ableitbarer Wert vorliegen - ansonsten
    kein Vergleichswert vorhanden, keine Meldung."""
    for idx, op in enumerate(operations):
        if getattr(op, "op_type", "") != "groove":
            continue
        params = getattr(op, "params", {}) or {}
        if not bool(params.get("use_tool_width", False)):
            continue
        manual_width = None
        for key in _GROOVE_WIDTH_PARAM_KEYS:
            if key in params and params.get(key) not in (None, ""):
                try:
                    manual_width = float(params[key])
                except Exception:
                    manual_width = None
                break
        if manual_width is None:
            continue
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            tool_num = 0
        if tool_num <= 0:
            continue
        tool = tools.get(tool_num)
        if tool is None:
            continue
        insert_width = getattr(tool, "insert_width_mm", None)
        if insert_width is None:
            continue
        if abs(manual_width - insert_width) > 0.05:
            _warn(
                warnings,
                "warning.tool_width_mismatch",
                tool_num=tool_num,
                insert_width=insert_width,
                idx=idx + 1,
                manual_width=manual_width,
            )


_TOOL_SNAPSHOT_FLOAT_TOL = 1e-6


def _tool_snapshot_value_differs(old_value: object, new_value: object, *, tol: float = _TOOL_SNAPSHOT_FLOAT_TOL) -> bool:
    if old_value is None and new_value is None:
        return False
    if old_value is None or new_value is None:
        return True
    try:
        return abs(float(old_value) - float(new_value)) > tol
    except (TypeError, ValueError):
        return old_value != new_value


def _check_tool_matches_snapshot(operations: List[object], tools: Dict[int, object], warnings: List[CheckWarning]) -> None:
    """LES-032/LES-053 (Format v2): `op.params["tool_snapshot"]` (siehe
    `tools.py::build_tool_snapshot()`) haelt fest, welche Radius-/
    Orientierungs-/Einstichbreiten-Werte beim letzten Speichern dieser
    Operation tatsaechlich galten. Weicht die AKTUELL geladene Tooltable
    davon ab, wurde das Werkzeug an dieser Nummer seither veraendert oder
    ausgetauscht - nur eine Warnung, keine Sperre (LES-032-Anforderung).

    Nur Operationen MIT Snapshot werden geprueft: ueber Format v1 geladene
    (und nach v2 migrierte) Altprogramme haben keinen Snapshot - dafuer
    entsteht bewusst KEINE Warnung, da kein historischer Vergleichswert
    existiert (siehe `storage.py::_migrate_v1_to_v2`). Fehlt das Werkzeug in
    der aktuellen Tabelle komplett, meldet das bereits separat
    `validate_tool_table_completeness()` (LES-028) - hier keine Dopplung."""
    for idx, op in enumerate(operations):
        params = getattr(op, "params", {}) or {}
        snapshot = params.get("tool_snapshot")
        if not isinstance(snapshot, dict):
            continue
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            continue
        if tool_num <= 0:
            continue
        tool = tools.get(tool_num)
        if tool is None:
            continue
        if _tool_snapshot_value_differs(snapshot.get("radius_mm"), getattr(tool, "radius_mm", None)):
            _warn(
                warnings,
                "warning.tool_snapshot_radius_changed",
                tool_num=tool_num,
                idx=idx + 1,
                old_radius=float(snapshot.get("radius_mm") or 0.0),
                new_radius=float(getattr(tool, "radius_mm", 0.0) or 0.0),
            )
        snap_orientation = snapshot.get("orientation")
        tool_orientation = getattr(tool, "q", None)
        if snap_orientation != tool_orientation:
            _warn(
                warnings,
                "warning.tool_snapshot_orientation_changed",
                tool_num=tool_num,
                idx=idx + 1,
                old_orientation=snap_orientation,
                new_orientation=tool_orientation,
            )
        if _tool_snapshot_value_differs(snapshot.get("insert_width_mm"), getattr(tool, "insert_width_mm", None)):
            _warn(
                warnings,
                "warning.tool_snapshot_width_changed",
                tool_num=tool_num,
                idx=idx + 1,
            )


def _check_groove_reaches_chuck_no_go_zone(
    operations: List[object], tools: Dict[int, object], settings: Dict[str, object], warnings: List[CheckWarning]
) -> None:
    """LES-032: Erreichbarkeits-/Werkzeughuellenpruefung mit Tooltable-Daten.

    Bisher wurde die Futter-Sperrzone (`chuck_no_go_x_min/x_max/z_limit`,
    siehe `gcode_safety.py::validate_chuck_segment()`) nur fuer die
    SEPARATEN Rueckzugswege vor/nach einer Operation geprueft
    (`emit_safe_retract_for_op()`) - die eigentliche Stechbewegung selbst
    (Z-Position der Operation, in `gcode_groove.py` erzeugt) hatte NIE
    eine Pruefung, und selbst die Rueckzugspruefung behandelt das Werkzeug
    als punktfoermig. Ein Stechwerkzeug hat aber eine reale Schneidenbreite
    (`Tool.insert_width_mm`, siehe `_check_tool_width_matches_operation()`
    oben) - die dem Futter zugewandte Kante der Einsatzbreite kann in die
    Sperrzone reichen, auch wenn die programmierte Z-Mitte selbst noch
    ausserhalb liegt.

    Prueft die tiefste Stechposition (Nutgrund) an beiden Kanten der
    bekannten Werkzeugbreite (0, wenn keine ableitbar ist - dann bleibt nur
    die Z-Mitte selbst geprueft) gegen dieselbe, bereits produktiv genutzte
    Sperrzonen-Logik wie die Rueckzugswege. Wie diese bewusst nur aktiv,
    wenn ueberhaupt eine Sperrzone konfiguriert ist (`validate_chuck_segment()`
    kehrt sonst folgenlos zurueck)."""
    for idx, op in enumerate(operations):
        if getattr(op, "op_type", "") != "groove":
            continue
        params = getattr(op, "params", {}) or {}
        try:
            z = float(params.get("z", 0.0) or 0.0)
            diameter = float(params.get("diameter", 0.0) or 0.0)
            depth = float(params.get("depth", 0.0) or 0.0)
        except Exception:
            continue
        floor_diameter = diameter + 2.0 * depth if is_internal_side(params.get("lage", 0)) else diameter - 2.0 * depth

        tool = None
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            tool_num = 0
        if tool_num > 0:
            tool = tools.get(tool_num)
        insert_width = getattr(tool, "insert_width_mm", None) if tool is not None else None
        half_width = (insert_width / 2.0) if insert_width else 0.0

        for z_edge in {z - half_width, z + half_width}:
            point = (floor_diameter, z_edge)
            try:
                validate_chuck_segment(settings, point, point)
            except ValueError:
                # Die eigene Meldung von validate_chuck_segment() wird bewusst
                # nicht relayed (bliebe sonst unuebersetztes Deutsch) - der
                # umgebende Kontext (Schritt, "Futter-Sperrzone") ist bereits
                # eindeutig genug.
                _warn(warnings, "warning.groove_reaches_chuck_no_go_zone", step=idx + 1)
                break


def validate_tool_table_completeness(operations: List[object], tools: Dict[int, object]) -> None:
    """LES-028: jede verwendete Werkzeugnummer muss einen Eintrag in der
    geladenen Werkzeugtabelle haben, sobald ueberhaupt eine geladen wurde.

    Ohne geladene Tabelle (leeres/fehlendes `tools`-Dict - z. B. reine
    Generatortests oder die Referenzregeneration ohne echtes `tool.tbl`)
    bleibt das unveraendert ungeprueft, damit dieser Aufruf nicht jeden
    bestehenden Test/jede Referenz ohne Tooltable-Kontext bricht. Sobald
    eine reale Tabelle vorliegt (der ueblich Fall in der laufenden UI,
    `_auto_load_tool_table()` laedt sie automatisch), ist eine fehlende
    Werkzeugnummer ein harter Fehler statt nur einer Warnung.
    """
    if not tools:
        return
    missing: set[int] = set()
    for op in operations:
        if getattr(op, "op_type", None) == OpType.PROGRAM_HEADER:
            continue
        params = getattr(op, "params", {}) or {}
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            tool_num = 0
        if tool_num > 0 and tool_num not in tools:
            missing.add(tool_num)
    if missing:
        formatted = ", ".join(f"T{num:02d}" for num in sorted(missing))
        raise ValueError(
            f"Werkzeug(e) {formatted} werden verwendet, haben aber keinen "
            "Eintrag in der geladenen Werkzeugtabelle."
        )


def validate_program_setup(operations: List[object], settings: Dict[str, object]) -> List[CheckWarning]:
    warnings: List[CheckWarning] = []
    contour_by_name: Dict[str, object] = {}
    tools = settings.get("tools", {}) if isinstance(settings.get("tools", {}), dict) else {}
    _check_drill_before_internal_machining(operations, warnings)
    _check_duplicate_operations(operations, warnings)
    _check_tool_kind_matches_operation(operations, tools, warnings)
    _check_tool_width_matches_operation(operations, tools, warnings)
    _check_tool_matches_snapshot(operations, tools, warnings)
    _check_groove_reaches_chuck_no_go_zone(operations, tools, settings, warnings)
    for op in operations:
        op_type = getattr(op, "op_type", "")
        params = getattr(op, "params", {}) or {}
        try:
            tool_num = int(float(params.get("tool", 0) or 0))
        except Exception:
            tool_num = 0
        tool = tools.get(tool_num) if tool_num > 0 else None
        if tool is not None:
            comment = str(getattr(tool, "comment", "") or "").lower()
            op_side_value = params.get("side", params.get("orientation", 0))
            if op_type in ("abspanen", "thread") and not is_internal_side(op_side_value) and any(word in comment for word in ("innen", "internal", "inside", " id ")):
                _warn(warnings, "warning.tool_looks_internal_op_external", tool_num=tool_num)
            if op_type in ("abspanen", "thread") and is_internal_side(op_side_value) and any(word in comment for word in ("aussen", "außen", "external", "outside", " od ")):
                _warn(warnings, "warning.tool_looks_external_op_internal", tool_num=tool_num)
        if op_type == "contour":
            name = str(params.get("name") or "").strip()
            if name:
                contour_by_name[name] = op
        if op_type == "thread":
            try:
                pitch = float(params.get("pitch", 0.0) or 0.0)
                length = float(params.get("length", 0.0) or 0.0)
                depth = float(params.get("thread_depth", 0.0) or 0.0)
                start_z = float(params.get("thread_start_z", 0.0) or 0.0)
                left_hand = is_left_hand(params.get("hand", 0))
                end_z = start_z + ((1.0 if left_hand else -1.0) * abs(length))
                za = float(settings.get("za", 0.0) or 0.0)
                zi = float(settings.get("zi", 0.0) or 0.0)
            except Exception:
                pitch, length, depth = 0.0, 0.0, 0.0
                start_z, end_z = 0.0, 0.0
                za, zi = 0.0, 0.0
            if pitch <= 0.0 or length <= 0.0:
                _warn(warnings, "warning.thread_g76_invalid_pitch_length")
            if depth < 0.0:
                _warn(warnings, "warning.thread_g76_negative_depth")
            if abs(start_z - end_z) <= 1e-9:
                _warn(warnings, "warning.thread_start_end_identical")
            z_min = min(zi, za)
            z_max = max(zi, za)
            if start_z < z_min - 1e-9 or start_z > z_max + 1e-9:
                _warn(warnings, "warning.thread_start_outside_stock")
            if end_z < z_min - 1e-9 or end_z > z_max + 1e-9:
                _warn(warnings, "warning.thread_end_outside_stock")
            standard = params.get("standard")
            if isinstance(standard, dict):
                # Realer Fund: "standard" (Preset-Metadaten, z. B. label_key
                # "m30x3_5") und das tatsaechlich fuer die G76-Erzeugung
                # verwendete "pitch"/"major_diameter" koennen auseinanderlaufen,
                # wenn ein Preset gewaehlt und danach manuell ueberschrieben
                # wurde (oder die Preset-Anwendung nicht alle Felder aktualisiert
                # hat). Kommentar/Vorschau und G-Code muessen aus denselben
                # Werten stammen - eine Abweichung wird hier nur gemeldet, nicht
                # automatisch aufgeloest (unklar, welcher Wert der gewollte ist).
                std_pitch = standard.get("pitch")
                if std_pitch not in (None, "") and abs(float(std_pitch) - pitch) > 1e-6:
                    label = str(standard.get("label") or standard.get("label_key") or "").strip()
                    _warn(
                        warnings,
                        "warning.thread_preset_pitch_mismatch",
                        label=label,
                        preset_value=float(std_pitch),
                        actual_value=pitch,
                    )
                std_major = standard.get("major")
                major_diameter = float(params.get("major_diameter", 0.0) or 0.0)
                if std_major not in (None, "") and abs(float(std_major) - major_diameter) > 1e-6:
                    label = str(standard.get("label") or standard.get("label_key") or "").strip()
                    _warn(
                        warnings,
                        "warning.thread_preset_major_mismatch",
                        label=label,
                        preset_value=float(std_major),
                        actual_value=major_diameter,
                    )
                expected = thread_preset_values(standard)
                if expected is not None:
                    field_keys = (
                        "thread_depth", "first_depth", "peak_offset", "retract_r",
                        "infeed_q", "spring_passes", "e", "l",
                    )
                    conflicts = []
                    for field_key in field_keys:
                        if field_key not in params or params.get(field_key) in (None, ""):
                            continue
                        try:
                            actual = float(params[field_key])
                        except (TypeError, ValueError):
                            continue
                        target = expected[field_key]
                        if abs(actual - target) > 1e-6:
                            conflicts.append({"field_key": field_key, "actual": actual, "target": target})
                    if conflicts:
                        label = str(standard.get("label") or standard.get("label_key") or "").strip()
                        _warn(
                            warnings,
                            "warning.thread_preset_field_conflicts",
                            label=label,
                            conflicts=conflicts,
                        )
        if op_type != "abspanen":
            continue
        contour_name = str(params.get("contour_name") or "").strip()
        contour_op = contour_by_name.get(contour_name)
        if contour_op is None:
            # SICHERHEITSFUND 2026-09-13: eine ABSPANEN-Operation verweist
            # per contour_name auf eine CONTOUR-Operation. Wird diese Kontur
            # spaeter geloescht (oder umbenannt), blieb das bisher hier
            # STUMM - erst bei "Programm erzeugen"/"Speichern" kam ein
            # harter ValueError ("Kontur X fehlt oder ist leer"). Diese
            # Funktion liefert aber genau die Warnungen, die schon waehrend
            # der Bearbeitung in Vorschau/Programmkopf angezeigt werden -
            # der Nutzer sollte den kaputten Verweis SOFORT sehen, nicht
            # erst beim naechsten Speicherversuch.
            if contour_name:
                _warn(warnings, "warning.dangling_contour_reference", contour_name=contour_name)
            continue
        contour_params = getattr(contour_op, "params", {}) or {}
        segments = contour_params.get("segments") or []
        relief_features = []
        relief_mode = normalize_relief_mode(params.get("undercut_mode"))
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            feature = resolve_din_relief((seg.get("feature") if isinstance(seg.get("feature"), dict) else seg))
            if str(feature.get("feature_type") or "").strip().lower() == "din_relief":
                relief_features.append(feature)
                if not str(feature.get("thread_size") or "").strip():
                    _warn(warnings, "warning.din_relief_missing_thread_size")
                if "internal" not in feature and "side" not in feature:
                    _warn(warnings, "warning.din_relief_missing_side")
        tool_width = params.get("cutting_width", params.get("tool_width"))
        if tool_width not in (None, ""):
            try:
                tool_width_f = abs(float(tool_width))
            except Exception:
                tool_width_f = 0.0
            for feature in relief_features:
                width = float(feature.get("width", 0.0) or 0.0)
                if tool_width_f > width + 1e-9:
                    _warn(warnings, "warning.groove_tool_wider_than_relief")
        if relief_mode == "separate" and not params.get("undercut_tool") and not params.get("tool"):
            _warn(warnings, "warning.relief_separate_no_tool")
        if relief_mode == "separate":
            try:
                undercut_tool_num = int(float(params.get("undercut_tool", 0) or 0))
            except Exception:
                undercut_tool_num = 0
            undercut_tool = tools.get(undercut_tool_num) if undercut_tool_num > 0 else None
            if undercut_tool is not None:
                undercut_comment = str(getattr(undercut_tool, "comment", "") or "").lower()
                if not any(token in undercut_comment for token in ("einst", "stech", "groove", "undercut", "freistich", "abstech")):
                    _warn(warnings, "warning.relief_separate_tool_mismatch", tool_num=undercut_tool_num)
        for settings_key in ("xt", "zt", "xra", "xri", "zra", "zri"):
            if settings.get(settings_key) in (None, ""):
                _warn(warnings, "warning.retract_plane_not_set", axis_key=settings_key.upper())
    return warnings
