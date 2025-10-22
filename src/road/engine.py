"""
Road input engine - unified interface for road excitation generation
Provides RoadInput class with get_wheel_excitation(t) method
"""

import numpy as np
from typing import Dict, Optional, Any, Tuple
from scipy.interpolate import interp1d
import warnings

from .types import SourceKind, RoadConfig, validate_wheel_excitation
from .generators import (
    generate_sine_profile,
    generate_sweep_profile,
    generate_step_profile,
    generate_pothole_profile,
    generate_speed_bump_profile,
    generate_iso8608_profile,
)
from .csv_io import load_csv_profile
from .scenarios import get_preset_by_name


class RoadInput:
    """Unified road input engine for vehicle simulation

    Generates time-domain road excitation profiles for all four wheels
    with proper axle delays, correlation, and interpolation.
    """

    def __init__(self):
        """Initialize empty road input engine"""
        self.is_configured = False
        self.config: Optional[RoadConfig] = None

        # Generated profile data
        self.time_base: Optional[np.ndarray] = None
        self.wheel_profiles: Optional[Dict[str, np.ndarray]] = None
        self.interpolators: Optional[Dict[str, interp1d]] = None

        # Timing parameters
        self.duration: float = 0.0
        self.velocity: float = 0.0
        self.wheelbase: float = 0.0
        self.track: float = 0.0
        self.axle_delay: float = 0.0

    def configure(self, config: RoadConfig, system: Any = None) -> None:
        """Configure road input from configuration

        Args:
            config: Road configuration
            system: Optional pneumatic system for geometry (wheelbase, track)
        """
        self.config = config

        # Get effective parameters
        params = config.get_effective_params()

        # Extract system geometry if available
        if system is not None and hasattr(system, "frame_geom"):
            # Try to get wheelbase from system
            if hasattr(system.frame_geom, "L_wb"):
                self.wheelbase = system.frame_geom.L_wb
            else:
                self.wheelbase = params["wheelbase"]
        else:
            self.wheelbase = params["wheelbase"]

        self.track = params["track"]
        self.velocity = params["velocity"]
        self.duration = params["duration"]

        # Calculate axle delay
        self.axle_delay = self.wheelbase / self.velocity

        self.is_configured = True

    def prime(self, duration: Optional[float] = None) -> None:
        """Generate road profiles and prepare interpolators

        Args:
            duration: Override duration (uses config duration if None)
        """
        if not self.is_configured:
            raise RuntimeError("RoadInput not configured. Call configure() first.")

        if duration is not None:
            self.duration = duration

        # Add buffer for axle delays
        total_duration = self.duration + self.axle_delay * 1.5

        # Generate profiles based on source type
        self._generate_profiles(total_duration)

        # Create interpolators for fast lookup
        self._create_interpolators()

    def get_wheel_excitation(self, t: float) -> Dict[str, float]:
        """Get road excitation for all wheels at given time

        Args:
            t: Time (seconds)

        Returns:
            Dictionary with wheel excitations: {'LF': y, 'RF': y, 'LR': y, 'RR': y}
            Values in meters (positive = upward road displacement)
        """
        if not self.is_configured:
            raise RuntimeError("RoadInput not configured")

        if self.interpolators is None:
            raise RuntimeError("RoadInput not primed. Call prime() first.")

        # Get excitation for each wheel
        excitation = {}

        for wheel in ["LF", "RF", "LR", "RR"]:
            if wheel in self.interpolators:
                # Apply axle delay for rear wheels
                if wheel in ["LR", "RR"]:
                    t_delayed = t + self.axle_delay  # Rear wheels see earlier road
                else:
                    t_delayed = t

                # Interpolate
                excitation[wheel] = float(self.interpolators[wheel](t_delayed))
            else:
                excitation[wheel] = 0.0

        # Validate output format
        if not validate_wheel_excitation(excitation):
            warnings.warn("Invalid wheel excitation format generated")
            return {"LF": 0.0, "RF": 0.0, "LR": 0.0, "RR": 0.0}

        return excitation

    def get_profile_preview(
        self, duration: float = 10.0, dt: float = 0.01
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Get preview of road profiles for plotting

        Args:
            duration: Preview duration (s)
            dt: Time step (s)

        Returns:
            (time_array, wheel_profiles_dict)
        """
        if not self.is_configured:
            raise RuntimeError("RoadInput not configured")

        if self.interpolators is None:
            # Auto-prime if not done
            self.prime()

        # Generate preview time array
        t_preview = np.arange(0, duration, dt)

        # Get excitations
        preview_profiles = {
            wheel: np.zeros_like(t_preview) for wheel in ["LF", "RF", "LR", "RR"]
        }

        for i, t in enumerate(t_preview):
            excitation = self.get_wheel_excitation(t)
            for wheel in ["LF", "RF", "LR", "RR"]:
                preview_profiles[wheel][i] = excitation[wheel]

        return t_preview, preview_profiles

    def _generate_profiles(self, duration: float) -> None:
        """Generate road profiles based on configuration"""
        params = self.config.get_effective_params()
        source = self.config.source

        if source == SourceKind.SINE:
            # Generate sinusoidal profile
            t, profile = generate_sine_profile(
                duration=duration,
                velocity=params["velocity"],
                amplitude=params["amplitude"],
                frequency=params["frequency"],
                phase=params["phase"],
                resample_hz=params["resample_hz"],
            )

            # Apply to all wheels with correlation
            self._apply_correlation(t, profile, params["correlation"])

        elif source == SourceKind.SWEEP:
            # Generate sweep profile
            t, profile = generate_sweep_profile(
                duration=duration,
                velocity=params["velocity"],
                amplitude=params["amplitude"],
                f_start=params["frequency"],
                f_end=params["frequency"] * 10,  # Decade sweep
                sweep_type="logarithmic",
                phase=params["phase"],
                resample_hz=params["resample_hz"],
            )

            self._apply_correlation(t, profile, params["correlation"])

        elif source == SourceKind.STEP:
            # Generate step profile
            t, profile = generate_step_profile(
                duration=duration,
                velocity=params["velocity"],
                step_height=params["amplitude"],
                step_time=duration / 3,  # Step at 1/3 duration
                rise_time=0.1,
                resample_hz=params["resample_hz"],
            )

            self._apply_correlation(t, profile, params["correlation"])

        elif source == SourceKind.POTHOLE:
            # Generate pothole profile
            preset = self.config.preset
            if preset:
                pothole_length = preset.feature_length
                pothole_depth = preset.feature_height
            else:
                pothole_length = 2.0
                pothole_depth = params.get("amplitude", 0.1)

            t, profile = generate_pothole_profile(
                duration=duration,
                velocity=params["velocity"],
                pothole_depth=pothole_depth,
                pothole_length=pothole_length,
                pothole_center_time=duration / 2,  # Center pothole
                resample_hz=params["resample_hz"],
            )

            self._apply_correlation(t, profile, params["correlation"])

        elif source == SourceKind.SPEED_BUMP:
            # Generate speed bump profile
            preset = self.config.preset
            if preset:
                bump_length = preset.feature_length
                bump_height = preset.feature_height
            else:
                bump_length = 3.7
                bump_height = params.get("amplitude", 0.1)

            t, profile = generate_speed_bump_profile(
                duration=duration,
                velocity=params["velocity"],
                bump_height=bump_height,
                bump_length=bump_length,
                bump_center_time=duration / 2,  # Center bump
                profile_type="sinusoidal",
                resample_hz=params["resample_hz"],
            )

            self._apply_correlation(t, profile, params["correlation"])

        elif source == SourceKind.ISO8608:
            # Generate ISO 8608 stochastic profile
            preset = self.config.preset
            if preset and preset.iso_class:
                iso_class = preset.iso_class
            else:
                from .types import Iso8608Class

                iso_class = Iso8608Class.C  # Default

            t, profiles_dict = generate_iso8608_profile(
                duration=duration,
                velocity=params["velocity"],
                iso_class=iso_class,
                correlation=params["correlation"],
                resample_hz=params["resample_hz"],
            )

            # Map left/right to wheels
            self._map_lr_to_wheels(t, profiles_dict)

        elif source == SourceKind.CSV:
            # Load from CSV file
            if not params["csv_path"]:
                raise ValueError("CSV path not specified in configuration")

            t, wheel_profiles = load_csv_profile(
                filepath=params["csv_path"],
                format_type=params["csv_format"],
                wheelbase=self.wheelbase,
                velocity=params["velocity"],
                correlation=params["correlation"],
                resample_hz=params["resample_hz"],
            )

            self.time_base = t
            self.wheel_profiles = wheel_profiles

        else:
            raise ValueError(f"Unsupported source type: {source}")

    def _apply_correlation(
        self, t: np.ndarray, base_profile: np.ndarray, correlation: Any
    ) -> None:
        """Apply correlation to generate 4-wheel profiles from single profile"""

        # Generate correlated right track
        if correlation and correlation.rho_LR < 1.0:
            np.random.seed(correlation.seed)
            noise = (
                np.random.randn(len(base_profile))
                * np.std(base_profile)
                * np.sqrt(1 - correlation.rho_LR**2)
            )
            right_profile = correlation.rho_LR * base_profile + noise
        else:
            right_profile = base_profile.copy()

        # Apply axle delays
        # Front: no delay, Rear: delayed by axle_delay
        dt = t[1] - t[0]
        delay_samples = int(self.axle_delay / dt)

        # Create rear profiles by shifting
        rear_left = np.zeros_like(base_profile)
        rear_right = np.zeros_like(right_profile)

        if delay_samples < len(base_profile):
            rear_left[delay_samples:] = base_profile[:-delay_samples]
            rear_right[delay_samples:] = right_profile[:-delay_samples]

        self.time_base = t
        self.wheel_profiles = {
            "LF": base_profile,
            "RF": right_profile,
            "LR": rear_left,
            "RR": rear_right,
        }

    def _map_lr_to_wheels(
        self, t: np.ndarray, profiles_dict: Dict[str, np.ndarray]
    ) -> None:
        """Map left/right profiles to 4 wheels with axle delay"""

        left_profile = profiles_dict["left"]
        right_profile = profiles_dict["right"]

        # Apply axle delays
        dt = t[1] - t[0]
        delay_samples = int(self.axle_delay / dt)

        # Create rear profiles by shifting
        rear_left = np.zeros_like(left_profile)
        rear_right = np.zeros_like(right_profile)

        if delay_samples < len(left_profile):
            rear_left[delay_samples:] = left_profile[:-delay_samples]
            rear_right[delay_samples:] = right_profile[:-delay_samples]

        self.time_base = t
        self.wheel_profiles = {
            "LF": left_profile,
            "RF": right_profile,
            "LR": rear_left,
            "RR": rear_right,
        }

    def _create_interpolators(self) -> None:
        """Create interpolation functions for fast wheel excitation lookup"""

        if self.time_base is None or self.wheel_profiles is None:
            raise RuntimeError("No profiles generated")

        self.interpolators = {}

        for wheel, profile in self.wheel_profiles.items():
            # Use linear interpolation with extrapolation
            self.interpolators[wheel] = interp1d(
                self.time_base,
                profile,
                kind="linear",
                bounds_error=False,
                fill_value=0.0,  # Zero outside bounds
            )

    def get_info(self) -> Dict[str, Any]:
        """Get information about current configuration

        Returns:
            Dictionary with configuration and status info
        """
        info = {
            "configured": self.is_configured,
            "primed": self.interpolators is not None,
            "source": self.config.source.name if self.config else None,
            "duration": self.duration,
            "velocity": self.velocity,
            "wheelbase": self.wheelbase,
            "track": self.track,
            "axle_delay": self.axle_delay,
        }

        if self.time_base is not None:
            info.update(
                {
                    "time_range": (self.time_base[0], self.time_base[-1]),
                    "sample_count": len(self.time_base),
                    "sample_rate": len(self.time_base)
                    / (self.time_base[-1] - self.time_base[0]),
                }
            )

        if self.wheel_profiles is not None:
            # Profile statistics
            stats = {}
            for wheel, profile in self.wheel_profiles.items():
                stats[wheel] = {
                    "min": float(np.min(profile)),
                    "max": float(np.max(profile)),
                    "rms": float(np.sqrt(np.mean(profile**2))),
                    "std": float(np.std(profile)),
                }
            info["profile_stats"] = stats

        return info


# Convenience functions for quick setup
def create_road_input_from_preset(preset_name: str, **overrides) -> RoadInput:
    """Create configured RoadInput from preset name

    Args:
        preset_name: Name of preset to use
        **overrides: Parameter overrides

    Returns:
        Configured RoadInput instance
    """
    preset = get_preset_by_name(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    # Apply overrides to preset
    for key, value in overrides.items():
        if hasattr(preset, key):
            setattr(preset, key, value)

    # Create configuration
    config = RoadConfig(source=preset.source_kind, preset=preset)

    # Create and configure road input
    road_input = RoadInput()
    road_input.configure(config)

    return road_input


# Export main classes and functions
__all__ = ["RoadInput", "create_road_input_from_preset"]
