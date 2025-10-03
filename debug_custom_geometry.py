#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug custom geometry step by step
"""
import numpy as np
from src.ui.custom_geometry import SphereGeometry

print("="*80)
print("STEP-BY-STEP CUSTOM GEOMETRY DEBUG")
print("="*80)
print()

# Step 1: Create geometry
print("Step 1: Creating SphereGeometry...")
sphere = SphereGeometry()
print(f"   ? Created: {sphere}")
print(f"   Type: {type(sphere)}")

# Step 2: Check parameters
print()
print("Step 2: Parameters...")
print(f"   Radius: {sphere._radius}")
print(f"   Segments: {sphere._segments}")
print(f"   Rings: {sphere._rings}")

# Step 3: Check data sizes
print()
print("Step 3: Data sizes...")
vertex_data = sphere.vertexData()
index_data = sphere.indexData()
print(f"   Vertex data: {len(vertex_data)} bytes")
print(f"   Index data: {len(index_data)} bytes")

if len(vertex_data) == 0:
    print("   ? CRITICAL: No vertex data!")
    import sys
    sys.exit(1)
else:
    print("   ? Vertex data present")

# Step 4: Check stride and attributes
print()
print("Step 4: Attributes...")
stride = sphere.stride()
attr_count = sphere.attributeCount()
print(f"   Stride: {stride} bytes")
print(f"   Attribute count: {attr_count}")

expected_vertices = (16 + 1) * (32 + 1) * 8 * 4  # rings+1 * segments+1 * 8_floats * 4_bytes
print(f"   Expected vertex data size: {expected_vertices} bytes")
print(f"   Actual vertex data size: {len(vertex_data)} bytes")

if len(vertex_data) != expected_vertices:
    print(f"   ?? Size mismatch! Expected {expected_vertices}, got {len(vertex_data)}")
else:
    print("   ? Size matches")

# Step 5: Check individual vertices (first few)
print()
print("Step 5: Sample vertices...")
if len(vertex_data) >= 32:  # At least 8 floats
    # Convert bytes back to floats
    import struct
    floats = struct.unpack('f' * (len(vertex_data) // 4), vertex_data)
    
    print(f"   Total floats: {len(floats)}")
    print(f"   First vertex (8 floats):")
    if len(floats) >= 8:
        print(f"     Position: {floats[0]:.3f}, {floats[1]:.3f}, {floats[2]:.3f}")
        print(f"     Normal:   {floats[3]:.3f}, {floats[4]:.3f}, {floats[5]:.3f}")
        print(f"     UV:       {floats[6]:.3f}, {floats[7]:.3f}")
        
        # Check if values are reasonable
        pos_mag = (floats[0]**2 + floats[1]**2 + floats[2]**2)**0.5
        norm_mag = (floats[3]**2 + floats[4]**2 + floats[5]**2)**0.5
        
        print(f"     Position magnitude: {pos_mag:.3f} (should be ~1.0)")
        print(f"     Normal magnitude: {norm_mag:.3f} (should be ~1.0)")
        
        if abs(pos_mag - 1.0) < 0.1 and abs(norm_mag - 1.0) < 0.1:
            print("     ? Values look reasonable")
        else:
            print("     ? Values look wrong!")

# Step 6: Bounds check
print()
print("Step 6: Bounds...")
bounds_min = sphere.boundsMin()
bounds_max = sphere.boundsMax()
print(f"   Min bounds: {bounds_min}")
print(f"   Max bounds: {bounds_max}")

print()
print("="*80)
print("GEOMETRY DEBUG COMPLETE")
print("="*80)