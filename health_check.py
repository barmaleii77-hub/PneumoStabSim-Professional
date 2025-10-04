#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated Project Health Check Script
Automatic project health check for PneumoStabSim
"""
import sys
import os
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check Python version compatibility"""
    print("?? Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 13):
        print("   ? Python version compatible")
        return True
    else:
        print("   ? Python version too old (requires >=3.13)")
        return False


def check_dependencies():
    """Check required dependencies"""
    print("?? Checking dependencies...")

    required_packages = [
        ('PySide6', 'PySide6'),
        ('numpy', 'numpy'), 
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib')
    ]
    
    all_ok = True
    for package_name, import_name in required_packages:
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'Unknown')
                print(f"   ? {package_name}: {version}")
            else:
                print(f"   ? {package_name}: Not found")
                all_ok = False
        except Exception as e:
            print(f"   ? {package_name}: Error - {e}")
            all_ok = False
    
    return all_ok


def check_project_structure():
    """Check project structure"""
    print("??? Checking project structure...")
    
    required_paths = [
        'src/',
        'src/core/',
        'src/mechanics/', 
        'src/ui/',
        'src/ui/panels/',
        'tests/',
        'requirements.txt',
        'pyproject.toml',
        'app.py'
    ]
    
    all_ok = True
    for path in required_paths:
        if Path(path).exists():
            print(f"   ? {path}")
        else:
            print(f"   ? {path} - Missing")
            all_ok = False
    
    return all_ok


def check_core_imports():
    """Check core module imports"""
    print("?? Checking core imports...")
    
    test_imports = [
        ('src.core.geometry', ['GeometryParams', 'Point2']),
        ('src.mechanics.kinematics', ['LeverKinematics', 'CylinderKinematics']),
        ('src.ui.panels.panel_geometry', ['GeometryPanel']),
        ('src.ui.panels.panel_pneumo', ['PneumoPanel'])
    ]
    
    all_ok = True
    for module_name, classes in test_imports:
        try:
            module = importlib.import_module(module_name)
            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"   ? {module_name}.{class_name}")
                else:
                    print(f"   ? {module_name}.{class_name} - Not found")
                    all_ok = False
        except Exception as e:
            print(f"   ? {module_name} - Import error: {e}")
            all_ok = False
    
    return all_ok


def check_compilation():
    """Check Python file compilation"""
    print("?? Checking compilation...")
    
    key_files = [
        'app.py',
        'test_user_controlled_suspension.py',
        'src/core/geometry.py',
        'src/mechanics/kinematics.py'
    ]
    
    all_ok = True
    for file_path in key_files:
        if Path(file_path).exists():
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'py_compile', file_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"   ? {file_path}")
                else:
                    print(f"   ? {file_path} - Compilation error:")
                    print(f"      {result.stderr}")
                    all_ok = False
            except Exception as e:
                print(f"   ? {file_path} - Error: {e}")
                all_ok = False
        else:
            print(f"   ? {file_path} - File not found")
            all_ok = False
    
    return all_ok


def check_qt_backend():
    """Check Qt Quick backend"""
    print("?? Checking Qt Quick backend...")
    
    try:
        os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtQuickWidgets import QQuickWidget
        
        # Quick test - create and destroy app
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            print("   ? Qt application created")
            
            widget = QQuickWidget()
            print("   ? QQuickWidget created")
            
            app.quit()
            print("   ? Qt Quick backend functional")
            return True
        else:
            print("   ? Qt application already running")
            return True
            
    except Exception as e:
        print(f"   ? Qt Quick error: {e}")
        return False


def run_integration_test():
    """Run quick integration test"""
    print("?? Running integration test...")
    
    try:
        # Test geometry calculations
        from src.core.geometry import GeometryParams, Point2
        params = GeometryParams()
        point = Point2(1.0, 2.0)
        print(f"   ? Geometry: wheelbase={params.wheelbase}m")
        
        # Test kinematics
        from src.mechanics.kinematics import LeverKinematics
        lever = LeverKinematics(0.4, point, 0.3, 0.7)
        state = lever.solve_from_angle(0.1)
        print(f"   ? Kinematics: angle={state.angle:.3f}rad")
        
        # Test UI panels (basic import)
        from src.ui.panels.panel_geometry import GeometryPanel
        print("   ? UI panels importable")
        
        return True
        
    except Exception as e:
        print(f"   ? Integration test failed: {e}")
        return False


def main():
    """Main health check"""
    print("="*60)
    print("?? PNEUMOSTABSIM PROJECT HEALTH CHECK")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies), 
        ("Project Structure", check_project_structure),
        ("Core Imports", check_core_imports),
        ("Compilation", check_compilation),
        ("Qt Backend", check_qt_backend),
        ("Integration Test", run_integration_test)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n?? {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ? Unexpected error: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("?? HEALTH CHECK SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "? PASS" if result else "? FAIL"
        print(f"{status} {check_name}")
    
    print(f"\n?? OVERALL SCORE: {passed}/{total} ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("?? PROJECT STATUS: HEALTHY ?")
        return 0
    elif passed >= total * 0.8:
        print("?? PROJECT STATUS: MOSTLY HEALTHY ??")
        return 1
    else:
        print("?? PROJECT STATUS: NEEDS ATTENTION ?") 
        return 2


if __name__ == "__main__":
    sys.exit(main())