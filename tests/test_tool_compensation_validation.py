import pytest
from lathe_easystep.gcode_safety import nose_compensation_command


@pytest.mark.parametrize("q", [-1, 10, 3.5, "bad", "", True])
def test_invalid_explicit_orientation_is_rejected(q):
    with pytest.raises(ValueError):
        nose_compensation_command({"radius_mm": .4, "q": q}, False)


@pytest.mark.parametrize("radius", [-.4, .000001, 1e308])
def test_invalid_or_unrepresentable_radius_is_rejected(radius):
    with pytest.raises(ValueError):
        nose_compensation_command({"radius_mm": radius, "q": 3}, True)


@pytest.mark.parametrize("external", [False, True])
def test_legacy_numeric_strings_preserve_compensation(external):
    command = nose_compensation_command({"radius_mm": "0.4", "q": "3.0"}, external)
    assert command == f"{'G42.1' if external else 'G41.1'} D0.8000 L3"
