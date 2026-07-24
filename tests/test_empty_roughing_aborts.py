import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import OpType, Operation

# LES-002: ein Schruppstep (mode=rough oder rough_finish), der keinen
# einzigen echten Schnittbefehl erzeugt, darf nicht als scheinbar gueltiges,
# aber leeres Programm durchgehen - das war zuvor bestenfalls ein Kommentar
# im G-Code. generate_abspanen_gcode() bricht jetzt mit ValueError ab.

_PATH = [(20.0, 0.0), (15.0, -5.0), (10.0, -10.0)]


def _abspanen(mode, side="outside", **overrides):
    settings = make_program_settings()
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": side, "mode": mode, **overrides,
        },
        path=_PATH,
    )
    return [Operation(OpType.PROGRAM_HEADER, {}), op], settings


def test_external_rough_without_strategy_raises():
    operations, settings = _abspanen("rough", side="outside")
    with pytest.raises(ValueError, match="keinen einzigen Schnitt"):
        generate_program_gcode(operations, settings)


def test_internal_rough_without_strategy_raises():
    operations, settings = _abspanen("rough", side="inside")
    settings.update({"xri": 5.0, "xri_absolute": True})
    with pytest.raises(ValueError, match="keinen einzigen Schnitt"):
        generate_program_gcode(operations, settings)


def test_rough_finish_without_strategy_raises():
    operations, settings = _abspanen("rough_finish", side="outside")
    with pytest.raises(ValueError, match="keinen einzigen Schnitt"):
        generate_program_gcode(operations, settings)


def test_rough_with_valid_strategy_does_not_raise():
    operations, settings = _abspanen("rough", side="outside", slice_strategy="parallel_z")
    lines = generate_program_gcode(operations, settings)
    assert any(line.startswith("G1 ") for line in lines)


def test_finish_only_without_rough_cut_is_still_allowed():
    """Ein reiner Schlichtstep darf weiterhin ohne eigenen Schruppschnitt
    generiert werden - er ist per Definition ein Einzelschnitt und schruppt
    bewusst nicht (siehe mode=finish darf nie erneut schruppen)."""
    operations, settings = _abspanen("finish", side="outside")
    lines = generate_program_gcode(operations, settings)
    assert any("Schlichtschnitt Kontur" in line for line in lines)
