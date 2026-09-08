"""Run stub and real Qt suites in separate, fresh Python processes."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    for mode in ("stub", "real"):
        print(f"Running {mode} tests", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", f"--qt-mode={mode}", *sys.argv[1:]],
            cwd=root, env=env,
        )
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
