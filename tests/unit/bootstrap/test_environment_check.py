from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.bootstrap import environment_check


class _DummyVariant(SimpleNamespace):
    """Test helper that mimics the interface of ``DependencyVariant``."""


@pytest.fixture
def dummy_variant() -> _DummyVariant:
    variant = _DummyVariant(library_name="GL", human_name="OpenGL runtime")
    variant.install_hint = "Install OpenGL runtime via system package manager."
    variant.missing_message = "Required OpenGL runtime (libGL.so.1) is missing."
    return variant


def test_opengl_check_warns_in_headless_environment(
    monkeypatch: pytest.MonkeyPatch, dummy_variant: _DummyVariant
) -> None:
    """Headless agents should downgrade the missing OpenGL runtime to a warning."""

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(
        environment_check, "resolve_dependency_variant", lambda name: dummy_variant
    )
    monkeypatch.setattr(environment_check, "find_library", lambda name: None)

    result = environment_check._check_opengl_runtime()

    assert result.status == "warning"
    assert "headless" in (result.detail or "").lower()


def test_opengl_check_errors_when_display_present(
    monkeypatch: pytest.MonkeyPatch, dummy_variant: _DummyVariant
) -> None:
    """When a display is available the OpenGL runtime remains a hard requirement."""

    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(
        environment_check, "resolve_dependency_variant", lambda name: dummy_variant
    )
    monkeypatch.setattr(environment_check, "find_library", lambda name: None)

    result = environment_check._check_opengl_runtime()

    assert result.status == "error"


def test_environment_report_treats_warnings_as_success() -> None:
    """Environment reports remain successful when only warnings are present."""

    report = environment_check.EnvironmentReport(
        python_version="3.13.3",
        platform="linux",
        checks=[
            environment_check.CheckResult(name="Python", status="ok"),
            environment_check.CheckResult(name="OpenGL", status="warning"),
        ],
    )

    assert report.is_successful
