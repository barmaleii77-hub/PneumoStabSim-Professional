"""Simplified environment validation utilities for the unit tests."""

from __future__ import annotations

import builtins
from dataclasses import dataclass
import re
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
        raise EnvironmentValidationError(f"{defn.key!r} below minimum {defn.min_value}")
    if defn.max_value is not None and value > defn.max_value:
        raise EnvironmentValidationError(f"{defn.key!r} above maximum {defn.max_value}")


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
            raise EnvironmentValidationError(
                f"{key!r} must be integer-compatible"
            ) from exc
    raise EnvironmentValidationError(f"{key!r} must be integer-compatible")


def _coerce_string(defn: EnvironmentParameterDefinition, value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not text and not defn.allow_empty_string:
            raise EnvironmentValidationError(f"'{defn.key}' cannot be empty")
    if defn.key.endswith("_color") and isinstance(value, str):
        text = value.strip()
        if text.startswith("#") and len(text) in {4, 7}:
            return text.lower()
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
    EnvironmentParameterDefinition(
        "background_mode",
        "string",
        allowed_values=("skybox", "color", "transparent"),
    ),
    EnvironmentParameterDefinition("background_color", "string"),
    EnvironmentParameterDefinition("skybox_enabled", "bool"),
    EnvironmentParameterDefinition("ibl_enabled", "bool"),
    EnvironmentParameterDefinition(
        "ibl_intensity", "float", min_value=0.0, max_value=8.0
    ),
    EnvironmentParameterDefinition(
        "skybox_brightness", "float", min_value=0.0, max_value=8.0
    ),
    EnvironmentParameterDefinition(
        "probe_horizon", "float", min_value=-1.0, max_value=1.0
    ),
    EnvironmentParameterDefinition("reflection_enabled", "bool"),
    EnvironmentParameterDefinition(
        "reflection_padding_m", "float", min_value=0.0, max_value=1.0
    ),
    EnvironmentParameterDefinition(
        "reflection_quality",
        "string",
        allowed_values=("veryhigh", "high", "medium", "low"),
    ),
    EnvironmentParameterDefinition(
        "reflection_refresh_mode",
        "string",
        allowed_values=("everyframe", "firstframe", "never"),
    ),
    EnvironmentParameterDefinition(
        "reflection_time_slicing",
        "string",
        allowed_values=("individualfaces", "allfacesatonce", "notimeslicing"),
    ),
    EnvironmentParameterDefinition(
        "ibl_rotation", "float", min_value=-1080.0, max_value=1080.0
    ),
    EnvironmentParameterDefinition("ibl_source", "string", allow_empty_string=True),
    EnvironmentParameterDefinition(
        "skybox_blur", "float", min_value=0.0, max_value=1.0
    ),
    EnvironmentParameterDefinition(
        "ibl_offset_x", "float", min_value=-180.0, max_value=180.0
    ),
    EnvironmentParameterDefinition(
        "ibl_offset_y", "float", min_value=-180.0, max_value=180.0
    ),
    EnvironmentParameterDefinition("ibl_bind_to_camera", "bool"),
    EnvironmentParameterDefinition("fog_enabled", "bool"),
    EnvironmentParameterDefinition("fog_color", "string"),
    EnvironmentParameterDefinition(
        "fog_density", "float", min_value=0.0, max_value=1.0
    ),
    EnvironmentParameterDefinition("fog_near", "float", min_value=0.0, max_value=20.0),
    EnvironmentParameterDefinition("fog_far", "float", min_value=0.0, max_value=20.0),
    EnvironmentParameterDefinition("fog_height_enabled", "bool"),
    EnvironmentParameterDefinition(
        "fog_least_intense_y", "float", min_value=-100.0, max_value=100.0
    ),
    EnvironmentParameterDefinition(
        "fog_most_intense_y", "float", min_value=-100.0, max_value=100.0
    ),
    EnvironmentParameterDefinition(
        "fog_height_curve", "float", min_value=0.0, max_value=4.0
    ),
    EnvironmentParameterDefinition("fog_transmit_enabled", "bool"),
    EnvironmentParameterDefinition(
        "fog_transmit_curve", "float", min_value=0.0, max_value=4.0
    ),
    EnvironmentParameterDefinition("ao_enabled", "bool"),
    EnvironmentParameterDefinition(
        "ao_strength", "float", min_value=0.0, max_value=100.0
    ),
    EnvironmentParameterDefinition(
        "ao_radius", "float", min_value=0.001, max_value=0.05
    ),
    EnvironmentParameterDefinition(
        "ao_softness", "float", min_value=0.0, max_value=50.0
    ),
    EnvironmentParameterDefinition("ao_dither", "bool"),
    EnvironmentParameterDefinition(
        "ao_sample_rate",
        "int",
        min_value=2,
        max_value=8,
        allowed_values=(2, 3, 4, 6, 8),
    ),
)

SCENE_PARAMETERS: Tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition(
        "scale_factor", "float", min_value=0.01, max_value=1000.0
    ),
    EnvironmentParameterDefinition("exposure", "float", min_value=0.0, max_value=32.0),
    EnvironmentParameterDefinition("default_clear_color", "string"),
    EnvironmentParameterDefinition("model_base_color", "string"),
    EnvironmentParameterDefinition(
        "model_roughness", "float", min_value=0.0, max_value=1.0
    ),
    EnvironmentParameterDefinition(
        "model_metalness", "float", min_value=0.0, max_value=1.0
    ),
)

