import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.checks import validate_program_setup
from lathe_easystep.contour_logic import build_contour_variants
from lathe_easystep.model import OpType, Operation


def _relief_warnings(warnings):
    return [w for w in warnings if "Freistich" in w]


def _relief_segment(z, orientation="end"):
    return {
        "mode": "z", "x": 0.0, "z": z, "x_empty": True, "z_empty": False,
        "feature": {
            "feature_type": "din_relief", "internal": False, "norm": "DIN 76-A",
            "orientation": orientation, "side": "external", "thread_size": "M30",
        },
    }


def _internal_relief_segment(z, orientation="end", size="M12"):
    return {
        "mode": "z", "x": 0.0, "z": z, "x_empty": True, "z_empty": False,
        "feature": {
            "feature_type": "din_relief", "internal": True, "norm": "DIN 76-C",
            "orientation": orientation, "side": "internal", "thread_size": size,
        },
    }


def test_relief_mid_contour_produces_geometry():
    """Realer Bugreport (LES-010/LES-011): ein M30-Aussengewinde-Freistich bei
    Z=-35, gefolgt von weiterem Wellenprofil bis Z=-60, erzeugte frueher KEINE
    Freistich-Geometrie - build_contour_variants() erkannte das Feature nur am
    absoluten Rand der GESAMTEN Kontur, nicht am Ende des Gewindes selbst
    (mitten in der Kontur). Jetzt wird der Freistich an der korrekten Stelle
    in die Kontur-Primitive gespleisst, unabhaengig von der Segmentposition."""
    segments = [
        {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True},
        _relief_segment(-35.0, orientation="end"),
        {"mode": "x", "x": 40.0, "z": -35.0, "x_empty": False, "z_empty": True},
        {"mode": "z", "x": 0.0, "z": -60.0, "x_empty": True, "z_empty": False},
    ]
    params = {"start_x": 27.0, "start_z": 0.0, "coord_mode": "absolute", "segments": segments}
    variants = build_contour_variants(params)
    relief_prims = [p for p in variants["finish_primitives"] if p.get("feature_type") == "din_relief"]
    assert len(relief_prims) == 3
    # Freistich muss VOR dem "weiteren Wellenprofil" (Segment zu X40) liegen,
    # nicht danach oder gar nicht.
    finish_prims = variants["finish_primitives"]
    relief_idx = next(i for i, p in enumerate(finish_prims) if p.get("feature_type") == "din_relief")
    profile_continuation_idx = next(
        i for i, p in enumerate(finish_prims) if p.get("p2") == [40.0, -35.0]
    )
    assert relief_idx < profile_continuation_idx
    # rough_primitives (fuer Hinterschnitt-Modus "ignore"/"finish_only") darf
    # den Freistich weiterhin NICHT enthalten.
    assert all(p.get("feature_type") != "din_relief" for p in variants["rough_primitives"])

    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []


def test_relief_mid_contour_produces_geometry_for_internal_side():
    """LES-005 ('Innenfreistich nach Umsetzung von LES-010/LES-011 separat
    abnehmen'): bisher hatte der eigenstaendige `din_relief`-Kontur-Feature
    (nicht das automatisch aus einer THREAD-Operation abgeleitete, siehe
    LES-037) keine Testabdeckung fuer die Innenseite mitten in einer
    Bohrungskontur - nur externe Faelle waren hier automatisiert geprueft.
    Die Geometrie in `_build_relief_primitives()` war laut Code-Kommentar
    bereits generisch (haengt nur von `internal` ab, keine separate
    Innen-Formel), dieser Test schliesst die fehlende Absicherung."""
    segments = [
        {"mode": "x", "x": 12.0, "z": 0.0, "x_empty": False, "z_empty": True},
        _internal_relief_segment(-35.0, orientation="end"),
        {"mode": "x", "x": 20.0, "z": -35.0, "x_empty": False, "z_empty": True},
        {"mode": "z", "x": 0.0, "z": -60.0, "x_empty": True, "z_empty": False},
    ]
    params = {"start_x": 10.0, "start_z": 0.0, "coord_mode": "absolute", "segments": segments}
    variants = build_contour_variants(params)
    relief_prims = [p for p in variants["finish_primitives"] if p.get("feature_type") == "din_relief"]
    assert len(relief_prims) == 3
    # Innenfreistich muss zu GROESSEREM X gehen (Material aus der Bohrungs-
    # wand entfernt, Durchmesser waechst) - genau umgekehrt zum Aussenfall
    # (kleineres X). Alle Freistich-Primitive muessen X >= Anfangs-X haben.
    assert all(p["p1"][0] >= 12.0 - 1e-9 and p["p2"][0] >= 12.0 - 1e-9 for p in relief_prims)
    assert any(p["p1"][0] > 12.0 + 1e-9 or p["p2"][0] > 12.0 + 1e-9 for p in relief_prims)
    # Freistich muss VOR dem weiteren Bohrungsprofil liegen, nicht danach.
    finish_prims = variants["finish_primitives"]
    relief_idx = next(i for i, p in enumerate(finish_prims) if p.get("feature_type") == "din_relief")
    profile_continuation_idx = next(
        i for i, p in enumerate(finish_prims) if p.get("p2") == [20.0, -35.0]
    )
    assert relief_idx < profile_continuation_idx
    assert all(p.get("feature_type") != "din_relief" for p in variants["rough_primitives"])

    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "innenbohrung", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []


def test_relief_at_actual_contour_end_still_works():
    segments = [
        {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True},
        _relief_segment(-35.0, orientation="end"),
    ]
    params = {"start_x": 27.0, "start_z": 0.0, "coord_mode": "absolute", "segments": segments}
    variants = build_contour_variants(params)
    assert any(p.get("feature_type") == "din_relief" for p in variants["finish_primitives"])
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []


def test_relief_at_actual_contour_start_still_works():
    segments = [_relief_segment(-2.0, orientation="start"), {"mode": "x", "x": 30.0, "z": 0.0, "x_empty": False, "z_empty": True}]
    params = {"start_x": 27.0, "start_z": 0.0, "coord_mode": "absolute", "segments": segments}
    variants = build_contour_variants(params)
    assert any(p.get("feature_type") == "din_relief" for p in variants["finish_primitives"])
    ops = [
        Operation(OpType.PROGRAM_HEADER, {}),
        Operation(OpType.CONTOUR, {"name": "abdrehen", "segments": segments}),
    ]
    assert _relief_warnings(validate_program_setup(ops, {})) == []


def test_relief_on_first_of_several_mid_segments():
    """Kontrollfall: ein Freistich auf dem ALLERERSTEN Segment (idx=0) mit
    orientation='end' - vorher ebenfalls durch die harte idx-Schranke
    ausgeschlossen (nur idx==len(segments)-1 war fuer 'end' erlaubt)."""
    segments = [
        _relief_segment(-5.0, orientation="end"),
        {"mode": "x", "x": 40.0, "z": -5.0, "x_empty": False, "z_empty": True},
        {"mode": "z", "x": 0.0, "z": -60.0, "x_empty": True, "z_empty": False},
    ]
    params = {"start_x": 30.0, "start_z": 0.0, "coord_mode": "absolute", "segments": segments}
    variants = build_contour_variants(params)
    assert any(p.get("feature_type") == "din_relief" for p in variants["finish_primitives"])
