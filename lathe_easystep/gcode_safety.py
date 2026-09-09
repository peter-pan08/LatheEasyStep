from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from .gcode_utils import float_or_none, get_tool_number, sanitize_comment_text
from .model import OpType, Operation
from .motion_state import MotionState, SpindleState
from .numeric import finite_float, whole_number


def _motion_state(settings: Dict[str, object] | None) -> MotionState:
    """Get-or-create den zentralen Bewegungszustand (LES-022) auf `settings`.

    Viele Aufrufer (insbesondere Tests) reichen rohe, handgebaute Dicts ohne
    vorherige Initialisierung durch `generate_program_gcode()` durch - daher
    legt diese Funktion `_motion` bei Bedarf lazy an, statt eine vorherige
    Initialisierung vorauszusetzen.
    """
    if settings is None:
        return MotionState()
    state = settings.get("_motion")
    if not isinstance(state, MotionState):
        state = MotionState()
        settings["_motion"] = state
    return state


def _spindle_state(settings: Dict[str, object] | None) -> SpindleState:
    """Get-or-create den CSS-Modalzustand (LES-022) auf `settings`."""
    if settings is None:
        return SpindleState()
    state = settings.get("_spindle")
    if not isinstance(state, SpindleState):
        state = SpindleState()
        settings["_spindle"] = state
    return state


def _safe_axis_value(
    settings: Dict[str, object] | None,
    *,
    axis: str,
    internal: bool,
) -> Optional[float]:
    if not settings:
        return None
    base_key = f"{axis}{'ri' if internal else 'ra'}"
    base_value = float_or_none(settings.get(base_key))
    if base_value is None:
        return None
    absolute = bool(settings.get(f"{base_key}_absolute", False))
    if absolute:
        return base_value
    # X: "innen" heisst radial zur Bohrungswand hin (xi = vorhandener Innen-
    # durchmesser), das kehrt sich zwischen aussen/innen tatsaechlich um.
    # Z: die Werkzeugfreifahrt erfolgt bei Innen- UND Aussenbearbeitung immer
    # zur vorderen, zugaenglichen Seite (za = "Vorderes Anfangsmass"), niemals
    # zum hinteren Ende (zi = "Hinteres Endmass"), das beim Innenbohren naeher
    # am Futter liegt und keine sichere Rueckzugsrichtung ist. zi + zri wuerde
    # hier eine Rueckzugsebene mitten im bzw. jenseits des Rohteils erzeugen
    # (siehe get_approach_warnings: "Rueckzugsebene schneidet den Futterbereich").
    stock_key = "xi" if internal and axis == "x" else "xa" if axis == "x" else "za"
    stock_value = float_or_none(settings.get(stock_key))
    if stock_value is None:
        return None
    return stock_value + base_value


def get_safe_position(settings: Dict[str, object] | None) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    internal = str(settings.get("_active_retract_mode", "") or "").strip().lower() == "internal"
    x_safe = _safe_axis_value(settings, axis="x", internal=internal)
    z_safe = _safe_axis_value(settings, axis="z", internal=internal)
    if x_safe is None or z_safe is None:
        if internal:
            x_safe = _safe_axis_value(settings, axis="x", internal=False)
            z_safe = _safe_axis_value(settings, axis="z", internal=False)
        if x_safe is None or z_safe is None:
            return None
    return (x_safe, z_safe)


def get_safe_position_for_mode(
    settings: Dict[str, object] | None,
    *,
    internal: bool,
) -> Optional[Tuple[float, float]]:
    if not settings:
        return None
    saved = settings.get("_active_retract_mode")
    try:
        settings["_active_retract_mode"] = "internal" if internal else "external"
        return get_safe_position(settings)
    finally:
        if saved is None:
            settings.pop("_active_retract_mode", None)
        else:
            settings["_active_retract_mode"] = saved


def emit_safe_retract(lines: List[str], settings: Dict[str, object] | None) -> None:
    emit_safe_retract_for_op(lines, settings, None)


