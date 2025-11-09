"""Unit tests for the headless launch environment helper."""

from tools.headless import HEADLESS_FLAG
from tools.headless import prepare_launch_environment


def test_prepare_launch_environment_applies_headless_defaults() -> None:
    base_env = {HEADLESS_FLAG: "1"}

    prepared = prepare_launch_environment(base_env, platform_name="win32")

    assert prepared["QT_QPA_PLATFORM"] == "offscreen"
    assert prepared["QT_QUICK_BACKEND"] == "software"
    assert prepared["QT_QUICK_CONTROLS_STYLE"] == "Basic"
    assert HEADLESS_FLAG in prepared
    assert "QSG_RHI_BACKEND" not in prepared


def test_prepare_launch_environment_restores_gpu_defaults() -> None:
    base_env = {
        "QT_QPA_PLATFORM": "offscreen",
        "QT_QUICK_BACKEND": "software",
        "PSS_FORCE_NO_QML_3D": "1",
    }

    prepared = prepare_launch_environment(base_env, platform_name="win32")

    assert HEADLESS_FLAG not in prepared
    assert prepared["QSG_RHI_BACKEND"] == "d3d11"
    assert prepared["QT_QUICK_BACKEND"] == "rhi"
    assert "QT_QPA_PLATFORM" not in prepared
    assert "PSS_FORCE_NO_QML_3D" not in prepared
    assert prepared["QT_QUICK_CONTROLS_STYLE"] == "Basic"

    # Ensure the original mapping is untouched so callers can reuse it.
    assert base_env["QT_QPA_PLATFORM"] == "offscreen"
