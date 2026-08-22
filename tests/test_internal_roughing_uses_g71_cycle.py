import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.examples import make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_roughing import _resolve_roughing_stock_x
from lathe_easystep.gcode_utils import is_monotonic_z, is_monotonic_z_decreasing, is_monotonic_z_increasing
from lathe_easystep.model import OpType, Operation

# Reale Innenkontur (Nutzer-Testprogramm "ausdrehen"): vom tiefsten Punkt
# (Bohrungsgrund) zur Bohrungsoeffnung definiert - Z UND X steigen monoton
# ueber den gesamten Pfad.
_BORE_TO_OPENING_PATH = [
    (10.0, -44.0),
    (11.4, -44.0),
    (12.0, -43.4),
    (12.0, -10.5),
    (13.0, -10.0),
    (16.0, -10.0),
    (16.0, -1.0),
    (18.0, 0.0),
    (19.2, 0.0),
]


def _internal_rough_op(path, **overrides):
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 9.3, "xri_absolute": True})
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
            **overrides,
        },
        path=path,
    )
    return [Operation(OpType.PROGRAM_HEADER, {}), op], settings


def test_is_monotonic_z_accepts_both_directions():
    increasing = [(0.0, -10.0), (1.0, -5.0), (2.0, 0.0)]
    decreasing = [(0.0, 0.0), (1.0, -5.0), (2.0, -10.0)]
    non_monotonic = [(0.0, -10.0), (1.0, 0.0), (2.0, -5.0)]
    assert is_monotonic_z_increasing(increasing) is True
    assert is_monotonic_z_decreasing(increasing) is False
    assert is_monotonic_z(increasing) is True
    assert is_monotonic_z(decreasing) is True
    assert is_monotonic_z(non_monotonic) is False


def test_internal_roughing_never_uses_g71_g72_cycle():
    """WICHTIG - Erkenntnis aus dieser Session: G71/G72 wurden real gegen den
    LinuxCNC-Interpreter getestet (Quelle: /home/adm1n/linuxcnc-src,
    interp_g7x.cc, Version 2.10.0~pre1 - identisch zur installierten
    LinuxCNC-Version). Fuer Innenkonturen erzeugt der Zyklus dort NUR EINEN
    durchgehenden Schnitt statt der erwarteten Treppenstufen-Schrupppaesse
    (empirisch bestaetigt mit rs274, sowohl fuer diese reale Kontur als auch
    fuer einen trivialen linearen Innenkegel) - waehrend derselbe Zyklus bei
    identisch aufgebauten Aussenkonturen korrekt mehrfach zustellt. Das ist
    KEIN Bug dieses Generators, sondern eine bestaetigte Einschraenkung der
    G7x-Taschenausraeumlogik dieser LinuxCNC-Version fuer Innenbearbeitung.
    G71/G72 duerfen deshalb nur noch fuer Aussenbearbeitung (external=True)
    gewaehlt werden; Innenbearbeitung nutzt immer die bewegungsbasierte
    Ersatzloesung (siehe LES-003 in TODO.md fuer den noch offenen,
    eigenstaendigen Bug in dieser Ersatzloesung selbst)."""
    for path in (_BORE_TO_OPENING_PATH, list(reversed(_BORE_TO_OPENING_PATH))):
        operations, settings = _internal_rough_op(path)
        lines = generate_program_gcode(operations, settings)
        assert not any(line.startswith(("G71 ", "G72 ")) for line in lines)
        text = "\n".join(lines)
        assert "Fallback-Grund: Innenbearbeitung - G71/G72 fuer diese LinuxCNC-Version nicht zuverlaessig" in text


def test_external_roughing_still_uses_g71_cycle():
    """Kontrollfall: Aussenbearbeitung ist von der Innen-spezifischen Sperre
    nicht betroffen und nutzt weiterhin den (dort real bestaetigt
    funktionierenden) G71-Zyklus."""
    settings = make_program_settings()
    op = Operation(
        OpType.ABSPANEN,
        {
            "tool": 1, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "outside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
        },
        path=[(27.0, 0.0), (30.0, -35.0), (50.0, -60.0)],
    )
    lines = generate_program_gcode([Operation(OpType.PROGRAM_HEADER, {}), op], settings)
    assert any(line.startswith("G71 ") for line in lines)


