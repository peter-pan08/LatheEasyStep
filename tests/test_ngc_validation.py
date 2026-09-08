from pathlib import Path
import re

from validate_ngc import validate_ngc_file


def test_reference_programs_pass_static_checks():
    for path in (Path(__file__).resolve().parents[1] / "ngc").glob("*.ngc"):
        assert validate_ngc_file(path)[1] == [], path.name


def test_checker_rejects_missing_spindle_even_if_comment_mentions_it(tmp_path):
    path = tmp_path / "broken.ngc"
    path.write_text("(G97 S1000 M3)\nG91.1\nT1 M6\nG1 X10 F0.2\nM5\nM9\nM30")
    assert any("spindle speed" in issue for issue in validate_ngc_file(path)[1])


def test_checker_rejects_nonfinite_words(tmp_path):
    path = tmp_path / "broken.ngc"
    path.write_text("G91.1\nT1 M6\nG97 S1000 M3\nG1 Xnan F0.2\nM5\nM9\nM30")
    assert any("non-finite" in issue for issue in validate_ngc_file(path)[1])