ANIMATION_PARAMETERS: Tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition("is_running", "bool"),
    EnvironmentParameterDefinition(
        "amplitude", "float", min_value=0.0, max_value=180.0
    ),
    EnvironmentParameterDefinition("frequency", "float", min_value=0.0, max_value=50.0),
)

ENVIRONMENT_REQUIRED_KEYS = frozenset(defn.key for defn in ENVIRONMENT_PARAMETERS)
ENVIRONMENT_CONTEXT_PROPERTIES: Dict[str, str] = {
    "background_mode": "startBackgroundMode",
    "background_color": "startBackgroundColor",
    "skybox_enabled": "startSkyboxEnabled",
    "ibl_enabled": "startIblEnabled",
    "ibl_intensity": "startIblIntensity",
    "skybox_brightness": "startSkyboxBrightness",
    "probe_horizon": "startProbeHorizon",
    "reflection_enabled": "startReflectionEnabled",
    "reflection_padding_m": "startReflectionPadding",
    "reflection_quality": "startReflectionQuality",
    "reflection_refresh_mode": "startReflectionRefreshMode",
    "reflection_time_slicing": "startReflectionTimeSlicing",
    "ibl_rotation": "startIblRotation",
    "ibl_source": "startIblSource",
    "skybox_blur": "startSkyboxBlur",
    "ibl_offset_x": "startIblOffsetX",
    "ibl_offset_y": "startIblOffsetY",
    "ibl_bind_to_camera": "startIblBindToCamera",
    "fog_enabled": "startFogEnabled",
    "fog_color": "startFogColor",
    "fog_density": "startFogDensity",
    "fog_near": "startFogNear",
    "fog_far": "startFogFar",
    "fog_height_enabled": "startFogHeightEnabled",
    "fog_least_intense_y": "startFogLeastY",
    "fog_most_intense_y": "startFogMostY",
    "fog_height_curve": "startFogHeightCurve",
    "fog_transmit_enabled": "startFogTransmitEnabled",
    "fog_transmit_curve": "startFogTransmitCurve",
    "ao_enabled": "startAoEnabled",
    "ao_strength": "startAoStrength",
    "ao_radius": "startAoRadius",
    "ao_softness": "startAoSoftness",
    "ao_dither": "startAoDither",
    "ao_sample_rate": "startAoSampleRate",
}


_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_ENVIRONMENT_KEY_ALIASES: Dict[str, str] = {
    "ibl_background_enabled": "skybox_enabled",
    "iblbackgroundenabled": "skybox_enabled",
}


def _camel_to_snake(name: str) -> str:
    if not isinstance(name, str):
        return name
    token = name.strip()
    if not token:
        return token
    token = token.replace("-", "_")
    converted = _CAMEL_BOUNDARY.sub("_", token)
    return converted.lower()


def _normalise_environment_key(key: str) -> str:
    if not isinstance(key, str):
        return key
    trimmed = key.strip()
    if not trimmed:
        return trimmed

    direct_alias = _ENVIRONMENT_KEY_ALIASES.get(trimmed)
    if direct_alias:
        return direct_alias

    snake = _camel_to_snake(trimmed)
    alias = _ENVIRONMENT_KEY_ALIASES.get(snake)
    if alias:
        return alias

    if trimmed in ENVIRONMENT_REQUIRED_KEYS:
        return trimmed
    if snake in ENVIRONMENT_REQUIRED_KEYS:
        return snake
    return snake


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
                raise EnvironmentValidationError(
                    "'fog_far' must be greater than or equal to 'fog_near'"
                )

    return normalized


def _prepare_environment_payload(settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict):
        raise EnvironmentValidationError("environment settings must be a dict")

    normalised: Dict[str, Any] = {}
    for raw_key, value in dict(settings).items():
        key = _normalise_environment_key(raw_key)
        if key in normalised and key != raw_key:
            continue
        normalised[key] = value

    payload = normalised

    if "skybox_enabled" not in payload and "ibl_enabled" in payload:
        payload["skybox_enabled"] = payload["ibl_enabled"]

    if "skybox_brightness" not in payload:
        if "probe_brightness" in payload:
            payload["skybox_brightness"] = payload["probe_brightness"]
        else:
            payload["skybox_brightness"] = 1.0

    payload.pop("probe_brightness", None)

    return payload


def validate_environment_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    payload = _prepare_environment_payload(settings)
    return _validate_section(payload, ENVIRONMENT_PARAMETERS, "environment")


def validate_scene_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    return _validate_section(settings, SCENE_PARAMETERS, "scene")


def validate_animation_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    return _validate_section(settings, ANIMATION_PARAMETERS, "animation")


def _build_payload(
    definitions: Sequence[EnvironmentParameterDefinition],
) -> Dict[str, Any]:
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
            if defn.allowed_values:
                payload[defn.key] = defn.allowed_values[0]
            elif defn.allow_empty_string:
                payload[defn.key] = ""
            elif defn.key.endswith("_color"):
                payload[defn.key] = "#000000"
            else:
                payload[defn.key] = defn.key
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
