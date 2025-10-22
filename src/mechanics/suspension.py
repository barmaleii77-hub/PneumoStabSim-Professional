"""
Mechanics module stub for P12 tests
"""

from src.core.geometry import GeometryParams


def calculate_stroke_from_angle(angle: float, params: GeometryParams) -> float:
    """Calculate piston stroke from lever angle

    Args:
        angle: Lever angle (radians)
        params: Geometry parameters

    Returns:
        Piston stroke (m)
    """
    # Simple linear approximation
    return params.lever_length * angle
