#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Project Test Suite
Full complex test for PneumoStabSim project
"""
import sys
import os
from pathlib import Path
import importlib
import traceback
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Results storage
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'total': 0
}

def log_test(category: str, name: str, status: str, details: str = ""):
    """Log test result"""
    test_results['total'] += 1
    
    icon = "?" if status == "PASS" else "?" if status == "FAIL" else "??"
    print(f"{icon} [{category}] {name}: {status}")
    
    if details:
        print(f"   Details: {details}")
    
    if status == "PASS":
        test_results['passed'].append((category, name))
    elif status == "FAIL":
        test_results['failed'].append((category, name, details))
    else:
        test_results['warnings'].append((category, name, details))


def test_python_version():
    """Test 1: Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        log_test("Environment", "Python Version", "PASS", 
                f"Python {version.major}.{version.minor}.{version.micro}")
    else:
        log_test("Environment", "Python Version", "FAIL",
                f"Python {version.major}.{version.minor} < 3.11")


def test_dependencies():
    """Test 2: Required dependencies"""
    required = [
        'PySide6',
        'numpy',
        'scipy',
    ]
    
    for module_name in required:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown')
            log_test("Dependencies", module_name, "PASS", f"v{version}")
        except ImportError as e:
            log_test("Dependencies", module_name, "FAIL", str(e))


def test_project_structure():
    """Test 3: Project structure"""
    critical_paths = [
        'src',
        'src/ui',
        'src/core',
        'src/mechanics',
        'src/physics',
        'src/pneumo',
        'src/road',
        'src/runtime',
        'src/common',
        'assets',
        'assets/qml',
        'docs',
        'tests',
    ]
    
    for path in critical_paths:
        full_path = project_root / path
        if full_path.exists():
            log_test("Structure", path, "PASS")
        else:
            log_test("Structure", path, "FAIL", "Directory not found")


def test_module_imports():
    """Test 4: Core module imports"""
    modules = [
        'src.common.logging',
        'src.core.geometry',
        'src.mechanics.kinematics',
        'src.ui.geometry_bridge',
        'src.ui.main_window',
    ]
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
            log_test("Module Import", module_name, "PASS")
        except Exception as e:
            log_test("Module Import", module_name, "FAIL", str(e))


def test_qml_files():
    """Test 5: QML files exist"""
    qml_files = [
        'assets/qml/main.qml',
        'assets/qml/UFrameScene.qml',
        'assets/qml/components/Materials.qml',
    ]
    
    for qml_path in qml_files:
        full_path = project_root / qml_path
        if full_path.exists():
            log_test("QML Files", qml_path, "PASS")
        else:
            log_test("QML Files", qml_path, "FAIL", "File not found")


def test_documentation():
    """Test 6: Documentation files"""
    doc_files = [
        'docs/README.md',
        'docs/INDEX.md',
        'docs/ARCHITECTURE.md',
        'docs/DEVELOPMENT_GUIDE.md',
        'docs/TROUBLESHOOTING.md',
        'docs/PYTHON_QML_API.md',
        'docs/MODULES/GEOMETRY_BRIDGE.md',
        'docs/MODULES/MAIN_WINDOW.md',
        'docs/MODULES/SIMULATION_MANAGER.md',
        'docs/MODULES/PNEUMATIC_SYSTEM.md',
        'docs/MODULES/PHYSICS_MECHANICS.md',
        'docs/MODULES/UI_PANELS_WIDGETS.md',
        'docs/MODULES/ROAD_SYSTEM.md',
    ]
    
    for doc_path in doc_files:
        full_path = project_root / doc_path
        if full_path.exists():
            log_test("Documentation", doc_path, "PASS")
        else:
            log_test("Documentation", doc_path, "FAIL", "File not found")


def test_geometry_bridge():
    """Test 7: GeometryBridge functionality"""
    try:
        from src.ui.geometry_bridge import GeometryBridge
        from src.core.geometry import FrameConfig
        
        # Create config
        config = FrameConfig(
            wheelbase=2.5,
            track_width=0.3,
            horn_height=0.65,
            beam_size=0.12
        )
        
        # Create bridge
        bridge = GeometryBridge(config)
        
        # Test calculation
        coords = bridge.get_corner_3d_coords('fl', lever_angle=0.0)
        
        if 'pistonPositionMm' in coords:
            log_test("GeometryBridge", "get_corner_3d_coords", "PASS",
                    f"Piston: {coords['pistonPositionMm']:.1f}mm")
        else:
            log_test("GeometryBridge", "get_corner_3d_coords", "FAIL",
                    "Missing pistonPositionMm")
        
    except Exception as e:
        log_test("GeometryBridge", "Functionality", "FAIL", str(e))