def emit_safe_retract_for_op(
    lines: List[str],
    settings: Dict[str, object] | None,
    op_type: Optional[str],
    current_pos: Optional[Tuple[float, float]] = None,
) -> None:
    suspend_css(lines, settings)
    safe = get_safe_position(settings)
    if not safe:
        return
    x_safe, z_safe = safe

    def _inside_stock_envelope(pos: Optional[Tuple[float, float]]) -> bool:
        if pos is None or settings is None:
            return False
        xa = float_or_none(settings.get("xa"))
        za = float_or_none(settings.get("za"))
        zi = float_or_none(settings.get("zi"))
        if xa is None or za is None or zi is None:
            return False
        xi = float_or_none(settings.get("xi"))
        if xi is None:
            xi = 0.0
        x, z = pos
        x_min = min(xi, xa)
        x_max = max(xi, xa)
        z_min = min(zi, za)
        z_max = max(zi, za)
        eps = 1e-6
        return (x_min - eps) <= x <= (x_max + eps) and (z_min - eps) <= z <= (z_max + eps)

    def _inside_chuck_nogo(pos: Optional[Tuple[float, float]]) -> bool:
        if pos is None or settings is None:
            return False
        x_min = float_or_none(settings.get("chuck_no_go_x_min"))
        x_max = float_or_none(settings.get("chuck_no_go_x_max"))
        z_lim = float_or_none(settings.get("chuck_no_go_z_limit"))
        if x_min is None or x_max is None or z_lim is None:
            return False
        x, z = pos
        lo = min(x_min, x_max)
        hi = max(x_min, x_max)
        eps = 1e-6
        if x < lo - eps or x > hi + eps:
            return False
        za = float_or_none(settings.get("za"))
        if za is None:
            return z <= z_lim + eps
        if z_lim <= za:
            return z <= z_lim + eps
        return z >= z_lim - eps

    inside_stock = _inside_stock_envelope(current_pos)
    inside_chuck_nogo = _inside_chuck_nogo(current_pos)
    internal = str((settings or {}).get("_active_retract_mode", "") or "").strip().lower() == "internal"

    def _validate_second_leg(corner: Tuple[float, float]) -> None:
        # Erstes Teilstueck (Weg AUS der aktuellen, ggf. gefaehrlichen
        # Position hinaus) wird bewusst NICHT geprueft: es darf legitim in
        # der Rohteil-Huellkurve bzw. Futter-Sperrzone STARTEN (genau dafuer
        # existiert diese Fluchtbewegung). Das zweite Teilstueck haelt die
        # zuerst freigefahrene Achse konstant auf ihrem sicheren Wert - hier
        # deckt die Pruefung eine fehlkonfigurierte "sichere" Position auf
        # (z. B. XRA/ZRA, die tatsaechlich noch im Rohteil oder in der
        # Futterzone liegt). Die Rohteil-Pruefung gilt nur fuer echte
        # Aussen-Sicherheitspositionen, da die Huellkurve keine Bohrung
        # abbilden kann.
        if current_pos is None:
            return
        validate_chuck_segment(settings, corner, (x_safe, z_safe))
        if not internal:
            validate_stock_segment(settings, corner, (x_safe, z_safe))

    if op_type in (OpType.GROOVE, OpType.KEYWAY):
        if current_pos is not None:
            _validate_second_leg((x_safe, current_pos[1]))
        lines.append(f"G0 X{x_safe:.3f}")
        lines.append(f"G0 Z{z_safe:.3f}")
    elif op_type in (OpType.DRILL, OpType.THREAD):
        if current_pos is not None:
            _validate_second_leg((current_pos[0], z_safe))
        lines.append(f"G0 Z{z_safe:.3f}")
        lines.append(f"G0 X{x_safe:.3f}")
    elif inside_stock or inside_chuck_nogo:
        if current_pos is not None:
            _validate_second_leg((x_safe, current_pos[1]))
        lines.append(f"G0 X{x_safe:.3f}")
        lines.append(f"G0 Z{z_safe:.3f}")
    else:
        if current_pos is not None:
            validate_chuck_segment(settings, current_pos, (x_safe, z_safe))
            if not internal:
                validate_stock_segment(settings, current_pos, (x_safe, z_safe))
        lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")
    if settings is not None:
        _motion_state(settings).record(x_safe, z_safe)


