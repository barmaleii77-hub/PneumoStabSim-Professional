"""Tests for the Qt provisioning helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import setup_qt


@pytest.fixture()
def qt_installation(tmp_path: Path) -> Path:
    install_dir = tmp_path / "Qt" / "6.10.0" / "gcc_64"
    for part in ("bin", "lib", "qml", "plugins"):
        (install_dir / part).mkdir(parents=True, exist_ok=True)
    return install_dir


def test_check_installation_success(
    qt_installation: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_import() -> tuple[str, str]:
        return "6.10.0", "6.10.0"

    result = setup_qt._check_installation(
        install_dir=qt_installation,
        qt_version="6.10.0",
        archives_dir=qt_installation.parent.parent.parent / ".qt",
        checksum_manifest=None,
        importer=fake_import,
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "Found Qt component" in captured.out


def test_check_installation_reports_missing_components(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    install_dir = tmp_path / "Qt" / "6.10.0" / "gcc_64"
    (install_dir / "bin").mkdir(parents=True, exist_ok=True)

    def fake_import() -> tuple[str, str]:
        return "6.10.0", "6.10.0"

    result = setup_qt._check_installation(
        install_dir=install_dir,
        qt_version="6.10.0",
        archives_dir=tmp_path / ".qt",
        checksum_manifest=None,
        importer=fake_import,
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "Missing required Qt subdirectory" in captured.out


def test_check_installation_detects_version_mismatch(
    qt_installation: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_import() -> tuple[str, str]:
        return "6.10.0", "6.9.9"

    result = setup_qt._check_installation(
        install_dir=qt_installation,
        qt_version="6.10.0",
        archives_dir=qt_installation.parent.parent.parent / ".qt",
        checksum_manifest=None,
        importer=fake_import,
    )

    captured = capsys.readouterr()
    assert result == 1
    assert "version mismatch" in captured.out
