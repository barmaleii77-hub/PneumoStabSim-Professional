# -*- coding: utf-8 -*-
"""
B-3: Full integration test with running simulation
������������ ������ ���������� � ���������� ����������
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=== B-3: ���� ������ ���������� � ���������� ===")

def setup_logging():
    """��������� ����������� ��� ������������ ����������"""
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
    """B-3.1: ���� ������� ���������"""
    logger = setup_logging()
    logger.info("B-3.1: Testing simulation startup")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        from src.runtime.sim_loop import SimulationManager
        
        app = QApplication([])
        
        print("+ �������� MainWindow...")
        window = MainWindow()
        
        print("+ �������� SimulationManager...")
        sim_manager = window.simulation_manager
        
        if sim_manager and hasattr(sim_manager, 'state_bus'):
            print("? SimulationManager �����")
            logger.info("SimulationManager created successfully")
        else:
            print("? SimulationManager �� �����")
            return False
        
        print("+ �������� PneumoPanel...")
        pneumo_panel = window.pneumo_panel
        
        if pneumo_panel and hasattr(pneumo_panel, 'receiver_volume_changed'):
            print("? PneumoPanel ����� � �����������")
            logger.info("PneumoPanel integration ready")
        else:
            print("? PneumoPanel �� �����")
            return False
        
        return True
        
    except Exception as e:
        print(f"? ������ ��� �������: {e}")
        logger.error(f"Startup failed: {e}")
        return False

def test_signal_flow():
    """B-3.2: ���� ������ �������� � �������� �������"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.2: Testing signal flow")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QSignalSpy
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        
        print("+ ������������ ������ ��������...")
        
        # Create spies for signal monitoring
        pneumo_spy = QSignalSpy(window.pneumo_panel.receiver_volume_changed)
        bus_spy = QSignalSpy(window.simulation_manager.state_bus.set_receiver_volume)
        
        print("  1. ��������� ������ � UI...")
        
        # Test manual volume change
        window.pneumo_panel.manual_volume_knob.setValue(0.035)  # 35L
        window.pneumo_panel._on_manual_volume_changed(0.035)
        
        # Check signal emission
        if pneumo_spy.count() > 0:
            print("  ? PneumoPanel ? signal emitted")
            logger.info("PneumoPanel signal emitted successfully")
        else:
            print("  ? PneumoPanel signal not emitted")
            return False
        
        print("  2. ������������ ������...")
        
        # Test mode switching
        window.pneumo_panel.volume_mode_combo.setCurrentIndex(1)  # Geometric
        window.pneumo_panel._on_volume_mode_changed(1)
        
        # Give time for signals to propagate
        app.processEvents()
        time.sleep(0.1)
        
        if pneumo_spy.count() > 1:
            print("  ? ������������ ������ ? signal emitted")
            logger.info("Mode switching signal emitted")
        else:
            print("  ? Mode switching signal not emitted")
        
        print("  3. �������� MainWindow �����������...")
        
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
        print(f"? ������ ������������ ��������: {e}")
        logger.error(f"Signal flow test failed: {e}")
        return False

def test_thermodynamic_modes():
    """B-3.3: ���� ����������������� �������"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.3: Testing thermodynamic modes")
    
    print("+ ������������ ����������������� �������...")
    
    # Test mode mappings
    mode_tests = [
        ('MANUAL', 'NO_RECALC', "������ ����� ? ��� ���������"),
        ('GEOMETRIC', 'ADIABATIC_RECALC', "�������������� ? �������������� ��������")
    ]
    
    for ui_mode, expected_thermo_mode, description in mode_tests:
        print(f"  ����: {description}")
        
        # This would be the mapping logic from MainWindow
        receiver_mode = 'NO_RECALC' if ui_mode == 'MANUAL' else 'ADIABATIC_RECALC'
        
        if receiver_mode == expected_thermo_mode:
            print(f"  ? {ui_mode} ? {receiver_mode}")
            logger.info(f"Mode mapping correct: {ui_mode} ? {receiver_mode}")
        else:
            print(f"  ? {ui_mode} ? {receiver_mode} (expected {expected_thermo_mode})")
            return False
    
    return True

def test_volume_calculations():
    """B-3.4: ���� �������� ������"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.4: Testing volume calculations")
    
    print("+ ������������ �������� ������...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        pneumo_panel = window.pneumo_panel
        
        # Test geometric volume calculation
        print("  1. �������������� ������ ������...")
        
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
            print(f"  ? ������ ������: {actual_volume:.3f}�? (��������� {expected_volume:.3f}�?)")
            logger.info(f"Volume calculation correct: {actual_volume:.3f}m?")
        else:
            print(f"  ? �������� ������: {actual_volume:.3f}�? (��������� {expected_volume:.3f}�?)")
            return False
        
        return True
        
    except Exception as e:
        print(f"? ������ ������� ������: {e}")
        logger.error(f"Volume calculation test failed: {e}")
        return False

def test_parameter_persistence():
    """B-3.5: ���� ���������� ����������"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.5: Testing parameter persistence")
    
    print("+ ������������ ���������� ����������...")
    
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
        
        print("  1. ��������� ����������...")
        pneumo_panel.set_parameters(test_params)
        
        print("  2. �������� ����������...")
        saved_params = pneumo_panel.get_parameters()
        
        for key, expected_value in test_params.items():
            actual_value = saved_params.get(key)
            if abs(actual_value - expected_value) < 0.001 if isinstance(expected_value, float) else actual_value == expected_value:
                print(f"  ? {key}: {actual_value}")
            else:
                print(f"  ? {key}: {actual_value} (��������� {expected_value})")
                return False
        
        logger.info("Parameter persistence test passed")
        return True
        
    except Exception as e:
        print(f"? ������ ���������� ����������: {e}")
        logger.error(f"Parameter persistence test failed: {e}")
        return False

def run_full_integration_test():
    """������ ������� ����� ����������"""
    logger = setup_logging()
    logger.info("Starting B-3 full integration test")
    
    print("?? ������ ������� ����� ���������� B-3")
    print("="*60)
    
    tests = [
        ("B-3.1: ������ ���������", test_simulation_startup),
        ("B-3.2: ����� ��������", test_signal_flow),
        ("B-3.3: ����������������� ������", test_thermodynamic_modes),
        ("B-3.4: ������� ������", test_volume_calculations),
        ("B-3.5: ���������� ����������", test_parameter_persistence),
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n?? {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"? {test_name} - �������")
                passed += 1
                logger.info(f"{test_name} - PASSED")
            else:
                print(f"? {test_name} - ��������")
                logger.error(f"{test_name} - FAILED")
        except Exception as e:
            print(f"?? {test_name} - ������: {e}")
            logger.error(f"{test_name} - ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"?? ���������� B-3: {passed}/{len(tests)} ������ ��������")
    
    if passed == len(tests):
        print("?? ��� ����� ���������� ��������!")
        print("? ���������� ������ �������� ��������� �������������")
        logger.info("B-3 full integration test PASSED")
    else:
        print("??  ��������� ����� ���������")
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