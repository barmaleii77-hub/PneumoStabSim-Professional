"""Post-Exit Test Runner utilities.

The original version of this script shipped with broken indentation which made the
module unparsable.  The reimplementation below keeps the same high level
behaviour (collecting helper scripts, running them sequentially and saving a
report) while restoring valid Python syntax so the tooling can import it again.
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
    """Return environment tweaks that make headless Qt launches succeed."""

    environment = dict(QT_ENV_DEFAULTS)

    try:  # pragma: no cover - PySide might be missing in CI
        from PySide6.QtCore import QLibraryInfo, LibraryLocation  # type: ignore
    except Exception as exc:  # pragma: no cover - diagnostic print only
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
    """Менеджер запуска тестов после выхода из приложения."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parent
        self.test_results: List[Dict[str, object]] = []
        self.test_environment = os.environ.copy()
        self.test_environment.update(_detect_qt_environment())
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        print("🔧 Настройка окружения Qt для тестов:")
        for key, value in _detect_qt_environment().items():
            print(f" • {key}={value}")

        print(f"🗂️ Логи тестов будут сохраняться в: {self.logs_dir}")

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def discover_test_scripts(self) -> List[Path]:
        """Найти вспомогательные скрипты, которые нужно прогнать."""

        test_patterns = ["test_*.py", "*_test.py", "analyze_*.py", "diagnose_*.py"]
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

        discovered: List[Path] = []
        for pattern in test_patterns:
            for script in self.project_root.rglob(pattern):
                if any(part in exclude_dirs for part in script.parts):
                    continue
                if ("tests" in script.parts and "smoke" in script.parts) or (
                    "tests" in script.parts and "integration" in script.parts
                ):
                    # Эти тесты покрываются make verify.
                    continue
                if script.name == Path(__file__).name:
                    continue

                resolved = script.resolve()
                if not resolved.is_file():
                    continue
                try:
                    resolved.relative_to(self.project_root.resolve())
                except ValueError:
                    print(
                        f"⚠️ Пропуск потенциально небезопасного скрипта вне репозитория: {resolved}"
                    )
                    continue

                discovered.append(resolved)

        return sorted(discovered)

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------
    def run_verify_suite(self) -> Optional[Dict[str, object]]:
        """Запустить smoke/integration набор (make verify)."""

        log_file = self.logs_dir / "post_exit_verify.log"

        if shutil.which("make"):
            command: List[str] = ["make", "verify"]
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

        print("=" * 60)
        print("🚦 ВЕРИФИКАЦИЯ SMOKE/INTEGRATION")
        print("=" * 60)
        print(f"📁 Команда: {' '.join(command)}")

        try:
            result = subprocess.run(  # noqa: S603
                command,
                capture_output=True,
                text=True,
                timeout=600,
                encoding="utf-8",
                errors="replace",
                env=self.test_environment,
                check=False,
            )
        except Exception as exc:  # pragma: no cover - diagnostic path only
            print(f"❌ Не удалось выполнить верификацию: {exc}")
            return None

        log_file.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")

        success = result.returncode == 0
        status = "✅" if success else "❌"
        print(f"{status} make verify завершен с кодом {result.returncode}")

        verification_result: Dict[str, object] = {
            "name": "make verify",
            "path": "make verify",
            "success": success,
            "returncode": result.returncode,
            "elapsed": 0.0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        self.test_results.append(verification_result)
        return verification_result

    def run_test_script(self, script_path: Path, timeout: int = 30) -> Dict[str, object]:
        """Запустить одиночный скрипт и вернуть результат."""

        script_path = script_path.resolve()

        try:
            script_path.relative_to(self.project_root.resolve())
        except ValueError:
            raise ValueError(
                f"Скрипт {script_path} находится вне каталога проекта и не будет выполнен"
            ) from None

        test_name = script_path.stem
        print(f"\n{'=' * 60}")
        print(f"🧪 ЗАПУСК: {test_name}")
        print("=" * 60)

        try:
            start_time = time.perf_counter()
            result = subprocess.run(  # noqa: S603
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                env=self.test_environment,
                check=False,
            )
            elapsed = time.perf_counter() - start_time
            success = result.returncode == 0
            test_result: Dict[str, object] = {
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
                "elapsed": float(timeout),
                "stdout": "",
                "stderr": f"Timeout: {exc}",
            }
        except Exception as exc:  # pragma: no cover - protective path
            test_result = {
                "name": test_name,
                "path": str(script_path),
                "success": False,
                "returncode": -2,
                "elapsed": 0.0,
                "stdout": "",
                "stderr": str(exc),
            }

        return test_result

    def run_all_tests(self, scripts: Optional[List[Path]] = None) -> Dict[str, object]:
        """Запустить набор скриптов и вернуть агрегированные результаты."""

        if scripts is None:
            scripts = self.discover_test_scripts()

        print("=" * 60)
        print("🚀 POST-EXIT TEST RUNNER")
        print("=" * 60)
        print(f"📊 Найдено тестов: {len(scripts)}")

        if not scripts:
            print("⚠️ Тестовые скрипты не найдены!")
            return {"success": False, "tests": []}

        for script in scripts:
            result = self.run_test_script(script)
            self.test_results.append(result)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get("success"))
        failed = total - passed

        print(f"\n{'=' * 60}")
        print("📊 СВОДКА ТЕСТОВ")
        print("=" * 60)
        print(f"📈 Всего тестов: {total}")
        print(f"✅ Успешно: {passed}")
        print(f"❌ Ошибок: {failed}")

        if failed > 0:
            print("\n❌ ТЕСТЫ С ОШИБКАМИ:")
            for result in self.test_results:
                if not result.get("success"):
                    print(f" • {result['name']} (код: {result['returncode']})")
                    stderr = str(result.get("stderr", ""))
                    if stderr:
                        print(f"   └─ {stderr[:100]}")

        summary: Dict[str, object] = {
            "success": failed == 0,
            "total": total,
            "passed": passed,
            "failed": failed,
            "tests": list(self.test_results),
        }
        return summary

    def save_report(self, output_file: Optional[Path] = None) -> None:
        """Сохранить текстовый отчёт с результатами тестов."""

        if output_file is None:
            output_file = self.project_root / "test_report.md"

        lines: List[str] = [
            "# Post-Exit Test Report",
            "",
            f"**Дата:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Сводка",
        ]

        for result in self.test_results:
            status = "✅" if result.get("success") else "❌"
            lines.extend(
                [
                    f"### {status} {result['name']}",
                    "",
                    f"- Путь: {result['path']}",
                    f"- Код возврата: {result['returncode']}",
                    f"- Время: {float(result['elapsed']):.2f} с",
                    "",
                    "**STDOUT:**",
                    "```",
                    str(result.get("stdout", ""))[:500],
                    "```",
                    "",
                ]
            )
            stderr = str(result.get("stderr", ""))
            if stderr:
                lines.extend(
                    [
                        "**STDERR:**",
                        "```",
                        stderr[:500],
                        "```",
                        "",
                    ]
                )

        output_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"💾 Отчет сохранен: {output_file}")


def main() -> int:
    """Entry point for manual execution."""

    print("\n" + "=" * 60)
    print("🧪 POST-EXIT TEST RUNNER")
    print("=" * 60)
    print("Запускает тесты ПОСЛЕ закрытия основного приложения")
    print("=" * 60 + "\n")

    runner = PostExitTestRunner()
    runner.run_verify_suite()

    test_scripts = runner.discover_test_scripts()
    if not test_scripts:
        print("⚠️ Тестовые скрипты не найдены!")
        print("💡 Убедитесь, что имена тестов начинаются с 'test_' или 'analyze_'")
        return 1

    print(f"📋 Найденные тесты ({len(test_scripts)}):")
    for index, script in enumerate(test_scripts, 1):
        rel_path = script.relative_to(Path.cwd())
        print(f" {index}. {rel_path}")

    print()

    summary = runner.run_all_tests(test_scripts)
    runner.save_report()

    return 0 if summary.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
