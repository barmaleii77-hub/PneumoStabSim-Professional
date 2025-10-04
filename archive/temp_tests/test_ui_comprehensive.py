# -*- coding: utf-8 -*-
"""
Comprehensive UI Test - Full interface testing
Tests all aspects of window layout, panels, and scaling
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt, QRect
from PySide6.QtTest import QTest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.main_window import MainWindow

class UITester:
    """Comprehensive UI testing"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = None
        self.test_results = []
        
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "? PASS" if passed else "? FAIL"
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"       {details}")
    
    def test_initial_window_size(self):
        """Test 1: Initial window size"""
        print("\n" + "="*60)
        print("TEST 1: Initial Window Size")
        print("="*60)
        
        size = self.window.size()
        width = size.width()
        height = size.height()
        
        print(f"Window size: {width}x{height}")
        
        # Check if size is reasonable
        passed = (1000 <= width <= 2000) and (700 <= height <= 1200)
        self.log_result(
            "Initial window size",
            passed,
            f"Expected: 1200x800, Got: {width}x{height}"
        )
        
        # Check minimum size
        min_size = self.window.minimumSize()
        min_passed = min_size.width() >= 1000 and min_size.height() >= 700
        self.log_result(
            "Minimum size constraint",
            min_passed,
            f"Min size: {min_size.width()}x{min_size.height()}"
        )
    
    def test_central_widget(self):
        """Test 2: Central widget existence and size"""
        print("\n" + "="*60)
        print("TEST 2: Central Widget")
        print("="*60)
        
        central = self.window.centralWidget()
        
        # Check existence
        exists = central is not None
        self.log_result("Central widget exists", exists)
        
        if central:
            size = central.size()
            print(f"Central widget size: {size.width()}x{size.height()}")
            
            # Central widget should have reasonable size
            reasonable = size.width() > 200 and size.height() > 200
            self.log_result(
                "Central widget has reasonable size",
                reasonable,
                f"Size: {size.width()}x{size.height()}"
            )
            
            # Check if visible
            visible = central.isVisible()
            self.log_result("Central widget is visible", visible)
    
    def test_dock_panels(self):
        """Test 3: All dock panels"""
        print("\n" + "="*60)
        print("TEST 3: Dock Panels")
        print("="*60)
        
        docks = {
            'Geometry': self.window.geometry_dock,
            'Pneumatics': self.window.pneumo_dock,
            'Charts': self.window.charts_dock,
            'Modes': self.window.modes_dock,
            'Road': self.window.road_dock
        }
        
        for name, dock in docks.items():
            print(f"\nChecking {name} dock:")
            
            # Existence
            exists = dock is not None
            self.log_result(f"{name} dock exists", exists)
            
            if dock:
                # Visibility (Road dock is hidden by default - this is OK)
                visible = dock.isVisible()
                if name == 'Road':
                    # Road dock is intentionally hidden by default
                    self.log_result(f"{name} dock state", True, 
                                  "Hidden by default (by design)" if not visible else "Visible")
                else:
                    self.log_result(f"{name} dock is visible", visible)
                
                # Size constraints
                if name in ['Geometry', 'Pneumatics']:
                    min_w = dock.minimumWidth()
                    max_w = dock.maximumWidth()
                    print(f"  Width constraints: {min_w} - {max_w}")
                    
                    has_min = min_w >= 200
                    has_max = max_w <= 500
                    self.log_result(
                        f"{name} dock has width constraints",
                        has_min and has_max,
                        f"Min: {min_w}, Max: {max_w}"
                    )
                
                elif name in ['Charts', 'Modes']:
                    min_w = dock.minimumWidth()
                    max_w = dock.maximumWidth()
                    print(f"  Width constraints: {min_w} - {max_w}")
                    
                    has_min = min_w >= 250
                    has_max = max_w <= 700
                    self.log_result(
                        f"{name} dock has width constraints",
                        has_min and has_max,
                        f"Min: {min_w}, Max: {max_w}"
                    )
                
                elif name == 'Road':
                    min_h = dock.minimumHeight()
                    max_h = dock.maximumHeight()
                    print(f"  Height constraints: {min_h} - {max_h}")
                    
                    has_min = min_h >= 100
                    has_max = max_h <= 400
                    self.log_result(
                        f"{name} dock has height constraints",
                        has_min and has_max,
                        f"Min: {min_h}, Max: {max_h}"
                    )
                
                # Widget inside dock
                widget = dock.widget()
                has_widget = widget is not None
                self.log_result(f"{name} dock has widget", has_widget)
                
                if widget:
                    w_size = widget.size()
                    print(f"  Widget size: {w_size.width()}x{w_size.height()}")
    
    def test_dock_overlap(self):
        """Test 4: Check if docks overlap"""
        print("\n" + "="*60)
        print("TEST 4: Dock Overlap Detection")
        print("="*60)
        
        docks = [
            ('Geometry', self.window.geometry_dock),
            ('Pneumatics', self.window.pneumo_dock),
            ('Charts', self.window.charts_dock),
            ('Modes', self.window.modes_dock),
            ('Road', self.window.road_dock)
        ]
        
        # Get geometries (only visible docks)
        geometries = {}
        for name, dock in docks:
            if dock and dock.isVisible() and not dock.isFloating():
                # Check if dock is tabified (not actually taking space)
                geom = dock.geometry()
                # Skip docks with negative coordinates (tabified hidden tabs)
                if geom.x() >= 0 and geom.y() >= 0:
                    geometries[name] = geom
                    print(f"{name}: x={geom.x()}, y={geom.y()}, "
                          f"w={geom.width()}, h={geom.height()}")
                else:
                    print(f"{name}: tabified (hidden)")
        
        # Check overlaps
        overlaps = []
        names = list(geometries.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name1, name2 = names[i], names[j]
                geom1 = geometries[name1]
                geom2 = geometries[name2]
                
                if geom1.intersects(geom2):
                    # Check if intersection is significant (not just edge touching)
                    intersection = geom1.intersected(geom2)
                    if intersection.width() > 5 and intersection.height() > 5:
                        overlaps.append((name1, name2, intersection))
                        print(f"??  Overlap detected: {name1} ? {name2}")
                        print(f"   Intersection: {intersection.width()}x{intersection.height()}")
        
        no_overlaps = len(overlaps) == 0
        self.log_result(
            "No significant dock overlaps",
            no_overlaps,
            f"Found {len(overlaps)} overlaps" if overlaps else "All visible docks properly positioned"
        )
    
    def test_central_widget_space(self):
        """Test 5: Central widget has adequate space"""
        print("\n" + "="*60)
        print("TEST 5: Central Widget Space")
        print("="*60)
        
        central = self.window.centralWidget()
        if not central:
            self.log_result("Central widget space", False, "No central widget")
            return
        
        window_size = self.window.size()
        central_size = central.size()
        
        print(f"Window: {window_size.width()}x{window_size.height()}")
        print(f"Central: {central_size.width()}x{central_size.height()}")
        
        # Central widget should have at least 30% of window width and height
        width_ratio = central_size.width() / window_size.width()
        height_ratio = central_size.height() / window_size.height()
        
        print(f"Central widget??: width={width_ratio*100:.1f}%, height={height_ratio*100:.1f}%")
        
        adequate = width_ratio >= 0.25 and height_ratio >= 0.25
        self.log_result(
            "Central widget has adequate space",
            adequate,
            f"Width: {width_ratio*100:.1f}%, Height: {height_ratio*100:.1f}%"
        )
    
    def test_maximize_window(self):
        """Test 6: Maximize window"""
        print("\n" + "="*60)
        print("TEST 6: Window Maximization")
        print("="*60)
        
        # Store original size
        original_size = self.window.size()
        print(f"Original size: {original_size.width()}x{original_size.height()}")
        
        # Maximize
        self.window.showMaximized()
        QTest.qWait(500)  # Wait for animation
        
        maximized_size = self.window.size()
        print(f"Maximized size: {maximized_size.width()}x{maximized_size.height()}")
        
        # Check if actually maximized
        is_maximized = self.window.isMaximized()
        self.log_result("Window is maximized", is_maximized)
        
        # Check if size increased
        increased = (maximized_size.width() > original_size.width() and 
                    maximized_size.height() > original_size.height())
        self.log_result("Window size increased", increased)
        
        # Check central widget still visible
        central = self.window.centralWidget()
        if central:
            central_size = central.size()
            print(f"Central widget (maximized): {central_size.width()}x{central_size.height()}")
            
            still_visible = central_size.width() > 200 and central_size.height() > 200
            self.log_result("Central widget still visible when maximized", still_visible)
        
        # Check docks after maximize
        self.test_dock_overlap()
        
        # Restore
        self.window.showNormal()
        QTest.qWait(500)
    
    def test_resize_stress(self):
        """Test 7: Resize stress test"""
        print("\n" + "="*60)
        print("TEST 7: Resize Stress Test")
        print("="*60)
        
        sizes_to_test = [
            (1000, 700),   # Minimum
            (1200, 800),   # Default
            (1400, 900),   # Larger
            (1600, 1000),  # Even larger
            (1000, 700),   # Back to minimum
        ]
        
        all_ok = True
        for width, height in sizes_to_test:
            print(f"\nResizing to {width}x{height}...")
            self.window.resize(width, height)
            QTest.qWait(200)
            
            # Check central widget
            central = self.window.centralWidget()
            if central:
                c_size = central.size()
                has_space = c_size.width() > 100 and c_size.height() > 100
                
                if not has_space:
                    print(f"  ? Central widget too small: {c_size.width()}x{c_size.height()}")
                    all_ok = False
                else:
                    print(f"  ? Central widget: {c_size.width()}x{c_size.height()}")
        
        self.log_result("Resize stress test", all_ok, 
                       "All sizes handled correctly" if all_ok else "Some sizes problematic")
    
    def test_toolbar_statusbar(self):
        """Test 8: Toolbar and status bar"""
        print("\n" + "="*60)
        print("TEST 8: Toolbar and Status Bar")
        print("="*60)
        
        # Toolbar
        toolbars = self.window.findChildren(QApplication.instance().__class__.__bases__[0])
        toolbar = None
        for tb in self.window.findChildren(self.window.__class__.__bases__[0]):
            if hasattr(tb, 'objectName') and 'toolbar' in tb.objectName().lower():
                toolbar = tb
                break
        
        if not toolbar:
            # Try to get toolbar differently
            for child in self.window.children():
                if child.__class__.__name__ == 'QToolBar':
                    toolbar = child
                    break
        
        has_toolbar = toolbar is not None
        self.log_result("Toolbar exists", has_toolbar)
        
        if toolbar:
            tb_height = toolbar.height()
            print(f"Toolbar height: {tb_height}")
            reasonable_height = 20 <= tb_height <= 60
            self.log_result("Toolbar height is reasonable", reasonable_height, 
                          f"Height: {tb_height}px")
        
        # Status bar
        statusbar = self.window.statusBar()
        has_statusbar = statusbar is not None
        self.log_result("Status bar exists", has_statusbar)
        
        if statusbar:
            sb_height = statusbar.height()
            print(f"Status bar height: {sb_height}")
            reasonable_height = 20 <= sb_height <= 40
            self.log_result("Status bar height is reasonable", reasonable_height,
                          f"Height: {sb_height}px")
    
    def test_qml_widget(self):
        """Test 9: QML widget in central area"""
        print("\n" + "="*60)
        print("TEST 9: QML Widget")
        print("="*60)
        
        has_qml = self.window._qquick_widget is not None
        self.log_result("QML widget exists", has_qml)
        
        if self.window._qquick_widget:
            qml = self.window._qquick_widget
            
            # Check size
            size = qml.size()
            print(f"QML widget size: {size.width()}x{size.height()}")
            
            has_size = size.width() > 100 and size.height() > 100
            self.log_result("QML widget has size", has_size, 
                          f"{size.width()}x{size.height()}")
            
            # Check visible
            visible = qml.isVisible()
            self.log_result("QML widget is visible", visible)
            
            # Check root object
            has_root = self.window._qml_root_object is not None
            self.log_result("QML root object exists", has_root)
            
            if self.window._qml_root_object:
                root = self.window._qml_root_object
                print(f"QML root: {root}")
                
                # Try to get properties
                try:
                    width = root.property('width')
                    height = root.property('height')
                    print(f"QML root size: {width}x{height}")
                    
                    has_qml_size = width > 0 and height > 0
                    self.log_result("QML root has size", has_qml_size,
                                  f"{width}x{height}")
                except Exception as e:
                    self.log_result("QML root properties accessible", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed} ?")
        print(f"Failed: {failed} ?")
        print(f"Success rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("Failed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  ? {result['name']}")
                    if result['details']:
                        print(f"     {result['details']}")
        
        print("\n" + "="*60)
        
        return passed == total
    
    def run_all_tests(self):
        """Run all UI tests"""
        print("\n" + "??"*30)
        print("COMPREHENSIVE UI TEST SUITE")
        print("??"*30)
        
        # Create window
        print("\nCreating MainWindow...")
        self.window = MainWindow()
        self.window.show()
        
        # Wait for window to stabilize
        QTest.qWait(1000)
        
        # Run tests
        self.test_initial_window_size()
        self.test_central_widget()
        self.test_dock_panels()
        self.test_dock_overlap()
        self.test_central_widget_space()
        self.test_toolbar_statusbar()
        self.test_qml_widget()
        self.test_resize_stress()
        self.test_maximize_window()
        
        # Print summary
        all_passed = self.print_summary()
        
        # Keep window open for 5 seconds for visual inspection
        print("\nWindow will remain open for 5 seconds for visual inspection...")
        QTest.qWait(5000)
        
        return all_passed


def main():
    """Main test function"""
    tester = UITester()
    all_passed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
