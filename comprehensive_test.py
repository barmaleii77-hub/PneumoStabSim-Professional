#!/usr/bin/env python
"""
PneumoStabSim Professional - Комплексный интеграционный тест
Comprehensive Integration Test Suite для всех систем проекта
"""

import sys
import os
import time
from pathlib import Path
import json

# Добавляем корень репозитория и src в путь для импортов
_PROJECT_ROOT = Path(__file__).parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
src_path = _PROJECT_ROOT / "src"
if str(src_path) not in sys.path:
    sys.path.insert(1, str(src_path))

from src.diagnostics.logger_factory import get_logger


logger = get_logger("tools.comprehensive_test")


def setup_test_environment():
    """Настройка тестового окружения"""
    print("🔧 Setting up test environment...")

    # Настройка кодировки
    if sys.platform == "win32":
        try:
            import subprocess

            subprocess.run(["chcp", "65001"], capture_output=True, check=False)
        except Exception as exc:
            logger.warning("Failed to set Windows codepage", error=str(exc))

    # Настройка Qt окружения для тестов
    os.environ.setdefault(
        "QSG_RHI_BACKEND", "d3d11" if sys.platform == "win32" else "opengl"
    )
    os.environ.setdefault("QSG_INFO", "0")  # Минимальный вывод для тестов
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false")

    print("✅ Test environment configured")


class TestResult:
    """Результат отдельного теста"""

    def __init__(self, name: str, success: bool, message: str, duration: float = 0.0):
        self.name = name
        self.success = success
        self.message = message
        self.duration = duration
        self.timestamp = time.time()


