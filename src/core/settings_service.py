"""Лёгкий сервис доступа к настройкам приложения (app_settings.json).

Сервис предоставляет кэшированную загрузку/сохранение JSON и утилиты
для обращения к значениям через dot‑путь. Предназначен для модулей без UI
и юнит‑тестов, где не требуется полная схема валидации SettingsManager.
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from collections.abc import Mapping as MappingABC

from src.infrastructure.container import (
    ServiceContainer,
    ServiceResolutionError,
    ServiceToken,
    get_default_container,
)
from src.infrastructure.event_bus import EVENT_BUS_TOKEN
from pydantic import ValidationError
from src.core.settings_validation import (
    DEFAULT_REQUIRED_MATERIALS,
    FORBIDDEN_MATERIAL_ALIASES,
)
from src.core.settings_models import AppSettings, dump_settings


class _RelaxedAppSettings(AppSettings):
    """Variant of :class:`AppSettings` that ignores unknown fields."""

    model_config = dict(AppSettings.model_config)
    model_config["extra"] = "ignore"


class _LooseAppSettings:
    """Dictionary-backed settings view used when schema validation is disabled."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = json.loads(json.dumps(payload))

    def model_dump(self, *_, **__) -> dict[str, Any]:  # pragma: no cover - minimal shim
        return json.loads(json.dumps(self._payload))


_MISSING = object()


