"""Generate isolated parser cases; no machine connection or machine approval."""
import argparse
from copy import deepcopy
from pathlib import Path

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.model import Operation, OpType
from lathe_easystep.verification_cases import thread_relief_case, same_tool_transition_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("tests/_local/linuxcnc_matrix"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    profiles = {
        "cylinder": [(12., -30.), (12., 0.)],
        "step": [(12., -30.), (12., -15.), (18., -15.), (18., 0.)],
        "cone": [(12., -30.), (18., 0.)],
    }
    count = 0
    for profile in (*profiles, "radius"):
        for reverse in (False, True):
            for mode in ("rough", "finish", "rough_finish"):
                ops, settings = example_programs()["Innen_Radius.ngc"]
                if profile == "radius":
                    if reverse:
                        ops[0].params.update(start_x=18., start_z=0., segments=[
                            {"x": 18., "z": -15.},
                            {"x": 12., "z": -15., "edge": "radius", "edge_size": 1.},
                            {"x": 12., "z": -30.}])
                    ops[-1].params["mode"] = mode
                else:
                    points = profiles[profile]
                    params = dict(ops[-1].params, mode=mode)
                    params.pop("contour_name")
                    ops = [Operation(OpType.ABSPANEN, params,
                                     list(reversed(points)) if reverse else list(points))]
                name = f"inside_{profile}_{'reverse' if reverse else 'forward'}_{mode}"
                settings["program_name"] = name
                (args.output_dir / (name + ".ngc")).write_text(
                    "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
                count += 1
                if profile in ("cylinder", "cone") and mode == "finish":
                    settings["tools"] = {11: {"radius_mm": .4, "q": 3}}
                    settings["program_name"] = name + "_comp"
                    (args.output_dir / (name + "_comp.ngc")).write_text(
                        "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
                    count += 1
    for strategy in ("parallel_x", "parallel_z"):
        ops, settings = example_programs()["Kontur_Radius_Fase.ngc"]
        ops[-1].params["slice_strategy"] = strategy
        name = f"outside_arc_{strategy}"
        settings["program_name"] = name
        (args.output_dir / (name + ".ngc")).write_text(
            "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
        count += 1
    for filename in ("Planen.ngc", "Abdrehen.ngc", "Innen_Stufe.ngc", "Gewinde.ngc", "Einstich.ngc"):
        ops, settings = example_programs()[filename]
        ops[-1].params.update(spindle_mode="css", cutting_speed=120, spindle_max_rpm=2500)
        name = "css_clearance_" + Path(filename).stem
        settings["program_name"] = name
        (args.output_dir / (name + ".ngc")).write_text(
            "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
        count += 1
    for preference in ("auto", "prefer_explicit"):
        ops, settings = example_programs()["Kontur_Radius_Fase.ngc"]
        ops[-1].params["mode"] = "rough"
        finish = deepcopy(ops[-1])
        finish.params.update(mode="finish", tool=3, output_preference=preference)
        ops.append(finish)
        name = "separate_finish_" + preference
        settings["program_name"] = name
        (args.output_dir / (name + ".ngc")).write_text(
            "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
        count += 1
    for internal in (False, True):
        for left in (False, True):
            ops, settings = thread_relief_case(internal, left)
            name = f"thread_relief_{'inside' if internal else 'outside'}_{'left' if left else 'right'}"
            settings["program_name"] = name
            (args.output_dir / (name + ".ngc")).write_text(
                "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
            count += 1
        ops, settings = same_tool_transition_case(internal)
        name = f"same_tool_{'inside' if internal else 'outside'}"
        settings["program_name"] = name
        (args.output_dir / (name + ".ngc")).write_text(
            "\n".join(generate_program_gcode(ops, settings)), encoding="utf-8")
        count += 1
    print(f"Generated {count} parser cases in {args.output_dir}")


if __name__ == "__main__":
    main()
