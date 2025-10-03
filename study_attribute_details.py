#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Study QQuick3DGeometry.Attribute semantics and types in detail
"""
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtWidgets import QApplication

def study_attribute_details():
    print("="*80)
    print("DETAILED QQuick3DGeometry.Attribute STUDY")
    print("="*80)
    
    app = QApplication([])
    
    # Study Attribute class
    Attr = QQuick3DGeometry.Attribute
    
    print("1. ALL ATTRIBUTE MEMBERS:")
    print("-" * 40)
    
    all_attrs = [name for name in dir(Attr) if not name.startswith('_')]
    for attr_name in sorted(all_attrs):
        try:
            value = getattr(Attr, attr_name)
            print(f"  {attr_name}: {value} ({type(value)})")
        except Exception as e:
            print(f"  {attr_name}: ERROR - {e}")
    
    print("\n2. TESTING SEMANTICS:")
    print("-" * 40)
    
    # Try to find all semantic constants
    semantic_names = [
        'PositionSemantic', 'NormalSemantic', 'TexCoord0Semantic', 
        'TexCoord1Semantic', 'TangentSemantic', 'BinormalSemantic',
        'ColorSemantic', 'JointSemantic', 'WeightSemantic', 'IndexSemantic'
    ]
    
    for semantic in semantic_names:
        try:
            value = getattr(Attr, semantic)
            print(f"  {semantic}: {value}")
        except AttributeError:
            print(f"  {semantic}: NOT FOUND")
        except Exception as e:
            print(f"  {semantic}: ERROR - {e}")
    
    print("\n3. TESTING COMPONENT TYPES:")
    print("-" * 40)
    
    type_names = [
        'U16Type', 'U32Type', 'I8Type', 'I16Type', 'I32Type', 
        'U8Type', 'F16Type', 'F32Type', 'F64Type'
    ]
    
    for type_name in type_names:
        try:
            value = getattr(Attr, type_name)
            print(f"  {type_name}: {value}")
        except AttributeError:
            print(f"  {type_name}: NOT FOUND")
        except Exception as e:
            print(f"  {type_name}: ERROR - {e}")
    
    print("\n4. TESTING addAttribute() CALL:")
    print("-" * 40)
    
    geometry = QQuick3DGeometry()
    
    try:
        # Try to add position attribute
        position_semantic = getattr(Attr, 'PositionSemantic', None)
        f32_type = getattr(Attr, 'F32Type', None)
        
        if position_semantic is not None and f32_type is not None:
            print(f"  Adding Position attribute: semantic={position_semantic}, type={f32_type}")
            geometry.addAttribute(position_semantic, 0, f32_type)
            print(f"  Success! AttributeCount: {geometry.attributeCount()}")
        else:
            print(f"  Cannot add attribute: PositionSemantic={position_semantic}, F32Type={f32_type}")
            
    except Exception as e:
        print(f"  addAttribute() ERROR: {e}")
    
    print(f"\n{'='*80}")
    print("ATTRIBUTE STUDY COMPLETE")
    print("="*80)

if __name__ == "__main__":
    study_attribute_details()