"""Platform detection helpers shared across entrypoint scripts.

The module provides a small surface area for emitting consistent platform
diagnostics across Linux and Windows runners. Scripts can import the
helpers without configuring logging; they emit to both ``structlog`` and
stdout so that CI logs and local consoles stay aligned.
"""

from __future__ import annotations

import platform
import sys
from typing import Mapping

import structlog


def describe_platform(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a normalized platform description for diagnostics."""

    description = {
        "system": platform.system() or "unknown",
        "release": platform.release() or "",
        "version": platform.version() or "",
        "python": platform.python_version(),
        "executable": sys.executable,
    }
    if extra:
        description.update({k: v for k, v in extra.items() if v})
    return description


def format_platform_banner(details: Mapping[str, str]) -> str:
    """Render a short, user-friendly banner string from platform details."""

    system = details.get("system") or "unknown"
    release = details.get("release") or ""
    python_version = details.get("python") or platform.python_version()
    suffix = f" {release}" if release else ""
    return f"[platform] {system}{suffix} | Python {python_version}"


def log_platform_context(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """Log the platform context via structlog and stdout."""

    details = describe_platform(extra)
    banner = format_platform_banner(details)
    structlog.get_logger(__name__).info("platform.detected", **details)
    print(banner)
    return details
