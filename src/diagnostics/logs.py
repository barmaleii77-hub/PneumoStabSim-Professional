# -*- coding: utf-8 -*-
"""
Модуль диагностики логов после завершения приложения.

Запускает комплексный анализ логов с использованием log_analyzer
и выводит результаты в консоль и Visual Studio Output.
"""
import sys
import os
import ctypes
from pathlib import Path


def run_log_diagnostics() -> None:
    """
    Запускает ВСТРОЕННУЮ диагностику логов после закрытия приложения.
    
    Включает:
    - Анализ синхронизации Python↔QML
    - Графические метрики
    - События пользователя
    - Несоответствия между категориями логов
    """
    # Дублируем вывод в окно Output Visual Studio (через OutputDebugString)
    class _VSOutputTee:
        def __init__(self, real):
            self._real = real
        
        def write(self, s: str) -> int:
            try:
                if sys.platform == 'win32' and s:
                    ctypes.windll.kernel32.OutputDebugStringW(str(s))
            except Exception:
                pass
            return self._real.write(s)
        
        def flush(self) -> None:
            try:
                self._real.flush()
            except Exception:
                pass

    _orig_stdout = sys.stdout
    _orig_stderr = sys.stderr
    
    try:
        # Включаем tee в VS Output
        sys.stdout = _VSOutputTee(_orig_stdout)
        sys.stderr = _VSOutputTee(_orig_stderr)

        print("\n" + "="*60)
        print("🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ")
        print("="*60)

        # ✅ Используем унифицированный анализатор
        from src.common.log_analyzer import run_full_diagnostics, quick_diagnostics
        
        # Запускаем комплексный анализ
        diag_result = run_full_diagnostics(Path("logs"))
        diagnostics_ok = bool(diag_result) if not isinstance(diag_result, dict) else bool(diag_result.get("ok", True))
        
        # Результат анализа
        print("\n" + "="*60)
        
        if diagnostics_ok:
            print("✅ Диагностика завершена - критических проблем не обнаружено")
        else:
            print("⚠️  Диагностика завершена - обнаружены проблемы")
            print("💡 См. детали выше")
        
        print("="*60)

        # Дополнительный раздел: несоответствия анализа (EVENTS vs GRAPHICS)
        _print_sync_discrepancies(quick_diagnostics)
        
    except ImportError as e:
        print(f"⚠️  Модуль анализа не найден: {e}")
        print("💡 Используйте устаревшую версию analyze_logs.py")
        _fallback_diagnostics()
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Восстанавливаем стандартные потоки
        sys.stdout = _orig_stdout
        sys.stderr = _orig_stderr


def _print_sync_discrepancies(quick_diagnostics) -> None:
    """Выводит несоответствия между EVENTS и GRAPHICS метриками."""
    try:
        q = quick_diagnostics(Path("logs")) or {}
        metrics = q.get("metrics", {}) or {}
        events_sync = None
        graphics_sync = None
        
        for key, val in metrics.items():
            if key.endswith("event_sync_rate") and key.startswith("events_"):
                events_sync = float(val)
            if key.endswith("graphics_sync_rate") and key.startswith("graphics_"):
                graphics_sync = float(val)
        
        if events_sync is not None and graphics_sync is not None and abs(events_sync - graphics_sync) >= 5.0:
            print("\n—— Несоответствия анализа ————————")
            print(f"EVENTS sync_rate: {events_sync:.1f}% vs GRAPHICS sync_rate: {graphics_sync:.1f}%")
            
            reason_hint = "QML-функции вызываются (EVENTS=OK), но часть графических обновлений не применяется."
            if events_sync < graphics_sync:
                reason_hint = "Графические метрики выше событийных — возможно, не все SIGNAL_EMIT логируются."
            
            print(f"Причина (гипотеза): {reason_hint}")
            
            if os.environ.get("PSS_DIAG_DETAILS") == "1":
                _print_detailed_sync_analysis()
            
            print("——————————————\n")
    except Exception:
        pass  # Не ломаем диагностику из-за раздела несоответствий


def _print_detailed_sync_analysis() -> None:
    """Выводит детальный анализ несинхронизированных событий."""
    try:
        from src.common.event_logger import get_event_logger
        evlog = get_event_logger()
        analysis = evlog.analyze_sync()
        pairs = analysis.get("pairs", [])
        missing = [p for p in pairs if p.get("status") != "synced"]
        
        if missing:
            print("\nНесинхронизированные пары (последние 10):")
            for p in missing[-10:]:
                py = p.get("python_event", {})
                ts = py.get("timestamp", "?")
                action = py.get("action", "?")
                print(f"  • {ts} — {action} → missing in QML")
        else:
            print("\nEVENTS: все пары синхронизированы (нет missing)")
    except Exception:
        pass


def _fallback_diagnostics() -> None:
    """Fallback на старую версию analyze_logs.py."""
    try:
        from analyze_logs import (
            analyze_all_logs,
            analyze_graphics_sync,
            analyze_user_session
        )
        
        print("\n📊 Анализ всех логов...")
        logs_result = analyze_all_logs()
        
        print("\n🎨 Анализ синхронизации графики...")
        graphics_result = analyze_graphics_sync()
        
        print("\n👤 Анализ пользовательской сессии...")
        session_result = analyze_user_session()
        
        _analyze_event_logger()
        
        print("\n" + "="*60)
        
        all_ok = all([logs_result, graphics_result, session_result])
        
        if all_ok:
            print("✅ Диагностика завершена - проблем не обнаружено")
        else:
            print("⚠️  Диагностика завершена - обнаружены проблемы")
        
        print("="*60)
        
    except ImportError:
        print("⚠️  Модули анализа не доступны")
    except Exception as e:
        print(f"❌ Ошибка fallback диагностики: {e}")
        import traceback
        traceback.print_exc()


def _analyze_event_logger() -> None:
    """Анализ событий Python↔QML через EventLogger."""
    print("\n🔗 Анализ событий Python↔QML...")
    try:
        from src.common.event_logger import get_event_logger
        
        event_logger = get_event_logger()
        events_file = event_logger.export_events()
        print(f"   📁 События экспортированы: {events_file}")
        
        analysis = event_logger.analyze_sync()
        total = analysis.get('total_signals', 0)
        synced = analysis.get('synced', 0)
        missing = analysis.get('missing_qml', 0)
        
        if total > 0:
            sync_rate = (synced / total) * 100
            print(f"   Всего сигналов: {total}")
            print(f"   Синхронизировано: {synced}")
            print(f"   Пропущено QML: {missing}")
            print(f"   Процент синхронизации: {sync_rate:.1f}%")
            
            if missing > 0:
                print(f"   ⚠️  Обнаружены несинхронизированные события!")
            else:
                print(f"   ✅ Все события успешно синхронизированы")
        else:
            print(f"   ℹ️  Сигналов не обнаружено")
        
        # Статистика по типам
        event_types: dict[str, int] = {}
        for event in event_logger.events:
            event_type = event.get('event_type', 'UNKNOWN')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if event_types:
            print(f"\n   📈 События по типам:")
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                print(f"      {event_type}: {count}")
        
    except ImportError:
        print(f"   ⚠️  EventLogger не доступен")
    except Exception as e:
        print(f"   ❌ Ошибка анализа событий: {e}")
