"""Finished face profile, shared by preview and G70/G72 output.

X coordinates and centers are diameters; geometric edge_size is a radius.
The supported edge is the outside corner at start_x, traversed towards end_x.
"""
from .numeric import finite_float
from .gcode_utils import resolve_enum_index

FACE_EDGE_TYPES = {"none": 0, "chamfer": 1, "radius": 2}


def face_primitives(start_x, end_x, end_z, edge_type=0, edge_size=0.0):
    sx = finite_float(start_x, "start_x")
    ex = finite_float(end_x, "end_x")
    z = finite_float(end_z, "end_z")
    edge = resolve_enum_index(edge_type, FACE_EDGE_TYPES, default=-1)
    size = finite_float(edge_size, "edge_size")
    if edge not in (0, 1, 2):
        raise ValueError("edge_type ist ungueltig.")
    if edge and (size <= 0 or sx <= ex or 2 * size > sx - ex):
        raise ValueError("edge_size muss > 0 sein und in die aeussere Planflaeche passen.")
    result = []
    start = (sx, z)
    if edge:
        start = (sx, z - size)
        tangent = (sx - 2 * size, z)
        if edge == 1:
            result.append({"type": "line", "p1": start, "p2": tangent})
        else:
            # In G18 (Z horizontal, X vertical) outside -> face is clockwise.
            result.append({"type": "arc", "p1": start, "p2": tangent,
                           "c": (sx - 2 * size, z - size), "ccw": False})
        start = tangent
    if start != (ex, z) or not result:
        result.append({"type": "line", "p1": start, "p2": (ex, z)})
    return result
