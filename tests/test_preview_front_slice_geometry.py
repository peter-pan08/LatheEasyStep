from lathe_easystep.model import Operation, OpType
from lathe_easystep.preview_geometry import (
    front_operation_side,
    front_reference_diameter,
    front_slice_profile,
    front_view_scale,
)

# LES-024/LES-034: front_operation_side/front_slice_profile/front_reference_diameter
# wurden aus preview_widget.py (LathePreviewWidget) extrahiert - reine
# Geometrieberechnung ohne QPainter/Widget, jetzt direkt ohne echtes PyQt5
# testbar. Vorher nur indirekt ueber die Schnittansicht des Widgets erreichbar.


def _identity_to_points(path):
    return path


def test_front_operation_side_classifies_each_op_type():
    assert front_operation_side(Operation(OpType.DRILL, {}, [])) == "inside"
    assert front_operation_side(Operation(OpType.BORE, {}, [])) == "inside"
    assert front_operation_side(Operation(OpType.GROOVE, {"lage": 1}, [])) == "inside"
    assert front_operation_side(Operation(OpType.GROOVE, {"lage": 0}, [])) == "outside"
    assert front_operation_side(Operation(OpType.THREAD, {"orientation": 1}, [])) == "inside"
    assert front_operation_side(Operation(OpType.ABSPANEN, {"side": 1}, [])) == "inside"
    assert front_operation_side(Operation(OpType.KEYWAY, {}, [])) is None
    assert front_operation_side(Operation(OpType.FACE, {}, [])) == "outside"


def test_front_slice_profile_classifies_outer_and_inner_hits_separately():
    outer_op = Operation(OpType.ABSPANEN, {"side": 0}, path=[(40.0, 0.0), (30.0, -10.0)])
    inner_op = Operation(OpType.DRILL, {}, path=[(10.0, 0.0), (10.0, -10.0)])

    profile = front_slice_profile(
        front_program={},
        front_operations=[outer_op, inner_op],
        paths=[],
        active_index=None,
        slice_z=-5.0,
        to_points=_identity_to_points,
    )

    assert profile["outer_hits"] == [35.0]
    assert profile["inner_hits"] == [10.0]
    assert profile["outer_fill"] == 35.0
    assert profile["inner_fill"] == 10.0
    assert profile["all_hits"] == [35.0, 10.0]


def test_front_slice_profile_falls_back_to_stock_diameters_without_hits():
    profile = front_slice_profile(
        front_program={"xa": 50.0, "xi": 20.0},
        front_operations=[],
        paths=[],
        active_index=None,
        slice_z=-5.0,
        to_points=_identity_to_points,
    )
    assert profile["outer_fill"] == 50.0
    assert profile["inner_fill"] == 20.0
    assert profile["outer_hits"] == []


def test_front_slice_profile_ignores_keyway_operations():
    """KEYWAY hat keine sinnvolle 'Seite' und keinen zuverlaessigen
    Durchmesser-Treffer ueber den Pfad - wird bewusst uebersprungen (die
    Schnittansicht zeichnet die Keilnut separat ueber ihr eigenes Overlay)."""
    keyway_op = Operation(OpType.KEYWAY, {}, path=[(40.0, 0.0), (34.0, -10.0)])

    profile = front_slice_profile(
        front_program={},
        front_operations=[keyway_op],
        paths=[],
        active_index=None,
        slice_z=-5.0,
        to_points=_identity_to_points,
    )
    assert profile["all_hits"] == []


def test_front_slice_profile_falls_back_to_active_path_when_no_operations_given():
    """Kontur-Eingabe vor dem Hinzufuegen eines Steps: keine Operations-Liste,
    aber ein aktiver Vorschaupfad."""
    paths = [[(40.0, 0.0), (30.0, -10.0)]]
    profile = front_slice_profile(
        front_program={},
        front_operations=[],
        paths=paths,
        active_index=0,
        slice_z=-5.0,
        to_points=_identity_to_points,
    )
    assert profile["outer_hits"] == [35.0]
    assert profile["all_hits"] == [35.0]


def test_front_reference_diameter_prefers_largest_candidate():
    op = Operation(OpType.ABSPANEN, {}, path=[(40.0, 0.0), (30.0, -10.0)])
    diameter = front_reference_diameter(
        front_program={"xa": 45.0},
        front_operations=[op],
        to_points=_identity_to_points,
    )
    assert diameter == 45.0


def test_front_reference_diameter_includes_keyway_expansion_when_cutting_outward():
    keyway_op = Operation(
        OpType.KEYWAY,
        {"start_x_dia": 40.0, "nut_depth": 3.0, "radial_side": 1},
        path=[(40.0, 0.0), (46.0, -10.0)],
    )
    diameter = front_reference_diameter(
        front_program={},
        front_operations=[keyway_op],
        to_points=_identity_to_points,
    )
    assert diameter == 46.0


def test_front_reference_diameter_defaults_to_ten_without_any_candidate():
    diameter = front_reference_diameter(
        front_program={},
        front_operations=[],
        to_points=_identity_to_points,
    )
    assert diameter == 10.0


def test_front_view_scale_fits_the_largest_diameter_into_the_smaller_side():
    # 100mm diameter with 15% margin should exactly fill the shorter side.
    assert front_view_scale(100.0, width=400.0, height=200.0) == 200.0 / (100.0 * 1.15)


def test_front_view_scale_uses_the_limiting_dimension():
    wide = front_view_scale(50.0, width=1000.0, height=100.0)
    tall = front_view_scale(50.0, width=100.0, height=1000.0)
    assert wide == tall == 100.0 / (50.0 * 1.15)


def test_front_view_scale_stays_finite_for_a_zero_diameter():
    assert front_view_scale(0.0, width=100.0, height=100.0) > 0.0
