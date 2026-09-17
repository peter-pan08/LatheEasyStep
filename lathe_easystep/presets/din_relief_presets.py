from __future__ import annotations

from typing import Dict, List


RELIEF_NORMS = ["DIN 76-A", "DIN 76-B", "DIN 76-C"]

# DIN 76-1:2016, tables 1 (outside forms A/B) and 2 (inside forms C/D).
# Each side stores dg as a diameter offset, then g1/g2 for the standard and
# short form.  The old table only held guessed depths; this data is the actual
# profile geometry used by the automatic relief generator.
def _din_side(dg_delta, g1, short_g1, g2, short_g2, radius):
    return {
        "dg_delta": dg_delta, "g1": g1, "short_g1": short_g1,
        "g2": g2, "short_g2": short_g2, "radius": radius,
    }



# M2/M2.5/M3.5 (2026-09-11/12): dg/g2/short_g2/radius/pitch stammen aus zwei
# unabhaengigen, sich deckenden Quellen (DIN 76 T1 12.83, "Tabellenbuch
# Metall", Europa-Lehrmittel, sowie DIN 76-1:2016-08, "Technische
# Kommunikation" K54, handwerk-technik.de) - beide Tabellen weisen allerdings
# NUR g2 (Form A/B/C/D) aus, kein g1. g1/short_g1 sind daher wie im
# Code-Kommentar oben beschrieben GEOMETRISCH HERGELEITET (g1 = g2 - Tiefe *
# tan(60 Grad), aus dem 30-Grad-Mindestflankenwinkel der Norm) - aber NUR fuer
# die AUSSENSEITE (Form A/B): Gegenprobe gegen alle 19 vorhandenen M3-M30-
# Aussen-Eintraege (2026-09-12, nach vollstaendiger Verifikation der
# gesamten Tabelle gegen DIN 76-1:2016-08, siehe TODO.md LES-010) trifft die
# Formel dort durchgehend auf 0.01-0.1mm genau. Fuer die INNENSEITE
# (Form C/D) ist dieselbe Formel NACHWEISLICH FALSCH - derselbe Vergleich
# zeigt eine mit der Groesse WACHSENDE Abweichung (M3: 0.44mm daneben, M30:
# 3.27mm daneben) statt kleiner Rundungsfehler; Innen-Freistiche folgen
# offenbar einer anderen geometrischen Konstruktion als der einfache
# 30-Grad-Flankenwinkel. Da sich diese Formel fuer die Innenseite nicht
# verifizieren liess, wird dort bewusst KEIN Wert geraten - `_din_side_
# unknown_g1()` (unten) laesst g1/short_g1 auf 0, was den bereits
# vorhandenen Fallback in contour_logic.py (`bottom_width = width * 0.5`,
# fuer genau diesen Fall vorgesehen) korrekt aktiviert.
def _din_side_derived_g1(dg_delta, g2, short_g2, radius):
    import math
    depth = abs(dg_delta) / 2.0
    flank = depth * math.tan(math.radians(60))
    return _din_side(dg_delta, round(g2 - flank, 3), round(short_g2 - flank, 3), g2, short_g2, radius)


def _din_side_unknown_g1(dg_delta, g2, short_g2, radius):
    """Wie `_din_side`, aber g1/short_g1 bewusst unbekannt (siehe Kommentar
    oben) - aktiviert den bestehenden width*0.5-Fallback in
    contour_logic.py statt eine ungeprueftes g1 anzunehmen."""
    return _din_side(dg_delta, 0.0, 0.0, g2, short_g2, radius)


