#!/usr/bin/env python3
"""
Comprehensive test runner for PneumoStabSim Professional.

The suite validates Python integration, repository structure, and
configuration health for the modernised Qt/Python stack.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging


class ProjectTester:
    """Comprehensive project testing and validation"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "warnings": 0},
        }
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for test runner"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"test_run_{int(time.time())}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Test session started - Log file: {log_file}")

    def run_command(
        self, command: list[str], cwd: Optional[Path] = None, timeout: int = 60
    ) -> dict[str, Any]:
        """Run a command and capture output"""
        cwd = cwd or self.project_root

        try:
            self.logger.info(f"Running: {' '.join(command)} in {cwd}")

            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(command),
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command),
            }

    def test_python_environment(self) -> bool:
        """Test Python environment setup"""
        self.logger.info("Testing Python environment...")

        # Run environment checker
        env_check = self.run_command(
            [
                sys.executable,
                str(self.project_root / "scripts" / "check_environment.py"),
            ]
        )

        self.results["tests"]["python_environment"] = {
            "passed": env_check["success"],
            "details": env_check,
        }

        if env_check["success"]:
            self.logger.info("✓ Python environment check passed")
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ Python environment check failed")
            self.logger.error(f"Error: {env_check['stderr']}")
            self.results["summary"]["failed"] += 1
            return False

    def test_python_imports(self) -> bool:
        """Test critical Python imports"""
        self.logger.info("Testing Python imports...")

        import_test_script = """
import sys
import os
sys.path.insert(0, ".")
sys.path.insert(0, "src")

try:
    # Test core imports
    import numpy as np
    import scipy
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer

    # Test project imports
    from src.common import init_logging
    from src.core.geometry import Vector3D
    from src.mechanics.components import Mass, Spring

    print("All critical imports successful")
    exit(0)

except ImportError as e:
    print(f"Import error: {e}")
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    exit(2)
"""

        import_result = self.run_command([sys.executable, "-c", import_test_script])

        self.results["tests"]["python_imports"] = {
            "passed": import_result["success"],
            "details": import_result,
        }

        if import_result["success"]:
            self.logger.info("✓ Python imports test passed")
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ Python imports test failed")
            self.logger.error(f"Error: {import_result['stderr']}")
            self.results["summary"]["failed"] += 1
            return False

    def test_python_app_startup(self) -> bool:
        """Test Python application startup (test mode)"""
        self.logger.info("Testing Python application startup...")

        # Test with --test-mode for automatic shutdown
        app_result = self.run_command(
            [sys.executable, "app.py", "--test-mode"], timeout=30
        )

        self.results["tests"]["python_app_startup"] = {
            "passed": app_result["success"],
            "details": app_result,
        }

        if app_result["success"]:
            self.logger.info("✓ Python application startup test passed")
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ Python application startup test failed")
            self.logger.error(f"Error: {app_result['stderr']}")
            self.results["summary"]["failed"] += 1
            return False

    def test_file_structure(self) -> bool:
        """Test project file structure"""
        self.logger.info("Testing project file structure...")

        required_files = [
            "app.py",
            "pyproject.toml",
            "uv.lock",
            "Makefile",
            "config/app_settings.json",
            "config/qml_bridge.yaml",
            "src/app_runner.py",
            "src/bootstrap/environment.py",
            "tests/__init__.py",
        ]

        deprecated_artifacts = [
            "PneumoStabSim-Professional.sln",
            "PneumoStabSim-Professional.csproj",
            "PneumoStabSim-Professional.pyproj",
            "PneumoStabSim.sln",
        ]

        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        unexpected_legacy = []
        for file_path in deprecated_artifacts:
            if (self.project_root / file_path).exists():
                unexpected_legacy.append(file_path)

        success = len(missing_files) == 0 and not unexpected_legacy

        self.results["tests"]["file_structure"] = {
            "passed": success,
            "details": {
                "required_files": required_files,
                "missing_files": missing_files,
                "unexpected_legacy": unexpected_legacy,
                "total_required": len(required_files),
                "found": len(required_files) - len(missing_files),
            },
        }

        if success:
            self.logger.info("✓ File structure test passed")
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ File structure test failed")
            if missing_files:
                self.logger.error(f"Missing files: {missing_files}")
            if unexpected_legacy:
                self.logger.error(
                    "Unexpected legacy artefacts detected: %s", unexpected_legacy
                )
            self.results["summary"]["failed"] += 1
            return False

    def test_python_syntax(self) -> bool:
        """Test Python syntax validation"""
        self.logger.info("Testing Python syntax...")

        python_files = list(self.project_root.glob("**/*.py"))
        syntax_errors = []

        for py_file in python_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    compile(f.read(), str(py_file), "exec")
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
            except Exception:
                # Skip files with encoding or other issues
                continue

        success = len(syntax_errors) == 0

        self.results["tests"]["python_syntax"] = {
            "passed": success,
            "details": {
                "files_checked": len(python_files),
                "syntax_errors": syntax_errors,
            },
        }

        if success:
            self.logger.info(
                f"✓ Python syntax test passed ({len(python_files)} files checked)"
            )
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ Python syntax test failed")
            for error in syntax_errors:
                self.logger.error(f"  {error}")
            self.results["summary"]["failed"] += 1
            return False

    def test_configuration_files(self) -> bool:
        """Test configuration file validity"""
        self.logger.info("Testing configuration files...")

        config_files = [
            "config/appsettings.json",
            "config/appsettings.Development.json",
        ]

        config_errors = []

        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    config_errors.append(f"{config_file}: {e}")

        success = len(config_errors) == 0

        self.results["tests"]["configuration_files"] = {
            "passed": success,
            "details": {"files_checked": config_files, "errors": config_errors},
        }

        if success:
            self.logger.info("✓ Configuration files test passed")
            self.results["summary"]["passed"] += 1
            return True
        else:
            self.logger.error("✗ Configuration files test failed")
            for error in config_errors:
                self.logger.error(f"  {error}")
            self.results["summary"]["failed"] += 1
            return False

    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

        # JSON report
        json_report = reports_dir / f"test_report_{int(time.time())}.json"
        with open(json_report, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Markdown report
        md_report = reports_dir / f"test_report_{int(time.time())}.md"
        with open(md_report, "w", encoding="utf-8") as f:
            f.write("# PneumoStabSim Professional Test Report\n\n")
            f.write(f"**Date:** {self.results['timestamp']}\n")
            f.write(
                f"**Summary:** {self.results['summary']['passed']} passed, {self.results['summary']['failed']} failed, {self.results['summary']['warnings']} warnings\n\n"
            )

            f.write("## Test Results\n\n")
            for test_name, test_result in self.results["tests"].items():
                status = "✓ PASSED" if test_result["passed"] else "✗ FAILED"
                f.write(f"### {test_name.replace('_', ' ').title()}: {status}\n\n")

                if "details" in test_result and "command" in test_result["details"]:
                    f.write(f"**Command:** `{test_result['details']['command']}`\n")

                if not test_result["passed"] and "details" in test_result:
                    if (
                        "stderr" in test_result["details"]
                        and test_result["details"]["stderr"]
                    ):
                        f.write(
                            f"**Error:**\n```\n{test_result['details']['stderr']}\n```\n"
                        )

                f.write("\n")

        self.logger.info(f"Reports generated: {json_report}, {md_report}")

    def run_comprehensive_test(self) -> bool:
        """Run all tests"""
        print("=" * 60)
        print("PneumoStabSim Professional - Comprehensive Test Suite")
        print("=" * 60)

        tests = [
            ("File Structure", self.test_file_structure),
            ("Python Syntax", self.test_python_syntax),
            ("Configuration Files", self.test_configuration_files),
            ("Python Environment", self.test_python_environment),
            ("Python Imports", self.test_python_imports),
            ("Python App Startup", self.test_python_app_startup),
        ]

        print(f"\nRunning {len(tests)} test categories...\n")

        overall_success = True

        for test_name, test_func in tests:
            print(f"{'=' * 20} {test_name} {'=' * 20}")
            try:
                success = test_func()
                if not success:
                    overall_success = False
            except Exception as e:
                self.logger.error(f"Test {test_name} crashed: {e}")
                self.results["tests"][test_name.lower().replace(" ", "_")] = {
                    "passed": False,
                    "details": {"error": str(e)},
                }
                self.results["summary"]["failed"] += 1
                overall_success = False

            print()

        # Generate reports
        try:
            self.generate_report()
        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")

        # Final summary
        print("=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {self.results['summary']['passed']}")
        print(f"Tests Failed: {self.results['summary']['failed']}")
        print(f"Warnings: {self.results['summary']['warnings']}")
        print()

        if overall_success:
            print("🎉 ALL TESTS PASSED!")
            print("Your PneumoStabSim Professional environment is ready!")
            print()
            print("Next steps:")
            print("1. Run: python app.py")
            print("2. Check the reports/ directory for detailed test results")
        else:
            print("❌ SOME TESTS FAILED")
            print("Please review the errors above and fix the issues.")
            print("Check the reports/ directory for detailed analysis.")

        print("=" * 60)

        return overall_success


def main():
    """Main entry point"""
    tester = ProjectTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