def estimate_operation_end_pos(op: Operation) -> Optional[Tuple[float, float]]:
    path = op.path or []
    if path:
        last = path[-1]
        if isinstance(last, (tuple, list)) and len(last) >= 2:
            try:
                return (float(last[0]), float(last[1]))
            except Exception:
                pass
    p = op.params or {}
    if op.op_type in (OpType.GROOVE, OpType.KEYWAY):
        a_end = float_or_none(p.get("A_end"))
        mode = int(float_or_none(p.get("mode")) or 0)
        c_val = float_or_none(p.get("C"))
        if a_end is not None and c_val is not None:
            return (a_end, c_val) if mode == 0 else (c_val, a_end)
    if op.op_type == OpType.FACE:
        x = float_or_none(p.get("end_x"))
        z = float_or_none(p.get("end_z"))
        if x is not None and z is not None:
            return (x, z)
    return None


def validate_chuck_segment(settings, start, end):
    """Closed X interval intersected with the chuck-side Z half-plane."""
    if not settings:
        return
    keys = ("chuck_no_go_x_min", "chuck_no_go_x_max", "chuck_no_go_z_limit")
    values = [float_or_none(settings.get(key)) for key in keys]
    if all(value is None for value in values):
        return
    if any(value is None for value in values):
        raise ValueError("Futter-Sperrzone ist unvollstaendig definiert.")
    lo, hi = sorted(values[:2])
    z_limit = values[2]
    za = float_or_none(settings.get("za"))
    direction = 1.0 if za is None or z_limit <= za else -1.0
    # Parametric segment clipping, including boundary contact.
    t_min, t_max = 0.0, 1.0
    x, z = start
    dx, dz = end[0] - x, end[1] - z
    for origin, delta, lower, upper in (
        (x, dx, lo - 1e-6, hi + 1e-6),
        (direction * z, direction * dz, float("-inf"), direction * z_limit + 1e-6),
    ):
        if abs(delta) < 1e-12:
            if origin < lower or origin > upper:
                return
        else:
            a, b = sorted(((lower - origin) / delta, (upper - origin) / delta))
            t_min, t_max = max(t_min, a), min(t_max, b)
            if t_min > t_max:
                return
    raise ValueError(f"Futter-Sperrzone: Fahrweg {start} -> {end} ist gesperrt.")


def validate_stock_segment(settings, start, end):
    """Closed X/Z rectangle formed by the raw stock envelope (XA/XI, ZA/ZI).

    Nur fuer reine Diagonal-Eilgaenge gedacht, die beide Endpunkte bewusst
    ausserhalb der Rohteil-Huellkurve anfahren (z. B. sicherer Rueckzug,
    Werkzeugwechselposition). Die achsweise Anfahrt/Rueckzugsfolge in
    emit_approach haelt bereits je einen Achswert ausserhalb der Huellkurve
    und wird hier bewusst nicht geprueft, da deren Zielpunkt haeufig
    beabsichtigt innerhalb der Huellkurve liegt (z. B. Schlichten auf einem
    bereits abgetragenen Durchmesser).
    """
    if not settings:
        return
    xa = float_or_none(settings.get("xa"))
    za = float_or_none(settings.get("za"))
    zi = float_or_none(settings.get("zi"))
    if xa is None or za is None or zi is None:
        return
    xi = float_or_none(settings.get("xi"))
    if xi is None:
        xi = 0.0
    x_lo, x_hi = sorted((xi, xa))
    z_lo, z_hi = sorted((zi, za))
    # Parametric segment clipping, including boundary contact.
    t_min, t_max = 0.0, 1.0
    x, z = start
    dx, dz = end[0] - x, end[1] - z
    for origin, delta, lower, upper in (
        (x, dx, x_lo - 1e-6, x_hi + 1e-6),
        (z, dz, z_lo - 1e-6, z_hi + 1e-6),
    ):
        if abs(delta) < 1e-12:
            if origin < lower or origin > upper:
                return
        else:
            a, b = sorted(((lower - origin) / delta, (upper - origin) / delta))
            t_min, t_max = max(t_min, a), min(t_max, b)
            if t_min > t_max:
                return
    raise ValueError(f"Rohteil: Eilgang {start} -> {end} durchquert die Rohteil-Huellkurve.")


