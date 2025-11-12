from __future__ import annotations

from tools import hdr_backend_matrix as matrix


def test_linux_plan_env_configuration():
    plan = matrix.compute_backend_plan("linux")
    assert plan.platform == "Linux"
    assert plan.primary_backend == "OpenGL 4.5 Core"
    assert plan.env["QSG_RHI_BACKEND"] == "opengl"
    assert plan.env["QT_OPENGL_PROFILE"] == "core"
    assert plan.optional_env["QSG_OPENGL_VERSION_FALLBACK"] == "3.3"


def test_windows_plan_forces_direct3d():
    plan = matrix.compute_backend_plan("windows")
    assert plan.platform == "Windows"
    assert plan.env["QSG_RHI_BACKEND"] == "d3d11"
    assert "Dithering" in "\n".join(plan.render().splitlines())


def test_macos_plan_uses_metal():
    plan = matrix.compute_backend_plan("macos")
    assert plan.platform == "macOS"
    assert plan.env["QSG_RHI_BACKEND"] == "metal"
    assert "Metal" in plan.render()


def test_quality_tab_contains_dithering_markers():
    issues = matrix._check_dithering_control(matrix.QUALITY_TAB)
    assert issues == []


def test_settings_expose_dithering_keys():
    payload = matrix._load_settings()
    issues = matrix._check_settings_for_dithering(payload)
    assert issues == []
