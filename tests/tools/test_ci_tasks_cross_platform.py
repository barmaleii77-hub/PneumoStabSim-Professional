from __future__ import annotations

import pytest

from tools import ci_tasks


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PSS_DETECTED_PLATFORM", raising=False)


def _capture_console(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    captured: list[str] = []
    monkeypatch.setattr(
        ci_tasks, "_safe_console_write", lambda text: captured.append(text)
    )
    return captured


def test_prepare_cross_platform_linux_sets_headless_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_console(monkeypatch)
    env: dict[str, str] = {}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="Linux"
    )

    assert result == "linux"
    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert env["QT_QUICK_BACKEND"] == "software"
    assert env["LIBGL_ALWAYS_SOFTWARE"] == "1"
    assert env["PSS_DETECTED_PLATFORM"] == "Linux"
    assert any("Linux" in line for line in captured)


def test_prepare_cross_platform_windows_prefers_direct3d(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_console(monkeypatch)
    env: dict[str, str] = {}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="Windows"
    )

    assert result == "windows"
    assert env["QT_QUICK_BACKEND"] == "rhi"
    assert env["QSG_RHI_BACKEND"] == "d3d11"
    assert env["PSS_DETECTED_PLATFORM"] == "Windows"
    assert "QT_QPA_PLATFORM" not in env
    assert any("Windows" in line for line in captured)


def test_prepare_cross_platform_macos_prefers_metal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_console(monkeypatch)
    env: dict[str, str] = {}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="Darwin"
    )

    assert result == "darwin"
    assert env["QT_QUICK_BACKEND"] == "rhi"
    assert env["QSG_RHI_BACKEND"] == "metal"
    assert env["PSS_DETECTED_PLATFORM"] == "Darwin"
    assert "QT_QPA_PLATFORM" not in env
    assert any("Darwin" in line for line in captured)


def test_prepare_cross_platform_respects_existing_overrides() -> None:
    env = {"QT_QPA_PLATFORM": "xcb", "QSG_RHI_BACKEND": "metal"}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="linux"
    )

    assert result == "linux"
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert env["QSG_RHI_BACKEND"] == "metal"
    assert env["QT_QUICK_BACKEND"] == "software"
    assert env["LIBGL_ALWAYS_SOFTWARE"] == "1"
    assert env["PSS_DETECTED_PLATFORM"] == "linux"
