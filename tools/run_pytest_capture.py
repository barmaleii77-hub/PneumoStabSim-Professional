#!/usr/bin/env python3
"""Helper to run pytest and capture full output into reports/pytest_last.txt.
Prints first 200 lines to stdout for quick inspection.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    report_path = root / "reports" / "pytest_last.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pytest", "-vv", "--maxfail=1", "--durations=5"]
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    combined = proc.stdout + "\n" + proc.stderr
    report_path.write_text(combined, encoding="utf-8")
    lines = combined.splitlines()
    head = lines[:200]
    print("\n=== PYTEST HEAD (first 200 lines) ===")
    print("\n".join(head))
    print("\n=== END HEAD ===")
    print(f"Exit code: {proc.returncode}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
