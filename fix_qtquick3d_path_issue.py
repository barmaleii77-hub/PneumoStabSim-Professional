#!/usr/bin/env python3
"""
QtQuick3D Path Fix Tool
Diagnoses and fixes QtQuick3D plugin loading issues
"""

import os
import sys
import tempfile
from pathlib import Path


def check_qtquick3d_installation():
    """Check QtQuick3D installation and paths"""
    print("🔍 ДИАГНОСТИКА QTQUICK3D УСТАНОВКИ")
    print("=" * 50)

    try:
        from PySide6.QtCore import QLibraryInfo

        # Qt locations
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)

        print(f"📂 Qt QML path: {qml_path}")
        print(f"📂 Qt Plugins path: {plugins_path}")

        # Check QtQuick3D existence
        qtquick3d_path = Path(qml_path) / "QtQuick3D"
        print(f"📂 QtQuick3D path: {qtquick3d_path}")
        print(f"✅ QtQuick3D exists: {qtquick3d_path.exists()}")

        if qtquick3d_path.exists():
            # Check plugin file
            plugin_file = qtquick3d_path / "qquick3dplugin.dll"
            print(f"📦 Plugin file: {plugin_file}")
            print(f"✅ Plugin exists: {plugin_file.exists()}")

            # Check qmldir
            qmldir_file = qtquick3d_path / "qmldir"
            print(f"📄 qmldir file: {qmldir_file}")
            print(f"✅ qmldir exists: {qmldir_file.exists()}")

            if qmldir_file.exists():
                print("\n📋 СОДЕРЖИМОЕ qmldir:")
                print("-" * 30)
                with open(qmldir_file) as f:
                    content = f.read()
                    print(content)
                print("-" * 30)

        return qtquick3d_path.exists()

    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False


def test_qml_import():
    """Test QML import with proper environment"""
    print("\n🧪 ТЕСТ ИМПОРТА QML")
    print("=" * 50)

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtQuickWidgets import QQuickWidget
        from PySide6.QtCore import QUrl, QLibraryInfo

        # Set up environment
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)

        # CRITICAL: Set QML import path environment variable
        os.environ["QML2_IMPORT_PATH"] = str(qml_path)
        os.environ["QML_IMPORT_PATH"] = str(qml_path)

        print(f"🔧 Установлена переменная QML2_IMPORT_PATH: {qml_path}")
        print(f"🔧 Установлена переменная QML_IMPORT_PATH: {qml_path}")

        # Create minimal test app
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # Create test QML
        test_qml = """
import QtQuick
import QtQuick3D

Item {
    id: root

    Component.onCompleted: {
        console.log("✅ QtQuick3D imported successfully!")
    }

    Text {
        text: "QtQuick3D Import Test"
        color: "green"
    }
}
"""

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".qml", delete=False) as f:
            f.write(test_qml)
            temp_qml_path = f.name

        print(f"📄 Создан тестовый QML файл: {temp_qml_path}")

        # Try to load QML
        widget = QQuickWidget()

        # Set import paths programmatically
        engine = widget.engine()
        engine.addImportPath(str(qml_path))
        print(f"🔧 Добавлен import path в QML engine: {qml_path}")

        # Try to load
        widget.setSource(QUrl.fromLocalFile(temp_qml_path))

        status = widget.status()
        print(f"📊 QML статус загрузки: {status}")

        if status == QQuickWidget.Status.Error:
            errors = widget.errors()
            print("❌ ОШИБКИ QML:")
            for error in errors:
                print(f"  - {error}")

            # Clean up
            os.unlink(temp_qml_path)
            return False
        else:
            print("✅ QML загружен успешно!")
            # Clean up
            os.unlink(temp_qml_path)
            return True

    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback

        traceback.print_exc()
        return False


def fix_environment_variables():
    """Set up proper environment variables for QtQuick3D"""
    print("\n🔧 ИСПРАВЛЕНИЕ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("=" * 50)

    try:
        from PySide6.QtCore import QLibraryInfo

        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)

        # Set critical environment variables
        env_vars = {
            "QML2_IMPORT_PATH": str(qml_path),
            "QML_IMPORT_PATH": str(qml_path),
            "QT_PLUGIN_PATH": str(plugins_path),
            "QT_QML_IMPORT_PATH": str(qml_path),
        }

        print("🔧 Установка переменных окружения:")
        for var, value in env_vars.items():
            os.environ[var] = value
            print(f"  {var} = {value}")

        print("✅ Переменные окружения установлены")
        return True

    except Exception as e:
        print(f"❌ Ошибка установки переменных: {e}")
        return False


def create_fixed_app_launcher():
    """Create a launcher script with proper environment setup"""
    print("\n📝 СОЗДАНИЕ ИСПРАВЛЕННОГО ЛАУНЧЕРА")
    print("=" * 50)

    launcher_code = '''#!/usr/bin/env python3
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
'''

    launcher_path = Path("app_fixed_qtquick3d.py")

    try:
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)

        print(f"✅ Создан исправленный лаунчер: {launcher_path}")
        print("💡 Запускайте приложение через: python app_fixed_qtquick3d.py")
        return True

    except Exception as e:
        print(f"❌ Ошибка создания лаунчера: {e}")
        return False


def main():
    """Main diagnostic and fix routine"""
    print("🔧 QTQUICK3D PATH FIX TOOL")
    print("=" * 60)

    # Step 1: Check installation
    installation_ok = check_qtquick3d_installation()

    if not installation_ok:
        print("\n❌ QtQuick3D не установлен или поврежден!")
        print("💡 Попробуйте переустановить PySide6:")
        print("   pip uninstall PySide6")
        print("   pip install PySide6")
        return 1

    # Step 2: Fix environment
    env_ok = fix_environment_variables()

    # Step 3: Test import
    import_ok = test_qml_import()

    # Step 4: Create fixed launcher
    launcher_ok = create_fixed_app_launcher()

    print("\n📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ")
    print("=" * 50)
    print(f"✅ QtQuick3D установлен: {installation_ok}")
    print(f"✅ Переменные окружения: {env_ok}")
    print(f"✅ QML импорт работает: {import_ok}")
    print(f"✅ Лаунчер создан: {launcher_ok}")

    if all([installation_ok, env_ok, import_ok, launcher_ok]):
        print("\n🎉 ВСЕ ИСПРАВЛЕНО!")
        print("💡 Запустите: python app_fixed_qtquick3d.py")
        return 0
    else:
        print("\n⚠️ НЕКОТОРЫЕ ПРОБЛЕМЫ ОСТАЛИСЬ")
        print("💡 Попробуйте переустановить PySide6")
        return 1


if __name__ == "__main__":
    sys.exit(main())
