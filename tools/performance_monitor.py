#!/usr/bin/env python3
"""PneumoStabSim Performance Monitor utilities and CLI."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import threading
from html import escape
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.diagnostics.profiler import (  # noqa: E402
    export_profiler_report,
    load_profiler_overlay_state,
    record_profiler_overlay,
)

# Опциональный импорт psutil с graceful fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[WARNING] psutil not available. Performance monitoring will be limited.")
    print("[TIP] Install psutil for full monitoring: pip install psutil")

try:
    import pynvml  # type: ignore[import]

    try:
        pynvml.nvmlInit()
    except Exception as nvml_exc:  # pragma: no cover - defensive logging
        print(f"[WARNING] Unable to initialise NVML: {nvml_exc}")
        PYNVML_AVAILABLE = False
    else:
        PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None  # type: ignore[assignment]
    print("[INFO] pynvml not available. GPU metrics will be skipped.")


LOGGER = logging.getLogger(__name__)


def _shutdown_nvml() -> None:
    if PYNVML_AVAILABLE:
        try:
            pynvml.nvmlShutdown()
        except Exception:  # pragma: no cover - defensive logging
            pass


if PYNVML_AVAILABLE:
    import atexit

    atexit.register(_shutdown_nvml)


class GPUMonitor:
    """Helper that queries GPU metrics when NVML is available."""

    def __init__(self) -> None:
        self.available = PYNVML_AVAILABLE
        self._device_count: int | None = None

        if not self.available:
            return
        try:
            self._device_count = pynvml.nvmlDeviceGetCount()
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("gpu_metrics_unavailable", error=str(exc))
            self.available = False
            self._device_count = None

    def collect(self) -> dict[str, float] | None:
        if not self.available or not self._device_count:
            return None

        total_util = 0.0
        total_used = 0.0
        total_free = 0.0
        total_memory = 0.0

        for index in range(self._device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(index)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.debug(
                    "gpu_metric_collection_failed",
                    gpu_index=index,
                    error=str(exc),
                )
                continue

            total_util += float(util.gpu)
            total_used += memory.used / 1024 / 1024
            total_free += memory.free / 1024 / 1024
            total_memory += memory.total / 1024 / 1024

        if total_memory <= 0 and total_util <= 0:
            return None

        device_count = max(self._device_count, 1)
        return {
            "gpu_utilization_percent": total_util / device_count,
            "gpu_memory_used_mb": total_used,
            "gpu_memory_free_mb": total_free,
            "gpu_memory_total_mb": total_memory,
        }


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    cpu_time_user: float | None = None
    cpu_time_system: float | None = None
    cpu_time_total: float | None = None
    fps: float | None = None
    frame_time_ms: float | None = None
    gpu_utilization_percent: float | None = None
    gpu_memory_total_mb: float | None = None
    gpu_memory_used_mb: float | None = None
    gpu_memory_free_mb: float | None = None
    qt_objects_count: int | None = None
    profiler_overlay_enabled: bool | None = None


@dataclass
class ScenarioArtifacts:
    """Paths to artefacts produced by a profiling scenario."""

    json_path: Path
    html_path: Path


class PerformanceMonitor:
    """Монитор производительности для PneumoStabSim"""

    def __init__(self, pid: int | None = None):
        if not PSUTIL_AVAILABLE:
            print("[PERF] Performance monitoring disabled (psutil not available)")
            self.process = None
            self.pid = None
        else:
            self.pid = pid or psutil.Process().pid
            self.process = psutil.Process(self.pid)

        self.metrics: list[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_thread: threading.Thread | None = None

        # FPS счетчик
        self._frame_times: list[float] = []
        self._last_frame_time = time.time()
        self._gpu_monitor = GPUMonitor()

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
                cpu_times = self.process.cpu_times()
                cpu_time_user = getattr(cpu_times, "user", None)
                cpu_time_system = getattr(cpu_times, "system", None)
                cpu_time_total = None
                if cpu_time_user is not None or cpu_time_system is not None:
                    cpu_time_total = sum(
                        value
                        for value in (cpu_time_user or 0.0, cpu_time_system or 0.0)
                    )

                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_percent = self.process.memory_percent()
                gpu_metrics = self._gpu_monitor.collect()

                # Вычисляем FPS если есть данные о кадрах
                fps = self._calculate_fps()
                frame_time_ms = self._calculate_frame_time()

                try:
                    overlay_snapshot = load_profiler_overlay_state()
                    overlay_enabled: bool | None = overlay_snapshot.overlay_enabled
                except Exception as overlay_exc:  # pragma: no cover - defensive logging
                    LOGGER.debug(
                        "Unable to load profiler overlay state: %s", overlay_exc
                    )
                    overlay_enabled = None

                # Создаем метрику
                metric = PerformanceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    cpu_time_user=cpu_time_user,
                    cpu_time_system=cpu_time_system,
                    cpu_time_total=cpu_time_total,
                    memory_mb=memory_mb,
                    memory_percent=memory_percent,
                    fps=fps,
                    frame_time_ms=frame_time_ms,
                    gpu_utilization_percent=(
                        gpu_metrics.get("gpu_utilization_percent")
                        if gpu_metrics
                        else None
                    ),
                    gpu_memory_total_mb=(
                        gpu_metrics.get("gpu_memory_total_mb") if gpu_metrics else None
                    ),
                    gpu_memory_used_mb=(
                        gpu_metrics.get("gpu_memory_used_mb") if gpu_metrics else None
                    ),
                    gpu_memory_free_mb=(
                        gpu_metrics.get("gpu_memory_free_mb") if gpu_metrics else None
                    ),
                    profiler_overlay_enabled=overlay_enabled,
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

    def _calculate_fps(self) -> float | None:
        """Вычислить FPS на основе записанных времен кадров"""
        if len(self._frame_times) < 5:
            return None

        avg_frame_time = sum(self._frame_times[-10:]) / min(10, len(self._frame_times))
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return None

    def _calculate_frame_time(self) -> float | None:
        """Вычислить среднее время кадра в миллисекундах"""
        if len(self._frame_times) < 5:
            return None

        avg_frame_time = sum(self._frame_times[-10:]) / min(10, len(self._frame_times))
        return avg_frame_time * 1000  # Конвертируем в миллисекунды

    def get_current_metrics(self) -> PerformanceMetrics | None:
        """Получить текущие метрики"""
        if not self.metrics:
            return None
        return self.metrics[-1]

    def get_average_metrics(self, last_n: int = 10) -> dict[str, float]:
        """Получить средние метрики за последние N записей"""
        if not self.metrics:
            return {}

        recent_metrics = self.metrics[-last_n:]

        def _average_optional(values: list[float | None]) -> float | None:
            valid = [value for value in values if value is not None]
            if not valid:
                return None
            return sum(valid) / len(valid)

        averages: dict[str, float | None] = {
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_memory_mb": sum(m.memory_mb for m in recent_metrics)
            / len(recent_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_fps": _average_optional([m.fps for m in recent_metrics]),
            "avg_frame_time_ms": _average_optional(
                [m.frame_time_ms for m in recent_metrics]
            ),
            "avg_cpu_time_user": _average_optional(
                [m.cpu_time_user for m in recent_metrics]
            ),
            "avg_cpu_time_system": _average_optional(
                [m.cpu_time_system for m in recent_metrics]
            ),
            "avg_cpu_time_total": _average_optional(
                [m.cpu_time_total for m in recent_metrics]
            ),
            "avg_gpu_utilization_percent": _average_optional(
                [m.gpu_utilization_percent for m in recent_metrics]
            ),
            "avg_gpu_memory_total_mb": _average_optional(
                [m.gpu_memory_total_mb for m in recent_metrics]
            ),
            "avg_gpu_memory_used_mb": _average_optional(
                [m.gpu_memory_used_mb for m in recent_metrics]
            ),
            "avg_gpu_memory_free_mb": _average_optional(
                [m.gpu_memory_free_mb for m in recent_metrics]
            ),
        }

        return averages

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
        if current.cpu_time_total is not None:
            avg_cpu_time_total = averages.get("avg_cpu_time_total")
            total_display = (
                f"{current.cpu_time_total:.2f}s"
                if current.cpu_time_total is not None
                else "n/a"
            )
            avg_total_display = (
                f"{avg_cpu_time_total:.2f}s" if avg_cpu_time_total else "n/a"
            )
            print(
                f"CPU time (user+system): {total_display} (среднее: {avg_total_display})"
            )
        if current.cpu_time_user is not None or current.cpu_time_system is not None:
            user_display = (
                f"{current.cpu_time_user:.2f}s"
                if current.cpu_time_user is not None
                else "n/a"
            )
            system_display = (
                f"{current.cpu_time_system:.2f}s"
                if current.cpu_time_system is not None
                else "n/a"
            )
            print(f"  user: {user_display} • system: {system_display}")
        print(f"Память: {current.memory_mb:.1f} MB ({current.memory_percent:.1f}%)")
        print(f"Среднее потребление памяти: {averages.get('avg_memory_mb', 0):.1f} MB")

        if current.fps:
            avg_fps = averages.get("avg_fps")
            avg_fps_display = f"{avg_fps:.1f}" if avg_fps is not None else "n/a"
            print(f"FPS: {current.fps:.1f} (среднее: {avg_fps_display})")
        if current.frame_time_ms:
            avg_frame_time = averages.get("avg_frame_time_ms")
            avg_frame_time_display = (
                f"{avg_frame_time:.2f}" if avg_frame_time is not None else "n/a"
            )
            print(
                "Время кадра: "
                f"{current.frame_time_ms:.2f}ms (среднее: {avg_frame_time_display}ms)"
            )
        if current.gpu_utilization_percent is not None:
            avg_gpu_util = averages.get("avg_gpu_utilization_percent")
            gpu_util_display = f"{current.gpu_utilization_percent:.1f}%"
            avg_gpu_util_display = (
                f"{avg_gpu_util:.1f}%" if avg_gpu_util is not None else "n/a"
            )
            print(f"GPU util: {gpu_util_display} (среднее: {avg_gpu_util_display})")
        if current.gpu_memory_total_mb is not None:
            used = (
                f"{current.gpu_memory_used_mb:.1f}"
                if current.gpu_memory_used_mb is not None
                else "n/a"
            )
            free = (
                f"{current.gpu_memory_free_mb:.1f}"
                if current.gpu_memory_free_mb is not None
                else "n/a"
            )
            total = f"{current.gpu_memory_total_mb:.1f}"
            print(f"GPU memory (used/free/total MB): {used}/{free}/{total}")

        overlay_state = None
        try:
            overlay_state = load_profiler_overlay_state()
        except Exception as overlay_exc:  # pragma: no cover - defensive logging
            LOGGER.debug(
                "Unable to refresh overlay state during status print: %s",
                overlay_exc,
            )

        if overlay_state:
            print(
                "Profiler overlay enabled:",
                "Yes" if overlay_state.overlay_enabled else "No",
            )
        elif current.profiler_overlay_enabled is not None:
            print(
                "Profiler overlay enabled (cached):",
                "Yes" if current.profiler_overlay_enabled else "No",
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
                        "cpu_time_user": m.cpu_time_user,
                        "cpu_time_system": m.cpu_time_system,
                        "cpu_time_total": m.cpu_time_total,
                        "memory_mb": m.memory_mb,
                        "memory_percent": m.memory_percent,
                        "fps": m.fps,
                        "frame_time_ms": m.frame_time_ms,
                        "gpu_utilization_percent": m.gpu_utilization_percent,
                        "gpu_memory_total_mb": m.gpu_memory_total_mb,
                        "gpu_memory_used_mb": m.gpu_memory_used_mb,
                        "gpu_memory_free_mb": m.gpu_memory_free_mb,
                        "profiler_overlay_enabled": m.profiler_overlay_enabled,
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
_global_monitor: PerformanceMonitor | None = None


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


def _write_html_report(json_path: Path, html_path: Path | None = None) -> Path:
    """Generate a lightweight HTML report next to the JSON artefact."""

    json_path = Path(json_path)
    html_path = Path(html_path) if html_path else json_path.with_suffix(".html")
    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    extra = payload.get("extra", {}) or {}
    averages = extra.get("averages") or payload.get("metadata", {}).get("averages", {})
    meta_rows = []

    for label, value in (
        ("Scenario", payload.get("scenario")),
        ("Recorded at", payload.get("recordedAt")),
        ("Overlay enabled", payload.get("overlayEnabled")),
        ("Sample count", extra.get("sampleCount")),
        ("psutil available", extra.get("psutilAvailable")),
        ("GPU metrics available", extra.get("gpuMetricsAvailable")),
    ):
        if value is None:
            value = "n/a"
        meta_rows.append(
            f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>"
        )

    averages_rows = []
    if isinstance(averages, dict):
        for key, value in sorted(averages.items()):
            if isinstance(value, (int, float)):
                display_value = f"{value:.3f}" if abs(value) < 10 else f"{value:.1f}"
            else:
                display_value = value if value is not None else "n/a"
            averages_rows.append(
                f"<tr><th>{escape(str(key))}</th><td>{escape(str(display_value))}</td></tr>"
            )

    html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>Qt Quick Profiling Report</title>
    <style>
      body {{ font-family: 'Segoe UI', sans-serif; margin: 2rem; background: #111; color: #eee; }}
      h1 {{ font-size: 1.8rem; margin-bottom: 1rem; }}
      section {{ margin-bottom: 2rem; }}
      table {{ border-collapse: collapse; width: 100%; max-width: 720px; }}
      th, td {{ border: 1px solid #333; padding: 0.5rem; text-align: left; }}
      th {{ background: #1f1f1f; color: #71c7ff; width: 260px; }}
      td {{ background: #181818; }}
    </style>
  </head>
  <body>
    <h1>Qt Quick Profiling Report</h1>
    <section>
      <h2>Scenario metadata</h2>
      <table>{"".join(meta_rows)}</table>
    </section>
    <section>
      <h2>Aggregated metrics</h2>
      <table>{"".join(averages_rows) if averages_rows else '<tr><td colspan="2">No aggregated metrics available.</td></tr>'}</table>
    </section>
    <section>
      <h2>Raw payload</h2>
      <pre style=\"background:#181818; padding:1rem; overflow-x:auto;\">{escape(json.dumps(payload, indent=2, ensure_ascii=False))}</pre>
    </section>
  </body>
</html>
"""

    html_path.parent.mkdir(parents=True, exist_ok=True)
    with html_path.open("w", encoding="utf-8") as handle:
        handle.write(html_content)

    LOGGER.info("performance_html_report_written path=%s", html_path)
    return html_path


