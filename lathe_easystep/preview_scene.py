from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .model import OpType, Operation


class PreviewLayer(str, Enum):
    WORKPIECE = "workpiece"
    TOOL_PATH = "tool_path"
    AUXILIARY = "auxiliary"


@dataclass(frozen=True)
class PreviewPath:
    primitives: list
    layer: PreviewLayer
    operation: Operation | None = None


@dataclass(frozen=True)
class PreviewScene:
    entries: tuple[PreviewPath, ...]
    active_index: int = -1

    @property
    def paths(self) -> list[list]:
        """Compatibility view in the exact historic drawing order."""
        return [entry.primitives for entry in self.entries]

    def paths_for(self, layer: PreviewLayer) -> list[list]:
        return [entry.primitives for entry in self.entries if entry.layer == layer]

    @property
    def active_entry(self) -> PreviewPath | None:
        if 0 <= self.active_index < len(self.entries):
            return self.entries[self.active_index]
        return None


_WORKPIECE_TYPES = {OpType.CONTOUR, OpType.GROOVE, OpType.KEYWAY}
_TOOL_PATH_TYPES = {OpType.FACE, OpType.THREAD, OpType.ABSPANEN}
_AUXILIARY_ROLES = {"stock", "retract", "worklimit", "chuck_nogo", "contour_rough"}


def _roles(path: Iterable) -> set[str]:
    return {
        str(primitive.get("role"))
        for primitive in path
        if isinstance(primitive, dict) and primitive.get("role")
    }


def scene_from_legacy_paths(
    paths: list[list],
    active_index: int,
    operations: Iterable[Operation] = (),
    active_operation: Operation | None = None,
) -> PreviewScene:
    """Classify the existing flat preview without changing drawing order."""
    operations_by_path = {
        id(op.path): op for op in operations if getattr(op, "path", None)
    }
    entries = []
    for index, path in enumerate(paths):
        operation = operations_by_path.get(id(path))
        if operation is None and index == active_index:
            operation = active_operation
        roles = _roles(path)
        if roles and roles <= _AUXILIARY_ROLES:
            layer = PreviewLayer.AUXILIARY
        elif "feature" in roles:
            layer = PreviewLayer.WORKPIECE
        elif operation is not None and operation.op_type in _WORKPIECE_TYPES:
            layer = PreviewLayer.WORKPIECE
        elif operation is not None and operation.op_type in _TOOL_PATH_TYPES:
            layer = PreviewLayer.TOOL_PATH
        else:
            # DRILL currently renders a tool silhouette, and unknown legacy
            # paths have no reliable motion semantics. Keep both out of the
            # asserted workpiece/tool-path layers until their builders expose
            # richer metadata.
            layer = PreviewLayer.AUXILIARY
        entries.append(PreviewPath(path, layer, operation))
    return PreviewScene(tuple(entries), active_index)


def primitive_strokes(
    primitives: Iterable[dict],
    sample_arc: Callable[[tuple, tuple, tuple, bool], list[tuple]],
) -> list[list[tuple[float, float]]]:
    """Convert every primitive to its own stroke without synthetic links."""
    strokes: list[list[tuple[float, float]]] = []
    for primitive in primitives:
        if not isinstance(primitive, dict):
            continue
        primitive_type = primitive.get("type")
        if primitive_type == "line":
            points = [primitive.get("p1"), primitive.get("p2")]
        elif primitive_type == "arc":
            p1, p2, center = primitive.get("p1"), primitive.get("p2"), primitive.get("c")
            if not p1 or not p2 or not center:
                continue
            try:
                points = sample_arc(tuple(p1), tuple(p2), tuple(center), bool(primitive.get("ccw", True)))
            except Exception:
                continue
        elif primitive_type == "polyline":
            points = primitive.get("points", [])
        else:
            continue
        try:
            stroke = [(float(point[0]), float(point[1])) for point in points if point is not None and len(point) >= 2]
        except Exception:
            continue
        if stroke:
            strokes.append(stroke)
    return strokes
