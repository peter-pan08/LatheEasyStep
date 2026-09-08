#!/usr/bin/env python3
"""Static checks for generated examples; this does not replace rs274/backplot."""
from pathlib import Path
import re


def validate_ngc_file(filepath):
    content = Path(filepath).read_text(encoding="utf-8")
    code = re.sub(r"\([^)]*\)", "", content)
    lines = [re.sub(r"^\s*N\d+\s*", "", line).strip().upper() for line in code.splitlines()]
    code = "\n".join(lines)
    checks, issues = [], []

    def check(condition, message):
        (checks if condition else issues).append(("OK: " if condition else "ERROR: ") + message)

    check(bool(re.search(r"\bT\d+\s+M6\b", code)), "tool change present")
    check(bool(re.search(r"\bS(?:[0-9.]|\[|#)", code)) and bool(re.search(r"\bM[34]\b", code)),
          "spindle speed and direction present")
    # F can be inline or an expression. G76 uses P (pitch), not F.
    check(bool(re.search(r"\bF(?:[0-9.]|\[|#)", code)) or bool(re.search(r"\bG76\b", code)),
          "feed or thread pitch cycle present")
    check(not re.search(r"(?:^|\s)[XYZIJKFSRD][-+]?(?:NAN|INF(?:INITY)?)(?=\s|$)", code),
          "no non-finite numeric words")
    check(bool(re.search(r"\bM5\s+M9\s+M30\b", code)), "program ends with spindle/coolant stop and M30")
    check(bool(re.search(r"\bG91\.1\b", code)), "incremental arc centers explicitly selected")
    check(not any(a == b and re.match(r"G0?1(?:\s|$)", a) for a, b in zip(lines, lines[1:])),
          "no duplicate adjacent linear cuts")
    # Literal D values are valid; they are not a safety or interpreter error.
    subs = re.findall(r"^O<?([A-Z0-9_]+)>?\s+SUB\b", code, re.MULTILINE)
    ends = re.findall(r"^O<?([A-Z0-9_]+)>?\s+ENDSUB\b", code, re.MULTILINE)
    check(subs == ends and len(subs) == len(set(subs)), "subroutine definitions balanced and unique")
    return checks, issues


def main():
    files = sorted((Path(__file__).resolve().parent / "ngc").glob("*.ngc"))
    if not files:
        print("ERROR: No reference NGC files found")
        return 1
    failures = 0
    for path in files:
        checks, issues = validate_ngc_file(path)
        print(f"{path.name}: {len(checks)} checks passed, {len(issues)} issues")
        for issue in issues:
            print("  " + issue)
        failures += len(issues)
    print("Static checks only; LinuxCNC interpreter and machine verification remain separate.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
