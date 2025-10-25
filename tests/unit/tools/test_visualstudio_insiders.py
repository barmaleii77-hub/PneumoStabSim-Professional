"""Tests for the Visual Studio Insiders environment generator."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import pytest

from src.tools.visualstudio_insiders import (
    build_insiders_environment,
    validate_insiders_environment,
)


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_environment_contains_expected_paths(project_root: Path) -> None:
    environment = build_insiders_environment(project_root)

    expected_keys = {
        "QML2_IMPORT_PATH",
        "QML_IMPORT_PATH",
        "QT_PLUGIN_PATH",
        "QT_QML_IMPORT_PATH",
        "PYTHONPATH",
        "PNEUMOSTABSIM_PROFILE",
        "VIRTUAL_ENV",
        "POWERSHELL_UPDATECHECK",
        "POWERSHELL_TELEMETRY_OPTOUT",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
        "LC_ALL",
        "LANG",
    }
    assert expected_keys.issubset(environment.keys())

    qml_paths = environment["QML2_IMPORT_PATH"].split(";")
    expected_qml = {
        str(PureWindowsPath(project_root / "assets" / "qml")),
        str(
            PureWindowsPath(
                project_root / ".venv" / "Lib" / "site-packages" / "PySide6" / "qml"
            )
        ),
    }
    assert expected_qml.issubset(qml_paths)

    python_path_entries = environment["PYTHONPATH"].split(";")
    expected_python_entries = {
        str(PureWindowsPath(project_root)),
        str(PureWindowsPath(project_root / "src")),
        str(PureWindowsPath(project_root / "tests")),
    }
    assert expected_python_entries.issubset(python_path_entries)

    assert environment["PNEUMOSTABSIM_PROFILE"] == "insiders"
    assert environment["VIRTUAL_ENV"] == str(PureWindowsPath(project_root / ".venv"))
    assert environment["POWERSHELL_UPDATECHECK"] == "Off"
    assert environment["POWERSHELL_TELEMETRY_OPTOUT"] == "1"
    assert environment["PYTHONUTF8"] == "1"
    assert environment["PYTHONIOENCODING"] == "utf-8"
    assert environment["LC_ALL"] == "C.UTF-8"
    assert environment["LANG"] == "en_US.UTF-8"


def _create_fake_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "pneumo-insiders"
    (project_root / "assets" / "qml").mkdir(parents=True)
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir(parents=True)

    pyside_root = project_root / ".venv" / "Lib" / "site-packages" / "PySide6"
    (pyside_root / "qml").mkdir(parents=True)
    (pyside_root / "plugins").mkdir(parents=True)

    return project_root


def test_validation_requires_expected_directories(tmp_path: Path) -> None:
    project_root = _create_fake_project(tmp_path)

    environment = validate_insiders_environment(project_root)
    assert environment["PNEUMOSTABSIM_PROFILE"] == "insiders"

    shutil.rmtree(project_root / "assets")
    with pytest.raises(FileNotFoundError):
        validate_insiders_environment(project_root)


def test_validation_supports_posix_layout(tmp_path: Path) -> None:
    project_root = tmp_path / "pneumo-insiders-posix"
    (project_root / "assets" / "qml").mkdir(parents=True)
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir(parents=True)

    pyside_root = (
        project_root / ".venv" / "lib" / "python3.13" / "site-packages" / "PySide6"
    )
    (pyside_root / "qml").mkdir(parents=True)
    (pyside_root / "plugins").mkdir(parents=True)

    environment = build_insiders_environment(project_root, ensure_paths=True)
    qml_paths = environment["QML2_IMPORT_PATH"].split(";")
    assert str(PureWindowsPath(pyside_root / "qml")) in qml_paths


def test_cli_matches_python_builder(project_root: Path, tmp_path: Path) -> None:
    script = (
        project_root / "tools" / "visualstudio" / "generate_insiders_environment.py"
    )
    assert script.exists()

    output = subprocess.check_output(
        [
            sys.executable,
            str(script),
            "--project-root",
            str(project_root),
            "--skip-validation",
        ],
        text=True,
    )
    cli_payload = json.loads(output)
    builder_payload = build_insiders_environment(project_root)

    assert cli_payload == builder_payload

    output_file = tmp_path / "insiders.json"
    subprocess.check_call(
        [
            sys.executable,
            str(script),
            "--project-root",
            str(project_root),
            "--output",
            str(output_file),
            "--skip-validation",
        ]
    )
    assert json.loads(output_file.read_text()) == builder_payload


def test_cli_validation_detects_missing_dependencies(
    tmp_path: Path, project_root: Path
) -> None:
    script = (
        project_root / "tools" / "visualstudio" / "generate_insiders_environment.py"
    )
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(
            [
                sys.executable,
                str(script),
                "--project-root",
                str(tmp_path / "missing-project"),
            ]
        )
