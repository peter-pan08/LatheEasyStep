"""Reproducible generator cases shared by regression and rs274 checks."""
from copy import deepcopy
from .examples import make_program_settings, example_programs
from .model import Operation, OpType


def thread_relief_case(internal=False, left=False, insufficient=False):
    settings = dict(make_program_settings(), xi=10.0, xri=9.0, zri=2.0,
                    xri_absolute=True, zri_absolute=True,
                    # Naher Wechselpunkt fuer lesbaren Backplot und kurze
                    # native SIM-Laeufe; Produktionsreferenzen bleiben bei
                    # ihren maschinenspezifischen XT/ZT-Werten.
                    xt=30.0, zt=10.0)
    start, end = (-40.0, 0.0) if internal else (0.0, -40.0)
    if insufficient:
        start, end = -18.0, -19.0
    contour = Operation(OpType.CONTOUR, {"name": "thread_relief", "start_x": 12.0,
        "start_z": start, "segments": [{"x": 12.0, "z": end}]})
    finish = Operation(OpType.ABSPANEN, {"contour_name": "thread_relief",
        "side": "inside" if internal else "outside", "mode": "finish",
        "tool": 1, "spindle": 600.0, "feed": .1, "depth_per_pass": .5,
        "undercut_mode": "full", "slice_strategy": "parallel_z"})
    thread = Operation(OpType.THREAD, {"tool": 2, "spindle": 400.0,
        "pitch": 1.5, "major_diameter": 12.0, "length": 20.0,
        "thread_start_z": -30.0 if left else -5.0,
        "hand": "left" if left else "right",
        "orientation": "internal" if internal else "external",
        "relief_mode": "suggest_din_relief", "safe_z": 2.0})
    return [contour, finish, thread], settings


def internal_relief_case():
    """LES-005 ('Innenfreistich ... separat abnehmen'): eigenstaendiger
    `din_relief`-Kontur-Feature (nicht aus einer THREAD-Operation
    abgeleitet, siehe dafuer `thread_relief_case()`) mitten in einer
    Innenkontur, gefolgt von weiterem Bohrungsprofil."""
    settings = dict(make_program_settings(), program_name="Innen_Freistich",
                    xi=10.0, xri=9.0, zri=2.0, xri_absolute=True, zri_absolute=True,
                    xt=30.0, zt=10.0)
    contour = Operation(OpType.CONTOUR, {"name": "innen_freistich", "start_x": 12.0,
        "start_z": -45.0, "segments": [
            {"x": 12.0, "z": -35.0, "x_empty": True, "z_empty": False, "feature": {
                "feature_type": "din_relief", "internal": True, "side": "internal",
                "thread_size": "M12", "orientation": "end"}},
            {"x": 20.0, "z": -35.0, "x_empty": False, "z_empty": True},
            {"x": 20.0, "z": 0.0, "x_empty": True, "z_empty": False},
        ]})
    rough = Operation(OpType.ABSPANEN, {"contour_name": "innen_freistich", "side": "inside",
        "mode": "rough_finish", "slice_strategy": "parallel_z", "tool": 11,
        "spindle": 800.0, "feed": 0.15, "depth_per_pass": 0.5,
        "finish_allow_x": 0.2, "finish_allow_z": 0.1})
    return [contour, rough], settings


def chip_break_case():
    """SICHERHEITSFUND 2026-09-13: reale Maschinenabnahme fuer den Spanbruch-
    Fix. Aussendrehen mit aktiver Vorschub-Unterbrechung (`pause_enabled`) -
    vor dem Fix wurde die lange Schnittstrecke NIE tatsaechlich geschnitten
    (nur eine wirkungslose Verweilzeit), das Programm lief danach so weiter,
    als sei das Material entfernt. Naher Werkzeugwechselpunkt fuer einen
    kurzen, gut beobachtbaren SIM-Lauf."""
    settings = dict(make_program_settings(), program_name="Chip_Break_SIM",
                    xt=30.0, zt=10.0)
    contour = Operation(OpType.CONTOUR, {"name": "chip_break", "start_x": 0.0,
        "start_z": 0.0, "segments": [{"x": 30.0, "z": 0.0}, {"x": 30.0, "z": -20.0}]})
    rough = Operation(OpType.ABSPANEN, {"contour_name": "chip_break", "side": "outside",
        "mode": "rough", "tool": 1, "spindle": 800.0, "feed": 0.15,
        "depth_per_pass": 5.0, "pause_enabled": True, "pause_distance": 5.0,
        "slice_strategy": "parallel_z"})
    return [contour, rough], settings


