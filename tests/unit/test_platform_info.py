from __future__ import annotations

import platform

from src.common.platform_info import (
    describe_platform,
    format_platform_banner,
    log_platform_context,
)


def test_describe_platform_includes_python_version() -> None:
    details = describe_platform({"script": "unit-test"})

    assert details["python"] == platform.python_version()
    assert details["script"] == "unit-test"


def test_format_platform_banner_contains_required_fields() -> None:
    details = describe_platform({"script": "banner"})
    banner = format_platform_banner(details)

    assert "[platform]" in banner
    assert details["system"] in banner
    assert details["python"] in banner


def test_log_platform_context_emits_banner(capfd) -> None:
    details = log_platform_context({"script": "capture"})
    captured = capfd.readouterr().out

    assert "platform" in captured.lower()
    assert details["script"] == "capture"
