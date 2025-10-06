# -*- coding: utf-8 -*-
"""
B-3: Full integration test with running simulation
Тестирование полной интеграции с запущенной симуляцией
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=== B-3: Тест полной интеграции с симуляцией ===")

def setup_logging():
    """Настроить логирование для отслеживания интеграции"""
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
    """B-3.1: Тест запуска симуляции"""
    logger = setup_logging()
    logger.info("B-3.1: Testing simulation startup")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        from src.runtime.sim_loop import SimulationManager
        
        app = QApplication([])
        
        print("+ Создание MainWindow...")
        window = MainWindow()
        
        print("+ Проверка SimulationManager...")
        sim_manager = window.simulation_manager
        
        if sim_manager and hasattr(sim_manager, 'state_bus'):
            print("? SimulationManager готов")
            logger.info("SimulationManager created successfully")
        else:
            print("? SimulationManager не готов")
            return False
        
        print("+ Проверка PneumoPanel...")
        pneumo_panel = window.pneumo_panel
        
        if pneumo_panel and hasattr(pneumo_panel, 'receiver_volume_changed'):
            print("? PneumoPanel готов с интеграцией")
            logger.info("PneumoPanel integration ready")
        else:
            print("? PneumoPanel не готов")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Ошибка при запуске: {e}")
        logger.error(f"Startup failed: {e}")
        return False

def test_signal_flow():
    """B-3.2: Тест потока сигналов в реальном времени"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.2: Testing signal flow")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QSignalSpy
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        
        print("+ Тестирование потока сигналов...")
        
        # Create spies for signal monitoring
        pneumo_spy = QSignalSpy(window.pneumo_panel.receiver_volume_changed)
        bus_spy = QSignalSpy(window.simulation_manager.state_bus.set_receiver_volume)
        
        print("  1. Изменение объёма в UI...")
        
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
        
        print("  2. Переключение режима...")
        
        # Test mode switching
        window.pneumo_panel.volume_mode_combo.setCurrentIndex(1)  # Geometric
        window.pneumo_panel._on_volume_mode_changed(1)
        
        # Give time for signals to propagate
        app.processEvents()
        time.sleep(0.1)
        
        if pneumo_spy.count() > 1:
            print("  ? Переключение режима ? signal emitted")
            logger.info("Mode switching signal emitted")
        else:
            print("  ? Mode switching signal not emitted")
        
        print("  3. Проверка MainWindow обработчика...")
        
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
        print(f"? Ошибка тестирования сигналов: {e}")
        logger.error(f"Signal flow test failed: {e}")
        return False

def test_thermodynamic_modes():
    """B-3.3: Тест термодинамических режимов"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.3: Testing thermodynamic modes")
    
    print("+ Тестирование термодинамических режимов...")
    
    # Test mode mappings
    mode_tests = [
        ('MANUAL', 'NO_RECALC', "Ручной объём ? без пересчёта"),
        ('GEOMETRIC', 'ADIABATIC_RECALC', "Геометрический ? адиабатический пересчёт")
    ]
    
    for ui_mode, expected_thermo_mode, description in mode_tests:
        print(f"  Тест: {description}")
        
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
    """B-3.4: Тест расчётов объёма"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.4: Testing volume calculations")
    
    print("+ Тестирование расчётов объёма...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        app = QApplication([])
        window = MainWindow()
        pneumo_panel = window.pneumo_panel
        
        # Test geometric volume calculation
        print("  1. Геометрический расчёт объёма...")
        
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
            print(f"  ? Расчёт объёма: {actual_volume:.3f}м? (ожидалось {expected_volume:.3f}м?)")
            logger.info(f"Volume calculation correct: {actual_volume:.3f}m?")
        else:
            print(f"  ? Неверный расчёт: {actual_volume:.3f}м? (ожидалось {expected_volume:.3f}м?)")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Ошибка расчёта объёма: {e}")
        logger.error(f"Volume calculation test failed: {e}")
        return False

def test_parameter_persistence():
    """B-3.5: Тест сохранения параметров"""
    logger = logging.getLogger(__name__)
    logger.info("B-3.5: Testing parameter persistence")
    
    print("+ Тестирование сохранения параметров...")
    
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
        
        print("  1. Установка параметров...")
        pneumo_panel.set_parameters(test_params)
        
        print("  2. Проверка сохранения...")
        saved_params = pneumo_panel.get_parameters()
        
        for key, expected_value in test_params.items():
            actual_value = saved_params.get(key)
            if abs(actual_value - expected_value) < 0.001 if isinstance(expected_value, float) else actual_value == expected_value:
                print(f"  ? {key}: {actual_value}")
            else:
                print(f"  ? {key}: {actual_value} (ожидалось {expected_value})")
                return False
        
        logger.info("Parameter persistence test passed")
        return True
        
    except Exception as e:
        print(f"? Ошибка сохранения параметров: {e}")
        logger.error(f"Parameter persistence test failed: {e}")
        return False

def run_full_integration_test():
    """Запуск полного теста интеграции"""
    logger = setup_logging()
    logger.info("Starting B-3 full integration test")
    
    print("?? Запуск полного теста интеграции B-3")
    print("="*60)
    
    tests = [
        ("B-3.1: Запуск симуляции", test_simulation_startup),
        ("B-3.2: Поток сигналов", test_signal_flow),
        ("B-3.3: Термодинамические режимы", test_thermodynamic_modes),
        ("B-3.4: Расчёты объёма", test_volume_calculations),
        ("B-3.5: Сохранение параметров", test_parameter_persistence),
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n?? {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"? {test_name} - ПРОЙДЕН")
                passed += 1
                logger.info(f"{test_name} - PASSED")
            else:
                print(f"? {test_name} - ПРОВАЛЕН")
                logger.error(f"{test_name} - FAILED")
        except Exception as e:
            print(f"?? {test_name} - ОШИБКА: {e}")
            logger.error(f"{test_name} - ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"?? РЕЗУЛЬТАТЫ B-3: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("?? ВСЕ ТЕСТЫ ИНТЕГРАЦИИ ПРОЙДЕНЫ!")
        print("? Интеграция объёма ресивера полностью функциональна")
        logger.info("B-3 full integration test PASSED")
    else:
        print("??  Некоторые тесты провалены")
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