def _load_base_payload() -> dict[str, Any]:
    template_path = Path(__file__).resolve().parents[2] / "config" / "app_settings.json"
    try:
        content = template_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS_BASE_PAYLOAD = _load_base_payload()


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
        self._cache_dict: dict[str, Any] | None = None
        self._cache_model: AppSettings | None = None
        self._schema_cache: dict[str, Any] | None = None
        self._validator: Any | None = None
        self._unknown_paths: set[str] = set()
        self._last_modified_snapshot: str | None = None

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
        try:
            with path.open("r", encoding="utf-8") as stream:
                payload: dict[str, Any] = json.load(stream)
        except FileNotFoundError as exc:
            raise SettingsValidationError(
                f"Settings file not found at '{path}'"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SettingsValidationError(
                "Settings file contains invalid JSON: "
                f"{path} (line {exc.lineno}, column {exc.colno})"
            ) from exc
        except OSError as exc:
            raise SettingsValidationError(
                f"Failed to read settings file '{path}': {exc}"
            ) from exc
        self._normalise_fog_depth_aliases(payload)
        self._normalise_hdr_paths(payload)

        if self._validate_schema:
            self.validate(payload)
        self._capture_last_modified(payload)
        return payload

    def _parse_model(self, payload: Mapping[str, Any]) -> AppSettings:
        """Return a typed settings model, relaxing extras when schema checks are off."""

        model_factory: type[AppSettings]
        if self._validate_schema:
            model_factory = AppSettings
        else:
            model_factory = _RelaxedAppSettings

        try:
            return model_factory.model_validate(payload)
        except ValidationError as exc:  # pragma: no cover - validated via tests
            if not self._validate_schema:
                sanitized = self._sanitize_payload_for_model(payload, exc)
                enriched = self._merge_with_template(sanitized)
                try:
                    return AppSettings.model_validate(enriched)
                except ValidationError as nested:
                    raise SettingsValidationError(
                        "Settings payload failed typed validation"
                    ) from nested
            raise SettingsValidationError(
                "Settings payload failed typed validation"
            ) from exc

    def _sanitize_payload_for_model(
        self, payload: Mapping[str, Any], exc: ValidationError
    ) -> dict[str, Any]:
        sanitized: dict[str, Any] = json.loads(json.dumps(payload))
        for error in exc.errors():
            if error.get("type") != "extra_forbidden":
                continue
            location = error.get("loc")
            if not location:
                continue
            self._prune_location(sanitized, location)
        return sanitized

    def _merge_with_template(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(_SETTINGS_BASE_PAYLOAD, dict):
            return json.loads(json.dumps(payload))
        template = deepcopy(_SETTINGS_BASE_PAYLOAD)
        self._deep_merge(template, payload)
        return template

    def _normalise_fog_depth_aliases(
        self, payload: MutableMapping[str, Any] | None
    ) -> None:
        if not isinstance(payload, MutableMapping):
            return

        def _environment_section(
            root: MutableMapping[str, Any] | None,
        ) -> MutableMapping[str, Any] | None:
            if not isinstance(root, MutableMapping):
                return None
            graphics = root.get("graphics")
            if not isinstance(graphics, MutableMapping):
                return None
            environment = graphics.get("environment")
            if not isinstance(environment, MutableMapping):
                return None
            return environment

        def _environment_ranges(
            root: MutableMapping[str, Any] | None,
        ) -> MutableMapping[str, Any] | None:
            if not isinstance(root, MutableMapping):
                return None
            graphics = root.get("graphics")
            if not isinstance(graphics, MutableMapping):
                return None
            ranges = graphics.get("environment_ranges")
            if not isinstance(ranges, MutableMapping):
                return None
            return ranges

        def _mirror_value(
            section: MutableMapping[str, Any],
            primary: str,
            legacy: str,
        ) -> None:
            if primary in section and legacy not in section:
                section[legacy] = section[primary]
            elif legacy in section and primary not in section:
                section[primary] = section[legacy]

        def _sync_environment(section: MutableMapping[str, Any]) -> None:
            _mirror_value(section, "fog_depth_near", "fog_near")
            _mirror_value(section, "fog_depth_far", "fog_far")
            if "fog_depth_enabled" not in section:
                section["fog_depth_enabled"] = bool(section.get("fog_enabled", True))
            if "fog_depth_curve" not in section:
                fallback = section.get("fog_height_curve")
                if isinstance(fallback, (int, float)):
                    section["fog_depth_curve"] = fallback
                else:
                    section["fog_depth_curve"] = 1.0

        def _sync_ranges(section: MutableMapping[str, Any]) -> None:
            if "fog_depth_near" in section and "fog_near" not in section:
                section["fog_near"] = deepcopy(section["fog_depth_near"])
            elif "fog_near" in section and "fog_depth_near" not in section:
                section["fog_depth_near"] = deepcopy(section["fog_near"])

            if "fog_depth_far" in section and "fog_far" not in section:
                section["fog_far"] = deepcopy(section["fog_depth_far"])
            elif "fog_far" in section and "fog_depth_far" not in section:
                section["fog_depth_far"] = deepcopy(section["fog_far"])

            if "fog_depth_curve" not in section and "fog_height_curve" in section:
                section["fog_depth_curve"] = deepcopy(section["fog_height_curve"])
            elif "fog_height_curve" not in section and "fog_depth_curve" in section:
                section["fog_height_curve"] = deepcopy(section["fog_depth_curve"])

        current = payload.get("current")
        defaults_snapshot = payload.get("defaults_snapshot")
        metadata = payload.get("metadata")

        for section in (
            _environment_section(current),
            _environment_section(defaults_snapshot),
        ):
            if section is not None:
                _sync_environment(section)

        for section in (
            _environment_ranges(current),
            _environment_ranges(defaults_snapshot),
        ):
            if section is not None:
                _sync_ranges(section)

        if isinstance(metadata, MutableMapping):
            slider_ranges = metadata.get("environment_slider_ranges")
            if isinstance(slider_ranges, MutableMapping):
                _sync_ranges(slider_ranges)

    @staticmethod
    def _prune_location(payload: Any, location: Sequence[Any]) -> None:
        if not location:
            return

        target: Any = payload
        for segment in location[:-1]:
            if isinstance(segment, int):
                if isinstance(target, list) and 0 <= segment < len(target):
                    target = target[segment]
                else:
                    return
            else:
                if isinstance(target, MutableMapping):
                    target = target.get(segment)
                else:
                    return

        final = location[-1]
        if isinstance(final, int):
            if isinstance(target, list) and 0 <= final < len(target):
                target.pop(final)
        else:
            if isinstance(target, MutableMapping):
                target.pop(final, None)

    @staticmethod
    def _deep_merge(
        target: MutableMapping[str, Any], source: Mapping[str, Any]
    ) -> None:
        for key, value in source.items():
            if isinstance(value, Mapping) and isinstance(
                target.get(key), MutableMapping
            ):
                SettingsService._deep_merge(target[key], value)
            else:
                target[key] = deepcopy(value)

    @staticmethod
    def _prune_slider_metadata_nulls(payload: Any) -> None:
        if isinstance(payload, MutableMapping):
            if {"min", "max", "step"}.issubset(payload.keys()):
                for field in ("decimals", "units"):
                    if payload.get(field) is None:
                        payload.pop(field, None)
            for value in list(payload.values()):
                SettingsService._prune_slider_metadata_nulls(value)
        elif isinstance(payload, list):
            for item in payload:
                SettingsService._prune_slider_metadata_nulls(item)

    @staticmethod
    def _normalise_hdr_path_value(value: Any) -> str:
        if value is None:
            return ""
        try:
            text = str(value).strip()
        except Exception:
            return ""
        if not text:
            return ""

        lowered = text.lower()
        if lowered.startswith("file://"):
            text = text[7:]
        elif lowered.startswith("file:/"):
            text = text[6:]

        text = text.replace("\\", "/")

        try:
            candidate = Path(text).expanduser()
        except Exception:
            return text

        try:
            resolved = candidate.resolve(strict=False)
        except Exception:
            resolved = candidate

        normalised = resolved.as_posix()

        if resolved.is_absolute():
            try:
                relative = resolved.relative_to(PROJECT_ROOT)
            except ValueError:
                pass
            else:
                normalised = relative.as_posix()

        if re.match(r"^[a-zA-Z]:[\\/].*", text):
            windows_normalised = PureWindowsPath(text).as_posix()
            if windows_normalised and windows_normalised not in normalised:
                normalised = windows_normalised

        return normalised

    def _normalise_hdr_paths(self, payload: MutableMapping[str, Any] | None) -> None:
        if not isinstance(payload, MutableMapping):
            return

        def _normalise_section(root: MutableMapping[str, Any] | None) -> None:
            if not isinstance(root, MutableMapping):
                return
            graphics = root.get("graphics")
            if not isinstance(graphics, MutableMapping):
                return
            environment = graphics.get("environment")
            if not isinstance(environment, MutableMapping):
                return
            if "ibl_source" in environment:
                current_value = environment.get("ibl_source")
                normalised = self._normalise_hdr_path_value(current_value)
                if normalised != current_value:
                    environment["ibl_source"] = normalised

        _normalise_section(payload.get("current"))
        _normalise_section(payload.get("defaults_snapshot"))

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
    def load(self, *, use_cache: bool = True) -> AppSettings:
        """Load and return the typed settings payload."""

        if not use_cache or self._cache_model is None:
            payload_dict = self._read_file()
            model_payload = self._build_model_payload(payload_dict)
            try:
                model = self._parse_model(model_payload)
            except SettingsValidationError:
                if self._validate_schema:
                    raise
                self._cache_dict = payload_dict
                self._cache_model = _LooseAppSettings(payload_dict)
            else:
                self._cache_dict = payload_dict
                self._cache_model = model
        return self._cache_model

    def reload(self) -> dict[str, Any]:
        """Сбросить кэш и перечитать файл."""

        self._cache_dict = None
        self._cache_model = None
        settings = self.load(use_cache=True)
        return dump_settings(settings)

    def save(
        self,
        payload: AppSettings | Mapping[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
        pending_unknown_paths: Iterable[str] | None = None,
    ) -> None:
        """Сохранить payload на диск и обновить кэш."""

        if isinstance(payload, AppSettings):
            payload_dict = dump_settings(payload)
        else:
            payload_dict = json.loads(json.dumps(payload))
            self._prune_slider_metadata_nulls(payload_dict)

        self._normalise_hdr_paths(payload_dict)
        self._strip_null_slider_metadata(payload_dict)

        last_modified = self._ensure_last_modified(payload_dict)
        if self._validate_schema:
            self.validate(payload_dict)
        self._write_file(payload_dict)
        model_payload = self._build_model_payload(
            payload_dict,
            extra_unknown_paths=pending_unknown_paths,
        )
        try:
            model = self._parse_model(model_payload)
        except SettingsValidationError:
            if self._validate_schema:
                raise
            self._cache_dict = payload_dict
            self._cache_model = _LooseAppSettings(payload_dict)
        else:
            self._cache_dict = payload_dict
            self._cache_model = model
        if last_modified is not None:
            self._last_modified_snapshot = last_modified
        if pending_unknown_paths:
            for candidate in pending_unknown_paths:
                self._record_unknown_path(candidate)
        self._publish_update_event(metadata or {})

    def _strip_null_slider_metadata(self, payload: MutableMapping[str, Any]) -> None:
        """Remove optional slider metadata fields that were serialised as ``null``."""

        metadata = payload.get("metadata")
        if not isinstance(metadata, MutableMapping):
            return

        slider_ranges = metadata.get("environment_slider_ranges")
        if not isinstance(slider_ranges, MutableMapping):
            return

        empty_ranges: list[str] = []
        for key, slider in slider_ranges.items():
            if not isinstance(slider, MutableMapping):
                continue

            null_keys = [
                candidate for candidate, value in slider.items() if value is None
            ]
            for candidate in null_keys:
                slider.pop(candidate, None)

            if not slider:
                empty_ranges.append(key)

        for key in empty_ranges:
            slider_ranges.pop(key, None)

        if not slider_ranges:
            metadata.pop("environment_slider_ranges", None)

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def get(self, path: str, default: Any | None = None) -> Any:
        """Получить значение по dot‑пути.

        Пример: ``service.get("current.constants.geometry.kinematics.track_width_m")``
        """

        segments = list(self._split_path(path))
        if not segments:
            return default

        payload = self.load()
        data: Any = dump_settings(payload)
        result = self._traverse_mapping(data, segments, _MISSING)
        if result is not _MISSING:
            return result

        if not self._validate_schema and self._cache_dict is not None:
            fallback = self._traverse_mapping(self._cache_dict, segments, _MISSING)
            if fallback is not _MISSING:
                return fallback
        return default

    def set(self, path: str, value: Any) -> None:
        """Установить значение по dot‑пути и сохранить изменения."""

        payload_model = self.load()
        payload = dump_settings(payload_model)
        segments = list(self._split_path(path))
        if not segments:
            raise ValueError("path must not be empty")

        parent = self._resolve_existing_parent(payload, segments)
        final_key = segments[-1]
        pending_unknown_paths: list[str] = []
        if final_key not in parent:
            pending_unknown_paths.append(path)

        parent[final_key] = value
        self.save(
            payload,
            metadata={
                "path": path,
                "action": "set",
            },
            pending_unknown_paths=pending_unknown_paths,
        )

    def update(self, path: str, patch: MutableMapping[str, Any]) -> None:
        """Слить (merge) словарь patch в целевой mapping по dot‑пути."""

        payload_model = self.load()
        payload = dump_settings(payload_model)
        data = self._get_existing_mapping(payload, path)
        pending_unknown_paths: list[str] = []
        for key in patch:
            if key not in data:
                pending_unknown_paths.append(f"{path}.{key}")

        data.update(patch)
        self.save(
            payload,
            metadata={
                "path": path,
                "action": "update",
            },
            pending_unknown_paths=pending_unknown_paths,
        )

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
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "settings"
            / "app_settings.schema.json"
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

        self._guard_legacy_material_aliases(payload)
        validator = self._get_validator()
        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        if not errors:
            self._validate_graphics_materials(payload)
            return

        if (
            isinstance(payload, MappingABC)
            and isinstance(payload.get("current"), MappingABC)
            and isinstance(payload.get("defaults_snapshot"), MappingABC)
            and all(
                tuple(error.path)[:2]
                in {("current", "graphics"), ("defaults_snapshot", "graphics")}
                for error in errors
            )
        ):
            try:
                self._validate_graphics_materials(payload)
            except SettingsValidationError as override_error:
                raise override_error

        formatted: list[str] = []
        for error in errors:
            path_parts = [str(part) for part in error.path]
            message = error.message

            if error.validator == "required":
                missing = error.message.split("'")[1] if "'" in error.message else "?"
                path_parts.append(str(missing))
                message = "обязательный параметр отсутствует"

            location = ".".join(path_parts) or "<root>"
            formatted.append(f"{location}: {message}")

        try:
            self._validate_graphics_materials(payload)
        except SettingsValidationError as graphics_exc:
            formatted.append(str(graphics_exc))

        joined = "; ".join(formatted)
        raise SettingsValidationError(
            f"Settings payload failed JSON Schema validation: {joined}",
            errors=formatted,
        ) from None

    def _guard_legacy_material_aliases(self, payload: MappingABC[str, Any]) -> None:
        """Pre-validate payload to surface legacy material aliases before JSON Schema."""

        def _material_section(
            root: MappingABC[str, Any] | None,
        ) -> MappingABC[str, Any] | None:
            if not isinstance(root, MappingABC):
                return None
            graphics = root.get("graphics")
            if not isinstance(graphics, MappingABC):
                return None
            materials = graphics.get("materials")
            if not isinstance(materials, MappingABC):
                return None
            return materials

        current: MappingABC[str, Any] | None = None
        defaults: MappingABC[str, Any] | None = None
        if isinstance(payload, MappingABC):
            maybe_current = payload.get("current")
            if isinstance(maybe_current, MappingABC):
                current = maybe_current
            maybe_defaults = payload.get("defaults_snapshot")
            if isinstance(maybe_defaults, MappingABC):
                defaults = maybe_defaults

        material_sections = (
            section
            for section in (
                _material_section(current),
                _material_section(defaults),
            )
            if section is not None
        )

        alias_keys: set[str] = set()
        for section in material_sections:
            alias_keys |= set(section.keys()) & FORBIDDEN_MATERIAL_ALIASES.keys()

        if alias_keys:
            alias_list = ", ".join(
                f"{alias}->{FORBIDDEN_MATERIAL_ALIASES[alias]}"
                for alias in sorted(alias_keys)
            )
            raise SettingsValidationError(
                f"Settings payload uses legacy graphics material keys: {alias_list}"
            )

    def _validate_graphics_materials(self, payload: MappingABC[str, Any]) -> None:
        """Ensure graphics materials are synchronised between current/defaults."""

        current_materials = self._require_mapping(
            payload, ("current", "graphics", "materials")
        )
        defaults_materials = self._require_mapping(
            payload, ("defaults_snapshot", "graphics", "materials")
        )

        # Reject legacy aliases early.
        alias_keys = (
            set(current_materials) | set(defaults_materials)
        ) & FORBIDDEN_MATERIAL_ALIASES.keys()
        if alias_keys:
            alias_list = ", ".join(
                f"{alias}->{FORBIDDEN_MATERIAL_ALIASES[alias]}"
                for alias in sorted(alias_keys)
            )
            raise SettingsValidationError(
                f"Settings payload uses legacy graphics material keys: {alias_list}"
            )

        current_keys = set(current_materials)
        defaults_keys = set(defaults_materials)

        missing_required = DEFAULT_REQUIRED_MATERIALS - current_keys
        if missing_required:
            required_list = ", ".join(sorted(missing_required))
            raise SettingsValidationError(
                "Settings payload is missing required graphics materials in current: "
                f"{required_list}"
            )

        missing_in_defaults = current_keys - defaults_keys
        missing_in_current = defaults_keys - current_keys
        if missing_in_defaults or missing_in_current:
            problems: list[str] = []
            if missing_in_defaults:
                problems.append(
                    "missing in defaults_snapshot: "
                    + ", ".join(sorted(missing_in_defaults))
                )
            if missing_in_current:
                problems.append(
                    "missing in current: " + ", ".join(sorted(missing_in_current))
                )
            raise SettingsValidationError(
                "Graphics materials mismatch between current and defaults_snapshot: "
                + "; ".join(problems)
            )

        mismatched_ids = self._collect_material_id_mismatches(
            current_materials, "current.graphics.materials"
        )
        mismatched_ids.extend(
            self._collect_material_id_mismatches(
                defaults_materials, "defaults_snapshot.graphics.materials"
            )
        )
        if mismatched_ids:
            raise SettingsValidationError(
                "Graphics materials contain inconsistent identifiers: "
                + "; ".join(mismatched_ids)
            )

    def _require_mapping(
        self, payload: MappingABC[str, Any], path: tuple[str, ...]
    ) -> MappingABC[str, Any]:
        node: MappingABC[str, Any] | Any = payload
        traversed: list[str] = []
        for segment in path:
            traversed.append(segment)
            if not isinstance(node, MappingABC):
                joined = ".".join(traversed[:-1]) or "<root>"
                raise SettingsValidationError(
                    f"Expected object at {joined}, found {type(node).__name__}"
                )
            if segment not in node:
                raise SettingsValidationError(
                    "Settings payload missing section " + ".".join(traversed)
                )
            node = node[segment]

        if not isinstance(node, MappingABC):
            raise SettingsValidationError(
                "Expected object at " + (".".join(traversed) or "<root>")
            )

        return node

    @staticmethod
    def _collect_material_id_mismatches(
        materials: MappingABC[str, Any], section: str
    ) -> list[str]:
        problems: list[str] = []
        for key, material in materials.items():
            if not isinstance(material, MappingABC):
                problems.append(f"{section}.{key} is not an object")
                continue
            material_id = material.get("id")
            if material_id != key:
                problems.append(f"{section}.{key} has id '{material_id}'")
        return problems

    def _resolve_existing_parent(
        self, payload: dict[str, Any], segments: list[str]
    ) -> MutableMapping[str, Any]:
        data: MutableMapping[str, Any] = payload
        for index, key in enumerate(segments[:-1]):
            next_value = data.get(key)
            if not isinstance(next_value, MutableMapping):
                raise KeyError(
                    f"Unknown settings path '{'.'.join(segments[: index + 1])}'"
                )
            data = next_value  # type: ignore[assignment]
        return data

    def _get_existing_mapping(
        self, payload: dict[str, Any], path: str
    ) -> MutableMapping[str, Any]:
        if not path:
            raise ValueError("path must not be empty")

        segments = list(self._split_path(path))
        data: MutableMapping[str, Any] = payload
        for index, key in enumerate(segments):
            next_value = data.get(key)
            if not isinstance(next_value, MutableMapping):
                raise KeyError(
                    f"Unknown settings path '{'.'.join(segments[: index + 1])}'"
                )
            data = next_value  # type: ignore[assignment]
        return data

    @staticmethod
    def _split_path(path: str) -> Iterable[str]:
        return [segment for segment in path.split(".") if segment]

    @staticmethod
    def _traverse_mapping(data: Any, segments: Iterable[str], default: Any) -> Any:
        current: Any = data
        for key in segments:
            if not isinstance(current, MutableMapping):
                return default
            if key not in current:
                return default
            current = current[key]
        return current

    def get_unknown_paths(self) -> list[str]:
        """Return a sorted list of settings paths that were not pre-defined."""

        return sorted(self._unknown_paths)

    def _record_unknown_path(self, path: str) -> None:
        self._unknown_paths.add(path)

    def _build_model_payload(
        self,
        payload: Mapping[str, Any],
        *,
        extra_unknown_paths: Iterable[str] | None = None,
    ) -> Mapping[str, Any]:
        """Return payload stripped of unknown paths for typed validation."""

        if self._validate_schema:
            return payload

        skip_paths: set[str] = set(self._unknown_paths)
        if extra_unknown_paths:
            skip_paths.update(extra_unknown_paths)
        if not skip_paths:
            return payload

        clone = json.loads(json.dumps(payload))
        for candidate in skip_paths:
            self._prune_path(clone, candidate)
        return clone

    def _prune_path(self, payload: MutableMapping[str, Any], path: str) -> None:
        segments = list(self._split_path(path))
        if not segments:
            return

        self._prune_location(payload, segments)

    def _capture_last_modified(self, payload: MappingABC[str, Any]) -> None:
        metadata = payload.get("metadata") if isinstance(payload, MappingABC) else None
        if isinstance(metadata, MappingABC):
            value = metadata.get("last_modified")
            self._last_modified_snapshot = value if isinstance(value, str) else None
        else:
            self._last_modified_snapshot = None

    def _ensure_last_modified(self, payload: dict[str, Any]) -> str | None:
        metadata = payload.get("metadata")
        if not isinstance(metadata, MutableMapping):
            metadata = {}
            payload["metadata"] = metadata

        current = metadata.get("last_modified")
        if isinstance(current, str):
            if (
                self._last_modified_snapshot is None
                or current != self._last_modified_snapshot
            ):
                return current

        timestamp = (
            datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        )
        metadata["last_modified"] = timestamp
        return timestamp

    def _publish_update_event(self, metadata: dict[str, Any]) -> None:
        container = get_default_container()
        try:
            event_bus = container.resolve(EVENT_BUS_TOKEN)
        except ServiceResolutionError:
            return

        payload = {
            "timestamp": datetime.now(UTC)
            .replace(tzinfo=None)
            .isoformat(timespec="milliseconds"),
            "source": "settings_service",
            **metadata,
        }
        event_bus.publish("settings.updated", payload)


SETTINGS_SERVICE_TOKEN = ServiceToken["SettingsService"](
    "settings_service",
    "Application-wide settings service bound to config/app_settings.json",
)


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
