"""
CSV export utilities for simulation data
Supports timeseries and snapshot export with optional gzip compression
"""

import csv
import gzip
from importlib import util
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from collections.abc import Iterable, Mapping, Sequence

_NUMPY_AVAILABLE = util.find_spec("numpy") is not None

if TYPE_CHECKING:
    import numpy as np

if _NUMPY_AVAILABLE:  # pragma: no branch - executed only when numpy is installed
    import numpy as np
else:  # pragma: no cover - behaviour depends on optional dependency
    np = cast(Any, None)


def export_timeseries_csv(
    time: Sequence[float],
    series: Mapping[str, Sequence[float]],
    path: Path,
    header: Sequence[str],
) -> None:
    """Export timeseries data to CSV

    Exports time-indexed series data to CSV file. Supports automatic
    gzip compression if path ends with .gz

    Args:
        time: Time array (1D)
        series: Dictionary of series name -> data array
        path: Output file path (.csv or .csv.gz)
        header: List of column names (including 'time' as first)

    Raises:
        ValueError: If arrays have different lengths

    Example:
        >>> time = np.linspace(0, 10, 100)
        >>> data = {'pressure': np.sin(time), 'flow': np.cos(time)}
        >>> export_timeseries_csv(time, data, Path('data.csv'), ['time', 'pressure', 'flow'])

    References:
        https://docs.python.org/3/library/csv.html
        https://numpy.org/doc/stable/reference/generated/numpy.savetxt.html
    """
    # Validate lengths
    n_points = len(time)
    for name, data in series.items():
        if len(data) != n_points:
            raise ValueError(
                f"Series '{name}' length {len(data)} != time length {n_points}"
            )

    # Determine if gzip compression needed
    use_gzip = path.suffix == ".gz" or str(path).endswith(".csv.gz")

    # Method 1: Using numpy.savetxt (preferred for numeric data)
    if _can_use_numpy_savetxt(series):
        _export_with_numpy(time, series, path, header, use_gzip)
    else:
        # Method 2: Using csv.writer (fallback)
        _export_with_csv_writer(time, series, path, header, use_gzip)


def _can_use_numpy_savetxt(series: Mapping[str, Sequence[float]]) -> bool:
    """Check if all series are numeric (suitable for numpy.savetxt)."""

    if not _NUMPY_AVAILABLE:
        return False

    for data in series.values():
        if not hasattr(data, "dtype"):
            return False
        if not np.issubdtype(data.dtype, np.number):
            return False
    return True


def _export_with_numpy(
    time: Sequence[float],
    series: Mapping[str, Sequence[float]],
    path: Path,
    header: Sequence[str],
    use_gzip: bool,
) -> None:
    """Export using numpy.savetxt (efficient for numeric data)"""
    if not _NUMPY_AVAILABLE:
        raise RuntimeError("NumPy is required for numpy-based CSV export")

    # Stack columns
    columns = [time] + [series[name] for name in header[1:]]
    data = np.column_stack(columns)

    # Prepare header
    header_str = ",".join(header)

    # Save (numpy automatically handles .gz)
    np.savetxt(
        path,
        data,
        fmt="%.6g",
        delimiter=",",
        header=header_str,
        comments="",  # No comment prefix
        encoding="utf-8",
    )


def _export_with_csv_writer(
    time: Sequence[float],
    series: Mapping[str, Sequence[float]],
    path: Path,
    header: Sequence[str],
    use_gzip: bool,
) -> None:
    """Export using csv.writer (fallback for mixed types)"""
    open_func = gzip.open if use_gzip else open

    with open_func(path, "wt", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(header)

        # Write data rows
        n_points = len(time)
        for i in range(n_points):
            row = [time[i]] + [series[name][i] for name in header[1:]]
            writer.writerow(row)


def export_snapshot_csv(snapshot_rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    """Export snapshot data to CSV

    Exports list of snapshot dictionaries to CSV. Fields are sorted
    alphabetically for consistency.

    Args:
        snapshot_rows: List of dictionaries with snapshot data
        path: Output file path (.csv or .csv.gz)

    Example:
        >>> snapshots = [
        ...     {'time': 0.0, 'heave': 0.0, 'roll': 0.0},
        ...     {'time': 0.1, 'heave': 0.01, 'roll': 0.001}
        ... ]
        >>> export_snapshot_csv(snapshots, Path('snapshots.csv'))

    References:
        https://docs.python.org/3/library/csv.html#csv.DictWriter
    """
    if not snapshot_rows:
        raise ValueError("No snapshot data to export")

    # Determine if gzip compression needed
    use_gzip = path.suffix == ".gz" or str(path).endswith(".csv.gz")

    # Get sorted field names from first row
    fieldnames = sorted(snapshot_rows[0].keys())

    # Open file (with optional gzip)
    open_func = gzip.open if use_gzip else open

    with open_func(path, "wt", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write rows
        writer.writerows(snapshot_rows)


def export_state_snapshot_csv(
    snapshots: Iterable[Any],
    path: Path,
) -> None:
    """Export StateSnapshot objects to CSV

    Converts StateSnapshot objects to flat dictionaries and exports.

    Args:
        snapshots: List of StateSnapshot-like objects
        path: Output file path
    """
    if not snapshots:
        raise ValueError("No snapshots to export")

    # Convert snapshots to dictionaries
    rows: list[dict[str, Any]] = []
    for snap in snapshots:
        row = {
            "time": snap.simulation_time,
            "step": snap.step_number,
            "dt": snap.dt_physics,
            # Frame state
            "heave": snap.frame.heave,
            "roll": snap.frame.roll,
            "pitch": snap.frame.pitch,
            "heave_rate": snap.frame.heave_rate,
            "roll_rate": snap.frame.roll_rate,
            "pitch_rate": snap.frame.pitch_rate,
            # Tank
            "tank_pressure": snap.tank.pressure,
            "tank_temp": snap.tank.temperature,
            "tank_mass": snap.tank.mass,
        }

        # Add line pressures
        for line_enum, line_state in snap.lines.items():
            prefix = f"line_{line_enum.value}"
            row[f"{prefix}_pressure"] = line_state.pressure
            row[f"{prefix}_temp"] = line_state.temperature
            row[f"{prefix}_mass"] = line_state.mass

        rows.append(row)

    export_snapshot_csv(rows, path)


def get_default_export_dir() -> Path:
    """Get default directory for exports

    Uses QStandardPaths.DocumentsLocation or falls back to user home

    Returns:
        Default export directory path
    """
    try:
        from PySide6.QtCore import QStandardPaths

        # Try Documents location
        docs = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        if docs:
            return Path(docs) / "PneumoStabSim"
    except ImportError:
        pass

    # Fallback to home directory
    return Path.home() / "PneumoStabSim"


def ensure_csv_extension(path: Path, allow_gz: bool = True) -> Path:
    """Ensure path has proper CSV extension

    Args:
        path: Input path
        allow_gz: Allow .csv.gz extension

    Returns:
        Path with proper extension
    """
    path_str = str(path)

    if allow_gz and path_str.endswith(".csv.gz"):
        return path
    elif path_str.endswith(".csv"):
        return path
    elif allow_gz and path_str.endswith(".gz"):
        # Add .csv before .gz
        return Path(path_str[:-3] + ".csv.gz")
    else:
        # Add .csv
        return Path(path_str + ".csv")
