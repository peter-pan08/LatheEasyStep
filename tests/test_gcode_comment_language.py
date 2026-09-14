import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lathe_easystep.gcode_utils import gcode_comment

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LES-044 Entscheidung (2026-09-14): G-Code-Kommentare (Werkstattkommentare)
# werden sprachabhaengig wie die UI-Texte. gcode_comment() ist bewusst NICHT
# an translations.TranslationStore gekoppelt (die haengt ueber ui_registry.py
# an qtpy) - der Generator muss ohne PyQt5 importierbar bleiben ("Der
# Generator ist von Qt getrennt"), sonst wuerden regenerate_all_ngc.py und
# alle Generator-Tests ohne Real-Qt-Marker brechen.


def test_known_key_is_translated_per_language():
    de = gcode_comment("operation.face.coolant_suffix", "de")
    en = gcode_comment("operation.face.coolant_suffix", "en")
    assert de == "mit Kuehlung"
    assert en == "with coolant"
    assert de != en


def test_missing_language_falls_back_to_german():
    assert gcode_comment("operation.face.coolant_suffix", None) == "mit Kuehlung"
    assert gcode_comment("operation.face.coolant_suffix", "") == "mit Kuehlung"


def test_unknown_key_returns_the_key_itself_not_a_crash():
    assert gcode_comment("gcode.comment.does_not_exist", "de") == "gcode.comment.does_not_exist"


def test_placeholders_are_substituted():
    text = gcode_comment("operation.groove.groove", "de", z="1.000", width="2.000", tool="T04")
    assert "1.000" in text
    assert "T04" in text


def test_result_is_sanitized_for_gcode_comments():
    """sanitize_gcode_text() transliteriert Umlaute/scharfes S - muss auch
    fuer uebersetzten Text gelten, nicht nur fuer von Hand geschriebene
    Kommentare."""
    text = gcode_comment("operation.face.coolant_suffix", "de")
    text.encode("ascii")  # darf nicht scheitern


def test_gcode_utils_imports_without_pyqt5_installed():
    """Regressions-Wachposten: der von pytest/conftest.py automatisch
    installierte qtpy-Stub wuerde einen echten `from qtpy import ...` in
    der Importkette verdecken. Reproduziert deshalb genau das Szenario, das
    diesen Fehler tatsaechlich gezeigt hat: `regenerate_all_ngc.py` mit dem
    venv-Python direkt ausgefuehrt (kein PyQt5 installiert, kein
    pytest-Stub) - schlug fehl, als gcode_utils.py translations.py
    importierte (haengt ueber ui_registry.py an qtpy)."""
    result = subprocess.run(
        [sys.executable, "-c", "import lathe_easystep.gcode_utils"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
