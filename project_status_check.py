#!/usr/bin/env python3
"""
Project Status Check - проверка состояния проекта PneumoStabSim
"""

import sys

def check_project_status():
    print('=== PROJECT STATUS CHECK ===')
    print(f'Python version: {sys.version}')
    print()
    
    # Test imports
    dependencies_ok = True
    
    try:
        import numpy as np
        print('✅ NumPy:', np.__version__)
    except ImportError as e:
        print('❌ NumPy import failed:', e)
        dependencies_ok = False
    
    try:
        import scipy
        print('✅ SciPy:', scipy.__version__)
    except ImportError as e:
        print('❌ SciPy import failed:', e)
        dependencies_ok = False
    
    try:
        import PySide6
        from PySide6.QtCore import qVersion
        print('✅ PySide6:', qVersion())
    except ImportError as e:
        print('❌ PySide6 import failed:', e)
        dependencies_ok = False
    
    try:
        import matplotlib
        print('✅ Matplotlib:', matplotlib.__version__)
    except ImportError as e:
        print('❌ Matplotlib import failed:', e)
        dependencies_ok = False
    
    print()
    print('=== MAIN APPLICATION COMPONENTS ===')
    
    # Test main application components
    app_components_ok = True
    
    try:
        from src.ui.main_window import MainWindow
        print('✅ MainWindow imported')
    except ImportError as e:
        print('❌ MainWindow import failed:', e)
        app_components_ok = False
    
    try:
        from src.ui.custom_geometry import SphereGeometry, CubeGeometry
        print('✅ Custom geometry imported')
    except ImportError as e:
        print('❌ Custom geometry import failed:', e)
        app_components_ok = False
    
    try:
        from src.runtime.sim_loop import SimulationManager, PhysicsWorker
        print('✅ SimulationManager and PhysicsWorker imported')
    except ImportError as e:
        print('❌ SimulationManager/PhysicsWorker import failed:', e)
        app_components_ok = False
    
    try:
        from src.pneumo.system import PneumaticSystem
        print('✅ PneumaticSystem imported')
    except ImportError as e:
        print('❌ PneumaticSystem import failed:', e)
        app_components_ok = False
    
    try:
        from src.ui.panels.panel_geometry import GeometryPanel
        print('✅ GeometryPanel imported')
    except ImportError as e:
        print('❌ GeometryPanel import failed:', e)
        app_components_ok = False
    
    try:
        from src.ui.panels.panel_pneumo import PneumoPanel
        print('✅ PneumoPanel imported')
    except ImportError as e:
        print('❌ PneumoPanel import failed:', e)
        app_components_ok = False
    
    try:
        from src.physics.odes import RigidBody3DOF, create_initial_conditions
        print('✅ Physics ODE components imported')
    except ImportError as e:
        print('❌ Physics ODE components import failed:', e)
        app_components_ok = False
    
    try:
        from src.physics.integrator import step_dynamics, PhysicsLoopConfig
        print('✅ Physics integrator imported')
    except ImportError as e:
        print('❌ Physics integrator import failed:', e)
        app_components_ok = False
    
    print()
    print('=== QML AND ASSETS ===')
    
    qml_assets_ok = True
    
    try:
        import os
        main_qml = "assets/qml/main.qml"
        if os.path.exists(main_qml):
            print(f'✅ Main QML file exists: {main_qml}')
        else:
            print(f'❌ Main QML file missing: {main_qml}')
            qml_assets_ok = False
    except Exception as e:
        print(f'❌ QML check failed: {e}')
        qml_assets_ok = False
    
    print()
    print('=== SUMMARY ===')
    
    if dependencies_ok:
        print('✅ All dependencies installed correctly')
    else:
        print('❌ Some dependencies missing - run: pip install -r requirements.txt')
    
    if app_components_ok:
        print('✅ All main application components available')
    else:
        print('❌ Some application components missing')
    
    if qml_assets_ok:
        print('✅ QML assets available')
    else:
        print('❌ QML assets missing')
    
    if dependencies_ok and app_components_ok and qml_assets_ok:
        print()
        print('🎉 PROJECT STATUS: READY TO RUN')
        print('   Try: python app.py')
        print('   Or:  python launch.py')
        return True
    else:
        print()
        print('⚠️  PROJECT STATUS: NEEDS ATTENTION')
        return False

if __name__ == "__main__":
    check_project_status()
