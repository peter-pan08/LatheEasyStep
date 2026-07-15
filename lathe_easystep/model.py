from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List


class OpType:
    PROGRAM_HEADER = "program_header"
    FACE = "face"
    CONTOUR = "contour"
    TURN = "turn"
    BORE = "bore"
    THREAD = "thread"
    GROOVE = "groove"
    DRILL = "drill"
    KEYWAY = "keyway"
    ABSPANEN = "abspanen"


@dataclass
class Operation:
    op_type: str
    params: Dict[str, object]
    path: list = field(default_factory=list)


def _default_geometry_builders() -> Dict[str, Callable]:
    from .preview_geometry import (
        build_abspanen_path,
        build_contour_path,
        build_drill_path,
        build_face_path,
        build_groove_preview_path,
        build_keyway_path,
        build_thread_path,
    )

    return {
        OpType.FACE: build_face_path,
        OpType.CONTOUR: build_contour_path,
        OpType.THREAD: build_thread_path,
        OpType.GROOVE: build_groove_preview_path,
        OpType.DRILL: build_drill_path,
        OpType.KEYWAY: build_keyway_path,
        OpType.ABSPANEN: build_abspanen_path,
    }


class ProgramModel:
    def __init__(
        self,
        *,
        geometry_builders: Dict[str, Callable] | None = None,
        gcode_generator: Callable[[List[Operation], Dict[str, object]], List[str]] | None = None,
    ):
        self.operations: List[Operation] = []
        self.spindle_speed_max: float = 0.0
        self.program_settings: Dict[str, object] = {"emit_line_numbers": False}
        self._geometry_builders = geometry_builders
        self._gcode_generator = gcode_generator

    def add_operation(self, op: Operation):
        self.operations.append(op)

    def remove_operation(self, index: int):
        if 0 <= index < len(self.operations):
            del self.operations[index]

    def move_up(self, index: int):
        if 1 <= index < len(self.operations):
            self.operations[index - 1], self.operations[index] = \
                self.operations[index], self.operations[index - 1]

    def move_down(self, index: int):
        if 0 <= index < len(self.operations) - 1:
            self.operations[index + 1], self.operations[index] = \
                self.operations[index], self.operations[index + 1]

    def update_geometry(self, op: Operation):
        builders = self._geometry_builders or _default_geometry_builders()
        builder = builders.get(op.op_type)
        if not builder:
            op.path = []
            return

        try:
            argc = builder.__code__.co_argcount
        except Exception:
            argc = 1

        if argc >= 2:
            op.path = builder(op.params, self.program_settings)
        else:
            # Frueher wurde hier der bisherige op.path als Snapshot in
            # op.params["path"] eingefroren (write-once: nur wenn der Key noch
            # fehlte). Da dieser Snapshot nie wieder aktualisiert wurde,
            # driftete er bei jeder spaeteren Parameteraenderung von der
            # tatsaechlichen Geometrie weg und wurde als solcher mitgespeichert
            # (siehe reale Step-Datei mit widerspruechlichem Aussen-/Innen-Pfad
            # in params vs. Operation.path). Geometrie wird jetzt ausschliesslich
            # ueber op.path gefuehrt; params["path"] wird nicht mehr geschrieben.
            op.path = builder(op.params)

    def generate_gcode(self) -> List[str]:
        generator = self._gcode_generator
        if generator is None:
            try:
                from .gcode_program import generate_program_gcode
            except Exception:
                generate_program_gcode = None
            generator = generate_program_gcode

        if generator:
            return generator(self.operations, self.program_settings or {})

        return ["%", "(G-Code generation failed - slicer module not found)", "M30", "%"]
