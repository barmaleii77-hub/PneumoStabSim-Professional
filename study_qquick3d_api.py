#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE QQuick3DGeometry API STUDY
Complete API exploration
"""
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtWidgets import QApplication
import sys

def study_qquick3d_geometry_api():
    """Full QQuick3DGeometry API study"""
    print("="*80)
    print("COMPREHENSIVE QQuick3DGeometry API STUDY")
    print("="*80)
    
    # Create QApplication for Qt initialization
    app = QApplication([])
    
    # Create geometry for study
    geometry = QQuick3DGeometry()
    
    print("\n1. ALL METHODS:")
    print("-" * 40)
    
    all_methods = [method for method in dir(geometry) if not method.startswith('_')]
    
    # Group methods by purpose
    data_methods = []
    attribute_methods = []
    primitive_methods = []
    bounds_methods = []
    other_methods = []
    
    for method in all_methods:
        if any(keyword in method.lower() for keyword in ['data', 'vertex', 'index']):
            data_methods.append(method)
        elif any(keyword in method.lower() for keyword in ['attribute', 'semantic']):
            attribute_methods.append(method)
        elif any(keyword in method.lower() for keyword in ['primitive', 'type']):
            primitive_methods.append(method)
        elif any(keyword in method.lower() for keyword in ['bound', 'min', 'max']):
            bounds_methods.append(method)
        else:
            other_methods.append(method)
    
    print("DATA METHODS:")
    for method in sorted(data_methods):
        print(f"  {method}")
    
    print("\nATTRIBUTE METHODS:")
    for method in sorted(attribute_methods):
        print(f"  {method}")
    
    print("\nPRIMITIVE METHODS:")
    for method in sorted(primitive_methods):
        print(f"  {method}")
    
    print("\nBOUNDS METHODS:")
    for method in sorted(bounds_methods):
        print(f"  {method}")
    
    print("\nOTHER METHODS:")
    for method in sorted(other_methods)[:20]:  # First 20 only
        print(f"  {method}")
    
    print(f"\n2. ENUMS AND CONSTANTS:")
    print("-" * 40)
    
    # Study Attribute enum
    try:
        attr_class = QQuick3DGeometry.Attribute
        semantics = [name for name in dir(attr_class) if 'Semantic' in name]
        print(f"Semantics: {semantics}")
        
        types = [name for name in dir(attr_class) if 'Type' in name]
        print(f"Types: {types}")
    except Exception as e:
        print(f"Attribute enum ERROR: {e}")
    
    # Study PrimitiveType
    try:
        prim_class = QQuick3DGeometry.PrimitiveType
        primitives = [name for name in dir(prim_class) if not name.startswith('_')]
        print(f"PrimitiveTypes: {primitives}")
    except Exception as e:
        print(f"PrimitiveType enum ERROR: {e}")
    
    print(f"\n3. CURRENT STATE:")
    print("-" * 40)
    
    try:
        print(f"attributeCount(): {geometry.attributeCount()}")
        print(f"stride(): {geometry.stride()}")
        print(f"primitiveType(): {geometry.primitiveType()}")
        print(f"vertexData(): {len(geometry.vertexData())} bytes")
        print(f"indexData(): {len(geometry.indexData())} bytes")
        
    except Exception as e:
        print(f"Method testing ERROR: {e}")
    
    print(f"\n{'='*80}")
    print("API STUDY COMPLETE")
    print("="*80)

if __name__ == "__main__":
    study_qquick3d_geometry_api()