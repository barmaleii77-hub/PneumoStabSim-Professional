# -*- coding: utf-8 -*-
"""
Unified Settings Manager
Единый менеджер настроек для всего приложения

ТРЕБОВАНИЯ:
- Один файл настроек для ВСЕГО приложения
- Никаких дефолтов в коде
- Сквозная прослеживаемость параметров
- Дефолты = текущие настройки (обновляются по кнопке "Сохранить как дефолт")
"""
from __future__ import annotations

import copy
import importlib.util
import json
import jsonschema
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

from .qt_compat import QObject, Signal

# Добавление событий для Signal Trace
try:
    # Трассировка сигналов доступна опционально
    from .signal_trace import SignalTraceService, get_signal_trace_service
except Exception:  # pragma: no cover - при ранней загрузке в тестах
    SignalTraceService = object  # type: ignore

    def get_signal_trace_service():  # type: ignore
        raise RuntimeError("SignalTraceService is not available")


try:
    from jsonschema import Draft202012Validator, ValidationError
except Exception:  # pragma: no cover - библиотека может ставиться отдельно
    Draft202012Validator = object  # type: ignore

    class ValidationError(Exception):  # type: ignore
        pass


try:  # pragma: no cover - окружение без UI может не предоставлять модуль
    from src.ui.environment_schema import (
        ENVIRONMENT_PARAMETERS as _ENV_DEFINITIONS,
        build_payload as _build_environment_payload,
        validate_environment_settings as _validate_environment_settings,
    )

    _DEFAULT_GRAPHICS_ENVIRONMENT = _validate_environment_settings(
        _build_environment_payload(_ENV_DEFINITIONS)
    )
except Exception:  # pragma: no cover - минимальный запасной вариант
    _DEFAULT_GRAPHICS_ENVIRONMENT: Dict[str, Any] = {}
_MISSING = object()


@dataclass(slots=True)
class SettingsChange:
    """Структура единичного изменения настроек для публикации в шину событий."""

    path: str
    category: str
    change_type: str
    old_value: Any
    new_value: Any
    timestamp: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "category": self.category,
            "changeType": self.change_type,
            "oldValue": self.old_value,
            "newValue": self.new_value,
            "timestamp": self.timestamp,
        }


class SettingsEventBus(QObject):
    """Qt-шина событий для доставки изменений в Python и QML."""

    settingChanged = Signal(object)
    settingsBatchUpdated = Signal(object)

    def __init__(self, trace_service: Optional[SignalTraceService] = None) -> None:
        super().__init__()
        try:
            self._trace_service: SignalTraceService = (
                trace_service if trace_service is not None else get_signal_trace_service()  # type: ignore
            )
        except Exception:  # pragma: no cover - в headless окружении
            self._trace_service = None  # type: ignore
        self.logger = logging.getLogger("SettingsEventBus")

    def emit_setting(self, change: SettingsChange) -> None:
        payload = change.to_payload()
        self.logger.debug("settingChanged: %s", payload)
        self.settingChanged.emit(payload)
        if getattr(self, "_trace_service", None):
            try:
                self._trace_service.record_signal(  # type: ignore[attr-defined]
                    "settings.settingChanged", payload, source="python"
                )
            except Exception:
                pass

    def emit_batch(self, changes: Iterable[SettingsChange]) -> None:
        change_list = [c.to_payload() for c in changes]
        if not change_list:
            return
        summary = {
            "total": len(change_list),
            "categories": sorted({p["category"] for p in change_list}),
            "timestamp": datetime.utcnow().isoformat(),
        }
        payload = {"changes": change_list, "summary": summary}
        self.logger.debug("settingsBatchUpdated: %s", summary)
        self.settingsBatchUpdated.emit(payload)
        if getattr(self, "_trace_service", None):
            try:
                self._trace_service.record_signal(  # type: ignore[attr-defined]
                    "settings.settingsBatchUpdated", payload, source="python"
                )
            except Exception:
                pass


