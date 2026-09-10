from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from .contour_logic import thread_relief_spec
from .model import Operation
from .numeric import finite_float, whole_number, validate_finite_data
from .gcode_utils import is_internal_side, is_left_hand, resolve_internal_safe_x, validate_internal_x_limit
from .gcode_safety import _motion_state, activate_pending_css


THREAD_ORIENTATION_LABELS: Tuple[str, str] = ("Aussen", "Innen")
THREAD_HAND_LABELS: Tuple[str, str] = ("Rechtsgewinde", "Linksgewinde")
def generate_thread_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require_tool: Callable[[Dict[str, object], str], int],
    get_tool_number: Callable[[Dict[str, object]], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
    emit_approach: Callable[[List[str], float, float, Dict[str, object] | None], None],
    sanitize_comment_text: Callable[[object], str],
) -> List[str]:
    settings = settings or {}
    validate_finite_data(op.params, "THREAD")
    validate_finite_data(settings, "Programmkopf")
    require_tool(op.params, "THREAD")
    safe_z = float(op.params.get("safe_z", 2.0))
    major_diameter = float(op.params.get("major_diameter", 0.0))
    pitch = float(op.params.get("pitch", 1.5))
    if pitch <= 0.0:
        raise ValueError("THREAD pitch muss groesser als 0 sein.")
    length = float(op.params.get("length", 0.0))
    start_z = float(op.params.get("thread_start_z", 0.0) or 0.0)
    hand_raw = op.params.get("hand", 0)
    hand_idx = 1 if is_left_hand(hand_raw) else 0
    hand_label = THREAD_HAND_LABELS[hand_idx]
    z_dir = -1.0 if hand_idx == 0 else 1.0
    end_z = start_z + (z_dir * abs(length))

    def automatic_positive(key, default):
        raw = op.params.get(key)
        value = 0.0 if raw in (None, "") else finite_float(raw, key)
        if value < 0:
            raise ValueError(f"THREAD {key} darf nicht negativ sein.")
        return value or default

    thread_depth = automatic_positive("thread_depth", pitch * 0.6134)
    first_depth = automatic_positive("first_depth", max(thread_depth * 0.1, pitch * 0.05))
    raw_peak_offset = op.params.get("peak_offset")
    peak_offset = abs(finite_float(raw_peak_offset, "peak_offset")) if raw_peak_offset not in (None, "") else 0.0
    peak_offset = peak_offset or max(first_depth, pitch * 0.05)
    retract_r = finite_float(op.params.get("retract_r", 1.5), "retract_r")
    infeed_q = finite_float(op.params.get("infeed_q", 29.5), "infeed_q")
    raw_spring = op.params.get("spring_passes")
    spring_passes = whole_number(op.params.get("passes", 1) if raw_spring in (None, "") else raw_spring, "spring_passes")
    e_val = finite_float(op.params.get("e", 0.0), "e")
    l_val = whole_number(op.params.get("l", 0), "l")
    lead_in = finite_float(op.params.get("lead_in", 0.0) or 0.0, "lead_in")
    lead_out = finite_float(op.params.get("lead_out", 0.0) or 0.0, "lead_out")
    if major_diameter <= 0 or length <= 0 or 2 * thread_depth >= major_diameter:
        raise ValueError("THREAD Durchmesser, Laenge und Kerndurchmesser muessen positiv sein.")
    if first_depth > thread_depth:
        raise ValueError("THREAD first_depth darf thread_depth nicht uebersteigen.")
    if retract_r < 1 or spring_passes < 0 or l_val not in (0, 1, 2, 3):
        raise ValueError("THREAD erfordert R >= 1, H >= 0 und L in 0..3.")
    # Q ist der Zustellwinkel des G76-Kompoundschlittens: 0 Grad bedeutet
    # radiale Zustellung (gueltig, z. B. fuer quadratische Gewinde), Werte
    # nahe/ueber 90 Grad sind physikalisch keine Zustellung mehr entlang der
    # Flanke. Bisher wurde ein negativer oder unplausibel grosser Wert
    # ungeprueft direkt in die Q-Ausgabe uebernommen.
    if not (0.0 <= infeed_q < 90.0) or float(f"{infeed_q:.4f}") >= 90.0:
        raise ValueError("THREAD Zustellwinkel (infeed_q/Q) muss im Bereich 0 bis <90 Grad liegen.")
    if min(e_val, lead_in, lead_out) < 0:
        raise ValueError("THREAD Taperlaengen duerfen nicht negativ sein.")
    if lead_in > 0.0 or lead_out > 0.0:
        if lead_in > 0.0 and lead_out > 0.0 and abs(lead_in - lead_out) > 1e-6:
            raise ValueError(
                "G76 unterstuetzt nur eine gemeinsame Taperlaenge E. "
                "Gewinde-Vorlauf und -Auslauf muessen deshalb gleich sein "
                "oder es darf nur einer der beiden Werte gesetzt werden."
            )
        e_val = lead_in or lead_out
        l_val = 3 if lead_in > 0.0 and lead_out > 0.0 else (1 if lead_in > 0.0 else 2)

    if e_val > length / 2:
        raise ValueError("THREAD Taperlaenge E darf die halbe Gewindelaenge nicht uebersteigen.")

    orientation_raw = op.params.get("orientation", 0)
    internal = is_internal_side(orientation_raw)
    orientation_idx = 1 if internal else 0
    orientation_label = THREAD_ORIENTATION_LABELS[orientation_idx]
    standard_data = op.params.get("standard")
    standard_label = ""
    if isinstance(standard_data, dict):
        std_label_tmp = standard_data.get("label")
        if isinstance(std_label_tmp, str):
            standard_label = std_label_tmp

    minor_diameter = major_diameter - 2.0 * thread_depth
    full_thread_depth = abs(major_diameter - minor_diameter)
    first_cut_depth = max(first_depth * 2.0, 0.0001)

    if internal:
        peak_offset = abs(peak_offset)
        approach_x = minor_diameter - peak_offset
        safe_x = validate_internal_x_limit(
            settings,
            [major_diameter, minor_diameter, approach_x],
            op_label="Innengewinde",
        )
    else:
        peak_offset = -abs(peak_offset)
        approach_x = major_diameter - peak_offset

    comments: List[str] = []
    if standard_label and standard_label != "Benutzerdefiniert":
        comments.append(f"(Normgewinde: {sanitize_comment_text(standard_label)})")
    comments.append(f"(Gewindetyp: {orientation_label})")
    comments.append(f"(Gewinderichtung: {hand_label})")
    comments.append(f"(Gewindestart/-ende Z: {start_z:.3f} -> {end_z:.3f})")
    if lead_in > 0.0 or lead_out > 0.0:
        comments.append(f"(Gewinde-Taper: Vorlauf={lead_in:.3f} Auslauf={lead_out:.3f} mm; G76 E={e_val:.3f} L={l_val})")
    relief_mode = str(op.params.get("relief_mode", "off") or "off").strip().lower()
    relief_norm = str(op.params.get("relief_norm", "DIN 76-A") or "DIN 76-A").strip()
    if relief_mode in ("suggest", "suggest_din_relief"):
        relief_data = op.params.get("_derived_relief")
        if not isinstance(relief_data, dict):
            relief_data = thread_relief_spec(op.params)
        if relief_data:
            relief_size = str(relief_data["thread_size"])
            relief_width = float(relief_data["width"])
            relief_depth = float(relief_data["depth"])
            comments.append(
                f"(DIN-Freistich: {relief_norm} {relief_size} {orientation_label} B={relief_width:.3f} T={relief_depth:.3f}"
                f"{' Kurzform' if relief_data.get('variant') == 'short' else ''})"
            )
            comments.append(
                f"(Gewindeende Z={end_z:.3f}; Ueberdeckung f={float(relief_data['thread_overlap']):.3f})"
            )

    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
        spindle_mode=op.params.get("spindle_mode"),
        spindle_max_rpm=op.params.get("spindle_max_rpm"),
        cutting_speed=op.params.get("cutting_speed"),
        css_start_diameter=abs(approach_x),
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    lines.extend(comments)

    if bool(op.params.get("optional_stop_before", False)):
        lines.append("M1")
    lines.append("(Anfahren vor Gewinde)")
    if internal:
        safe_x = resolve_internal_safe_x(settings)
        if safe_x is None:
            raise ValueError("Innengewinde erfordert ein gueltiges XRI im Programmkopf.")
        # Direkt auf (XRI, start_z) anfahren statt zusaetzlich ueber das
        # eigene "Sicherheits-Z"-Feld des Gewinde-Steps zu routen: XRI ist per
        # Definition bei JEDER Z-Position innerhalb der Bohrung sicher, ein
        # zusaetzlicher Zwischenstopp bei einem ggf. abweichenden safe_z
        # erzeugte sonst einen unnoetigen Rueckzug (Z wird zwischenzeitlich
        # groesser/weiter vom Material weg, bevor wieder auf start_z
        # zugefahren wird) - real beobachtet und gemeldet.
        emit_approach(lines, safe_x, start_z, settings)
        if abs(approach_x - safe_x) > 1e-9:
            lines.append(f"G0 X{approach_x:.3f}")
    else:
        emit_approach(lines, approach_x, safe_z, settings)
        if abs(start_z - safe_z) > 1e-9:
            lines.append(f"G0 Z{start_z:.3f}")
    activate_pending_css(lines, settings)
    lines.append(
        (
            "G76 "
            f"P{pitch:.4f} "
            f"Z{end_z:.3f} "
            f"I{peak_offset:.4f} "
            f"J{first_cut_depth:.4f} "
            f"R{retract_r:.4f} "
            f"K{full_thread_depth:.4f} "
            f"Q{infeed_q:.4f} "
            f"H{spring_passes:d} "
            f"E{e_val:.4f} "
            f"L{l_val:d}"
        )
    )
    # LES-022 (dritte Etappe): G76 endet nachweislich (rs274-Verifikation)
    # exakt bei (approach_x, end_z) - der letzte Gewindeschnitt faehrt auf
    # volle Tiefe bis zum Gewindeende und retraktiert NICHT automatisch.
    # Vorher blieb der gemeinsame Bewegungszustand faelschlich auf der
    # Anfahrposition VOR dem Gewindeschneiden stehen (insbesondere Z blieb
    # auf start_z statt end_z) - ein Folgeschritt haette einen noetigen
    # Rueckzug potenziell faelschlich als bereits erledigt angesehen.
    if settings is not None:
        _motion_state(settings).record(approach_x, end_z)
    return lines
