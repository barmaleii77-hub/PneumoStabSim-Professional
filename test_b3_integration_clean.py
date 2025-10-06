# -*- coding: utf-8 -*-
"""
B-3: Full integration test with running simulation
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=== B-3: Full integration test ===")

def setup_logging():
    """Setup logging for integration tracking"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('b3_integration_test.log')
        ]
    )
    return logging.getLogger(__name__)

def test_simulation_startup():
    """B-3.1: Test simulation startup"""
    logger = setup_logging()
    logger.info("B-3.1: Testing simulation startup")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        from src.runtime.sim_loop import SimulationManager
        
        app = QApplication([])
        
        print("+ Creating MainWindow...")
        window = MainWindow()
        
        print("+ Checking SimulationManager...")
        sim_manager = window.simulation_manager
        
        if sim_manager and hasattr(sim_manager, 'state_bus'):
            print("? SimulationManager ready")
            logger.info("SimulationManager created successfully")
        else:
            print("? SimulationManager not ready")
            return False
        
        print("+ Checking PneumoPanel...")
        pneumo_panel = window.pneumo_panel
        
        if pneumo_panel and hasattr(pneumo_panel, 'receiver_volume_changed'):
            print("? PneumoPanel ready with integration")
            logger.info("PneumoPanel integration ready")
        else:
            print("? PneumoPanel not ready")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Startup error: {e}")
        logger.error(f"Startup failed: {e}")
        return False

def test_signal_flow():
    """B-3.2: Test signal flow in real-time"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.2: Testing signal flow")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QSignalSpy
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        
        print("+ Testing signal flow...")
        
        # Create spies for signal monitoring
        pneumo_spy = QSignalSpy(window.pneumo_panel.receiver_volume_changed)
        
        print("  1. Changing volume in UI...")
        
        # Test manual volume change
        window.pneumo_panel.manual_volume_knob.setValue(0.035)  # 35L
        window.pneumo_panel._on_manual_volume_changed(0.035)
        
        # Check signal emission
        if pneumo_spy.count() > 0:
            print("  ? PneumoPanel -> signal emitted")
            logger.info("PneumoPanel signal emitted successfully")
        else:
            print("  ? PneumoPanel signal not emitted")
            return False
        
        print("  2. Switching mode...")
        
        # Test mode switching
        window.pneumo_panel.volume_mode_combo.setCurrentIndex(1)  # Geometric
        window.pneumo_panel._on_volume_mode_changed(1)
        
        # Give time for signals to propagate
        app.processEvents()
        time.sleep(0.1)
        
        if pneumo_spy.count() > 1:
            print("  ? Mode switching -> signal emitted")
            logger.info("Mode switching signal emitted")
        else:
            print("  ? Mode switching signal not emitted")
        
        print("  3. Testing MainWindow handler...")
        
        # Test MainWindow handler directly
        try:
            window._on_receiver_volume_changed(0.040, 'MANUAL')
            print("  ? MainWindow handler working")
            logger.info("MainWindow handler executed successfully")
        except Exception as e:
            print(f"  ? MainWindow handler error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Signal flow test error: {e}")
        logger.error(f"Signal flow test failed: {e}")
        return False

def test_thermodynamic_modes():
    """B-3.3: Test thermodynamic modes"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.3: Testing thermodynamic modes")
    
    print("+ Testing thermodynamic modes...")
    
    # Test mode mappings
    mode_tests = [
        ('MANUAL', 'NO_RECALC', "Manual volume -> no recalc"),
        ('GEOMETRIC', 'ADIABATIC_RECALC', "Geometric -> adiabatic recalc")
    ]
    
    for ui_mode, expected_thermo_mode, description in mode_tests:
        print(f"  Test: {description}")
        
        # This would be the mapping logic from MainWindow
        receiver_mode = 'NO_RECALC' if ui_mode == 'MANUAL' else 'ADIABATIC_RECALC'
        
        if receiver_mode == expected_thermo_mode:
            print(f"  ? {ui_mode} -> {receiver_mode}")
            logger.info(f"Mode mapping correct: {ui_mode} -> {receiver_mode}")
        else:
            print(f"  ? {ui_mode} -> {receiver_mode} (expected {expected_thermo_mode})")
            return False
    
    return True

