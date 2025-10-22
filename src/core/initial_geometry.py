"""
Initial geometry calculation for suspension system
Ensures V_head = V_rod at neutral position
"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CylinderParams:
    """Cylinder physical parameters"""

    D_cylinder: float = 0.080  # 80mm cylinder bore (m)
    D_rod: float = 0.032  # 32mm rod diameter (m)
    L_body: float = 0.250  # 250mm cylinder body (m)
    L_piston: float = 0.020  # 20mm piston thickness (m)


@dataclass
class InitialGeometry:
    """Initial suspension geometry at neutral position"""

    # Piston position (from start of cylinder body)
    x_piston_0: float

    # Chamber lengths at neutral
    L_head_0: float
    L_rod_0: float

    # Volumes at neutral (should be equal!)
    V_head_0: float
    V_rod_0: float

    # Tail rod length (calculated from geometry)
    L_tail: float

    # Rod positions (horizontal lever)
    j_rod_left: Tuple[float, float, float]  # Left side
    j_rod_right: Tuple[float, float, float]  # Right side


def calculate_initial_piston_position(params: CylinderParams) -> float:
    """
    Calculate initial piston position where V_head = V_rod

    Args:
        params: Cylinder physical parameters

    Returns:
        x_piston_0: Piston position from cylinder start (m)
    """
    # Calculate chamber areas
    A_head = math.pi * (params.D_cylinder / 2.0) ** 2
    A_rod_area = math.pi * (params.D_rod / 2.0) ** 2
    A_rod = A_head - A_rod_area  # Effective area (head - rod)

    # Working length (total body - piston thickness)
    L_working = params.L_body - params.L_piston

    # From condition V_head = V_rod:
    # A_head * L_head = A_rod * L_rod
    # A_head * L_head = A_rod * (L_working - L_head)
    # A_head * L_head = A_rod * L_working - A_rod * L_head
    # L_head * (A_head + A_rod) = A_rod * L_working
    # L_head = (A_rod * L_working) / (A_head + A_rod)

    L_head_0 = (A_rod * L_working) / (A_head + A_rod)

    # Piston position is head chamber length
    x_piston_0 = L_head_0

    return x_piston_0


def calculate_initial_geometry(
    params: CylinderParams,
    lever_length: float = 0.315,  # 315mm
    j_arm_left: Tuple[float, float, float] = (-0.150, 0.060, -1.000),
    j_arm_right: Tuple[float, float, float] = (0.150, 0.060, -1.000),
    j_tail_left: Tuple[float, float, float] = (-0.100, 0.710, -1.000),
    j_tail_right: Tuple[float, float, float] = (0.100, 0.710, -1.000),
) -> InitialGeometry:
    """
    Calculate complete initial geometry at neutral position

    Args:
        params: Cylinder parameters
        lever_length: Lever length from pivot to rod joint (m)
        j_arm_left/right: Lever pivot positions
        j_tail_left/right: Cylinder tail positions

    Returns:
        InitialGeometry with all calculated values
    """
    # 1. Calculate piston position for equal volumes
    x_piston_0 = calculate_initial_piston_position(params)

    # 2. Calculate chamber lengths
    L_working = params.L_body - params.L_piston
    L_head_0 = x_piston_0
    L_rod_0 = L_working - L_head_0

    # 3. Calculate areas
    A_head = math.pi * (params.D_cylinder / 2.0) ** 2
    A_rod_area = math.pi * (params.D_rod / 2.0) ** 2
    A_rod = A_head - A_rod_area

    # 4. Calculate volumes (should be equal!)
    V_head_0 = A_head * L_head_0
    V_rod_0 = A_rod * L_rod_0

    # 5. Calculate rod positions (lever HORIZONTAL at neutral)
    # Left side: lever points LEFT (180 degrees)
    j_rod_left = (
        j_arm_left[0] - lever_length,  # x: pivot - lever_length
        j_arm_left[1],  # y: same as pivot
        j_arm_left[2],  # z: same as pivot
    )

    # Right side: lever points RIGHT (0 degrees)
    j_rod_right = (
        j_arm_right[0] + lever_length,  # x: pivot + lever_length
        j_arm_right[1],  # y: same as pivot
        j_arm_right[2],  # z: same as pivot
    )

    # 6. Calculate tail rod length from geometry
    # Distance from j_tail to start of cylinder body
    # At neutral: cylinder axis is from j_tail toward j_rod

    # For left side:
    dx = j_rod_left[0] - j_tail_left[0]
    dy = j_rod_left[1] - j_tail_left[1]
    total_length = math.sqrt(dx * dx + dy * dy)

    # Tail rod length = total_length - cylinder_body - piston_rod
    # For now, use default 100mm (will be refined)
    L_tail = 0.100  # 100mm default

    return InitialGeometry(
        x_piston_0=x_piston_0,
        L_head_0=L_head_0,
        L_rod_0=L_rod_0,
        V_head_0=V_head_0,
        V_rod_0=V_rod_0,
        L_tail=L_tail,
        j_rod_left=j_rod_left,
        j_rod_right=j_rod_right,
    )


def print_initial_geometry_report(geom: InitialGeometry, params: CylinderParams):
    """Print detailed report of initial geometry"""
    print("=" * 70)
    print("INITIAL GEOMETRY CALCULATION REPORT")
    print("=" * 70)

    print("\n?? CYLINDER PARAMETERS:")
    print(f"  Cylinder bore:    {params.D_cylinder * 1000:.1f} mm")
    print(f"  Rod diameter:     {params.D_rod * 1000:.1f} mm")
    print(f"  Body length:      {params.L_body * 1000:.1f} mm")
    print(f"  Piston thickness: {params.L_piston * 1000:.1f} mm")

    print("\n??  PISTON POSITION (EQUAL VOLUMES):")
    print(f"  Piston position:  {geom.x_piston_0 * 1000:.2f} mm from cylinder start")
    print(f"  Head chamber:     {geom.L_head_0 * 1000:.2f} mm")
    print(f"  Rod chamber:      {geom.L_rod_0 * 1000:.2f} mm")

    print("\n?? VOLUMES AT NEUTRAL:")
    print(f"  V_head:           {geom.V_head_0 * 1e6:.2f} cm?")
    print(f"  V_rod:            {geom.V_rod_0 * 1e6:.2f} cm?")
    print(f"  Difference:       {abs(geom.V_head_0 - geom.V_rod_0) * 1e6:.6f} cm?")

    volume_ratio = geom.V_head_0 / geom.V_rod_0 if geom.V_rod_0 > 0 else 0
    print(f"  Ratio V_head/V_rod: {volume_ratio:.6f}")

    if abs(volume_ratio - 1.0) < 0.001:
        print("  ? VOLUMES ARE EQUAL!")
    else:
        print("  ? VOLUMES NOT EQUAL!")

    print("\n?? GEOMETRY POSITIONS:")
    print(f"  Tail rod length:  {geom.L_tail * 1000:.1f} mm")
    print(
        f"  Left j_rod:       ({geom.j_rod_left[0]:.3f}, {geom.j_rod_left[1]:.3f}, {geom.j_rod_left[2]:.3f}) m"
    )
    print(
        f"  Right j_rod:      ({geom.j_rod_right[0]:.3f}, {geom.j_rod_right[1]:.3f}, {geom.j_rod_right[2]:.3f}) m"
    )

    print("\n" + "=" * 70)


# Example usage
if __name__ == "__main__":
    # Create default cylinder parameters
    params = CylinderParams()

    # Calculate initial geometry
    geom = calculate_initial_geometry(params)

    # Print report
    print_initial_geometry_report(geom, params)

    # Export values for QML
    print("\n?? QML PROPERTY VALUES:")
    print(
        f"property real pistonPositionMm: {geom.x_piston_0 * 1000:.2f}  // mm from cylinder start"
    )
    print(
        f"property real pistonRatio: {geom.x_piston_0 / params.L_body:.3f}  // Normalized (0..1)"
    )
    print("\n// Left side (FL, RL):")
    print(
        f"property vector3d fl_j_rod: Qt.vector3d({geom.j_rod_left[0]:.3f}, {geom.j_rod_left[1]:.3f}, {geom.j_rod_left[2]:.3f})"
    )
    print("\n// Right side (FR, RR):")
    print(
        f"property vector3d fr_j_rod: Qt.vector3d({geom.j_rod_right[0]:.3f}, {geom.j_rod_right[1]:.3f}, {geom.j_rod_right[2]:.3f})"
    )
