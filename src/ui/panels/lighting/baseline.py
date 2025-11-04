"""Structured access to the lighting baseline catalogue.

The renovation plan keeps baseline material presets, tonemapping presets and
HDR skybox metadata inside ``config/baseline/materials.json``.  This module
provides typed helpers that normalise the JSON payload into predictable data
structures so UI code and maintenance scripts can reason about it without
sprinkling validation logic everywhere.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

DEFAULT_BASELINE_PATH = Path("config/baseline/materials.json")
_ALLOWED_ORIENTATIONS = {"z-up", "y-up"}


class BaselineLoadError(RuntimeError):
    """Raised when the baseline payload is malformed."""


@dataclass(frozen=True)
class MaterialDefinition:
    """Normalised material preset."""

    id: str
    base_color: str
    roughness: float
    metalness: float
    label_key: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "base_color": self.base_color,
            "roughness": self.roughness,
            "metalness": self.metalness,
        }
        if self.label_key:
            payload["label_key"] = self.label_key
        if self.extras:
            payload.update(self.extras)
        return payload


@dataclass(frozen=True)
class TonemapPreset:
    """Tonemapping preset definition used by UI bindings."""

    id: str
    mode: str
    exposure: float
    white_point: float
    label_key: str
    description_key: str | None = None
    tonemap_enabled: bool = True
    extras: Mapping[str, Any] = field(default_factory=dict)

    def to_qml_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "mode": self.mode,
            "exposure": self.exposure,
            "whitePoint": self.white_point,
            "labelKey": self.label_key,
            "tonemapEnabled": self.tonemap_enabled,
        }
        if self.description_key:
            payload["descriptionKey"] = self.description_key
        for key, value in self.extras.items():
            payload[key] = value
        return payload

    def matches(
        self, effects_payload: Mapping[str, Any], *, tolerance: float = 1e-3
    ) -> bool:
        """Return ``True`` if the provided effects state matches the preset."""

        if not isinstance(effects_payload, Mapping):
            return False

        if effects_payload.get("tonemap_mode") != self.mode:
            return False

        try:
            exposure = float(effects_payload.get("tonemap_exposure"))
            white_point = float(effects_payload.get("tonemap_white_point"))
        except (TypeError, ValueError):
            return False

        return (
            abs(exposure - self.exposure) <= tolerance
            and abs(white_point - self.white_point) <= tolerance
        )


@dataclass(frozen=True)
class SkyboxOrientation:
    """Orientation metadata for a HDR skybox."""

    id: str
    label: str
    file: str
    orientation: str
    rotation: float
    status: str = "ok"
    notes: str | None = None


@dataclass(frozen=True)
class OrientationIssue:
    """Represents an orientation validation issue."""

    skybox: SkyboxOrientation
    kind: str
    message: str


@dataclass(frozen=True)
class MaterialsBaseline:
    """Bundled access to all baseline segments."""

    version: int
    materials: Dict[str, MaterialDefinition]
    tonemap_presets: tuple[TonemapPreset, ...]
    skyboxes: tuple[SkyboxOrientation, ...]

    def find_tonemap_preset(self, preset_id: str) -> TonemapPreset | None:
        for preset in self.tonemap_presets:
            if preset.id == preset_id:
                return preset
        return None


def _normalise_color(value: Any) -> str:
    if not isinstance(value, str):
        raise BaselineLoadError("Material base_color must be a string")
    token = value.strip()
    if not token:
        raise BaselineLoadError("Material base_color cannot be empty")
    if not token.startswith("#"):
        raise BaselineLoadError("Material base_color must be a hex colour")
    if len(token) not in {7, 9}:
        raise BaselineLoadError("Material base_color must be #RRGGBB or #RRGGBBAA")
    return token.upper()


def _coerce_float(value: Any, *, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive guard
        raise BaselineLoadError(f"{field_name} must be a numeric value") from None


def _normalise_materials(
    raw_materials: Mapping[str, Any],
) -> Dict[str, MaterialDefinition]:
    materials: Dict[str, MaterialDefinition] = {}
    for key, value in raw_materials.items():
        if not isinstance(value, Mapping):
            raise BaselineLoadError(f"Material '{key}' must be an object")
        base_color = _normalise_color(value.get("base_color", ""))
        roughness = _coerce_float(value.get("roughness", 0.5), field_name="roughness")
        metalness = _coerce_float(value.get("metalness", 0.0), field_name="metalness")
        label_key = value.get("label_key")
        extras = {
            extra_key: extra_value
            for extra_key, extra_value in value.items()
            if extra_key not in {"base_color", "roughness", "metalness", "label_key"}
        }
        materials[key] = MaterialDefinition(
            id=key,
            base_color=base_color,
            roughness=roughness,
            metalness=metalness,
            label_key=label_key if isinstance(label_key, str) else None,
            extras=extras,
        )
    return materials


def _normalise_presets(
    raw_presets: Iterable[Mapping[str, Any]],
) -> tuple[TonemapPreset, ...]:
    presets: list[TonemapPreset] = []
    seen_ids: set[str] = set()
    for item in raw_presets:
        if not isinstance(item, Mapping):
            raise BaselineLoadError("Tonemap preset entry must be an object")
        preset_id = str(item.get("id", "")).strip()
        if not preset_id:
            raise BaselineLoadError("Tonemap preset requires an 'id'")
        if preset_id in seen_ids:
            raise BaselineLoadError(f"Duplicate tonemap preset id '{preset_id}'")
        seen_ids.add(preset_id)

        mode = str(item.get("mode", "")).strip()
        if not mode:
            raise BaselineLoadError(f"Tonemap preset '{preset_id}' missing 'mode'")

        label_key = str(item.get("label_key", "")).strip()
        if not label_key:
            raise BaselineLoadError(f"Tonemap preset '{preset_id}' missing 'label_key'")

        description_key_raw = item.get("description_key")
        description_key = (
            str(description_key_raw).strip() if description_key_raw else None
        )

        exposure = _coerce_float(
            item.get("exposure", 1.0),
            field_name=f"tonemap preset '{preset_id}' exposure",
        )
        white_point = _coerce_float(
            item.get("white_point", 1.0),
            field_name=f"tonemap preset '{preset_id}' white_point",
        )
        tonemap_enabled = bool(item.get("tonemap_enabled", True))

        extras = {
            extra_key: extra_value
            for extra_key, extra_value in item.items()
            if extra_key
            not in {
                "id",
                "mode",
                "exposure",
                "white_point",
                "label_key",
                "description_key",
                "tonemap_enabled",
            }
        }

        presets.append(
            TonemapPreset(
                id=preset_id,
                mode=mode,
                exposure=exposure,
                white_point=white_point,
                label_key=label_key,
                description_key=description_key,
                tonemap_enabled=tonemap_enabled,
                extras=extras,
            )
        )
    return tuple(presets)


def _normalise_skyboxes(
    raw_skyboxes: Iterable[Mapping[str, Any]],
) -> tuple[SkyboxOrientation, ...]:
    skyboxes: list[SkyboxOrientation] = []
    seen_ids: set[str] = set()
    for item in raw_skyboxes:
        if not isinstance(item, Mapping):
            raise BaselineLoadError("Skybox entry must be an object")
        identifier = str(item.get("id", "")).strip()
        if not identifier:
            raise BaselineLoadError("Skybox entry missing 'id'")
        if identifier in seen_ids:
            raise BaselineLoadError(f"Duplicate skybox id '{identifier}'")
        seen_ids.add(identifier)

        label = str(item.get("label", identifier)).strip() or identifier
        file_name = str(item.get("file", "")).strip()
        if not file_name:
            raise BaselineLoadError(f"Skybox '{identifier}' missing file path")

        orientation_raw = str(item.get("orientation", "")).strip().lower()
        if orientation_raw not in _ALLOWED_ORIENTATIONS:
            raise BaselineLoadError(
                f"Skybox '{identifier}' orientation must be one of {_ALLOWED_ORIENTATIONS}"
            )
        rotation = _coerce_float(item.get("rotation", 0.0), field_name="rotation")
        status = str(item.get("status", "ok")).strip().lower() or "ok"
        notes_raw = item.get("notes")
        notes = str(notes_raw).strip() if isinstance(notes_raw, str) else None

        skyboxes.append(
            SkyboxOrientation(
                id=identifier,
                label=label,
                file=file_name,
                orientation=orientation_raw,
                rotation=rotation,
                status=status,
                notes=notes,
            )
        )
    return tuple(skyboxes)


def load_materials_baseline(
    path: Path | str = DEFAULT_BASELINE_PATH,
) -> MaterialsBaseline:
    """Load and normalise the baseline catalogue."""

    baseline_path = Path(path)
    if not baseline_path.exists():
        raise BaselineLoadError(f"Baseline file not found: {baseline_path}")

    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise BaselineLoadError("Baseline JSON must be an object")

    version = int(data.get("version", 1))

    raw_materials = data.get("materials", {})
    if not isinstance(raw_materials, Mapping):
        raise BaselineLoadError("materials section must be an object")

    raw_presets = data.get("tonemap_presets", [])
    if not isinstance(raw_presets, Iterable):
        raise BaselineLoadError("tonemap_presets must be an array")

    raw_skyboxes = data.get("skyboxes", [])
    if not isinstance(raw_skyboxes, Iterable):
        raise BaselineLoadError("skyboxes must be an array")

    materials = _normalise_materials(raw_materials)
    presets = _normalise_presets(raw_presets)
    skyboxes = _normalise_skyboxes(raw_skyboxes)

    return MaterialsBaseline(
        version=version,
        materials=materials,
        tonemap_presets=presets,
        skyboxes=skyboxes,
    )
