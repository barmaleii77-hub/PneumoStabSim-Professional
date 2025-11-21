"""UI Setup Module - MainWindow UI construction

Модуль построения UI элементов главного окна.
Отвечает за создание всех виджетов, сплиттеров, панелей и их расположение.

Russian UI / English code.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping

from PySide6.QtCore import Qt, QSettings, QUrl, qVersion
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface, QQuickView
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtGui import QAction, QKeySequence, QSurfaceFormat

from src.common.settings_manager import get_settings_event_bus, get_settings_manager
from src.ui.bridge import TrainingPresetBridge
from src.ui.panels.lighting import LightingSettingsBridge, LightingSettingsFacade
from src.ui.panels.modes.defaults import (
    DEFAULT_MODES_PARAMS,
    DEFAULT_PHYSICS_OPTIONS,
    MODE_PRESETS,
    PARAMETER_RANGES,
)

if TYPE_CHECKING:
    from .main_window_refactored import MainWindow


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QML_RELATIVE_ROOT = Path("assets") / "qml"
QML_ABSOLUTE_ROOT = PROJECT_ROOT / QML_RELATIVE_ROOT
SHADER_ROOT = PROJECT_ROOT / "assets" / "shaders"
EFFECT_SHADER_DIR = SHADER_ROOT / "effects"
EFFECT_SHADER_DIRS: tuple[Path, ...] = (EFFECT_SHADER_DIR,)

_SCENE_SUSPENSION_REQUIRED_KEYS: tuple[str, ...] = ("rod_warning_threshold_m",)
_SCENE_SUSPENSION_DEFAULTS: dict[str, float] = {"rod_warning_threshold_m": 0.001}
_SCENE_REQUIRED_KEYS: tuple[str, ...] = (
    "scale_factor",
    "exposure",
    "default_clear_color",
    "model_base_color",
    "model_roughness",
    "model_metalness",
)
_SCENE_FLOAT_KEYS: tuple[str, ...] = (
    "scale_factor",
    "exposure",
    "model_roughness",
    "model_metalness",
)
_SCENE_DEFAULTS: dict[str, Any] = {
    "scale_factor": 1.0,
    "exposure": 1.0,
    "default_clear_color": "#1b1f27",
    "model_base_color": "#9da3aa",
    "model_roughness": 0.42,
    "model_metalness": 0.82,
}


class UISetup:
    """Построение UI элементов главного окна

    Static methods для делегирования из MainWindow.
    Каждый метод принимает `window: MainWindow` как первый аргумент.
    """

    logger = logging.getLogger(__name__)

    _SUPPORTED_SCENES: dict[str, Path] = {
        "main": QML_ABSOLUTE_ROOT / "main.qml",
        "realism": QML_ABSOLUTE_ROOT / "main_v2_realism.qml",
        "fallback": QML_ABSOLUTE_ROOT / "main_fallback.qml",
    }
    # Предпочитаем реалистичную сцену по умолчанию, чтобы избежать пустого канваса
    _SCENE_LOAD_ORDER: tuple[str, ...] = ("realism", "main", "fallback")
    _SCENE_ENV_VAR = "PSS_QML_SCENE"
    _POST_DIAG_ENV = "PSS_POST_DIAG_TRACE"

    @staticmethod
    def _build_effect_shader_manifest() -> dict[str, dict[str, Any]]:
        """Return a manifest of effect shader files available on disk."""

        manifest: dict[str, dict[str, Any]] = {}

        for directory in EFFECT_SHADER_DIRS:
            try:
                for path in directory.iterdir():
                    if not path.is_file():
                        continue
                    if path.suffix.lower() not in {".frag", ".vert"}:
                        continue

                    try:
                        relative_path = path.relative_to(SHADER_ROOT)
                        relative_key = relative_path.as_posix()
                    except ValueError:
                        relative_key = path.name

                    entry = manifest.get(path.name)
                    if entry is None:
                        manifest[path.name] = {
                            "enabled": True,
                            "path": relative_key,
                            "paths": [relative_key],
                        }
                        continue

                    entry.setdefault("enabled", True)
                    entry_paths = entry.setdefault("paths", [])
                    if relative_key not in entry_paths:
                        entry_paths.append(relative_key)
                    entry.setdefault("path", relative_key)
            except FileNotFoundError:
                UISetup.logger.error(
                    "    ❌ Effect shader directory missing: %s", directory
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                UISetup.logger.warning(
                    "    ⚠️ Unable to enumerate effect shaders at %s: %s",
                    directory,
                    exc,
                )

        return manifest

    @staticmethod
    def _register_postmortem_reason(reason: str) -> None:
        """Зафиксировать причину обязательного пост-анализа логов."""

        try:
            normalized = (reason or "").strip()
            if not normalized:
                return

            existing = os.environ.get(UISetup._POST_DIAG_ENV, "")
            parts = [item for item in existing.split("|") if item]
            if normalized not in parts:
                parts.append(normalized)
            os.environ[UISetup._POST_DIAG_ENV] = "|".join(parts)
        except Exception as exc:  # pragma: no cover - логируем, но не прерываем
            UISetup.logger.debug(
                "    ⚠️ Не удалось зафиксировать причину пост-анализа: %s", exc
            )

    @staticmethod
    def build_qml_context_payload(
        settings_manager: Any | None,
    ) -> dict[str, dict[str, Any]]:
        """Подготовить стартовые словари для QML контекста.

        Дополнительная нормализация: обеспечиваем наличие ключей
        `ibl_lighting_enabled` и `ibl_master_enabled` в scene.environment
        чтобы интеграционные тесты SceneEnvironmentController видели ожидаемые
        флаги даже если конфигурация их не содержит (обратная совместимость).
        """

        manager = settings_manager
        if manager is None:
            try:
                manager = get_settings_manager()
            except Exception as exc:
                UISetup.logger.exception(
                    "    ❌ Не удалось получить SettingsManager: %s", exc
                )
                UISetup._register_postmortem_reason("settings-manager-unavailable")
                raise RuntimeError(
                    "SettingsManager недоступен. Проверьте загрузку конфигурации."
                ) from exc

        if manager is None:
            UISetup._register_postmortem_reason("settings-manager-not-initialized")
            raise RuntimeError(
                "SettingsManager не был инициализирован. Остановлена загрузка QML."
            )

        def _serialize(section: str, payload: dict[str, Any]) -> dict[str, Any]:
            try:
                return json.loads(json.dumps(payload))
            except (TypeError, ValueError) as exc:
                UISetup.logger.error(
                    "    ❌ Настройки %s содержат несериализуемые значения: %s",
                    section,
                    exc,
                )
                UISetup._register_postmortem_reason(
                    f"settings-serialization-failed:{section}"
                )
                raise RuntimeError(
                    f"Настройки {section} содержат неподдерживаемые данные"
                ) from exc

        def _read_section(name: str) -> dict[str, Any]:
            path = name if name == "animation" else f"graphics.{name}"
            try:
                data = manager.get(path, {})
            except Exception:
                data = {}
            if not isinstance(data, dict):
                return {}
            return data

        # Read sections -------------------------------------------------
        scene_payload = _read_section("scene")
        # Normalize expected environment flags for tests
        env_payload = scene_payload.get("environment")
        if isinstance(env_payload, dict):
            # ibl_lighting_enabled falls back to ibl_enabled if absent
            if (
                "ibl_lighting_enabled" not in env_payload
                and "ibl_enabled" in env_payload
            ):
                env_payload["ibl_lighting_enabled"] = bool(
                    env_payload.get("ibl_enabled")
                )
            # ibl_master_enabled: master OR skybox (default True when skybox enabled)
            if "ibl_master_enabled" not in env_payload:
                env_payload["ibl_master_enabled"] = bool(
                    env_payload.get("ibl_enabled", False)
                    or env_payload.get("skybox_enabled", True)
                )
        else:
            # If whole environment block missing create minimal defaults
            scene_payload["environment"] = {
                "background_mode": "skybox",
                "skybox_enabled": True,
                "ibl_enabled": True,
                "ibl_lighting_enabled": True,
                "ibl_master_enabled": True,
            }

        geometry_payload = _read_section("geometry")
        animation_payload = _read_section("animation")
        lighting_payload = _read_section("lighting")
        quality_payload = _read_section("quality")
        camera_payload = _read_section("camera")
        effects_payload = _read_section("effects")
        materials_payload = _read_section("materials")
        diagnostics_payload = _read_section("diagnostics")

        payload: dict[str, dict[str, Any]] = {
            "scene": _serialize("scene", scene_payload),
            "geometry": _serialize("geometry", geometry_payload),
            "animation": _serialize("animation", animation_payload),
            "lighting": _serialize("lighting", lighting_payload),
            "quality": _serialize("quality", quality_payload),
            "camera": _serialize("camera", camera_payload),
            "effects": _serialize("effects", effects_payload),
            "materials": _serialize("materials", materials_payload),
            "diagnostics": _serialize("diagnostics", diagnostics_payload),
        }

        return payload


__all__ = ["UISetup"]