def test_kinematics():
    """Test 8: Kinematics calculations"""
    try:
        from src.mechanics.kinematics import CylinderKinematics
        import numpy as np
        
        kinematics = CylinderKinematics(
            lever_length=0.4,
            cylinder_length=0.25,
            pivot_to_tail=0.15
        )
        
        # Test angle ? stroke
        angle = np.deg2rad(5.0)
        stroke = kinematics.angle_to_stroke(angle)
        
        # Test stroke ? angle
        angle_back = kinematics.stroke_to_angle(stroke)
        
        # Check roundtrip
        error = abs(angle - angle_back)
        if error < 1e-6:
            log_test("Kinematics", "Angle?Stroke", "PASS",
                    f"Error: {error:.2e} rad")
        else:
            log_test("Kinematics", "Angle?Stroke", "FAIL",
                    f"Error: {error:.2e} rad")
        
    except Exception as e:
        log_test("Kinematics", "Calculations", "FAIL", str(e))


def test_app_startup():
    """Test 9: App can be imported"""
    try:
        # Just import, don't run
        import app
        log_test("Application", "app.py import", "PASS")
    except Exception as e:
        log_test("Application", "app.py import", "FAIL", str(e))


def test_panels():
    """Test 10: UI Panels"""
    try:
        from src.ui.panels import (
            GeometryPanel,
            ModesPanel,
            PneumoPanel,
            RoadPanel
        )
        log_test("UI Panels", "All panels import", "PASS")
    except Exception as e:
        log_test("UI Panels", "Panel imports", "FAIL", str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*70)
    
    total = test_results['total']
    passed = len(test_results['passed'])
    failed = len(test_results['failed'])
    warnings = len(test_results['warnings'])
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n?? Results:")
    print(f"  Total Tests:   {total}")
    print(f"  ? Passed:      {passed} ({pass_rate:.1f}%)")
    print(f"  ? Failed:      {failed}")
    print(f"  ??  Warnings:    {warnings}")
    
    if failed > 0:
        print(f"\n? FAILED TESTS:")
        for category, name, details in test_results['failed']:
            print(f"  [{category}] {name}")
            if details:
                print(f"    ? {details}")
    
    if warnings > 0:
        print(f"\n??  WARNINGS:")
        for category, name, details in test_results['warnings']:
            print(f"  [{category}] {name}")
            if details:
                print(f"    ? {details}")
    
    print("\n" + "="*70)
    
    if failed == 0:
        print("?? ALL TESTS PASSED!")
        print("? Project is in good state")
    else:
        print(f"??  {failed} TEST(S) FAILED")
        print("? Issues need attention")
    
    print("="*70)
    
    return failed == 0


def save_report():
    """Save test report to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = project_root / f"test_report_{timestamp}.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("COMPREHENSIVE PROJECT TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Total Tests: {test_results['total']}\n")
        f.write(f"Passed: {len(test_results['passed'])}\n")
        f.write(f"Failed: {len(test_results['failed'])}\n")
        f.write(f"Warnings: {len(test_results['warnings'])}\n\n")
        
        if test_results['failed']:
            f.write("FAILED TESTS:\n")
            for category, name, details in test_results['failed']:
                f.write(f"  [{category}] {name}\n")
                if details:
                    f.write(f"    Details: {details}\n")
            f.write("\n")
        
        f.write("="*70 + "\n")
    
    print(f"\n?? Report saved to: {report_path}")


def main():
    """Run all tests"""
    print("="*70)
    print("?? COMPREHENSIVE PROJECT TEST SUITE")
    print("="*70)
    print(f"Project: PneumoStabSim v2.0.0")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Run all tests
    test_python_version()
    test_dependencies()
    test_project_structure()
    test_module_imports()
    test_qml_files()
    test_documentation()
    test_geometry_bridge()
    test_kinematics()
    test_app_startup()
    test_panels()
    
    # Print summary
    success = print_summary()
    
    # Save report
    save_report()
    
    # Exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
