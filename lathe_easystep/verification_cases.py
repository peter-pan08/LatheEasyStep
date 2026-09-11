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


def same_tool_transition_case(internal=False):
    ops, settings = example_programs()["Innen_Stufe.ngc" if internal else "Kontur_Radius_Fase.ngc"]
    ops[-1].params.update(mode="rough", output_preference="prefer_explicit",
                         spindle_mode="css", cutting_speed=120, spindle_max_rpm=2500)
    finish = deepcopy(ops[-1])
    finish.params.update(mode="finish", cutting_speed=100)
    ops.append(finish)
    return ops, settings