DIN76_THREAD_DATA: Dict[str, Dict[str, object]] = {
    "M2": {"pitch": .4, "external": _din_side_derived_g1(-.7, 1.4, 1.0, .2), "internal": _din_side_unknown_g1(.2, 2.2, 1.6, .2)},
    "M2.5": {"pitch": .45, "external": _din_side_derived_g1(-.7, 1.6, 1.1, .2), "internal": _din_side_unknown_g1(.2, 2.4, 1.7, .2)},
    "M3": {"pitch": .5, "external": _din_side(-.8, 1.1, .5, 1.75, 1.25, .2), "internal": _din_side(.3, 2., 1.25, 2.7, 2., .2)},
    # M3.5 (2026-09-11): kein eigener Tabelleneintrag in beiden bisherigen
    # Quellen - die Zeile fuer Steigung P=0.6 (zwischen M3/P=0.5 und
    # M4/P=0.7) hat in DIN 76 T1 12.83 ("Tabellenbuch Metall",
    # Europa-Lehrmittel) an der ISO-Regelgewinde-Spalte ein "-", ist aber per
    # Tabellen-Fussnote ("Fuer Feingewinde sind die Masse des
    # Gewindefreistichs der einfachen Steigung P zu waehlen") explizit fuer
    # JEDES Gewinde mit dieser Steigung gueltig - und M3.5 hat genau P=0.6.
    # Vorbehalt: die AUSSENWERTE (Form A/B) dieser 1983er-Ausgabe liegen bei
    # M3 (direkte Nachbarzeile) ca. 0.05mm ueber der 2016er-Ausgabe/dem Rest
    # dieser Tabelle (1.8/1.3 statt 1.75/1.25) - die INNENWERTE stimmten dort
    # exakt ueberein. Fuer eine Freistichnut (keine Passmass-Funktion)
    # praktisch bedeutungslos, aber bewusst dokumentiert statt verschwiegen.
    "M3.5": {"pitch": .6, "external": _din_side_derived_g1(-1., 2.1, 1.5, .4), "internal": _din_side_unknown_g1(.3, 3.3, 2.4, .4)},
    "M4": {"pitch": .7, "external": _din_side(-1.1, 1.5, .8, 2.45, 1.75, .4), "internal": _din_side(.3, 2.8, 1.75, 3.8, 2.75, .4)},
    "M5": {"pitch": .8, "external": _din_side(-1.3, 1.7, .9, 2.8, 2., .4), "internal": _din_side(.3, 3.2, 2., 4.2, 3., .4)},
    "M6": {"pitch": 1., "external": _din_side(-1.6, 2.1, 1.1, 3.5, 2.5, .6), "internal": _din_side(.5, 4., 2.5, 5.2, 3.7, .6)},
    "M7": {"pitch": 1., "external": _din_side(-1.6, 2.1, 1.1, 3.5, 2.5, .6), "internal": _din_side(.5, 4., 2.5, 5.2, 3.7, .6)},
    "M8": {"pitch": 1.25, "external": _din_side(-2., 2.7, 1.5, 4.4, 3.2, .6), "internal": _din_side(.5, 5., 3.2, 6.7, 4.9, .6)},
    "M9": {"pitch": 1.25, "external": _din_side(-2., 2.7, 1.5, 4.4, 3.2, .6), "internal": _din_side(.5, 5., 3.2, 6.7, 4.9, .6)},
    "M10": {"pitch": 1.5, "external": _din_side(-2.3, 3.2, 1.8, 5.2, 3.8, .8), "internal": _din_side(.5, 6., 3.8, 7.8, 5.6, .8)},
    "M11": {"pitch": 1.5, "external": _din_side(-2.3, 3.2, 1.8, 5.2, 3.8, .8), "internal": _din_side(.5, 6., 3.8, 7.8, 5.6, .8)},
    # Internal short_g2 (Form D Kurz) 2026-09-12: war 6.4, per Vollverifikation
    # gegen DIN 76-1:2016-08 (siehe TODO.md LES-010) auf den korrekten
    # tabellierten Wert 6.1 korrigiert - die drei anderen M12-g-Werte
    # (Form A/B/C) stimmten bereits exakt, nur dieser eine wich ab.
    "M12": {"pitch": 1.75, "external": _din_side(-2.6, 3.9, 2.1, 6.1, 4.3, 1.), "internal": _din_side(.5, 7., 4.3, 9.1, 6.1, 1.)},
    "M14": {"pitch": 2., "external": _din_side(-3., 4.5, 2.5, 7., 5., 1.), "internal": _din_side(.5, 8., 5., 10.3, 7.3, 1.)},
    "M16": {"pitch": 2., "external": _din_side(-3., 4.5, 2.5, 7., 5., 1.), "internal": _din_side(.5, 8., 5., 10.3, 7.3, 1.)},
    "M18": {"pitch": 2.5, "external": _din_side(-3.6, 5.6, 3.2, 8.7, 6.3, 1.2), "internal": _din_side(.5, 10., 6.3, 13., 9.3, 1.2)},
    "M20": {"pitch": 2.5, "external": _din_side(-3.6, 5.6, 3.2, 8.7, 6.3, 1.2), "internal": _din_side(.5, 10., 6.3, 13., 9.3, 1.2)},
    "M22": {"pitch": 2.5, "external": _din_side(-3.6, 5.6, 3.2, 8.7, 6.3, 1.2), "internal": _din_side(.5, 10., 6.3, 13., 9.3, 1.2)},
    "M24": {"pitch": 3., "external": _din_side(-4.4, 6.7, 3.7, 10.5, 7.5, 1.6), "internal": _din_side(.5, 12., 7.5, 15.2, 10.7, 1.6)},
    "M27": {"pitch": 3., "external": _din_side(-4.4, 6.7, 3.7, 10.5, 7.5, 1.6), "internal": _din_side(.5, 12., 7.5, 15.2, 10.7, 1.6)},
    "M30": {"pitch": 3.5, "external": _din_side(-5., 7.7, 4.7, 12., 9., 1.6), "internal": _din_side(.5, 14., 9., 17.7, 12.7, 1.6)},
}

