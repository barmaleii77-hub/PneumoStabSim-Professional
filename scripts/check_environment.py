#!/usr/bin/env python3
"""Basic environment diagnostics used by the comprehensive test runner.

This script intentionally performs lightweight checks so that continuous
integration pipelines can fail fast when the Python environment is missing
critical requirements.  The historical reports referenced by the renovation
playbooks expect a JSON payload on ``stdout`` and a zero exit status when all
checks succeed.

The checks implemented here focus on validating that:

* The repository root can be located relative to this script.
* The ``src`` package directory is importable.
* Key third-party dependencies declared in ``pyproject.toml`` can be imported.
* The Python interpreter version satisfies the minimum supported version.

The script exits with status code ``0`` when everything looks correct and ``1``
otherwise.  Failures are reported as a JSON document to make the output easy to
parse programmatically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any 


MIN_PYTHON_VERSION = (3, 10)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"


def _check_python_version() -> dict[str, Any]:
    current = sys.version_info[:3]
    ok = current >= MIN_PYTHON_VERSION
    return {
        "check": "python-version",
        "status": "ok" if ok else "error",
        "current": list(current),
        "minimum": list(MIN_PYTHON_VERSION),
        "message": (
            "Python version is sufficient"
            if ok
            else f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required"
        ),
    }


def _check_repository_layout() -> dict[str, Any]:
    if SRC_PATH.is_dir():
        status = "ok"
        message = "src directory is present"
    else:
        status = "error"
        message = "src directory is missing"
    return {
        "check": "repository-layout",
        "status": status,
        "path": str(SRC_PATH),
        "message": message,
    }


def _check_imports() -> dict[str, Any]:
    required_modules = [
        "numpy",
        "PySide6",
        "src",
    ]
    failures: list[str] = []

    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(SRC_PATH))

    for module_name in required_modules:
        try:
            __import__(module_name)
        except Exception:  # pragma: no cover - diagnostics path
            failures.append(module_name)

    if failures:
        status = "error"
        message = f"Failed to import: {', '.join(sorted(set(failures)))}"
    else:
        status = "ok"
        message = "All critical modules imported"

    return {
        "check": "python-imports",
        "status": status,
        "required": required_modules,
        "failed": failures,
        "message": message,
    }


def main() -> int:
    checks = [
        _check_python_version(),
        _check_repository_layout(),
        _check_imports(),
    ]

    overall_status = "ok"
    for check in checks:
        if check["status"] != "ok":
            overall_status = "error"
            break

    payload = {
        "status": overall_status,
        "checks": checks,
        "project_root": str(PROJECT_ROOT),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if overall_status == "ok" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())

