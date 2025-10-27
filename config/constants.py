"""Centralized access to static configuration constants."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from src.core.settings_service import SettingsService, get_settings_service


def _get_service(custom_path: str | None = None) -> SettingsService:
    if custom_path is not None:
        return SettingsService(custom_path)
    return get_settings_service()


def _load_settings(custom_path: str | None = None) -> Dict[str, Any]:
    """Load the JSON settings file using :class:`SettingsService`."""

    service = _get_service(custom_path)
    return service.load()


def _ensure_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(
            f"Expected '{context}' to be a JSON object in app_settings.json, "
            f"got {type(value).__name__}"
        )
    return value


def _require_mapping_key(
    container: Mapping[str, Any], key: str, context: str
) -> Mapping[str, Any]:
    if key not in container:
        raise KeyError(f"Missing '{context}.{key}' section in app_settings.json")
    return _ensure_mapping(container[key], f"{context}.{key}")


def _require_scalar_key(container: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in container:
        raise KeyError(f"Missing '{context}.{key}' value in app_settings.json")
    return container[key]


def _get_constants_root(
    root_key: str = "current",
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return the constants section for the requested root key (current/defaults_snapshot)."""
    data = _load_settings(custom_path)
    try:
        root = data[root_key]
    except KeyError as exc:
        raise KeyError(f"Missing '{root_key}' section in app_settings.json") from exc
    root_mapping = _ensure_mapping(root, root_key)
    constants = _require_mapping_key(root_mapping, "constants", root_key)
    return constants


def _get_constants_section(
    section: str,
    *,
    root_key: str = "current",
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Helper that returns a nested constants section by name."""
    constants = _get_constants_root(root_key, custom_path=custom_path)
    return _require_mapping_key(constants, section, f"{root_key}.constants")


def refresh_cache() -> None:
    """Clear the cached JSON payload (useful for tests)."""

    get_settings_service().reload()


def get_geometry_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return the entire geometry constants mapping."""
    return _get_constants_section("geometry", custom_path=custom_path)


def get_geometry_kinematics_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return geometry constants for kinematic calculations."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return _require_mapping_key(geometry, "kinematics", "constants.geometry")


def get_geometry_cylinder_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return cylinder-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return _require_mapping_key(geometry, "cylinder", "constants.geometry")


def get_geometry_visual_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return visualization-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return _require_mapping_key(geometry, "visualization", "constants.geometry")


def get_geometry_initial_state_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return constants that define the neutral geometry state."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return _require_mapping_key(geometry, "initial_state", "constants.geometry")


def get_pneumo_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return pneumatic system constants."""

    return _get_constants_section("pneumo", custom_path=custom_path)


def get_physics_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return physics constants root mapping."""

    return _get_constants_section("physics", custom_path=custom_path)


def get_physics_suspension_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return suspension-related physics constants."""

    physics = get_physics_constants(custom_path=custom_path)
    return _require_mapping_key(physics, "suspension", "constants.physics")


def get_physics_reference_axes(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return reference axis definitions used by physics helpers."""

    physics = get_physics_constants(custom_path=custom_path)
    return _require_mapping_key(physics, "reference_axes", "constants.physics")


def get_physics_validation_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return validation thresholds for physics calculations."""

    physics = get_physics_constants(custom_path=custom_path)
    return _require_mapping_key(physics, "validation", "constants.physics")


def get_physics_rigid_body_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return rigid-body defaults for physics integrators."""

    physics = get_physics_constants(custom_path=custom_path)
    return _require_mapping_key(physics, "rigid_body", "constants.physics")


def get_physics_integrator_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return solver and loop defaults for physics integration."""

    physics = get_physics_constants(custom_path=custom_path)
    return _require_mapping_key(physics, "integrator", "constants.physics")


def get_current_section(
    section: str,
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return an arbitrary section from the ``current`` settings root."""

    data = _load_settings(custom_path)
    current = _ensure_mapping(data.get("current", {}), "current")
    return _require_mapping_key(current, section, "current")


def get_simulation_settings(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return current simulation loop settings."""

    return get_current_section("simulation", custom_path=custom_path)


def get_pneumo_valve_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return configuration for check valves."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return _require_mapping_key(pneumo, "valves", "constants.pneumo")


def get_pneumo_receiver_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return receiver specification defaults."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return _require_mapping_key(pneumo, "receiver", "constants.pneumo")


def get_pneumo_gas_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return gas network defaults (time step, thermo mode, etc.)."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return _require_mapping_key(pneumo, "gas", "constants.pneumo")


def get_pneumo_master_isolation_default(
    *,
    custom_path: str | None = None,
) -> bool:
    """Return default state of the master isolation valve."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    value = _require_scalar_key(pneumo, "master_isolation_open", "constants.pneumo")
    if not isinstance(value, bool):
        raise TypeError(
            "'constants.pneumo.master_isolation_open' must be a boolean value"
        )
    return value
