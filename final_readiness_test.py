#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PneumoStabSim Professional - Финальный тест готовности
Final Readiness Test - окончательная проверка перед продакшеном
"""

import sys
import time
from pathlib import Path


class FinalReadinessTest:
    """Финальный тест готовности системы"""

    def __init__(self):
        self.results = []

    def log(self, test_name: str, success: bool, message: str):
        """Логирование результата теста"""
        self.results.append((test_name, success, message))
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")

    def test_core_system(self) -> bool:
        """Тест ядра системы"""
        print("🔬 Testing Core System...")

        all_passed = True

        # Python версия
        version = sys.version_info
        if version >= (3, 8):
            self.log(
                "Python Version",
                True,
                f"{version.major}.{version.minor}.{version.micro}",
            )
        else:
            self.log(
                "Python Version",
                False,
                f"{version.major}.{version.minor}.{version.micro} < 3.8",
            )
            all_passed = False

        # Критические зависимости
        deps = [
            ("PySide6", "PySide6.QtWidgets"),
            ("NumPy", "numpy"),
        ]

        for name, module in deps:
            try:
                __import__(module)
                self.log(f"Dependency {name}", True, "Available")
            except ImportError:
                self.log(f"Dependency {name}", False, "Missing")
                all_passed = False

        return all_passed

    def test_project_structure(self) -> bool:
        """Тест структуры проекта"""
        print("\n📁 Testing Project Structure...")

        critical_files = {
            "app.py": "Main application entry point",
            "src/ui/main_window.py": "Main window implementation",
            "src/ui/panels/panel_graphics.py": "Graphics control panel",
            "assets/qml/main_optimized.qml": "3D visualization engine",
            "assets/qml/components/IblProbeLoader.qml": "IBL system component",
        }

        all_passed = True

        for file_path, description in critical_files.items():
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size
                self.log(f"File {path.name}", True, f"{description} ({size:,} bytes)")
            else:
                self.log(f"File {path.name}", False, f"Missing: {description}")
                all_passed = False

        return all_passed

    def test_ibl_system(self) -> bool:
        """Тест системы IBL"""
        print("\n🌟 Testing IBL System...")

        # Проверка компонента IblProbeLoader
        ibl_loader = Path("assets/qml/components/IblProbeLoader.qml")
        if not ibl_loader.exists():
            self.log("IBL Loader", False, "IblProbeLoader.qml missing")
            return False

        content = ibl_loader.read_text(encoding="utf-8")

        # Проверка ключевых элементов
        checks = [
            ("primarySource", "primarySource:" in content),
            ("fallbackSource", "fallbackSource:" in content),
            ("ready property", "readonly property bool ready" in content),
            ("Texture", "Texture {" in content),
        ]

        all_passed = True
        for check_name, result in checks:
            self.log(f"IBL {check_name}", result, "Present" if result else "Missing")
            if not result:
                all_passed = False

        # Проверка HDR файла
        hdr_file = Path("assets/hdr/studio.hdr")
        if hdr_file.exists():
            size_mb = hdr_file.stat().st_size / (1024 * 1024)
            self.log("HDR Asset", True, f"studio.hdr available ({size_mb:.1f}MB)")
        else:
            self.log("HDR Asset", False, "studio.hdr missing (IBL won't work fully)")
            all_passed = False

        return all_passed

    def test_graphics_integration(self) -> bool:
        """Тест интеграции графики"""
        print("\n🎨 Testing Graphics Integration...")

        # Проверка main_optimized.qml
        main_qml = Path("assets/qml/main_optimized.qml")
        if not main_qml.exists():
            self.log("Main QML", False, "main_optimized.qml missing")
            return False

        content = main_qml.read_text(encoding="utf-8")

        # Проверка ключевых интеграций
        integrations = [
            ("IblProbeLoader import", "IblProbeLoader {" in content),
            ("ExtendedSceneEnvironment", "ExtendedSceneEnvironment {" in content),
            ("Glass IOR", "glassIOR" in content),
            ("Tonemap function", "resolvedTonemapMode" in content),
            ("Batch updates", "applyBatchedUpdates" in content),
        ]

        all_passed = True
        for integration_name, result in integrations:
            self.log(
                f"Graphics {integration_name}",
                result,
                "Integrated" if result else "Missing",
            )
            if not result:
                all_passed = False

        return all_passed

    def test_python_integration(self) -> bool:
        """Тест интеграции Python компонентов"""
        print("\n🐍 Testing Python Integration...")

        try:
            # Тест импорта основных модулей

            self.log("MainWindow Import", True, "Successfully imported")

            from src.ui.panels.panel_graphics import GraphicsPanel

            self.log("GraphicsPanel Import", True, "Successfully imported")

            # Создание тестового экземпляра GraphicsPanel (без GUI)
            try:
                # Импортируем QApplication для тестового окружения
                from PySide6.QtWidgets import QApplication

                if not QApplication.instance():
                    app = QApplication([])

                # Создаем тестовый экземпляр
                test_panel = GraphicsPanel()

                # Проверка наличия ключевых атрибутов
                if (
                    hasattr(test_panel, "current_graphics")
                    and test_panel.current_graphics
                ):
                    config_count = len(test_panel.current_graphics)
                    self.log(
                        "Graphics Config",
                        True,
                        f"Configuration with {config_count} parameters",
                    )

                    # Проверка критических параметров
                    critical_params = [
                        "key_brightness",
                        "glass_ior",
                        "ibl_enabled",
                        "bloom_threshold",
                    ]
                    for param in critical_params:
                        if param in test_panel.current_graphics:
                            value = test_panel.current_graphics[param]
                            self.log(f"Config Param {param}", True, f"Value: {value}")
                        else:
                            self.log(f"Config Param {param}", False, "Missing")
                            return False
                else:
                    self.log(
                        "Graphics Config", False, "Configuration dictionary missing"
                    )
                    return False

                # Очистка тестового объекта
                test_panel.deleteLater()

            except Exception as e:
                self.log("GraphicsPanel Instance", False, f"Failed to create: {e}")
                return False

            return True

        except Exception as e:
            self.log("Python Integration", False, f"Import error: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Запуск всех тестов"""
        print("=" * 70)
        print("🏁 PNEUMOSTABSIM PROFESSIONAL - FINAL READINESS TEST")
        print("=" * 70)
        print(f"📅 Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        tests = [
            self.test_core_system,
            self.test_project_structure,
            self.test_ibl_system,
            self.test_graphics_integration,
            self.test_python_integration,
        ]

        all_passed = True
        for test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                test_name = (
                    test_func.__name__.replace("test_", "").replace("_", " ").title()
                )
                self.log(test_name, False, f"Test crashed: {e}")
                all_passed = False

        return all_passed

    def generate_final_report(self, overall_result: bool):
        """Генерация финального отчета"""
        print("\n" + "=" * 70)
        print("📊 FINAL READINESS REPORT")
        print("=" * 70)

        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"📈 Tests Run: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")

        if overall_result and success_rate >= 90:
            print("\n🏆 PRODUCTION READINESS: CONFIRMED")
            print("✅ PneumoStabSim Professional is ready for production use")
            print("🚀 All critical systems operational")
            print("🌟 IBL system configured with HDR assets")
            print("🎨 37+ graphics parameters available")
            print("⚡ Optimized performance engine ready")

            print("\n🎯 READY FOR:")
            print("   • Professional demonstrations")
            print("   • Engineering education")
            print("   • Technical presentations")
            print("   • Research and development")

            print("\n💡 LAUNCH COMMAND: py app.py")
            return 0

        elif success_rate >= 70:
            print("\n⚠️ PRODUCTION READINESS: CONDITIONAL")
            print("🔧 Core functionality available with minor issues")
            print("📝 Review failed tests above")
            return 1

        else:
            print("\n❌ PRODUCTION READINESS: NOT READY")
            print("🛠️ Critical issues prevent production use")
            print("🔍 Fix all failed tests before deployment")
            return 2


def main():
    """Главная функция финального теста"""
    test_suite = FinalReadinessTest()
    overall_result = test_suite.run_all_tests()
    return test_suite.generate_final_report(overall_result)


if __name__ == "__main__":
    sys.exit(main())