DIN_RELIEF_TABLE: Dict[str, Dict[str, Dict[str, object]]] = {
    # M2/M2.5: width/depth sind bereits die realen, aus DIN76_THREAD_DATA
    # abgeleiteten Werte (g2/Tiefe) statt grob geschaetzter Platzhalter wie
    # bei den aelteren Eintraegen unten - werden ohnehin von
    # get_din_relief_preset() ueberschrieben, sobald DIN76_THREAD_DATA (siehe
    # oben) einen Eintrag hat.
    "M2": {"external": {"width": 1.4, "depth": 0.35, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 2.2, "depth": 0.10, "transition": "radius", "transition_size": 0.2}},
    "M2.5": {"external": {"width": 1.6, "depth": 0.35, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 2.4, "depth": 0.10, "transition": "radius", "transition_size": 0.2}},
    "M3": {"external": {"width": 0.8, "depth": 0.25, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 0.8, "depth": 0.20, "transition": "radius", "transition_size": 0.2}},
    "M3.5": {"external": {"width": 2.1, "depth": 0.50, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 3.3, "depth": 0.15, "transition": "radius", "transition_size": 0.4}},
    "M4": {"external": {"width": 1.0, "depth": 0.30, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 1.0, "depth": 0.25, "transition": "radius", "transition_size": 0.2}},
    "M5": {"external": {"width": 1.2, "depth": 0.35, "transition": "radius", "transition_size": 0.2}, "internal": {"width": 1.2, "depth": 0.30, "transition": "radius", "transition_size": 0.2}},
    "M6": {"external": {"width": 1.5, "depth": 0.40, "transition": "radius", "transition_size": 0.25}, "internal": {"width": 1.5, "depth": 0.35, "transition": "radius", "transition_size": 0.25}},
    "M7": {"external": {"width": 1.6, "depth": 0.45, "transition": "radius", "transition_size": 0.25}, "internal": {"width": 1.6, "depth": 0.40, "transition": "radius", "transition_size": 0.25}},
    "M8": {"external": {"width": 1.8, "depth": 0.50, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 1.8, "depth": 0.45, "transition": "radius", "transition_size": 0.3}},
    "M9": {"external": {"width": 1.9, "depth": 0.55, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 1.9, "depth": 0.50, "transition": "radius", "transition_size": 0.3}},
    "M10": {"external": {"width": 2.0, "depth": 0.60, "transition": "radius", "transition_size": 0.3}, "internal": {"width": 2.0, "depth": 0.55, "transition": "radius", "transition_size": 0.3}},
    "M11": {"external": {"width": 2.1, "depth": 0.68, "transition": "radius", "transition_size": 0.35}, "internal": {"width": 2.1, "depth": 0.60, "transition": "radius", "transition_size": 0.35}},
    "M12": {"external": {"width": 2.3, "depth": 0.75, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.3, "depth": 0.65, "transition": "radius", "transition_size": 0.4}},
    "M13": {"external": {"width": 2.5, "depth": 0.80, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.5, "depth": 0.70, "transition": "radius", "transition_size": 0.4}},
    "M14": {"external": {"width": 2.6, "depth": 0.85, "transition": "radius", "transition_size": 0.4}, "internal": {"width": 2.6, "depth": 0.75, "transition": "radius", "transition_size": 0.4}},
    "M15": {"external": {"width": 2.8, "depth": 0.92, "transition": "radius", "transition_size": 0.45}, "internal": {"width": 2.8, "depth": 0.82, "transition": "radius", "transition_size": 0.45}},
    "M16": {"external": {"width": 3.0, "depth": 1.00, "transition": "radius", "transition_size": 0.5}, "internal": {"width": 3.0, "depth": 0.90, "transition": "radius", "transition_size": 0.5}},
    "M17": {"external": {"width": 3.1, "depth": 1.05, "transition": "radius", "transition_size": 0.5}, "internal": {"width": 3.1, "depth": 0.95, "transition": "radius", "transition_size": 0.5}},
    "M18": {"external": {"width": 3.3, "depth": 1.12, "transition": "radius", "transition_size": 0.55}, "internal": {"width": 3.3, "depth": 1.00, "transition": "radius", "transition_size": 0.55}},
    "M19": {"external": {"width": 3.4, "depth": 1.18, "transition": "radius", "transition_size": 0.55}, "internal": {"width": 3.4, "depth": 1.05, "transition": "radius", "transition_size": 0.55}},
    "M20": {"external": {"width": 3.6, "depth": 1.25, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.6, "depth": 1.10, "transition": "radius", "transition_size": 0.6}},
    "M21": {"external": {"width": 3.7, "depth": 1.30, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.7, "depth": 1.15, "transition": "radius", "transition_size": 0.6}},
    "M22": {"external": {"width": 3.8, "depth": 1.35, "transition": "radius", "transition_size": 0.6}, "internal": {"width": 3.8, "depth": 1.20, "transition": "radius", "transition_size": 0.6}},
    "M23": {"external": {"width": 4.0, "depth": 1.45, "transition": "radius", "transition_size": 0.65}, "internal": {"width": 4.0, "depth": 1.30, "transition": "radius", "transition_size": 0.65}},
    "M24": {"external": {"width": 4.2, "depth": 1.55, "transition": "radius", "transition_size": 0.65}, "internal": {"width": 4.2, "depth": 1.40, "transition": "radius", "transition_size": 0.65}},
    "M25": {"external": {"width": 4.3, "depth": 1.62, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.3, "depth": 1.46, "transition": "radius", "transition_size": 0.7}},
    "M26": {"external": {"width": 4.4, "depth": 1.68, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.4, "depth": 1.52, "transition": "radius", "transition_size": 0.7}},
    "M27": {"external": {"width": 4.5, "depth": 1.74, "transition": "radius", "transition_size": 0.7}, "internal": {"width": 4.5, "depth": 1.58, "transition": "radius", "transition_size": 0.7}},
    "M28": {"external": {"width": 4.6, "depth": 1.80, "transition": "radius", "transition_size": 0.75}, "internal": {"width": 4.6, "depth": 1.64, "transition": "radius", "transition_size": 0.75}},
    "M29": {"external": {"width": 4.8, "depth": 1.88, "transition": "radius", "transition_size": 0.75}, "internal": {"width": 4.8, "depth": 1.72, "transition": "radius", "transition_size": 0.75}},
    "M30": {"external": {"width": 5.0, "depth": 2.00, "transition": "radius", "transition_size": 0.8}, "internal": {"width": 5.0, "depth": 1.84, "transition": "radius", "transition_size": 0.8}},
}


