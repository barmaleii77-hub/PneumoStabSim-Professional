"""Utilities supporting graphics bootstrap decisions.

The functions defined here are shared between :mod:`app` bootstrap code and
tests.  They isolate the environment detection heuristics so that platform
selection and headless fallbacks can be validated without importing the full
Qt stack during unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class GraphicsBootstrapState:
    """Снимок параметров графической среды, сформированных на этапе bootstrap.

    Attributes:
        backend: Выбранный графический backend (например, "d3d11", "opengl").
        use_qml_3d: Разрешено ли использовать Qt Quick 3D.
        safe_mode: Включён ли безопасный режим (минимальные требования графики).
        headless: Запуск без графического дисплея/окна.
        headless_reasons: Причины, по которым активирован headless.
    """

    backend: str
    use_qml_3d: bool
    safe_mode: bool
    headless: bool
    headless_reasons: tuple[str, ...]


def _truthy(value: str | None) -> bool:
    """Интерпретировать строку окружения как истину."""

    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def choose_scenegraph_backend(platform: str) -> str:
    """Return the preferred Qt scenegraph backend for ``platform``."""

    normalized = platform.lower()
    if normalized.startswith("win"):
        return "d3d11"
    if normalized.startswith("darwin") or normalized.startswith("mac"):
        return "metal"
    return "opengl"


def detect_headless_environment(env: Mapping[str, str]) -> tuple[bool, tuple[str, ...]]:
    """Determine headless mode triggers and return reasons."""

    if _truthy(env.get("PSS_HEADLESS")):
        return True, ("flag:pss-headless",)

    reasons: list[str] = []
    qpa = (env.get("QT_QPA_PLATFORM") or "").strip().lower()
    display_present = bool(env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"))

    if _truthy(env.get("CI")):
        reasons.append("ci-flag")

    if not qpa:
        if not display_present:
            reasons.append("no-display-server")
            reasons.append("qt-qpa-platform-missing")
    elif qpa in {"offscreen", "minimal", "minimal:tools=auto"}:
        reasons.append(f"qt-qpa-platform:{qpa}")

    headless = bool(reasons)
    return headless, tuple(reasons)


def bootstrap_graphics_environment(
    env: Mapping[str, str],
    *,
    platform: str,
    safe_mode: bool,
) -> GraphicsBootstrapState:
    """Определение графической среды без агрессивного headless на Windows.

    Правки:
    - Windows больше NO помечается headless по косвенным признакам.
    - Headless на Windows только при:
        * PSS_HEADLESS=1 (или аналогичных truthy),
        * QT_QPA_PLATFORM=offscreen (явно задан пользователем/окружением).
    - На Unix: headless при отсутствии DISPLAY/WAYLAND_DISPLAY, либо при offscreen.
    - ``use_qml_3d`` выключается только при реальном headless или в ``safe_mode``.
    """

    headless, reasons = detect_headless_environment(env)

    if headless:
        if not env.get("QT_QPA_PLATFORM"):
            env["QT_QPA_PLATFORM"] = "offscreen"
        env["PSS_FORCE_NO_QML_3D"] = "1"

    backend = env.get("QSG_RHI_BACKEND") or ""
    chosen_backend = choose_scenegraph_backend(platform)
    if not safe_mode and not backend:
        env["QSG_RHI_BACKEND"] = chosen_backend
        backend = chosen_backend
    elif not backend:
        backend = chosen_backend

    use_qml_3d = not headless
    return GraphicsBootstrapState(
        backend=backend,
        use_qml_3d=use_qml_3d,
        safe_mode=safe_mode,
        headless=headless,
        headless_reasons=reasons,
    )


def enforce_fixed_window_metrics(window, *, width: int, height: int) -> None:
    """Fix the Qt window size to stable metrics for screenshots/tests."""

    # Prefer explicit bounds to avoid implicit resizes when window decorations
    # change between platforms or when HiDPI scaling is applied.
    if hasattr(window, "setMinimumWidth"):
        window.setMinimumWidth(width)
    if hasattr(window, "setMaximumWidth"):
        window.setMaximumWidth(width)
    if hasattr(window, "setMinimumHeight"):
        window.setMinimumHeight(height)
    if hasattr(window, "setMaximumHeight"):
        window.setMaximumHeight(height)

    if hasattr(window, "setWidth"):
        window.setWidth(width)
    if hasattr(window, "setHeight"):
        window.setHeight(height)