def emit_approach(lines: List[str], start_x: float, start_z: float, settings: Dict[str, object] | None) -> None:
    suspend_css(lines, settings, resume=True)
    start_x = finite_float(start_x, "Anfahrt X")
    start_z = finite_float(start_z, "Anfahrt Z")
    validate_chuck_segment(settings, (start_x, start_z), (start_x, start_z))
    safe = get_safe_position(settings)
    if safe:
        x_safe, z_safe = safe
        validate_chuck_segment(settings, safe, (x_safe, start_z))
        validate_chuck_segment(settings, (x_safe, start_z), (start_x, start_z))
        internal = str((settings or {}).get("_active_retract_mode", "") or "").strip().lower() == "internal"
        # Der Z-Zwischenzug haelt X bewusst auf der sicheren Aussenposition -
        # die Zielposition selbst (naechste Zeile oben) darf dagegen
        # absichtlich innerhalb der Rohteil-Huellkurve liegen (z. B.
        # Schlichten nach Schruppen). Fuer den Innen-Modus entfaellt die
        # Pruefung, da die Huellkurve eine Bohrung nicht abbilden kann.
        if not internal:
            validate_stock_segment(settings, safe, (x_safe, start_z))
    for warning in get_approach_warnings(settings, (start_x, start_z)):
        lines.append(f"(WARN: {sanitize_comment_text(warning)})")
    safe = get_safe_position(settings)
    if safe and settings is not None:
        x_safe, z_safe = safe
        internal = str(settings.get("_active_retract_mode", "") or "").strip().lower() == "internal"
        # In der Bohrung darf kein diagonaler Schnellgang vom Rueckzugspunkt
        # zum Konturstart entstehen. Der Inventor/LinuxCNC-Post faehrt erst
        # axial auf der freien XRI-Ebene und stellt erst dort radial zu.
        state = _motion_state(settings)
        if internal:
            if not state.at(x_safe, z_safe):
                lines.append(f"G0 Z{z_safe:.3f}")
                lines.append(f"G0 X{x_safe:.3f}")
            # Nach der (ggf. uebersprungenen) Anfahrt auf die sichere XRI-/
            # ZRI-Ebene steht das Werkzeug bereits auf z_safe - ein weiterer
            # G0 auf denselben Z-Wert (haeufig, da der Konturstart oft genau
            # auf der sicheren Z-Ebene liegt) waere eine bedeutungslose
            # Nullbewegung.
            if abs(start_z - z_safe) > 1e-9:
                lines.append(f"G0 Z{start_z:.3f}")
            if abs(start_x - x_safe) > 1e-9:
                lines.append(f"G0 X{start_x:.3f}")
            state.record(start_x, start_z)
            return
        if not state.at(x_safe, z_safe):
            lines.append(f"G0 Z{z_safe:.3f}")
            lines.append(f"G0 X{x_safe:.3f}")
        if abs(start_z - z_safe) > 1e-9:
            lines.append(f"G0 Z{start_z:.3f}")
        if abs(start_x - x_safe) > 1e-9:
            lines.append(f"G0 X{start_x:.3f}")
        state.record(start_x, start_z)
        return
    lines.append(f"G0 Z{start_z:.3f}")
    lines.append(f"G0 X{start_x:.3f}")
    if settings is not None:
        _motion_state(settings).record(start_x, start_z)


