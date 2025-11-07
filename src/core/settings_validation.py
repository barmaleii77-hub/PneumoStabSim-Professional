"""Utilities for validating PneumoStabSim settings payloads.

The application performs an aggressive validation pass on the configuration
before creating any Qt windows.  Historically that logic lived inside
``ApplicationRunner`` which made it hard to exercise in isolation.  This module
extracts the validation helpers so they can be unit-tested without Qt, making
startup failures predictable and easier to diagnose.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Iterable, Mapping

from src.common.settings_requirements import (
    BOOL_PNEUMATIC_KEYS,
    NUMERIC_PNEUMATIC_KEYS,
    NUMERIC_SIMULATION_KEYS,
    RECEIVER_VOLUME_LIMIT_KEYS,
    REQUIRED_CURRENT_SECTIONS,
    STRING_PNEUMATIC_KEYS,
)

# The materials are defined by the art department and referenced by the QML
# scene.  The list lives here so both the application and the tests use the same
# canonical set.
_DEFAULT_MATERIAL_NAMES = {
    "frame",
    "lever",
    "tail_rod",
    "cylinder",
    "piston_body",
    "piston_rod",
    "joint_tail",
    "joint_arm",
    "joint_rod",
}
DEFAULT_REQUIRED_MATERIALS = frozenset(_DEFAULT_MATERIAL_NAMES)

# Legacy material keys that are no longer accepted.
FORBIDDEN_MATERIAL_ALIASES = {"tail": "tail_rod"}


class SettingsValidationError(ValueError):
    """Raised when the settings payload fails structural validation."""


@dataclass(frozen=True)
class SettingsValidationSummary:
    """Result of the validation pass used for logging."""

    path: Path
    source: str


def determine_settings_source(
    settings_path: Path,
    *,
    env_var: str = "PSS_SETTINGS_FILE",
    project_default: Path | None = None,
) -> str:
    """Return a short label describing where the settings path came from."""

    if os.environ.get(env_var):
        return "ENV"

    if project_default is not None:
        try:
            if settings_path.samefile(project_default):
                return "PROJECT"
        except OSError:
            # samefile may fail on different devices or non-existing targets.
            pass

    return "CWD"


def _load_settings_payload(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise SettingsValidationError(f"Файл настроек не найден: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SettingsValidationError(
            f"Некорректный JSON в файле настроек: {path}\n{exc}"
        ) from exc
    except OSError as exc:
        raise SettingsValidationError(
            f"Не удалось прочитать файл настроек: {path}\n{exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise SettingsValidationError(
            "Файл настроек должен содержать JSON-объект на верхнем уровне"
        )

    current = payload.get("current")
    if not isinstance(current, dict):
        raise SettingsValidationError(
            "Отсутствует секция current с текущими настройками"
        )

    return payload


def _get_path(payload: Mapping[str, Any], path: str) -> Any:
    node: Any = payload
    for part in path.split("."):
        if not isinstance(node, Mapping) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


def _require_dict(payload: Mapping[str, Any], path: str) -> Mapping[str, Any]:
    try:
        value = _get_path(payload, path)
    except KeyError as exc:
        raise SettingsValidationError(
            f"Отсутствует обязательная секция {path}"
        ) from exc
    if not isinstance(value, Mapping):
        raise SettingsValidationError(f"Секция {path} должна быть объектом")
    return value


def _require_number(payload: Mapping[str, Any], path: str) -> float:
    try:
        value = _get_path(payload, path)
    except KeyError as exc:
        raise SettingsValidationError(
            f"Отсутствует обязательный числовой параметр {path}"
        ) from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SettingsValidationError(f"Параметр {path} должен быть числом")
    return float(value)


def _require_string(payload: Mapping[str, Any], path: str) -> str:
    try:
        value = _get_path(payload, path)
    except KeyError as exc:
        raise SettingsValidationError(
            f"Отсутствует обязательный текстовый параметр {path}"
        ) from exc
    if not isinstance(value, str) or not value.strip():
        raise SettingsValidationError(f"Параметр {path} должен быть непустой строкой")
    return value


def _require_bool(payload: Mapping[str, Any], path: str) -> bool:
    try:
        value = _get_path(payload, path)
    except KeyError as exc:
        raise SettingsValidationError(
            f"Отсутствует обязательный логический параметр {path}"
        ) from exc
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    raise SettingsValidationError(
        f"Параметр {path} должен быть логическим значением (true/false)"
    )


def _validate_required_paths(payload: Mapping[str, Any]) -> None:
    for section in REQUIRED_CURRENT_SECTIONS:
        _require_dict(payload, section)

    for key in NUMERIC_SIMULATION_KEYS:
        _require_number(payload, f"current.simulation.{key}")

    for key in NUMERIC_PNEUMATIC_KEYS:
        _require_number(payload, f"current.pneumatic.{key}")

    for key in RECEIVER_VOLUME_LIMIT_KEYS:
        _require_number(payload, f"current.pneumatic.receiver_volume_limits.{key}")

    for key in STRING_PNEUMATIC_KEYS:
        _require_string(payload, f"current.pneumatic.{key}")

    for key in BOOL_PNEUMATIC_KEYS:
        _require_bool(payload, f"current.pneumatic.{key}")


def _validate_materials(
    payload: Mapping[str, Any],
    required_materials: Iterable[str],
) -> None:
    try:
        materials_node = _get_path(payload, "current.graphics.materials")
    except KeyError as exc:
        raise SettingsValidationError(
            "Отсутствуют обязательные материалы в current.graphics.materials: "
            + ", ".join(sorted(required_materials))
        ) from exc

    if not isinstance(materials_node, Mapping):
        raise SettingsValidationError(
            "Секция current.graphics.materials должна быть объектом"
        )

    present = {str(name) for name in materials_node.keys()}

    forbidden = sorted(name for name in present if name in FORBIDDEN_MATERIAL_ALIASES)
    if forbidden:
        details = ", ".join(
            f"'{name}' → '{FORBIDDEN_MATERIAL_ALIASES[name]}'" for name in forbidden
        )
        raise SettingsValidationError(
            "Обнаружены устаревшие ключи материалов в current.graphics.materials: "
            + details
        )

    missing = sorted(set(required_materials) - present)
    if missing:
        raise SettingsValidationError(
            "Отсутствуют обязательные материалы в current.graphics.materials: "
            + ", ".join(missing)
        )


def ensure_directory_writable(directory: Path) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / "~pss_write_test.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover - defensive: convert to domain error
        raise SettingsValidationError(
            f"Нет прав на запись в каталог конфигурации: {directory}\n{exc}"
        ) from exc


def validate_settings_payload(
    payload: Mapping[str, Any],
    *,
    required_materials: Iterable[str] = DEFAULT_REQUIRED_MATERIALS,
) -> None:
    _validate_required_paths(payload)
    _validate_materials(payload, required_materials)


def validate_settings_file(
    path: Path,
    *,
    required_materials: Iterable[str] = DEFAULT_REQUIRED_MATERIALS,
) -> Mapping[str, Any]:
    payload = _load_settings_payload(path)
    validate_settings_payload(payload, required_materials=required_materials)
    ensure_directory_writable(path.parent)
    return payload


__all__ = [
    "DEFAULT_REQUIRED_MATERIALS",
    "SettingsValidationError",
    "SettingsValidationSummary",
    "determine_settings_source",
    "ensure_directory_writable",
    "validate_settings_file",
    "validate_settings_payload",
]
