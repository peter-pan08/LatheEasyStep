import re

import pytest

from lathe_easystep.examples import make_program_settings
from lathe_easystep.model import Operation, OpType
from lathe_easystep.gcode_program import generate_program_gcode

# LES-003: "automatisierte Faelle fuer monoton steigende UND fallende
# Z-Konturen sowie Innen-/Aussenbearbeitung pflegen". Die Innen-Variante
# existiert bereits (test_internal_profile_matrix.py). Aussenbearbeitung
# nutzt einen GRUNDSAETZLICH anderen Ausgabepfad (G71/G72-Zyklus statt der
# bewegungsbasierten Innen-Ersatzloesung, siehe LES-003-Hauptbefund) und war
# fuer diese Richtungs-/Modus-Matrix bisher nicht separat abgedeckt.

PROFILES = {
    "cylinder": [(12.0, -30.0), (12.0, 0.0)],
    "step": [(12.0, -30.0), (12.0, -15.0), (18.0, -15.0), (18.0, 0.0)],
    "cone": [(12.0, -30.0), (18.0, 0.0)],
}


@pytest.mark.parametrize("points", PROFILES.values(), ids=PROFILES.keys())
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("mode", ["rough", "finish", "rough_finish"])
def test_external_profiles_stay_within_stock_in_both_contour_directions(points, reverse, mode):
    settings = make_program_settings()
    op = Operation(
        OpType.ABSPANEN,
        {"side": "outside", "mode": mode, "tool": 11, "spindle": 800.0, "feed": 0.15,
         "depth_per_pass": 0.5, "slice_strategy": "parallel_z",
         "finish_allow_x": 0.2, "finish_allow_z": 0.1},
        path=list(reversed(points)) if reverse else points,
    )
    lines = generate_program_gcode([op], settings)
    cuts = [line for line in lines if line.startswith("G1 ")]
    assert cuts
    xs = [float(m.group(1)) for line in cuts if (m := re.search(r"\bX(-?[0-9.]+)", line))]
    # Aussenbearbeitung darf nie ueber den Rohteil-Aussendurchmesser (XA)
    # hinausschneiden - der Aussen-Analog zur Innen-XRI-Grenze.
    assert xs and max(xs) <= settings["xa"] + 1e-6
    if mode == "finish":
        assert not any(line.startswith("(ABSPANEN Rough") for line in lines)
    else:
        assert any(line.startswith("(ABSPANEN Rough") for line in lines)
