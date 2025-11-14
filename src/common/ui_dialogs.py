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

Дополнительно: прямые вызовы QMessageBox.* теперь патчатся и не блокируют
тесты (автоматический возврат дефолтной кнопки / Ok) — см. _apply_qmessagebox_patch.
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


# ---------------------------------------------------------------------------
# QMessageBox monkeypatch (чтобы прямые вызовы не блокировали тесты)
# ---------------------------------------------------------------------------


def _apply_qmessagebox_patch() -> None:
    """Патчит стандартные методы QMessageBox.* если не было сделано ранее.

    При подавлении диалогов возвращает сразу стандартные ответы без показа окна.
    Это защищает тесты от зависаний при прямых вызовах QMessageBox.question и др.
    """
    force_nonblocking = _env_truthy("PSS_FORCE_NONBLOCKING_DIALOGS")
    suppressed = not dialogs_allowed() or force_nonblocking
    try:
        from PySide6.QtWidgets import QMessageBox  # type: ignore
    except Exception:
        return

    if getattr(QMessageBox, "_pss_patched", False):  # уже пропатчено
        return

    def _log(action: str, title: str, text: str) -> None:
        _logger.info(
            "[UI][patched-%s] %s: %s (suppressed=%s)", action, title, text, suppressed
        )

    # Сохраняем оригиналы
    _orig_information = QMessageBox.information
    _orig_warning = QMessageBox.warning
    _orig_critical = QMessageBox.critical
    _orig_question = QMessageBox.question

    def _wrap_simple(orig_func, action: str):  # type: ignore
        def _wrapped(parent, title, text, *args, **kwargs):
            if not dialogs_allowed() or _env_truthy("PSS_FORCE_NONBLOCKING_DIALOGS"):
                _log(action, title, text)
                return QMessageBox.StandardButton.Ok
            return orig_func(parent, title, text, *args, **kwargs)

        return _wrapped

    def _wrapped_question(
        parent,
        title,
        text,
        buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        defaultButton=QMessageBox.StandardButton.No,
    ):  # type: ignore
        if not dialogs_allowed() or _env_truthy("PSS_FORCE_NONBLOCKING_DIALOGS"):
            _log("question", title, text)
            # Возвращаем defaultButton как выбор пользователя
            return defaultButton
        return _orig_question(parent, title, text, buttons, defaultButton)

    QMessageBox.information = _wrap_simple(_orig_information, "information")  # type: ignore[attr-defined]
    QMessageBox.warning = _wrap_simple(_orig_warning, "warning")  # type: ignore[attr-defined]
    QMessageBox.critical = _wrap_simple(_orig_critical, "critical")  # type: ignore[attr-defined]
    QMessageBox.question = _wrapped_question  # type: ignore[attr-defined]
    QMessageBox._pss_patched = True  # type: ignore[attr-defined]


# Пытаемся применить патч сразу при импорте модуля (без ошибок)
try:  # pragma: no cover - best effort
    _apply_qmessagebox_patch()
except Exception:  # noqa: BLE001
    pass


def ensure_dialog_patching() -> None:
    """Явный вызов из bootstrap при необходимости повторить патч."""
    try:
        _apply_qmessagebox_patch()
    except Exception:  # pragma: no cover
        pass


# ---------------------------------------------------------------------------
# Высокоуровневые удобные обёртки
# ---------------------------------------------------------------------------


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


def message_question(
    parent: Any, title: str, text: str, *, default_yes: bool = False
) -> bool:
    """Показывает вопрос пользователю. Возвращает True для ответа "Да".

    Если диалоги подавлены или активирован принудительный немодальный режим,
    возвращает default_yes и логирует событие.
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
        default = (
            QMessageBox.StandardButton.Yes
            if default_yes
            else QMessageBox.StandardButton.No
        )
        reply = QMessageBox.question(parent, title, text, buttons, default)
        return reply == QMessageBox.StandardButton.Yes
    except Exception:  # pragma: no cover
        _logger.info(
            "[UI][question-fallback] %s: %s -> %s",
            title,
            text,
            default_yes,
            exc_info=True,
        )
        return bool(default_yes)