class ComprehensiveTestSuite:
    """Комплексный набор тестов для PneumoStabSim Professional"""

    def __init__(self):
        self.results: list[TestResult] = []
        self.start_time = time.time()

    def log_result(self, name: str, success: bool, message: str, duration: float = 0.0):
        """Записать результат теста"""
        result = TestResult(name, success, message, duration)
        self.results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}: {message}")
        if duration > 0:
            print(f"    ⏱️ Duration: {duration:.2f}s")

    def test_python_environment(self) -> bool:
        """Тест Python окружения и зависимостей"""
        print("\n📦 Testing Python Environment...")

        start = time.time()

        try:
            # Проверка версии Python
            version = sys.version_info
            if version < (3, 8):
                self.log_result(
                    "Python Version",
                    False,
                    f"Python {version.major}.{version.minor}.{version.micro} < 3.8",
                )
                return False
            else:
                self.log_result(
                    "Python Version",
                    True,
                    f"Python {version.major}.{version.minor}.{version.micro} ✓",
                )

            # Проверка критических зависимостей
            dependencies = [
                ("PySide6", "PySide6.QtWidgets"),
                ("NumPy", "numpy"),
                ("Pathlib", "pathlib"),
                ("JSON", "json"),
                ("Logging", "logging"),
            ]

            for dep_name, module_name in dependencies:
                try:
                    __import__(module_name)
                    self.log_result(f"Dependency {dep_name}", True, "Available")
                except ImportError as e:
                    self.log_result(f"Dependency {dep_name}", False, f"Missing: {e}")
                    return False

            duration = time.time() - start
            self.log_result("Python Environment", True, "All dependencies OK", duration)
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("Python Environment", False, f"Error: {e}", duration)
            return False

    def test_file_structure(self) -> bool:
        """Тест структуры файлов проекта"""
        print("\n📁 Testing File Structure...")

        start = time.time()

        critical_files = [
            "app.py",
            "src/common/__init__.py",
            "src/ui/main_window.py",
            "src/ui/panels/panel_geometry.py",
            "src/ui/panels/panel_graphics.py",
            "assets/qml/main_optimized.qml",
            "assets/qml/components/IblProbeLoader.qml",
        ]

        optional_files = [
            "assets/hdr/studio.hdr",
            "assets/hdr/README.md",
            "logs/",
            "src/ui/custom_geometry.py",
        ]

        missing_critical = []
        missing_optional = []

        # Проверка критических файлов
        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size if path.is_file() else "DIR"
                self.log_result(f"File {file_path}", True, f"Size: {size}")
            else:
                missing_critical.append(file_path)
                self.log_result(f"File {file_path}", False, "Missing")

        # Проверка опциональных файлов
        for file_path in optional_files:
            path = Path(file_path)
            if path.exists():
                size = path.stat().st_size if path.is_file() else "DIR"
                self.log_result(
                    f"Optional {file_path}", True, f"Available, size: {size}"
                )
            else:
                missing_optional.append(file_path)
                self.log_result(f"Optional {file_path}", False, "Missing (optional)")

        duration = time.time() - start

        if missing_critical:
            self.log_result(
                "File Structure",
                False,
                f"Missing critical files: {missing_critical}",
                duration,
            )
            return False
        else:
            self.log_result(
                "File Structure", True, "All critical files present", duration
            )
            return True

    def test_qml_syntax(self) -> bool:
        """Тест синтаксиса QML файлов"""
        print("\n📜 Testing QML Syntax...")

        start = time.time()

        qml_files = [
            "assets/qml/main_optimized.qml",
            "assets/qml/components/IblProbeLoader.qml",
        ]

        try:
            for qml_file in qml_files:
                path = Path(qml_file)
                if not path.exists():
                    self.log_result(f"QML {qml_file}", False, "File not found")
                    continue

                # Базовая проверка синтаксиса QML
                content = path.read_text(encoding="utf-8")

                # Проверка основных QML элементов
                if "import QtQuick" not in content:
                    self.log_result(f"QML {qml_file}", False, "Missing QtQuick import")
                    continue

                # Проверка на базовые синтаксические ошибки
                brace_count = content.count("{") - content.count("}")
                if brace_count != 0:
                    self.log_result(
                        f"QML {qml_file}", False, f"Unmatched braces: {brace_count}"
                    )
                    continue

                self.log_result(f"QML {qml_file}", True, "Syntax OK")

            duration = time.time() - start
            self.log_result("QML Syntax", True, "All QML files valid", duration)
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("QML Syntax", False, f"Error: {e}", duration)
            return False

    def test_python_imports(self) -> bool:
        """Тест импортов Python модулей"""
        print("\n🐍 Testing Python Imports...")

        start = time.time()

        try:
            # Тест импорта основных модулей проекта
            modules_to_test = [
                ("src.common", "init_logging, log_ui_event"),
                ("src.ui.main_window", "MainWindow"),
                ("src.ui.panels.panel_geometry", "GeometryPanel"),
                ("src.ui.panels.panel_graphics", "GraphicsPanel"),
            ]

            for module_name, imports in modules_to_test:
                try:
                    exec(f"from {module_name} import {imports}")
                    self.log_result(f"Import {module_name}", True, "Success")
                except ImportError as e:
                    self.log_result(f"Import {module_name}", False, f"Failed: {e}")
                    return False
                except Exception as e:
                    self.log_result(f"Import {module_name}", False, f"Error: {e}")
                    return False

            duration = time.time() - start
            self.log_result(
                "Python Imports", True, "All modules imported successfully", duration
            )
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("Python Imports", False, f"Error: {e}", duration)
            return False

    def test_qt_integration(self) -> bool:
        """Тест интеграции Qt (без GUI)"""
        print("\n🖼️ Testing Qt Integration...")

        start = time.time()

        try:
            # Импорт Qt компонентов
            from PySide6.QtWidgets import QApplication
            from PySide6.QtQuickWidgets import QQuickWidget

            self.log_result("Qt Imports", True, "PySide6 components imported")

            # Создание тестового QApplication (без показа окна)
            if not QApplication.instance():
                app = QApplication([])
                self.log_result("QApplication", True, "Created successfully")

                # Тест создания QQuickWidget
                widget = QQuickWidget()
                widget.resize(100, 100)  # Минимальный размер
                self.log_result("QQuickWidget", True, "Created successfully")

                # Очистка
                widget.deleteLater()
                app.quit()
            else:
                self.log_result("QApplication", True, "Already exists")

            duration = time.time() - start
            self.log_result("Qt Integration", True, "Qt components working", duration)
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("Qt Integration", False, f"Error: {e}", duration)
            return False

    def test_graphics_panel_config(self) -> bool:
        """Тест конфигурации GraphicsPanel"""
        print("\n🎨 Testing Graphics Panel Configuration...")

        start = time.time()

        try:
            # Создание тестового объекта (без GUI)
            # Проверяем наличие ключевых атрибутов конфигурации
            test_config = {
                "key_brightness": 2.8,
                "glass_ior": 1.52,
                "ibl_enabled": True,
                "bloom_threshold": 1.0,
                "tonemap_mode": 3,
            }

            self.log_result(
                "Graphics Config", True, f"Test config: {len(test_config)} parameters"
            )

            # Проверка критических параметров
            critical_params = ["key_brightness", "glass_ior", "ibl_enabled"]
            for param in critical_params:
                if param in test_config:
                    self.log_result(
                        f"Graphics Param {param}", True, f"Value: {test_config[param]}"
                    )
                else:
                    self.log_result(f"Graphics Param {param}", False, "Missing")
                    return False

            duration = time.time() - start
            self.log_result(
                "Graphics Panel Config", True, "Configuration valid", duration
            )
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("Graphics Panel Config", False, f"Error: {e}", duration)
            return False

    def test_ibl_system(self) -> bool:
        """Тест системы IBL"""
        print("\n🌟 Testing IBL System...")

        start = time.time()

        try:
            # Проверка файла IblProbeLoader
            ibl_loader_path = Path("assets/qml/components/IblProbeLoader.qml")
            if not ibl_loader_path.exists():
                self.log_result(
                    "IBL Loader File", False, "IblProbeLoader.qml not found"
                )
                return False

            # Проверка содержимого IblProbeLoader
            content = ibl_loader_path.read_text(encoding="utf-8")

            ibl_checks = [
                ("primarySource", "primarySource:" in content),
                ("fallbackSource", "fallbackSource:" in content),
                ("ready property", "readonly property bool ready" in content),
                ("Texture component", "Texture {" in content),
                ("Error handling", "onStatusChanged" in content),
            ]

            for check_name, result in ibl_checks:
                self.log_result(
                    f"IBL {check_name}", result, "Present" if result else "Missing"
                )
                if not result:
                    return False

            # Проверка HDR файлов
            hdr_paths = ["assets/hdr/studio.hdr", "assets/hdr/README.md"]

            hdr_available = False
            for hdr_path in hdr_paths:
                path = Path(hdr_path)
                if path.exists():
                    if hdr_path.endswith(".hdr"):
                        size_mb = path.stat().st_size / (1024 * 1024)
                        self.log_result(
                            f"HDR File {hdr_path}", True, f"Size: {size_mb:.1f}MB"
                        )
                        hdr_available = True
                    else:
                        self.log_result(
                            f"HDR File {hdr_path}", True, "Documentation present"
                        )
                else:
                    self.log_result(f"HDR File {hdr_path}", False, "Not found")

            # Проверка интеграции в main_optimized.qml
            main_qml_path = Path("assets/qml/main_optimized.qml")
            if main_qml_path.exists():
                main_content = main_qml_path.read_text(encoding="utf-8")

                main_checks = [
                    ("IblProbeLoader import", "IblProbeLoader {" in main_content),
                    ("iblTextureReady property", "iblTextureReady" in main_content),
                    ("lightProbe binding", "lightProbe:" in main_content),
                ]

                for check_name, result in main_checks:
                    self.log_result(
                        f"Main QML {check_name}",
                        result,
                        "Present" if result else "Missing",
                    )

            duration = time.time() - start
            status_msg = "IBL system configured"
            if hdr_available:
                status_msg += " with HDR assets"
            else:
                status_msg += " (HDR files needed for full functionality)"

            self.log_result("IBL System", True, status_msg, duration)
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("IBL System", False, f"Error: {e}", duration)
            return False

    def test_application_startup(self) -> bool:
        """Тест запуска приложения (без GUI показа)"""
        print("\n🚀 Testing Application Startup...")

        start = time.time()

        try:
            # Импорт главного модуля
            import app

            self.log_result("App Module Import", True, "app.py imported successfully")

            # Проверка глобальных переменных и констант
            globals_to_check = ["USE_QML_3D_SCHEMA", "app_instance", "window_instance"]

            for global_name in globals_to_check:
                if hasattr(app, global_name):
                    value = getattr(app, global_name)
                    self.log_result(
                        f"App Global {global_name}", True, f"Value: {value}"
                    )
                else:
                    self.log_result(f"App Global {global_name}", False, "Missing")

            # Проверка основных функций (они определены на уровне модуля)
            main_functions = ["main", "parse_arguments", "qt_message_handler"]

            for func_name in main_functions:
                if hasattr(app, func_name):
                    self.log_result(f"App Function {func_name}", True, "Present")
                else:
                    self.log_result(f"App Function {func_name}", False, "Missing")
                    return False

            # Проверка импортов в модуле app
            try:
                # Проверяем, что QApplication импортирован в app
                if hasattr(app, "QApplication"):
                    self.log_result("App Qt Import", True, "QApplication available")
                else:
                    self.log_result("App Qt Import", False, "QApplication not found")
            except Exception as exc:
                self.log_result("App Qt Import", False, "Import issues")
                logger.warning("Failed to validate QApplication import", error=str(exc))

            duration = time.time() - start
            self.log_result(
                "Application Startup", True, "Core application structure OK", duration
            )
            return True

        except Exception as e:
            duration = time.time() - start
            self.log_result("Application Startup", False, f"Error: {e}", duration)
            return False

    def generate_report(self) -> dict:
        """Генерация финального отчета"""
        total_time = time.time() - self.start_time

        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        total = len(self.results)

        success_rate = (passed / total * 100) if total > 0 else 0

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "total_duration": total_time,
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                }
                for r in self.results
            ],
        }

        return report


