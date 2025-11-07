from __future__ import annotations

import pytest

from src.ui.startup import (
    bootstrap_graphics_environment,
    choose_scenegraph_backend,
    detect_headless_environment,
)


@pytest.mark.parametrize(
    "platform,expected",
    [
        ("win32", "d3d11"),
        ("darwin", "metal"),
        ("linux", "opengl"),
        ("linux-x86_64", "opengl"),
        ("macos", "metal"),
    ],
)
def test_choose_scenegraph_backend(platform: str, expected: str) -> None:
    assert choose_scenegraph_backend(platform) == expected


@pytest.mark.parametrize(
    "env,expected_reasons",
    [
        (
            {"CI": "true", "QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"},
            ("ci-flag",),
        ),
        (
            {"QT_QPA_PLATFORM": "", "DISPLAY": ""},
            ("no-display-server", "qt-qpa-platform-missing"),
        ),
        ({"QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"}, ()),
    ],
)
def test_detect_headless_environment(
    env: dict[str, str], expected_reasons: tuple[str, ...]
) -> None:
    headless, reasons = detect_headless_environment(env)
    assert reasons == expected_reasons
    assert headless is bool(expected_reasons)


def test_bootstrap_graphics_environment_sets_backend_when_not_safe() -> None:
    env: dict[str, str] = {"QT_QPA_PLATFORM": "xcb"}
    state = bootstrap_graphics_environment(env, platform="win32", safe_mode=False)

    assert env["QSG_RHI_BACKEND"] == "d3d11"
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert "PSS_FORCE_NO_QML_3D" not in env
    assert state.backend == "d3d11"
    assert state.headless is False
    assert state.use_qml_3d is True


def test_bootstrap_graphics_environment_enables_headless_defaults() -> None:
    env: dict[str, str] = {}
    state = bootstrap_graphics_environment(env, platform="linux", safe_mode=False)

    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert env["PSS_FORCE_NO_QML_3D"] == "1"
    assert env["QSG_RHI_BACKEND"] == "opengl"
    assert state.headless is True
    assert "qt-qpa-platform-missing" in state.headless_reasons
    assert state.use_qml_3d is False


def test_bootstrap_graphics_environment_respects_safe_mode() -> None:
    env: dict[str, str] = {"QT_QPA_PLATFORM": "xcb"}
    state = bootstrap_graphics_environment(env, platform="darwin", safe_mode=True)

    assert "QSG_RHI_BACKEND" not in env
    assert "PSS_FORCE_NO_QML_3D" not in env
    assert state.backend == "metal"
    assert state.safe_mode is True
    assert state.use_qml_3d is True
