"""Helpers for coordinating Qt headless configuration in tests."""

from __future__ import annotations

import os
import sys
from collections.abc import MutableMapping

HEADLESS_FLAG = "PSS_HEADLESS"
_TRUTHY = {"1", "true", "yes", "on"}
HEADLESS_DEFAULTS: dict[str, str] = {
    "QT_QPA_PLATFORM": "offscreen",
    # Значения по умолчанию для Linux/macOS; на Windows переопределяются в apply_headless_defaults
    "QT_QUICK_BACKEND": "software",
    "QT_QUICK_CONTROLS_STYLE": "Basic",
}


def _normalise(value: str | None) -> str:
    return value.strip().lower() if value is not None else ""


def headless_requested(env: MutableMapping[str, str] | None = None) -> bool:
    """Return ``True`` when the caller requested headless Qt defaults."""

    environment = env if env is not None else os.environ
    return _normalise(environment.get(HEADLESS_FLAG)) in _TRUTHY


def apply_headless_defaults(env: MutableMapping[str, str] | None = None) -> None:
    """Ensure Qt headless defaults are set in ``env``.

    На Windows Qt Quick 3D в софтверном режиме («software») падает чаще, чем в RHI/D3D11,
    поэтому в headless-тестах принудительно используем D3D11. Для Linux/macOS сохраняем
    программный рендер.
    """

    environment = env if env is not None else os.environ
    environment[HEADLESS_FLAG] = "1"
    environment["QT_QPA_PLATFORM"] = "offscreen"

    if sys.platform.startswith("win"):
        # Headless Windows: RHI + D3D11
        environment["QT_QUICK_BACKEND"] = "rhi"
        environment["QSG_RHI_BACKEND"] = "d3d11"
    else:
        # Linux/macOS: программный backend
        environment["QT_QUICK_BACKEND"] = "software"
        environment.pop("QSG_RHI_BACKEND", None)

    environment.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")


__all__ = [
    "HEADLESS_FLAG",
    "HEADLESS_DEFAULTS",
    "apply_headless_defaults",
    "headless_requested",
]
