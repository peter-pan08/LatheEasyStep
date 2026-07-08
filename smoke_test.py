#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    run(["pytest", "-q"])
    run(["python3", "regenerate_all_ngc.py"])
    expected = {
        "Abdrehen.ngc",
        "Bohren.ngc",
        "Einstich.ngc",
        "Gewinde.ngc",
        "Kontur_Radius_Fase.ngc",
        "Planen.ngc",
    }
    ngc_dir = os.path.join(ROOT, "ngc")
    existing = {name for name in os.listdir(ngc_dir) if name.endswith(".ngc")}
    missing = sorted(expected - existing)
    if missing:
        print("Missing generated files:", ", ".join(missing), file=sys.stderr)
        return 1
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