def append_tool_and_spindle(
    lines: List[str],
    tool_value: object | None,
    spindle_value: object | None,
    settings: Dict[str, object] | None = None,
    *,
    spindle_mode: object | None = None,
    spindle_max_rpm: object | None = None,
    cutting_speed: object | None = None,
    css_start_diameter: object | None = None,
    require_spindle: bool = True,
):
    suspend_css(lines, settings)
    if tool_value is None and settings is not None:
        tool_num = get_tool_number(settings)
    else:
        tool_num = get_tool_number({"tool": tool_value})

    if tool_num > 0:
        last_tool = int(float(settings.get("_current_tool", 0))) if settings else 0
        if tool_num != last_tool:
            if settings is None:
                raise ValueError("Werkzeugwechsel erfordert Programmkopf mit XT/ZT.")
            toolchange_lines = move_to_toolchange_pos(settings)
            lines.append(f"(Werkzeug T{tool_num:02d})")
            if settings is not None:
                # M1 VOR der angenommenen sicheren Rueckzugsbewegung, nicht
                # danach: bei unbekanntem Ausgangszustand (insbesondere vor
                # dem allerersten Werkzeugwechsel, wo Werkzeug und Position
                # nicht aus einer vorherigen Operation bekannt sind) soll der
                # Bediener vor JEDER angenommenen sicheren Bewegung pruefen
                # koennen - nicht erst danach. Bewusst nicht mehr auf
                # last_tool > 0 beschraenkt: das Tooltip verspricht "vor
                # jedem Werkzeugwechsel", nicht "vor jedem weiteren".
                if bool(settings.get("optional_stop_toolchange", False)):
                    lines.append("M1")
                safe = get_safe_position_for_mode(settings, internal=False)
                if safe:
                    x_safe, z_safe = safe
                    # Die vorherige Operation hat bereits per
                    # emit_safe_retract_for_op() exakt auf diese Aussen-
                    # Position zurueckgezogen (haeufigster Fall: Aussen- auf
                    # Aussen-Operation mit demselben XRA/ZRA) - ein erneuter
                    # G0 auf denselben Wert waere eine bedeutungslose
                    # Nullbewegung. Der zentrale Bewegungszustand (LES-022)
                    # haelt fest, WELCHE Position zuletzt tatsaechlich
                    # erreicht wurde (Innen- und Aussen-Sicherheitspositionen
                    # koennen sich unterscheiden, ein reines Flag reicht
                    # nicht).
                    already_here = _motion_state(settings).at(x_safe, z_safe)
                    if not already_here:
                        lines.append(f"G0 Z{z_safe:.3f}")
                        lines.append(f"G0 X{x_safe:.3f}")
                    _motion_state(settings).record(x_safe, z_safe)
                lines.append("M5")
                lines.append("M9")
                lines.extend(toolchange_lines)
            lines.append(f"T{tool_num:02d} M6")
            if settings is not None:
                settings["_current_tool"] = tool_num
                safe = get_safe_position(settings)
                if safe:
                    x_safe, z_safe = safe
                    lines.append(f"G0 X{x_safe:.3f} Z{z_safe:.3f}")
                    _motion_state(settings).record(x_safe, z_safe)
    # Op-spezifischer Drehzahlmodus hat Vorrang; ohne Angabe gilt weiterhin
    # der globale Programmkopf-Wert (Rueckwaertskompatibilitaet).
    if spindle_mode is not None:
        effective_mode = str(spindle_mode or "fixed").strip().lower()
    else:
        effective_mode = str((settings or {}).get("spindle_mode", "fixed") or "fixed").strip().lower()
    if effective_mode in ("css", "g96"):
        # G96 (CSS) erwartet unter S die Schnittgeschwindigkeit Vc (m/min),
        # NICHT die Drehzahl - beide Werte duerfen nicht verwechselt werden,
        # auch wenn im Festdrehzahl-Modus (G97) dasselbe Feld "spindle" die
        # Drehzahl traegt. Fehlt cutting_speed (z. B. weil der Aufrufer den
        # neuen Parameter noch nicht befuellt), wird sicherheitshalber G97
        # mit der Drehzahl verwendet statt eine falsche Zahl als Vc zu senden.
        vc = float_or_none(cutting_speed)
        if spindle_max_rpm is not None:
            max_rpm = float_or_none(spindle_max_rpm)
        else:
            max_rpm = float_or_none((settings or {}).get("spindle_max_rpm"))
        if vc and vc > 0 and max_rpm and max_rpm > 0:
            diameter = float_or_none(css_start_diameter)
            if diameter is None or diameter <= 0 or float(f"{diameter:.3f}") <= 0:
                raise ValueError(
                    "CSS/G96 erfordert einen positiven ersten Bearbeitungsdurchmesser."
                )
            if float(f"{vc:.1f}") <= 0:
                raise ValueError("CSS/G96 Schnittgeschwindigkeit rundet in der Ausgabe auf null.")
            # Vc wird in der UI immer in m/min erfasst, X ist ein Durchmesser.
            # Die feste Anfahrdrehzahl entspricht deshalb n=1000*Vc/(pi*d)
            # und wird hart auf die programmweite Maximaldrehzahl begrenzt.
            rpm_limit = math.floor(max_rpm)
            if rpm_limit < 1:
                raise ValueError("CSS/G96 Maximaldrehzahl muss mindestens 1 U/min sein.")
            start_rpm = min(rpm_limit, (vc / diameter) * (1000.0 / math.pi))
            rpm_value = min(rpm_limit, max(1, int(round(start_rpm))))
            lines.append(f"G97 S{rpm_value} M3 (CSS-Anfahrdrehzahl bei X{diameter:.3f})")
            if settings is None:
                raise ValueError("CSS/G96 erfordert Programmkopf-Einstellungen.")
            _spindle_state(settings).request(rpm_limit, vc, rpm_value)
            return
        rpm = float_or_none(spindle_value)
        rpm_value = int(round(rpm)) if rpm and rpm > 0 else 0
        if rpm_value > 0:
            if not (vc and vc > 0):
                lines.append("(WARN: CSS angefordert, aber Schnittgeschwindigkeit fehlt - nutze G97)")
            else:
                lines.append("(WARN: CSS angefordert, aber spindle_max_rpm fehlt - nutze G97)")
            lines.append(f"G97 S{rpm_value} M3")
        elif require_spindle:
            raise ValueError(
                "Drehzahl fehlt: weder vollstaendige CSS-Parameter (Schnittgeschwindigkeit "
                "und Maximaldrehzahl) noch eine positive feste Drehzahl als Ausweichwert "
                "vorhanden - die Spindel wuerde nicht gestartet."
            )
        return
    rpm = float_or_none(spindle_value)
    if settings is not None:
        _spindle_state(settings).pending = None
    rpm_value = int(round(rpm)) if rpm and rpm > 0 else 0
    if rpm_value > 0:
        lines.append(f"G97 S{rpm_value} M3")
    elif require_spindle:
        raise ValueError(
            "Drehzahl fehlt, ist nicht positiv oder rundet auf 0 U/min - die Spindel "
            "wuerde nicht gestartet."
        )


