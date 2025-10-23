#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Exit Test Runner
Запускает тестовые скрипты ПОСЛЕ закрытия приложения
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional


QT_ENV_DEFAULTS: Dict[str, str] = {
 "QT_QPA_PLATFORM": "offscreen",
 "QT_QUICK_BACKEND": "software",
 "QT_PLUGIN_PATH": "",
 "QML2_IMPORT_PATH": "",
}


@lru_cache(maxsize=1)
def _detect_qt_environment() -> Dict[str, str]:
 """Возвращает значения переменных окружения для корректной работы Qt."""

 environment = dict(QT_ENV_DEFAULTS)

 try:
 from PySide6.QtCore import QLibraryInfo, LibraryLocation # type: ignore
 except Exception as exc: # pragma: no cover - диагностический вывод
 print(f"⚠️ Не удалось определить пути Qt автоматически: {exc}")
 return environment

 plugin_path = QLibraryInfo.path(LibraryLocation.Plugins)
 if plugin_path:
 environment["QT_PLUGIN_PATH"] = plugin_path

 qml_import_path = QLibraryInfo.path(LibraryLocation.QmlImports)
 if qml_import_path:
 environment["QML2_IMPORT_PATH"] = qml_import_path

 return environment


class PostExitTestRunner:
 """Менеджер запуска тестов после выхода из приложения"""

 def __init__(self) -> None:
 self.project_root = Path(__file__).parent
 self.test_results: List[Dict] = []
 self.test_environment = os.environ.copy()
 self.test_environment.update(_detect_qt_environment())
 self.logs_dir = self.project_root / "logs"
 self.logs_dir.mkdir(parents=True, exist_ok=True)

 print("🔧 Настройка окружения Qt для тестов:")
 for key, value in _detect_qt_environment().items():
 print(f" • {key}={value}")

 print(f"🗂️ Логи тестов будут сохраняться в: {self.logs_dir}")

 def run_verify_suite(self) -> Optional[Dict]:
 """Запускает make verify или прямой pytest для smoke/integration."""

 log_file = self.logs_dir / "post_exit_verify.log"
 command: List[str]

 if shutil.which("make"):
 command = ["make", "verify"]
 else:
 command = [
 sys.executable,
 "-m",
 "pytest",
 "-m",
 "smoke or integration",
 "-vv",
 "--color=yes",
 f"--log-file={log_file}",
 "--log-file-level=INFO",
 ]

 print("=" *60)
 print("🚦 ВЕРИФИКАЦИЯ SMOKE/INTEGRATION")
 print("=" *60)
 print(f"📁 Команда: {' '.join(command)}")

 try:
 result = subprocess.run(
 command,
 capture_output=True,
 text=True,
 timeout=600,
 encoding="utf-8",
 errors="replace",
 env=self.test_environment,
 )
 except Exception as exc: # pragma: no cover - diagnostic path
 print(f"❌ Не удалось выполнить верификацию: {exc}")
 return None

 log_file.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")

 success = result.returncode ==0
 status = "✅" if success else "❌"
 print(f"{status} make verify завершен с кодом {result.returncode}")

 verification_result = {
 "name": "make verify",
 "path": "make verify",
 "success": success,
 "returncode": result.returncode,
 "elapsed":0.0,
 "stdout": result.stdout,
 "stderr": result.stderr,
 }

 self.test_results.append(verification_result)
 return verification_result

 def run_test_script(self, script_path: Path, timeout: int =30) -> Dict:
 """
 Запускает тестовый скрипт и возвращает результат

 Args:
 script_path: Путь к скрипту
 timeout: Таймаут выполнения (сек)

 Returns:
 Словарь с результатами теста
 """
 test_name = script_path.stem

 print(f"\n{'=' *60}")
 print(f"🧪 ЗАПУСК: {test_name}")
 print(f"{'=' *60}")

 try:
 start_time = time.perf_counter()

 result = subprocess.run(
 [sys.executable, str(script_path)],
 capture_output=True,
 text=True,
 timeout=timeout,
 encoding="utf-8",
 errors="replace",
 env=self.test_environment,
 )

 elapsed = time.perf_counter() - start_time

 # Определяем успешность по коду возврата
 success = result.returncode ==0

 test_result = {
 "name": test_name,
 "path": str(script_path),
 "success": success,
 "returncode": result.returncode,
 "elapsed": elapsed,
 "stdout": result.stdout,
 "stderr": result.stderr,
 }
 except subprocess.TimeoutExpired as exc:
 test_result = {
 "name": test_name,
 "path": str(script_path),
 "success": False,
 "returncode": -1,
 "elapsed": timeout,
 "stdout": "",
 "stderr": f"Timeout: {exc}",
 }
 except Exception as exc:
 test_result = {
 "name": test_name,
 "path": str(script_path),
 "success": False,
 "returncode": -2,
 "elapsed":0.0,
 "stdout": "",
 "stderr": str(exc),
 }

 return test_result

 def discover_test_scripts(self) -> List[Path]:
 """
 Находит все скрипты для запуска после выхода

 Returns:
 Список путей к тестовым скриптам
 """
 test_patterns = ["test_*.py", "*_test.py", "analyze_*.py", "diagnose_*.py"]

 test_scripts: List[Path] = []

 # Исключаем определенные директории
 exclude_dirs = {
 "venv",
 ".venv",
 "__pycache__",
 ".git",
 "build",
 "dist",
 ".pytest_cache",
 "logs",
 }

 for pattern in test_patterns:
 for script in self.project_root.rglob(pattern):
 # Пропускаем скрипты в исключенных директориях
 if any(excluded in script.parts for excluded in exclude_dirs):
 continue

 # Тесты Pytest с GUI обрабатываются через make verify
 if ("tests" in script.parts and "smoke" in script.parts) or (
 "tests" in script.parts and "integration" in script.parts
 ):
 continue

 # Пропускаем этот файл
 if script.name == Path(__file__).name:
 continue

 test_scripts.append(script)

 return sorted(test_scripts)

 def run_all_tests(self, scripts: Optional[List[Path]] = None) -> Dict:
 """
 Запускает все тестовые скрипты

 Args:
 scripts: Список скриптов (None = автопоиск)

 Returns:
 Сводные результаты
 """
 if scripts is None:
 scripts = self.discover_test_scripts()

 print("=" *60)
 print("🚀 POST-EXIT TEST RUNNER")
 print("=" *60)
 print(f"📊 Найдено тестов: {len(scripts)}")

 if not scripts:
 print("⚠️ Тестовые скрипты не найдены!")
 return {"success": False, "tests": []}

 # Запуск всех тестов
 for script in scripts:
 result = self.run_test_script(script)
 self.test_results.append(result)

 # Сводка
 total = len(self.test_results)
 passed = sum(1 for r in self.test_results if r["success"])
 failed = total - passed

 print(f"\n{'=' *60}")
 print("📊 СВОДКА ТЕСТОВ")
 print(f"{'=' *60}")
 print(f"📈 Всего тестов: {total}")
 print(f"✅ Успешно: {passed}")
 print(f"❌ Ошибок: {failed}")

 # Детали по ошибкам
 if failed >0:
 print("\n❌ ТЕСТЫ С ОШИБКАМИ:")
 for result in self.test_results:
 if not result["success"]:
 print(f" • {result['name']} (код: {result['returncode']})")
 if result["stderr"]:
 print(f" └─ {result['stderr'][:100]}")

 print(f"\n{'=' *60}")

 return {
 "success": failed ==0,
 "total": total,
 "passed": passed,
 "failed": failed,
 "tests": self.test_results,
 }

 def save_report(self, output_file: Optional[Path] = None) -> None:
 """
 Сохраняет отчет о тестах

 Args:
 output_file: Путь к файлу отчета
 """
 if output_file is None:
 output_file = self.project_root / "test_report.md"

 report_lines = [
 "# Post-Exit Test Report",
 "",
 f"**Дата:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
 "",
 "## Сводка",
 ]

 for result in self.test_results:
 status = "✅" if result["success"] else "❌"
 report_lines.extend(
 [
 f"### {status} {result['name']}",
 "",
 f"- Путь: {result['path']}",
 f"- Код возврата: {result['returncode']}",
 f"- Время: {result['elapsed']:.2f} с",
 "",
 "**STDOUT:**",
 "```",
 result["stdout"][:500], # Первые500 символов
 "```",
 "",
 ]
 )
 if result["stderr"]:
 report_lines.extend(
 [
 "**STDERR:**",
 "```",
 result["stderr"][:500], # Первые500 символов
 "```",
 "",
 ]
 )

 output_file.write_text("\n".join(report_lines), encoding="utf-8")
 print(f"💾 Отчет сохранен: {output_file}")


def main() -> int:
 """Главная функция"""
 print("\n" + "=" *60)
 print("🧪 POST-EXIT TEST RUNNER")
 print("=" *60)
 print("Запускает тесты ПОСЛЕ закрытия основного приложения")
 print("=" *60 + "\n")

 runner = PostExitTestRunner()

 runner.run_verify_suite()

 # Автоопределение тестов
 test_scripts = runner.discover_test_scripts()

 if not test_scripts:
 print("⚠️ Тестовые скрипты не найдены!")
 print("💡 Убедитесь, что имена тестов начинаются с 'test_' или 'analyze_'")
 return 1

 print(f"📋 Найденные тесты ({len(test_scripts)}):")
 for i, script in enumerate(test_scripts,1):
 rel_path = script.relative_to(Path.cwd())
 print(f" {i}. {rel_path}")

 print()

 # Запуск всех тестов
 summary = runner.run_all_tests(test_scripts)

 # Сохранение отчета
 runner.save_report()

 # Возвращаем код ошибки если есть проблемы
 return 0 if summary["success"] else 1


if __name__ == "__main__":
 raise SystemExit(main())
