from __future__ import annotations

from typing import Callable, Dict, List

from .model import Operation


def generate_keyway_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require: Callable[[Dict[str, object], List[str], str], None],
    require_positive: Callable[[Dict[str, object], List[str], str], None],
) -> List[str]:
    settings = settings or {}
    p = op.params
    require(p, ["depth_per_pass"], "KEYWAY")
    require_positive(p, ["depth_per_pass"], "KEYWAY")

    raise ValueError(
        "KEYWAY verwendet Makro-Variablen (#...), die im erzeugten G-Code verboten sind."
    )