def test_resolve_roughing_stock_x_uses_drilled_diameter_when_xi_unset():
    """Realer Bugreport: Bei Vollzylinder-Rohteil (kein XI im Programmkopf
    gesetzt, xi=0.0 - die Bohrung entsteht erst durch einen vorangehenden
    Bohren-Step) fiel _resolve_roughing_stock_x() auf den kleinsten X-Wert
    der ZIELKONTUR selbst zurueck (hier 10.0), statt den tatsaechlich
    gebohrten Durchmesser (hier 8.0) zu verwenden. Direkter Unit-Test der
    Stock-X-Aufloesung, unabhaengig von der (siehe LES-003) noch offenen
    Frage, ob die bewegungsbasierte Ersatzloesung diesen Wert fuer JEDE
    Kontur in echte Mehrfachpaesse umsetzt."""
    settings = {"xi": 0.0, "_last_drill_diameter": 8.0}
    assert _resolve_roughing_stock_x(settings, _BORE_TO_OPENING_PATH, external=False) == 8.0


def test_resolve_roughing_stock_x_ignores_drilled_diameter_larger_than_target():
    """Kontrollfall: ein gebohrter Durchmesser, der bereits (fehlerhaft)
    groesser als die Zielkontur waere, darf nicht blind uebernommen werden -
    Fallback bleibt der bisherige, sichere kleinste Konturwert."""
    settings = {"xi": 0.0, "_last_drill_diameter": 15.0}
    assert _resolve_roughing_stock_x(settings, _BORE_TO_OPENING_PATH, external=False) == 10.0


def test_internal_roughing_with_real_bore_contour_produces_even_stepped_passes():
    """Realer Bugreport ('keine wirkliche Abspanaufgabe generiert'): mit
    korrektem stock_x (siehe Test oben, Bohrdurchmesser statt Konturwert) UND
    der "Materialreichweite"-Baenderung in rough_turn_parallel_x() (statt
    eines hauchduennen Fensters direkt an x_cut) erzeugt diese reale
    Innenkontur (flache Anfahrt, Diagonale, lange senkrechte Bohrungswand,
    Radien) jetzt fuer jedes X-Band bis zur Kontur-Oeffnung einen eigenen,
    gleichmaessig zugestellten Schnitt - nicht mehr einen einzelnen
    ~33mm-Schnitt in einem Band und "no cut region" in den uebrigen. Die
    letzten drei Baender (X17-19.2) melden korrekt "no cut region": dort
    macht die Kontur (16,-1)->(18,0)->(19.2,0) einen sehr kurzen, steilen
    Uebergang zur Bohrungsoeffnung, der geometrisch keine eigene Zustellung
    mehr benoetigt (bereits durch Pass 9 miterfasst)."""
    settings = make_program_settings()
    settings.update({"xi": 0.0, "xri": 6.0, "xri_absolute": True})
    drill = Operation(
        OpType.DRILL,
        {"tool": 10, "spindle": 600.0, "feed": 0.12, "mode": 0, "safe_z": 2.0, "diameter": 8.0},
        path=[(0.0, 2.0), (0.0, -45.0)],
    )
    rough = Operation(
        OpType.ABSPANEN,
        {
            "tool": 11, "spindle": 1200.0, "feed": 0.15, "depth_per_pass": 1.0,
            "side": "inside", "mode": "rough", "slice_strategy": "parallel_z",
            "finish_allow_x": 0.1, "finish_allow_z": 0.03,
        },
        path=_BORE_TO_OPENING_PATH,
    )
    operations = [Operation(OpType.PROGRAM_HEADER, {}), drill, rough]
    lines = generate_program_gcode(operations, settings)
    text = "\n".join(lines)
    # Passes 1-9 (X8 bis X17) schneiden jeweils einzeln und gleichmaessig -
    # keiner davon darf mehr fehlen oder als "no cut region" ausfallen.
    for pass_i in range(1, 10):
        assert f"(Pass {pass_i}: X-band [" in text
    # Kein einzelner Riesenschnitt mehr, der die gesamte Bohrungswand
    # (Z-44 bis Z-10) in einem Pass zusammenfasst.
    assert "Z-44.000 F0.150\nG1 X13.000" not in text
    # Die letzten Baender bis zur Oeffnung liefern konsistent "no cut region"
    # (nicht mehr eine leere "X-band"-Kopfzeile ohne folgenden Schnitt).
    assert "(Pass 10: no cut region in band X[17.000,18.000])" in text
    assert "(Pass 11: no cut region in band X[18.000,19.000])" in text
    assert "(Pass 12: no cut region in band X[19.000,19.200])" in text
