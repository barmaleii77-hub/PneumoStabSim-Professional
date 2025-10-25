"""Tests for the Visual Studio Insiders environment generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import pytest

from src.tools.visualstudio_insiders import build_insiders_environment


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
    }
    assert expected_keys.issubset(environment.keys())

    qml_paths = environment["QML2_IMPORT_PATH"].split(";")
    expected_qml = {
        str(PureWindowsPath(project_root / "assets" / "qml")),
        str(PureWindowsPath(project_root / ".venv" / "Lib" / "site-packages" / "PySide6" / "qml")),
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


def test_cli_matches_python_builder(project_root: Path, tmp_path: Path) -> None:
    script = project_root / "tools" / "visualstudio" / "generate_insiders_environment.py"
    assert script.exists()

    output = subprocess.check_output(
        [sys.executable, str(script), "--project-root", str(project_root)],
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
        ]
    )
    assert json.loads(output_file.read_text()) == builder_payload
