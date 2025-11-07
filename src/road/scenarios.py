"""
Predefined road scenarios and presets
Highway, urban, offroad, and maneuver scenarios with typical parameters
"""

from .types import SourceKind, Iso8608Class, CorrelationSpec, Preset


def create_highway_preset(velocity: float = 27.8, duration: float = 60.0) -> Preset:
    """Highway scenario: smooth roads at high speed

    Args:
        velocity: Vehicle velocity (m/s) - default 100 km/h
        duration: Scenario duration (s)

    Returns:
        Highway preset configuration
    """
    return Preset(
        name="Highway",
        source_kind=SourceKind.ISO8608,
        velocity=velocity,
        duration=duration,
        # ISO parameters
        iso_class=Iso8608Class.C,  # Average highway condition
        # High correlation on highways (similar left/right conditions)
        correlation=CorrelationSpec(rho_LR=0.85, method="coherence", seed=42),
        # High sampling for smooth highways
        resample_hz=1000.0,
    )


def create_urban_preset(velocity: float = 13.9, duration: float = 120.0) -> Preset:
    """Urban scenario: mixed surface with speed bumps

    Args:
        velocity: Vehicle velocity (m/s) - default 50 km/h
        duration: Scenario duration (s)

    Returns:
        Urban preset configuration
    """
    return Preset(
        name="Urban",
        source_kind=SourceKind.ISO8608,  # Base road surface
        velocity=velocity,
        duration=duration,
        # ISO parameters - more variation in urban areas
        iso_class=Iso8608Class.D,
        # Speed bump parameters (will be added as features)
        feature_length=3.7,  # Standard speed bump length (m)
        feature_height=0.08,  # 8cm height (within 10cm TRL limit)
        feature_spacing=200.0,  # Average spacing between speed bumps (m)
        # Moderate correlation (different wear patterns)
        correlation=CorrelationSpec(rho_LR=0.7, method="coherence", seed=123),
        resample_hz=1000.0,
    )


def create_offroad_preset(velocity: float = 15.0, duration: float = 180.0) -> Preset:
    """Off-road scenario: rough terrain

    Args:
        velocity: Vehicle velocity (m/s) - default 54 km/h
        duration: Scenario duration (s)

    Returns:
        Off-road preset configuration
    """
    return Preset(
        name="Offroad",
        source_kind=SourceKind.ISO8608,
        velocity=velocity,
        duration=duration,
        # Rough terrain
        iso_class=Iso8608Class.F,  # Extremely poor roads
        # Low correlation on off-road (independent tracks)
        correlation=CorrelationSpec(rho_LR=0.4, method="coherence", seed=456),
        resample_hz=1000.0,
    )


def create_maneuver_preset(
    maneuver_type: str = "double_lane_change",
    velocity: float = 20.0,
    duration: float = 30.0,
) -> Preset:
    """Maneuver scenario: standardized test maneuvers

    Args:
        maneuver_type: 'double_lane_change', 'sine_sweep', 'step_steer'
        velocity: Vehicle velocity (m/s) - default 72 km/h
        duration: Scenario duration (s)

    Returns:
        Maneuver preset configuration
    """
    if maneuver_type == "double_lane_change":
        # ISO 3888-1 double lane change
        # Minimal road excitation, focus on lateral dynamics
        return Preset(
            name=f"Maneuver_{maneuver_type}",
            source_kind=SourceKind.ISO8608,
            velocity=velocity,
            duration=duration,
            # Very smooth road for maneuver testing
            iso_class=Iso8608Class.B,
            # High correlation (consistent surface)
            correlation=CorrelationSpec(rho_LR=0.95, method="coherence", seed=789),
            resample_hz=1000.0,
        )

    elif maneuver_type == "sine_sweep":
        # Sinusoidal steering input equivalent
        return Preset(
            name=f"Maneuver_{maneuver_type}",
            source_kind=SourceKind.SWEEP,
            velocity=velocity,
            duration=duration,
            # Sweep parameters
            amplitude=0.02,  # 2cm road variation
            frequency=0.1,  # Start frequency (Hz)
            correlation=CorrelationSpec(rho_LR=0.9, method="coherence"),
            resample_hz=1000.0,
        )

    elif maneuver_type == "step_steer":
        # Step steering input equivalent
        return Preset(
            name=f"Maneuver_{maneuver_type}",
            source_kind=SourceKind.STEP,
            velocity=velocity,
            duration=duration,
            # Step parameters
            amplitude=0.05,  # 5cm step height
            correlation=CorrelationSpec(rho_LR=0.95, method="coherence"),
            resample_hz=1000.0,
        )

    else:
        raise ValueError(f"Unknown maneuver type: {maneuver_type}")


