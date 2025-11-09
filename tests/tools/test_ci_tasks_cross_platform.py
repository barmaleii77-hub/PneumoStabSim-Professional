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


def test_prepare_cross_platform_linux_uses_gpu_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_console(monkeypatch)
    env: dict[str, str] = {}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="Linux"
    )

    assert result == "linux"
    assert env.get("QT_QPA_PLATFORM") != "offscreen"
    assert env.get("QT_QUICK_BACKEND") is None
    assert env["QSG_RHI_BACKEND"] == "opengl"
    assert env["LIBGL_ALWAYS_SOFTWARE"] == "1"
    assert env["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert env["PSS_DETECTED_PLATFORM"] == "Linux"
    assert any("Linux" in line for line in captured)
    assert any("Qt launch mode: gpu" in line for line in captured)


def test_prepare_cross_platform_linux_respects_headless_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_console(monkeypatch)
    env: dict[str, str] = {"PSS_HEADLESS": "1"}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="Linux"
    )

    assert result == "linux"
    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert env["QT_QUICK_BACKEND"] == "software"
    assert env["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert env["PSS_HEADLESS"] == "1"
    assert env["PSS_DETECTED_PLATFORM"] == "Linux"
    assert any("Qt launch mode: headless" in line for line in captured)


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
    assert env["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert env["PSS_DETECTED_PLATFORM"] == "Windows"
    assert "QT_QPA_PLATFORM" not in env
    assert any("Windows" in line for line in captured)
    assert any("Qt launch mode: gpu" in line for line in captured)


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
    assert env["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert env["PSS_DETECTED_PLATFORM"] == "Darwin"
    assert "QT_QPA_PLATFORM" not in env
    assert any("Darwin" in line for line in captured)
    assert any("Qt launch mode: gpu" in line for line in captured)


def test_prepare_cross_platform_respects_existing_overrides() -> None:
    env = {"QT_QPA_PLATFORM": "xcb", "QSG_RHI_BACKEND": "metal"}

    result = ci_tasks._prepare_cross_platform_test_environment(
        env, platform_name="linux"
    )

    assert result == "linux"
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert env["QSG_RHI_BACKEND"] == "metal"
    assert "QT_QUICK_BACKEND" not in env
    assert env["LIBGL_ALWAYS_SOFTWARE"] == "1"
    assert env["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert env["PSS_DETECTED_PLATFORM"] == "linux"
