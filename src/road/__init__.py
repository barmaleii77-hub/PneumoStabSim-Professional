"""
Road input module for vehicle simulation

Provides road profile generation, CSV I/O, scenarios, and unified engine interface.
Supports ISO 8608 stochastic profiles, deterministic patterns, and real-world data.
"""

from .types import (
    SourceKind,
    Iso8608Class,
    CorrelationSpec,
    Preset,
    RoadConfig,
    ISO8608_PARAMETERS,
    WHEEL_POSITIONS,
    validate_wheel_excitation,
)

from .generators import (
    generate_sine_profile,
    generate_sweep_profile,
    generate_step_profile,
    generate_pothole_profile,
    generate_speed_bump_profile,
    generate_iso8608_profile,
    validate_iso8608_profile,
)

from .csv_io import detect_csv_format, load_csv_profile, save_csv_profile

from .scenarios import (
    create_highway_preset,
    create_urban_preset,
    create_offroad_preset,
    create_maneuver_preset,
    create_test_preset,
    get_all_presets,
    get_preset_by_name,
    list_preset_names,
    get_presets_by_category,
    ISO3888_DLC_GEOMETRY,
    TRL_SPEED_BUMP_SPECS,
)

from .engine import RoadInput, create_road_input_from_preset

# Version info
__version__ = "5.0.1"

# Export main interface
__all__ = [
    # Main classes
    "RoadInput",
    # Configuration types
    "SourceKind",
    "Iso8608Class",
    "CorrelationSpec",
    "Preset",
    "RoadConfig",
    # Generator functions
    "generate_sine_profile",
    "generate_sweep_profile",
    "generate_step_profile",
    "generate_pothole_profile",
    "generate_speed_bump_profile",
    "generate_iso8608_profile",
    # CSV I/O
    "load_csv_profile",
    "save_csv_profile",
    "detect_csv_format",
    # Scenario presets
    "create_highway_preset",
    "create_urban_preset",
    "create_offroad_preset",
    "create_maneuver_preset",
    "create_test_preset",
    "get_all_presets",
    "get_preset_by_name",
    "list_preset_names",
    "get_presets_by_category",
    # Convenience functions
    "create_road_input_from_preset",
    # Validation and utilities
    "validate_wheel_excitation",
    "validate_iso8608_profile",
    # Constants and reference data
    "ISO8608_PARAMETERS",
    "WHEEL_POSITIONS",
    "ISO3888_DLC_GEOMETRY",
    "TRL_SPEED_BUMP_SPECS",
]
