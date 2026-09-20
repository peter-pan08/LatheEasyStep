from __future__ import annotations

from typing import Dict, List, Tuple

from .contour_features import normalize_relief_mode, resolve_din_relief
from .gcode_safety import validate_chuck_segment
from .gcode_utils import is_internal_side, is_left_hand
from .model import OpType
from .presets import thread_preset_values


ValidationError = Tuple[int, str]  # (Elementindex, Beschreibung)


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


def _check_drill_before_internal_machining(operations: List[object], warnings: List[str]) -> None:
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
            warnings.append(
                f"Innenbearbeitung '{comment}' steht vor der (ersten) Bohrung in der Ablaufreihenfolge - "
                "das Werkzeug hat moeglicherweise keinen Zugang zum Material. Bohrung nach vorne verschieben "
                "oder Reihenfolge pruefen."
            )


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


def _check_duplicate_operations(operations: List[object], warnings: List[str]) -> None:
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
            warnings.append(
                f"Operation {idx + 1} ist inhaltlich identisch mit Operation {first_idx + 1} "
                f"(gleicher Typ '{op_type}', gleiche Bearbeitungsparameter). Falls nicht "
                "beabsichtigt: pruefen, ob hier eine andere Operation gemeint war."
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

_TOOL_KIND_LABELS_DE = {
    "turning": "Drehwerkzeug",
    "drilling": "Bohrwerkzeug",
    "grooving": "Stechwerkzeug",
    "threading": "Gewindewerkzeug",
    "parting": "Abstechwerkzeug",
}

_OP_TYPE_LABELS_DE = {
    "face": "Plan-Operation",
    "turn": "Dreh-Operation",
    "bore": "Bohrungsdreh-Operation",
    "abspanen": "Abspanen-Operation",
    "thread": "Gewinde-Operation",
    "groove": "Stech-Operation",
    "drill": "Bohr-Operation",
}


def _check_tool_kind_matches_operation(operations: List[object], tools: Dict[int, object], warnings: List[str]) -> None:
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
        kind_label = _TOOL_KIND_LABELS_DE.get(kind, kind)
        op_label = _OP_TYPE_LABELS_DE.get(op_type, op_type)
        warnings.append(
            f"T{tool_num:02d}: Q{orientation}-Wert deutet auf '{kind_label}' hin, "
            f"aber in Schritt {idx + 1} fuer eine {op_label} verwendet. "
            "Bitte Werkzeugzuordnung pruefen."
        )


_GROOVE_WIDTH_PARAM_KEYS = ("wtool", "W_tool", "tool_width", "cutting_width", "groove_cutting_width")


def _check_tool_width_matches_operation(operations: List[object], tools: Dict[int, object], warnings: List[str]) -> None:
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
            warnings.append(
                f"T{tool_num:02d}: Kommentar deutet auf {insert_width:.2f} mm Schneidenbreite hin, "
                f"in Schritt {idx + 1} werden aber {manual_width:.2f} mm eingetragen. "
                "Bitte Werkzeugbreite pruefen."
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


def _check_tool_matches_snapshot(operations: List[object], tools: Dict[int, object], warnings: List[str]) -> None:
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
            warnings.append(
                f"T{tool_num:02d}: Radius hat sich seit dem Speichern von Schritt {idx + 1} "
                f"geaendert ({float(snapshot.get('radius_mm') or 0.0):.3f} mm -> "
                f"{float(getattr(tool, 'radius_mm', 0.0) or 0.0):.3f} mm). Bitte Werkzeug pruefen."
            )
        snap_orientation = snapshot.get("orientation")
        tool_orientation = getattr(tool, "q", None)
        if snap_orientation != tool_orientation:
            warnings.append(
                f"T{tool_num:02d}: Orientierung hat sich seit dem Speichern von Schritt {idx + 1} "
                f"geaendert (Q{snap_orientation} -> Q{tool_orientation}). Bitte Werkzeug pruefen."
            )
        if _tool_snapshot_value_differs(snapshot.get("insert_width_mm"), getattr(tool, "insert_width_mm", None)):
            warnings.append(
                f"T{tool_num:02d}: Einstichbreite hat sich seit dem Speichern von Schritt {idx + 1} "
                f"geaendert. Bitte Werkzeug pruefen."
            )


def _check_groove_reaches_chuck_no_go_zone(
    operations: List[object], tools: Dict[int, object], settings: Dict[str, object], warnings: List[str]
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
            except ValueError as exc:
                warnings.append(f"Schritt {idx + 1}: {exc}")
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


def validate_program_setup(operations: List[object], settings: Dict[str, object]) -> List[str]:
    warnings: List[str] = []
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
                warnings.append(f"Tool T{tool_num:02d} wirkt wie Innenwerkzeug, Operation aber wie Aussenbearbeitung")
            if op_type in ("abspanen", "thread") and is_internal_side(op_side_value) and any(word in comment for word in ("aussen", "außen", "external", "outside", " od ")):
                warnings.append(f"Tool T{tool_num:02d} wirkt wie Aussenwerkzeug, Operation aber wie Innenbearbeitung")
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
                warnings.append("G76 ohne sinnvolle Steigung/Laenge konfiguriert")
            if depth < 0.0:
                warnings.append("G76 mit negativer Gewindetiefe konfiguriert")
            if abs(start_z - end_z) <= 1e-9:
                warnings.append("Gewindestart und Gewindeende sind identisch")
            z_min = min(zi, za)
            z_max = max(zi, za)
            if start_z < z_min - 1e-9 or start_z > z_max + 1e-9:
                warnings.append("Gewindestart ausserhalb des Werkstuecks")
            if end_z < z_min - 1e-9 or end_z > z_max + 1e-9:
                warnings.append("Gewindeende ausserhalb des Werkstuecks")
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
                    warnings.append(
                        f"Gewinde-Preset {label or '(unbenannt)'} nennt Steigung {float(std_pitch):.3f}, "
                        f"tatsaechlich verwendet wird aber {pitch:.3f} - Preset und manueller Wert sind "
                        "inkonsistent. Bitte pruefen, welcher Wert gewollt ist."
                    )
                std_major = standard.get("major")
                major_diameter = float(params.get("major_diameter", 0.0) or 0.0)
                if std_major not in (None, "") and abs(float(std_major) - major_diameter) > 1e-6:
                    label = str(standard.get("label") or standard.get("label_key") or "").strip()
                    warnings.append(
                        f"Gewinde-Preset {label or '(unbenannt)'} nennt Nenndurchmesser {float(std_major):.3f}, "
                        f"tatsaechlich verwendet wird aber {major_diameter:.3f} - Preset und manueller Wert "
                        "sind inkonsistent. Bitte pruefen, welcher Wert gewollt ist."
                    )
                expected = thread_preset_values(standard)
                if expected is not None:
                    field_labels = {
                        "thread_depth": "Gewindetiefe",
                        "first_depth": "erste Zustellung",
                        "peak_offset": "Spitzenversatz",
                        "retract_r": "Ruecklauf R",
                        "infeed_q": "Zustellwinkel Q",
                        "spring_passes": "Federschnitte",
                        "e": "Auslauf E",
                        "l": "Auslaufmodus L",
                    }
                    conflicts = []
                    for key, field_label in field_labels.items():
                        if key not in params or params.get(key) in (None, ""):
                            continue
                        try:
                            actual = float(params[key])
                        except (TypeError, ValueError):
                            continue
                        target = expected[key]
                        if abs(actual - target) > 1e-6:
                            conflicts.append(f"{field_label} {actual:.3f} statt {target:.3f}")
                    if conflicts:
                        label = str(standard.get("label") or standard.get("label_key") or "").strip()
                        warnings.append(
                            f"Gewinde-Preset {label or '(unbenannt)'} und manuelle Werte sind "
                            f"inkonsistent: {', '.join(conflicts)}. Bitte Preset erneut anwenden "
                            "oder bewusst auf Benutzerdefiniert umstellen."
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
                warnings.append(
                    f"Abspanen-Step verweist auf Kontur '{contour_name}', "
                    "die nicht (mehr) existiert - vermutlich geloescht oder "
                    "umbenannt. Kontur neu auswaehlen, bevor gespeichert wird."
                )
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
                    warnings.append("DIN-Freistich ohne Gewindegroesse definiert")
                if "internal" not in feature and "side" not in feature:
                    warnings.append("DIN-Freistich ohne Aussen/Innen-Angabe definiert")
        tool_width = params.get("cutting_width", params.get("tool_width"))
        if tool_width not in (None, ""):
            try:
                tool_width_f = abs(float(tool_width))
            except Exception:
                tool_width_f = 0.0
            for feature in relief_features:
                width = float(feature.get("width", 0.0) or 0.0)
                if tool_width_f > width + 1e-9:
                    warnings.append("Einstichwerkzeug breiter als Freistich/Hinterschnitt")
        if relief_mode == "separate" and not params.get("undercut_tool") and not params.get("tool"):
            warnings.append("Hinterschnitt separat aktiviert, aber kein Werkzeug hinterlegt")
        if relief_mode == "separate":
            try:
                undercut_tool_num = int(float(params.get("undercut_tool", 0) or 0))
            except Exception:
                undercut_tool_num = 0
            undercut_tool = tools.get(undercut_tool_num) if undercut_tool_num > 0 else None
            if undercut_tool is not None:
                undercut_comment = str(getattr(undercut_tool, "comment", "") or "").lower()
                if not any(token in undercut_comment for token in ("einst", "stech", "groove", "undercut", "freistich", "abstech")):
                    warnings.append(f"Hinterschnitt separat aktiv, aber T{undercut_tool_num:02d} wirkt nicht wie Einstich-/Spezialwerkzeug")
        for key in ("xt", "zt", "xra", "xri", "zra", "zri"):
            if settings.get(key) in (None, ""):
                warnings.append(f"{key.upper()} ist nicht gesetzt")
    return warnings
