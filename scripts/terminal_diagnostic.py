#!/usr/bin/env python3
"""
Terminal and Encoding Diagnostic Tool
Comprehensive check for terminal capabilities, encoding support, and compatibility
"""

import sys
import os
import locale
import platform
import subprocess
from pathlib import Path


class TerminalDiagnostic:
    def __init__(self):
        self.results = []
        self.warnings = []
        self.errors = []

    def log_result(self, category, status, message):
        """Log diagnostic result"""
        symbol = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
        result_line = f"{symbol} [{category}] {message}"
        print(result_line)

        self.results.append(
            {"category": category, "status": status, "message": message}
        )

        if status == "WARNING":
            self.warnings.append(message)
        elif status == "ERROR":
            self.errors.append(message)

    def test_python_version(self):
        """Test Python version compatibility"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version < (3, 8):
            self.log_result(
                "PYTHON", "ERROR", f"Version {version_str} too old (need 3.8+)"
            )
            return False
        elif version >= (3, 12):
            self.log_result(
                "PYTHON",
                "WARNING",
                f"Version {version_str} very new (recommend 3.8-3.11)",
            )
            return True
        else:
            self.log_result("PYTHON", "OK", f"Version {version_str} compatible")
            return True

    def test_encoding_support(self):
        """Test encoding and Unicode support"""
        try:
            # Test default encoding
            default_encoding = sys.getdefaultencoding()
            if default_encoding.lower() in ["utf-8", "utf8"]:
                self.log_result(
                    "ENCODING", "OK", f"Default encoding: {default_encoding}"
                )
            else:
                self.log_result(
                    "ENCODING",
                    "WARNING",
                    f"Default encoding: {default_encoding} (not UTF-8)",
                )

            # Test locale encoding
            try:
                locale_encoding = locale.getpreferredencoding()
                if "utf" in locale_encoding.lower():
                    self.log_result(
                        "LOCALE", "OK", f"Locale encoding: {locale_encoding}"
                    )
                else:
                    self.log_result(
                        "LOCALE",
                        "WARNING",
                        f"Locale encoding: {locale_encoding} (not UTF-8)",
                    )
            except Exception as e:
                self.log_result(
                    "LOCALE", "ERROR", f"Cannot detect locale encoding: {e}"
                )

            # Test Unicode output
            try:
                test_unicode = "🔧 Testing Unicode: ✅ ❌ ⚠️ 🎯 📊 русский текст"
                print(test_unicode)
                self.log_result("UNICODE", "OK", "Unicode output test passed")
                return True
            except UnicodeEncodeError as e:
                self.log_result("UNICODE", "ERROR", f"Unicode output failed: {e}")
                return False

        except Exception as e:
            self.log_result("ENCODING", "ERROR", f"Encoding test failed: {e}")
            return False

    def test_terminal_capabilities(self):
        """Test terminal capabilities"""
        try:
            # Check if running in terminal
            if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
                self.log_result("TERMINAL", "OK", "Running in interactive terminal")
            else:
                self.log_result(
                    "TERMINAL", "WARNING", "Not running in interactive terminal"
                )

            # Test terminal encoding on Windows
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["chcp"], capture_output=True, text=True, shell=True
                    )
                    if result.returncode == 0:
                        codepage = result.stdout.strip()
                        if "65001" in codepage:
                            self.log_result(
                                "CODEPAGE", "OK", "Windows codepage: UTF-8 (65001)"
                            )
                        else:
                            self.log_result(
                                "CODEPAGE",
                                "WARNING",
                                f"Windows codepage: {codepage} (not UTF-8)",
                            )
                    else:
                        self.log_result(
                            "CODEPAGE", "WARNING", "Cannot detect Windows codepage"
                        )
                except Exception as e:
                    self.log_result(
                        "CODEPAGE", "WARNING", f"Codepage detection failed: {e}"
                    )

            # Test ANSI color support
            try:
                # Try to print ANSI colors
                ansi_test = (
                    "\033[31mRed\033[0m \033[32mGreen\033[0m \033[34mBlue\033[0m"
                )
                if os.getenv("TERM"):
                    self.log_result(
                        "ANSI", "OK", f"TERM environment variable: {os.getenv('TERM')}"
                    )
                else:
                    self.log_result(
                        "ANSI", "WARNING", "TERM environment variable not set"
                    )

            except Exception as e:
                self.log_result("ANSI", "WARNING", f"ANSI color test failed: {e}")

        except Exception as e:
            self.log_result(
                "TERMINAL", "ERROR", f"Terminal capability test failed: {e}"
            )

    def test_environment_variables(self):
        """Test Python and Qt environment variables"""
        env_vars = {
            "PYTHONIOENCODING": "Python I/O encoding",
            "PYTHONUTF8": "Python UTF-8 mode",
            "PYTHONLEGACYWINDOWSFSENCODING": "Windows filesystem encoding",
            "QSG_RHI_BACKEND": "Qt Scene Graph backend",
            "QT_LOGGING_RULES": "Qt logging configuration",
            "PYTHONPATH": "Python module search path",
        }

        for var, description in env_vars.items():
            value = os.environ.get(var)
            if value:
                self.log_result("ENV", "OK", f"{var}={value}")
            else:
                if var in ["PYTHONIOENCODING", "PYTHONUTF8"]:
                    self.log_result("ENV", "WARNING", f"{var} not set ({description})")
                else:
                    self.log_result("ENV", "INFO", f"{var} not set ({description})")

    def test_qt_imports(self):
        """Test Qt framework imports"""
        try:
            import PySide6

            version = getattr(PySide6, "__version__", "unknown")
            self.log_result("QT", "OK", f"PySide6 {version} available")

            # Test specific Qt modules
            try:
                from PySide6.QtWidgets import QApplication
                from PySide6.QtCore import QTimer
                from PySide6.QtQml import qmlRegisterType

                self.log_result("QT_MODULES", "OK", "Essential Qt modules available")
                return True
            except ImportError as e:
                self.log_result("QT_MODULES", "ERROR", f"Qt module import failed: {e}")
                return False

        except ImportError:
            # Try PyQt6 as fallback
            try:
                import PyQt6

                version = getattr(PyQt6, "__version__", "unknown")
                self.log_result(
                    "QT", "WARNING", f"PySide6 not available, PyQt6 {version} found"
                )
                return True
            except ImportError:
                self.log_result(
                    "QT", "ERROR", "No Qt framework available (PySide6 or PyQt6)"
                )
                return False

    def test_project_structure(self):
        """Test project file structure"""
        required_files = [
            "app.py",
            "requirements.txt",
            "src/",
            "venv/" if Path("venv").exists() else None,
        ]

        for file_path in required_files:
            if file_path is None:
                continue

            if Path(file_path).exists():
                if file_path.endswith("/"):
                    self.log_result("PROJECT", "OK", f"Directory {file_path} exists")
                else:
                    self.log_result("PROJECT", "OK", f"File {file_path} exists")
            else:
                self.log_result("PROJECT", "WARNING", f"Missing: {file_path}")

    def generate_fixes(self):
        """Generate fix recommendations"""
        fixes = []

        if any("not UTF-8" in warning for warning in self.warnings):
            fixes.append("Run fix_terminal.bat to configure UTF-8 encoding")

        if any("Version" in error and "too old" in error for error in self.errors):
            fixes.append("Upgrade Python to version 3.8 or newer")

        if any("Qt" in error for error in self.errors):
            fixes.append("Install Qt framework: pip install PySide6")

        if any("Unicode" in error for error in self.errors):
            fixes.append(
                "Set environment variables: PYTHONIOENCODING=utf-8 PYTHONUTF8=1"
            )

        return fixes

    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        print("=" * 70)
        print("🔍 PneumoStabSim - Terminal & Encoding Diagnostic")
        print("=" * 70)
        print()

        print("🐍 Python Environment:")
        python_ok = self.test_python_version()
        print()

        print("📝 Encoding Support:")
        encoding_ok = self.test_encoding_support()
        print()

        print("💻 Terminal Capabilities:")
        self.test_terminal_capabilities()
        print()

        print("🌍 Environment Variables:")
        self.test_environment_variables()
        print()

        print("🖼️ Qt Framework:")
        qt_ok = self.test_qt_imports()
        print()

        print("📁 Project Structure:")
        self.test_project_structure()
        print()

        # Summary
        print("=" * 70)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 70)

        total_tests = len(self.results)
        ok_tests = len([r for r in self.results if r["status"] == "OK"])
        warning_tests = len(self.warnings)
        error_tests = len(self.errors)

        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {ok_tests}")
        print(f"⚠️ Warnings: {warning_tests}")
        print(f"❌ Errors: {error_tests}")
        print()

        # Overall status
        if error_tests == 0 and warning_tests <= 2:
            print("🎉 OVERALL STATUS: EXCELLENT - Ready for development!")
        elif error_tests == 0:
            print("✅ OVERALL STATUS: GOOD - Minor issues that can be ignored")
        elif error_tests <= 2:
            print("⚠️ OVERALL STATUS: NEEDS ATTENTION - Some issues should be fixed")
        else:
            print("❌ OVERALL STATUS: CRITICAL - Multiple issues need fixing")

        # Recommendations
        fixes = self.generate_fixes()
        if fixes:
            print()
            print("🔧 RECOMMENDED FIXES:")
            for i, fix in enumerate(fixes, 1):
                print(f"   {i}. {fix}")

        print()
        print("=" * 70)

        return error_tests == 0


def main():
    """Main diagnostic function"""
    diagnostic = TerminalDiagnostic()
    success = diagnostic.run_full_diagnostic()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
