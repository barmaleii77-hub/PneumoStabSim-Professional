from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

RECOMMENDED_MAJOR = 3
RECOMMENDED_MINOR = 13
MINIMUM_MINOR = 11

REQUIREMENTS_FILES = (
    "requirements.txt",
    "requirements-dev.txt",
    "current_requirements.txt",
)

REQUIRED_IMPORTS = (
    "PySide6",
    "numpy",
    "scipy",
    "structlog",
)

SUPPORTED_SYSTEMS: dict[str, dict[str, tuple[int, ...]]] = {
    "Windows": {"min_release": (10,)},
    "Linux": {"min_release": ()},
    "Darwin": {"min_release": (20,)},
}


@dataclass(frozen=True)
class Interpreter:
    executable: Path
    version: tuple[int, int, int]
    command: Sequence[str]

    @property
    def display(self) -> str:
        return (
            f"{self.executable} ({self.version[0]}.{self.version[1]}.{self.version[2]})"
        )


class EnvironmentError(RuntimeError):
    """Raised when the environment cannot be prepared automatically."""


def probe_interpreter(command: Sequence[str]) -> Optional[Interpreter]:
    query = list(command) + [
        "-c",
        "import json, sys; print(json.dumps({'executable': sys.executable, 'version': sys.version_info[:3]}))",
    ]
    try:
        result = subprocess.run(query, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    try:
        payload = json.loads(result.stdout.strip())
        executable = Path(payload["executable"]).resolve()
        version_tuple = tuple(int(part) for part in payload["version"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    return Interpreter(
        executable=executable, version=version_tuple, command=tuple(command)
    )


def discover_interpreters() -> list[Interpreter]:
    commands: list[Sequence[str]] = []
    if sys.executable:
        commands.append((sys.executable,))

    for minor in (13, 12, 11):
        commands.append(("py", f"-3.{minor}"))
        commands.append((f"python3.{minor}",))
        commands.append((f"python{minor}",))

    commands.extend((("python3",), ("python",)))

    interpreters: list[Interpreter] = []
    seen: set[Path] = set()
    for candidate in commands:
        interpreter = probe_interpreter(candidate)
        if interpreter and interpreter.executable not in seen:
            interpreters.append(interpreter)
            seen.add(interpreter.executable)

    interpreters.sort(key=lambda item: item.version, reverse=True)
    return interpreters


def select_interpreter() -> Interpreter:
    interpreters = discover_interpreters()
    if not interpreters:
        raise EnvironmentError(
            "Не удалось найти установленный Python. Установите Python 3.13 или более свежую совместимую версию."
        )

    preferred = [
        interpreter
        for interpreter in interpreters
        if interpreter.version[0] == RECOMMENDED_MAJOR
        and interpreter.version[1] >= RECOMMENDED_MINOR
    ]
    if preferred:
        return preferred[0]

    fallback = [
        interpreter
        for interpreter in interpreters
        if interpreter.version[0] == RECOMMENDED_MAJOR
        and interpreter.version[1] >= MINIMUM_MINOR
    ]
    if fallback:
        return fallback[0]

    return interpreters[0]


def ensure_supported_platform() -> dict[str, object]:
    system = platform.system()
    release = platform.release()
    version = platform.version()

    if system not in SUPPORTED_SYSTEMS:
        raise EnvironmentError(
            "Обнаружена неподдерживаемая операционная система: {system}. "
            "Поддерживаются Windows, Linux и macOS.".format(system=system)
        )

    requirements = SUPPORTED_SYSTEMS[system]
    min_release = requirements.get("min_release", ())
    release_tuple = _parse_release(release)

    if min_release and release_tuple and release_tuple < min_release:
        raise EnvironmentError(
            "Требуется версия {system} {required}+ (обнаружено {release}).".format(
                system=system,
                required=".".join(str(part) for part in min_release),
                release=release,
            )
        )

    return {
        "system": system,
        "release": release,
        "version": version,
        "minimum_release": ".".join(str(part) for part in min_release)
        if min_release
        else "",
    }


def _parse_release(raw: str) -> tuple[int, ...]:
    parts: list[int] = []
    for token in raw.replace("-", ".").split("."):
        if token.isdigit():
            parts.append(int(token))
        else:
            break
    return tuple(parts)


def ensure_virtual_environment(interpreter: Interpreter, project_root: Path) -> Path:
    venv_dir = project_root / ".venv"
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    python_path = (
        venv_dir / scripts_dir / ("python.exe" if os.name == "nt" else "python")
    )

    if python_path.exists():
        return python_path

    venv_command = list(interpreter.command) + ["-m", "venv", str(venv_dir)]
    subprocess.run(venv_command, check=True)
    return python_path


def compute_requirements_digest(files: Iterable[Path]) -> str:
    hasher = hashlib.sha256()
    for file_path in files:
        if not file_path.exists():
            continue
        hasher.update(str(file_path).encode("utf-8"))
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def detect_missing_imports(python_path: Path) -> list[str]:
    script_lines = [
        "import importlib.util",
        "import json",
        f"modules = {list(REQUIRED_IMPORTS)!r}",
        "missing = [name for name in modules if importlib.util.find_spec(name) is None]",
        "print(json.dumps(missing))",
        "raise SystemExit(0 if not missing else 1)",
    ]
    result = subprocess.run(
        [str(python_path), "-c", "\n".join(script_lines)],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout.strip() or "[]"
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        payload = []
    return [str(name) for name in payload]


def ensure_required_imports(python_path: Path) -> list[str]:
    missing = detect_missing_imports(python_path)
    if not missing:
        return []

    for package in missing:
        subprocess.run([str(python_path), "-m", "pip", "install", package], check=True)

    remaining = detect_missing_imports(python_path)
    if remaining:
        raise EnvironmentError(
            "Не удалось установить обязательные пакеты: {packages}".format(
                packages=", ".join(remaining)
            )
        )

    return missing


def ensure_dependencies(python_path: Path, project_root: Path) -> dict[str, Any]:
    requirement_paths = [project_root / name for name in REQUIREMENTS_FILES]
    digest = compute_requirements_digest(requirement_paths)
    marker = project_root / ".venv" / ".requirements.hash"

    needs_install = True
    if marker.exists():
        previous = marker.read_text(encoding="utf-8").strip()
        if previous == digest:
            needs_install = False

    applied_requirements: list[str] = []
    if needs_install:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True
        )
        for req in requirement_paths:
            if req.exists():
                subprocess.run(
                    [str(python_path), "-m", "pip", "install", "-r", str(req)],
                    check=True,
                )
                applied_requirements.append(str(req))
        marker.write_text(digest, encoding="utf-8")

    installed_missing_imports = ensure_required_imports(python_path)
    remaining_missing_imports = detect_missing_imports(python_path)

    return {
        "requirements_updated": needs_install,
        "applied_requirement_files": applied_requirements,
        "installed_missing_imports": installed_missing_imports,
        "remaining_missing_imports": remaining_missing_imports,
    }


def describe_virtual_envs(project_root: Path) -> list[str]:
    environments: list[str] = []
    for candidate in project_root.iterdir():
        if not candidate.is_dir():
            continue
        if not (candidate / "pyvenv.cfg").exists():
            continue
        scripts_dir = candidate / ("Scripts" if os.name == "nt" else "bin")
        if scripts_dir.exists():
            environments.append(candidate.name)
    environments.sort()
    return environments


def collect_status(
    python_path: Path,
    interpreter: Interpreter,
    project_root: Path,
    platform_info: dict[str, object],
    dependency_report: dict[str, Any],
) -> dict[str, object]:
    venv_active = os.environ.get("VIRTUAL_ENV")
    expected_venv = python_path.parent.parent
    active_matches_expected = False
    if venv_active:
        try:
            active_matches_expected = (
                Path(venv_active).resolve() == expected_venv.resolve()
            )
        except OSError:
            active_matches_expected = False

    return {
        "platform": platform_info,
        "python": {
            "executable": str(interpreter.executable),
            "version": ".".join(str(part) for part in interpreter.version),
            "meets_recommendation": interpreter.version[0] == RECOMMENDED_MAJOR
            and interpreter.version[1] >= RECOMMENDED_MINOR,
            "meets_minimum": interpreter.version[0] == RECOMMENDED_MAJOR
            and interpreter.version[1] >= MINIMUM_MINOR,
        },
        "virtual_environment": {
            "path": str(expected_venv),
            "active": bool(venv_active),
            "active_path": venv_active or "",
            "available": describe_virtual_envs(project_root),
            "active_matches_expected": active_matches_expected,
        },
        "dependencies": {
            "ok": not dependency_report["remaining_missing_imports"],
            "remaining_missing": dependency_report["remaining_missing_imports"],
            "installed_missing": dependency_report["installed_missing_imports"],
            "requirements_updated": dependency_report["requirements_updated"],
            "applied_requirement_files": dependency_report["applied_requirement_files"],
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure PneumoStabSim Python environment is ready.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to the PneumoStabSim project root.",
    )
    parser.add_argument(
        "--status-json",
        type=Path,
        help="Optional path to write the environment status JSON.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    project_root: Path = args.project_root.resolve()

    platform_info = ensure_supported_platform()
    interpreter = select_interpreter()
    python_path = ensure_virtual_environment(interpreter, project_root)
    dependency_report = ensure_dependencies(python_path, project_root)
    status = collect_status(
        python_path, interpreter, project_root, platform_info, dependency_report
    )

    message_lines = [
        "=== PneumoStabSim Environment Summary ===",
        "Platform: {system} {release}".format(
            system=status["platform"]["system"], release=status["platform"]["release"]
        ),
        "Platform version: {version}".format(version=status["platform"]["version"]),
        f"Python executable: {status['python']['executable']}",
        f"Python version: {status['python']['version']}",
        "Recommended version installed: "
        + ("yes" if status["python"]["meets_recommendation"] else "no"),
        "Minimum supported version satisfied: "
        + ("yes" if status["python"]["meets_minimum"] else "no"),
        f"Virtual env path: {status['virtual_environment']['path']}",
        "Active virtual env: "
        + ("yes" if status["virtual_environment"]["active"] else "no"),
        "Active environment matches expected: "
        + ("yes" if status["virtual_environment"]["active_matches_expected"] else "no"),
        "Available virtual envs: "
        + ", ".join(status["virtual_environment"]["available"]),
        "Dependencies OK: " + ("yes" if status["dependencies"]["ok"] else "no"),
    ]

    installed_missing = status["dependencies"]["installed_missing"]
    if installed_missing:
        message_lines.append(
            "Installed missing packages: " + ", ".join(sorted(installed_missing))
        )

    if status["dependencies"]["remaining_missing"]:
        message_lines.append(
            "Remaining missing packages: "
            + ", ".join(status["dependencies"]["remaining_missing"])
        )

    print("\n".join(message_lines))

    if args.status_json:
        args.status_json.parent.mkdir(parents=True, exist_ok=True)
        args.status_json.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
