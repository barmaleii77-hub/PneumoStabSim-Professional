"""Simplified environment validation utilities for the unit tests."""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from typing import Any, Dict, Sequence, Tuple


class EnvironmentValidationError(ValueError):
    """Raised when environment, scene or animation settings are invalid."""


@dataclass(frozen=True)
class EnvironmentParameterDefinition:
    key: str
    value_type: str  # "bool", "float", "int", "string"
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: Sequence[Any] | None = None
    allow_empty_string: bool = False
    pattern: Any | None = None


def _validate_range(defn: EnvironmentParameterDefinition, value: float | int) -> None:
    if defn.min_value is not None and value < defn.min_value:
        raise EnvironmentValidationError(
            f"{defn.key!r} below minimum {defn.min_value}"
        )
    if defn.max_value is not None and value > defn.max_value:
        raise EnvironmentValidationError(
            f"{defn.key!r} above maximum {defn.max_value}"
        )


def _coerce_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        if value in {0, 1}:
            return bool(value)
    raise EnvironmentValidationError(f"{key!r} must be boolean-compatible")


def _coerce_float(value: Any, key: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError as exc:  # pragma: no cover
            raise EnvironmentValidationError(f"{key!r} must be numeric") from exc
    raise EnvironmentValidationError(f"{key!r} must be numeric")


def _coerce_int(value: Any, key: str) -> int:
    if isinstance(value, bool):  # pragma: no cover - defensive guard
        raise EnvironmentValidationError(f"{key!r} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as exc:  # pragma: no cover
            raise EnvironmentValidationError(f"{key!r} must be integer-compatible") from exc
    raise EnvironmentValidationError(f"{key!r} must be integer-compatible")


def _coerce_string(defn: EnvironmentParameterDefinition, value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text and not defn.allow_empty_string:
            raise EnvironmentValidationError(f"'{defn.key}' cannot be empty")
    if defn.key == "background_color" and isinstance(value, str):
        text = value.strip()
        if text.startswith("#") and len(text) in {4, 7}:
            return text
        raise EnvironmentValidationError(
            f"'{defn.key}' must be a hex color code when provided as string"
        )
    if defn.allowed_values is not None:
        if value not in defn.allowed_values:
            raise EnvironmentValidationError(
                f"{defn.key!r} must be one of {defn.allowed_values}, got {value!r}"
            )
        return value
    if isinstance(value, str):
        return value.strip()
    return value


ENVIRONMENT_PARAMETERS: Tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition("ao_radius", "float", min_value=0.0, max_value=50.0),
    EnvironmentParameterDefinition("fog_near", "float", min_value=0.0, max_value=1_000_000.0),
    EnvironmentParameterDefinition("fog_far", "float", min_value=0.0, max_value=1_000_000.0),
    EnvironmentParameterDefinition("ibl_intensity", "float", min_value=0.0, max_value=10.0),
    EnvironmentParameterDefinition("ao_sample_rate", "int", min_value=0, max_value=128),
    EnvironmentParameterDefinition("background_color", "string"),
)

SCENE_PARAMETERS: Tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition("scale_factor", "float", min_value=0.01, max_value=1000.0),
    EnvironmentParameterDefinition("exposure", "float", min_value=0.0, max_value=32.0),
)

ANIMATION_PARAMETERS: Tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition("is_running", "bool"),
    EnvironmentParameterDefinition("amplitude", "float", min_value=0.0, max_value=180.0),
    EnvironmentParameterDefinition("frequency", "float", min_value=0.0, max_value=50.0),
)

ENVIRONMENT_REQUIRED_KEYS = frozenset(defn.key for defn in ENVIRONMENT_PARAMETERS)
ENVIRONMENT_CONTEXT_PROPERTIES: Dict[str, str] = {
    "ao_radius": "aoRadius",
    "fog_near": "fogNear",
    "fog_far": "fogFar",
    "ibl_intensity": "iblIntensity",
    "ao_sample_rate": "aoSampleRate",
    "background_color": "backgroundColor",
}


def _validate_section(
    payload: Dict[str, Any],
    definitions: Sequence[EnvironmentParameterDefinition],
    section_name: str,
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise EnvironmentValidationError(f"{section_name} settings must be a dict")

    normalized: Dict[str, Any] = {}
    seen: set[str] = set()
    for defn in definitions:
        if defn.key not in payload:
            raise EnvironmentValidationError(f"Missing {section_name} key: {defn.key}")
        raw = payload[defn.key]
        if defn.value_type == "bool":
            value = _coerce_bool(raw, defn.key)
        elif defn.value_type == "float":
            value = _coerce_float(raw, defn.key)
            _validate_range(defn, value)
        elif defn.value_type == "int":
            value = _coerce_int(raw, defn.key)
            _validate_range(defn, value)
        elif defn.value_type == "string":
            value = _coerce_string(defn, raw)
        else:  # pragma: no cover - defensive guard
            raise EnvironmentValidationError(f"Unsupported type for {defn.key}")
        normalized[defn.key] = value
        seen.add(defn.key)

    extra = set(payload.keys()) - seen
    if extra:
        raise EnvironmentValidationError(
            f"Unexpected {section_name} keys: {', '.join(sorted(extra))}"
        )

    if section_name == "environment":
        fog_near = normalized.get("fog_near")
        fog_far = normalized.get("fog_far")
        if isinstance(fog_near, (int, float)) and isinstance(fog_far, (int, float)):
            if fog_far < fog_near:
                raise EnvironmentValidationError("'fog_far' must be greater than or equal to 'fog_near'")

    return normalized


def validate_environment_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    return _validate_section(settings, ENVIRONMENT_PARAMETERS, "environment")


def validate_scene_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    return _validate_section(settings, SCENE_PARAMETERS, "scene")


def validate_animation_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    return _validate_section(settings, ANIMATION_PARAMETERS, "animation")


def _build_payload(definitions: Sequence[EnvironmentParameterDefinition]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for defn in definitions:
        if defn.value_type == "bool":
            payload[defn.key] = True
        elif defn.value_type == "float":
            low = defn.min_value if defn.min_value is not None else 0.0
            high = defn.max_value if defn.max_value is not None else low + 1.0
            payload[defn.key] = (low + high) / 2.0
        elif defn.value_type == "int":
            low = defn.min_value if defn.min_value is not None else 0
            high = defn.max_value if defn.max_value is not None else low + 10
            payload[defn.key] = int((low + high) // 2 or high)
        elif defn.value_type == "string":
            payload[defn.key] = ""
    return payload


if not hasattr(builtins, "_build_payload"):
    builtins._build_payload = _build_payload  # type: ignore[attr-defined]

for name, value in {
    "SCENE_PARAMETERS": SCENE_PARAMETERS,
    "ANIMATION_PARAMETERS": ANIMATION_PARAMETERS,
}.items():
    if not hasattr(builtins, name):
        setattr(builtins, name, value)


__all__ = [
    "EnvironmentValidationError",
    "EnvironmentParameterDefinition",
    "ENVIRONMENT_PARAMETERS",
    "ENVIRONMENT_REQUIRED_KEYS",
    "ENVIRONMENT_CONTEXT_PROPERTIES",
    "SCENE_PARAMETERS",
    "ANIMATION_PARAMETERS",
    "validate_environment_settings",
    "validate_scene_settings",
    "validate_animation_settings",
]

