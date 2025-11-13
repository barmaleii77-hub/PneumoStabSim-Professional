"""Helpers for coordinating Qt headless and GPU launch environments."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, MutableMapping

HEADLESS_FLAG = "PSS_HEADLESS"
_HEADLESS_TRUTHY = {"1", "true", "yes", "on"}
HEADLESS_DEFAULTS: dict[str, str] = {
    "QT_QPA_PLATFORM": "offscreen",
    # Базовое значение; на Windows переопределяется на RHI ниже
    "QT_QUICK_BACKEND": "software",
    "QT_QUICK_CONTROLS_STYLE": "Basic",
}


def _normalise(value: str | None) -> str:
    return value.strip().lower() if value is not None else ""


def headless_requested(env: Mapping[str, str] | None = None) -> bool:
    """Return ``True`` when ``HEADLESS_FLAG`` is enabled in *env*."""

    environment = env if env is not None else os.environ
    return _normalise(environment.get(HEADLESS_FLAG)) in _HEADLESS_TRUTHY


def apply_headless_defaults(env: MutableMapping[str, str] | None = None) -> None:
    """Apply the standard Qt headless environment overrides.

    На Windows используем RHI + D3D11 вместо программного backend'а, т.к.
    software-путь Qt Quick 3D нестабилен и часто падает при offscreen.
    На Linux/macOS сохраняем программный backend.
    """

    environment = env if env is not None else os.environ
    environment[HEADLESS_FLAG] = "1"
    environment["QT_QPA_PLATFORM"] = "offscreen"

    if sys.platform.startswith("win"):
        environment["QT_QUICK_BACKEND"] = "rhi"
        environment["QSG_RHI_BACKEND"] = "d3d11"
    else:
        environment["QT_QUICK_BACKEND"] = "software"
        # В headless без GPU оставляем выбор Qt, гарантируя отсутствие d3d/metal
        environment.pop("QSG_RHI_BACKEND", None)

    environment.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")


def _preferred_backend(platform_name: str | None = None) -> str:
    platform_key = (platform_name or sys.platform).lower()
    if platform_key.startswith("win"):
        return "d3d11"
    if platform_key.startswith("darwin") or platform_key.startswith("mac"):
        return "metal"
    return "opengl"


def apply_gpu_defaults(
    env: MutableMapping[str, str] | None = None, *, platform_name: str | None = None
) -> None:
    """Normalise *env* for GPU-backed launches when headless mode is disabled."""

    environment = env if env is not None else os.environ
    environment.pop(HEADLESS_FLAG, None)

    if _normalise(environment.get("QT_QPA_PLATFORM")) == "offscreen":
        environment.pop("QT_QPA_PLATFORM", None)
    if _normalise(environment.get("QT_QUICK_BACKEND")) == "software":
        environment.pop("QT_QUICK_BACKEND", None)

    backend = _preferred_backend(platform_name)
    environment.setdefault("QSG_RHI_BACKEND", backend)
    if backend in {"d3d11", "metal"}:
        environment.setdefault("QT_QUICK_BACKEND", "rhi")

    # Ensure any forced QML3D disable flag from prior headless runs is cleared.
    environment.pop("PSS_FORCE_NO_QML_3D", None)


def prepare_launch_environment(
    base: Mapping[str, str] | None = None, *, platform_name: str | None = None
) -> dict[str, str]:
    """Return a launch environment respecting the headless toggle."""

    env = dict(base or os.environ)
    if headless_requested(env):
        apply_headless_defaults(env)
    else:
        apply_gpu_defaults(env, platform_name=platform_name)
    env.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    return env


__all__ = [
    "HEADLESS_FLAG",
    "HEADLESS_DEFAULTS",
    "apply_gpu_defaults",
    "apply_headless_defaults",
    "headless_requested",
    "prepare_launch_environment",
]
