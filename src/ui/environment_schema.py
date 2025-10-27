"""Environment settings validation helpers used by tests and runtime code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Sequence
import re

__all__ = [
    "EnvironmentValidationError",
    "EnvironmentParameterDefinition",
    "ENVIRONMENT_PARAMETERS",
    "ENVIRONMENT_OPTIONAL_PARAMETERS",
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

ENVIRONMENT_OPTIONAL_PARAMETERS: tuple[EnvironmentParameterDefinition, ...] = (
    EnvironmentParameterDefinition(
        key="background_mode",
        value_type="string",
        allowed_values=("skybox", "color", "transparent"),
    ),
    EnvironmentParameterDefinition(
        key="skybox_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="ibl_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="probe_brightness",
        value_type="float",
        min_value=0.0,
        max_value=8.0,
    ),
    EnvironmentParameterDefinition(
        key="probe_horizon",
        value_type="float",
        min_value=-1.0,
        max_value=1.0,
    ),
    EnvironmentParameterDefinition(
        key="ibl_rotation",
        value_type="float",
        min_value=-1080.0,
        max_value=1080.0,
    ),
    EnvironmentParameterDefinition(
        key="ibl_source",
        value_type="string",
        allow_empty_string=True,
    ),
    EnvironmentParameterDefinition(
        key="ibl_fallback",
        value_type="string",
        allow_empty_string=True,
    ),
    EnvironmentParameterDefinition(
        key="skybox_blur",
        value_type="float",
        min_value=0.0,
        max_value=1.0,
    ),
    EnvironmentParameterDefinition(
        key="ibl_offset_x",
        value_type="float",
        min_value=-180.0,
        max_value=180.0,
    ),
    EnvironmentParameterDefinition(
        key="ibl_offset_y",
        value_type="float",
        min_value=-180.0,
        max_value=180.0,
    ),
    EnvironmentParameterDefinition(
        key="ibl_bind_to_camera",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="fog_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="fog_color",
        value_type="color",
    ),
    EnvironmentParameterDefinition(
        key="fog_density",
        value_type="float",
        min_value=0.0,
        max_value=1.0,
    ),
    EnvironmentParameterDefinition(
        key="fog_height_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="fog_least_intense_y",
        value_type="float",
        min_value=-100_000.0,
        max_value=100_000.0,
    ),
    EnvironmentParameterDefinition(
        key="fog_most_intense_y",
        value_type="float",
        min_value=-100_000.0,
        max_value=100_000.0,
    ),
    EnvironmentParameterDefinition(
        key="fog_height_curve",
        value_type="float",
        min_value=0.0,
        max_value=4.0,
    ),
    EnvironmentParameterDefinition(
        key="fog_transmit_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="fog_transmit_curve",
        value_type="float",
        min_value=0.0,
        max_value=4.0,
    ),
    EnvironmentParameterDefinition(
        key="ao_enabled",
        value_type="bool",
    ),
    EnvironmentParameterDefinition(
        key="ao_strength",
        value_type="float",
        min_value=0.0,
        max_value=100.0,
    ),
    EnvironmentParameterDefinition(
        key="ao_softness",
        value_type="float",
        min_value=0.0,
        max_value=50.0,
    ),
    EnvironmentParameterDefinition(
        key="ao_dither",
        value_type="bool",
    ),
)

ENVIRONMENT_REQUIRED_KEYS = frozenset(param.key for param in ENVIRONMENT_PARAMETERS)

ENVIRONMENT_OPTIONAL_KEYS = frozenset(
    param.key for param in ENVIRONMENT_OPTIONAL_PARAMETERS
)

ENVIRONMENT_CONTEXT_PROPERTIES: Dict[str, str] = {
    "background_mode": "startBackgroundMode",
    "background_color": "startBackgroundColor",
    "skybox_enabled": "startSkyboxEnabled",
    "ibl_enabled": "startIblEnabled",
    "ibl_intensity": "startIblIntensity",
    "probe_brightness": "startProbeBrightness",
    "probe_horizon": "startProbeHorizon",
    "ibl_rotation": "startIblRotation",
    "ibl_source": "startIblSource",
    "ibl_fallback": "startIblFallback",
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


def _coerce_parameter(
    definition: EnvironmentParameterDefinition, raw_value: Any
) -> Any:
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
        text_value = _coerce_string(definition, raw_value)
        coerced = text_value
        allowed_text = text_value if isinstance(raw_value, str) else None
    else:  # pragma: no cover - defensive guard
        raise EnvironmentValidationError(
            f"Unknown value_type for '{definition.key}': {definition.value_type}"
        )

    if definition.allowed_values and allowed_text is not None:
        lowered = allowed_text.lower()
        normalized_choice = next(
            (choice for choice in definition.choices() if choice.lower() == lowered),
            None,
        )
        if normalized_choice is None:
            raise EnvironmentValidationError(
                f"'{definition.key}' must be one of {definition.allowed_values}, got {coerced!r}"
            )
        coerced = normalized_choice

    if definition.value_type in {"float", "int"}:
        _validate_range(definition, coerced)  # type: ignore[arg-type]

    return coerced


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

        result[definition.key] = _coerce_parameter(
            definition, settings[definition.key]
        )

    for definition in ENVIRONMENT_OPTIONAL_PARAMETERS:
        if definition.key not in settings:
            continue
        result[definition.key] = _coerce_parameter(
            definition, settings[definition.key]
        )

    return result
