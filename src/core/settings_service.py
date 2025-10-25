"""Лёгкий сервис доступа к настройкам приложения (app_settings.json).

Сервис предоставляет кэшированную загрузку/сохранение JSON и утилиты
для обращения к значениям через dot‑путь. Предназначен для модулей без UI
и юнит‑тестов, где не требуется полная схема валидации SettingsManager.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, MutableMapping

from src.infrastructure.container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)


class SettingsValidationError(ValueError):
    """Raised when the settings file does not conform to the JSON schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class SettingsService:
    """Сервис доступа к настройкам с кэшем и простыми helper‑ами.

    Args:
        settings_path: Переопределение пути к файлу настроек. Если не задан,
            используется переменная окружения и стандартный путь
            ``config/app_settings.json``.
        env_var: Имя переменной окружения с альтернативным путём
            (по умолчанию ``PSS_SETTINGS_FILE``).
    """

    def __init__(
        self,
        settings_path: str | os.PathLike[str] | None = None,
        *,
        env_var: str = "PSS_SETTINGS_FILE",
        schema_path: str | os.PathLike[str] | None = None,
        schema_env_var: str = "PSS_SETTINGS_SCHEMA",
        validate_schema: bool = True,
    ) -> None:
        self._explicit_path = (
            Path(settings_path).expanduser().resolve() if settings_path else None
        )
        self._env_var = env_var
        self._explicit_schema_path = (
            Path(schema_path).expanduser().resolve() if schema_path else None
        )
        self._schema_env_var = schema_env_var
        self._validate_schema = validate_schema
        self._cache: dict[str, Any] | None = None
        self._schema_cache: dict[str, Any] | None = None
        self._validator: Any | None = None

    # ------------------------------------------------------------------
    # Path resolution & raw IO
    # ------------------------------------------------------------------
    def resolve_path(self) -> Path:
        """Вернуть путь к файлу настроек для чтения/записи."""

        if self._explicit_path is not None:
            return self._explicit_path

        env_path = os.getenv(self._env_var)
        if env_path:
            candidate = Path(env_path).expanduser().resolve()
            if candidate.exists():
                return candidate

        # Корень репозитория: src/core/settings_service.py -> ../../config/app_settings.json
        return Path(__file__).resolve().parents[2] / "config" / "app_settings.json"

    def _read_file(self) -> dict[str, Any]:
        path = self.resolve_path()
        with path.open("r", encoding="utf-8") as stream:
            payload: dict[str, Any] = json.load(stream)
        if self._validate_schema:
            self.validate(payload)
        return payload

    def _write_file(self, payload: dict[str, Any]) -> None:
        path = self.resolve_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
        tmp_path.replace(path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load(self, *, use_cache: bool = True) -> dict[str, Any]:
        """Загрузить и вернуть весь JSON payload в виде dict.

        При use_cache=True возвращает кэш при повторных вызовах.
        """

        if not use_cache or self._cache is None:
            self._cache = self._read_file()
        return self._cache

    def reload(self) -> dict[str, Any]:
        """Сбросить кэш и перечитать файл."""

        self._cache = None
        return self.load(use_cache=True)

    def save(self, payload: dict[str, Any]) -> None:
        """Сохранить payload на диск и обновить кэш."""

        if self._validate_schema:
            self.validate(payload)
        self._write_file(payload)
        self._cache = payload

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def get(self, path: str, default: Any | None = None) -> Any:
        """Получить значение по dot‑пути.

        Пример: ``service.get("current.constants.geometry.kinematics.track_width_m")``
        """

        data: Any = self.load()
        for key in self._split_path(path):
            if not isinstance(data, MutableMapping):
                return default
            data = data.get(key, default)
            if data is default:
                return default
        return data

    def set(self, path: str, value: Any) -> None:
        """Установить значение по dot‑пути и сохранить изменения."""

        payload = self.load()
        data: MutableMapping[str, Any] = payload
        segments = list(self._split_path(path))
        if not segments:
            raise ValueError("path must not be empty")

        for key in segments[:-1]:
            next_value = data.get(key)
            if not isinstance(next_value, MutableMapping):
                next_value = {}
            data[key] = next_value
            data = next_value  # type: ignore[assignment]

        data[segments[-1]] = value
        self.save(payload)

    def update(self, path: str, patch: MutableMapping[str, Any]) -> None:
        """Слить (merge) словарь patch в целевой mapping по dot‑пути."""

        payload = self.load()
        data = self._ensure_mapping(payload, path)
        data.update(patch)
        self.save(payload)

    # ------------------------------------------------------------------
    # Schema validation helpers
    # ------------------------------------------------------------------
    def resolve_schema_path(self) -> Path:
        """Определить путь к JSON Schema."""

        if self._explicit_schema_path is not None:
            return self._explicit_schema_path

        env_path = os.getenv(self._schema_env_var)
        if env_path:
            candidate = Path(env_path).expanduser().resolve()
            if candidate.exists():
                return candidate

        return (
            Path(__file__).resolve().parents[2] / "config" / "app_settings.schema.json"
        )

    def _read_schema(self) -> dict[str, Any]:
        if self._schema_cache is None:
            path = self.resolve_schema_path()
            if not path.exists():
                raise SettingsValidationError(f"Settings schema not found at '{path}'")
            with path.open("r", encoding="utf-8") as stream:
                self._schema_cache = json.load(stream)
        return self._schema_cache

    def _get_validator(self) -> Any:
        if self._validator is not None:
            return self._validator

        try:
            from jsonschema import Draft202012Validator
            from jsonschema.exceptions import SchemaError
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise SettingsValidationError(
                "jsonschema package is required for settings validation"
            ) from exc

        schema = self._read_schema()

        try:
            self._validator = Draft202012Validator(schema)
        except SchemaError as exc:
            raise SettingsValidationError(
                f"Settings schema at '{self.resolve_schema_path()}' is invalid: {exc.message}"
            ) from exc

        return self._validator

    def validate(self, payload: dict[str, Any]) -> None:
        """Проверить payload по JSON Schema и выбросить ошибку при несовпадении."""

        validator = self._get_validator()
        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        if not errors:
            return

        formatted: list[str] = []
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            formatted.append(f"{location}: {error.message}")

        joined = "; ".join(formatted)
        raise SettingsValidationError(
            f"Settings payload failed JSON Schema validation: {joined}",
            errors=formatted,
        ) from None

    def _ensure_mapping(
        self, payload: dict[str, Any], path: str
    ) -> MutableMapping[str, Any]:
        data: MutableMapping[str, Any] = payload
        for key in self._split_path(path):
            next_value = data.get(key)
            if not isinstance(next_value, MutableMapping):
                next_value = {}
            data[key] = next_value
            data = next_value  # type: ignore[assignment]
        return data

    @staticmethod
    def _split_path(path: str) -> Iterable[str]:
        return [segment for segment in path.split(".") if segment]


SETTINGS_SERVICE_TOKEN = ServiceToken["SettingsService"](
    "settings_service",
    "Application-wide settings service bound to config/app_settings.json",
)


def _ensure_default_registration() -> None:
    container = get_default_container()
    if not container.is_registered(SETTINGS_SERVICE_TOKEN):
        container.register_factory(SETTINGS_SERVICE_TOKEN, lambda _: SettingsService())


_ensure_default_registration()


def get_settings_service(
    container: ServiceContainer | None = None,
) -> SettingsService:
    """Получить экземпляр SettingsService из контейнера зависимостей."""

    target = container or get_default_container()
    return target.resolve(SETTINGS_SERVICE_TOKEN)


__all__ = [
    "SettingsService",
    "SettingsValidationError",
    "get_settings_service",
    "SETTINGS_SERVICE_TOKEN",
]
