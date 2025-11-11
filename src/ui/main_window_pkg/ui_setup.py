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
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
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
    _SCENE_LOAD_ORDER: tuple[str, ...] = ("main", "realism", "fallback")
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
        """Подготовить стартовые словари для QML контекста."""

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
                data = manager.get(path, None)
            except Exception as exc:
                UISetup.logger.exception("    ❌ Ошибка чтения %s: %s", path, exc)
                UISetup._register_postmortem_reason(f"settings-read-error:{path}")
                raise RuntimeError(f"Не удалось прочитать настройки {path}") from exc
            if not isinstance(data, dict) or not data:
                UISetup._register_postmortem_reason(f"settings-missing:{path}")
                raise RuntimeError(f"Настройки {path} отсутствуют или повреждены")
            return _serialize(path, data)

        def _read_geometry() -> dict[str, Any]:
            try:
                payload = manager.get_category("geometry") or {}
            except Exception as exc:
                UISetup.logger.exception("    ❌ Ошибка чтения geometry: %s", exc)
                UISetup._register_postmortem_reason("settings-read-error:geometry")
                raise RuntimeError("Не удалось прочитать настройки geometry") from exc

            if not isinstance(payload, dict) or not payload:
                UISetup._register_postmortem_reason("settings-missing:geometry")
                raise RuntimeError("Секция geometry отсутствует или повреждена")

            return _serialize("geometry", payload)

        def _read_diagnostics() -> dict[str, Any]:
            try:
                payload = manager.get("diagnostics", {}) or {}
            except Exception as exc:
                UISetup.logger.exception("    ❌ Ошибка чтения diagnostics: %s", exc)
                UISetup._register_postmortem_reason("settings-read-error:diagnostics")
                raise RuntimeError("Не удалось прочитать diagnostics") from exc
            if not isinstance(payload, dict):
                UISetup._register_postmortem_reason("settings-missing:diagnostics")
                raise RuntimeError("Секция diagnostics повреждена")
            return _serialize("diagnostics", payload)

        reflection_required_keys: tuple[str, ...] = (
            "enabled",
            "padding_m",
            "quality",
            "refresh_mode",
            "time_slicing",
        )

        reflection_defaults: dict[str, Any] = {
            "enabled": False,
            "padding_m": 0.15,
            "quality": "veryhigh",
            "refresh_mode": "everyframe",
            "time_slicing": "individualfaces",
        }

        def _coerce_bool(value: Any) -> bool | None:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"1", "true", "yes", "on"}:
                    return True
                if lowered in {"0", "false", "no", "off"}:
                    return False
            return None

        def _coerce_number(value: Any) -> float | None:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.strip())
                except ValueError:
                    return None
            return None

        def _coerce_text(value: Any, *, lowercase: bool = False) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                text = value.strip()
            else:
                text = str(value).strip()
            if not text:
                return None
            return text.lower() if lowercase else text

        def _map_environment_to_reflection(
            payload: Mapping[str, Any] | None,
        ) -> dict[str, Any]:
            if not isinstance(payload, Mapping):
                return {}
            return {
                "enabled": payload.get("reflection_enabled"),
                "padding_m": payload.get("reflection_padding_m"),
                "quality": payload.get("reflection_quality"),
                "refresh_mode": payload.get("reflection_refresh_mode"),
                "time_slicing": payload.get("reflection_time_slicing"),
            }

        def _sanitize_reflection_probe(
            primary: Mapping[str, Any] | None,
            fallbacks: Iterable[Mapping[str, Any] | None],
        ) -> tuple[dict[str, Any], list[str]]:
            result: dict[str, Any] = {}
            missing: list[str] = []

            def _seek_value(
                key: str,
                extractor: Callable[[Any], Any | None],
                lowercase: bool = False,
            ) -> tuple[Any, bool]:
                primary_value = None
                if isinstance(primary, Mapping) and key in primary:
                    primary_value = extractor(primary[key])
                if primary_value is not None:
                    return (
                        primary_value.lower()
                        if lowercase and isinstance(primary_value, str)
                        else primary_value,
                        False,
                    )

                for source in fallbacks:
                    if not isinstance(source, Mapping):
                        continue
                    candidate = source.get(key)
                    if candidate is None:
                        continue
                    coerced = extractor(candidate)
                    if coerced is not None:
                        return (
                            coerced.lower()
                            if lowercase and isinstance(coerced, str)
                            else coerced,
                            True,
                        )
                return (None, True)

            for key in reflection_required_keys:
                if key == "enabled":
                    value, used_fallback = _seek_value(key, _coerce_bool)
                elif key == "padding_m":
                    value, used_fallback = _seek_value(key, _coerce_number)
                else:
                    value, used_fallback = _seek_value(
                        key,
                        lambda raw: _coerce_text(raw, lowercase=True),
                        lowercase=True,
                    )

                if value is None:
                    value = reflection_defaults[key]
                    used_fallback = True

                if used_fallback:
                    missing.append(key)

                result[key] = value

            result["padding"] = float(result["padding_m"])
            return result, missing

        def _read_reflection_probe(
            environment_payload: Mapping[str, Any],
        ) -> tuple[dict[str, Any], list[str]]:
            try:
                raw_payload = manager.get("graphics.reflection_probe", None) or {}
            except Exception as exc:
                UISetup.logger.warning(
                    "    ⚠️ Ошибка чтения graphics.reflection_probe: %s", exc
                )
                raw_payload = {}

            if not isinstance(raw_payload, Mapping):
                UISetup.logger.warning(
                    "    ⚠️ graphics.reflection_probe имеет неверный тип (%s); используется fallback.",
                    type(raw_payload).__name__,
                )
                raw_payload = {}

            fallback_sources: list[Mapping[str, Any]] = []
            fallback_sources.append(_map_environment_to_reflection(environment_payload))

            try:
                snapshot_probe = (
                    manager.get("defaults_snapshot.graphics.reflection_probe", {}) or {}
                )
            except Exception as exc:
                UISetup.logger.debug(
                    "    ⚠️ Не удалось прочитать defaults_snapshot.graphics.reflection_probe: %s",
                    exc,
                )
                snapshot_probe = {}
            if isinstance(snapshot_probe, Mapping):
                fallback_sources.append(snapshot_probe)

            try:
                snapshot_env = (
                    manager.get("defaults_snapshot.graphics.environment", {}) or {}
                )
            except Exception:
                snapshot_env = {}
            fallback_sources.append(_map_environment_to_reflection(snapshot_env))

            sanitized, missing = _sanitize_reflection_probe(
                raw_payload, fallback_sources
            )
            unique_missing = sorted(
                {key for key in missing if key in reflection_required_keys}
            )
            return sanitized, unique_missing

        def _ensure_scene_suspension(scene_payload: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(scene_payload, dict):
                return {}

            def _fallback_section(path: str) -> dict[str, Any]:
                try:
                    payload = manager.get(path, {}) or {}
                except Exception as exc:  # pragma: no cover - defensive logging
                    UISetup.logger.debug(
                        "    ⚠️ Failed to read %s for scene defaults: %s", path, exc
                    )
                    return {}
                return payload if isinstance(payload, dict) else {}

            fallback_sources: list[dict[str, Any]] = []
            metadata_defaults = _fallback_section("metadata.scene_defaults")
            suspension_defaults = metadata_defaults.get("suspension")
            if isinstance(suspension_defaults, dict):
                fallback_sources.append(suspension_defaults)

            snapshot_scene = _fallback_section("defaults_snapshot.graphics.scene")
            snapshot_suspension = snapshot_scene.get("suspension")
            if isinstance(snapshot_suspension, dict):
                fallback_sources.append(snapshot_suspension)

            raw_suspension = scene_payload.get("suspension")
            normalised_suspension: dict[str, Any] = {}
            if isinstance(raw_suspension, dict):
                normalised_suspension.update(raw_suspension)
            else:
                if raw_suspension is not None:
                    UISetup.logger.warning(
                        "    ⚠️ Scene settings 'suspension' section has invalid type (%s); "
                        "using defaults.",
                        type(raw_suspension).__name__,
                    )
                else:
                    UISetup.logger.warning(
                        "    ⚠️ Scene settings missing 'suspension' section; applying defaults."
                    )

            missing_keys: list[str] = []
            for key in _SCENE_SUSPENSION_REQUIRED_KEYS:
                value = normalised_suspension.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    normalised_suspension[key] = float(value)
                    continue

                for fallback in fallback_sources:
                    candidate = fallback.get(key)
                    if isinstance(candidate, (int, float)) and not isinstance(
                        candidate, bool
                    ):
                        normalised_suspension[key] = float(candidate)
                        break

                if key not in normalised_suspension:
                    normalised_suspension[key] = float(
                        _SCENE_SUSPENSION_DEFAULTS.get(key, 0.0)
                    )
                    missing_keys.append(key)

            if missing_keys:
                UISetup.logger.warning(
                    "    ⚠️ Scene suspension settings missing keys: %s. Using defaults.",
                    ", ".join(sorted(missing_keys)),
                )

            result = dict(scene_payload)
            result["suspension"] = normalised_suspension
            return result

        animation_payload = _read_section("animation")
        scene_payload = _ensure_scene_suspension(_read_section("scene"))
        materials_payload = _read_section("materials")
        environment_payload = _read_section("environment")
        effects_payload = _read_section("effects")
        quality_payload = _read_section("quality")
        lighting_payload = _read_section("lighting")
        reflection_probe_payload, missing_reflection_keys = _read_reflection_probe(
            environment_payload
        )

        if missing_reflection_keys:
            UISetup.logger.warning(
                "    ⚠️ Reflection probe settings missing keys: %s. Используются значения из fallback.",
                ", ".join(missing_reflection_keys),
            )

        modes_payload = manager.get_category("modes") or {}
        pneumatic_payload = manager.get_category("pneumatic") or {}
        simulation_payload = manager.get_category("simulation") or {}
        cylinder_payload = manager.get("current.constants.geometry.cylinder", {}) or {}

        def _serialize_mapping(section: str, payload: dict[str, Any]) -> dict[str, Any]:
            if not payload:
                return {}
            return _serialize(section, payload)

        def _make_preset_id(name: str, index: int) -> str:
            token = (name or f"preset_{index}").strip().lower()
            normalized = [ch if ch.isalnum() else "_" for ch in token]
            collapsed = "".join(normalized)
            while "__" in collapsed:
                collapsed = collapsed.replace("__", "_")
            return collapsed.strip("_") or f"preset_{index}"

        preset_entries: list[dict[str, Any]] = []
        for preset_index, preset_payload in MODE_PRESETS.items():
            entry = {key: value for key, value in preset_payload.items()}
            entry["index"] = int(preset_index)
            entry["id"] = _make_preset_id(
                str(preset_payload.get("name", "")), int(preset_index)
            )
            preset_entries.append(_serialize("modes.preset", entry))

        modes_metadata = {
            "presets": preset_entries,
            "defaults": _serialize("modes.defaults", DEFAULT_MODES_PARAMS),
            "physicsDefaults": _serialize(
                "modes.physics.defaults", DEFAULT_PHYSICS_OPTIONS
            ),
            "parameterRanges": _serialize("modes.parameter_ranges", PARAMETER_RANGES),
        }

        composed_scene: dict[str, Any] = dict(scene_payload)
        composed_scene.update(
            {
                "materials": materials_payload,
                "environment": environment_payload,
                "effects": effects_payload,
                "quality": quality_payload,
                "lighting": lighting_payload,
                "reflection_probe": reflection_probe_payload,
                "graphics": {
                    "scene": scene_payload,
                    "materials": materials_payload,
                    "environment": environment_payload,
                    "reflection_probe": reflection_probe_payload,
                    "effects": effects_payload,
                    "quality": quality_payload,
                    "lighting": lighting_payload,
                },
            }
        )

        return {
            "animation": animation_payload,
            "scene": _serialize("graphics.scene", composed_scene),
            "materials": materials_payload,
            "geometry": _read_geometry(),
            "diagnostics": _read_diagnostics(),
            "reflection_probe": _serialize(
                "graphics.reflection_probe", reflection_probe_payload
            ),
            "lighting": _serialize_mapping("graphics.lighting", lighting_payload),
            "effects": _serialize_mapping("graphics.effects", effects_payload),
            "quality": _serialize_mapping("graphics.quality", quality_payload),
            "environment": _serialize_mapping(
                "graphics.environment", environment_payload
            ),
            "modes": _serialize_mapping("modes", modes_payload),
            "pneumatic": _serialize_mapping("pneumatic", pneumatic_payload),
            "simulation": _serialize_mapping("simulation", simulation_payload),
            "cylinder": _serialize_mapping(
                "constants.geometry.cylinder", cylinder_payload
            ),
            "modes_metadata": modes_metadata,
        }

    @staticmethod
    def _graphics_api_to_string(api: QSGRendererInterface.GraphicsApi) -> str:
        """Convert ``QSGRendererInterface.GraphicsApi`` to a readable label."""

        mapping: dict[QSGRendererInterface.GraphicsApi, str] = {
            QSGRendererInterface.GraphicsApi.Unknown: "unknown",
            QSGRendererInterface.GraphicsApi.Software: "software",
            QSGRendererInterface.GraphicsApi.OpenGL: "opengl",
            QSGRendererInterface.GraphicsApi.OpenGLRhi: "opengl-rhi",
            QSGRendererInterface.GraphicsApi.Direct3D11: "direct3d11",
            QSGRendererInterface.GraphicsApi.Vulkan: "vulkan",
            QSGRendererInterface.GraphicsApi.Metal: "metal",
            QSGRendererInterface.GraphicsApi.Null: "null",
        }
        if api in mapping:
            return mapping[api]

        fallback: str
        value = getattr(api, "value", None)
        if value is not None:
            fallback = str(value)
        else:
            try:
                fallback = str(int(api))
            except (TypeError, ValueError):
                fallback = str(api)

        return f"unknown({fallback})"

    @staticmethod
    def _graphics_api_requires_desktop_shaders(
        api: QSGRendererInterface.GraphicsApi,
    ) -> bool:
        """Return ``True`` when GLSL core profile shaders are required."""

        return api in (
            QSGRendererInterface.GraphicsApi.Direct3D11,
            QSGRendererInterface.GraphicsApi.Vulkan,
            QSGRendererInterface.GraphicsApi.Metal,
            QSGRendererInterface.GraphicsApi.Software,
            QSGRendererInterface.GraphicsApi.Null,
            QSGRendererInterface.GraphicsApi.OpenGLRhi,
        )

    # ------------------------------------------------------------------
    # Central Widget Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_central(window: MainWindow) -> None:
        """Создать центральный вид с горизонтальным и вертикальным сплиттерами

        Layout: [3D Scene (top) + Charts (bottom)] | [Control Panels (right)]

        Args:
            window: MainWindow instance
        """
        UISetup.logger.debug("setup_central: Создание системы сплиттеров...")

        # Create main horizontal splitter (left: scene+charts, right: panels)
        window.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        window.main_horizontal_splitter.setObjectName("MainHorizontalSplitter")

        # Create vertical splitter for left side (scene + charts)
        window.main_splitter = QSplitter(Qt.Orientation.Vertical)
        window.main_splitter.setObjectName("SceneChartsSplitter")

        # Top section: 3D scene
        if window.use_qml_3d:
            UISetup._setup_qml_3d_view(window)
        else:
            UISetup._setup_legacy_opengl_view(window)

        if window._qquick_widget:
            window.main_splitter.addWidget(window._qquick_widget)
            window._qquick_widget.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

        # Bottom section: Charts
        from src.ui.charts import ChartWidget

        window.chart_widget = ChartWidget(window)
        window.chart_widget.setMinimumHeight(200)
        window.main_splitter.addWidget(window.chart_widget)

        # Set stretch factors (3D gets more space)
        window.main_splitter.setStretchFactor(0, 3)  # 60% for 3D
        window.main_splitter.setStretchFactor(1, 2)  # 40% for charts

        # Add to horizontal splitter
        window.main_horizontal_splitter.addWidget(window.main_splitter)

        # Set as central widget
        window.setCentralWidget(window.main_horizontal_splitter)

        UISetup.logger.debug("✅ Система сплиттеров создана")

    @staticmethod
    def _format_qml_errors(errors: list[Any]) -> str:
        """Сформировать развёрнутый отчёт об ошибках QML.

        PySide6 возвращает список QQmlError. str(error) может быть пустым,
        поэтому собираем человеко-читаемое описание вручную.
        """
        if not errors:
            return "<no error details from engine>"

        parts: list[str] = []
        for err in errors:
            try:
                # PySide6.QtQml.QQmlError API
                to_string = getattr(err, "toString", None)
                if callable(to_string):
                    text = to_string()
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
                        continue

                # Fallback: manual formatting
                url = None
                try:
                    u = getattr(err, "url", None)
                    if callable(u):
                        url = u()
                        try:
                            # QUrl → string
                            url = url.toString()  # type: ignore[attr-defined]
                        except Exception:
                            url = str(url)
                    else:
                        url = str(getattr(err, "url", ""))
                except Exception:
                    url = None
                line = getattr(err, "line", lambda: None)()
                col = getattr(err, "column", lambda: None)()
                desc = getattr(err, "description", lambda: None)()
                chunk = []
                if url:
                    chunk.append(str(url))
                if line is not None:
                    chunk.append(f"{line}")
                    if col is not None:
                        chunk[-1] += f":{col}"
                if desc:
                    chunk.append(str(desc))
                parts.append(" - ".join(chunk) if chunk else repr(err))
            except Exception:
                # Защитный путь — хоть что-то выведем
                try:
                    parts.append(str(err))
                except Exception:
                    parts.append("<unprintable qml error>")
        return "\n".join(parts)

    @staticmethod
    def _setup_qml_3d_view(window: MainWindow) -> None:
        """Setup Qt Quick 3D scene with QQuickWidget

        Loads unified main.qml file with full suspension visualization.

        Args:
            window: MainWindow instance
        """
        if not window.use_qml_3d:
            UISetup.logger.info(
                "    [QML] use_qml_3d disabled — skipping QML scene initialisation"
            )
            UISetup._setup_legacy_opengl_view(window)
            return

        UISetup.logger.info("    [QML] Загрузка main.qml...")

        try:
            window._qquick_widget = QQuickWidget(window)
            window._qquick_widget.setResizeMode(
                QQuickWidget.ResizeMode.SizeRootObjectToView
            )
            window._qquick_widget.setClearColor(Qt.transparent)
            window._qquick_widget.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground
            )
            window._qquick_widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
            window._qquick_widget.setAttribute(
                Qt.WidgetAttribute.WA_OpaquePaintEvent,
                False,
            )
            window._qquick_widget.setAutoFillBackground(False)
            window._qquick_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Get QML engine
            engine = window._qquick_widget.engine()

            # ✅ КРИТИЧЕСКОЕ: Устанавливаем контекст ДО загрузки QML
            context = engine.rootContext()
            context.setContextProperty("window", window)

            try:
                graphics_api = QQuickWindow.graphicsApi()
            except Exception as api_exc:  # pragma: no cover - diagnostic logging
                UISetup.logger.debug(
                    "    ⚠️ Unable to query QQuickWindow graphics API: %s", api_exc
                )
                graphics_api = QSGRendererInterface.GraphicsApi.Unknown

            graphics_api_label = UISetup._graphics_api_to_string(graphics_api)
            requires_desktop_shaders = UISetup._graphics_api_requires_desktop_shaders(
                graphics_api
            )

            try:
                surface_format = window._qquick_widget.format()
                renderable_type = surface_format.renderableType()
            except Exception as format_exc:  # pragma: no cover - diagnostic logging
                UISetup.logger.debug(
                    "    ⚠️ Unable to query QQuickWidget surface format: %s", format_exc
                )
            else:
                if renderable_type == QSurfaceFormat.OpenGLES:
                    graphics_api_label = "opengl-es"
                    requires_desktop_shaders = False
                    UISetup.logger.info(
                        "    [QML] Detected OpenGL ES surface format; forcing GLES shaders"
                    )

            context.setContextProperty("qtGraphicsApiName", graphics_api_label)
            context.setContextProperty(
                "qtGraphicsApiRequiresDesktopShaders", requires_desktop_shaders
            )
            context.setContextProperty(
                "effectShaderManifest",
                UISetup._build_effect_shader_manifest(),
            )
            try:
                context.setContextProperty("qtRuntimeVersion", qVersion())
                UISetup.logger.info(
                    "    ✅ Qt runtime version exposed to QML context (%s)",
                    qVersion(),
                )
            except Exception as qt_version_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose qtRuntimeVersion: %s",
                    qt_version_exc,
                )
            UISetup.logger.info("    [QML] Renderer API: %s", graphics_api_label)

            try:
                feedback_controller = getattr(window, "feedback_controller", None)
                if feedback_controller is not None:
                    context.setContextProperty(
                        "feedbackController", feedback_controller
                    )
                    UISetup.logger.info(
                        "    ✅ Feedback controller exposed to QML context"
                    )
            except Exception as feedback_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose feedback controller: %s",
                    feedback_exc,
                )

            window._scene_bridge = None
            try:
                context.setContextProperty("pythonSceneBridge", None)
            except Exception as bridge_ctx_exc:
                UISetup.logger.debug(
                    "    ⚠️ Unable to seed pythonSceneBridge context: %s",
                    bridge_ctx_exc,
                )

            try:
                from src.ui.scene_bridge import SceneBridge

                window._scene_bridge = SceneBridge(window)
                context.setContextProperty("pythonSceneBridge", window._scene_bridge)
                UISetup.logger.info("    ✅ SceneBridge exposed to QML context")
            except Exception as bridge_exc:
                window._scene_bridge = None
                UISetup.logger.error(
                    "    ❌ Failed to initialise SceneBridge: %s", bridge_exc
                )

            # Новые контексты: события настроек и трассировка сигналов
            try:
                from src.common.signal_trace import get_signal_trace_service

                context.setContextProperty("settingsEvents", get_settings_event_bus())
                context.setContextProperty("signalTrace", get_signal_trace_service())
            except Exception as inject_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to inject diagnostics contexts: %s", inject_exc
                )

            try:
                facade = LightingSettingsFacade(
                    settings_manager=getattr(window, "settings_manager", None)
                )
                bridge = LightingSettingsBridge(facade)
                window._lighting_settings_facade = facade
                window._lighting_settings_bridge = bridge
                context.setContextProperty("lightingSettings", bridge)
                UISetup.logger.info(
                    "    ✅ Lighting settings facade exposed to QML context"
                )
            except Exception as lighting_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose lighting settings facade: %s",
                    lighting_exc,
                )

            try:
                training_bridge = TrainingPresetBridge(
                    settings_manager=getattr(window, "settings_manager", None)
                )
                window._training_bridge = training_bridge
                context.setContextProperty("trainingBridge", training_bridge)
                UISetup.logger.info(
                    "    ✅ Training presets bridge exposed to QML context"
                )
            except Exception as training_exc:
                window._training_bridge = None
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose training presets bridge: %s",
                    training_exc,
                )

            try:
                telemetry_bridge = getattr(window, "telemetry_bridge", None)
                context.setContextProperty("pythonTelemetryBridge", telemetry_bridge)
                if telemetry_bridge is not None:
                    UISetup.logger.info(
                        "    ✅ Telemetry bridge exposed to QML context"
                    )
            except Exception as telemetry_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose telemetry bridge: %s",
                    telemetry_exc,
                )

            UISetup.logger.info("    ✅ Window context registered")

            try:
                payload = UISetup.build_qml_context_payload(
                    getattr(window, "settings_manager", None)
                )
                context.setContextProperty(
                    "initialAnimationSettings", payload["animation"]
                )
                context.setContextProperty("initialSceneSettings", payload["scene"])
                context.setContextProperty(
                    "initialSharedMaterials", payload["materials"]
                )
                context.setContextProperty("materialsDefaults", payload["materials"])
                context.setContextProperty(
                    "initialReflectionProbeSettings", payload["reflection_probe"]
                )
                context.setContextProperty(
                    "initialGeometrySettings", payload["geometry"]
                )
                context.setContextProperty(
                    "initialDiagnosticsSettings", payload.get("diagnostics", {})
                )
                context.setContextProperty(
                    "lightingAccess", payload.get("lighting", {})
                )
                context.setContextProperty(
                    "initialModesSettings", payload.get("modes", {})
                )
                context.setContextProperty(
                    "initialPneumaticSettings", payload.get("pneumatic", {})
                )
                context.setContextProperty(
                    "initialSimulationSettings", payload.get("simulation", {})
                )
                context.setContextProperty(
                    "initialCylinderSettings", payload.get("cylinder", {})
                )
                context.setContextProperty(
                    "modesMetadata", payload.get("modes_metadata", {})
                )
                UISetup.logger.info("    ✅ Initial graphics settings exposed to QML")
            except Exception as ctx_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose initial graphics settings: %s",
                    ctx_exc,
                )
                UISetup._register_postmortem_reason(
                    f"initial-settings-export-failed:{ctx_exc}"
                )

            # Export profile manager
            profile_service = getattr(window, "profile_service", None)
            if profile_service is None:
                profile_service = getattr(window, "profile_manager", None)
            try:
                if profile_service is not None:
                    context.setContextProperty("settingsProfiles", profile_service)
            except Exception as profile_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose profile manager: %s", profile_exc
                )

            try:
                if profile_service is not None and hasattr(profile_service, "refresh"):
                    profile_service.refresh()
            except Exception as refresh_exc:
                UISetup.logger.debug(
                    "    ⚠️ Failed to refresh profile list: %s", refresh_exc
                )

            # Import paths
            from PySide6.QtCore import QLibraryInfo

            qml_import_path = QLibraryInfo.path(
                QLibraryInfo.LibraryPath.Qml2ImportsPath
            )
            engine.addImportPath(str(qml_import_path))

            # Ensure the relative path is registered for qmlimportscanner parity
            engine.addImportPath(QML_RELATIVE_ROOT.as_posix())

            local_qml_path = QML_ABSOLUTE_ROOT
            if local_qml_path.exists():
                engine.addImportPath(str(local_qml_path.resolve()))

            # Load QML file
            qml_file = UISetup._resolve_supported_qml_scene()
            if not qml_file.exists():
                UISetup._register_postmortem_reason(f"qml-file-missing:{qml_file}")
                raise FileNotFoundError(f"QML file not found: {qml_file}")

            qml_url = QUrl.fromLocalFile(str(qml_file.absolute()))
            window._qquick_widget.setSource(qml_url)

            # Check status
            status = window._qquick_widget.status()
            if status == QQuickWidget.Status.Error:
                errors = window._qquick_widget.errors()
                error_msg = UISetup._format_qml_errors(errors)
                UISetup._register_postmortem_reason(f"qml-engine-error:{error_msg}")
                raise RuntimeError(f"QML load errors:\n{error_msg}")

            # Get root object
            window._qml_root_object = window._qquick_widget.rootObject()
            if not window._qml_root_object:
                raise RuntimeError("Failed to get QML root object")

            quick_window = window._qquick_widget.quickWindow()
            if quick_window is not None:
                try:
                    quick_window.setColor(Qt.transparent)
                    quick_window.setClearColor(Qt.transparent)
                except Exception:
                    pass

            try:
                if getattr(window, "_scene_bridge", None) is not None:
                    window._qml_root_object.setProperty(
                        "sceneBridge", window._scene_bridge
                    )
                    UISetup.logger.info(
                        "    ✅ SceneBridge assigned to QML root property"
                    )
            except Exception as assign_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to assign SceneBridge to QML root: %s", assign_exc
                )

            # Store base directory
            window._qml_base_dir = qml_file.parent.resolve()

            UISetup.logger.info("    ✅ %s loaded successfully", qml_file.name)

        except Exception as e:
            UISetup._register_postmortem_reason(f"qml-load-failed:{e}")
            UISetup.logger.exception(f"    ❌ QML load failed: {e}")

            # Fallback: error label
            fallback = QLabel(
                f"КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                f"Проверьте файл assets/qml/main.qml"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet(
                "background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;"
            )
            window._qquick_widget = fallback

    @staticmethod
    def _setup_legacy_opengl_view(window: MainWindow) -> None:
        """Setup legacy OpenGL widget (stub)"""
        UISetup.logger.debug("_setup_legacy_opengl_view: Using QWidget placeholder")

        placeholder = QLabel(
            "Legacy diagnostics mode — Qt Quick 3D scene disabled.\n"
            "Use --legacy or headless mode to re-enable this fallback view."
        )
        placeholder.setObjectName("LegacyScenePlaceholder")
        placeholder.setWordWrap(True)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumSize(640, 360)
        placeholder.setStyleSheet(
            "background-color: #1f1f1f; color: #f0f0f0; font-size: 14px; padding: 24px;"
        )

        window._scene_bridge = None
        window._qml_root_object = None  # type: ignore[attr-defined]
        window._qquick_widget = placeholder

    @staticmethod
    def _normalize_scene_key(value: str) -> str:
        key = value.strip().lower().replace("-", "_")
        if key.endswith(".qml"):
            key = key[:-4]
        if key.startswith("main.") and key != "main":
            key = key.split(".", 1)[0]
        if key.startswith("main_") and key != "main":
            key = key[len("main_") :]
        return key

    @staticmethod
    def _resolve_supported_qml_scene() -> Path:
        """Resolve which QML scene should be loaded."""

        requested = os.environ.get(UISetup._SCENE_ENV_VAR)
        load_order = list(UISetup._SCENE_LOAD_ORDER)

        if requested:
            normalized = UISetup._normalize_scene_key(requested)
            if normalized in UISetup._SUPPORTED_SCENES:
                load_order = [normalized] + [
                    name for name in load_order if name != normalized
                ]
                UISetup.logger.info(
                    "    [QML] Requested scene via %s: %s",
                    UISetup._SCENE_ENV_VAR,
                    UISetup._SUPPORTED_SCENES[normalized].name,
                )
            else:
                UISetup.logger.warning(
                    "    [QML] Unsupported scene '%s' requested via %s. Allowed: %s",
                    requested,
                    UISetup._SCENE_ENV_VAR,
                    ", ".join(
                        UISetup._SUPPORTED_SCENES[name].name
                        for name in UISetup._SCENE_LOAD_ORDER
                    ),
                )

        for scene_key in load_order:
            scene_path = UISetup._SUPPORTED_SCENES[scene_key]
            if scene_path.exists():
                UISetup.logger.info("    [QML] Загрузка сцены: %s", scene_path.name)
                return scene_path
            UISetup.logger.debug(
                "    [QML] Scene %s not found at %s",
                scene_key,
                scene_path,
            )

        searched = ", ".join(
            str(UISetup._SUPPORTED_SCENES[key]) for key in UISetup._SCENE_LOAD_ORDER
        )
        raise FileNotFoundError("No supported QML scenes found. Checked: " + searched)

    # ------------------------------------------------------------------
    # Tabs Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_tabs(window: MainWindow) -> None:
        """Создать вкладки с панелями параметров

        Tabs:
          - Геометрия (Geometry)
          - Пневмосистема (Pneumatics)
          - Графика (Graphics)
          - Динамика движения (Road - stub)

        Args:
            window: MainWindow instance
        """
        UISetup.logger.debug("setup_tabs: Создание вкладок...")

        # Create tab widget
        window.tab_widget = QTabWidget(window)
        window.tab_widget.setObjectName("ParameterTabs")
        window.tab_widget.setMinimumWidth(300)
        window.tab_widget.setMaximumWidth(800)

        # Import panels
        from src.ui.panels import (
            GeometryPanel,
            PneumoPanel,
            GraphicsPanel,
        )
        from src.ui.feedback import FeedbackPanel

        # Tab 1: Геометрия
        window.geometry_panel = GeometryPanel(window)
        scroll_geometry = QScrollArea()
        scroll_geometry.setWidgetResizable(True)
        scroll_geometry.setWidget(window.geometry_panel)
        scroll_geometry.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        window.tab_widget.addTab(scroll_geometry, "Геометрия")

        # Tab 2: Пневмосистема
        window.pneumo_panel = PneumoPanel(window)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(window.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        window.tab_widget.addTab(scroll_pneumo, "Пневмосистема")

        # Режимы перенесены в QML SimulationPanel
        window.modes_panel = None

        # Tab 3: Графика (без дополнительного ScrollArea!)
        window.graphics_panel = GraphicsPanel(window)
        window._graphics_panel = window.graphics_panel  # Alias
        window.tab_widget.addTab(window.graphics_panel, "🎨 Графика")

        try:
            window.feedback_panel = FeedbackPanel(
                window,
                controller=getattr(window, "feedback_controller", None),
            )
            window.tab_widget.addTab(window.feedback_panel, "Обратная связь")
        except Exception as feedback_exc:
            window.feedback_panel = None
            UISetup.logger.warning(
                "⚠️ Не удалось построить вкладку обратной связи: %s",
                feedback_exc,
            )

        # Tab 5: Динамика движения (stub)
        dynamics_stub = QWidget()
        dynamics_layout = QVBoxLayout(dynamics_stub)
        dynamics_label = QLabel(
            "Динамика движения\n\n"
            "Генератор профилей дороги\n"
            "(Будет реализовано отдельным промтом)"
        )
        dynamics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dynamics_label.setStyleSheet("color: #888; font-size: 12px; padding: 20px;")
        dynamics_layout.addWidget(dynamics_label)
        dynamics_layout.addStretch()
        window.tab_widget.addTab(dynamics_stub, "Динамика движения")

        # Add to horizontal splitter
        window.main_horizontal_splitter.addWidget(window.tab_widget)

        # Set stretch factors
        window.main_horizontal_splitter.setStretchFactor(0, 3)  # 75% scene+charts
        window.main_horizontal_splitter.setStretchFactor(1, 1)  # 25% panels

        # Restore last tab
        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)
        last_tab = settings.value(window.SETTINGS_LAST_TAB, 0, type=int)
        if 0 <= last_tab < window.tab_widget.count():
            window.tab_widget.setCurrentIndex(last_tab)

        # Connect tab change signal
        window.tab_widget.currentChanged.connect(window._on_tab_changed)

        UISetup.logger.debug("✅ Вкладки созданы")

    # ------------------------------------------------------------------
    # Menus Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_menus(window: MainWindow) -> None:
        """Создать меню приложения

        Menus:
          - Файл (File): Выход
          - Вид (View): Сбросить расположение

        Args:
            window: MainWindow instance
        """
        menubar = window.menuBar()
        menubar.clear()

        # File menu
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", window)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(window.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("Вид")
        reset_layout_action = QAction("Сбросить расположение", window)
        reset_layout_action.triggered.connect(window._reset_ui_layout)
        view_menu.addAction(reset_layout_action)

        UISetup.logger.debug("✅ Меню создано")

    # ------------------------------------------------------------------
    # Toolbar Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_toolbar(window: MainWindow) -> None:
        """Создать панель инструментов

        Buttons:
          - ▶ Старт
          - ⏸ Пауза
          - ⏹ Стоп
          - ↺ Сброс

        Args:
            window: MainWindow instance
        """
        toolbar = window.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)

        actions = [
            ("▶ Старт", "start"),
            ("⏸ Пауза", "pause"),
            ("⏹ Стоп", "stop"),
            ("↺ Сброс", "reset"),
        ]

        for title, command in actions:
            act = QAction(title, window)
            act.triggered.connect(
                lambda _=False, cmd=command: window._on_sim_control(cmd)
            )
            toolbar.addAction(act)

        UISetup.logger.debug("✅ Панель инструментов создана")

    # ------------------------------------------------------------------
    # Status Bar Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_status_bar(window: MainWindow) -> None:
        """Создать строку состояния

        Displays:
          - Sim Time
          - Steps
          - Physics FPS
          - Queue stats

        Args:
            window: MainWindow instance
        """
        status_bar = QStatusBar(window)
        window.setStatusBar(status_bar)

        window.sim_time_label = QLabel("Sim Time: 0.000s")
        window.step_count_label = QLabel("Steps: 0")
        window.fps_label = QLabel("Physics FPS: 0.0")
        window.queue_label = QLabel("Queue: 0/0")

        for widget in (
            window.sim_time_label,
            window.step_count_label,
            window.fps_label,
            window.queue_label,
        ):
            widget.setStyleSheet("padding: 0 6px")
            status_bar.addPermanentWidget(widget)

        window.status_bar = status_bar

        UISetup.logger.debug("✅ Строка состояния создана")