def relief_thread_sizes() -> list[str]:
    return sorted(DIN_RELIEF_TABLE.keys(), key=lambda item: float(item[1:]) if item[1:].replace(".", "", 1).isdigit() else 999.0)


def validate_din_relief_preset_data(data: Dict[str, object] | None) -> List[str]:
    """Plausibilitaetspruefung fuer einen einzelnen Freistich-Datensatz
    (Breite/Tiefe/Uebergang), analog zu validate_thread_preset_data."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["preset is not a dictionary"]
    width = data.get("width")
    if not isinstance(width, (int, float)) or float(width) <= 0.0:
        errors.append("width must be > 0")
    depth = data.get("depth")
    if not isinstance(depth, (int, float)) or float(depth) <= 0.0:
        errors.append("depth must be > 0")
    transition = str(data.get("transition") or "").strip().lower()
    if transition not in {"radius", "chamfer"}:
        errors.append("transition must be 'radius' or 'chamfer'")
    transition_size = data.get("transition_size")
    if not isinstance(transition_size, (int, float)) or float(transition_size) <= 0.0:
        errors.append("transition_size must be > 0")
    return errors


def get_din_relief_preset(thread_size: str, internal: bool = False) -> Dict[str, object] | None:
    side = "internal" if internal else "external"
    preset = DIN_RELIEF_TABLE.get(str(thread_size or "").strip().upper(), {}).get(side)
    if not preset or validate_din_relief_preset_data(preset):
        return None
    result = dict(preset)
    standard = DIN76_THREAD_DATA.get(str(thread_size or "").strip().upper())
    if standard:
        side_data = dict(standard[side])
        result.update({
            "pitch": float(standard["pitch"]),
            "width": float(side_data["g2"]),
            "bottom_width": float(side_data["g1"]),
            "short_width": float(side_data["short_g2"]),
            "short_bottom_width": float(side_data["short_g1"]),
            "depth": abs(float(side_data["dg_delta"])) / 2.0,
            "diameter_delta": float(side_data["dg_delta"]),
            # g1 is the standardized overlap of the thread into the relief.
            "thread_overlap": float(side_data["short_g1"]),
            "radius": float(side_data["radius"]),
        })
    return result


def get_thread_with_relief(thread_size: str, internal: bool = False) -> Dict[str, object] | None:
    preset = get_din_relief_preset(thread_size, internal=internal)
    if preset is None:
        return None
    preset["thread_size"] = str(thread_size or "").strip().upper()
    preset["internal"] = bool(internal)
    preset["side"] = "internal" if internal else "external"
    return preset
