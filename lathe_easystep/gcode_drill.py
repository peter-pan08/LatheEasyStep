from __future__ import annotations

from typing import Callable, Dict, List

from .model import Operation
from .numeric import finite_float, whole_number, validate_finite_data


# Mapping: combo index (float from _collect_params) -> G-code mode string
DRILL_MODE_MAP: Dict[int, str] = {
    0: "G81",  # Normal drilling
    1: "G82",  # Drilling with dwell
    2: "G83",  # Peck drilling (full retract)
    3: "G73",  # Chip breaking drilling (partial retract)
    4: "G84",  # Tapping
}


def generate_drill_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require: Callable[[Dict[str, object], List[str], str], None],
    require_tool: Callable[[Dict[str, object], str], int],
    get_tool_number: Callable[[Dict[str, object]], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
    emit_approach: Callable[[List[str], float, float, Dict[str, object] | None], None],
) -> List[str]:
    settings = settings or {}
    path = op.path or []
    if not path:
        return []
    p = op.params
    validate_finite_data(p, "DRILL")
    validate_finite_data(path, "DRILL path")
    require_tool(p, "DRILL")

    mode_raw_value = p.get("mode", "G81")
    if isinstance(mode_raw_value, str) and mode_raw_value.strip().upper() in DRILL_MODE_MAP.values():
        # ID-only-Combo liefert die G-Code-ID direkt (z. B. 'g83'), unabhaengig von Gross-/Kleinschreibung.
        mode = mode_raw_value.strip().upper()
    else:
        mode_idx = whole_number(mode_raw_value, "DRILL mode")
        if mode_idx not in DRILL_MODE_MAP:
            raise ValueError("DRILL: unbekannter Bohrmodus.")
        mode = DRILL_MODE_MAP[mode_idx]

    if mode == "G82":
        require(p, ["dwell"], "DRILL G82")
    elif mode in ["G83", "G73"]:
        require(p, ["peck_depth"], "DRILL " + mode)

    safe_z = finite_float(p.get("safe_z", 2.0), "DRILL safe_z")
    feed = finite_float(p.get("feed", 0.12), "DRILL feed")
    depth_z = finite_float(path[-1][1], "DRILL depth_z")
    x_start = finite_float(path[0][0], "DRILL x_start")
    retract = finite_float(p.get("retract", safe_z), "DRILL retract")
    if feed <= 0 or float(f"{feed:.3f}") <= 0:
        raise ValueError("DRILL: Vorschub muss in der Ausgabe groesser als null sein.")
    if mode == "G82":
        dwell = finite_float(p["dwell"], "DRILL dwell")
        if dwell < 0:
            raise ValueError("DRILL: Verweilzeit darf nicht negativ sein.")
    if mode in ("G83", "G73"):
        peck_depth = finite_float(p["peck_depth"], "DRILL peck_depth")
        if peck_depth <= 0 or float(f"{peck_depth:.3f}") <= 0:
            raise ValueError("DRILL: Zustelltiefe muss in der Ausgabe groesser als null sein.")

    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
        spindle_mode="fixed",
        spindle_max_rpm=op.params.get("spindle_max_rpm"),
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    if retract < safe_z:
        lines.append(f"(WARN: retract ({retract:.3f}) < safe_z ({safe_z:.3f}); verwende safe_z)")
        retract = safe_z

    lines.append("(Anfahren vor Zyklus)")
    # Nutzte zuvor eine eigene, dupliziert-und-abweichende Anfahrlogik (generische
    # sichere Position ueber Z/X, danach nochmal separat auf x_start/safe_z -
    # teils redundante Bewegungen). Verwendet jetzt denselben Sicherheits-Helfer
    # wie jede andere Operation (Abspanen, Einstich), damit Anfahrt und die
    # bereits als korrekt bestaetigte Rueckzugssequenz (emit_safe_retract_for_op)
    # strukturell zueinander passen.
    emit_approach(lines, x_start, safe_z, settings)
    lines.append("(G17 nur fuer Bohrzyklus - LinuxCNC Besonderheit)")
    lines.append("G17")
    lines.append(f"F{feed:.3f}")
    if mode == "G81":
        lines.append(f"G81 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    elif mode == "G82":
        lines.append(f"G82 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} P{dwell:.3f} F{feed:.3f}")
    elif mode == "G83":
        lines.append(f"G83 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} Q{peck_depth:.3f} F{feed:.3f}")
    elif mode == "G73":
        lines.append(f"G73 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} Q{peck_depth:.3f} F{feed:.3f}")
    elif mode == "G84":
        lines.append(f"G84 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    else:
        lines.append(f"G81 X{x_start:.3f} Z{depth_z:.3f} R{retract:.3f} F{feed:.3f}")
    lines.append("G80")
    # LinuxCNC kehrt nach dem Zyklus (G80) auf die Rueckzugsebene R zurueck
    # (Default-Modus G99, real gegen rs274 verifiziert: nach STRAIGHT_FEED
    # zur Bohrtiefe folgt STRAIGHT_TRAVERSE zurueck auf R, nicht auf die vor
    # dem Zyklus aktive Z-Position). Steht R (retract) bereits auf safe_z -
    # der Standardfall, da retract ohne Angabe auf safe_z faellt - ist ein
    # zusaetzlicher G0 auf denselben Wert eine bedeutungslose Nullbewegung.
    # Nur wenn retract > safe_z explizit gesetzt wurde, ist die Freifahrt
    # auf safe_z eine echte Bewegung.
    if retract > safe_z:
        lines.append(f"G0 Z{safe_z:.3f}")
    lines.append("G18")
    return lines
