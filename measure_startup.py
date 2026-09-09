"""Measure isolated real-Qt UI construction, not HAL or full QTVCP startup.

Each repetition runs in a fresh process. qtvcp.Action is deliberately
isolated; this utility never connects to a machine or loads user settings.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time


def sample():
    import types
    started = time.perf_counter()
    times = {}
    def mark(name):
        nonlocal started
        now = time.perf_counter()
        times[name] = now - started
        started = now
    from PyQt5 import QtWidgets, uic
    app = QtWidgets.QApplication([])
    core = types.ModuleType("qtvcp.core")
    core.Action = type("Action", (), {})
    sys.modules["qtvcp"] = types.ModuleType("qtvcp")
    sys.modules["qtvcp.core"] = core
    import lathe_easystep_handler
    from lathe_easystep.ui_split import load_split_tab_uis
    from lathe_easystep.ui_advanced import ensure_advanced_widgets
    from lathe_easystep.ui_static import load_ui_static_map
    mark("imports_and_qapplication")
    root = uic.loadUi(str(Path(__file__).resolve().parent / "lathe_easystep.ui"))
    mark("shell_ui")
    handler = types.SimpleNamespace(root_widget=root, w=root, _split_tabs_loaded=False,
        _log=lambda *a, **k: None,
        _get_widget_by_name=lambda name: root.findChild(QtWidgets.QWidget, name))
    load_split_tab_uis(handler)
    mark("eight_tab_uis")
    ensure_advanced_widgets(handler)
    mark("advanced_widgets")
    load_ui_static_map()
    mark("translation_source_map")
    root.ensurePolished()
    app.processEvents()
    mark("polish_and_pending_events")
    times["total_measured"] = sum(times.values())
    root.close()
    return times


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sample", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sample:
        print(json.dumps(sample()))
        return
    if not 1 <= args.runs <= 50:
        parser.error("runs must be between 1 and 50")
    samples = []
    for _ in range(args.runs):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--sample"],
            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"), capture_output=True,
            text=True, check=True, timeout=60)
        row = json.loads(result.stdout)
        row["process_wall_time"] = time.perf_counter() - start
        samples.append(row)
    report = {"scope": "isolated Qt UI construction; no HandlerClass initialization, HAL, tooltable or visible panel",
        "platform": platform.platform(), "python": platform.python_version(),
        "samples_seconds": samples,
        "median_seconds": {key: statistics.median(row[key] for row in samples) for key in samples[0]}}
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
