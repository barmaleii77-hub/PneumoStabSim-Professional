#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify initial geometry calculations
"""

import math

print("=" * 70)
print("INITIAL GEOMETRY VERIFICATION")
print("=" * 70)

# Cylinder parameters
D_cylinder = 80.0  # mm
D_rod = 32.0       # mm
L_body = 250.0     # mm
L_piston = 20.0    # mm

print("\nCYLINDER PARAMETERS:")
print(f"  Cylinder diameter: {D_cylinder} mm")
print(f"  Rod diameter:      {D_rod} mm")
print(f"  Body length:       {L_body} mm")
print(f"  Piston thickness:  {L_piston} mm")

# Calculate areas
A_head = math.pi * (D_cylinder / 2.0) ** 2
A_rod_steel = math.pi * (D_rod / 2.0) ** 2
A_rod = A_head - A_rod_steel

print("\nAREAS:")
print(f"  A_head (head chamber):    {A_head:.2f} mm^2")
print(f"  A_rod_steel (rod area):   {A_rod_steel:.2f} mm^2")
print(f"  A_rod (effective):        {A_rod:.2f} mm^2")

# Working length
L_working = L_body - L_piston

print(f"\n  Working length: {L_working} mm")

# Calculate initial piston position (V_head = V_rod)
L_head_0 = (A_rod * L_working) / (A_head + A_rod)
L_rod_0 = L_working - L_head_0

print("\nINITIAL PISTON POSITION (V_head = V_rod):")
print(f"  L_head (head chamber): {L_head_0:.2f} mm")
print(f"  L_rod (rod chamber):   {L_rod_0:.2f} mm")

# Volumes
V_head = A_head * L_head_0
V_rod = A_rod * L_rod_0

print(f"\nVOLUMES:")
print(f"  V_head: {V_head:.2f} mm^3 = {V_head/1000:.2f} cm^3")
print(f"  V_rod:  {V_rod:.2f} mm^3 = {V_rod/1000:.2f} cm^3")
print(f"  Difference: {abs(V_head - V_rod):.2f} mm^3")

ratio = V_head / V_rod if V_rod > 0 else 0
print(f"  Ratio V_head/V_rod: {ratio:.6f}")

if abs(ratio - 1.0) < 0.001:
    print("  OK VOLUMES ARE EQUAL!")
else:
    print(f"  ERROR VOLUMES NOT EQUAL! Error: {abs(ratio - 1.0) * 100:.4f}%")

# Piston position
x_piston_0 = L_head_0
piston_ratio = x_piston_0 / L_body

print(f"\nPISTON POSITION:")
print(f"  x_piston_0: {x_piston_0:.2f} mm from cylinder start")
print(f"  pistonRatio: {piston_ratio:.4f} ({piston_ratio * 100:.2f}% of length)")

# Lever geometry
lever_length = 315.0  # mm

j_arm_left = (-150.0, 60.0, -1000.0)
j_arm_right = (150.0, 60.0, -1000.0)
j_tail_left = (-100.0, 710.0, -1000.0)
j_tail_right = (100.0, 710.0, -1000.0)

print(f"\nLEVER GEOMETRY:")
print(f"  Lever length: {lever_length} mm")
print(f"  j_arm (left):  {j_arm_left}")
print(f"  j_arm (right): {j_arm_right}")

# Initial j_rod positions (lever HORIZONTAL!)
j_rod_left = (j_arm_left[0] - lever_length, j_arm_left[1], j_arm_left[2])
j_rod_right = (j_arm_right[0] + lever_length, j_arm_right[1], j_arm_right[2])

print(f"\nINITIAL j_rod POSITIONS (angle = 0 deg):")
print(f"  Left:  {j_rod_left}")
print(f"  Right: {j_rod_right}")

# Check horizontal
if j_rod_left[1] == j_arm_left[1] and j_rod_right[1] == j_arm_right[1]:
    print("  OK Levers are HORIZONTAL (Y coordinates equal)")
else:
    print("  ERROR Levers are NOT horizontal!")

# Distance from j_tail to j_rod
dx_left = j_rod_left[0] - j_tail_left[0]
dy_left = j_rod_left[1] - j_tail_left[1]
L_total_left = math.sqrt(dx_left**2 + dy_left**2)

print(f"\nTOTAL LENGTH (j_tail -> j_rod, left side):")
print(f"  dx: {dx_left:.2f} mm")
print(f"  dy: {dy_left:.2f} mm")
print(f"  L_total: {L_total_left:.2f} mm")

# Components
L_tail = 100.0  # tail rod (given)
L_cylinder = 250.0  # cylinder body
L_piston_rod = L_total_left - L_tail - L_cylinder

print(f"\nCOMPONENTS:")
print(f"  L_tail (tail rod):     {L_tail:.2f} mm")
print(f"  L_cylinder (body):     {L_cylinder:.2f} mm")
print(f"  L_piston_rod (rod):    {L_piston_rod:.2f} mm")
print(f"  Sum:                   {L_tail + L_cylinder + L_piston_rod:.2f} mm")

if abs(L_tail + L_cylinder + L_piston_rod - L_total_left) < 0.1:
    print("  OK Sum of components matches total length!")
else:
    print(f"  ERROR Difference: {abs(L_tail + L_cylinder + L_piston_rod - L_total_left):.2f} mm")

print("\n" + "=" * 70)
print("QML VALUES:")
print("=" * 70)
print(f"""
property real pistonPositionMm: {x_piston_0:.2f}  // mm from cylinder start
property real pistonRatio: {piston_ratio:.4f}  // Normalized (0..1)
property real pistonRodLength: {L_piston_rod:.2f}  // mm (piston rod length)

// INITIAL POSITIONS (lever HORIZONTAL at angle=0):
// Left side:
property vector3d fl_j_rod_0: Qt.vector3d({j_rod_left[0]:.1f}, {j_rod_left[1]:.1f}, {j_rod_left[2]:.1f})
property vector3d rl_j_rod_0: Qt.vector3d({j_rod_left[0]:.1f}, {j_rod_left[1]:.1f}, 1000.0)

// Right side:
property vector3d fr_j_rod_0: Qt.vector3d({j_rod_right[0]:.1f}, {j_rod_right[1]:.1f}, {j_rod_right[2]:.1f})
property vector3d rr_j_rod_0: Qt.vector3d({j_rod_right[0]:.1f}, {j_rod_right[1]:.1f}, 1000.0)
""")

print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