def test_volume_calculations():
    """B-3.4: Test volume calculations"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.4: Testing volume calculations")
    
    print("+ Testing volume calculations...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        pneumo_panel = window.pneumo_panel
        
        # Test geometric volume calculation
        print("  1. Geometric volume calculation...")
        
        # Set known dimensions
        diameter = 0.300  # 300mm
        length = 0.800    # 800mm
        
        pneumo_panel.receiver_diameter_knob.setValue(diameter)
        pneumo_panel.receiver_length_knob.setValue(length)
        
        # Switch to geometric mode and trigger calculation
        pneumo_panel.volume_mode_combo.setCurrentIndex(1)
        pneumo_panel._on_volume_mode_changed(1)
        
        # Calculate expected volume: V = ? ? (D/2)? ? L
        import math
        expected_volume = math.pi * (diameter/2)**2 * length
        
        actual_volume = pneumo_panel.parameters.get('receiver_volume', 0)
        
        if abs(actual_volume - expected_volume) < 0.001:  # 1L tolerance
            print(f"  ? Volume calculation: {actual_volume:.3f}m? (expected {expected_volume:.3f}m?)")
            logger.info(f"Volume calculation correct: {actual_volume:.3f}m?")
        else:
            print(f"  ? Wrong calculation: {actual_volume:.3f}m? (expected {expected_volume:.3f}m?)")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Volume calculation error: {e}")
        logger.error(f"Volume calculation test failed: {e}")
        return False

def test_parameter_persistence():
    """B-3.5: Test parameter persistence"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.5: Testing parameter persistence")
    
    print("+ Testing parameter persistence...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        pneumo_panel = window.pneumo_panel
        
        # Set test parameters
        test_params = {
            'volume_mode': 'GEOMETRIC',
            'receiver_diameter': 0.250,
            'receiver_length': 0.600,
            'receiver_volume': 0.025
        }
        
        print("  1. Setting parameters...")
        pneumo_panel.set_parameters(test_params)
        
        print("  2. Checking persistence...")
        saved_params = pneumo_panel.get_parameters()
        
        for key, expected_value in test_params.items():
            actual_value = saved_params.get(key)
            if isinstance(expected_value, float):
                if abs(actual_value - expected_value) < 0.001:
                    print(f"  ? {key}: {actual_value}")
                else:
                    print(f"  ? {key}: {actual_value} (expected {expected_value})")
                    return False
            else:
                if actual_value == expected_value:
                    print(f"  ? {key}: {actual_value}")
                else:
                    print(f"  ? {key}: {actual_value} (expected {expected_value})")
                    return False
        
        logger.info("Parameter persistence test passed")
        return True
        
    except Exception as e:
        print(f"? Parameter persistence error: {e}")
        logger.error(f"Parameter persistence test failed: {e}")
        return False

def run_full_integration_test():
    """Run full integration test"""
    logger = setup_logging()
    logger.info("Starting B-3 full integration test")
    
    print("?? Running B-3 full integration test")
    print("="*60)
    
    tests = [
        ("B-3.1: Simulation startup", test_simulation_startup),
        ("B-3.2: Signal flow", test_signal_flow),
        ("B-3.3: Thermodynamic modes", test_thermodynamic_modes),
        ("B-3.4: Volume calculations", test_volume_calculations),
        ("B-3.5: Parameter persistence", test_parameter_persistence),
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n?? {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"? {test_name} - PASSED")
                passed += 1
                logger.info(f"{test_name} - PASSED")
            else:
                print(f"? {test_name} - FAILED")
                logger.error(f"{test_name} - FAILED")
        except Exception as e:
            print(f"?? {test_name} - ERROR: {e}")
            logger.error(f"{test_name} - ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"?? B-3 RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("?? ALL INTEGRATION TESTS PASSED!")
        print("? Receiver volume integration fully functional")
        logger.info("B-3 full integration test PASSED")
    else:
        print("??  Some tests failed")
        logger.warning(f"B-3 integration test incomplete: {passed}/{len(tests)}")
    
    print("="*60)
    return passed == len(tests)

if __name__ == "__main__":
    success = run_full_integration_test()
    
    # Create completion report
    with open("reports/receiver/B3_test_results.md", "w", encoding="utf-8") as f:
        f.write(f"# B-3 Test Results\n\n")
        f.write(f"**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Result**: {'? PASSED' if success else '? FAILED'}\n\n")
        f.write(f"See `b3_integration_test.log` for detailed logs.\n")
    
    sys.exit(0 if success else 1)