from __future__ import annotations

from typing import Dict, List, Tuple

from .contour_features import normalize_relief_mode, resolve_din_relief


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


def validate_program_setup(operations: List[object], settings: Dict[str, object]) -> List[str]:
    warnings: List[str] = []
    contour_by_name: Dict[str, object] = {}
    tools = settings.get("tools", {}) if isinstance(settings.get("tools", {}), dict) else {}
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
            if op_type in ("abspanen", "thread") and int(float(params.get("side", params.get("orientation", 0)) or 0)) == 0 and any(word in comment for word in ("innen", "internal", "inside", " id ")):
                warnings.append(f"Tool T{tool_num:02d} wirkt wie Innenwerkzeug, Operation aber wie Aussenbearbeitung")
            if op_type in ("abspanen", "thread") and int(float(params.get("side", params.get("orientation", 0)) or 0)) == 1 and any(word in comment for word in ("aussen", "außen", "external", "outside", " od ")):
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
                hand = int(float(params.get("hand", 0) or 0))
                end_z = start_z + ((-1.0 if hand == 0 else 1.0) * abs(length))
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