def activate_pending_css(lines: List[str], settings: Dict[str, object] | None) -> None:
    """Aktiviert ein vorbereitetes G96 erst an der Bearbeitungsposition."""
    if settings is None:
        return
    pending = _spindle_state(settings).activate()
    if pending is None:
        return
    max_rpm, vc = pending
    lines.append(f"G96 D{int(max_rpm)} S{float(vc):.1f}")


def suspend_css(lines: List[str], settings: Dict[str, object] | None, *, resume=False) -> None:
    """Use the bounded approach RPM for explicit clearance and tool changes."""
    if settings is None:
        return
    state = _spindle_state(settings)
    active = state.suspend(resume=resume)
    if active is not None:
        rpm = state.fixed_rpm
        if rpm is None:
            raise ValueError("CSS-Rueckzug erfordert eine bekannte Festdrehzahl.")
        lines.append(f"G97 S{int(rpm)} (CSS-Freifahrt)")


def nose_compensation_command(tool_info: Dict[str, object] | None, external: bool) -> Optional[str]:
    if not tool_info:
        return None
    radius = float_or_none(tool_info.get("radius_mm"))
    if radius is not None and radius < 0:
        raise ValueError("Werkzeugradius darf nicht negativ sein.")
    if radius is None or radius == 0:
        return None
    orientation_raw = tool_info.get("q")
    if orientation_raw is None:
        return None
    orientation_idx = whole_number(orientation_raw, "Werkzeugorientierung Q/L")
    if not 0 <= orientation_idx <= 9:
        raise ValueError("Werkzeugorientierung Q/L muss in 0..9 liegen.")
    diameter = finite_float(radius * 2, "Schneidendurchmesser")
    if float(f"{diameter:.4f}") <= 0:
        raise ValueError("Schneidendurchmesser rundet bei Radiuskorrektur auf null.")
    comp_code = "G42.1" if external else "G41.1"
    return f"{comp_code} D{diameter:.4f} L{orientation_idx}"


def _coord_mode(settings: Dict[str, object] | None, primary_key: str, *, legacy_x_key: str | None = None, legacy_z_key: str | None = None, default: str = "work") -> str:
    if settings is None:
        return default
    mode = str(settings.get(primary_key, "") or "").strip().lower()
    if mode in ("machine", "g53"):
        return "machine"
    if mode in ("work", "wcs", "g54"):
        return "work"
    if legacy_x_key and legacy_z_key:
        x_abs = bool(settings.get(legacy_x_key, True))
        z_abs = bool(settings.get(legacy_z_key, True))
        if x_abs != z_abs:
            return "mixed"
        return "work" if x_abs and z_abs else "machine"
    return default


