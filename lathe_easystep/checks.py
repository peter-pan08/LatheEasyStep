from __future__ import annotations

from typing import Dict, List, Tuple

from .contour_features import normalize_relief_mode, resolve_din_relief
from .gcode_utils import is_internal_side, is_left_hand


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


def _check_din_relief_feature_position(operations: List[object], warnings: List[str]) -> None:
    """build_contour_variants() erzeugt nur dann tatsaechlich Freistich-
    Geometrie fuer ein "din_relief"-Feature, wenn dessen Segment das absolut
    ERSTE (orientation="start") oder LETZTE (orientation="end") Segment der
    GESAMTEN Kontur ist - nicht nur das erste/letzte Segment DES GEWINDES
    innerhalb einer laengeren Kontur. Sitzt der Freistich mitten in einer
    Kontur (z. B. Gewinde-Freistich, gefolgt von weiterem Wellenprofil), bleibt
    die Geometrie ohne jede Warnung leer. Bis das Splicing an beliebiger
    Segmentposition unterstuetzt wird, wird das hier wenigstens gemeldet."""
    for op in operations:
        if getattr(op, "op_type", "") != "contour":
            continue
        params = getattr(op, "params", {}) or {}
        segments = params.get("segments") or []
        name = str(params.get("name") or "").strip() or "(unbenannt)"
        for idx, seg in enumerate(segments):
            if not isinstance(seg, dict):
                continue
            feature = seg.get("feature")
            if not isinstance(feature, dict) or str(feature.get("feature_type") or "").strip().lower() != "din_relief":
                continue
            orientation = str(feature.get("orientation") or "end").strip().lower()
            is_boundary = (orientation == "start" and idx == 0) or (orientation != "start" and idx == len(segments) - 1)
            if not is_boundary:
                warnings.append(
                    f"DIN-Freistich in Kontur '{name}' (Segment {idx + 1}) erzeugt keine Geometrie: "
                    f"das Feature sitzt nicht am {'Anfang' if orientation == 'start' else 'Ende'} der "
                    "GESAMTEN Kontur, sondern mittendrin (z. B. gefolgt von weiterem Wellenprofil)."
                )


def validate_program_setup(operations: List[object], settings: Dict[str, object]) -> List[str]:
    warnings: List[str] = []
    contour_by_name: Dict[str, object] = {}
    tools = settings.get("tools", {}) if isinstance(settings.get("tools", {}), dict) else {}
    _check_drill_before_internal_machining(operations, warnings)
    _check_duplicate_operations(operations, warnings)
    _check_din_relief_feature_position(operations, warnings)
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
        if op_type != "abspanen":
            continue
        contour_name = str(params.get("contour_name") or "").strip()
        contour_op = contour_by_name.get(contour_name)
        if contour_op is None:
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
