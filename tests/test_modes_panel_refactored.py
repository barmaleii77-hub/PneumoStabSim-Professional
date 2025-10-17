# -*- coding: utf-8 -*-
"""
Unit tests for ModesPanel refactored version
Тесты панели режимов симуляции
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.ui.panels.modes import ModesPanel, ModesStateManager
from src.ui.panels.modes.defaults import DEFAULT_MODES_PARAMS, MODE_PRESETS

# Create QApplication for tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


def test_state_manager_initialization():
    """Тест инициализации StateManager"""
    print("\n" + "="*60)
    print("TEST 1: StateManager Initialization")
    print("="*60)
    
    manager = ModesStateManager()
    
    # Check default parameters
    params = manager.get_parameters()
    assert params['sim_type'] == 'KINEMATICS'
    assert params['thermo_mode'] == 'ISOTHERMAL'
    assert params['amplitude'] == 0.05
    assert params['frequency'] == 1.0
    
    # Check physics options
    options = manager.get_physics_options()
    assert options['include_springs'] == True
    assert options['include_dampers'] == True
    assert options['include_pneumatics'] == True
    
    print("✅ Default parameters initialized correctly")
    print(f"   Sim type: {params['sim_type']}")
    print(f"   Thermo: {params['thermo_mode']}")
    print(f"   Physics: {options}")
    return True


def test_parameter_validation():
    """Тест валидации параметров"""
    print("\n" + "="*60)
    print("TEST 2: Parameter Validation")
    print("="*60)
    
    manager = ModesStateManager()
    
    # Valid parameters
    manager.update_parameter('amplitude', 0.08)
    manager.update_parameter('frequency', 2.5)
    errors = manager.validate_state()
    assert len(errors) == 0
    print("✅ Valid parameters passed validation")
    
    # Invalid amplitude
    manager.update_parameter('amplitude', 0.25)  # > max (0.2)
    errors = manager.validate_state()
    assert len(errors) > 0
    print(f"✅ Invalid amplitude detected: {errors}")
    
    # Invalid frequency
    manager.update_parameter('amplitude', 0.1)  # Fix amplitude
    manager.update_parameter('frequency', 15.0)  # > max (10.0)
    errors = manager.validate_state()
    assert len(errors) > 0
    print(f"✅ Invalid frequency detected: {errors}")
    
    return True


def test_preset_application():
    """Тест применения пресетов"""
    print("\n" + "="*60)
    print("TEST 3: Preset Application")
    print("="*60)
    
    manager = ModesStateManager()
    
    # Test each preset
    for index, preset in MODE_PRESETS.items():
        if preset.get('custom'):
            continue
        
        print(f"\n   Testing preset #{index}: {preset['name']}")
        updates = manager.apply_preset(index)
        
        params = manager.get_parameters()
        options = manager.get_physics_options()
        
        # Check sim type
        if 'sim_type' in preset:
            assert params['sim_type'] == preset['sim_type']
            print(f"      ✓ Sim type: {params['sim_type']}")
        
        # Check thermo mode
        if 'thermo_mode' in preset:
            assert params['thermo_mode'] == preset['thermo_mode']
            print(f"      ✓ Thermo: {params['thermo_mode']}")
        
        # Check physics options
        for key in ['include_springs', 'include_dampers', 'include_pneumatics']:
            if key in preset:
                assert options[key] == preset[key]
        print(f"      ✓ Physics: {options}")
    
    print("\n✅ All presets applied correctly")
    return True


def test_panel_initialization():
    """Тест инициализации панели"""
    print("\n" + "="*60)
    print("TEST 4: Panel Initialization")
    print("="*60)
    
    panel = ModesPanel()
    
    # Check tabs exist
    assert panel.tabs.count() == 4
    print(f"✅ Panel has {panel.tabs.count()} tabs")
    
    # Check tab names
    expected_tabs = ["🎮 Управление", "⚙️ Режим", "🔧 Физика", "🛣️ Дорога"]
    for i, expected in enumerate(expected_tabs):
        actual = panel.tabs.tabText(i)
        assert expected in actual
        print(f"   Tab {i}: {actual}")
    
    # Check state manager
    assert panel.state_manager is not None
    print("✅ State manager created")
    
    # Check tab instances
    assert panel.control_tab is not None
    assert panel.simulation_tab is not None
    assert panel.physics_tab is not None
    assert panel.road_tab is not None
    print("✅ All tabs initialized")
    
    return True


def test_signal_connections():
    """Тест подключения сигналов"""
    print("\n" + "="*60)
    print("TEST 5: Signal Connections")
    print("="*60)
    
    panel = ModesPanel()
    signals_tested = []
    
    # Test simulation_control signal
    def on_sim_control(cmd):
        signals_tested.append(('simulation_control', cmd))
    
    panel.simulation_control.connect(on_sim_control)
    panel.control_tab.simulation_control.emit("start")
    assert ('simulation_control', 'start') in signals_tested
    print("✅ simulation_control signal works")
    
    # Test mode_changed signal
    def on_mode_changed(mode_type, mode):
        signals_tested.append(('mode_changed', mode_type, mode))
    
    panel.mode_changed.connect(on_mode_changed)
    panel.simulation_tab.mode_changed.emit('sim_type', 'DYNAMICS')
    assert ('mode_changed', 'sim_type', 'DYNAMICS') in signals_tested
    print("✅ mode_changed signal works")
    
    # Test parameter_changed signal
    def on_param_changed(name, value):
        signals_tested.append(('parameter_changed', name, value))
    
    panel.parameter_changed.connect(on_param_changed)
    panel.road_tab.parameter_changed.emit('amplitude', 0.08)
    assert ('parameter_changed', 'amplitude', 0.08) in signals_tested
    print("✅ parameter_changed signal works")
    
    # Test physics_options_changed signal
    def on_physics_changed(options):
        signals_tested.append(('physics_options_changed', options))
    
    panel.physics_options_changed.connect(on_physics_changed)
    test_options = {'include_springs': False}
    panel.physics_tab.physics_options_changed.emit(test_options)
    assert ('physics_options_changed', test_options) in signals_tested
    print("✅ physics_options_changed signal works")
    
    print(f"\n✅ All {len(signals_tested)} signals connected and working")
    return True


def test_api_compatibility():
    """Тест совместимости API с оригиналом"""
    print("\n" + "="*60)
    print("TEST 6: API Compatibility")
    print("="*60)
    
    panel = ModesPanel()
    
    # Test get_parameters
    params = panel.get_parameters()
    assert isinstance(params, dict)
    assert 'sim_type' in params
    assert 'amplitude' in params
    print("✅ get_parameters() returns dict")
    
    # Test get_physics_options
    options = panel.get_physics_options()
    assert isinstance(options, dict)
    assert 'include_springs' in options
    print("✅ get_physics_options() returns dict")
    
    # Test set_simulation_running
    panel.set_simulation_running(True)
    assert panel.control_tab._simulation_running == True
    print("✅ set_simulation_running(True) works")
    
    panel.set_simulation_running(False)
    assert panel.control_tab._simulation_running == False
    print("✅ set_simulation_running(False) works")
    
    # Test validate_state
    errors = panel.validate_state()
    assert isinstance(errors, list)
    print(f"✅ validate_state() returns list (errors: {len(errors)})")
    
    return True


def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*70)
    print("MODESPANEL REFACTORED - UNIT TESTS")
    print("="*70)
    
    tests = [
        ("StateManager Initialization", test_state_manager_initialization),
        ("Parameter Validation", test_parameter_validation),
        ("Preset Application", test_preset_application),
        ("Panel Initialization", test_panel_initialization),
        ("Signal Connections", test_signal_connections),
        ("API Compatibility", test_api_compatibility),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} FAILED with exception:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ ✅ ✅ ALL TESTS PASSED! ✅ ✅ ✅")
        print("\nModesPanel refactored version is fully functional!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