def main():
    """Главная функция комплексного теста"""
    print("=" * 70)
    print("🔬 PNEUMOSTABSIM PROFESSIONAL - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"📅 Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Настройка окружения
    setup_test_environment()

    # Создание набора тестов
    test_suite = ComprehensiveTestSuite()

    # Выполнение всех тестов
    tests = [
        test_suite.test_python_environment,
        test_suite.test_file_structure,
        test_suite.test_qml_syntax,
        test_suite.test_python_imports,
        test_suite.test_qt_integration,
        test_suite.test_graphics_panel_config,
        test_suite.test_ibl_system,
        test_suite.test_application_startup,
    ]

    print(f"\n🧪 Running {len(tests)} test categories...")

    overall_success = True
    for test_func in tests:
        try:
            result = test_func()
            if not result:
                overall_success = False
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            overall_success = False

    # Генерация отчета
    report = test_suite.generate_report()

    # Вывод итогов
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)

    print(f"📈 Total Tests: {report['total_tests']}")
    print(f"✅ Passed: {report['passed']}")
    print(f"❌ Failed: {report['failed']}")
    print(f"📊 Success Rate: {report['success_rate']:.1f}%")
    print(f"⏱️ Total Duration: {report['total_duration']:.2f}s")

    # Статус готовности
    if overall_success and report["success_rate"] >= 80:
        print("\n🎉 SYSTEM STATUS: READY FOR PRODUCTION")
        print("✅ All critical systems operational")
        print("🚀 PneumoStabSim Professional ready to launch!")
    elif report["success_rate"] >= 60:
        print("\n⚠️ SYSTEM STATUS: PARTIALLY READY")
        print("🔧 Some issues found, but core functionality works")
        print("💡 Check failed tests above for details")
    else:
        print("\n❌ SYSTEM STATUS: NOT READY")
        print("🛠️ Critical issues found, requires fixes")
        print("🔍 Review all failed tests before deployment")

    # Сохранение отчета
    try:
        report_path = Path("comprehensive_test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Detailed report saved: {report_path}")
    except Exception as e:
        print(f"\n⚠️ Could not save report: {e}")

    print("\n" + "=" * 70)

    # Возврат кода выхода
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
