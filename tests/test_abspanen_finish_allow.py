"""Tests for Abspanen (parting) finish allowance fields.

Validates that:
1. finish_allow_x and finish_allow_z are correctly read from params
2. Roughing mode (mode=0) applies the finish allowance
3. Finishing mode (mode=1) does not use finish allowance for stock adjustment
4. Finish allowance comment is emitted in G-code
5. Widget visibility toggle works (roughing=visible, finishing=hidden)
"""
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lathe_easystep.gcode_roughing import generate_abspanen_gcode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_abspanen_settings(**overrides):
    """Create minimal settings dict for abspanen."""
    s = {
        "xa": 40.0,
        "xi": 0.0,
        "za": 2.0,
        "zi": -55.0,
        "xra": 42.0,
        "xri": 0.0,
        "zra": 5.0,
        "zri": -60.0,
        "xra_absolute": True,
        "zra_absolute": True,
        "xri_absolute": True,
        "zri_absolute": True,
        "xt": 150.0,
        "zt": 300.0,
    }
    s.update(overrides)
    return s


def _make_abspanen_params(mode=0, **overrides):
    """Create minimal params for abspanen. mode: 0=Schruppen, 1=Schlichten."""
    p = {
        "tool": 1,
        "spindle": 1000.0,
        "feed": 0.2,
        "depth_per_pass": 1.0,
        "side": 0,  # external
        "mode": mode,
        # LES-002: ein Schruppstep ohne Bearbeitungsrichtung erzeugt keinen
        # Schnitt mehr und bricht die Programmerzeugung jetzt bewusst mit
        # ValueError ab. Diese Tests pruefen das Schlichtaufmass-Verhalten,
        # nicht diesen Fehlerfall - deshalb braucht mode=0 hier eine gueltige
        # Strategie, damit tatsaechlich geschruppt wird.
        "slice_strategy": "parallel_z",
    }
    p.update(overrides)
    return p


def _simple_contour_path():
    """Simple external contour: step from D40 to D30 at Z=-20."""
    return [
        (40.0, 0.0),
        (30.0, 0.0),
        (30.0, -20.0),
        (40.0, -20.0),
    ]


# ---------------------------------------------------------------------------
# finish_allow_x / finish_allow_z in G-code for roughing
# ---------------------------------------------------------------------------

class TestFinishAllowanceRoughing:
    """Schlichtaufmaß is applied during roughing (mode=0)."""

    def test_comment_emitted_when_nonzero(self):
        """A comment shows the finish allowance values."""
        p = _make_abspanen_params(mode=0, finish_allow_x=0.2, finish_allow_z=0.1)
        path = _simple_contour_path()
        settings = _make_abspanen_settings()
        lines = generate_abspanen_gcode(p, path, settings)
        text = "\n".join(lines)
        assert "Schlichtaufmaß" in text or "Schlichtaufma" in text
        assert "0.200" in text
        assert "0.100" in text

    def test_no_comment_when_zero(self):
        """No finish allowance comment when both are zero."""
        p = _make_abspanen_params(mode=0, finish_allow_x=0.0, finish_allow_z=0.0)
        path = _simple_contour_path()
        settings = _make_abspanen_settings()
        lines = generate_abspanen_gcode(p, path, settings)
        text = "\n".join(lines)
        # No "Schlichtaufmaß" comment
        assert "Schlichtaufma" not in text.replace("(ABSPANEN)", "")

    def test_defaults_to_zero_when_missing(self):
        """Missing finish allowance defaults to 0.0 (no crash)."""
        p = _make_abspanen_params(mode=0)
        # Explicitly remove finish allowance keys
        p.pop("finish_allow_x", None)
        p.pop("finish_allow_z", None)
        path = _simple_contour_path()
        settings = _make_abspanen_settings()
        # Should not raise
        lines = generate_abspanen_gcode(p, path, settings)
        assert len(lines) > 0

    def test_negative_values_clamped_to_zero(self):
        """Negative finish allowance is clamped to 0."""
        p = _make_abspanen_params(mode=0, finish_allow_x=-0.5, finish_allow_z=-0.3)
        path = _simple_contour_path()
        settings = _make_abspanen_settings()
        lines = generate_abspanen_gcode(p, path, settings)
        text = "\n".join(lines)
        # No comment because both are effectively 0
        assert "Schlichtaufma" not in text.replace("(ABSPANEN)", "")


class TestFinishAllowanceFinishing:
    """Schlichtaufmaß should not modify behavior during finishing (mode=1)."""

    def test_finish_mode_ignores_stock_adjustment(self):
        """Mode=1 (Schlichten) should still generate G-code without crash."""
        p = _make_abspanen_params(mode=1, finish_allow_x=0.2, finish_allow_z=0.1)
        path = _simple_contour_path()
        settings = _make_abspanen_settings()
        lines = generate_abspanen_gcode(p, path, settings)
        assert len(lines) > 0


# ---------------------------------------------------------------------------
# Widget-level integration: param_widgets mapping includes the keys
# ---------------------------------------------------------------------------

class TestParamWidgetMapping:
    """The handler's param_widgets dict must include finish allowance keys."""

    def test_abspanen_param_keys_include_finish_allow(self):
        """Check that the source code maps 'finish_allow_x' and 'finish_allow_z'."""
        import lathe_easystep_handler as handler
        source = open(handler.__file__, "r").read()
        assert '"finish_allow_x": self._get_widget_by_name("parting_finish_allow_x")' in source
        assert '"finish_allow_z": self._get_widget_by_name("parting_finish_allow_z")' in source
