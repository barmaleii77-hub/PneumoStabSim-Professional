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
from typing import Any
from collections.abc import Iterable, Mapping, Sequence

DEFAULT_BASELINE_PATH = Path("config/baseline/materials.json")
_ALLOWED_ORIENTATIONS = {"z-up", "y-up"}


class BaselineLoadError(RuntimeError):
    """Raised when the baseline payload is malformed."""


@dataclass(frozen=True)
class MaterialDefinition:
    """Normalised material preset aligned with the Phase 3 calibration targets."""

    id: str
    base_color: str
    roughness: float
    metalness: float
    specular: float | None = None
    specular_tint: float | None = None
    transmission: float | None = None
    opacity: float | None = None
    clearcoat: float | None = None
    clearcoat_roughness: float | None = None
    ior: float | None = None
    thickness: float | None = None
    attenuation_distance: float | None = None
    attenuation_color: str | None = None
    emissive_color: str | None = None
    emissive_intensity: float | None = None
    normal_strength: float | None = None
    texture_path: str | None = None
    occlusion_amount: float | None = None
    alpha_mode: str | None = None
    alpha_cutoff: float | None = None
    warning_color: str | None = None
    ok_color: str | None = None
    label_key: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "base_color": self.base_color,
            "roughness": self.roughness,
            "metalness": self.metalness,
        }
        if self.specular is not None:
            payload["specular"] = self.specular
        if self.specular_tint is not None:
            payload["specular_tint"] = self.specular_tint
        if self.transmission is not None:
            payload["transmission"] = self.transmission
        if self.opacity is not None:
            payload["opacity"] = self.opacity
        if self.clearcoat is not None:
            payload["clearcoat"] = self.clearcoat
        if self.clearcoat_roughness is not None:
            payload["clearcoat_roughness"] = self.clearcoat_roughness
        if self.ior is not None:
            payload["ior"] = self.ior
        if self.thickness is not None:
            payload["thickness"] = self.thickness
        if self.attenuation_distance is not None:
            payload["attenuation_distance"] = self.attenuation_distance
        if self.attenuation_color is not None:
            payload["attenuation_color"] = self.attenuation_color
        if self.emissive_color is not None:
            payload["emissive_color"] = self.emissive_color
        if self.emissive_intensity is not None:
            payload["emissive_intensity"] = self.emissive_intensity
        if self.normal_strength is not None:
            payload["normal_strength"] = self.normal_strength
        if self.texture_path is not None:
            payload["texture_path"] = self.texture_path
        if self.occlusion_amount is not None:
            payload["occlusion_amount"] = self.occlusion_amount
        if self.alpha_mode is not None:
            payload["alpha_mode"] = self.alpha_mode
        if self.alpha_cutoff is not None:
            payload["alpha_cutoff"] = self.alpha_cutoff
        if self.warning_color is not None:
            payload["warning_color"] = self.warning_color
        if self.ok_color is not None:
            payload["ok_color"] = self.ok_color
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
    display_order: float = 0.0
    extras: Mapping[str, Any] = field(default_factory=dict)

    def to_qml_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "mode": self.mode,
            "exposure": self.exposure,
            "whitePoint": self.white_point,
            "labelKey": self.label_key,
            "tonemapEnabled": self.tonemap_enabled,
            "order": self.display_order,
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

    def sort_key(self) -> tuple[float, str]:
        return (self.display_order, self.id)


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
    materials: dict[str, MaterialDefinition]
    tonemap_presets: tuple[TonemapPreset, ...]
    skyboxes: tuple[SkyboxOrientation, ...]

    def find_tonemap_preset(self, preset_id: str) -> TonemapPreset | None:
        for preset in self.tonemap_presets:
            if preset.id == preset_id:
                return preset
        return None

    def list_tonemap_presets(self) -> Sequence[TonemapPreset]:
        return tuple(sorted(self.tonemap_presets, key=lambda preset: preset.sort_key()))

    def detect_orientation_issues(self) -> list[OrientationIssue]:
        issues: list[OrientationIssue] = []
        for entry in self.skyboxes:
            if entry.status != "ok":
                issues.append(
                    OrientationIssue(
                        skybox=entry,
                        kind="status",
                        message=entry.notes or "Skybox flagged for manual review",
                    )
                )
                continue

            if entry.orientation != "z-up":
                issues.append(
                    OrientationIssue(
                        skybox=entry,
                        kind="orientation",
                        message=(
                            "Expected 'z-up' orientation but received"
                            f" '{entry.orientation}'"
                        ),
                    )
                )
                continue

            if abs(entry.rotation) > 180.0:
                issues.append(
                    OrientationIssue(
                        skybox=entry,
                        kind="rotation",
                        message=(
                            "Rotation offset must stay within ±180°, "
                            f"got {entry.rotation:.1f}"
                        ),
                    )
                )
                continue

            if "\\" in entry.file:
                issues.append(
                    OrientationIssue(
                        skybox=entry,
                        kind="path",
                        message="File path must use POSIX separators",
                    )
                )
                continue

            suffix = Path(entry.file).suffix.lower()
            if suffix not in {".hdr", ".exr"}:
                issues.append(
                    OrientationIssue(
                        skybox=entry,
                        kind="format",
                        message="Skybox must reference an .hdr or .exr asset",
                    )
                )
        return issues


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


