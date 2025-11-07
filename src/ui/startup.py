"""Utilities supporting graphics bootstrap decisions.

The functions defined here are shared between :mod:`app` bootstrap code and
tests.  They isolate the environment detection heuristics so that platform
selection and headless fallbacks can be validated without importing the full
Qt stack during unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from collections.abc import Mapping, MutableMapping


_TRUTHY_VALUES = {"1", "true", "yes", "on"}


def _is_truthy(value: str | None) -> bool:
    """Return ``True`` for common truthy environment string values."""

    if value is None:
        return False
    return value.strip().lower() in _TRUTHY_VALUES


def choose_scenegraph_backend(platform: str) -> str:
    """Return the preferred Qt Quick Scene Graph backend for ``platform``."""

    normalised = platform.lower()
    if normalised.startswith("win"):
        return "d3d11"
    if normalised.startswith("darwin") or normalised.startswith("mac"):
        return "metal"
    if normalised.startswith("linux"):
        return "opengl"
    return "opengl"


def detect_headless_environment(env: Mapping[str, str]) -> tuple[bool, tuple[str, ...]]:
    """Detect whether the current process should consider itself headless.

    Parameters
    ----------
    env:
        Environment mapping to inspect.  ``os.environ`` is passed at runtime but
        the mapping can be substituted in tests.
    """

    reasons: list[str] = []

    if _is_truthy(env.get("CI")):
        reasons.append("ci-flag")

    qt_qpa = (env.get("QT_QPA_PLATFORM") or "").strip().lower()
    has_display = bool(env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"))
    if qt_qpa in {"offscreen", "minimal", "minimalgl", "vkkhrdisplay"}:
        reasons.append(f"qt-qpa-platform:{qt_qpa}")
    elif not qt_qpa and not has_display:
        reasons.append("qt-qpa-platform-missing")

    return bool(reasons), tuple(reasons)


@dataclass(frozen=True)
class GraphicsEnvironmentDecision:
    """Outcome of the graphics bootstrap phase."""

    backend: str
    headless: bool
    headless_reasons: tuple[str, ...]
    safe_mode: bool


def bootstrap_graphics_environment(
    env: MutableMapping[str, str], *, platform: str, safe_mode: bool
) -> GraphicsEnvironmentDecision:
    """Prepare environment variables for Qt graphics initialisation."""

    backend = choose_scenegraph_backend(platform)
    headless, reasons = detect_headless_environment(env)

    if headless:
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["PSS_FORCE_NO_QML_3D"] = "1"
    else:
        env.pop("PSS_FORCE_NO_QML_3D", None)

    if not safe_mode:
        env["QSG_RHI_BACKEND"] = backend

    return GraphicsEnvironmentDecision(
        backend=backend,
        headless=headless,
        headless_reasons=reasons,
        safe_mode=safe_mode,
    )


__all__ = [
    "GraphicsEnvironmentDecision",
    "bootstrap_graphics_environment",
    "choose_scenegraph_backend",
    "detect_headless_environment",
]
