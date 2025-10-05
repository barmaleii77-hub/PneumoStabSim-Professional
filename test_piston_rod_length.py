#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test piston rod length parameter
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_geometry_panel_import():
    """Test that GeometryPanel can be imported"""
    print("=" * 70)
    print("TEST 1: Import GeometryPanel")
    print("=" * 70)
    
    try:
        from src.ui.panels.panel_geometry import GeometryPanel
        print("? GeometryPanel imported successfully")
        return True
    except Exception as e:
        print(f"? Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_piston_rod_length_parameter():
    """Test that piston_rod_length parameter exists"""
    print("\n" + "=" * 70)
    print("TEST 2: Check piston_rod_length parameter")
    print("=" * 70)
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.panels.panel_geometry import GeometryPanel
        
        # Create QApplication (required for widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create panel
        panel = GeometryPanel()
        
        # Check slider exists
        has_slider = hasattr(panel, 'piston_rod_length_slider')
        print(f"? piston_rod_length_slider exists: {has_slider}")
        
        # Check parameter in defaults
        has_param = 'piston_rod_length' in panel.parameters
        print(f"? piston_rod_length in parameters: {has_param}")
        
        # Get default value
        default_value = panel.parameters.get('piston_rod_length', 'NOT FOUND')
        print(f"? Default value: {default_value}mm")
        
        # Check slider range
        if has_slider:
            slider_min = panel.piston_rod_length_slider.minimum()
            slider_max = panel.piston_rod_length_slider.maximum()
            slider_val = panel.piston_rod_length_slider.value()
            print(f"? Slider range: {slider_min} - {slider_max} mm")
            print(f"? Slider value: {slider_val} mm")
        
        # Clean up
        panel.deleteLater()
        
        return has_slider and has_param and default_value == 200.0
        
    except Exception as e:
        print(f"? Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qml_parameter():
    """Test that QML files have pistonRodLength property"""
    print("\n" + "=" * 70)
    print("TEST 3: Check QML files for pistonRodLength")
    print("=" * 70)
    
    # Check main.qml
    main_qml = Path("assets/qml/main.qml")
    if main_qml.exists():
        try:
            # Try different encodings
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']:
                try:
                    content = main_qml.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content:
                has_property = 'userPistonRodLength' in content
                print(f"? main.qml has userPistonRodLength: {has_property}")
            else:
                print(f"??  Could not read main.qml (encoding issue)")
                has_property = False
        except Exception as e:
            print(f"??  Error reading main.qml: {e}")
            has_property = False
    else:
        print(f"??  main.qml not found")
        has_property = False
    
    # Check CorrectedSuspensionCorner.qml
    corner_qml = Path("assets/qml/components/CorrectedSuspensionCorner.qml")
    if corner_qml.exists():
        try:
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']:
                try:
                    content = corner_qml.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content:
                has_property2 = 'pistonRodLength' in content
                print(f"? CorrectedSuspensionCorner.qml has pistonRodLength: {has_property2}")
            else:
                print(f"??  Could not read CorrectedSuspensionCorner.qml (encoding issue)")
                has_property2 = False
        except Exception as e:
            print(f"??  Error reading CorrectedSuspensionCorner.qml: {e}")
            has_property2 = False
    else:
        print(f"??  CorrectedSuspensionCorner.qml not found")
        has_property2 = False
    
    return has_property or has_property2  # At least one should pass


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("?? PISTON ROD LENGTH PARAMETER TEST")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Import
    results.append(("Import GeometryPanel", test_geometry_panel_import()))
    
    # Test 2: Parameter exists
    results.append(("piston_rod_length parameter", test_piston_rod_length_parameter()))
    
    # Test 3: QML properties
    results.append(("QML properties", test_qml_parameter()))
    
    # Summary
    print("\n" + "=" * 70)
    print("?? TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "? PASS" if result else "? FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("?? ALL TESTS PASSED!")
        return 0
    else:
        print("??  SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
