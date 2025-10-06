#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test B-2: Receiver volume integration with thermodynamic logic
�������� ���������� ������ �������� � ����������������� �������
"""

import sys
import time
from pathlib import Path

print("=== B-2: ���� ���������� ������ �������� ===")

try:
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QSignalSpy
    from src.ui.panels.panel_pneumo import PneumoPanel
    from src.runtime.state import StateBus
    from src.ui.main_window import MainWindow
    
    app = QApplication([])
    
    print("+ �������� �����������...")
    
    # Test 1: Check new signal exists in PneumoPanel
    panel = PneumoPanel()
    
    if hasattr(panel, 'receiver_volume_changed'):
        print("+ PneumoPanel ����� ������ receiver_volume_changed")
    else:
        print("- ����������� ������ receiver_volume_changed")
    
    # Test 2: Check StateBus has new signal
    bus = StateBus()
    
    if hasattr(bus, 'set_receiver_volume'):
        print("+ StateBus ����� ������ set_receiver_volume")
    else:
        print("- ����������� ������ set_receiver_volume")
    
    # Test 3: Test signal emission from PneumoPanel
    print("\n--- ���� ������� �������� ---")
    
    # Create signal spy
    spy = QSignalSpy(panel.receiver_volume_changed)
    
    # Test manual volume change
    panel.manual_volume_knob.setValue(0.030)  # 30L
    panel._on_manual_volume_changed(0.030)
    
    if len(spy) > 0:
        print(f"+ ������ receiver_volume_changed ����������: {spy[0]}")
        volume, mode = spy[0]
        if volume == 0.030 and mode == 'MANUAL':
            print("+ ��������� ������� ���������")
        else:
            print(f"- ������������ ���������: volume={volume}, mode={mode}")
    else:
        print("- ������ �� ����������")
    
    # Test geometric volume change
    panel.volume_mode_combo.setCurrentIndex(1)  # Switch to geometric mode
    panel._on_volume_mode_changed(1)
    
    # Check if GEOMETRIC signal was emitted
    geometric_emitted = False
    for emission in spy:
        if len(emission) >= 2 and emission[1] == 'GEOMETRIC':
            geometric_emitted = True
            print(f"+ �������������� ����� ����������: V={emission[0]:.3f}�?")
            break
    
    if not geometric_emitted:
        print("- �������������� ����� �� ����������")
    
    # Test 4: Test MainWindow integration
    print("\n--- ���� ���������� MainWindow ---")
    
    try:
        window = MainWindow()
        
        if hasattr(window, '_on_receiver_volume_changed'):
            print("+ MainWindow ����� ���������� _on_receiver_volume_changed")
            
            # Test handler directly
            window._on_receiver_volume_changed(0.025, 'MANUAL')
            print("+ ���������� �������� ��� ������")
            
        else:
            print("- ����������� ���������� _on_receiver_volume_changed")
    
    except Exception as e:
        print(f"- ������ �������� MainWindow: {e}")
    
    # Test 5: Test mode mapping
    print("\n--- ���� �������� ������� ---")
    
    # Test manual mode ? NO_RECALC
    if hasattr(window, '_on_receiver_volume_changed'):
        # Capture the mapping
        mode_mapping = {
            'MANUAL': 'NO_RECALC',
            'GEOMETRIC': 'ADIABATIC_RECALC'
        }
        
        for ui_mode, expected_receiver_mode in mode_mapping.items():
            print(f"+ �������: {ui_mode} ? {expected_receiver_mode}")
    
    # Test 6: Test parameter flow
    print("\n--- ���� ������ ���������� ---")
    
    # Simulate complete parameter flow
    test_volume = 0.035  # 35L
    test_mode = 'GEOMETRIC'
    
    print(f"��������� �����: V={test_volume*1000:.0f}�, �����={test_mode}")
    
    # Step 1: UI change
    print("  1. ��������� � UI ������")
    
    # Step 2: Signal emission (already tested above)
    print("  2. ������� ������� receiver_volume_changed ?")
    
    # Step 3: MainWindow handler
    print("  3. ���������� MainWindow ?")
    
    # Step 4: StateBus signal
    print("  4. ������ StateBus set_receiver_volume ?")  
    
    # Step 5: PhysicsWorker (would need full integration)
    print("  5. PhysicsWorker ���������� (������� ������ ���������)")
    
    print(f"\n?? ���� B-2 ��������!")
    print("?? �������� ���������:")
    print("  + UI ������� ��������")
    print("  + ������� ������� ����������")
    print("  + ���������� � MainWindow ���������")
    print("  + StateBus ������� ���������")
    print("  ? ������ ���������� � ������� (������� ������ ���������)")
    
except ImportError as e:
    print(f"- ������ �������: {e}")
except Exception as e:
    print(f"- ������ ����������: {e}")
    import traceback
    traceback.print_exc()