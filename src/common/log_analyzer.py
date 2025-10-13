# -*- coding: utf-8 -*-
"""
Комплексный анализатор логов PneumoStabSim
Объединяет все типы анализов в единую систему
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import re
from collections import defaultdict, Counter


class LogAnalysisResult:
    """Результат анализа логов"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.metrics: Dict[str, float] = {}
        self.recommendations: List[str] = []
        self.status: str = "unknown"  # ok, warning, error
    
    def is_ok(self) -> bool:
        """Проверяет, всё ли в порядке"""
        return len(self.errors) == 0 and self.status != "error"
    
    def add_error(self, message: str):
        """Добавляет ошибку"""
        self.errors.append(message)
        self.status = "error"
    
    def add_warning(self, message: str):
        """Добавляет предупреждение"""
        self.warnings.append(message)
        if self.status != "error":
            self.status = "warning"
    
    def add_info(self, message: str):
        """Добавляет информацию"""
        self.info.append(message)
        if self.status == "unknown":
            self.status = "ok"
    
    def add_metric(self, name: str, value: float):
        """Добавляет метрику"""
        self.metrics[name] = value
    
    def add_recommendation(self, message: str):
        """Добавляет рекомендацию"""
        self.recommendations.append(message)


class UnifiedLogAnalyzer:
    """Объединенный анализатор всех типов логов"""
    
    def __init__(self, logs_dir: Path = Path("logs")):
        self.logs_dir = logs_dir
        self.results: Dict[str, LogAnalysisResult] = {}
    
    def analyze_all(self) -> Dict[str, LogAnalysisResult]:
        """Запускает полный анализ всех логов"""
        
        # Основной лог
        self.results['main'] = self._analyze_main_log()
        
        # Graphics логи
        self.results['graphics'] = self._analyze_graphics_logs()
        
        # IBL логи
        self.results['ibl'] = self._analyze_ibl_logs()
        
        # Event логи (Python↔QML)
        self.results['events'] = self._analyze_event_logs()
        
        # Общий статус
        self.results['summary'] = self._generate_summary()
        
        return self.results
    
    def _analyze_main_log(self) -> LogAnalysisResult:
        """Анализирует основной лог приложения"""
        result = LogAnalysisResult()
        
        run_log = self.logs_dir / "run.log"
        if not run_log.exists():
            result.add_error("run.log не найден")
            return result
        
        try:
            with open(run_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            errors = [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]
            warnings = [line for line in lines if 'WARNING' in line]
            
            result.add_metric('total_lines', len(lines))
            result.add_metric('errors', len(errors))
            result.add_metric('warnings', len(warnings))
            
            if errors:
                result.add_error(f"Обнаружено {len(errors)} ошибок в run.log")
                for error in errors[:3]:  # Первые 3
                    result.add_error(f"  → {error.strip()}")
            
            if warnings:
                result.add_warning(f"Обнаружено {len(warnings)} предупреждений")
                if len(warnings) > 10:
                    result.add_recommendation("Много предупреждений - проверьте конфигурацию")
            
            if not errors and not warnings:
                result.add_info("Основной лог чистый - ошибок нет")
            
            # Анализ времени работы
            startup_time = None
            shutdown_time = None
            
            for line in lines:
                if 'START RUN' in line:
                    match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line)
                    if match:
                        startup_time = match.group(0)
                elif 'END RUN' in line:
                    match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', line)
                    if match:
                        shutdown_time = match.group(0)
            
            if startup_time and shutdown_time:
                try:
                    start = datetime.fromisoformat(startup_time)
                    end = datetime.fromisoformat(shutdown_time)
                    duration = (end - start).total_seconds()
                    result.add_metric('runtime_seconds', duration)
                    result.add_info(f"Время работы: {duration:.1f}s")
                except:
                    pass
            
        except Exception as e:
            result.add_error(f"Ошибка анализа run.log: {e}")
        
        return result
    
    def _analyze_graphics_logs(self) -> LogAnalysisResult:
        """Анализирует логи графики"""
        result = LogAnalysisResult()
        
        graphics_dir = self.logs_dir / "graphics"
        if not graphics_dir.exists():
            result.add_warning("Директория graphics логов не найдена")
            return result
        
        # Находим последний session лог
        session_logs = sorted(graphics_dir.glob("session_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not session_logs:
            result.add_warning("Нет session логов графики")
            return result
        
        latest_session = session_logs[0]
        
        try:
            events = []
            with open(latest_session, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            # Анализ синхронизации
            total_events = len([e for e in events if e.get('event_type') in ('parameter_change', 'parameter_update')])
            synced_events = len([e for e in events if e.get('applied_to_qml', False)])
            failed_events = len([e for e in events if e.get('error')])
            
            result.add_metric('graphics_total_events', total_events)
            result.add_metric('graphics_synced', synced_events)
            result.add_metric('graphics_failed', failed_events)
            
            if total_events > 0:
                sync_rate = (synced_events / total_events) * 100
                result.add_metric('graphics_sync_rate', sync_rate)
                
                if sync_rate >= 95:
                    result.add_info(f"Синхронизация графики: {sync_rate:.1f}% (отлично)")
                elif sync_rate >= 80:
                    result.add_warning(f"Синхронизация графики: {sync_rate:.1f}% (приемлемо)")
                    result.add_recommendation("Проверьте QML функции applyXxxUpdates()")
                else:
                    result.add_error(f"Синхронизация графики: {sync_rate:.1f}% (критично низкая)")
                    result.add_recommendation("Критические проблемы синхронизации - проверьте Python↔QML мост")
            
            # Анализ по категориям
            categories = Counter(e.get('category', 'unknown') for e in events if e.get('category'))
            if categories:
                result.add_info(f"Категории изменений: {dict(categories)}")
            
        except Exception as e:
            result.add_error(f"Ошибка анализа graphics логов: {e}")
        
        return result
    
    def _analyze_ibl_logs(self) -> LogAnalysisResult:
        """Анализирует IBL логи"""
        result = LogAnalysisResult()
        
        ibl_dir = self.logs_dir / "ibl"
        if not ibl_dir.exists():
            result.add_warning("Директория IBL логов не найдена")
            return result
        
        ibl_logs = sorted(ibl_dir.glob("ibl_signals_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        if not ibl_logs:
            result.add_warning("Нет IBL логов")
            return result
        
        latest_ibl = ibl_logs[0]
        
        try:
            with open(latest_ibl, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            errors = [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]
            warnings = [line for line in lines if 'WARN' in line]
            success = [line for line in lines if 'SUCCESS' in line or 'LOADED successfully' in line]
            
            result.add_metric('ibl_total_events', len(lines))
            result.add_metric('ibl_errors', len(errors))
            result.add_metric('ibl_warnings', len(warnings))
            result.add_metric('ibl_success', len(success))
            
            if errors:
                result.add_error(f"IBL ошибки: {len(errors)}")
                for error in errors[:2]:
                    result.add_error(f"  → {error.strip()}")
                result.add_recommendation("Проверьте пути к HDR файлам")
            
            if success:
                result.add_info(f"IBL успешно загружен ({len(success)} событий)")
            
        except Exception as e:
            result.add_error(f"Ошибка анализа IBL логов: {e}")
        
        return result
    
    def _analyze_event_logs(self) -> LogAnalysisResult:
        """Анализирует логи событий Python↔QML"""
        result = LogAnalysisResult()
        
        # Пытаемся найти события через EventLogger
        try:
            from src.common.event_logger import get_event_logger
            
            event_logger = get_event_logger()
            analysis = event_logger.analyze_sync()
            
            total = analysis.get('total_signals', 0)
            synced = analysis.get('synced', 0)
            missing = analysis.get('missing_qml', 0)
            
            result.add_metric('event_total', total)
            result.add_metric('event_synced', synced)
            result.add_metric('event_missing', missing)
            
            if total > 0:
                sync_rate = (synced / total) * 100
                result.add_metric('event_sync_rate', sync_rate)
                
                if sync_rate >= 95:
                    result.add_info(f"Python↔QML синхронизация: {sync_rate:.1f}% (отлично)")
                elif sync_rate >= 80:
                    result.add_warning(f"Python↔QML синхронизация: {sync_rate:.1f}%")
                else:
                    result.add_error(f"Python↔QML синхронизация: {sync_rate:.1f}% (критично)")
                
                if missing > 0:
                    result.add_warning(f"Пропущено QML событий: {missing}")
                    result.add_recommendation("Проверьте QML connections и signals")
            else:
                result.add_info("Событий Python↔QML не обнаружено (возможно, не было активности)")
            
        except ImportError:
            result.add_warning("EventLogger не доступен - пропущен анализ событий")
        except Exception as e:
            result.add_error(f"Ошибка анализа событий: {e}")
        
        return result
    
    def _generate_summary(self) -> LogAnalysisResult:
        """Генерирует общий summary"""
        summary = LogAnalysisResult()
        
        # Собираем все ошибки и предупреждения
        all_errors = []
        all_warnings = []
        all_metrics = {}
        all_recommendations = []
        
        for category, result in self.results.items():
            if category == 'summary':
                continue
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_metrics.update({f"{category}_{k}": v for k, v in result.metrics.items()})
            all_recommendations.extend(result.recommendations)
        
        # Общая статистика
        summary.add_metric('total_errors', len(all_errors))
        summary.add_metric('total_warnings', len(all_warnings))
        summary.add_metric('total_recommendations', len(all_recommendations))
        
        # Определяем общий статус
        if all_errors:
            summary.status = "error"
            summary.add_error(f"Обнаружено критических проблем: {len(all_errors)}")
        elif all_warnings:
            summary.status = "warning"
            summary.add_warning(f"Обнаружено предупреждений: {len(all_warnings)}")
        else:
            summary.status = "ok"
            summary.add_info("Все проверки пройдены успешно")
        
        # Сохраняем все собранные данные
        for error in all_errors:
            if error not in summary.errors:
                summary.errors.append(error)
        
        for warning in all_warnings:
            if warning not in summary.warnings:
                summary.warnings.append(warning)
        
        for rec in all_recommendations:
            if rec not in summary.recommendations:
                summary.recommendations.append(rec)
        
        summary.metrics.update(all_metrics)
        
        return summary
    
    def print_results(self):
        """Выводит результаты анализа в консоль"""
        print("\n" + "="*70)
        print("📊 КОМПЛЕКСНЫЙ АНАЛИЗ ЛОГОВ")
        print("="*70)
        
        for category, result in self.results.items():
            if category == 'summary':
                continue
            
            print(f"\n📁 {category.upper()}")
            print("-"*70)
            
            # Метрики
            if result.metrics:
                print("\nМетрики:")
                for name, value in result.metrics.items():
                    print(f"  • {name}: {value}")
            
            # Информация
            if result.info:
                print("\nℹ️  Информация:")
                for info in result.info:
                    print(f"  {info}")
            
            # Предупреждения
            if result.warnings:
                print("\n⚠️  Предупреждения:")
                for warning in result.warnings:
                    print(f"  {warning}")
            
            # Ошибки
            if result.errors:
                print("\n❌ Ошибки:")
                for error in result.errors:
                    print(f"  {error}")
        
        # Summary
        if 'summary' in self.results:
            summary = self.results['summary']
            
            print("\n" + "="*70)
            print("📋 ИТОГИ")
            print("="*70)
            
            status_icon = {
                'ok': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(summary.status, '❓')
            
            print(f"\nСтатус: {status_icon} {summary.status.upper()}")
            print(f"Ошибок: {len(summary.errors)}")
            print(f"Предупреждений: {len(summary.warnings)}")
            
            if summary.recommendations:
                print("\n💡 Рекомендации:")
                for i, rec in enumerate(summary.recommendations, 1):
                    print(f"  {i}. {rec}")
        
        print("\n" + "="*70 + "\n")


# ============================================================================
# ЭКСПОРТНЫЕ ФУНКЦИИ ДЛЯ APP.PY
# ============================================================================

def run_full_diagnostics(logs_dir: Path = Path("logs")) -> bool:
    """
    Запускает полную диагностику всех логов
    
    Args:
        logs_dir: Директория с логами
    
    Returns:
        True если проблем нет, False если есть критические проблемы
    """
    analyzer = UnifiedLogAnalyzer(logs_dir)
    results = analyzer.analyze_all()
    analyzer.print_results()
    
    # Возвращаем True только если нет критических ошибок
    return results.get('summary', LogAnalysisResult()).status != "error"


def quick_diagnostics(logs_dir: Path = Path("logs")) -> Dict[str, any]:
    """
    Быстрая диагностика - только ключевые метрики
    
    Returns:
        Dict с ключевыми метриками
    """
    analyzer = UnifiedLogAnalyzer(logs_dir)
    results = analyzer.analyze_all()
    
    summary = results.get('summary', LogAnalysisResult())
    
    return {
        'status': summary.status,
        'errors': len(summary.errors),
        'warnings': len(summary.warnings),
        'recommendations': len(summary.recommendations),
        'metrics': summary.metrics
    }
