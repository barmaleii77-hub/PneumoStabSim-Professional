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

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


# Требуемая версия Python: 3.11–3.13 (исключаем 3.14+, т.к. PySide6 6.10 ещё не готов)
MIN_PYTHON_VERSION = (3, 11)
MAX_PYTHON_MINOR_SUPPORTED = 13
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"


def _check_python_version() -> dict[str, Any]:
    current = sys.version_info[:3]
    major, minor = current[0], current[1]
    ok = (major == 3 and MIN_PYTHON_VERSION <= (major, minor) <= (3, MAX_PYTHON_MINOR_SUPPORTED))
    message: str
    if ok:
        message = "Python version is within supported range (3.11–3.13)"
    else:
        if major != 3:
            message = "Python 3.x is required"
        elif minor < MIN_PYTHON_VERSION[1]:
            message = "Python 3.11+ is required"
        else:
            message = "Python 3.14+ is not supported by PySide6 6.10 yet"
    return {
        "check": "python-version",
        "status": "ok" if ok else "error",
        "current": list(current),
        "minimum": [*MIN_PYTHON_VERSION, 0],
        "maximum_minor": MAX_PYTHON_MINOR_SUPPORTED,
        "message": message,
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
    # Расширенный список обязательных модулей для исключения запуска без GUI-стека
    required_modules = [
        "numpy",
        "scipy",
        "PySide6",
        "PySide6.QtQml",
        "PySide6.QtQuick3D",
        "src",
    ]
    failures: list[str] = []
    failure_details: list[dict[str, str]] = []

    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(SRC_PATH))

    for module_name in required_modules:
        try:
            __import__(module_name)
        except Exception as exc:  # pragma: no cover - diagnostics path
            failures.append(module_name)
            failure_details.append({"module": module_name, "error": str(exc)})

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
        "failure_details": failure_details,
        "message": message,
    }


def _should_attempt_auto_repair(import_check: dict[str, Any]) -> bool:
    failed_modules = import_check.get("failed", [])
    return any(name.startswith("PySide6") for name in failed_modules)


def _run_auto_repair(import_check: dict[str, Any]) -> dict[str, Any]:
    if not _should_attempt_auto_repair(import_check):
        return {
            "attempted": False,
            "success": True,
            "message": "Auto-repair not required for current failures",
        }

    command = [
        sys.executable,
        "-m",
        "tools.cross_platform_test_prep",
        "--use-uv",
        "--skip-python",
    ]

    try:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - external command
        return {
            "attempted": True,
            "success": False,
            "message": f"Auto-repair failed: {exc}",
        }

    return {
        "attempted": True,
        "success": True,
        "message": "Installed system Qt runtime dependencies via cross_platform_test_prep",
    }


def _build_payload() -> dict[str, Any]:
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
    return payload


def _first_error_message(payload: dict[str, Any]) -> str:
    for c in payload.get("checks", []):
        if c.get("status") != "ok":
            msg = c.get("message") or c.get("check") or "unknown error"
            return str(msg)
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Environment diagnostics")
    parser.add_argument("--compact", action="store_true", help="Однострочный вывод в stdout; полный JSON сохраняется в файл")
    parser.add_argument("--output", type=str, default="", help="Путь к файлу для записи полного JSON-отчёта")
    parser.add_argument(
        "--auto-repair",
        action="store_true",
        help="Автоматически установить системные зависимости Qt при провале импортов PySide6",
    )
    args = parser.parse_args()

    payload = _build_payload()
    auto_repair_result: dict[str, Any] | None = None

    if payload["status"] != "ok" and args.auto_repair:
        import_check = next((c for c in payload["checks"] if c["check"] == "python-imports"), None)
        if import_check:
            auto_repair_result = _run_auto_repair(import_check)
            payload = _build_payload()
        else:  # pragma: no cover - defensive fallback
            auto_repair_result = {
                "attempted": False,
                "success": False,
                "message": "Auto-repair skipped: python-imports check is missing",
            }

    if auto_repair_result is not None:
        payload["auto_repair"] = auto_repair_result

    # Если указан выходной файл — записываем полный JSON
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.compact:
        # Краткая строка статуса для PowerShell/CI консоли
        if payload["status"] == "ok":
            print("ENV OK")
            return 0
        else:
            print(f"ENV ERROR: {_first_error_message(payload)}")
            return 1

    # Полный вывод в stdout (исторический режим)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())

