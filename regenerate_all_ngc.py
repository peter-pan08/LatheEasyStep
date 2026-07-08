#!/usr/bin/env python3
"""Regenerate all checked-in NGC example files from the reference programs."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lathe_easystep.examples import example_programs
from lathe_easystep.gcode_program import generate_program_gcode


def main():
    try:
        print("Regenerating NGC example files...")
        print()

        out_dir = os.path.join(os.path.dirname(__file__), "ngc")
        os.makedirs(out_dir, exist_ok=True)

        total_lines = 0
        examples = example_programs()
        for filename, (operations, settings) in examples.items():
            gcode_lines = generate_program_gcode(operations, settings)
            filepath = os.path.join(out_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(gcode_lines))
            print(f"✓ {filename} ({len(gcode_lines)} lines)")
            total_lines += len(gcode_lines)

        print()
        print(f"Total: {total_lines} lines of G-code generated in {len(examples)} files")
        print()
        print("Next step: Run validate_ngc.py to check for issues")
    except Exception as exc:
        print(f"Error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