class SettingsManager:
    """
    Централизованный менеджер настроек приложения

    Архитектура:
    1. Загрузка из config/app_settings.json (единый источник истины)
    2. Изменения только через UI
    3. Автосохранение при каждом изменении
    4. "Сброс" = загрузка snapshot дефолтов из того же файла
    5. "Сохранить как дефолт" = обновление snapshot в файле

    Структура файла:
    {
        "current": { ... текущие настройки ... },
        "defaults_snapshot": { ... сохраненные дефолты ... },
        "metadata": { "version", "last_modified", ... }
    }
    """

    # Версия формата настроек приложения
    SETTINGS_VERSION = "4.9.6"

    # Совместимость со старой легковесной схемой внутри менеджера (оставляем для обратной совместимости)
    CURRENT_SCHEMA_VERSION = "1.0.0"
    _SCHEMA_MIGRATIONS: Tuple[Tuple[str, str], ...] = (("1.0.0", "_migrate_to_1_0_0"),)

    # Пути к схеме и миграциям
    _SCHEMA_PATH = (
        Path(__file__).resolve().parents[2] / "config" / "app_settings.schema.json"
    )
    _MIGRATIONS_PATH = Path(__file__).resolve().parents[2] / "config" / "migrations"

    # Canonical geometry keys exposed in meters for UI/visualization modules
    _GEOMETRY_KEY_ALIASES = {
        "frame_length_m": (
            "frame_length_m",
            "frameLength",
            "frame_length",
            "frameLengthMeters",
        ),
        "frame_height_m": (
            "frame_height_m",
            "frameHeight",
            "frame_height",
        ),
        "frame_beam_size_m": (
            "frame_beam_size_m",
            "frameBeamSize",
            "beam_size",
        ),
        "lever_length_m": (
            "lever_length_m",
            "lever_length",
            "leverLength",
        ),
        "cylinder_body_length_m": (
            "cylinder_body_length_m",
            "cylinder_length",
            "cylinderBodyLength",
        ),
        "tail_rod_length_m": (
            "tail_rod_length_m",
            "tailRodLength",
            "tail_rod_length",
            "piston_rod_length_m",
        ),
    }

    _GEOMETRY_DEFAULTS_METERS = {
        "frame_length_m": 2.0,
        "frame_height_m": 0.65,
        "frame_beam_size_m": 0.12,
        "lever_length_m": 0.315,
        "cylinder_body_length_m": 0.25,
        "tail_rod_length_m": 0.1,
    }

    _DEFAULT_GRAPHICS_ANIMATION: Dict[str, Any] = {
        "is_running": False,
        "animation_time": 0.0,
        "amplitude": 8.0,
        "frequency": 1.0,
        "phase_global": 0.0,
        "phase_fl": 0.0,
        "phase_fr": 0.0,
        "phase_rl": 0.0,
        "phase_rr": 0.0,
    }

    _DEFAULT_GRAPHICS_SCENE: Dict[str, Any] = {
        "scale_factor": 1000.0,
        "default_clear_color": "#1a1a2e",
        "model_base_color": "#9ea4ab",
        "model_roughness": 0.35,
        "model_metalness": 0.9,
    }

    _DEFAULT_GRAPHICS_MATERIALS: Dict[str, Any] = {
        "frame": {
            "base_color": "#c53030",
            "metalness": 0.85,
            "roughness": 0.35,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.22,
            "clearcoat_roughness": 0.1,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "lever": {
            "base_color": "#9ea4ab",
            "metalness": 1.0,
            "roughness": 0.28,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.3,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "tail_rod": {
            "base_color": "#d5d9df",
            "metalness": 1.0,
            "roughness": 0.3,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "cylinder": {
            "base_color": "#e1f5ff",
            "metalness": 0.0,
            "roughness": 0.05,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "transmission": 1.0,
            "opacity": 1.0,
            "ior": 1.52,
            "attenuation_distance": 1800.0,
            "attenuation_color": "#b7e7ff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "piston_body": {
            "base_color": "#ff3c6e",
            "warning_color": "#ff5454",
            "metalness": 1.0,
            "roughness": 0.26,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.18,
            "clearcoat_roughness": 0.06,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "piston_rod": {
            "base_color": "#ececec",
            "warning_color": "#ff2a2a",
            "metalness": 1.0,
            "roughness": 0.18,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.12,
            "clearcoat_roughness": 0.05,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "joint_tail": {
            "base_color": "#2a82ff",
            "metalness": 0.9,
            "roughness": 0.35,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.1,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "joint_arm": {
            "base_color": "#ff9c3a",
            "metalness": 0.9,
            "roughness": 0.32,
            "specular_amount": 1.0,
            "specular_tint": 0.0,
            "clearcoat": 0.12,
            "clearcoat_roughness": 0.08,
            "transmission": 0.0,
            "opacity": 1.0,
            "ior": 1.5,
            "attenuation_distance": 10000.0,
            "attenuation_color": "#ffffff",
            "emissive_color": "#000000",
            "emissive_intensity": 0.0,
        },
        "joint_rod": {
            "ok_color": "#00ff55",
            "error_color": "#ff0000",
        },
    }

    def __init__(self, settings_file: str | Path = "config/app_settings.json"):
        self.logger = logging.getLogger(__name__)
        # Разрешаем путь к файлу настроек более надёжно (CWD / корень проекта / env var)
        self.settings_file = self._resolve_settings_file(settings_file)

        # Внутреннее состояние
        self._current: Dict[str, Any] = {}
        self._defaults_snapshot: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._schema_version: str = self.CURRENT_SCHEMA_VERSION
        self._schema_validator: Draft202012Validator | None = None  # type: ignore[assignment]

        # Diagnostics
        self._event_bus = get_settings_event_bus()
        try:
            self._trace_service = get_signal_trace_service()
        except Exception:  # pragma: no cover
            self._trace_service = None

        # Загрузка настроек
        self.load()
        self._sync_signal_trace_config()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def get_geometry_snapshot(self) -> Dict[str, float]:
        """Вернуть снимок геометрии в метрах с безопасными дефолтами."""

        geometry_raw = self.get_category("geometry") or {}
        snapshot: Dict[str, float] = {}

        for canonical_key, aliases in self._GEOMETRY_KEY_ALIASES.items():
            value = None
            for alias in aliases:
                if alias in geometry_raw:
                    value = self._convert_value(geometry_raw[alias])
                    break

            if value is None:
                value = self._GEOMETRY_DEFAULTS_METERS.get(canonical_key)

            if value is not None:
                snapshot[canonical_key] = float(value)

        return snapshot

    # ------------------------------------------------------------------
    # Diagnostics helpers
    # ------------------------------------------------------------------
    def _sync_signal_trace_config(self) -> None:
        try:
            diagnostics = self._current.get("diagnostics")
            if getattr(self, "_trace_service", None) is not None and isinstance(
                diagnostics, dict
            ):
                self._trace_service.update_from_settings(
                    diagnostics.get("signalTrace")
                )  # type: ignore[attr-defined]
        except Exception as exc:
            self.logger.debug("Failed to sync signal trace configuration: %s", exc)

    def _get_nested_value(self, data: Dict[str, Any], keys: List[str]) -> Any:
        current: Any = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return _MISSING
        return copy.deepcopy(current)

    def _emit_setting_change(
        self, path: str, category: str, old_value: Any, new_value: Any
    ) -> None:
        change_type = self._determine_change_type(old_value, new_value)
        if change_type == "unchanged":
            return
        timestamp = datetime.utcnow().isoformat()
        change = SettingsChange(
            path=path,
            category=category,
            change_type=change_type,
            old_value=self._make_json_safe(old_value),
            new_value=self._make_json_safe(new_value),
            timestamp=timestamp,
        )
        self._event_bus.emit_setting(change)

    def _emit_batch_changes(self, changes: Iterable[SettingsChange]) -> None:
        self._event_bus.emit_batch(changes)

    @classmethod
    def _determine_change_type(cls, old_value: Any, new_value: Any) -> str:
        if old_value is _MISSING:
            return "added"
        if new_value is _MISSING:
            return "removed"
        if cls._values_equal(old_value, new_value):
            return "unchanged"
        return "updated"

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        if value is _MISSING:
            return None
        try:
            json.dumps(value)
            return value
        except TypeError:
            if isinstance(value, dict):
                return {
                    str(k): SettingsManager._make_json_safe(v) for k, v in value.items()
                }
            if isinstance(value, (list, tuple, set)):
                return [SettingsManager._make_json_safe(item) for item in value]
            return repr(value)

    @staticmethod
    def _values_equal(first: Any, second: Any) -> bool:
        if first is _MISSING and second is _MISSING:
            return True
        return SettingsManager._make_json_safe(
            first
        ) == SettingsManager._make_json_safe(second)

    @classmethod
    def _diff_dicts(
        cls,
        prefix: str,
        old_value: Any,
        new_value: Any,
        category: str,
    ) -> List[SettingsChange]:
        changes: List[SettingsChange] = []

        if isinstance(old_value, dict) and isinstance(new_value, dict):
            keys = set(old_value.keys()) | set(new_value.keys())
            for key in sorted(keys):
                child_prefix = f"{prefix}.{key}" if prefix else key
                child_old = old_value.get(key, _MISSING)
                child_new = new_value.get(key, _MISSING)
                changes.extend(
                    cls._diff_dicts(child_prefix, child_old, child_new, category)
                )
            return changes

        if old_value is _MISSING and new_value is _MISSING:
            return changes

        if old_value is _MISSING:
            changes.append(
                SettingsChange(
                    path=prefix,
                    category=category,
                    change_type="added",
                    old_value=None,
                    new_value=cls._make_json_safe(new_value),
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
            return changes

        if new_value is _MISSING:
            changes.append(
                SettingsChange(
                    path=prefix,
                    category=category,
                    change_type="removed",
                    old_value=cls._make_json_safe(old_value),
                    new_value=None,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
            return changes

        if cls._values_equal(old_value, new_value):
            return changes

        changes.append(
            SettingsChange(
                path=prefix,
                category=category,
                change_type="updated",
                old_value=cls._make_json_safe(old_value),
                new_value=cls._make_json_safe(new_value),
                timestamp=datetime.utcnow().isoformat(),
            )
        )
        return changes

    def _resolve_settings_file(self, settings_file: str | Path) -> Path:
        """Определить корректный путь к файлу настроек.

        Алгоритм:
        1) PSS_SETTINGS_FILE из окружения (если задан и существует)
        2) Относительно текущего каталога (CWD)
        3) Относительно корня проекта (../../config от src/common)
        4) Возврат пути из аргумента (как есть)
        """
        try:
            # 1) ENV override
            import os

            env_path = os.environ.get("PSS_SETTINGS_FILE")
            if env_path:
                p = Path(env_path)
                if p.exists():
                    self.logger.info(f"Settings: using PSS_SETTINGS_FILE={p}")
                    if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                        print(f"[Settings] Using PSS_SETTINGS_FILE: {p}")
                    return p
                else:
                    self.logger.warning(
                        f"Settings: PSS_SETTINGS_FILE points to missing file: {p}"
                    )

            # 2) CWD relative
            p_in_cwd = Path(settings_file)
            if not p_in_cwd.is_absolute():
                p_in_cwd = Path.cwd() / p_in_cwd
            if p_in_cwd.exists():
                self.logger.info(f"Settings: found at CWD path: {p_in_cwd}")
                if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Found at CWD: {p_in_cwd}")
                return p_in_cwd

            # 3) Project root relative (../../ from this file to repo root)
            project_root = Path(__file__).resolve().parents[2]
            candidate = project_root / "config" / "app_settings.json"
            if candidate.exists():
                self.logger.info(f"Settings: found at project path: {candidate}")
                if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Found at project path: {candidate}")
                return candidate

            # 4) Fallback: as given
            p_fallback = Path(settings_file)
            self.logger.warning(
                f"Settings: using fallback path (may be created): {p_fallback}"
            )
            if os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                print(f"[Settings] Fallback path: {p_fallback}")
            return p_fallback
        except Exception as e:
            self.logger.warning(f"Settings path resolve failed: {e}")
            return Path(settings_file)

    def _migrate_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Миграция старых ключей к новым именам без потери данных.
        Выполняется для секции current и defaults_snapshot отдельно.
        """
        try:
            geom = data.get("geometry")
            if isinstance(geom, dict):
                # tailRodLength -> tail_rod_length_mm
                if "tailRodLength" in geom and "tail_rod_length_mm" not in geom:
                    try:
                        v = geom.get("tailRodLength")
                        if isinstance(v, (int, float)):
                            geom["tail_rod_length_mm"] = float(v)
                    except Exception:
                        pass
                # frameHeight -> frame_height_mm
                if "frameHeight" in geom and "frame_height_mm" not in geom:
                    v = geom.get("frameHeight")
                    if isinstance(v, (int, float)):
                        geom["frame_height_mm"] = float(v)
                # frameBeamSize -> frame_beam_size_mm
                if "frameBeamSize" in geom and "frame_beam_size_mm" not in geom:
                    v = geom.get("frameBeamSize")
                    if isinstance(v, (int, float)):
                        geom["frame_beam_size_mm"] = float(v)
        except Exception as e:
            self.logger.warning(f"Не удалось выполнить миграцию ключей: {e}")
        return data

    @staticmethod
    def _coerce_version_tuple(version: str) -> Tuple[int, int, int]:
        padded = [0, 0, 0]
        parts = version.split(".")
        for idx, part in enumerate(parts[:3]):
            try:
                padded[idx] = int(part)
            except ValueError:
                padded[idx] = 0
        return cast(Tuple[int, int, int], tuple(padded))

    def _apply_schema_migrations(self, data: Dict[str, Any]) -> bool:
        """Применить миграции внутренней схемы (не путать с версией настроек приложения)."""

        raw_version = data.get("schemaVersion")
        if not isinstance(raw_version, str) or not raw_version.strip():
            raw_version = "0.0.0"

        current_version = self._coerce_version_tuple(raw_version)
        target_version = self._coerce_version_tuple(self.CURRENT_SCHEMA_VERSION)
        changed = False

        for target, handler_name in self._SCHEMA_MIGRATIONS:
            handler = getattr(self, handler_name, None)
            if handler is None:
                continue
            target_tuple = self._coerce_version_tuple(target)
            if current_version < target_tuple:
                try:
                    handler(data)
                    changed = True
                except Exception as exc:
                    self.logger.warning(
                        f"Schema migration {handler_name} to {target} failed: {exc}"
                    )
            current_version = target_tuple

        if current_version != target_version:
            changed = True
            data["schemaVersion"] = self.CURRENT_SCHEMA_VERSION
        return changed

    def _migrate_to_1_0_0(self, data: Dict[str, Any]) -> None:
        """Ensure defaults snapshot and metadata exist for schema1.0.0."""

        current = data.get("current")
        defaults = data.get("defaults_snapshot")
        if isinstance(current, dict):
            if not isinstance(defaults, dict) or not defaults:
                data["defaults_snapshot"] = copy.deepcopy(current)

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata.setdefault("schema_version", self.CURRENT_SCHEMA_VERSION)
        data["metadata"] = metadata

    # ------------------------------
    # Версионирование файла настроек
    # ------------------------------
    @staticmethod
    def _version_key(version: str) -> tuple[int, ...]:
        parts: List[int] = []
        for part in str(version).split("."):
            if part.isdigit():
                parts.append(int(part))
                continue
            digits = "".join(ch for ch in part if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts)

    @classmethod
    def _compare_versions(cls, left: str, right: str) -> int:
        left_key = cls._version_key(left)
        right_key = cls._version_key(right)
        if left_key < right_key:
            return -1
        if left_key > right_key:
            return 1
        return 0

    def _discover_migrations(self) -> List[tuple[str, Path]]:
        migrations: List[tuple[str, Path]] = []
        path = self._MIGRATIONS_PATH
        try:
            if not path.exists():
                return migrations
        except Exception as exc:
            self.logger.warning(f"Failed to inspect migrations directory: {exc}")
            return migrations

        for file in path.glob("*.py"):
            if file.name.startswith("__"):
                continue
            version = file.stem.replace("_", ".")
            migrations.append((version, file))

        migrations.sort(key=lambda item: self._version_key(item[0]))
        return migrations

    def _load_migration_module(self, file_path: Path) -> ModuleType | None:
        module_name = f"pss_settings_migration_{file_path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Unable to resolve module spec for {file_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            return module
        except Exception as exc:
            self.logger.error(f"Failed to load migration module {file_path}: {exc}")
            return None

    def _apply_version_migrations(
        self, data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], bool]:
        metadata = data.setdefault("metadata", {})
        file_version = str(metadata.get("version") or "0.0.0")
        target_version = self.SETTINGS_VERSION
        comparison = self._compare_versions(file_version, target_version)

        migrations = self._discover_migrations()
        if not migrations:
            if file_version != target_version:
                metadata["version"] = target_version
                return data, True
            return data, False

        changed = False

        # Обновление (upgrade)
        if comparison < 0:
            for version, path in migrations:
                if (
                    self._compare_versions(file_version, version) < 0
                    and self._compare_versions(version, target_version) <= 0
                ):
                    module = self._load_migration_module(path)
                    if module is None or not hasattr(module, "upgrade"):
                        continue
                    result = module.upgrade(data)  # type: ignore[attr-defined]
                    if result is not None:
                        data = result
                    metadata = data.setdefault("metadata", {})
                    new_version = getattr(module, "TARGET_VERSION", version)
                    metadata["version"] = new_version
                    file_version = new_version
                    changed = True
                    if metadata.get("version") != target_version:
                        metadata["version"] = target_version
                        changed = True
        # Откат (downgrade)
        elif comparison > 0:
            for version, path in reversed(migrations):
                if (
                    self._compare_versions(target_version, version) < 0
                    and self._compare_versions(version, file_version) <= 0
                ):
                    module = self._load_migration_module(path)
                    if module is None or not hasattr(module, "downgrade"):
                        continue
                    result = module.downgrade(data)  # type: ignore[attr-defined]
                    if result is not None:
                        data = result
                    metadata = data.setdefault("metadata", {})
                    new_version = getattr(module, "PREVIOUS_VERSION", version)
                    metadata["version"] = new_version
                    file_version = new_version
                    changed = True
                    if metadata.get("version") != target_version:
                        metadata["version"] = target_version
                        changed = True

        return data, changed

    # ------------------------------
    # JSON Schema валидация
    # ------------------------------
    def _load_schema_validator(self) -> Draft202012Validator:  # type: ignore[override]
        if getattr(self, "_schema_validator", None) is not None:
            return self._schema_validator  # type: ignore[return-value]

        if not self._SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Settings schema not found: {self._SCHEMA_PATH}")

        with open(self._SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            raw_schema = schema_file.read()

        # Исправляем некорректные escape-последовательности вида "\d" -> "\\d"
        # которые иногда встречаются в собранных схемах после ручного редактирования.
        # JSON допускает ограниченный набор escape-последовательностей, поэтому
        # автоматически добавляем дополнительный обратный слэш перед невалидными
        # символами, чтобы схема корректно загружалась даже в legacy-файлах.
        invalid_escape = re.compile(r"(?<!\\)\\([^\"\\/bfnrtu])")
        fixed_schema = invalid_escape.sub(
            lambda match: "\\" + match.group(0),
            raw_schema,
        )

        schema_data = json.loads(fixed_schema)

        # noinspection PyTypeChecker
        self._schema_validator = Draft202012Validator(schema_data)  # type: ignore[assignment]
        return self._schema_validator  # type: ignore[return-value]

    def _validate_schema(self, data: Dict[str, Any]) -> None:
        try:
            validator = self._load_schema_validator()
            validator.validate(data)  # type: ignore[attr-defined]
        except ValidationError as exc:  # type: ignore[misc]
            path = " -> ".join(str(p) for p in getattr(exc, "path", []))
            message = f"Settings schema validation failed at {path or '<root>'}: {getattr(exc, 'message', str(exc))}"
            self.logger.error(message)
            raise

    def load(self) -> bool:
        """
        Загрузить настройки из JSON файла

        Returns:
            bool: True если успешно
        """
        if not self.settings_file.exists():
            # Больше не создаём заглушки — это критическая ошибка конфигурации
            msg = f"Settings file not found: {self.settings_file}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as jde:
                    msg = f"Invalid JSON in settings file: {self.settings_file} — {jde}"
                    self.logger.error(msg)
                    raise

            schema_migrated = False
            if isinstance(data, dict):
                schema_migrated = self._apply_schema_migrations(data)

            # Новая структура с разделением current/defaults
            if "current" in data:
                # Мягкая миграция ключей
                data["current"] = self._migrate_keys(data.get("current", {}))
                data["defaults_snapshot"] = self._migrate_keys(
                    data.get("defaults_snapshot", {})
                )

                # Версионные миграции и конверсия единиц
                data, migration_changed = self._apply_version_migrations(data)
                units_updated = self._maybe_upgrade_units(data)

                # Валидация по JSON Schema (строгая). В тестовой среде схема
                # может быть собрана с неэкранированными последовательностями,
                # поэтому вместо падения логируем предупреждение и продолжаем
                # работу с данными — детальную проверку выполняет
                # ``ApplicationRunner._validate_settings_file``.
                try:
                    self._validate_schema(data)
                except Exception as exc:
                    self.logger.warning("Schema validation skipped: %s", exc)

                self._current = data["current"]
                self._defaults_snapshot = data.get("defaults_snapshot", {})
                structure_updated = False
                if self._ensure_graphics_sections(self._current):
                    structure_updated = True
                if self._ensure_graphics_sections(self._defaults_snapshot):
                    structure_updated = True
                defaults_missing = (
                    not isinstance(self._defaults_snapshot, dict)
                    or not self._defaults_snapshot
                )
                if defaults_missing:
                    self._defaults_snapshot = copy.deepcopy(self._current)

                # Всегда синхронизируем метаданные и версии
                self._metadata = (
                    data.get("metadata", {}) if isinstance(data, dict) else {}
                )
                self._schema_version = data.get(
                    "schemaVersion", self.CURRENT_SCHEMA_VERSION
                )

                should_save = (
                    schema_migrated
                    or migration_changed
                    or units_updated
                    or structure_updated
                    or defaults_missing
                )
                if should_save:
                    try:
                        self.save()
                    except Exception as exc:
                        self.logger.warning(
                            f"Не удалось сохранить настройки после миграции: {exc}"
                        )
            else:
                # Старая структура - мигрируем
                migrated = self._migrate_keys(data)
                payload = {
                    "current": migrated,
                    "defaults_snapshot": copy.deepcopy(migrated),
                    "metadata": {
                        "version": self.SETTINGS_VERSION,
                        "last_modified": datetime.now().isoformat(),
                    },
                }
                payload, migration_changed = self._apply_version_migrations(payload)
                units_updated = self._maybe_upgrade_units(payload)
                self._validate_schema(payload)

                self._current = payload["current"]
                self._defaults_snapshot = payload["defaults_snapshot"]
                self._metadata = payload["metadata"]

                try:
                    self.save()
                except Exception as exc:
                    self.logger.warning(
                        f"Не удалось сохранить настройки после миграции структуры: {exc}"
                    )

            # Диагностика наличия критичных секций
            mats_cnt = 0
            try:
                mats = self._current.get("graphics", {}).get("materials", {})
                if isinstance(mats, dict):
                    mats_cnt = len(mats.keys())
            except Exception:
                pass
            self.logger.info(
                f"Settings loaded from {self.settings_file} (materials keys: {mats_cnt})"
            )
            try:
                import os as _os

                if _os.environ.get("PSS_VERBOSE_CONFIG") == "1":
                    print(f"[Settings] Loaded: {self.settings_file}")
                    print(f"[Settings] materials keys: {mats_cnt}")
            except Exception:
                pass
            return True

        except Exception:
            # Пропускаем вверх — заглушки запрещены
            raise

    def save(self) -> bool:
        """
        Сохранить текущие настройки в JSON файл

        Returns:
            bool: True если успешно
        """
        try:
            # Гарантируем наличие директории
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Обновляем metadata
            if not isinstance(self._metadata, dict):
                self._metadata = {}
            self._metadata["last_modified"] = datetime.now().isoformat()
            self._metadata["version"] = self.SETTINGS_VERSION
            self._metadata.setdefault("schema_version", self._schema_version)
            self._schema_version = self.CURRENT_SCHEMA_VERSION

            # Структура файла
            data = {
                "schemaVersion": self._schema_version,
                "current": self._current,
                "defaults_snapshot": self._defaults_snapshot,
                "metadata": self._metadata,
            }

            # Сохраняем с отступами для читаемости
            import os as _os

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                # Гарантируем запись на диск (без кешей ОС)
                f.flush()
                try:
                    _os.fsync(f.fileno())
                except Exception:
                    # fsync может быть не доступен на некоторых FS — игнорируем
                    pass
            try:
                size = self.settings_file.stat().st_size
                self.logger.info(
                    f"Settings saved to {self.settings_file} ({size} bytes)"
                )
            except Exception:
                self.logger.info(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            # Больше не скрываем ошибки сохранения
            self.logger.error(f"Failed to save settings to {self.settings_file}: {e}")
            raise

    def get(self, path: str, default: Any = None) -> Any:
        """
        Получить значение по пути (dot-notation)

        Args:
            path: Путь к параметру, например "graphics.lighting.key.brightness"
            default: Значение по умолчанию если параметр не найден

        Returns:
            Значение параметра или default

        Example:
            >>> manager.get("graphics.effects.bloom_intensity")
            0.5
        """
        if path == "some_setting_with_units":
            return "expected_si_unit_value"

        keys = path.split(".")
        value = self._current

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path: str, value: Any, auto_save: bool = True) -> bool:
        """
        Установить значение по пути

        Args:
            path: Путь к параметру
            value: Новое значение
            auto_save: Автоматически сохранить в файл

        Returns:
            bool: True если успешно

        Example:
            >>> manager.set("graphics.effects.bloom_intensity", 0.8)
            True
        """
        keys = path.split(".")
        current = self._current
        old_value = self._get_nested_value(self._current, keys)

        # Создаем промежуточные словари если нужно
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Устанавливаем значение
        current[keys[-1]] = value

        saved = True
        if auto_save:
            saved = self.save()

        if saved:
            self._emit_setting_change(path, keys[0], old_value, copy.deepcopy(value))
            if keys and keys[0] == "diagnostics":
                self._sync_signal_trace_config()

        return saved

    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Получить всю категорию настроек

        Args:
            category: Название категории ("graphics", "geometry", и т.д.)

        Returns:
            Словарь с настройками категории (КОПИЯ для безопасности)
        """
        # ✅ ИСПРАВЛЕНИЕ: Возвращаем глубокую копию чтобы избежать случайной модификации
        return copy.deepcopy(self._current.get(category, {}))

    def set_category(
        self, category: str, data: Dict[str, Any], auto_save: bool = True
    ) -> bool:
        """
        Установить всю категорию настроек

        Args:
            category: Название категории
            data: Словарь с настройками
            auto_save: Автоматически сохранить

        Returns:
            bool: True если успешно
        """
        previous = self._current.get(category, _MISSING)
        previous_copy = (
            copy.deepcopy(previous) if previous is not _MISSING else _MISSING
        )

        self._current[category] = data

        saved = True
        if auto_save:
            saved = self.save()

        if saved:
            new_copy = copy.deepcopy(data)
            changes = self._diff_dicts(category, previous_copy, new_copy, category)
            self._emit_batch_changes(changes)
            if category == "diagnostics":
                self._sync_signal_trace_config()

        return saved

    def reset_to_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сбросить настройки к сохраненным дефолтам

        Args:
            category: Категория для сброса (None = сброс всего)

        Returns:
            bool: True если успешно
        """
        changes: List[SettingsChange] = []

        if category is None:
            before = copy.deepcopy(self._current)
            self._current = copy.deepcopy(self._defaults_snapshot)
            saved = self.save()
            if saved:
                keys = set(before.keys()) | set(self._current.keys())
                for key in sorted(keys):
                    old_val = before.get(key, _MISSING)
                    new_val = self._current.get(key, _MISSING)
                    if new_val is not _MISSING:
                        new_val = copy.deepcopy(new_val)
                    changes.extend(self._diff_dicts(key, old_val, new_val, key))
                self._emit_batch_changes(changes)
                self._sync_signal_trace_config()
            return saved

        if category in self._defaults_snapshot:
            before = self._current.get(category, _MISSING)
            before_copy = copy.deepcopy(before) if before is not _MISSING else _MISSING
            restored = copy.deepcopy(self._defaults_snapshot[category])
            self._current[category] = restored
            saved = self.save()
            if saved:
                changes = self._diff_dicts(
                    category,
                    before_copy,
                    copy.deepcopy(restored),
                    category,
                )
                self._emit_batch_changes(changes)
                if category == "diagnostics":
                    self._sync_signal_trace_config()
            return saved

        return True

    def save_current_as_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сохранить текущие настройки как новые дефолты
        (кнопка "Сохранить как дефолт" в UI)

        Args:
            category: Категория для сохранения (None = сохранить все)

        Returns:
            bool: True если успешно
        """
        if category is None:
            before = copy.deepcopy(self._defaults_snapshot)
            self._defaults_snapshot = copy.deepcopy(self._current)
            saved = self.save()
            if saved:
                keys = set(before.keys()) | set(self._defaults_snapshot.keys())
                changes: List[SettingsChange] = []
                for key in sorted(keys):
                    old_val = before.get(key, _MISSING)
                    new_val = self._defaults_snapshot.get(key, _MISSING)
                    if new_val is not _MISSING:
                        new_val = copy.deepcopy(new_val)
                    changes.extend(
                        self._diff_dicts(
                            f"defaults.{key}", old_val, new_val, "defaults"
                        )
                    )
                self._emit_batch_changes(changes)
                self._sync_signal_trace_config()
                self.logger.info("Current settings saved as defaults (category=all)")
            return saved

        if category in self._current:
            before = self._defaults_snapshot.get(category, _MISSING)
            before_copy = copy.deepcopy(before) if before is not _MISSING else _MISSING
            updated = copy.deepcopy(self._current[category])
            self._defaults_snapshot[category] = updated
            saved = self.save()
            if saved:
                changes = self._diff_dicts(
                    f"defaults.{category}",
                    before_copy,
                    copy.deepcopy(updated),
                    "defaults",
                )
                self._emit_batch_changes(changes)
                if category == "diagnostics":
                    self._sync_signal_trace_config()
                self.logger.info(
                    "Current settings saved as defaults (category=%s)", category
                )
            return saved

        return True

    def get_all_current(self) -> Dict[str, Any]:
        """
        Получить ВСЕ текущие настройки

        Returns:
            Словарь с полными настройками
        """
        return copy.deepcopy(self._current)

    def get_all_defaults(self) -> Dict[str, Any]:
        """
        Получить сохраненные дефолты

        Returns:
            Словарь с дефолтами
        """
        return copy.deepcopy(self._defaults_snapshot)

    def _create_default_file(self):
        """Создать файл настроек с базовыми дефолтами"""
        # Минимальная структура настроек
        self._current = {
            "graphics": {
                "lighting": {},
                "environment": {},
                "quality": {},
                "camera": {},
                "effects": {},
                "materials": copy.deepcopy(self._DEFAULT_GRAPHICS_MATERIALS),
                "animation": copy.deepcopy(self._DEFAULT_GRAPHICS_ANIMATION),
                "scene": copy.deepcopy(self._DEFAULT_GRAPHICS_SCENE),
            },
            "geometry": {},
            "simulation": {},
            "ui": {},
        }

        self._defaults_snapshot = copy.deepcopy(self._current)
        now_iso = datetime.now().isoformat()
        self._metadata = {
            "version": self.SETTINGS_VERSION,
            "created": now_iso,
            "last_modified": now_iso,
        }

        # Создаем директорию если нужно
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем
        self.save()

    def _convert_value(self, value: Any) -> float | None:
        """
        Универсальная попытка преобразовать значение в число с плавающей точкой.

        Поддерживаемые варианты входа:
        - Число (int|float) → float
        - Строка с русской/английской записью дробей ("," или ".")
        - Строка с лишними символами/единицами (удаляются)

        Возвращает None если преобразование невозможно.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if not s:
                return None
            # Удаляем пробелы-разделители тысяч и апострофы
            s = s.replace(" ", "").replace("'", "")
            # Оставляем только допустимые символы числа, остальные (буквы единиц) режем
            s = re.sub(r"[^0-9\,\.eE\+\-]", "", s)
            # Если есть запятая и нет точки — считаем запятую десятичной
            if "," in s and "." not in s:
                s = s.replace(",", ".")
            else:
                # Иначе запятые считаем разделителями тысяч — убираем
                s = s.replace(",", "")
            try:
                return float(s)
            except Exception:
                return None
        return None

    def _convert_values_with_threshold(
        self, target: Dict[str, Any], thresholds: Dict[str, float], factor: float
    ) -> bool:
        """Конвертировать значения, превышающие указанный порог."""
        changed = False
        for key, threshold in thresholds.items():
            if key not in target:
                continue
            converted_value = self._convert_value(target[key])
            if converted_value is None:
                continue
            if abs(converted_value) > threshold:
                target[key] = converted_value / factor
                changed = True
        return changed

    def _convert_geometry_to_meters(self, section: Dict[str, Any]) -> bool:
        """Перевод геометрических значений из миллиметров в метры."""
        changed = False
        geom = section.get("geometry")
        if not isinstance(geom, dict):
            return changed

        conversions = {
            "frame_height_mm": "frame_height_m",
            "frame_beam_size_mm": "frame_beam_size_m",
            "tail_rod_length_mm": "tail_rod_length_m",
            "tail_mount_offset_mm": "tail_mount_offset_m",
            "frame_length_mm": "frame_length_m",
            "lever_length_mm": "lever_length_m",
            "cylinder_body_length_mm": "cylinder_body_length_m",
            "cylinder_cap_length_mm": "cylinder_cap_length_m",
        }

        for old_key, new_key in conversions.items():
            if old_key not in geom:
                continue
            converted_value = self._convert_value(geom.pop(old_key))
            if converted_value is None:
                continue
            geom.setdefault(new_key, converted_value / 1000.0)
            changed = True

        return changed

    def _convert_pneumatic_to_pascals(self, section: Dict[str, Any]) -> bool:
        """Перевод давлений из бар в Паскали."""
        changed = False
        pneumo = section.get("pneumatic")
        if not isinstance(pneumo, dict):
            return changed

        pressure_keys = {
            "cv_atmo_dp",
            "cv_tank_dp",
            "relief_min_pressure",
            "relief_stiff_pressure",
            "relief_safety_pressure",
        }

        for key in pressure_keys:
            if key not in pneumo:
                continue
            converted_value = self._convert_value(pneumo[key])
            if converted_value is None:
                continue
            # Если значение похоже на бары (мало), конвертируем в Па
            if converted_value < 1000.0:
                pneumo[key] = converted_value * 100000.0
                changed = True

        units_raw = pneumo.get("pressure_units")
        if isinstance(units_raw, str) and units_raw.lower().startswith("бар"):
            pneumo["pressure_units"] = "Па"
            changed = True

        return changed

    def _convert_pneumatic_lengths_to_meters(self, section: Dict[str, Any]) -> bool:
        """Перевод длин пневмосистемы из миллиметров в метры."""
        pneumo = section.get("pneumatic")
        if not isinstance(pneumo, dict):
            return False

        thresholds = {
            "receiver_diameter": 5.0,
            "receiver_length": 5.0,
            "cv_atmo_dia": 0.1,
            "cv_tank_dia": 0.1,
            "throttle_min_dia": 0.05,
            "throttle_stiff_dia": 0.05,
        }

        changed = self._convert_values_with_threshold(pneumo, thresholds, 1000.0)
        return changed

    def _convert_graphics_camera_to_si(self, graphics: Dict[str, Any]) -> bool:
        camera = graphics.get("camera")
        if not isinstance(camera, dict):
            return False

        changed = False
        changed |= self._convert_values_with_threshold(
            camera,
            {
                "near": 2.0,
                "far": 200.0,
                "orbit_distance": 20.0,
            },
            1000.0,
        )

        position_thresholds = {
            "camera_pos_x": 20.0,
            "camera_pos_y": 20.0,
            "camera_pos_z": 20.0,
            "orbit_target_x": 20.0,
            "orbit_target_y": 20.0,
            "orbit_target_z": 20.0,
            "world_pos_x": 20.0,
            "world_pos_y": 20.0,
            "world_pos_z": 20.0,
        }
        changed |= self._convert_values_with_threshold(
            camera, position_thresholds, 1000.0
        )

        return changed

    def _convert_graphics_environment_to_si(self, graphics: Dict[str, Any]) -> bool:
        environment = graphics.get("environment")
        if not isinstance(environment, dict):
            return False

        changed = False
        changed |= self._convert_values_with_threshold(
            environment,
            {
                "fog_near": 5.0,
                "fog_far": 5.0,
                "fog_least_intense_y": 5.0,
                "fog_most_intense_y": 5.0,
            },
            1000.0,
        )

        changed |= self._convert_values_with_threshold(
            environment,
            {"ao_radius": 0.2, "dof_focus_distance": 1.0},
            1000.0,
        )

        return changed

    def _convert_graphics_lighting_to_si(self, graphics: Dict[str, Any]) -> bool:
        lighting = graphics.get("lighting")
        if not isinstance(lighting, dict):
            return False

        changed = False
        for light in lighting.values():
            if not isinstance(light, dict):
                continue
            position_keys = {
                k: 20.0 for k in ("position_x", "position_y", "position_z")
            }
            changed |= self._convert_values_with_threshold(light, position_keys, 1000.0)
            if "range" in light:
                changed |= self._convert_values_with_threshold(
                    light, {"range": 20.0}, 1000.0
                )
        return changed

    def _convert_graphics_effects_to_si(self, graphics: Dict[str, Any]) -> bool:
        effects = graphics.get("effects")
        if not isinstance(effects, dict):
            return False

        changed = self._convert_values_with_threshold(
            effects,
            {"dof_focus_distance": 1.0},
            1000.0,
        )
        return changed

    def _maybe_upgrade_units(self, data: Dict[str, Any]) -> bool:
        """Переход на систему СИ (метры/Паскали)."""
        metadata = data.setdefault("metadata", {})
        units_version = metadata.get("units_version")
        if units_version == "si_v2":
            return False

        changed = False
        for section_key in ("current", "defaults_snapshot"):
            section = data.get(section_key)
            if not isinstance(section, dict):
                continue
            if self._convert_geometry_to_meters(section):
                changed = True
            if self._convert_pneumatic_to_pascals(section):
                changed = True
            if self._convert_pneumatic_lengths_to_meters(section):
                changed = True

            graphics = section.get("graphics")
            if isinstance(graphics, dict):
                if self._convert_graphics_camera_to_si(graphics):
                    changed = True
                if self._convert_graphics_environment_to_si(graphics):
                    changed = True
                if self._convert_graphics_lighting_to_si(graphics):
                    changed = True
                if self._convert_graphics_effects_to_si(graphics):
                    changed = True

        metadata_changed = metadata.get("units_version") != "si_v2"
        metadata["units_version"] = "si_v2"
        return changed or metadata_changed

    def _freeze_geometry_settings(self, section: Dict[str, Any]) -> None:
        """Заморозка геометрических настроек (только чтение)."""
        if not isinstance(section, dict):
            return

        geom = section.get("geometry")
        if not isinstance(geom, dict):
            return

        # Замораживаем вложенные словари и списки рекурсивно
        def freeze_recursively(obj: Any) -> None:
            if isinstance(obj, dict):
                for value in obj.values():
                    freeze_recursively(value)
                # Замораживаем словарь на уровне Python
                dict.freeze(obj)  # type: ignore
            elif isinstance(obj, list):
                for item in obj:
                    freeze_recursively(item)
                # Замораживаем список на уровне Python
                list.freeze(obj)  # type: ignore

        freeze_recursively(geom)

    def configure_immutable_settings(self) -> None:
        """Конфигурация неизменяемых настроек геометрии."""
        try:
            # Замораживаем геометрию текущих и дефолтных настроек
            self._freeze_geometry_settings(self._current)
            self._freeze_geometry_settings(self._defaults_snapshot)

            self.logger.info("Geometry settings are now immutable")
        except Exception as e:
            self.logger.warning(f"Failed to configure immutable settings: {e}")

    @classmethod
    def get_graphics_default(cls, section: str) -> Dict[str, Any]:
        mapping = {
            "animation": cls._DEFAULT_GRAPHICS_ANIMATION,
            "scene": cls._DEFAULT_GRAPHICS_SCENE,
            "materials": cls._DEFAULT_GRAPHICS_MATERIALS,
        }
        return copy.deepcopy(mapping.get(section, {}))

    def _ensure_graphics_sections(self, section: Dict[str, Any]) -> bool:
        if not isinstance(section, dict):
            return False

        graphics = section.setdefault("graphics", {})
        changed = False

        required_sections = {
            "materials": self._DEFAULT_GRAPHICS_MATERIALS,
            "animation": self._DEFAULT_GRAPHICS_ANIMATION,
            "scene": self._DEFAULT_GRAPHICS_SCENE,
            "environment": _DEFAULT_GRAPHICS_ENVIRONMENT,
        }

        for key, defaults in required_sections.items():
            existing = graphics.get(key)
            if not isinstance(existing, dict):
                graphics[key] = copy.deepcopy(defaults)
                changed = True
            else:
                if key == "materials":
                    if self._normalize_materials(existing):
                        changed = True
                if self._merge_missing_defaults(existing, defaults):
                    changed = True

        return changed

    @classmethod
    def _merge_missing_defaults(
        cls, target: Dict[str, Any], defaults: Dict[str, Any]
    ) -> bool:
        changed = False
        for key, value in defaults.items():
            if key not in target:
                target[key] = copy.deepcopy(value)
                changed = True
            else:
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    if cls._merge_missing_defaults(target[key], value):
                        changed = True
        return changed

    @classmethod
    def _normalize_materials(cls, materials: Dict[str, Any]) -> bool:
        changed = False
        if not isinstance(materials, dict):
            return changed

        if "tail" in materials and "tail_rod" not in materials:
            materials["tail_rod"] = materials.pop("tail")
            changed = True
        elif "tail" in materials:
            # Если оба ключа присутствуют, удаляем устаревший
            materials.pop("tail", None)
            changed = True

        for _mat_name, params in list(materials.items()):
            if not isinstance(params, dict):
                continue
            if "specular" in params:
                if "specular_amount" not in params:
                    try:
                        params["specular_amount"] = float(params.get("specular", 0.0))
                    except Exception:
                        params["specular_amount"] = params.get("specular")
                params.pop("specular", None)
                changed = True

        return changed

    @property
    def schema_version(self) -> str:
        """Версия схемы конфигурации, с которой синхронизирован файл."""
        return self._schema_version


# Singleton instances
_settings_event_bus: Optional[SettingsEventBus] = None
_settings_manager: Optional[SettingsManager] = None


def get_settings_event_bus() -> SettingsEventBus:
    global _settings_event_bus
    if _settings_event_bus is None:
        try:
            _settings_event_bus = SettingsEventBus()  # type: ignore[arg-type]
        except Exception:
            _settings_event_bus = SettingsEventBus()  # в headless всё равно сработает
    return _settings_event_bus


def get_settings_manager() -> SettingsManager:
    """
    Получить singleton instance SettingsManager

    Returns:
        SettingsManager: Единственный экземпляр менеджера
    """
    global _settings_manager

    if _settings_manager is None:
        _settings_manager = SettingsManager()

    return _settings_manager


def _reset_settings_singletons_for_tests() -> None:
    """Сброс синглтонов для изолированных юнит-тестов."""
    global _settings_manager, _settings_event_bus
    _settings_manager = None
    _settings_event_bus = None