def move_to_toolchange_pos(settings: Dict[str, object], label: str | None = None) -> List[str]:
    xt = float_or_none(settings.get("xt"))
    zt = float_or_none(settings.get("zt"))
    prefix = f"({label})" if label else "(Toolchange move)"
    lines: List[str] = [prefix]
    if xt is None or zt is None:
        raise ValueError("Werkzeugwechselposition XT/ZT fehlt.")
    mode = _coord_mode(settings, "toolchange_coords", legacy_x_key="xt_absolute", legacy_z_key="zt_absolute")
    if mode == "machine":
        lines.append(f"G53 G0 X{xt:.3f} Z{zt:.3f}")
    elif mode == "mixed":
        if not bool(settings.get("xt_absolute", True)):
            lines.append(f"G53 G0 X{xt:.3f}")
        if not bool(settings.get("zt_absolute", True)):
            lines.append(f"G53 G0 Z{zt:.3f}")
        if bool(settings.get("xt_absolute", True)) and bool(settings.get("zt_absolute", True)):
            lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
        else:
            work_parts = []
            if bool(settings.get("xt_absolute", True)):
                work_parts.append(f"X{xt:.3f}")
            if bool(settings.get("zt_absolute", True)):
                work_parts.append(f"Z{zt:.3f}")
            if work_parts:
                lines.append(f"G0 {' '.join(work_parts)}")
    else:
        safe = get_safe_position_for_mode(settings, internal=False)
        validate_chuck_segment(settings, safe or (xt, zt), (xt, zt))
        validate_stock_segment(settings, safe or (xt, zt), (xt, zt))
        lines.append(f"G0 X{xt:.3f} Z{zt:.3f}")
    return lines


def get_approach_warnings(settings: Dict[str, object] | None, start_pos: Tuple[float, float] | None) -> List[str]:
    warnings: List[str] = []
    if settings is None or start_pos is None:
        return warnings
    x, z = start_pos
    xa = float_or_none(settings.get("xa"))
    xi = float_or_none(settings.get("xi"))
    za = float_or_none(settings.get("za"))
    zi = float_or_none(settings.get("zi"))
    if xa is not None and za is not None and zi is not None:
        x_min = min(xi if xi is not None else 0.0, xa)
        x_max = max(xi if xi is not None else 0.0, xa)
        z_min = min(zi, za)
        z_max = max(zi, za)
        if x_min - 1e-6 <= x <= x_max + 1e-6 and z_min - 1e-6 <= z <= z_max + 1e-6:
            warnings.append(f"Startpunkt X{x:.3f} Z{z:.3f} liegt im Rohteil")
    x_min = float_or_none(settings.get("chuck_no_go_x_min"))
    x_max = float_or_none(settings.get("chuck_no_go_x_max"))
    z_lim = float_or_none(settings.get("chuck_no_go_z_limit"))
    if x_min is not None and x_max is not None and z_lim is not None:
        if min(x_min, x_max) - 1e-6 <= x <= max(x_min, x_max) + 1e-6:
            if z <= z_lim + 1e-6:
                warnings.append(f"Startpunkt X{x:.3f} Z{z:.3f} liegt in der Futter-Sperrzone")
        safe = get_safe_position(settings)
        if safe is not None:
            safe_x, safe_z = safe
            # Wie validate_chuck_segment() ist die Sperrzone ein Rechteck aus
            # X-Intervall UND Z-Halbebene - eine "sichere" Z-Ebene, die zwar
            # den Z-Grenzwert unterschreitet, deren X aber ausserhalb des
            # gesperrten X-Bereichs liegt, ist real nicht betroffen. Ohne
            # diese Pruefung widerspraeche die Warnung dem tatsaechlichen,
            # bereits durch validate_chuck_segment() abgesicherten Fahrweg.
            if safe_z <= z_lim + 1e-6 and min(x_min, x_max) - 1e-6 <= safe_x <= max(x_min, x_max) + 1e-6:
                warnings.append(f"Rueckzugsebene X{safe_x:.3f} Z{safe_z:.3f} schneidet den Futterbereich")
    return warnings


