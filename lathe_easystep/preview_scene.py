from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .model import OpType, Operation

_LOGGER = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class PreviewDrawItem:
    index: int
    role: str | None
    layer: PreviewLayer | None
    style_key: str


@dataclass(frozen=True)
class FrontViewCircle:
    diameter: float
    style_key: str
    filled: bool = False


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
            except Exception as exc:
                _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "primitive_strokes", exc)
                continue
        elif primitive_type == "polyline":
            points = primitive.get("points", [])
        else:
            continue
        try:
            stroke = [(float(point[0]), float(point[1])) for point in points if point is not None and len(point) >= 2]
        except Exception as exc:
            _LOGGER.debug("[LatheEasyStep] %s: unexpected exception suppressed: %s", "primitive_strokes", exc)
            continue
        if stroke:
            strokes.append(stroke)
    return strokes


def stroke_bounding_rectangle(
    strokes: Iterable[Iterable[tuple[float, float]]],
) -> list[tuple[float, float]]:
    """Return the axis-aligned model-space rectangle enclosing all strokes."""
    points = [point for stroke in strokes for point in stroke]
    if not points:
        return []
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_z = min(point[1] for point in points)
    max_z = max(point[1] for point in points)
    return [
        (min_x, min_z),
        (min_x, max_z),
        (max_x, max_z),
        (max_x, min_z),
    ]


def build_preview_draw_plan(
    paths: list[list], active_index: int | None, scene: PreviewScene | None = None
) -> list[PreviewDrawItem]:
    """Resolve draw order and semantic style without depending on Qt."""
    order = [index for index in range(len(paths)) if index != active_index]
    if active_index is not None and 0 <= active_index < len(paths):
        order.append(active_index)

    special_styles = {
        "stock": "stock",
        "retract": "retract",
        "worklimit": "worklimit",
        "chuck_nogo": "chuck_nogo",
        "contour_rough": "contour_rough",
        "feature": "feature",
        "feature_separate": "feature_separate",
    }
    plan = []
    for index in order:
        path = paths[index]
        if not path:
            continue
        roles = [
            str(item.get("role")) for item in path
            if isinstance(item, dict) and item.get("role")
        ]
        role = roles[0] if roles else None
        try:
            layer = scene.entries[index].layer if scene is not None else None
        except (AttributeError, IndexError, TypeError):
            layer = None
        if role in special_styles:
            style_key = special_styles[role]
        elif index == active_index:
            style_key = "active"
        elif layer == PreviewLayer.WORKPIECE:
            style_key = "workpiece"
        elif layer == PreviewLayer.AUXILIARY:
            style_key = "auxiliary"
        else:
            style_key = "tool_path"
        plan.append(PreviewDrawItem(index, role, layer, style_key))
    return plan


def build_front_view_draw_plan(
    *,
    stock_od: float,
    stock_id: float,
    outer_fill_diameter: float,
    inner_fill_diameter: float,
    outer_hits: list[float],
    inner_hits: list[float],
    active_diameters: list[float],
) -> list[FrontViewCircle]:
    """Resolve the front view's circles (Rohteilkreise, Endkonturfuellung,
    sichtbare Durchmesserringe) and their semantic style without any Qt/
    QPainter dependency. Order matches the original paint code: stock
    outlines, then the filled end-contour donut, then diameter rings
    (outer/inner/active) - the widget still draws the keyway overlay
    between the fill and the rings, since it comes from a separate
    operation list rather than this plan."""
    plan: list[FrontViewCircle] = []
    if stock_od > 1e-6:
        plan.append(FrontViewCircle(stock_od, "stock_od"))
    if stock_id > 1e-6 and stock_id < stock_od:
        plan.append(FrontViewCircle(stock_id, "stock_id"))
    if outer_fill_diameter > 1e-6:
        plan.append(FrontViewCircle(outer_fill_diameter, "end_contour_fill", filled=True))
        if inner_fill_diameter > 1e-6 and inner_fill_diameter < outer_fill_diameter - 1e-6:
            plan.append(FrontViewCircle(inner_fill_diameter, "end_contour_hole", filled=True))
    for diameter in outer_hits:
        plan.append(FrontViewCircle(diameter, "outer_ring"))
    for diameter in inner_hits:
        plan.append(FrontViewCircle(diameter, "inner_ring"))
    for diameter in active_diameters:
        if any(abs(diameter - existing) <= 1e-6 for existing in outer_hits + inner_hits):
            continue
        plan.append(FrontViewCircle(diameter, "active_ring"))
    return plan
