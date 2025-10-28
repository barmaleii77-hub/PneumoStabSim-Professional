"""Tests for the Copilot environment preparation helper."""

from __future__ import annotations

import json

import pytest

from tools import cipilot_environment

pytest.importorskip("PySide6")


def test_gather_environment_python_mode_populates_qt_paths() -> None:
    snapshot = cipilot_environment.gather_environment("python")

    assert snapshot.env_vars["QT_QPA_PLATFORM"] == "offscreen"
    assert snapshot.env_vars["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert snapshot.env_vars.get("QT_PLUGIN_PATH")
    assert snapshot.env_vars.get("QML2_IMPORT_PATH")
    assert snapshot.metadata.qt_version
    assert snapshot.metadata.pyside6_version


def test_render_shell_exports_orders_core_variables() -> None:
    exports = cipilot_environment.render_shell_exports(
        {
            "QT_PLUGIN_PATH": "/tmp/qt/plugins",
            "QML2_IMPORT_PATH": "/tmp/qml",
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_CONTROLS_STYLE": "Basic",
            "QT_QUICK_BACKEND": "software",
        }
    )

    lines = [line for line in exports.splitlines() if line.startswith("export ")]
    assert lines[:3] == [
        "export QT_QPA_PLATFORM=offscreen",
        "export QT_QUICK_BACKEND=software",
        "export QT_QUICK_CONTROLS_STYLE=Basic",
    ]


def test_write_report_persists_metadata(tmp_path) -> None:
    snapshot = cipilot_environment.EnvironmentSnapshot(
        env_vars={"QT_QPA_PLATFORM": "offscreen"},
        metadata=cipilot_environment.QtMetadata(
            qt_version="6.10.0",
            pyside6_version="6.10.0",
        ),
    )
    report_path = tmp_path / "cipilot.json"

    cipilot_environment.write_report(
        report_path,
        snapshot,
        uv_sync=True,
        probe_mode="python",
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["uv_sync_performed"] is True
    assert payload["probe_mode"] == "python"
    assert payload["metadata"]["qt_version"] == "6.10.0"
    assert payload["env"]["QT_QPA_PLATFORM"] == "offscreen"
