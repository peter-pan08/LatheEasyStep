import pytest
from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode


@pytest.mark.parametrize("key,value", [("feed", .00001), ("sweep_feed", .00001),
                                      ("stepA", .00001), ("chip_n", 1.5), ("chip_n", -1)])
def test_invalid_macro_values_block_output(key, value):
    ops, settings = example_programs()["Einstich.ngc"]
    ops[-1].params[key] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)
