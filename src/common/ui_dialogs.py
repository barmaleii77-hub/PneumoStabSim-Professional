"""
Утилиты для безопасного показа модальных диалогов в Qt.

Цель: не блокировать автотесты и headless-окружения модальными окнами.
Использование:
- dialogs_allowed() -> bool — можно ли показывать модальные окна сейчас
- message_info/warning/critical/question — обёртки над QMessageBox

Правила подавления диалогов:
- Переменная окружения PSS_SUPPRESS_UI_DIALOGS в значениях {1, true, yes, on}
- Тестовая среда (PYTEST_CURRENT_TEST) или CI (CI=true)
- Отсутствует QApplication или платформа headless/offscreen/minimal
- Приложение выставило флаг QApplication.is_headless = True
- Принудительное немодальное подтверждение: PSS_FORCE_NONBLOCKING_DIALOGS
"""

from __future__ import annotations

from typing import Any
import logging
import os

_logger = logging.getLogger(__name__)


def _env_truthy(name: str) -> bool:
    value = os.environ.get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def dialogs_allowed() -> bool:
    """Вернуть True, если показ модальных QMessageBox допустим.

    Проверяет переменные окружения и состояние QApplication, чтобы избежать
    блокирующих окон в headless/CI/pytest окружениях.
    """

    # Явные флаги подавления из окружения
    if _env_truthy("PSS_SUPPRESS_UI_DIALOGS"):
        return False
    # Принудительный немодальный режим — полностью запрещаем модальные окна
    if _env_truthy("PSS_FORCE_NONBLOCKING_DIALOGS"):
        return False
    # Явный headless-пресет окружения
    if _env_truthy("PSS_HEADLESS"):
        return False

    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    if _env_truthy("CI"):
        return False

    try:
        from PySide6.QtWidgets import QApplication  # type: ignore
    except Exception:
        return False

    app = QApplication.instance()
    if app is None:
        return False

    platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    if platform in {"offscreen", "minimal", "headless"}:
        return False

    if bool(getattr(app, "is_headless", False)):
        return False

    return True


def message_info(parent: Any, title: str, text: str) -> None:
    if not dialogs_allowed():
        _logger.info("[UI] %s: %s", title, text)
        return
    try:
        from PySide6.QtWidgets import QMessageBox  # type: ignore
        QMessageBox.information(parent, title, text)
    except Exception:  # pragma: no cover
        _logger.info("[UI][fallback] %s: %s", title, text, exc_info=True)


def message_warning(parent: Any, title: str, text: str) -> None:
    if not dialogs_allowed():
        _logger.warning("[UI] %s: %s", title, text)
        return
    try:
        from PySide6.QtWidgets import QMessageBox  # type: ignore
        QMessageBox.warning(parent, title, text)
    except Exception:  # pragma: no cover
        _logger.warning("[UI][fallback] %s: %s", title, text, exc_info=True)


def message_critical(parent: Any, title: str, text: str) -> None:
    if not dialogs_allowed():
        _logger.error("[UI] %s: %s", title, text)
        return
    try:
        from PySide6.QtWidgets import QMessageBox  # type: ignore
        QMessageBox.critical(parent, title, text)
    except Exception:  # pragma: no cover
        _logger.error("[UI][fallback] %s: %s", title, text, exc_info=True)


def message_question(parent: Any, title: str, text: str, *, default_yes: bool = False) -> bool:
    """Показывает вопрос пользователю. Возвращает True для ответа "Да".

    Если диалоги подавлены или активирован принудительный немодальный режим,
    возвращает default_yes и логирует событие. Принудительный режим включается
    переменной окружения PSS_FORCE_NONBLOCKING_DIALOGS.
    """
    force_nonblocking = _env_truthy("PSS_FORCE_NONBLOCKING_DIALOGS")
    if force_nonblocking:
        _logger.info(
            "[UI][question-nonblocking] %s: %s -> %s (forced)",
            title,
            text,
            default_yes,
        )
        return bool(default_yes)

    if not dialogs_allowed():
        _logger.info("[UI][question-suppressed] %s: %s -> %s", title, text, default_yes)
        return bool(default_yes)
    try:
        from PySide6.QtWidgets import QMessageBox  # type: ignore
        buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        default = QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No
        reply = QMessageBox.question(parent, title, text, buttons, default)
        return reply == QMessageBox.StandardButton.Yes
    except Exception:  # pragma: no cover
        _logger.info("[UI][question-fallback] %s: %s -> %s", title, text, default_yes, exc_info=True)
        return bool(default_yes)
