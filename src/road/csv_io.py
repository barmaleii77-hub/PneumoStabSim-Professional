"""
CSV road profile input/output
Supports RFC 4180 compliant CSV parsing with auto-detection
Handles formats: time,z and time,LF,RF,LR,RR
"""

import csv
import numpy as np
from pathlib import Path
from typing import Any
import warnings
from scipy.interpolate import interp1d

from .types import CorrelationSpec


def detect_csv_format(filepath: str, max_preview_lines: int = 10) -> dict[str, Any]:
    """Auto-detect CSV format and encoding

    Args:
        filepath: Path to CSV file
        max_preview_lines: Number of lines to preview for format detection

    Returns:
        Dictionary with detected format info
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    format_info = {
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "columns": [],
        "format_type": "unknown",
        "warnings": [],
    }

    # Try different encodings
    encodings_to_try = ["utf-8", "cp1251", "latin1"]

    for encoding in encodings_to_try:
        try:
            with open(filepath, encoding=encoding, newline="") as f:
                # Read first few lines
                preview_lines = []
                for i, line in enumerate(f):
                    if i >= max_preview_lines:
                        break
                    preview_lines.append(line.strip())

                if len(preview_lines) == 0:
                    continue

                format_info["encoding"] = encoding
                break

        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode file with any of: {encodings_to_try}")

    # Detect delimiter
    sample_line = preview_lines[0] if preview_lines else ""
    dialect = csv.Sniffer().sniff(sample_line, delimiters=",;\t")
    format_info["delimiter"] = dialect.delimiter

    # Parse header to detect format
    if len(preview_lines) >= 1:
        reader = csv.reader(preview_lines, delimiter=format_info["delimiter"])
        header = next(reader, [])

        if header:
            # Clean header (remove whitespace, convert to lowercase)
            clean_header = [col.strip().lower() for col in header]
            format_info["columns"] = clean_header

            # Determine format type
            if "time" in clean_header:
                if len(clean_header) == 2:
                    # Likely time,z format
                    format_info["format_type"] = "time_z"
                elif len(clean_header) == 5 and all(
                    wheel in clean_header for wheel in ["lf", "rf", "lr", "rr"]
                ):
                    # time,LF,RF,LR,RR format
                    format_info["format_type"] = "time_wheels"
                else:
                    format_info["format_type"] = "custom"
            else:
                # No time column detected
                if len(clean_header) == 4:
                    format_info["format_type"] = "wheels_only"
                else:
                    format_info["format_type"] = "unknown"

        # Check for potential RFC 4180 compliance issues
        for line in preview_lines[1:3]:  # Check first couple data lines
            if format_info["delimiter"] in line and '"' in line:
                # Check if quotes are properly handled
                try:
                    list(csv.reader([line], delimiter=format_info["delimiter"]))
                except csv.Error:
                    format_info["warnings"].append(
                        "Potential RFC 4180 compliance issue: improper quote handling"
                    )

            # Check for mixed line endings
            if "\r\n" in line or "\r" in line:
                format_info["warnings"].append(
                    "Mixed line endings detected (not strictly RFC 4180)"
                )

    return format_info


def load_csv_profile(
    filepath: str,
    format_type: str = "auto",
    wheelbase: float = 3.2,
    velocity: float = 25.0,
    correlation: CorrelationSpec | None = None,
    resample_hz: float = 1000.0,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Load road profile from CSV file

    Args:
        filepath: Path to CSV file
        format_type: 'auto', 'time_z', 'time_wheels', 'wheels_only'
        wheelbase: Vehicle wheelbase for rear axle delay (m)
        velocity: Vehicle velocity for time/distance conversion (m/s)
        correlation: Correlation spec for generating right track from left
        resample_hz: Target sampling frequency (Hz)

    Returns:
        (time_array, wheel_profiles_dict)
        wheel_profiles_dict keys: 'LF', 'RF', 'LR', 'RR'
    """
    # Auto-detect format if needed
    if format_type == "auto":
        format_info = detect_csv_format(filepath)
        format_type = format_info["format_type"]
        delimiter = format_info["delimiter"]
        encoding = format_info["encoding"]

        # Print warnings
        for warning in format_info["warnings"]:
            warnings.warn(f"CSV format warning: {warning}")

    else:
        # Use default parameters
        delimiter = ","
        encoding = "utf-8"

    if correlation is None:
        correlation = CorrelationSpec()

    # Read CSV data
    try:
        with open(filepath, encoding=encoding, newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)

            # Read header
            header = next(reader, [])
            header = [col.strip() for col in header]

            # Read data
            data_rows = []
            for row_num, row in enumerate(
                reader, start=2
            ):  # Start from line 2 (after header)
                try:
                    # Convert to float, skip empty cells
                    float_row = []
                    for i, cell in enumerate(row):
                        cell = cell.strip()
                        if cell == "":
                            continue
                        try:
                            float_row.append(float(cell))
                        except ValueError:
                            warnings.warn(
                                f"Invalid numeric value '{cell}' at row {row_num}, column {i + 1}"
                            )
                            continue

                    if len(float_row) >= 2:  # At least time and one profile
                        data_rows.append(float_row)

                except Exception as e:
                    warnings.warn(f"Error parsing row {row_num}: {e}")
                    continue

            if len(data_rows) == 0:
                raise ValueError("No valid data rows found in CSV")

            # Convert to numpy array
            data = np.array(data_rows)

    except Exception as e:
        raise RuntimeError(f"Failed to read CSV file {filepath}: {e}")

    # Process based on detected format
    if format_type == "time_z":
        # Format: time, z_profile
        if data.shape[1] < 2:
            raise ValueError(
                f"time_z format requires at least 2 columns, got {data.shape[1]}"
            )

        time_orig = data[:, 0]
        z_profile = data[:, 1]

        # Generate 4-wheel profiles from single profile
        time_uniform, wheel_profiles = _expand_single_profile_to_wheels(
            time_orig, z_profile, wheelbase, velocity, correlation, resample_hz
        )

    elif format_type == "time_wheels":
        # Format: time, LF, RF, LR, RR
        if data.shape[1] < 5:
            raise ValueError(
                f"time_wheels format requires 5 columns, got {data.shape[1]}"
            )

        time_orig = data[:, 0]

        # Map columns to wheels (case insensitive)
        header_lower = [h.lower() for h in header]
        wheel_indices = {}

        for wheel in ["lf", "rf", "lr", "rr"]:
            try:
                wheel_indices[wheel.upper()] = header_lower.index(wheel)
            except ValueError:
                raise ValueError(
                    f"Wheel column '{wheel}' not found in header: {header}"
                )

        # Extract wheel profiles
        wheel_data = {
            "LF": data[:, wheel_indices["LF"]],
            "RF": data[:, wheel_indices["RF"]],
            "LR": data[:, wheel_indices["LR"]],
            "RR": data[:, wheel_indices["RR"]],
        }

        # Resample to uniform time grid
        time_uniform, wheel_profiles = _resample_wheel_profiles(
            time_orig, wheel_data, resample_hz
        )

    elif format_type == "wheels_only":
        # Format: LF, RF, LR, RR (no time column, assume uniform spacing)
        if data.shape[1] < 4:
            raise ValueError(
                f"wheels_only format requires 4 columns, got {data.shape[1]}"
            )

        # Assume uniform time spacing
        n_samples = data.shape[0]
        duration = n_samples / resample_hz
        time_uniform = np.linspace(0, duration, n_samples)

        wheel_profiles = {
            "LF": data[:, 0],
            "RF": data[:, 1],
            "LR": data[:, 2],
            "RR": data[:, 3],
        }

    else:
        raise ValueError(f"Unsupported CSV format type: {format_type}")

    # Validate monotonic time
    if not np.all(np.diff(time_uniform) > 0):
        warnings.warn(
            "Time array is not strictly monotonic - interpolation may be unreliable"
        )

    # Check for NaN/inf values
    for wheel, profile in wheel_profiles.items():
        if not np.all(np.isfinite(profile)):
            warnings.warn(f"Non-finite values detected in {wheel} profile")
            # Replace with interpolation
            mask = np.isfinite(profile)
            if np.sum(mask) >= 2:
                interp_func = interp1d(
                    time_uniform[mask],
                    profile[mask],
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )
                wheel_profiles[wheel] = interp_func(time_uniform)

    return time_uniform, wheel_profiles


