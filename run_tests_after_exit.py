#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Exit Test Runner
Запускает тестовые скрипты ПОСЛЕ закрытия приложения
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional


class PostExitTestRunner:
    """Менеджер запуска тестов после выхода из приложения"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results: List[Dict] = []
        
    def run_test_script(self, script_path: Path, timeout: int = 30) -> Dict:
        """
        Запускает тестовый скрипт и возвращает результат
        
        Args:
            script_path: Путь к скрипту
            timeout: Таймаут выполнения (сек)
            
        Returns:
            Словарь с результатами теста
        """
        test_name = script_path.stem
        
        print(f"\n{'='*60}")
        print(f"🧪 ЗАПУСК: {test_name}")
        print(f"{'='*60}")
        
        try:
            start_time = time.perf_counter()
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            elapsed = time.perf_counter() - start_time
            
            # Определяем успешность по коду возврата
            success = result.returncode == 0
            
            test_result = {
                'name': test_name,
                'path': str(script_path),
                'success': success,
                'returncode': result.returncode,
                'elapsed': elapsed,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            # Вывод результата
            if success:
                print(f"✅ УСПЕХ: {test_name} ({elapsed:.2f}s)")
            else:
                print(f"❌ ОШИБКА: {test_name} (код: {result.returncode})")
                
            # Вывод stdout/stderr если есть ошибки
            if result.stderr:
                print(f"\n⚠️  STDERR:")
                print(result.stderr)
                
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"⏱️  ТАЙМАУТ: {test_name} (>{timeout}s)")
            return {
                'name': test_name,
                'path': str(script_path),
                'success': False,
                'returncode': -1,
                'elapsed': timeout,
                'stdout': '',
                'stderr': f'Timeout after {timeout}s'
            }
            
        except Exception as e:
            print(f"💥 ИСКЛЮЧЕНИЕ: {test_name} - {e}")
            return {
                'name': test_name,
                'path': str(script_path),
                'success': False,
                'returncode': -1,
                'elapsed': 0,
                'stdout': '',
                'stderr': str(e)
            }
    
    def discover_test_scripts(self) -> List[Path]:
        """
        Находит все тестовые скрипты в проекте
        
        Returns:
            Список путей к тестовым скриптам
        """
        test_patterns = [
            'test_*.py',
            '*_test.py',
            'analyze_*.py',
            'diagnose_*.py'
        ]
        
        test_scripts = []
        
        # Исключаем определенные директории
        exclude_dirs = {
            'venv', '.venv', '__pycache__', '.git', 
            'build', 'dist', '.pytest_cache', 'logs'
        }
        
        for pattern in test_patterns:
            for script in self.project_root.rglob(pattern):
                # Пропускаем скрипты в исключенных директориях
                if any(excluded in script.parts for excluded in exclude_dirs):
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
        
        print("=" * 60)
        print("🚀 POST-EXIT TEST RUNNER")
        print("=" * 60)
        print(f"📊 Найдено тестов: {len(scripts)}")
        
        if not scripts:
            print("⚠️  Тестовые скрипты не найдены!")
            return {'success': False, 'tests': []}
        
        # Запуск всех тестов
        for script in scripts:
            result = self.run_test_script(script)
            self.test_results.append(result)
        
        # Сводка
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed
        
        print(f"\n{'='*60}")
        print("📊 СВОДКА ТЕСТОВ")
        print(f"{'='*60}")
        print(f"📈 Всего тестов: {total}")
        print(f"✅ Успешно: {passed}")
        print(f"❌ Ошибок: {failed}")
        
        # Детали по ошибкам
        if failed > 0:
            print(f"\n❌ ТЕСТЫ С ОШИБКАМИ:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['name']} (код: {result['returncode']})")
                    if result['stderr']:
                        print(f"    └─ {result['stderr'][:100]}")
        
        print(f"\n{'='*60}")
        
        return {
            'success': failed == 0,
            'total': total,
            'passed': passed,
            'failed': failed,
            'tests': self.test_results
        }
    
    def save_report(self, output_file: Path = None):
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
            "",
            f"- Всего тестов: {len(self.test_results)}",
            f"- Успешно: {sum(1 for r in self.test_results if r['success'])}",
            f"- Ошибок: {sum(1 for r in self.test_results if not r['success'])}",
            "",
            "## Детали",
            ""
        ]
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            report_lines.extend([
                f"### {status} {result['name']}",
                "",
                f"- **Путь:** `{result['path']}`",
                f"- **Код возврата:** {result['returncode']}",
                f"- **Время выполнения:** {result['elapsed']:.2f}s",
                ""
            ])
            
            if result['stderr']:
                report_lines.extend([
                    "**STDERR:**",
                    "```",
                    result['stderr'][:500],  # Первые 500 символов
                    "```",
                    ""
                ])
        
        output_file.write_text('\n'.join(report_lines), encoding='utf-8')
        print(f"💾 Отчет сохранен: {output_file}")


def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🧪 POST-EXIT TEST RUNNER")
    print("="*60)
    print("Запускает тесты ПОСЛЕ закрытия основного приложения")
    print("="*60 + "\n")
    
    runner = PostExitTestRunner()
    
    # Автоопределение тестов
    test_scripts = runner.discover_test_scripts()
    
    if not test_scripts:
        print("⚠️  Тестовые скрипты не найдены!")
        print("💡 Убедитесь, что имена тестов начинаются с 'test_' или 'analyze_'")
        return 1
    
    print(f"📋 Найденные тесты ({len(test_scripts)}):")
    for i, script in enumerate(test_scripts, 1):
        rel_path = script.relative_to(Path.cwd())
        print(f"  {i}. {rel_path}")
    
    print()
    
    # Запуск всех тестов
    summary = runner.run_all_tests(test_scripts)
    
    # Сохранение отчета
    runner.save_report()
    
    # Возвращаем код ошибки если есть проблемы
    return 0 if summary['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
