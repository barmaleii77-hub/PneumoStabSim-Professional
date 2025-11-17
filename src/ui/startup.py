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

    is_windows = platform.startswith("win")

    qpa = (env.get("QT_QPA_PLATFORM") or "").strip().lower()
    user_forced_offscreen = qpa in {"offscreen", "minimal", "minimal:tools=auto"}

    explicit_headless = (
        _truthy(env.get("PSS_HEADLESS"))
        or _truthy(env.get("CI"))
        or _truthy(env.get("GITHUB_ACTIONS"))
    )

    headless = False
    reasons: list[str] = []

    if is_windows:
        # На Windows headless только по явному сигналу пользователя/окружения
        if explicit_headless:
            headless = True
            reasons.append("user-requested")
        elif user_forced_offscreen:
            headless = True
            reasons.append("qt-qpa-offscreen")
        # иначе — считаем интерактивный режим
    else:
        # Unix: нет дисплея => headless, либо явный offscreen
        display_present = bool(env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"))
        if explicit_headless:
            headless = True
            reasons.append("user-requested")
        elif user_forced_offscreen:
            headless = True
            reasons.append("qt-qpa-offscreen")
        elif not display_present:
            headless = True
            reasons.append("no-display-server")

    # Выбор backend по умолчанию
    backend = (env.get("QSG_RHI_BACKEND") or "").strip().lower()
    if not backend:
        backend = "d3d11" if is_windows else "opengl"

    # QML 3D доступен только вне safe_mode и не в headless
    use_qml_3d = not safe_mode and not headless

    return GraphicsBootstrapState(
        backend=backend,
        use_qml_3d=use_qml_3d,
        safe_mode=safe_mode,
        headless=headless,
        headless_reasons=tuple(reasons),
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
