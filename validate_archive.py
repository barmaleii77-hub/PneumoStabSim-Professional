#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Archive Validation - Verify all research is saved
"""
from pathlib import Path

def validate_archive():
    """Validate that all research files are saved"""
    
    print("="*80)
    print("VALIDATING QT QUICK 3D RESEARCH ARCHIVE")
    print("="*80)
    
    # Key categories to check
    categories = {
        "Working Solutions": [
            "assets/qml/main.qml",
            "assets/qml/main_working_builtin.qml", 
            "test_builtin_primitives.py",
            "app.py"
        ],
        "Custom Geometry Research": [
            "src/ui/custom_geometry.py",
            "src/ui/example_geometry.py",
            "src/ui/triangle_geometry.py",
            "src/ui/stable_geometry.py",
            "src/ui/direct_geometry.py"
        ],
        "API Documentation": [
            "study_qquick3d_api.py",
            "study_attribute_details.py"
        ],
        "Diagnostic Tests": [
            "check_environment_comprehensive.py",
            "debug_custom_geometry.py",
            "test_minimal_qt3d.py"
        ],
        "Final Reports": [
            "FINAL_QT_QUICK_3D_SUCCESS_REPORT.md",
            "QT_QUICK_3D_INVESTIGATION_ARCHIVE.md",
            "ANIMATED_PNEUMATIC_SCHEME_PLAN.md"
        ]
    }
    
    total_files = 0
    found_files = 0
    
    for category, files in categories.items():
        print(f"\n{category}:")
        print("-" * 40)
        
        for file_path in files:
            total_files += 1
            path = Path(file_path)
            
            if path.exists():
                size = path.stat().st_size
                print(f"  ? {file_path} ({size} bytes)")
                found_files += 1
            else:
                print(f"  ? {file_path} - NOT FOUND")
    
    print(f"\n{'='*80}")
    print(f"ARCHIVE VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Files found: {found_files}/{total_files}")
    print(f"Coverage: {found_files/total_files*100:.1f}%")
    
    if found_files == total_files:
        print("? ALL RESEARCH FILES SAVED SUCCESSFULLY!")
    else:
        print(f"?? {total_files - found_files} files missing")
    
    print(f"\n?? READY FOR ANIMATED PNEUMATIC SCHEME DEVELOPMENT")
    return found_files == total_files

if __name__ == "__main__":
    validate_archive()