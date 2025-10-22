"""
Road profile generators: sine, sweep, step, pothole, speed bump, ISO 8608 stochastic
Implements deterministic and stochastic road excitation patterns
"""

import numpy as np
from scipy import signal
from typing import Tuple, Optional, Dict, Any

from .types import Iso8608Class, ISO8608_PARAMETERS, CorrelationSpec


def generate_sine_profile(
    duration: float,
    velocity: float,
    amplitude: float,
    frequency: float,
    phase: float = 0.0,
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate sinusoidal road profile

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        amplitude: Amplitude (m)
        frequency: Frequency (Hz)
        phase: Phase offset (rad)
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, profile_array) both in SI units
    """
    t = np.linspace(0, duration, int(duration * resample_hz))

    # Convert spatial frequency to temporal: f_spatial = f_temporal / velocity
    # For spatial wavelength ?: f_spatial = velocity / ?
    # For temporal frequency f: spatial_frequency = f / velocity

    # y(z) = A * sin(2? * z/? + ?) where z = v*t
    # y(t) = A * sin(2? * v*t/? + ?) = A * sin(2? * f * t + ?)
    profile = amplitude * np.sin(2 * np.pi * frequency * t + phase)

    return t, profile


def generate_sweep_profile(
    duration: float,
    velocity: float,
    amplitude: float,
    f_start: float,
    f_end: float,
    sweep_type: str = "logarithmic",
    phase: float = 0.0,
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate frequency sweep (chirp) road profile

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        amplitude: Amplitude (m)
        f_start: Starting frequency (Hz)
        f_end: Ending frequency (Hz)
        sweep_type: 'linear' or 'logarithmic'
        phase: Phase offset (rad)
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, profile_array)
    """
    t = np.linspace(0, duration, int(duration * resample_hz))

    if sweep_type == "linear":
        # Linear frequency sweep
        profile = amplitude * signal.chirp(
            t, f_start, duration, f_end, method="linear", phi=phase
        )
    elif sweep_type == "logarithmic":
        # Logarithmic frequency sweep
        profile = amplitude * signal.chirp(
            t, f_start, duration, f_end, method="logarithmic", phi=phase
        )
    else:
        raise ValueError(f"Unknown sweep_type: {sweep_type}")

    return t, profile


def generate_step_profile(
    duration: float,
    velocity: float,
    step_height: float,
    step_time: float,
    rise_time: float = 0.01,
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate step input profile

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        step_height: Step height (m, positive = up)
        step_time: Time when step occurs (s)
        rise_time: Rise time for smooth transition (s)
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, profile_array)
    """
    t = np.linspace(0, duration, int(duration * resample_hz))

    # Smooth step using sigmoid-like transition
    profile = np.zeros_like(t)

    if rise_time > 0:
        # Smooth transition using tanh
        transition = 0.5 * (1 + np.tanh((t - step_time) / (rise_time / 4)))
        profile = step_height * transition
    else:
        # Sharp step
        profile[t >= step_time] = step_height

    return t, profile


def generate_pothole_profile(
    duration: float,
    velocity: float,
    pothole_depth: float,
    pothole_length: float,
    pothole_center_time: float,
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate pothole profile

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        pothole_depth: Pothole depth (m, positive = down)
        pothole_length: Pothole length (m)
        pothole_center_time: Time when pothole center is reached (s)
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, profile_array)
    """
    t = np.linspace(0, duration, int(duration * resample_hz))

    # Convert length to time duration
    pothole_duration = pothole_length / velocity

    # Pothole profile: negative sine lobe
    profile = np.zeros_like(t)

    t_start = pothole_center_time - pothole_duration / 2
    t_end = pothole_center_time + pothole_duration / 2

    # Find indices within pothole region
    mask = (t >= t_start) & (t <= t_end)

    if np.any(mask):
        # Normalized time within pothole (0 to ?)
        t_norm = (t[mask] - t_start) / pothole_duration * np.pi
        # Negative sine lobe (pothole goes down)
        profile[mask] = -pothole_depth * np.sin(t_norm)

    return t, profile