def _coerce_optional_float(value: Any, *, field_name: str) -> float | None:
    if value is None:
        return None
    return _coerce_float(value, field_name=field_name)


def _normalise_optional_color(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    try:
        return _normalise_color(value)
    except BaselineLoadError as exc:  # pragma: no cover - defensive guard
        raise BaselineLoadError(f"{field_name} must be a hex colour string") from exc


def _normalise_materials(
    raw_materials: Mapping[str, Any],
) -> dict[str, MaterialDefinition]:
    materials: dict[str, MaterialDefinition] = {}
    for key, value in raw_materials.items():
        if not isinstance(value, Mapping):
            raise BaselineLoadError(f"Material '{key}' must be an object")
        base_color = _normalise_color(value.get("base_color", ""))
        roughness = _coerce_float(value.get("roughness", 0.5), field_name="roughness")
        metalness = _coerce_float(value.get("metalness", 0.0), field_name="metalness")
        label_key = value.get("label_key")
        specular = _coerce_optional_float(value.get("specular"), field_name="specular")
        specular_tint = _coerce_optional_float(
            value.get("specular_tint"), field_name="specular_tint"
        )
        transmission = _coerce_optional_float(
            value.get("transmission"), field_name="transmission"
        )
        opacity = _coerce_optional_float(value.get("opacity"), field_name="opacity")
        clearcoat = _coerce_optional_float(
            value.get("clearcoat"), field_name="clearcoat"
        )
        clearcoat_roughness = _coerce_optional_float(
            value.get("clearcoat_roughness"), field_name="clearcoat_roughness"
        )
        ior = _coerce_optional_float(value.get("ior"), field_name="ior")
        thickness = _coerce_optional_float(
            value.get("thickness"), field_name="thickness"
        )
        attenuation_distance = _coerce_optional_float(
            value.get("attenuation_distance"), field_name="attenuation_distance"
        )
        attenuation_color = _normalise_optional_color(
            value.get("attenuation_color"), field_name="attenuation_color"
        )
        emissive_color = _normalise_optional_color(
            value.get("emissive_color"), field_name="emissive_color"
        )
        emissive_intensity = _coerce_optional_float(
            value.get("emissive_intensity"), field_name="emissive_intensity"
        )
        normal_strength = _coerce_optional_float(
            value.get("normal_strength"), field_name="normal_strength"
        )
        occlusion_amount = _coerce_optional_float(
            value.get("occlusion_amount"), field_name="occlusion_amount"
        )
        alpha_cutoff = _coerce_optional_float(
            value.get("alpha_cutoff"), field_name="alpha_cutoff"
        )
        warning_color = _normalise_optional_color(
            value.get("warning_color"), field_name="warning_color"
        )
        ok_color = _normalise_optional_color(
            value.get("ok_color"), field_name="ok_color"
        )

        alpha_mode_raw = value.get("alpha_mode")
        alpha_mode = (
            str(alpha_mode_raw).strip() if isinstance(alpha_mode_raw, str) else None
        )
        if alpha_mode == "":
            alpha_mode = None

        texture_path_raw = value.get("texture_path")
        texture_path = None
        if isinstance(texture_path_raw, str):
            texture_path = texture_path_raw.strip()
            if texture_path_raw == "":
                texture_path = ""

        extras = {
            extra_key: extra_value
            for extra_key, extra_value in value.items()
            if extra_key
            not in {
                "base_color",
                "roughness",
                "metalness",
                "label_key",
                "specular",
                "specular_tint",
                "transmission",
                "opacity",
                "clearcoat",
                "clearcoat_roughness",
                "ior",
                "thickness",
                "attenuation_distance",
                "attenuation_color",
                "emissive_color",
                "emissive_intensity",
                "normal_strength",
                "texture_path",
                "occlusion_amount",
                "alpha_mode",
                "alpha_cutoff",
                "warning_color",
                "ok_color",
            }
        }
        materials[key] = MaterialDefinition(
            id=key,
            base_color=base_color,
            roughness=roughness,
            metalness=metalness,
            specular=specular,
            specular_tint=specular_tint,
            transmission=transmission,
            opacity=opacity,
            clearcoat=clearcoat,
            clearcoat_roughness=clearcoat_roughness,
            ior=ior,
            thickness=thickness,
            attenuation_distance=attenuation_distance,
            attenuation_color=attenuation_color,
            emissive_color=emissive_color,
            emissive_intensity=emissive_intensity,
            normal_strength=normal_strength,
            texture_path=texture_path,
            occlusion_amount=occlusion_amount,
            alpha_mode=alpha_mode,
            alpha_cutoff=alpha_cutoff,
            warning_color=warning_color,
            ok_color=ok_color,
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

        order_raw = item.get("order", len(presets))
        try:
            display_order = float(order_raw)
        except (TypeError, ValueError):
            display_order = float(len(presets))

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
                "order",
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
                display_order=display_order,
                extras=extras,
            )
        )
    return tuple(sorted(presets, key=lambda preset: preset.sort_key()))


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
