#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for initial geometry calculation
"""

import sys
import math

# Cylinder parameters
D_cylinder = 0.080  # 80mm
D_rod = 0.032       # 32mm
L_body = 0.250      # 250mm
L_piston = 0.020    # 20mm

# Calculate areas
A_head = math.pi * (D_cylinder / 2.0) ** 2
A_rod_steel = math.pi * (D_rod / 2.0) ** 2
A_rod = A_head - A_rod_steel

# Working length
L_working = L_body - L_piston

# Calculate initial piston position (V_head = V_rod)
L_head_0 = (A_rod * L_working) / (A_head + A_rod)
x_piston_0 = L_head_0
L_rod_0 = L_working - L_head_0

# Calculate volumes
V_head_0 = A_head * L_head_0
V_rod_0 = A_rod * L_rod_0

# Lever geometry
lever_length = 0.315  # 315mm

# Pivot positions
j_arm_left = (-0.150, 0.060, -1.000)
j_arm_right = (0.150, 0.060, -1.000)

# Rod positions (HORIZONTAL lever at neutral)
j_rod_left = (j_arm_left[0] - lever_length, j_arm_left[1], j_arm_left[2])
j_rod_right = (j_arm_right[0] + lever_length, j_arm_right[1], j_arm_right[2])

# Print report
print("=" * 70)
print("INITIAL GEOMETRY CALCULATION REPORT")
print("=" * 70)

print("\n?? CYLINDER PARAMETERS:")
print(f"  Cylinder bore:    {D_cylinder * 1000:.1f} mm")
print(f"  Rod diameter:     {D_rod * 1000:.1f} mm")
print(f"  Body length:      {L_body * 1000:.1f} mm")
print(f"  Piston thickness: {L_piston * 1000:.1f} mm")

print("\n??  PISTON POSITION (EQUAL VOLUMES):")
print(f"  Piston position:  {x_piston_0 * 1000:.2f} mm from cylinder start")
print(f"  Head chamber:     {L_head_0 * 1000:.2f} mm")
print(f"  Rod chamber:      {L_rod_0 * 1000:.2f} mm")

print("\n?? VOLUMES AT NEUTRAL:")
print(f"  V_head:           {V_head_0 * 1e6:.4f} cm?")
print(f"  V_rod:            {V_rod_0 * 1e6:.4f} cm?")
print(f"  Difference:       {abs(V_head_0 - V_rod_0) * 1e6:.6f} cm?")

volume_ratio = V_head_0 / V_rod_0 if V_rod_0 > 0 else 0
print(f"  Ratio V_head/V_rod: {volume_ratio:.6f}")

if abs(volume_ratio - 1.0) < 0.001:
    print("  ? VOLUMES ARE EQUAL!")
else:
    print("  ? VOLUMES NOT EQUAL!")

print("\n?? INITIAL LEVER POSITIONS (HORIZONTAL):")
print(f"  Lever length:     {lever_length * 1000:.1f} mm")
print(f"  Left j_rod:       ({j_rod_left[0]:.3f}, {j_rod_left[1]:.3f}, {j_rod_left[2]:.3f}) m")
print(f"  Right j_rod:      ({j_rod_right[0]:.3f}, {j_rod_right[1]:.3f}, {j_rod_right[2]:.3f}) m")

print("\n?? QML PROPERTY VALUES (COPY TO CODE):")
print("=" * 70)
print(f"property real pistonPositionMm: {x_piston_0 * 1000:.2f}  // mm from cylinder start")
print(f"property real pistonRatio: {x_piston_0 / L_body:.4f}  // Normalized (0..1)")
print()
print("// INITIAL POSITIONS (lever HORIZONTAL at neutral):")
print("// Left side (FL, RL):")
print(f"property vector3d fl_j_rod: Qt.vector3d({j_rod_left[0]:.3f}, {j_rod_left[1]:.3f}, {j_rod_left[2]:.3f})")
print(f"property vector3d rl_j_rod: Qt.vector3d({j_rod_left[0]:.3f}, {j_rod_left[1]:.3f}, 1.000)")
print()
print("// Right side (FR, RR):")
print(f"property vector3d fr_j_rod: Qt.vector3d({j_rod_right[0]:.3f}, {j_rod_right[1]:.3f}, {j_rod_right[2]:.3f})")
print(f"property vector3d rr_j_rod: Qt.vector3d({j_rod_right[0]:.3f}, {j_rod_right[1]:.3f}, 1.000)")

print("\n" + "=" * 70)
