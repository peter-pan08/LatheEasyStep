#!/usr/bin/env python3
"""Run the checked-in references through standalone rs274, never a machine.

CLI reference: https://linuxcnc.org/docs/stable/html/code/rs274.html
Uses isolated parameter files and a synthetic tool table; no HAL connection.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interpreter", default="rs274")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).resolve().parent / "ngc")
    parser.add_argument("--report-dir", type=Path, help="Save canonical interpreter output and SHA256 manifest")
    args = parser.parse_args(argv)
    executable = shutil.which(args.interpreter)
    if not executable:
        parser.error(f"LinuxCNC interpreter not found: {args.interpreter}")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be positive")
    files = sorted(args.input_dir.resolve().glob("*.ngc"))
    if not files:
        parser.error("No reference programs found")
    failed = 0
    reports = []
    if args.report_dir:
        args.report_dir.mkdir(parents=True, exist_ok=True)
    for path in files:
        with tempfile.TemporaryDirectory(prefix="lathe-rs274-") as directory:
            scratch = Path(directory)
            tools = sorted(set(re.findall(r"\bT(\d+)\s+M6", path.read_text(encoding="utf-8"))))
            table = scratch / "tools.tbl"
            table.write_text("".join(f"T{int(tool)} P{index} X0 Z0 D0 Q0\n" for index, tool in enumerate(tools, 1)))
            command = [executable, "-g", "-n", "2", "-t", str(table), "-v", str(scratch / "parameters.var"), str(path)]
            try:
                result = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=args.timeout)
                output = result.stdout + result.stderr
                error = result.returncode != 0 or bool(re.search(r"\b(error|failed|unknown g code)\b", output, re.I))
                # Batch rs274 emits PROGRAM_END on a completed program. This
                # prevents accepting an early stop with a zero return code.
                error = error or "PROGRAM_END" not in output
            except subprocess.TimeoutExpired:
                output, error = "Interpreter timeout", True
            print(f"{path.name}: {'FAILED' if error else 'OK'}")
            if args.report_dir:
                (args.report_dir / (path.stem + ".txt")).write_text(output, encoding="utf-8")
            reports.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "ok": not error, "program_end": "PROGRAM_END" in output})
            if error:
                print(output)
                failed += 1
    if args.report_dir:
        (args.report_dir / "manifest.json").write_text(
            json.dumps({"interpreter": executable, "results": reports}, indent=2) + "\n", encoding="utf-8")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