def generate_speed_bump_profile(
    duration: float,
    velocity: float,
    bump_height: float,
    bump_length: float,
    bump_center_time: float,
    profile_type: str = "sinusoidal",
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate speed bump profile (TRL-style)

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        bump_height: Bump height (m, ? 0.1m per TRL recommendations)
        bump_length: Bump length (m, ~3.7m per TRL recommendations)
        bump_center_time: Time when bump center is reached (s)
        profile_type: 'sinusoidal' or 'circular'
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, profile_array)
    """
    t = np.linspace(0, duration, int(duration * resample_hz))

    # Convert length to time duration
    bump_duration = bump_length / velocity

    profile = np.zeros_like(t)

    t_start = bump_center_time - bump_duration / 2
    t_end = bump_center_time + bump_duration / 2

    # Find indices within bump region
    mask = (t >= t_start) & (t <= t_end)

    if np.any(mask):
        if profile_type == "sinusoidal":
            # Sinusoidal bump (positive sine lobe)
            t_norm = (t[mask] - t_start) / bump_duration * np.pi
            profile[mask] = bump_height * np.sin(t_norm)

        elif profile_type == "circular":
            # Circular arc profile
            t_norm = (t[mask] - t_start) / bump_duration  # 0 to 1
            x_norm = 2 * t_norm - 1  # -1 to 1
            # Circle equation: y = h * sqrt(1 - x?) for |x| ? 1
            y_norm = np.sqrt(np.clip(1 - x_norm**2, 0, 1))
            profile[mask] = bump_height * y_norm

        else:
            raise ValueError(f"Unknown profile_type: {profile_type}")

    return t, profile


def generate_iso8608_profile(
    duration: float,
    velocity: float,
    iso_class: Iso8608Class,
    correlation: Optional[CorrelationSpec] = None,
    resample_hz: float = 1000.0,
) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
    """Generate ISO 8608 stochastic road profile

    Generates correlated left/right track profiles according to ISO 8608 PSD specification

    Args:
        duration: Duration in seconds
        velocity: Vehicle velocity (m/s)
        iso_class: ISO 8608 roughness class (A-H)
        correlation: Left/right correlation specification
        resample_hz: Sampling frequency (Hz)

    Returns:
        (time_array, {'left': profile_left, 'right': profile_right})
    """
    if correlation is None:
        correlation = CorrelationSpec()

    # Set random seed for reproducibility
    if correlation.seed is not None:
        np.random.seed(correlation.seed)

    # Time and spatial parameters
    t = np.linspace(0, duration, int(duration * resample_hz))
    dt = t[1] - t[0]
    distance = velocity * duration

    # Spatial sampling
    dz = velocity * dt  # spatial resolution (m)
    n_samples = len(t)

    # Spatial frequency array (cycles/m)
    freqs = np.fft.fftfreq(n_samples, dz)
    freqs = freqs[: n_samples // 2 + 1]  # One-sided spectrum

    # ISO 8608 parameters
    params = ISO8608_PARAMETERS[iso_class]
    Gd = params["Gd"]  # roughness coefficient (m?/cycle)
    w = params["w"]  # waviness exponent (~2.0)
    n0 = 0.1  # reference spatial frequency (cycles/m)

    # ISO 8608 PSD: Gd(n) = Gd * (n/n0)^(-w)
    # Avoid DC component and very low frequencies
    freqs_pos = freqs[1:]  # Skip DC
    psd = Gd * (freqs_pos / n0) ** (-w)

    # Generate white noise in frequency domain
    # Use Hermitian symmetry for real output
    noise_complex = np.random.randn(len(freqs_pos)) + 1j * np.random.randn(
        len(freqs_pos)
    )

    # Scale by PSD to get colored noise
    # Factor of 2 accounts for one-sided spectrum
    amplitude_spectrum = (
        np.sqrt(2 * psd * (freqs_pos[1] - freqs_pos[0])) * noise_complex
    )

    # Construct full spectrum with Hermitian symmetry
    full_spectrum = np.zeros(n_samples, dtype=complex)
    full_spectrum[0] = 0  # DC component
    full_spectrum[1 : len(freqs_pos) + 1] = amplitude_spectrum

    # Hermitian symmetry for negative frequencies
    if n_samples % 2 == 0:
        # Even length: symmetric around nyquist
        n_neg = len(freqs_pos) - 1  # Exclude nyquist frequency
        if n_neg > 0:
            full_spectrum[-n_neg:] = np.conj(amplitude_spectrum[1 : n_neg + 1][::-1])
    else:
        # Odd length: full symmetry
        n_neg = len(freqs_pos) - 1
        if n_neg > 0:
            full_spectrum[-n_neg:] = np.conj(amplitude_spectrum[1 : n_neg + 1][::-1])

    # Generate left track profile
    profile_left = np.fft.ifft(full_spectrum).real

    # Generate correlated right track profile
    if correlation.method == "coherence":
        # Method: right = rho * left + sqrt(1-rho?) * independent_noise
        rho = correlation.rho_LR

        # Generate independent noise for right track
        noise_right_complex = np.random.randn(len(freqs_pos)) + 1j * np.random.randn(
            len(freqs_pos)
        )
        amplitude_right = (
            np.sqrt(2 * psd * (freqs_pos[1] - freqs_pos[0])) * noise_right_complex
        )

        full_spectrum_right = np.zeros(n_samples, dtype=complex)
        full_spectrum_right[1 : len(freqs_pos) + 1] = amplitude_right

        if n_samples % 2 == 0:
            n_neg = len(freqs_pos) - 1
            if n_neg > 0:
                full_spectrum_right[-n_neg:] = np.conj(
                    amplitude_right[1 : n_neg + 1][::-1]
                )
        else:
            n_neg = len(freqs_pos) - 1
            if n_neg > 0:
                full_spectrum_right[-n_neg:] = np.conj(
                    amplitude_right[1 : n_neg + 1][::-1]
                )

        independent_noise = np.fft.ifft(full_spectrum_right).real

        # Correlated right track
        profile_right = rho * profile_left + np.sqrt(1 - rho**2) * independent_noise

    elif correlation.method == "mixing":
        # Alternative method: frequency domain mixing
        profile_right = profile_left.copy()  # Start with identical

        # Add uncorrelated component in frequency domain
        if correlation.rho_LR < 1.0:
            # Generate additional noise
            noise_add = np.random.randn(n_samples) * np.sqrt(
                1 - correlation.rho_LR**2
            )
            profile_right = correlation.rho_LR * profile_left + noise_add

    else:
        raise ValueError(f"Unknown correlation method: {correlation.method}")

    return t, {"left": profile_left, "right": profile_right}


def validate_iso8608_profile(
    profile: np.ndarray,
    velocity: float,
    iso_class: Iso8608Class,
    resample_hz: float = 1000.0,
    tolerance: float = 0.5,
) -> Tuple[bool, Dict[str, Any]]:
    """Validate generated ISO 8608 profile against target PSD

    Args:
        profile: Generated profile array
        velocity: Vehicle velocity (m/s)
        iso_class: Target ISO class
        resample_hz: Sampling frequency (Hz)
        tolerance: Tolerance for PSD validation (log10 scale)

    Returns:
        (is_valid, validation_info)
    """
    # Calculate PSD using Welch's method
    dt = 1.0 / resample_hz
    dz = velocity * dt

    # Use Welch's method for PSD estimation
    freqs, psd_estimated = signal.welch(profile, fs=1 / dz, nperseg=len(profile) // 4)

    # Convert to spatial frequency (cycles/m)
    freqs = freqs[1:]  # Skip DC
    psd_estimated = psd_estimated[1:]

    # Target ISO 8608 PSD
    params = ISO8608_PARAMETERS[iso_class]
    Gd = params["Gd"]
    w = params["w"]
    n0 = 0.1

    psd_target = Gd * (freqs / n0) ** (-w)

    # Validation in log space (more appropriate for PSD)
    log_psd_estimated = np.log10(psd_estimated + 1e-15)  # Avoid log(0)
    log_psd_target = np.log10(psd_target)

    # Check if estimated PSD is within tolerance
    error = np.abs(log_psd_estimated - log_psd_target)
    is_valid = np.mean(error) < tolerance

    validation_info = {
        "mean_error_log10": np.mean(error),
        "max_error_log10": np.max(error),
        "frequency_range_hz": (freqs[0] / velocity, freqs[-1] / velocity),
        "psd_target_range": (psd_target.min(), psd_target.max()),
        "psd_estimated_range": (psd_estimated.min(), psd_estimated.max()),
        "tolerance": tolerance,
        "iso_class": iso_class.value,
    }

    return is_valid, validation_info


# Export functions
__all__ = [
    "generate_sine_profile",
    "generate_sweep_profile",
    "generate_step_profile",
    "generate_pothole_profile",
    "generate_speed_bump_profile",
    "generate_iso8608_profile",
    "validate_iso8608_profile",
]