def _expand_single_profile_to_wheels(
    time_orig: np.ndarray,
    z_profile: np.ndarray,
    wheelbase: float,
    velocity: float,
    correlation: CorrelationSpec,
    resample_hz: float,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Expand single profile to 4 wheels with delays and correlation"""

    # Calculate rear axle delay
    axle_delay = wheelbase / velocity

    # Create uniform time grid
    duration = time_orig[-1] - time_orig[0] + axle_delay  # Add buffer for delays
    time_uniform = np.linspace(
        time_orig[0], time_orig[0] + duration, int(duration * resample_hz)
    )

    # Interpolate original profile to uniform grid
    interp_func = interp1d(
        time_orig, z_profile, kind="linear", bounds_error=False, fill_value=0.0
    )
    z_uniform = interp_func(time_uniform)

    # Generate correlated right track
    if correlation.rho_LR < 1.0:
        # Add uncorrelated noise for right track
        np.random.seed(correlation.seed)
        noise = (
            np.random.randn(len(z_uniform))
            * np.std(z_uniform)
            * np.sqrt(1 - correlation.rho_LR**2)
        )
        z_right = correlation.rho_LR * z_uniform + noise
    else:
        z_right = z_uniform.copy()

    # Apply axle delays
    # Front axle: no delay
    # Rear axle: delayed by wheelbase/velocity

    # Create delayed time arrays
    time_rear = time_uniform - axle_delay

    # Interpolate for rear wheels
    interp_rear_left = interp1d(
        time_uniform, z_uniform, kind="linear", bounds_error=False, fill_value=0.0
    )
    interp_rear_right = interp1d(
        time_uniform, z_right, kind="linear", bounds_error=False, fill_value=0.0
    )

    z_rear_left = interp_rear_left(time_rear)
    z_rear_right = interp_rear_right(time_rear)

    wheel_profiles = {
        "LF": z_uniform,  # Left front
        "RF": z_right,  # Right front
        "LR": z_rear_left,  # Left rear
        "RR": z_rear_right,  # Right rear
    }

    return time_uniform, wheel_profiles


def _resample_wheel_profiles(
    time_orig: np.ndarray, wheel_data: dict[str, np.ndarray], resample_hz: float
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Resample wheel profiles to uniform time grid"""

    duration = time_orig[-1] - time_orig[0]
    time_uniform = np.linspace(time_orig[0], time_orig[-1], int(duration * resample_hz))

    wheel_profiles = {}

    for wheel, profile in wheel_data.items():
        interp_func = interp1d(
            time_orig,
            profile,
            kind="linear",
            bounds_error=False,
            fill_value="extrapolate",
        )
        wheel_profiles[wheel] = interp_func(time_uniform)

    return time_uniform, wheel_profiles


def save_csv_profile(
    filepath: str,
    time: np.ndarray,
    wheel_profiles: dict[str, np.ndarray],
    format_type: str = "time_wheels",
    encoding: str = "utf-8",
) -> None:
    """Save wheel profiles to CSV file

    Args:
        filepath: Output file path
        time: Time array (s)
        wheel_profiles: Dictionary with wheel profiles
        format_type: 'time_wheels' or 'time_z' (uses LF only)
        encoding: File encoding
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        if format_type == "time_wheels":
            # Write header
            writer.writerow(["time", "LF", "RF", "LR", "RR"])

            # Write data
            for i in range(len(time)):
                row = [
                    f"{time[i]:.6f}",
                    f"{wheel_profiles['LF'][i]:.6f}",
                    f"{wheel_profiles['RF'][i]:.6f}",
                    f"{wheel_profiles['LR'][i]:.6f}",
                    f"{wheel_profiles['RR'][i]:.6f}",
                ]
                writer.writerow(row)

        elif format_type == "time_z":
            # Write header
            writer.writerow(["time", "z"])

            # Write data (use LF profile)
            for i in range(len(time)):
                row = [f"{time[i]:.6f}", f"{wheel_profiles['LF'][i]:.6f}"]
                writer.writerow(row)

        else:
            raise ValueError(f"Unsupported save format: {format_type}")


# Export functions
__all__ = ["detect_csv_format", "load_csv_profile", "save_csv_profile"]
