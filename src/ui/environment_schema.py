"""Environment settings validation helpers used by tests and runtime code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Sequence
import re

__all__ = [
    "EnvironmentValidationError",
    "EnvironmentParameterDefinition",
    "ENVIRONMENT_PARAMETERS",
    "ENVIRONMENT_REQUIRED_KEYS",
    "ENVIRONMENT_CONTEXT_PROPERTIES",
    "ENVIRONMENT_OPTIONAL_KEYS",
    "validate_environment_settings",
]

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_TRUE_SET = {"1", "true", "yes", "on"}
_FALSE_SET = {"0", "false", "no", "off"}


class EnvironmentValidationError(ValueError):
    """Raised when environment settings violate the expected contract."""


@dataclass(frozen=True)
class EnvironmentParameterDefinition:
    """A lightweight schema entry for a single environment field."""

    key: str
    value_type: str  # "bool", "float", "int", "string", "color"
    min_value: float | int | None = None
    max_value: float | int | None = None
    allowed_values: Sequence[str] | None = None
    allow_empty_string: bool = False
    pattern: re.Pattern[str] | None = None

    def choices(self) -> Iterable[str]:
        return self.allowed_values or ()


ENVIRONMENT_PARAMETERS: tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition(
        key="background_color",
        value_type="color",
    ),
    EnvironmentParameterDefinition(
        key="ibl_intensity",
        value_type="float",
        min_value=0.0,
        max_value=10.0,
    ),
    EnvironmentParameterDefinition(
        key="ao_radius",
        value_type="float",
        min_value=0.0,
        max_value=50.0,
    ),
    EnvironmentParameterDefinition(
        key="ao_sample_rate",
        value_type="int",
        min_value=0,
        max_value=128,
    ),
    EnvironmentParameterDefinition(
        key="fog_near",
        value_type="float",
        min_value=0.0,
        max_value=1_000_000.0,
    ),
    EnvironmentParameterDefinition(
        key="fog_far",
        value_type="float",
        min_value=0.0,
        max_value=1_000_000.0,
    ),
)

ENVIRONMENT_REQUIRED_KEYS = frozenset(param.key for param in ENVIRONMENT_PARAMETERS)

ENVIRONMENT_OPTIONAL_KEYS = frozenset(
    {
        "background_mode",
        "skybox_enabled",
        "ibl_enabled",
        "probe_brightness",
        "probe_horizon",
        "ibl_rotation",
        "ibl_source",
        "ibl_fallback",
        "skybox_blur",
        "ibl_offset_x",
        "ibl_offset_y",
        "ibl_bind_to_camera",
        "fog_enabled",
        "fog_color",
        "fog_density",
        "fog_height_enabled",
        "fog_least_intense_y",
        "fog_most_intense_y",
        "fog_height_curve",
        "fog_transmit_enabled",
        "fog_transmit_curve",
        "ao_enabled",
        "ao_strength",
        "ao_softness",
        "ao_dither",
    }
)

ENVIRONMENT_CONTEXT_PROPERTIES: Dict[str, str] = {
    "background_color": "startBackgroundColor",
    "ibl_intensity": "startIblIntensity",
    "ao_radius": "startAoRadius",
    "ao_sample_rate": "startAoSampleRate",
    "fog_near": "startFogNear",
    "fog_far": "startFogFar",
}


def _coerce_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        ivalue = int(value)
        if ivalue in (0, 1):
            return bool(ivalue)
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
        except ValueError as exc:  # pragma: no cover
            raise EnvironmentValidationError(
                f"'{key}' must be a numeric value, got {value!r}"
            ) from exc
    raise EnvironmentValidationError(f"'{key}' must be numeric, got {value!r}")


def _coerce_int(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise EnvironmentValidationError(f"'{key}' must be an integer, got boolean {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as exc:  # pragma: no cover
            raise EnvironmentValidationError(
                f"'{key}' must be an integer-compatible value, got {value!r}"
            ) from exc
    raise EnvironmentValidationError(f"'{key}' must be integer-compatible, got {value!r}")


def _coerce_string(defn: EnvironmentParameterDefinition, value: Any) -> str:
    text = value.strip() if isinstance(value, str) else str(value).strip()
    if not text and not defn.allow_empty_string:
        raise EnvironmentValidationError(f"'{defn.key}' cannot be empty")
    if defn.pattern and isinstance(value, str) and text and not defn.pattern.match(text):
        raise EnvironmentValidationError(
            f"'{defn.key}' must match pattern {defn.pattern.pattern}, got {text!r}"
        )
    return text


def _coerce_color(value: Any, key: str) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if not _HEX_COLOR_RE.match(text):
            raise EnvironmentValidationError(
                f"'{key}' must be a hex colour string, got {value!r}"
            )
        return text

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            raise EnvironmentValidationError(f"'{key}' colour sequence cannot be empty")
        if len(value) not in (3, 4):
            raise EnvironmentValidationError(
                f"'{key}' colour sequence must contain 3 or 4 channels, got {len(value)}"
            )
        validated: list[int] = []
        for index, channel in enumerate(value):
            if not isinstance(channel, (int, float)):
                raise EnvironmentValidationError(
                    f"'{key}' channel {index} must be numeric, got {channel!r}"
                )
            if not 0 <= channel <= 255:
                raise EnvironmentValidationError(
                    f"'{key}' channel {index} out of range 0-255: {channel!r}"
                )
            validated.append(int(channel))
        return validated

    if isinstance(value, (int, float)):
        return value

    raise EnvironmentValidationError(f"'{key}' has unsupported colour value {value!r}")


def _validate_range(defn: EnvironmentParameterDefinition, value: float | int) -> None:
    if defn.min_value is not None and value < defn.min_value:
        raise EnvironmentValidationError(
            f"'{defn.key}'={value!r} below minimum {defn.min_value!r}"
        )
    if defn.max_value is not None and value > defn.max_value:
        raise EnvironmentValidationError(
            f"'{defn.key}'={value!r} above maximum {defn.max_value!r}"
        )


def validate_environment_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict):
        raise EnvironmentValidationError("Environment settings must be a dict")

    result: Dict[str, Any] = {}
    known_keys = ENVIRONMENT_REQUIRED_KEYS | ENVIRONMENT_OPTIONAL_KEYS

    unexpected_keys = set(settings.keys()) - known_keys
    if unexpected_keys:
        raise EnvironmentValidationError(
            f"Unexpected environment keys: {sorted(unexpected_keys)}"
        )
    for definition in ENVIRONMENT_PARAMETERS:
        if definition.key not in settings:
            raise EnvironmentValidationError(f"Missing environment key: {definition.key}")

        raw_value = settings[definition.key]
        allowed_text: str | None = None

        if definition.value_type == "bool":
            coerced: Any = _coerce_bool(raw_value, definition.key)
        elif definition.value_type == "float":
            coerced = _coerce_float(raw_value, definition.key)
        elif definition.value_type == "int":
            coerced = _coerce_int(raw_value, definition.key)
        elif definition.value_type == "color":
            coerced = _coerce_color(raw_value, definition.key)
        elif definition.value_type == "string":
            coerced = _coerce_string(definition, raw_value)
            allowed_text = coerced if isinstance(raw_value, str) else None
        else:  # pragma: no cover
            raise EnvironmentValidationError(
                f"Unknown value_type for '{definition.key}': {definition.value_type}"
            )

        if definition.allowed_values and allowed_text is not None:
            lowered = allowed_text.lower()
            if lowered not in {choice.lower() for choice in definition.choices()}:
                raise EnvironmentValidationError(
                    f"'{definition.key}' must be one of {definition.allowed_values}, got {coerced!r}"
                )

        if definition.value_type in {"float", "int"}:
            _validate_range(definition, coerced)  # type: ignore[arg-type]

        result[definition.key] = coerced

    return result
