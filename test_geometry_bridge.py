#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test geometry bridge module
"""
import sys
from pathlib import Path

def test_geometry_bridge():
    """Test geometry bridge functionality"""
    print("="*60)
    print("GEOMETRY BRIDGE TEST")
    print("="*60)
    
    try:
        from src.ui.geometry_bridge import create_geometry_converter
        print("? geometry_bridge imported successfully")
    except Exception as e:
        print(f"? Failed to import geometry_bridge: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        # Create converter with test parameters
        converter = create_geometry_converter(
            wheelbase=2.6,          # m
            lever_length=0.45,     # m  
            cylinder_diameter=0.085 # m
        )
        print("? Geometry converter created")
        
        # Test frame parameters
        frame_params = converter.get_frame_params()
        print(f"? Frame params: {frame_params}")
        
        # Test corner coordinates
        print("\n?? Testing corner coordinates:")
        for corner in ['fl', 'fr', 'rl', 'rr']:
            coords = converter.get_corner_3d_coords(corner, lever_angle_deg=0.0)
            j_arm = coords['j_arm']
            print(f"  {corner.upper()}: j_arm=({j_arm.x():.0f}, {j_arm.y():.0f}, {j_arm.z():.0f})")
        
        print("? All geometry calculations successful")
        return True
        
    except Exception as e:
        print(f"? Geometry bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_geometry_bridge()
    sys.exit(0 if success else 1)