def _run_phase3_scenario(
    output_path: Path,
    *,
    duration: float,
    interval: float,
    html_output: Path | None = None,
) -> ScenarioArtifacts:
    """Capture profiler overlay information for the phase 3 UI scenario."""

    LOGGER.info(
        "Running phase3 performance scenario (duration=%.2fs, interval=%.2fs)",
        duration,
        interval,
    )
    monitor = PerformanceMonitor()
    monitor.start_monitoring(interval)
    try:
        frame_interval = 1.0 / 60.0  # emulate a 60 FPS render loop in headless mode
        deadline = time.time() + duration
        while time.time() < deadline:
            monitor.record_frame()
            time.sleep(frame_interval)
    finally:
        monitor.stop_monitoring()

    averages = monitor.get_average_metrics()
    sample_count = len(monitor.metrics)

    base_state = load_profiler_overlay_state()
    metadata = {
        "scenario": "phase3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "averages": averages,
        "samples": sample_count,
        "overlay_enabled": base_state.overlay_enabled,
        "gpu_metrics_available": monitor._gpu_monitor.available,
    }
    snapshot = record_profiler_overlay(
        base_state.overlay_enabled,
        source="performance_monitor.phase3",
        scenario="phase3",
        metadata=metadata,
    )

    extra_payload = {
        "averages": averages,
        "sampleCount": sample_count,
        "psutilAvailable": PSUTIL_AVAILABLE,
        "gpuMetricsAvailable": monitor._gpu_monitor.available,
        "overlayEnabled": snapshot.overlay_enabled,
    }

    json_path = export_profiler_report(
        output_path,
        state=snapshot,
        scenario="phase3",
        extra=extra_payload,
    )
    html_path = _write_html_report(json_path, html_output)
    return ScenarioArtifacts(json_path=json_path, html_path=html_path)