def get_machine_limit_warnings(settings: Dict[str, object] | None) -> List[str]:
    if settings is None:
        return []
    warnings: List[str] = []
    xa = float_or_none(settings.get("xa"))
    xi = float_or_none(settings.get("xi"))
    za = float_or_none(settings.get("za"))
    zi = float_or_none(settings.get("zi"))
    bounds = {
        "xt": float_or_none(settings.get("xt")),
        "zt": float_or_none(settings.get("zt")),
        "xra": float_or_none(settings.get("xra")),
        "xri": float_or_none(settings.get("xri")),
        "zra": float_or_none(settings.get("zra")),
        "zri": float_or_none(settings.get("zri")),
    }
    if xa is not None and xi is not None:
        span = max(abs(xa - xi), 1.0)
        low = min(xi, xa) - span * 2.0
        high = max(xi, xa) + span * 10.0 + 50.0
        for key in ("xt", "xra", "xri"):
            val = bounds.get(key)
            if val is not None and not (low <= val <= high):
                warnings.append(f"{key.upper()}={val:.3f} liegt ausserhalb plausibler X-Grenzen")
    if za is not None and zi is not None:
        span = max(abs(za - zi), 1.0)
        low = min(zi, za) - span * 10.0 - 50.0
        high = max(zi, za) + span * 10.0 + 50.0
        for key in ("zt", "zra", "zri"):
            val = bounds.get(key)
            if val is not None and not (low <= val <= high):
                warnings.append(f"{key.upper()}={val:.3f} liegt ausserhalb plausibler Z-Grenzen")
    return warnings


def get_end_park_lines(settings: Dict[str, object] | None) -> List[str]:
    if settings is None:
        return []
    park_mode = str(settings.get("park_mode", "toolchange") or "toolchange").strip().lower()
    sequential = bool(settings.get("park_sequential", False))
    if park_mode in ("end_position", "park", "custom"):
        x_park = float_or_none(settings.get("park_x"))
        z_park = float_or_none(settings.get("park_z"))
        label = "(Parkposition am Ende)"
        if x_park is None or z_park is None:
            return [label, "(WARN: Parkposition aktiv, aber park_x/park_z fehlen)"]
        park_machine = _coord_mode(settings, "park_coords", default="work") == "machine"
        if sequential:
            return [label, f"{'G53 G0' if park_machine else 'G0'} X{x_park:.3f}", f"{'G53 G0' if park_machine else 'G0'} Z{z_park:.3f}"]
        return [label, f"{'G53 G0' if park_machine else 'G0'} X{x_park:.3f} Z{z_park:.3f}"]
    xt_end = float_or_none(settings.get("xt"))
    zt_end = float_or_none(settings.get("zt"))
    if xt_end is None or zt_end is None:
        return []
    mode = _coord_mode(settings, "toolchange_coords", legacy_x_key="xt_absolute", legacy_z_key="zt_absolute")
    if mode == "machine":
        return ["(Werkzeugwechselpunkt am Ende)", f"G53 G0 X{xt_end:.3f} Z{zt_end:.3f}"]
    if mode == "mixed":
        lines = ["(Werkzeugwechselpunkt am Ende)"]
        if not bool(settings.get("xt_absolute", True)):
            lines.append(f"G53 G0 X{xt_end:.3f}")
        if not bool(settings.get("zt_absolute", True)):
            lines.append(f"G53 G0 Z{zt_end:.3f}")
        work_parts = []
        if bool(settings.get("xt_absolute", True)):
            work_parts.append(f"X{xt_end:.3f}")
        if bool(settings.get("zt_absolute", True)):
            work_parts.append(f"Z{zt_end:.3f}")
        if work_parts:
            lines.append(f"G0 {' '.join(work_parts)}")
        return lines
    return ["(Werkzeugwechselpunkt am Ende)", f"G0 X{xt_end:.3f} Z{zt_end:.3f}"]


__all__ = [
    "append_tool_and_spindle",
    "activate_pending_css",
    "emit_approach",
    "emit_safe_retract",
    "emit_safe_retract_for_op",
    "estimate_operation_end_pos",
    "get_safe_position",
    "get_safe_position_for_mode",
    "get_approach_warnings",
    "get_end_park_lines",
    "get_machine_limit_warnings",
    "move_to_toolchange_pos",
    "nose_compensation_command",
]
