from __future__ import annotations

from typing import Dict, List, Tuple

from .model import OpType, Operation


def make_program_settings() -> Dict[str, object]:
    return {
        "unit": "mm",
        "emit_line_numbers": False,
        "xa": 40.0,
        "xi": 0.0,
        "za": 0.0,
        "zi": -55.0,
        "xra": 40.0,
        "xri": 0.0,
        "zra": 2.0,
        "zri": -60.0,
        "xt": 150.0,
        "zt": 300.0,
        "xra_absolute": False,
        "xri_absolute": False,
        "zra_absolute": False,
        "zri_absolute": False,
    }


def example_programs() -> Dict[str, Tuple[List[Operation], Dict[str, object]]]:
    examples: Dict[str, Tuple[List[Operation], Dict[str, object]]] = {}

    settings = make_program_settings()
    settings["program_name"] = "Abdrehen"
    examples["Abdrehen.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Abdrehen"}),
            Operation(
                OpType.CONTOUR,
                {"name": "main_contour"},
                path=[(0.0, 0.0), (20.0, 0.0), (25.0, -5.0), (25.0, -10.025), (39.985, -54.980), (40.0, -55.0)],
            ),
            Operation(
                OpType.ABSPANEN,
                {
                    "mode": 0,
                    "tool": 1,
                    "spindle": 1300.0,
                    "feed": 0.15,
                    "depth_per_pass": 0.5,
                    "slice_strategy": 1,
                    "pause_enabled": False,
                    "pause_distance": 0.0,
                    "contour_name": "main_contour",
                },
            ),
        ],
        dict(settings),
    )

    settings = make_program_settings()
    settings["program_name"] = "Planen"
    examples["Planen.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Planen"}),
            Operation(
                OpType.FACE,
                {
                    "mode": 0,
                    "tool": 1,
                    "spindle": 2000.0,
                    "feed": 0.1,
                    "depth_max": 0.05,
                    "start_z": 2.0,
                    "end_z": 0.0,
                    "start_x": 40.0,
                    "end_x": 0.0,
                    "finish_allow_z": 0.0,
                    "retract": 1.0,
                    "edge_type": 0,
                    "edge_size": 0.0,
                    "coolant": True,
                    "comment": "Gesicht planen",
                },
                path=[(40.0, 0.0), (0.0, 0.0)],
            ),
        ],
        dict(settings),
    )

    settings = make_program_settings()
    settings["program_name"] = "Bohren"
    examples["Bohren.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Bohren"}),
            Operation(
                OpType.DRILL,
                {"tool": 7, "spindle": 1500.0, "feed": 0.1, "mode": 0, "safe_z": 2.0, "comment": "Loch bohren"},
                path=[(0.0, 2.0), (0.0, 0.0), (8.0, 0.0), (8.0, -27.0), (0.0, -30.0)],
            ),
        ],
        dict(settings),
    )

    settings = make_program_settings()
    settings["program_name"] = "Gewinde"
    examples["Gewinde.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Gewinde"}),
            Operation(
                OpType.THREAD,
                {
                    "tool": 3,
                    "spindle": 500.0,
                    "pitch": 1.5,
                    "length": 30.0,
                    "major_diameter": 10.0,
                    "comment": "Gewinde schneiden",
                },
                path=[(10.0, 0.0), (10.0, -30.0)],
            ),
        ],
        dict(settings),
    )

    settings = make_program_settings()
    settings["program_name"] = "Einstich"
    examples["Einstich.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Einstich"}),
            Operation(
                OpType.GROOVE,
                {
                    "tool": 5,
                    "spindle": 800.0,
                    "feed": 0.05,
                    "safe_z": 2.0,
                    "mode": 0,
                    "lage": 0,
                    "diameter": 30.0,
                    "z": -25.0,
                    "width": 2.0,
                    "depth": 2.0,
                    "depth_per_pass": 1.0,
                    "comment": "Einstich",
                },
                path=[(30.0, -26.0), (26.0, -26.0), (26.0, -24.0), (30.0, -24.0)],
            ),
        ],
        dict(settings),
    )

    settings = make_program_settings()
    settings["program_name"] = "Kontur_Radius_Fase"
    examples["Kontur_Radius_Fase.ngc"] = (
        [
            Operation(OpType.PROGRAM_HEADER, {"program_name": "Kontur_Radius_Fase"}),
            Operation(
                OpType.CONTOUR,
                {"name": "radius_chamfer"},
                path=[
                    {"type": "line", "p1": (40.0, 0.0), "p2": (32.0, -8.0)},
                    {"type": "arc", "p1": (32.0, -8.0), "p2": (26.0, -16.0), "c": (26.0, -8.0), "ccw": False},
                    {"type": "line", "p1": (26.0, -16.0), "p2": (20.0, -28.0)},
                ],
            ),
            Operation(
                OpType.ABSPANEN,
                {
                    "mode": 2,
                    "tool": 2,
                    "spindle": 1100.0,
                    "feed": 0.18,
                    "depth_per_pass": 0.75,
                    "slice_strategy": "parallel_z",
                    "contour_name": "radius_chamfer",
                },
            ),
        ],
        dict(settings),
    )
    return examples
