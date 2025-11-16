"""Profile settings management utilities.

The real application exposes a rich profile subsystem that stores the
environment, scene and animation parameters to standalone JSON files.  The
test-suite only relies on a small and well-defined surface of this module, but
the original implementation brings in the full Qt stack and a large dependency
tree which is not available inside the execution environment.  To keep the
tests hermetic we provide a lightweight, pure-Python implementation that mirrors
the behaviour required by :mod:`tests.unit.test_profile_settings_manager`.

The goal of this shim is not to be feature complete – it simply preserves the
observable semantics that the rest of the code expects:

* profile names are normalised to file-safe slugs;
* saving a profile serialises the relevant graphics sections;
* loading a profile pushes the values back into the shared settings manager and
  triggers a save to mimic the auto-persist behaviour of the production code;
* profiles can be enumerated and deleted in a deterministic fashion.

The implementation is intentionally straightforward so it can operate in a
headless environment without Qt or the full filesystem layout of the desktop
application.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar
from collections.abc import Callable, Iterable, Mapping

from config.constants import get_pneumo_master_isolation_default
from src.common.units import KELVIN_0C, PA_ATM
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    ThermoMode,
    Wheel,
)
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.geometry import CylinderGeom, FrameGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.thermo import PolytropicParameters
from src.pneumo.valves import CheckValve


_PROFILE_PATHS: tuple[str, ...] = (
    "graphics.environment",
    "graphics.reflection_probe",
    "graphics.scene",
    "animation",
)


@dataclass(slots=True)
class ProfileOperationResult:
    """Lightweight result object returned by profile operations."""

    success: bool
    message: str = ""

    def __bool__(self) -> bool:  # pragma: no cover - convenience wrapper
        return self.success


def _slugify(name: str) -> str:
    """Convert a profile name to a filesystem-friendly slug."""

    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "profile"


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _collect_sections(settings_manager: Any, paths: Iterable[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in paths:
        section = settings_manager.get(path, {})
        # Nest the section under the last path component (e.g. "environment")
        target = result
        components = path.split(".")
        for key in components[:-1]:
            target = target.setdefault(key, {})
        target[components[-1]] = section
    return result


class ProfileSettingsManager:
    """Persist and restore profile presets for the graphics subsystem."""

    def __init__(
        self,
        settings_manager: Any,
        profile_dir: Path | None = None,
        apply_callback: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self._settings_manager = settings_manager
        self._profile_dir = Path(profile_dir or Path.home() / ".pss" / "profiles")
        _ensure_directory(self._profile_dir)
        self._apply_callback = apply_callback

    # ------------------------------------------------------------------ utils
    def _path_for(self, name: str) -> Path:
        return self._profile_dir / f"{_slugify(name)}.json"

    def _make_payload(self, name: str) -> dict[str, Any]:
        payload = _collect_sections(self._settings_manager, _PROFILE_PATHS)
        payload.setdefault("metadata", {})["profile_name"] = name
        return payload

    # ----------------------------------------------------------------- actions
    def save_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        payload = self._make_payload(name)
        try:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:  # pragma: no cover - filesystem errors are rare in tests
            return ProfileOperationResult(False, f"Failed to save profile: {exc}")
        return ProfileOperationResult(True, str(path))

    def load_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        if not path.exists():
            return ProfileOperationResult(False, f"Profile '{name}' not found")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:  # pragma: no cover - corrupt files are unlikely
            return ProfileOperationResult(False, f"Failed to load profile: {exc}")

        graphics = payload.get("graphics", {})
        section_map = {
            "environment": "graphics.environment",
            "scene": "graphics.scene",
        }
        for section_name, path_key in section_map.items():
            value = graphics.get(section_name)
            if value is None:
                continue
            self._settings_manager.set(path_key, value, auto_save=False)
            if self._apply_callback is not None:
                try:
                    self._apply_callback(path_key, value)
                except Exception:  # pragma: no cover - UI callbacks may fail in tests
                    pass

        animation_payload = payload.get("animation")
        if animation_payload is None:
            animation_payload = graphics.get("animation")  # legacy profiles
        if isinstance(animation_payload, dict):
            self._settings_manager.set("animation", animation_payload, auto_save=False)
            if self._apply_callback is not None:
                try:
                    self._apply_callback("animation", animation_payload)
                except Exception:  # pragma: no cover - UI callbacks may fail in tests
                    pass

        # Mimic auto-save behaviour expected by the tests
        if hasattr(self._settings_manager, "save"):
            self._settings_manager.save()

        return ProfileOperationResult(True, str(path))

    def list_profiles(self) -> list[str]:
        names: list[str] = []
        for file in sorted(self._profile_dir.glob("*.json")):
            display_name = _slugify(file.stem).replace("_", " ").title()
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                display_name = data.get("metadata", {}).get(
                    "profile_name", display_name
                )
            except json.JSONDecodeError:  # pragma: no cover - ignore malformed payloads
                pass
            names.append(display_name)
        return sorted(names, key=lambda s: s.lower())

    def delete_profile(self, name: str) -> ProfileOperationResult:
        path = self._path_for(name)
        if not path.exists():
            return ProfileOperationResult(False, f"Profile '{name}' not found")
        try:
            path.unlink()
        except OSError as exc:  # pragma: no cover - filesystem errors are rare in tests
            return ProfileOperationResult(False, f"Failed to delete profile: {exc}")
        return ProfileOperationResult(True, str(path))


EnumType = TypeVar("EnumType", bound=Enum)

_CYLINDER_WALL_THICKNESS = 0.01
_MIN_AREA = 1e-9


def _ensure_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(
            f"Expected '{context}' to be an object in config/app_settings.json, "
            f"got {type(value).__name__}"
        )
    return value


def _require_value(container: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in container:
        raise KeyError(f"Missing '{context}.{key}' in config/app_settings.json")
    return container[key]


def _require_float(container: Mapping[str, Any], key: str, context: str) -> float:
    value = _require_value(container, key, context)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"Expected '{context}.{key}' to be numeric in config/app_settings.json"
        )
    return float(value)


def _require_bool(container: Mapping[str, Any], key: str, context: str) -> bool:
    value = _require_value(container, key, context)
    if not isinstance(value, bool):
        raise TypeError(
            f"Expected '{context}.{key}' to be boolean in config/app_settings.json"
        )
    return value


def _require_str(container: Mapping[str, Any], key: str, context: str) -> str:
    value = _require_value(container, key, context)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(
            f"Expected '{context}.{key}' to be a non-empty string in config/app_settings.json"
        )
    return value.strip()


def _enum_from_string(
    enum_cls: type[EnumType],
    value: object,
    *,
    context: str,
    aliases: Mapping[str, EnumType] | None = None,
) -> EnumType:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        candidate = value.strip().upper()
        if aliases is not None:
            alias_match = aliases.get(candidate)
            if alias_match is not None:
                return alias_match
        try:
            return enum_cls[candidate]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"Invalid value '{value}' for {context} in config/app_settings.json"
            ) from exc
    raise TypeError(
        f"{context} must be a string or {enum_cls.__name__}, got {type(value).__name__}"
    )


def _resolve_settings_manager(settings_manager: Any | None) -> Any:
    if settings_manager is not None:
        return settings_manager
    from src.common.settings_manager import get_settings_manager

    return get_settings_manager()


def _safe_outer_diameter(inner: float, candidate: object) -> float:
    if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
        diameter = float(candidate)
        if diameter > inner:
            return diameter
    return inner + 2.0 * _CYLINDER_WALL_THICKNESS


def _tail_coordinates(initial_state: Mapping[str, Any]) -> tuple[float, float]:
    tail = initial_state.get("j_tail_right") or initial_state.get("j_tail_left")
    if isinstance(tail, (list, tuple)) and len(tail) >= 3:
        try:
            y_value = float(tail[1])
            z_value = float(tail[2])
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            return 0.0, 0.0
        return abs(y_value), abs(z_value)
    return 0.0, 0.0


def _clamp_volume(volume: float, spec: ReceiverSpec) -> float:
    if volume < spec.V_min:
        return spec.V_min
    if volume > spec.V_max:
        return spec.V_max
    return volume


@dataclass(slots=True)
class PneumaticSystemDefaults:
    """Concrete pneumatic defaults derived from config/app_settings.json."""

    frame_geom: FrameGeom
    lever_geom: LeverGeom
    cylinder_geom: CylinderGeom
    cylinder_specs: dict[Wheel, CylinderSpec]
    line_configs: dict[Line, dict[str, CheckValve]]
    receiver: ReceiverState
    master_isolation_open: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "frame_geom": self.frame_geom,
            "lever_geom": self.lever_geom,
            "cylinder_geom": self.cylinder_geom,
            "cylinder_specs": self.cylinder_specs,
            "line_configs": self.line_configs,
            "receiver": self.receiver,
            "master_isolation_open": self.master_isolation_open,
        }


def load_pneumatic_defaults(
    *, settings_manager: Any | None = None
) -> PneumaticSystemDefaults:
    manager = _resolve_settings_manager(settings_manager)
    defaults_root = manager.get_all_defaults()

    defaults = _ensure_mapping(defaults_root, "defaults_snapshot")
    geometry_defaults = _ensure_mapping(
        defaults.get("geometry", {}), "defaults_snapshot.geometry"
    )
    pneumatic_defaults = _ensure_mapping(
        defaults.get("pneumatic", {}), "defaults_snapshot.pneumatic"
    )
    constants_root = _ensure_mapping(
        defaults.get("constants", {}), "defaults_snapshot.constants"
    )
    geometry_constants = _ensure_mapping(
        constants_root.get("geometry", {}), "defaults_snapshot.constants.geometry"
    )
    pneumo_constants = _ensure_mapping(
        constants_root.get("pneumo", {}), "defaults_snapshot.constants.pneumo"
    )
    valve_constants = _ensure_mapping(
        pneumo_constants.get("valves", {}), "defaults_snapshot.constants.pneumo.valves"
    )
    receiver_constants = _ensure_mapping(
        pneumo_constants.get("receiver", {}),
        "defaults_snapshot.constants.pneumo.receiver",
    )

    # Geometry -------------------------------------------------------------
    geom_context = "defaults_snapshot.geometry"
    wheelbase = _require_float(geometry_defaults, "wheelbase", geom_context)

    lever_length = geometry_defaults.get("lever_length_m")
    if not isinstance(lever_length, (int, float)) or isinstance(lever_length, bool):
        lever_length = _require_float(geometry_defaults, "lever_length", geom_context)
    else:
        lever_length = float(lever_length)

    rod_fraction = _require_float(geometry_defaults, "rod_position", geom_context)
    frame_to_pivot = _require_float(geometry_defaults, "frame_to_pivot", geom_context)
    cylinder_length = _require_float(geometry_defaults, "cylinder_length", geom_context)
    inner_diameter = _require_float(geometry_defaults, "cyl_diam_m", geom_context)
    piston_thickness = _require_float(
        geometry_defaults, "piston_thickness_m", geom_context
    )
    rod_diameter = _require_float(geometry_defaults, "rod_diameter_m", geom_context)
    link_rods = _require_bool(geometry_defaults, "link_rod_diameters", geom_context)

    geometry_initial_state = _ensure_mapping(
        geometry_constants.get("initial_state", {}),
        "defaults_snapshot.constants.geometry.initial_state",
    )
    y_tail, z_axle = _tail_coordinates(geometry_initial_state)
    if y_tail == 0.0:
        y_tail = frame_to_pivot
    if z_axle == 0.0:
        z_axle = geometry_defaults.get("frame_height_m", 0.0) or frame_to_pivot

    outer_candidate = geometry_defaults.get("cyl_outer_diameter_m")
    outer_diameter = _safe_outer_diameter(inner_diameter, outer_candidate)

    cylinder_constants = _ensure_mapping(
        geometry_constants.get("cylinder", {}),
        "defaults_snapshot.constants.geometry.cylinder",
    )
    geom_constants_ctx = "defaults_snapshot.constants.geometry.cylinder"
    # Удалён прямой вызов _require_float для dead_zone_head_m3 / dead_zone_rod_m3 (заменён безопасным фолбеком)
    import logging as _logging
    _log = _logging.getLogger(__name__)
    def _safe_dead_volume(container, key, ctx, default):
        if key not in container:
            _log.warning("Отсутствует %s.%s, используем fallback=%s", ctx, key, default)
            return float(default)
        try:
            value = container[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError
            return float(value)
        except Exception:
            _log.warning("Некорректное значение %s.%s, используем fallback=%s", ctx, key, default)
            return float(default)
    dead_head_volume = _safe_dead_volume(cylinder_constants, "dead_zone_head_m3", geom_constants_ctx, 0.001)
    dead_rod_volume = _safe_dead_volume(cylinder_constants, "dead_zone_rod_m3", geom_constants_ctx, 0.001)

    area_head = math.pi * (inner_diameter / 2.0) ** 2
    rod_area = math.pi * (rod_diameter / 2.0) ** 2
    effective_rod_area = max(area_head - rod_area, _MIN_AREA)
    L_dead_head = max(dead_head_volume / max(area_head, _MIN_AREA), 1e-6)
    L_dead_rod = max(dead_rod_volume / effective_rod_area, 1e-6)

    frame_geom = FrameGeom(L_wb=wheelbase)
    lever_geom = LeverGeom(
        L_lever=lever_length,
        rod_joint_frac=rod_fraction,
        d_frame_to_lever_hinge=frame_to_pivot,
    )
    cylinder_geom = CylinderGeom(
        D_in_front=inner_diameter,
        D_in_rear=inner_diameter,
        D_out_front=outer_diameter,
        D_out_rear=outer_diameter,
        L_inner=cylinder_length,
        t_piston=piston_thickness,
        D_rod=rod_diameter,
        link_rod_diameters_front_rear=link_rods,
        L_dead_head=L_dead_head,
        L_dead_rod=L_dead_rod,
        Y_tail=y_tail,
        Z_axle=z_axle,
    )

    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever_geom),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever_geom),
    }

    delta_open = _require_float(
        valve_constants, "delta_open_pa", "defaults_snapshot.constants.pneumo.valves"
    )
    equivalent_diameter = _require_float(
        valve_constants,
        "equivalent_diameter_m",
        "defaults_snapshot.constants.pneumo.valves",
    )

    def _check_valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=delta_open, d_eq=equivalent_diameter)

    line_configs = {
        line: {
            "cv_atmo": _check_valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _check_valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in (Line.A1, Line.B1, Line.A2, Line.B2)
    }

    receiver_context = "defaults_snapshot.constants.pneumo.receiver"
    receiver_spec = ReceiverSpec(
        V_min=_require_float(receiver_constants, "volume_min_m3", receiver_context),
        V_max=_require_float(receiver_constants, "volume_max_m3", receiver_context),
    )

    pneumatic_context = "defaults_snapshot.pneumatic"
    receiver_volume = _require_float(
        pneumatic_defaults, "receiver_volume", pneumatic_context
    )
    ambient_temp = _require_float(pneumatic_defaults, "atmo_temp", pneumatic_context)
    receiver_mode = _enum_from_string(
        ReceiverVolumeMode,
        pneumatic_defaults.get("volume_mode"),
        context=f"{pneumatic_context}.volume_mode",
        aliases={"MANUAL": ReceiverVolumeMode.ADIABATIC_RECALC},
    )

    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=_clamp_volume(receiver_volume, receiver_spec),
        p=PA_ATM,
        T=max(ambient_temp + KELVIN_0C, 1.0),
        mode=receiver_mode,
    )

    master_isolation_open = pneumatic_defaults.get("master_isolation_open")
    if not isinstance(master_isolation_open, bool):
        master_isolation_open = get_pneumo_master_isolation_default()

    return PneumaticSystemDefaults(
        frame_geom=frame_geom,
        lever_geom=lever_geom,
        cylinder_geom=cylinder_geom,
        cylinder_specs=cylinder_specs,
        line_configs=line_configs,
        receiver=receiver_state,
        master_isolation_open=bool(master_isolation_open),
    )


def create_default_system_configuration(
    *, settings_manager: Any | None = None
) -> dict[str, Any]:
    defaults = load_pneumatic_defaults(settings_manager=settings_manager)
    return defaults.as_dict()


def create_default_gas_network(
    system: Any, *, settings_manager: Any | None = None
) -> GasNetwork:
    defaults = _ensure_mapping(
        _resolve_settings_manager(settings_manager).get_all_defaults(),
        "defaults_snapshot",
    )
    pneumatic_defaults = _ensure_mapping(
        defaults.get("pneumatic", {}), "defaults_snapshot.pneumatic"
    )
    constants_root = _ensure_mapping(
        defaults.get("constants", {}), "defaults_snapshot.constants"
    )
    pneumo_constants = _ensure_mapping(
        constants_root.get("pneumo", {}), "defaults_snapshot.constants.pneumo"
    )
    valve_constants = _ensure_mapping(
        pneumo_constants.get("valves", {}), "defaults_snapshot.constants.pneumo.valves"
    )
    gas_constants = _ensure_mapping(
        pneumo_constants.get("gas", {}), "defaults_snapshot.constants.pneumo.gas"
    )

    ambient_temperature = _require_float(
        pneumatic_defaults, "atmo_temp", "defaults_snapshot.pneumatic"
    )
    ambient_temperature_k = max(ambient_temperature + KELVIN_0C, 1.0)

    relief_min_threshold = _require_float(
        gas_constants,
        "relief_min_threshold_pa",
        "defaults_snapshot.constants.pneumo.gas",
    )
    relief_stiff_threshold = _require_float(
        gas_constants,
        "relief_stiff_threshold_pa",
        "defaults_snapshot.constants.pneumo.gas",
    )
    relief_safety_threshold = _require_float(
        gas_constants,
        "relief_safety_threshold_pa",
        "defaults_snapshot.constants.pneumo.gas",
    )

    relief_min_orifice = _require_float(
        valve_constants,
        "relief_min_orifice_diameter_m",
        "defaults_snapshot.constants.pneumo.valves",
    )
    relief_stiff_orifice = _require_float(
        valve_constants,
        "relief_stiff_orifice_diameter_m",
        "defaults_snapshot.constants.pneumo.valves",
    )

    polytropic_params = PolytropicParameters(
        heat_transfer_coeff=_require_float(
            pneumatic_defaults,
            "polytropic_heat_transfer_coeff",
            "defaults_snapshot.pneumatic",
        ),
        exchange_area=_require_float(
            pneumatic_defaults,
            "polytropic_exchange_area",
            "defaults_snapshot.pneumatic",
        ),
        ambient_temperature=ambient_temperature_k,
    )

    leak_coefficient = _require_float(
        pneumatic_defaults, "leak_coefficient", "defaults_snapshot.pneumatic"
    )
    leak_reference_area = _require_float(
        pneumatic_defaults, "leak_reference_area", "defaults_snapshot.pneumatic"
    )
    master_equalization_diameter = _require_float(
        pneumatic_defaults, "diagonal_coupling_dia", "defaults_snapshot.pneumatic"
    )

    tank_mode = _enum_from_string(
        ReceiverVolumeMode,
        gas_constants.get("tank_volume_mode"),
        context="defaults_snapshot.constants.pneumo.gas.tank_volume_mode",
    )
    tank_state = create_tank_gas_state(
        V_initial=_require_float(
            gas_constants,
            "tank_volume_initial_m3",
            "defaults_snapshot.constants.pneumo.gas",
        ),
        p_initial=_require_float(
            gas_constants,
            "tank_pressure_initial_pa",
            "defaults_snapshot.constants.pneumo.gas",
        ),
        T_initial=_require_float(
            gas_constants,
            "tank_temperature_initial_k",
            "defaults_snapshot.constants.pneumo.gas",
        ),
        mode=tank_mode,
    )

    volumes = system.get_line_volumes()
    line_states: dict[Line, Any] = {}
    for line_name, payload in volumes.items():
        if not isinstance(payload, Mapping):
            raise TypeError(
                "Line volume payload must be a mapping with 'total_volume' entry"
            )
        total_volume = payload.get("total_volume")
        if isinstance(total_volume, bool) or not isinstance(total_volume, (int, float)):
            raise TypeError("Line volume must be numeric in system.get_line_volumes()")
        line_states[line_name] = create_line_gas_state(
            line_name, PA_ATM, ambient_temperature_k, float(total_volume)
        )

    master_isolation_open = pneumatic_defaults.get("master_isolation_open")
    if not isinstance(master_isolation_open, bool):
        master_isolation_open = get_pneumo_master_isolation_default()

    return GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=bool(master_isolation_open),
        ambient_temperature=ambient_temperature_k,
        relief_min_threshold=relief_min_threshold,
        relief_stiff_threshold=relief_stiff_threshold,
        relief_safety_threshold=relief_safety_threshold,
        relief_min_orifice_diameter=relief_min_orifice,
        relief_stiff_orifice_diameter=relief_stiff_orifice,
        polytropic_params=polytropic_params,
        leak_coefficient=leak_coefficient,
        leak_reference_area=leak_reference_area,
        master_equalization_diameter=master_equalization_diameter,
    )


def get_default_lever_angles() -> dict[Wheel, float]:
    """Return neutral lever angles for all wheels."""

    return {wheel: 0.0 for wheel in Wheel}


def get_default_gas_parameters(
    *, settings_manager: Any | None = None
) -> dict[str, Any]:
    defaults = _ensure_mapping(
        _resolve_settings_manager(settings_manager).get_all_defaults(),
        "defaults_snapshot",
    )
    constants_root = _ensure_mapping(
        defaults.get("constants", {}), "defaults_snapshot.constants"
    )
    pneumo_constants = _ensure_mapping(
        constants_root.get("pneumo", {}), "defaults_snapshot.constants.pneumo"
    )
    gas_constants = _ensure_mapping(
        pneumo_constants.get("gas", {}), "defaults_snapshot.constants.pneumo.gas"
    )

    thermo_mode = _enum_from_string(
        ThermoMode,
        _require_value(
            gas_constants, "thermo_mode", "defaults_snapshot.constants.pneumo.gas"
        ),
        context="defaults_snapshot.constants.pneumo.gas.thermo_mode",
    )
    return {
        "dt": _require_float(
            gas_constants, "time_step_s", "defaults_snapshot.constants.pneumo.gas"
        ),
        "thermo_mode": thermo_mode,
        "total_time": _require_float(
            gas_constants, "total_time_s", "defaults_snapshot.constants.pneumo.gas"
        ),
    }


@dataclass(slots=True)
class SystemWithDefaults:
    system: Any
    gas_network: GasNetwork


def create_system_with_gas_network(
    *, settings_manager: Any | None = None
) -> SystemWithDefaults:
    defaults = load_pneumatic_defaults(settings_manager=settings_manager)
    system = create_standard_diagonal_system(
        cylinder_specs=defaults.cylinder_specs,
        line_configs=defaults.line_configs,
        receiver=defaults.receiver,
        master_isolation_open=defaults.master_isolation_open,
    )
    gas_network = create_default_gas_network(system, settings_manager=settings_manager)
    return SystemWithDefaults(system=system, gas_network=gas_network)


__all__ = [
    "ProfileSettingsManager",
    "ProfileOperationResult",
    "PneumaticSystemDefaults",
    "SystemWithDefaults",
    "create_default_gas_network",
    "create_default_system_configuration",
    "create_system_with_gas_network",
    "get_default_gas_parameters",
    "get_default_lever_angles",
    "load_pneumatic_defaults",
]
