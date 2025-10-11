#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PneumoStabSim - Fixed QtQuick3D Launcher
This launcher properly sets up QtQuick3D environment before starting the app
"""

import os
import sys
from pathlib import Path

def setup_qtquick3d_environment():
    """Set up QtQuick3D environment variables before importing Qt"""
    try:
        # Import Qt after environment setup
        from PySide6.QtCore import QLibraryInfo
        
        # Get Qt paths
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        
        # Set critical environment variables
        os.environ["QML2_IMPORT_PATH"] = str(qml_path)
        os.environ["QML_IMPORT_PATH"] = str(qml_path)
        os.environ["QT_PLUGIN_PATH"] = str(plugins_path)
        os.environ["QT_QML_IMPORT_PATH"] = str(qml_path)
        
        print(f"✅ QtQuick3D environment configured:")
        print(f"   QML2_IMPORT_PATH = {qml_path}")
        print(f"   QT_PLUGIN_PATH = {plugins_path}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to setup QtQuick3D environment: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PneumoStabSim - QtQuick3D Fixed Launcher")
    print("=" * 50)
    
    # Setup environment BEFORE importing app
    if setup_qtquick3d_environment():
        print("✅ Environment configured, starting app...")
        
        # Now import and run the app
        try:
            from app import main
            sys.exit(main())
        except Exception as e:
            print(f"❌ App failed to start: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("❌ Failed to configure environment")
        sys.exit(1)
