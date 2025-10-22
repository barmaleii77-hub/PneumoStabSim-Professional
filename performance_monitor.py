#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PneumoStabSim Performance Monitor
Утилита для мониторинга производительности приложения
"""

import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from pathlib import Path

# Опциональный импорт psutil с graceful fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[WARNING] psutil not available. Performance monitoring will be limited.")
    print("[TIP] Install psutil for full monitoring: pip install psutil")


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    fps: Optional[float] = None
    frame_time_ms: Optional[float] = None
    qt_objects_count: Optional[int] = None


class PerformanceMonitor:
    """Монитор производительности для PneumoStabSim"""

    def __init__(self, pid: Optional[int] = None):
        if not PSUTIL_AVAILABLE:
            print("[PERF] Performance monitoring disabled (psutil not available)")
            self.process = None
            self.pid = None
        else:
            self.pid = pid or psutil.Process().pid
            self.process = psutil.Process(self.pid)

        self.metrics: List[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # FPS счетчик
        self._frame_times: List[float] = []
        self._last_frame_time = time.time()

    def start_monitoring(self, interval: float = 1.0):
        """Запустить мониторинг"""
        if not PSUTIL_AVAILABLE:
            print("[PERF] Cannot start monitoring: psutil not available")
            return

        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        print(f"[PERF] Мониторинг производительности запущен (PID: {self.pid})")

    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("[PERF] Мониторинг производительности остановлен")

    def _monitor_loop(self, interval: float):
        """Основной цикл мониторинга"""
        while self.monitoring:
            try:
                if not PSUTIL_AVAILABLE or not self.process:
                    time.sleep(interval)
                    continue

                # Получаем базовые метрики системы
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = self.process.memory_percent()

                # Вычисляем FPS если есть данные о кадрах
                fps = self._calculate_fps()
                frame_time_ms = self._calculate_frame_time()

                # Создаем метрику
                metric = PerformanceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    fps=fps,
                    frame_time_ms=frame_time_ms,
                )

                self.metrics.append(metric)

                # Ограничиваем количество метрик в памяти
                if len(self.metrics) > 1000:
                    self.metrics = self.metrics[-800:]  # Оставляем последние 800

                time.sleep(interval)

            except Exception as e:
                print(f"[PERF ERROR] {e}")
                time.sleep(interval)

    def record_frame(self):
        """Записать время кадра для FPS расчета"""
        current_time = time.time()
        frame_time = current_time - self._last_frame_time
        self._frame_times.append(frame_time)
        self._last_frame_time = current_time

        # Ограничиваем количество записей о кадрах
        if len(self._frame_times) > 60:  # Последние 60 кадров
            self._frame_times = self._frame_times[-30:]

    def _calculate_fps(self) -> Optional[float]:
        """Вычислить FPS на основе записанных времен кадров"""
        if len(self._frame_times) < 5:
            return None

        avg_frame_time = sum(self._frame_times[-10:]) / min(10, len(self._frame_times))
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return None

    def _calculate_frame_time(self) -> Optional[float]:
        """Вычислить среднее время кадра в миллисекундах"""
        if len(self._frame_times) < 5:
            return None

        avg_frame_time = sum(self._frame_times[-10:]) / min(10, len(self._frame_times))
        return avg_frame_time * 1000  # Конвертируем в миллисекунды

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Получить текущие метрики"""
        if not self.metrics:
            return None
        return self.metrics[-1]

    def get_average_metrics(self, last_n: int = 10) -> Dict[str, float]:
        """Получить средние метрики за последние N записей"""
        if not self.metrics:
            return {}

        recent_metrics = self.metrics[-last_n:]

        return {
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_memory_mb": sum(m.memory_mb for m in recent_metrics)
            / len(recent_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_fps": sum(m.fps for m in recent_metrics if m.fps)
            / max(sum(1 for m in recent_metrics if m.fps), 1),
            "avg_frame_time_ms": sum(
                m.frame_time_ms for m in recent_metrics if m.frame_time_ms
            )
            / max(sum(1 for m in recent_metrics if m.frame_time_ms), 1),
        }

    def print_status(self):
        """Вывести текущий статус производительности"""
        if not PSUTIL_AVAILABLE:
            print("[PERF] Мониторинг недоступен (psutil не установлен)")
            return

        current = self.get_current_metrics()
        if not current:
            print("[PERF] Нет данных о производительности")
            return

        averages = self.get_average_metrics()

        print("\n" + "=" * 50)
        print("СТАТУС ПРОИЗВОДИТЕЛЬНОСТИ PNEUMOSTABSIM")
        print("=" * 50)
        print(
            f"CPU: {current.cpu_percent:.1f}% (среднее: {averages.get('avg_cpu_percent', 0):.1f}%)"
        )
        print(f"Память: {current.memory_mb:.1f} MB ({current.memory_percent:.1f}%)")
        print(f"Среднее потребление памяти: {averages.get('avg_memory_mb', 0):.1f} MB")

        if current.fps:
            print(f"FPS: {current.fps:.1f} (среднее: {averages.get('avg_fps', 0):.1f})")
        if current.frame_time_ms:
            print(
                f"Время кадра: {current.frame_time_ms:.2f}ms (среднее: {averages.get('avg_frame_time_ms', 0):.2f}ms)"
            )

        print("=" * 50 + "\n")

    def save_metrics(self, filepath: Path):
        """Сохранить метрики в файл"""
        try:
            data = {
                "pid": self.pid,
                "psutil_available": PSUTIL_AVAILABLE,
                "metrics": [
                    {
                        "timestamp": m.timestamp,
                        "cpu_percent": m.cpu_percent,
                        "memory_mb": m.memory_mb,
                        "memory_percent": m.memory_percent,
                        "fps": m.fps,
                        "frame_time_ms": m.frame_time_ms,
                    }
                    for m in self.metrics
                ],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[PERF] Метрики сохранены в {filepath}")

        except Exception as e:
            print(f"[PERF ERROR] Не удалось сохранить метрики: {e}")


# Глобальный монитор производительности
_global_monitor: Optional[PerformanceMonitor] = None


def start_global_monitoring():
    """Запустить глобальный мониторинг производительности"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
        _global_monitor.start_monitoring()


def stop_global_monitoring():
    """Остановить глобальный мониторинг производительности"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()
        _global_monitor = None


def record_frame():
    """Записать кадр для глобального мониторинга"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.record_frame()


def print_performance_status():
    """Вывести статус производительности"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.print_status()
    else:
        print("[PERF] Мониторинг не запущен")


if __name__ == "__main__":
    # Тестирование монитора
    monitor = PerformanceMonitor()
    monitor.start_monitoring(0.5)

    try:
        for i in range(10):
            time.sleep(1)
            monitor.print_status()
    finally:
        monitor.stop_monitoring()
