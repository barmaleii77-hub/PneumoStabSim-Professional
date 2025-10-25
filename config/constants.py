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


def _get_constants_root(
    root_key: str = "current",
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return the constants section for the requested root key (current/defaults_snapshot)."""
    data = _load_settings(custom_path)
    root = data.get(root_key, {})
    constants = root.get("constants")
    if constants is None:
        raise KeyError(
            f"Missing 'constants' section under '{root_key}' in app_settings.json"
        )
    return constants


def _get_constants_section(
    section: str,
    *,
    root_key: str = "current",
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Helper that returns a nested constants section by name."""
    constants = _get_constants_root(root_key, custom_path=custom_path)
    try:
        return constants[section]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise KeyError(
            f"Missing constants section '{section}' under '{root_key}'"
        ) from exc


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
    return geometry.get("kinematics", {})


def get_geometry_cylinder_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return cylinder-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("cylinder", {})


def get_geometry_visual_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return visualization-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("visualization", {})


def get_geometry_initial_state_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return constants that define the neutral geometry state."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("initial_state", {})


def get_pneumo_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return pneumatic system constants."""

    return _get_constants_section("pneumo", custom_path=custom_path)


def get_pneumo_valve_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return configuration for check valves."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return pneumo.get("valves", {})


def get_pneumo_receiver_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return receiver specification defaults."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return pneumo.get("receiver", {})


def get_pneumo_gas_constants(
    *,
    custom_path: str | None = None,
) -> Mapping[str, Any]:
    """Return gas network defaults (time step, thermo mode, etc.)."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return pneumo.get("gas", {})


def get_pneumo_master_isolation_default(
    *,
    custom_path: str | None = None,
) -> bool:
    """Return default state of the master isolation valve."""

    pneumo = get_pneumo_constants(custom_path=custom_path)
    return bool(pneumo.get("master_isolation_open", False))
