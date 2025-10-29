"""
Road input data types and enumerations
Defines source types, ISO 8608 classes, correlation specs, and configuration structures
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
import numpy as np


class SourceKind(Enum):
    """Road input source types"""

    SINE = auto()  # Sinusoidal excitation
    SWEEP = auto()  # Frequency sweep (chirp)
    STEP = auto()  # Step input
    POTHOLE = auto()  # Pothole profile
    SPEED_BUMP = auto()  # Speed bump (sleeping policeman)
    ISO8608 = auto()  # ISO 8608 stochastic profile
    CSV = auto()  # CSV file input


class Iso8608Class(Enum):
    """ISO 8608 road roughness classes"""

    A = "A"  # Very good (airports)
    B = "B"  # Good (highways)
    C = "C"  # Average (main roads)
    D = "D"  # Poor (secondary roads)
    E = "E"  # Very poor (unpaved)
    F = "F"  # Extremely poor (off-road)
    G = "G"  # Severe (rough terrain)
    H = "H"  # Extreme (very rough terrain)


@dataclass
class CorrelationSpec:
    """Correlation specification for left/right tracks"""

    rho_LR: float = 0.8  # Correlation coefficient (0..1)
    method: str = "coherence"  # 'coherence' or 'mixing'
    seed: Optional[int] = None  # Random seed for reproducibility

    def __post_init__(self):
        if not 0.0 <= self.rho_LR <= 1.0:
            raise ValueError(f"rho_LR must be in [0, 1], got {self.rho_LR}")
        if self.method not in ["coherence", "mixing"]:
            raise ValueError(
                f"method must be 'coherence' or 'mixing', got {self.method}"
            )


@dataclass
class Preset:
    """Predefined scenario parameters"""

    name: str  # Preset name
    source_kind: SourceKind  # Primary source type
    velocity: float  # Vehicle velocity (m/s)
    duration: float  # Scenario duration (s)

    # Source-specific parameters
    amplitude: float = 0.01  # Base amplitude (m)
    frequency: float = 1.0  # Base frequency (Hz)
    phase: float = 0.0  # Base phase (rad)

    # ISO 8608 parameters
    iso_class: Optional[Iso8608Class] = None  # ISO roughness class

    # Geometric parameters for features
    feature_length: float = 3.7  # Length of speed bumps/potholes (m)
    feature_height: float = 0.1  # Height/depth of features (m)
    feature_spacing: float = 200.0  # Average spacing between features (m)

    # Correlation
    correlation: CorrelationSpec = None

    # Sampling
    resample_hz: float = 1000.0  # Resampling frequency (Hz)

    def __post_init__(self):
        if self.correlation is None:
            self.correlation = CorrelationSpec()
        if self.velocity <= 0:
            raise ValueError(f"velocity must be positive, got {self.velocity}")
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")


@dataclass
class RoadConfig:
    """Complete road input configuration"""

    source: SourceKind  # Input source type
    preset: Optional[Preset] = None  # Predefined preset

    # Manual parameters (override preset if specified)
    velocity: Optional[float] = None  # Vehicle velocity (m/s)
    duration: Optional[float] = None  # Duration (s)
    amplitude: Optional[float] = None  # Amplitude (m)
    frequency: Optional[float] = None  # Frequency (Hz)
    phase: Optional[float] = None  # Phase (rad)

    # Vehicle geometry
    wheelbase: float = 3.2  # Wheelbase (m)
    track: float = 1.6  # Track width (m)

    # Correlation and sampling
    correlation: Optional[CorrelationSpec] = None
    resample_hz: float = 1000.0  # Sampling frequency (Hz)

    # CSV-specific
    csv_path: Optional[str] = None  # Path to CSV file
    csv_format: str = "auto"  # 'auto', 'time_z', 'time_wheels'

    def get_effective_params(self) -> Dict[str, Any]:
        """Get effective parameters (preset overridden by manual values)"""
        params = {}

        if self.preset is not None:
            preset_params = {
                "velocity": self.preset.velocity,
                "duration": self.preset.duration,
                "amplitude": self.preset.amplitude,
                "frequency": self.preset.frequency,
                "phase": self.preset.phase,
                "correlation": self.preset.correlation,
                "resample_hz": self.preset.resample_hz,
            }
            params.update(preset_params)
        else:
            # Default values when no preset
            default_params = {
                "velocity": 25.0,
                "duration": 60.0,
                "amplitude": 0.01,
                "frequency": 1.0,
                "phase": 0.0,
                "correlation": CorrelationSpec(),
                "resample_hz": 1000.0,
            }
            params.update(default_params)

        # Override with manual parameters
        if self.velocity is not None:
            params["velocity"] = self.velocity
        if self.duration is not None:
            params["duration"] = self.duration
        if self.amplitude is not None:
            params["amplitude"] = self.amplitude
        if self.frequency is not None:
            params["frequency"] = self.frequency
        if self.phase is not None:
            params["phase"] = self.phase
        if self.correlation is not None:
            params["correlation"] = self.correlation

        base_params = {
            "wheelbase": self.wheelbase,
            "track": self.track,
            "resample_hz": self.resample_hz,
            "csv_path": self.csv_path,
            "csv_format": self.csv_format,
        }
        params.update(base_params)

        return params


# ISO 8608 roughness class parameters
# PSD = Gd * (n/n0)^(-w) where n0 = 0.1 cycles/m, w ? 2.0
ISO8608_PARAMETERS = {
    Iso8608Class.A: {"Gd": 1e-8, "w": 2.0},  # Very good roads
    Iso8608Class.B: {"Gd": 4e-8, "w": 2.0},  # Good roads
    Iso8608Class.C: {"Gd": 16e-8, "w": 2.0},  # Average roads
    Iso8608Class.D: {"Gd": 64e-8, "w": 2.0},  # Poor roads
    Iso8608Class.E: {"Gd": 256e-8, "w": 2.0},  # Very poor roads
    Iso8608Class.F: {"Gd": 1024e-8, "w": 2.0},  # Extremely poor
    Iso8608Class.G: {"Gd": 4096e-8, "w": 2.0},  # Severe
    Iso8608Class.H: {"Gd": 16384e-8, "w": 2.0},  # Extreme
}


# Wheel position mapping
WheelPosition = Dict[str, Union[str, float]]
WHEEL_POSITIONS = {
    "LF": {"name": "Left Front", "x": -0.8, "z": -1.6},  # Left front
    "RF": {"name": "Right Front", "x": +0.8, "z": -1.6},  # Right front
    "LR": {"name": "Left Rear", "x": -0.8, "z": +1.6},  # Left rear
    "RR": {"name": "Right Rear", "x": +0.8, "z": +1.6},  # Right rear
}


def validate_wheel_excitation(excitation: Dict[str, float]) -> bool:
    """Validate wheel excitation dictionary format"""
    required_keys = {"LF", "RF", "LR", "RR"}
    if not isinstance(excitation, dict):
        return False
    if set(excitation.keys()) != required_keys:
        return False
    return all(
        isinstance(v, (int, float)) and np.isfinite(v) for v in excitation.values()
    )


# Export main types
__all__ = [
    "SourceKind",
    "Iso8608Class",
    "CorrelationSpec",
    "Preset",
    "RoadConfig",
    "ISO8608_PARAMETERS",
    "WHEEL_POSITIONS",
    "WheelPosition",
    "validate_wheel_excitation",
]