def _run_default_scenario(
    output_path: Path,
    *,
    duration: float,
    interval: float,
    html_output: Path | None = None,
) -> ScenarioArtifacts:
    """Базовый сценарий perf-check (default): метрики процесса без специфической UI фазы.

    Эмулирует рендер цикл 60 FPS для оценки frame time. Пишет агрегаты
    (averages) и snapshot overlay в perf_summary.json.
    """

    LOGGER.info(
        "Running default performance scenario (duration=%.2fs, interval=%.2fs)",
        duration,
        interval,
    )
    monitor = PerformanceMonitor()
    monitor.start_monitoring(interval)
    try:
        frame_interval = 1.0 / 60.0
        deadline = time.time() + duration
        while time.time() < deadline:
            monitor.record_frame()
            time.sleep(frame_interval)
    finally:
        monitor.stop_monitoring()

    averages = monitor.get_average_metrics()
    sample_count = len(monitor.metrics)
    base_state = load_profiler_overlay_state()
    metadata = {
        "scenario": "default",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "averages": averages,
        "samples": sample_count,
        "overlay_enabled": base_state.overlay_enabled,
        "gpu_metrics_available": monitor._gpu_monitor.available,
    }
    snapshot = record_profiler_overlay(
        base_state.overlay_enabled,
        source="performance_monitor.default",
        scenario="default",
        metadata=metadata,
    )
    extra_payload = {
        "averages": averages,
        "sampleCount": sample_count,
        "psutilAvailable": PSUTIL_AVAILABLE,
        "gpuMetricsAvailable": monitor._gpu_monitor.available,
        "overlayEnabled": snapshot.overlay_enabled,
    }
    json_path = export_profiler_report(
        output_path,
        state=snapshot,
        scenario="default",
        extra=extra_payload,
    )
    html_path = _write_html_report(json_path, html_output)
    return ScenarioArtifacts(json_path=json_path, html_path=html_path)


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PneumoStabSim performance monitor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scenario",
        choices=["default", "phase3"],
        help="Run a predefined monitoring scenario instead of the interactive sampler.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Destination file for scenario reports.",
    )
    parser.add_argument(
        "--html-output",
        type=Path,
        default=None,
        help="Optional HTML report path. Defaults to replacing the JSON extension with .html.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=3.0,
        help="Sampling duration in seconds.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.25,
        help="Sampling interval in seconds.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Verbosity for diagnostic output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.scenario:
        output = args.output
        if args.scenario == "default":
            if output is None:
                output = Path("reports/performance/perf_summary.json")
            artifacts = _run_default_scenario(
                output_path=output,
                duration=args.duration,
                interval=args.interval,
                html_output=args.html_output,
            )
            print(
                "[PERF] Scenario 'default' reports written to"  # консольный вывод
                f" JSON={artifacts.json_path} HTML={artifacts.html_path}"
            )
            return 0
        if args.scenario == "phase3":
            if output is None:
                output = Path("reports/performance/ui_phase3_profile.json")
            artifacts = _run_phase3_scenario(
                output_path=output,
                duration=args.duration,
                interval=args.interval,
                html_output=args.html_output,
            )
            print(
                "[PERF] Scenario 'phase3' reports written to"
                f" JSON={artifacts.json_path} HTML={artifacts.html_path}"
            )
            return 0
        parser.error(f"Unsupported scenario: {args.scenario}")

    # Интерактивный режим (без --scenario)
    monitor = PerformanceMonitor()
    monitor.start_monitoring(args.interval)
    try:
        time.sleep(args.duration)
        monitor.print_status()
    finally:
        monitor.stop_monitoring()
    return 0


if __name__ == "__main__":
    sys.exit(main())