def create_test_preset(
    test_type: str = "pothole", velocity: float = 16.7, duration: float = 20.0
) -> Preset:
    """Test scenario: specific road features for testing

    Args:
        test_type: 'pothole', 'speed_bump', 'sine_wave'
        velocity: Vehicle velocity (m/s) - default 60 km/h
        duration: Scenario duration (s)

    Returns:
        Test preset configuration
    """
    if test_type == "pothole":
        return Preset(
            name=f"Test_{test_type}",
            source_kind=SourceKind.POTHOLE,
            velocity=velocity,
            duration=duration,
            # Pothole parameters
            feature_length=2.0,  # 2m long pothole
            feature_height=0.15,  # 15cm deep
            correlation=CorrelationSpec(rho_LR=0.6, method="coherence"),
            resample_hz=1000.0,
        )

    elif test_type == "speed_bump":
        return Preset(
            name=f"Test_{test_type}",
            source_kind=SourceKind.SPEED_BUMP,
            velocity=velocity,
            duration=duration,
            # TRL-compliant speed bump
            feature_length=3.7,  # 3.7m length
            feature_height=0.1,  # 10cm height (max allowed)
            correlation=CorrelationSpec(rho_LR=0.9, method="coherence"),
            resample_hz=1000.0,
        )

    elif test_type == "sine_wave":
        return Preset(
            name=f"Test_{test_type}",
            source_kind=SourceKind.SINE,
            velocity=velocity,
            duration=duration,
            # Sine wave parameters
            amplitude=0.05,  # 5cm amplitude
            frequency=1.0,  # 1 Hz
            phase=0.0,
            correlation=CorrelationSpec(rho_LR=1.0, method="coherence"),
            resample_hz=1000.0,
        )

    else:
        raise ValueError(f"Unknown test type: {test_type}")


def get_all_presets() -> dict[str, Preset]:
    """Get dictionary of all available presets

    Returns:
        Dictionary mapping preset names to Preset objects
    """
    presets = {}

    # Highway presets
    presets["highway_100kmh"] = create_highway_preset(velocity=27.8, duration=60.0)
    presets["highway_120kmh"] = create_highway_preset(velocity=33.3, duration=60.0)

    # Urban presets
    presets["urban_50kmh"] = create_urban_preset(velocity=13.9, duration=120.0)
    presets["urban_30kmh"] = create_urban_preset(velocity=8.3, duration=180.0)

    # Off-road presets
    presets["offroad_moderate"] = create_offroad_preset(velocity=15.0, duration=180.0)
    presets["offroad_slow"] = create_offroad_preset(velocity=8.0, duration=300.0)

    # Maneuver presets
    presets["dlc_72kmh"] = create_maneuver_preset(
        "double_lane_change", velocity=20.0, duration=30.0
    )
    presets["sine_sweep"] = create_maneuver_preset(
        "sine_sweep", velocity=16.7, duration=20.0
    )
    presets["step_steer"] = create_maneuver_preset(
        "step_steer", velocity=16.7, duration=15.0
    )

    # Test presets
    presets["test_pothole"] = create_test_preset(
        "pothole", velocity=16.7, duration=20.0
    )
    presets["test_speed_bump"] = create_test_preset(
        "speed_bump", velocity=8.3, duration=20.0
    )
    presets["test_sine"] = create_test_preset("sine_wave", velocity=16.7, duration=10.0)

    return presets


def get_preset_by_name(name: str) -> Preset | None:
    """Get preset by name

    Args:
        name: Preset name

    Returns:
        Preset object or None if not found
    """
    presets = get_all_presets()
    return presets.get(name)


def list_preset_names() -> list[str]:
    """Get list of all preset names

    Returns:
        List of preset names
    """
    return list(get_all_presets().keys())


def get_presets_by_category() -> dict[str, list[str]]:
    """Get presets organized by category

    Returns:
        Dictionary mapping categories to preset name lists
    """
    categories = {"Highway": [], "Urban": [], "Offroad": [], "Maneuver": [], "Test": []}

    for name, preset in get_all_presets().items():
        if "highway" in name:
            categories["Highway"].append(name)
        elif "urban" in name:
            categories["Urban"].append(name)
        elif "offroad" in name:
            categories["Offroad"].append(name)
        elif "dlc" in name or "sine_sweep" in name or "step_steer" in name:
            categories["Maneuver"].append(name)
        elif "test" in name:
            categories["Test"].append(name)

    return categories


# Double lane change geometry (ISO 3888-1) - metadata for future use
ISO3888_DLC_GEOMETRY = {
    "lane_width": 3.5,  # m
    "cone_spacing": 12.0,  # m (longitudinal)
    "offset_distance": 3.5,  # m (lateral offset)
    "entry_length": 12.0,  # m
    "maneuver_length": 13.0,  # m
    "exit_length": 12.0,  # m
    "total_length": 37.0,  # m
    "recommended_speed": 20.0,  # m/s (72 km/h)
}


# TRL speed bump specifications - reference data
TRL_SPEED_BUMP_SPECS = {
    "sinusoidal": {
        "length": 3.7,  # m
        "max_height": 0.1,  # m
        "recommended_speeds": [8.3, 11.1, 13.9],  # 30, 40, 50 km/h
    },
    "circular": {
        "length": 3.7,  # m
        "max_height": 0.1,  # m
        "recommended_speeds": [8.3, 11.1],  # 30, 40 km/h
    },
}


# Export functions and constants
__all__ = [
    "create_highway_preset",
    "create_urban_preset",
    "create_offroad_preset",
    "create_maneuver_preset",
    "create_test_preset",
    "get_all_presets",
    "get_preset_by_name",
    "list_preset_names",
    "get_presets_by_category",
    "ISO3888_DLC_GEOMETRY",
    "TRL_SPEED_BUMP_SPECS",
]
