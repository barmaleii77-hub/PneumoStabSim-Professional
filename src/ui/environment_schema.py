"""Environment settings schema and validation utilities.

Used by both the Python UI layer and the QML bridge to guarantee that every
environment parameter is explicitly defined in ``config/app_settings.json``
and falls within the documented Qt6.10 ranges.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence
import re

__all__ = [
    "EnvironmentValidationError",
    "EnvironmentParameterDefinition",
    "ENVIRONMENT_PARAMETERS",
    "ENVIRONMENT_REQUIRED_KEYS",
    "ENVIRONMENT_CONTEXT_PROPERTIES",
    "validate_environment_settings",
]

_TRUE_SET = {"1", "true", "yes", "on"}
_FALSE_SET = {"0", "false", "no", "off"}


class EnvironmentValidationError(ValueError):
    """Raised when environment settings violate the expected contract."""


@dataclass(frozen=True)
class EnvironmentParameterDefinition:
    """Schema entry for a single environment parameter."""

    key: str
    value_type: str  # "bool", "float", "int", "string"
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: Sequence[str] | None = None
    allow_empty_string: bool = False
    pattern: re.Pattern[str] | None = None
    _allowed_values_lower: tuple[str, ...] | None = field(
        init=False, default=None, repr=False
    )

    def __post_init__(self) -> None:
        if self.allowed_values is not None:
            normalized = tuple(val.lower() for val in self.allowed_values)
            object.__setattr__(self, "allowed_values", tuple(self.allowed_values))
            object.__setattr__(self, "_allowed_values_lower", normalized)


def _coerce_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return bool(value)
        raise EnvironmentValidationError(f"'{key}' numeric boolean must be0 or1, got {value!r}")
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE_SET:
            return True
        if lowered in _FALSE_SET:
            return False
    raise EnvironmentValidationError(f"'{key}' must be a boolean-compatible value, got {value!r}")


def _coerce_float(value: Any, key: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError as exc:  # pragma: no cover - explicit error path
            raise EnvironmentValidationError(
                f"'{key}' must be a numeric value, got {value!r}"
            ) from exc
    raise EnvironmentValidationError(f"'{key}' must be numeric, got {value!r}")


def _coerce_int(value: Any, key: str) -> int:
    if isinstance(value, bool):  # pragma: no cover - defensive guard
        raise EnvironmentValidationError(f"'{key}' must be an integer, got boolean {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as exc:  # pragma: no cover - explicit error path
            raise EnvironmentValidationError(
                f"'{key}' must be an integer-compatible value, got {value!r}"
            ) from exc
    raise EnvironmentValidationError(f"'{key}' must be integer-compatible, got {value!r}")


def _coerce_string(defn: EnvironmentParameterDefinition, value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    if not text and not defn.allow_empty_string:
        raise EnvironmentValidationError(f"'{defn.key}' cannot be empty")
    if defn.pattern and text:
        if not defn.pattern.match(text):
            raise EnvironmentValidationError(
                f"'{defn.key}' must match pattern {defn.pattern.pattern}, got {text!r}"
            )
    return text


def _validate_range(defn: EnvironmentParameterDefinition, value: float | int) -> None:
    if defn.min_value is not None and value < defn.min_value:
        raise EnvironmentValidationError(
            f"'{defn.key}'={value!r} below minimum {defn.min_value!r}"
        )
    if defn.max_value is not None and value > defn.max_value:
        raise EnvironmentValidationError(
            f"'{defn.key}'={value!r} above maximum {defn.max_value!r}"
        )