def chuck_nogo_case():
    """LES-030 ('Maschinenprofile und Futter-Sperrzonen mit Beispielen
    verifizieren'): ein vollstaendiges Programm (Einstich, wie
    `Einstich.ngc`) mit konfigurierter Futter-Sperrzone, die den
    tatsaechlichen Rueckzugsdurchmesser (X80, der zwischenzeitliche
    Sicherheits-X-Wert vor Groove) EINSCHLIESST (X0..90) - die Zone wird
    nur ueber die Z-Seite sicher umgangen (ZRA=2.0 liegt oberhalb der
    Sperrgrenze Z<=-45), nicht trivial durch einen ausserhalb liegenden
    X-Wert. Damit wird die Z-seitige Segment-Clipping-Pruefung
    (`validate_chuck_segment` in `gcode_safety.py`) in einem realen,
    vollstaendigen Programm tatsaechlich ausgewertet statt nur in
    isolierten Unit-Tests."""
    ops, settings = deepcopy(example_programs()["Einstich.ngc"])
    settings.update(
        chuck_no_go_x_min=0.0, chuck_no_go_x_max=90.0, chuck_no_go_z_limit=-45.0,
        program_name="Chuck_NoGo_Demo", xt=30.0, zt=10.0,
    )
    return ops, settings


def css_switch_case():
    """LES-013 ('grafischen Backplot und reale Maschinenabnahme
    dokumentieren'): Plandrehen mit CSS (G96, D-Wort-Drehzahlgrenze) ->
    Bohren mit Festdrehzahl (G97) -> Plandrehen mit anderer CSS-
    Schnittgeschwindigkeit, mit grober Zustellung fuer einen kurzen,
    reproduzierbaren SIM-Lauf (die Produktionsreferenz `CSS_Wechsel.ngc`
    nutzt 0.05mm radiale Zustellung = ~400 Passes, fuer eine reale
    Maschinenabnahme unpraktikabel lang)."""
    settings = dict(make_program_settings(), program_name="CSS_Switch_SIM",
                    xt=30.0, zt=10.0)
    face1 = Operation(OpType.FACE, {
        "mode": 0, "tool": 1, "spindle": 2000.0, "feed": 0.1, "depth_max": 1.0,
        "start_z": 2.0, "end_z": 0.0, "start_x": 40.0, "end_x": 0.0,
        "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
        "coolant": True, "spindle_mode": "css", "cutting_speed": 120.0,
        "spindle_max_rpm": 2500.0,
    }, path=[(40.0, 0.0), (0.0, 0.0)])
    drill = Operation(OpType.DRILL, {"tool": 2, "spindle": 900.0, "feed": 0.1,
        "mode": 0, "safe_z": 2.0, "spindle_mode": "fixed"},
        path=[(0.0, 2.0), (0.0, 0.0), (8.0, 0.0), (8.0, -20.0), (0.0, -23.0)])
    face2 = Operation(OpType.FACE, {
        "mode": 0, "tool": 1, "spindle": 2000.0, "feed": 0.1, "depth_max": 1.0,
        "start_z": 0.0, "end_z": -1.0, "start_x": 40.0, "end_x": 0.0,
        "finish_allow_z": 0.0, "retract": 1.0, "edge_type": 0, "edge_size": 0.0,
        "coolant": True, "spindle_mode": "css", "cutting_speed": 180.0,
        "spindle_max_rpm": 2500.0,
    }, path=[(40.0, -1.0), (0.0, -1.0)])
    return [face1, drill, face2], settings


def same_tool_transition_case(internal=False):
    ops, settings = example_programs()["Innen_Stufe.ngc" if internal else "Kontur_Radius_Fase.ngc"]
    ops[-1].params.update(mode="rough", output_preference="prefer_explicit",
                         spindle_mode="css", cutting_speed=120, spindle_max_rpm=2500)
    finish = deepcopy(ops[-1])
    finish.params.update(mode="finish", cutting_speed=100)
    ops.append(finish)
    return ops, settings
