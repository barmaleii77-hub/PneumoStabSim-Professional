#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализатор логов PneumoStabSim
Комплексный анализ всех типов логов с детальной статистикой и рекомендациями
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
import re

# ============================================================================
# Безопасный вывод для Windows
# ============================================================================


def safe_print(text: str):
    """Безопасный вывод с обработкой кодировки"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback для Windows консоли
        print(text.encode("ascii", "replace").decode("ascii"))


# ============================================================================
# ЦВЕТНОЙ ВЫВОД ДЛЯ КОНСОЛИ
# ============================================================================


class Colors:
    """ANSI цвета для красивого вывода"""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Основные цвета
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def colored(text: str, color: str, bold: bool = False) -> str:
    """Раскрашивает текст"""
    # Для Windows консоли убираем цвета если не поддерживаются
    if sys.platform == "win32" and not sys.stdout.isatty():
        return text
    prefix = Colors.BOLD if bold else ""
    return f"{prefix}{color}{text}{Colors.RESET}"


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ФАЙЛАМИ
# ============================================================================


def find_latest_log(log_dir: Path, pattern: str) -> Optional[Path]:
    """Находит самый свежий лог-файл по паттерну"""
    logs = list(log_dir.glob(pattern))
    if not logs:
        return None
    return max(logs, key=lambda p: p.stat().st_mtime)


def format_timestamp(ts: str) -> str:
    """Форматирует timestamp для отображения"""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except:
        return ts


def format_size(size_bytes: int) -> str:
    """Форматирует размер файла"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# ============================================================================
# АНАЛИЗАТОР GRAPHICS ЛОГОВ
# ============================================================================


class GraphicsLogAnalyzer:
    """Анализирует логи изменений графики"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events = []
        self.stats = {
            "total": 0,
            "by_category": defaultdict(int),
            "synced": 0,
            "failed": 0,
            "pending": 0,
            "by_parameter": defaultdict(int),
            "timeline": [],
        }

    def load_events(self) -> bool:
        """Загружает события из файла"""
        if not self.log_file.exists():
            return False

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self.events.append(event)
                        except json.JSONDecodeError:
                            continue
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def analyze(self):
        """Анализирует загруженные события"""
        self.stats["total"] = len(self.events)

        for event in self.events:
            # Категории
            category = event.get("category", "unknown")
            self.stats["by_category"][category] += 1

            # Параметры
            param = event.get("parameter_name", "unknown")
            self.stats["by_parameter"][param] += 1

            # Синхронизация
            applied = event.get("applied_to_qml", False)
            qml_state = event.get("qml_state")

            if applied:
                self.stats["synced"] += 1
            elif qml_state and not qml_state.get("applied"):
                self.stats["failed"] += 1
            else:
                self.stats["pending"] += 1

            # Timeline
            timestamp = event.get("timestamp", "")
            if timestamp:
                self.stats["timeline"].append(
                    {
                        "time": format_timestamp(timestamp),
                        "category": category,
                        "param": param,
                        "old": event.get("old_value"),
                        "new": event.get("new_value"),
                    }
                )

    def get_sync_rate(self) -> float:
        """Вычисляет процент синхронизации"""
        if self.stats["total"] == 0:
            return 0.0
        return (self.stats["synced"] / self.stats["total"]) * 100

    def get_top_parameters(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Возвращает топ измененных параметров"""
        return sorted(
            self.stats["by_parameter"].items(), key=lambda x: x[1], reverse=True
        )[:limit]

    def get_category_distribution(self) -> Dict[str, float]:
        """Возвращает распределение по категориям в процентах"""
        total = self.stats["total"]
        if total == 0:
            return {}
        return {
            cat: (count / total) * 100
            for cat, count in self.stats["by_category"].items()
        }


# ============================================================================
# АНАЛИЗАТОР IBL ЛОГОВ
# ============================================================================


class IblLogAnalyzer:
    """Анализирует IBL логи"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events = []
        self.stats = {
            "total": 0,
            "by_component": defaultdict(int),
            "by_level": defaultdict(int),
            "errors": [],
            "warnings": [],
        }

    def load_events(self) -> bool:
        """Загружает IBL события"""
        if not self.log_file.exists():
            return False

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 4:
                            event = {
                                "timestamp": parts[0].strip(),
                                "level": parts[1].strip(),
                                "component": parts[2].strip(),
                                "message": parts[3].strip(),
                            }
                            self.events.append(event)
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки IBL: {e}")
            return False

    def analyze(self):
        """Анализирует IBL события"""
        self.stats["total"] = len(self.events)

        for event in self.events:
            component = event.get("component", "unknown")
            level = event.get("level", "INFO")
            message = event.get("message", "")

            self.stats["by_component"][component] += 1
            self.stats["by_level"][level] += 1

            if level == "ERROR":
                self.stats["errors"].append(event)
            elif level == "WARNING":
                self.stats["warnings"].append(event)


# ============================================================================
# АНАЛИЗАТОР RUN.LOG
# ============================================================================


class RunLogAnalyzer:
    """Анализирует основной лог приложения"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.stats = {
            "errors": [],
            "warnings": [],
            "info": [],
            "qml_events": [],
            "startup_time": None,
            "shutdown_time": None,
        }

    def analyze(self) -> bool:
        """Анализирует run.log"""
        if not self.log_file.exists():
            return False

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()

                # Определяем уровень
                if "ERROR" in line:
                    self.stats["errors"].append(line)
                elif "WARNING" in line:
                    self.stats["warnings"].append(line)
                elif "INFO" in line:
                    self.stats["info"].append(line)

                # QML события
                if any(
                    keyword in line for keyword in ["QML", "qml:", "apply", "update"]
                ):
                    self.stats["qml_events"].append(line)

                # Время запуска/завершения
                if "START RUN" in line:
                    self.stats["startup_time"] = self._extract_time(line)
                elif "END RUN" in line:
                    self.stats["shutdown_time"] = self._extract_time(line)

            return True
        except Exception as e:
            print(f"❌ Ошибка анализа run.log: {e}")
            return False

    def _extract_time(self, line: str) -> Optional[str]:
        """Извлекает время из строки лога"""
        match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line)
        return match.group(0) if match else None


# ============================================================================
# АНАЛИЗАТОР JSON ЛОГОВ ОШИБОК
# ============================================================================


class ErrorLogAnalyzer:
    """Парсит jsonl логи глобального обработчика ошибок."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.entries: List[Dict[str, Any]] = []
        self.stats = {
            "total": 0,
            "by_type": defaultdict(int),
            "by_source": defaultdict(int),
            "with_stack": 0,
        }

    def load(self) -> bool:
        """Загружает jsonl и нормализует записи."""

        if not self.log_file.exists():
            return False

        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    payload = line.strip()
                    if not payload:
                        continue
                    try:
                        raw = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    normalized = self._normalize_entry(raw)
                    self.entries.append(normalized)
        except Exception as exc:
            safe_print(f"❌ Ошибка загрузки лога ошибок: {exc}")
            return False

        self._recalculate_stats()
        return True

    def _normalize_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Приводит запись к универсальному виду для отображения."""

        entry: Dict[str, Any] = {
            "timestamp": raw.get("timestamp")
            or raw.get("time")
            or raw.get("ts"),
            "type": None,
            "message": None,
            "source": raw.get("logger")
            or raw.get("component")
            or raw.get("module"),
            "context": raw.get("context") or raw.get("details"),
            "stack": None,
            "raw": raw,
        }

        error_block: Any = raw.get("error") or raw.get("exception")

        if isinstance(error_block, dict):
            entry["type"] = (
                error_block.get("type")
                or error_block.get("name")
                or error_block.get("exception_type")
            )
            entry["message"] = error_block.get("message") or error_block.get(
                "value"
            )
            entry["stack"] = error_block.get("stack") or error_block.get(
                "traceback"
            )
        elif isinstance(error_block, str):
            entry["message"] = error_block

        if not entry["type"]:
            entry["type"] = (
                raw.get("type")
                or raw.get("error_type")
                or raw.get("level")
                or "Ошибка"
            )

        if not entry["message"]:
            entry["message"] = (
                raw.get("message")
                or raw.get("msg")
                or raw.get("description")
                or "(сообщение отсутствует)"
            )

        stack = raw.get("stack") or raw.get("traceback")
        if stack and not entry["stack"]:
            entry["stack"] = stack

        return entry

    def _recalculate_stats(self) -> None:
        stats = self.stats
        stats["total"] = len(self.entries)
        stats["by_type"].clear()
        stats["by_source"].clear()
        stats["with_stack"] = 0

        for entry in self.entries:
            stats["by_type"][entry["type"]] += 1
            if entry.get("source"):
                stats["by_source"][entry["source"]] += 1
            if entry.get("stack"):
                stats["with_stack"] += 1

    def get_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.entries[-limit:]

    def get_top_types(self, limit: int = 5) -> List[Tuple[str, int]]:
        return sorted(
            self.stats["by_type"].items(), key=lambda item: item[1], reverse=True
        )[:limit]

    def get_top_sources(self, limit: int = 5) -> List[Tuple[str, int]]:
        return sorted(
            self.stats["by_source"].items(), key=lambda item: item[1], reverse=True
        )[:limit]

# ============================================================================
# ГЛАВНЫЙ АНАЛИЗАТОР
# ============================================================================


class LogAnalyzer:
    """Главный класс анализатора всех логов"""

    def __init__(self):
        self.logs_dir = Path("logs")
        self.graphics_analyzer = None
        self.ibl_analyzer = None
        self.run_analyzer = None
        self.error_analyzer = None

    def run(self):
        """Запускает полный анализ"""
        safe_print(colored("\n" + "=" * 80, Colors.CYAN, bold=True))
        safe_print(colored("АНАЛИЗАТОР ЛОГОВ PneumoStabSim", Colors.CYAN, bold=True))
        safe_print(colored("=" * 80 + "\n", Colors.CYAN, bold=True))

        if not self.logs_dir.exists():
            safe_print(
                colored("ERROR: Директория logs/ не найдена!", Colors.RED, bold=True)
            )
            return

        # Анализ Graphics логов
        self._analyze_graphics()

        # Анализ IBL логов
        self._analyze_ibl()

        # Анализ Run.log
        self._analyze_run()

        # Анализ JSON лога ошибок
        self._analyze_error_logs()

        # Итоговый отчёт
        self._generate_summary()

        # Рекомендации
        self._generate_recommendations()

    def _analyze_graphics(self):
        """Анализирует Graphics логи"""
        safe_print(colored("АНАЛИЗ ГРАФИЧЕСКИХ ЛОГОВ", Colors.BLUE, bold=True))
        safe_print("-" * 80)

        graphics_dir = self.logs_dir / "graphics"
        if not graphics_dir.exists():
            safe_print(
                colored("ERROR: Директория logs/graphics не найдена", Colors.RED)
            )
            return

        latest = find_latest_log(graphics_dir, "session_*.jsonl")
        if not latest:
            safe_print(colored("ERROR: Файлы session_*.jsonl не найдены", Colors.RED))
            return

        safe_print(f"Файл: {colored(latest.name, Colors.CYAN)}")
        safe_print(
            f"Размер: {colored(format_size(latest.stat().st_size), Colors.CYAN)}"
        )

        analyzer = GraphicsLogAnalyzer(latest)
        if not analyzer.load_events():
            return

        analyzer.analyze()
        self.graphics_analyzer = analyzer

        # Статистика
        stats = analyzer.stats
        sync_rate = analyzer.get_sync_rate()

        safe_print("\nСТАТИСТИКА:")
        safe_print(
            f"   Всего событий: {colored(str(stats['total']), Colors.GREEN, bold=True)}"
        )
        synced_str = f"{stats['synced']}/{stats['total']}"
        safe_print(
            f"   Синхронизировано: {colored(synced_str, Colors.GREEN)} ({sync_rate:.1f}%)"
        )
        safe_print(f"   Ожидание: {colored(str(stats['pending']), Colors.YELLOW)}")
        safe_print(f"   Ошибки: {colored(str(stats['failed']), Colors.RED)}")

        # Прогресс-бар синхронизации
        bar_width = 50
        filled = int(bar_width * sync_rate / 100)
        bar = "#" * filled + "-" * (bar_width - filled)

        if sync_rate >= 95:
            bar_color = Colors.GREEN
        elif sync_rate >= 80:
            bar_color = Colors.YELLOW
        else:
            bar_color = Colors.RED

        safe_print(f"\n   Синхронизация: {colored(bar, bar_color)} {sync_rate:.1f}%")

        # Категории
        safe_print("\nПО КАТЕГОРИЯМ:")
        for cat, count in sorted(
            stats["by_category"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / stats["total"]) * 100
            safe_print(
                f"   {cat:15} {colored(str(count), Colors.CYAN):>6} ({percentage:5.1f}%)"
            )

        # Топ параметров
        safe_print("\nТОП-10 ИЗМЕНЁННЫХ ПАРАМЕТРОВ:")
        for param, count in analyzer.get_top_parameters(10):
            safe_print(f"   {param:30} {colored(f'{count}x', Colors.MAGENTA)}")

        # Последние события
        safe_print("\nПОСЛЕДНИЕ 5 СОБЫТИЙ:")
        for event in stats["timeline"][-5:]:
            time_str = colored(f"[{event['time']}]", Colors.CYAN)
            cat_str = colored(event["category"], Colors.BLUE)
            param_str = colored(event["param"], Colors.GREEN)
            change_str = (
                f"{event['old']} -> {colored(str(event['new']), Colors.YELLOW)}"
            )
            safe_print(f"   {time_str} {cat_str}.{param_str}: {change_str}")

    def _analyze_ibl(self):
        """Анализирует IBL логи"""
        safe_print(colored("\nАНАЛИЗ IBL ЛОГОВ", Colors.BLUE, bold=True))
        safe_print("-" * 80)

        ibl_dir = self.logs_dir / "ibl"
        if not ibl_dir.exists():
            safe_print(colored("ERROR: Директория logs/ibl не найдена", Colors.RED))
            return

        latest = find_latest_log(ibl_dir, "ibl_signals_*.log")
        if not latest:
            safe_print(colored("ERROR: Файлы ibl_signals не найдены", Colors.RED))
            return

        safe_print(f"Файл: {colored(latest.name, Colors.CYAN)}")
        safe_print(
            f"Размер: {colored(format_size(latest.stat().st_size), Colors.CYAN)}"
        )

        analyzer = IblLogAnalyzer(latest)
        if not analyzer.load_events():
            return

        analyzer.analyze()
        self.ibl_analyzer = analyzer

        stats = analyzer.stats

        safe_print("\nСТАТИСТИКА:")
        safe_print(
            f"   Всего событий: {colored(str(stats['total']), Colors.GREEN, bold=True)}"
        )

        safe_print("\nПО КОМПОНЕНТАМ:")
        for comp, count in sorted(
            stats["by_component"].items(), key=lambda x: x[1], reverse=True
        ):
            safe_print(f"   {comp:20} {colored(str(count), Colors.CYAN):>6}")

        safe_print("\nПО УРОВНЯМ:")
        for level, count in sorted(stats["by_level"].items()):
            level_color = {
                "ERROR": Colors.RED,
                "WARNING": Colors.YELLOW,
                "INFO": Colors.GREEN,
            }.get(level, Colors.WHITE)
            safe_print(f"   {level:10} {colored(str(count), level_color):>6}")

        if stats["errors"]:
            safe_print(f"\nОШИБКИ ({len(stats['errors'])}):")
            for error in stats["errors"][:3]:
                safe_print(f"   {colored(error['message'][:70], Colors.RED)}")

        if stats["warnings"]:
            safe_print(f"\nПРЕДУПРЕЖДЕНИЯ ({len(stats['warnings'])}):")
            for warning in stats["warnings"][:3]:
                safe_print(f"   {colored(warning['message'][:70], Colors.YELLOW)}")

    def _analyze_error_logs(self):
        """Отображает детальный список ошибок из JSON лога."""

        safe_print(colored("\nАНАЛИЗ ЛОГА ОШИБОК", Colors.BLUE, bold=True))
        safe_print("-" * 80)

        errors_dir = self.logs_dir / "errors"
        if not errors_dir.exists():
            safe_print(colored("⚠️  Директория logs/errors не найдена", Colors.YELLOW))
            return

        latest = find_latest_log(errors_dir, "errors_*.jsonl")
        if not latest:
            safe_print(colored("⚠️  Файлы errors_*.jsonl не найдены", Colors.YELLOW))
            return

        safe_print(f"Файл: {colored(latest.name, Colors.CYAN)}")
        safe_print(
            f"Размер: {colored(format_size(latest.stat().st_size), Colors.CYAN)}"
        )

        analyzer = ErrorLogAnalyzer(latest)
        if not analyzer.load():
            return

        self.error_analyzer = analyzer
        stats = analyzer.stats

        total_color = Colors.RED if stats["total"] else Colors.GREEN
        safe_print("\nСТАТИСТИКА:")
        safe_print(
            f"   Всего ошибок: {colored(str(stats['total']), total_color, bold=True)}"
        )
        safe_print(
            f"   Со стеком вызовов: {colored(str(stats['with_stack']), Colors.MAGENTA)}"
        )

        top_types = analyzer.get_top_types()
        if top_types:
            safe_print("\nПО ТИПАМ:")
            for err_type, count in top_types:
                safe_print(
                    f"   {err_type:25} {colored(str(count), Colors.RED):>6}"
                )

        top_sources = analyzer.get_top_sources()
        if top_sources:
            safe_print("\nИСТОЧНИКИ:")
            for source, count in top_sources:
                safe_print(
                    f"   {source:25} {colored(str(count), Colors.CYAN):>6}"
                )

        recent = analyzer.get_recent()
        if recent:
            safe_print("\nПОСЛЕДНИЕ ОШИБКИ:")
            for entry in recent:
                time_str = (
                    colored(f"[{format_timestamp(entry['timestamp'])}]", Colors.CYAN)
                    if entry.get("timestamp")
                    else ""
                )
                type_str = colored(entry.get("type", "Ошибка"), Colors.RED, bold=True)
                message = entry.get("message", "")
                safe_print(f"   {time_str} {type_str}: {message}")
                if entry.get("source"):
                    safe_print(
                        f"      Источник: {colored(entry['source'], Colors.YELLOW)}"
                    )
                if entry.get("context"):
                    safe_print(f"      Контекст: {entry['context']}")
                stack = entry.get("stack")
                if stack:
                    first_line = stack.strip().splitlines()[0]
                    safe_print(
                        f"      Stack: {colored(first_line[:120], Colors.MAGENTA)}"
                    )

    def _analyze_run(self):
        """Анализирует run.log"""
        safe_print(colored("\nАНАЛИЗ СИСТЕМНОГО ЛОГА", Colors.BLUE, bold=True))
        safe_print("-" * 80)

        run_log = self.logs_dir / "run.log"
        if not run_log.exists():
            safe_print(colored("ERROR: Файл run.log не найден", Colors.RED))
            return

        safe_print(f"Файл: {colored('run.log', Colors.CYAN)}")
        safe_print(
            f"Размер: {colored(format_size(run_log.stat().st_size), Colors.CYAN)}"
        )

        analyzer = RunLogAnalyzer(run_log)
        if not analyzer.analyze():
            return

        self.run_analyzer = analyzer
        stats = analyzer.stats

        safe_print("\nСТАТИСТИКА:")
        safe_print(f"   Ошибки: {colored(str(len(stats['errors'])), Colors.RED)}")
        safe_print(
            f"   Предупреждения: {colored(str(len(stats['warnings'])), Colors.YELLOW)}"
        )
        safe_print(
            f"   QML события: {colored(str(len(stats['qml_events'])), Colors.CYAN)}"
        )

        if stats["startup_time"] and stats["shutdown_time"]:
            safe_print("\nВРЕМЯ СЕССИИ:")
            safe_print(f"   Запуск: {colored(stats['startup_time'], Colors.GREEN)}")
            safe_print(
                f"   Завершение: {colored(stats['shutdown_time'], Colors.GREEN)}"
            )

        if stats["errors"]:
            safe_print("\nПОСЛЕДНИЕ ОШИБКИ:")
            for error in stats["errors"][-3:]:
                safe_print(f"   {colored(error[:70], Colors.RED)}")

        if stats["warnings"]:
            safe_print("\nПОСЛЕДНИЕ ПРЕДУПРЕЖДЕНИЯ:")
            for warning in stats["warnings"][-3:]:
                safe_print(f"   {colored(warning[:70], Colors.YELLOW)}")

    def _generate_summary(self):
        """Генерирует итоговый отчёт"""
        safe_print(colored("\n" + "=" * 80, Colors.CYAN, bold=True))
        safe_print(colored("ИТОГОВЫЙ ОТЧЁТ", Colors.CYAN, bold=True))
        safe_print(colored("=" * 80, Colors.CYAN, bold=True))

        if self.graphics_analyzer:
            sync_rate = self.graphics_analyzer.get_sync_rate()
            total = self.graphics_analyzer.stats["total"]

            safe_print("\nГРАФИКА:")
            safe_print(f"   События: {colored(str(total), Colors.GREEN, bold=True)}")
            safe_print(
                f"   Синхронизация: {colored(f'{sync_rate:.1f}%', Colors.GREEN if sync_rate >= 90 else Colors.YELLOW)}"
            )

            # Оценка
            if sync_rate >= 95:
                rating = colored("ОТЛИЧНО", Colors.GREEN, bold=True)
            elif sync_rate >= 85:
                rating = colored("ХОРОШО", Colors.GREEN)
            elif sync_rate >= 70:
                rating = colored("УДОВЛЕТВОРИТЕЛЬНО", Colors.YELLOW)
            else:
                rating = colored("ТРЕБУЕТ ВНИМАНИЯ", Colors.RED)

            safe_print(f"   Оценка: {rating}")

        if self.ibl_analyzer:
            total = self.ibl_analyzer.stats["total"]
            errors = len(self.ibl_analyzer.stats["errors"])

            safe_print("\nIBL:")
            safe_print(f"   События: {colored(str(total), Colors.CYAN)}")
            safe_print(
                f"   Ошибки: {colored(str(errors), Colors.RED if errors > 0 else Colors.GREEN)}"
            )

        if self.run_analyzer:
            errors = len(self.run_analyzer.stats["errors"])
            warnings = len(self.run_analyzer.stats["warnings"])

            safe_print("\nСИСТЕМА:")
            safe_print(
                f"   Ошибки: {colored(str(errors), Colors.RED if errors > 0 else Colors.GREEN)}"
            )
            safe_print(
                f"   Предупреждения: {colored(str(warnings), Colors.YELLOW if warnings > 0 else Colors.GREEN)}"
            )

        if self.error_analyzer:
            total = self.error_analyzer.stats["total"]
            safe_print("\nГЛОБАЛЬНЫЕ ОШИБКИ:")
            safe_print(
                f"   Записей: {colored(str(total), Colors.RED if total else Colors.GREEN, bold=True)}"
            )
            top_types = self.error_analyzer.get_top_types(limit=3)
            if top_types:
                formatted = ", ".join(
                    f"{err_type}×{count}" for err_type, count in top_types
                )
                safe_print(f"   Топ типы: {colored(formatted, Colors.MAGENTA)}")
            recent = self.error_analyzer.get_recent(limit=1)
            if recent:
                preview = recent[-1]
                message = preview.get("message", "")
                safe_print(f"   Последняя: {colored(message[:120], Colors.RED)}")

    def _generate_recommendations(self):
        """Генерирует рекомендации"""
        safe_print(colored("\nРЕКОМЕНДАЦИИ:", Colors.MAGENTA, bold=True))
        safe_print("-" * 80)

        recommendations = []

        if self.graphics_analyzer:
            sync_rate = self.graphics_analyzer.get_sync_rate()
            pending = self.graphics_analyzer.stats["pending"]

            if sync_rate < 95:
                recommendations.append(
                    "Синхронизация < 95%: Проверьте QML функции applyXxxUpdates()"
                )

            if pending > 100:
                recommendations.append(
                    f"{pending} ожидающих событий: Добавьте debounce для быстро меняющихся параметров"
                )

        if self.ibl_analyzer:
            errors = self.ibl_analyzer.stats["errors"]
            if errors:
                recommendations.append(
                    f"{len(errors)} IBL ошибок: Проверьте пути к HDR файлам"
                )

        if self.run_analyzer:
            errors = self.run_analyzer.stats["errors"]
            warnings = self.run_analyzer.stats["warnings"]

            if errors:
                recommendations.append(
                    f"{len(errors)} системных ошибок: Проверьте logs/run.log"
                )

            if len(warnings) > 10:
                recommendations.append(
                    f"{len(warnings)} предупреждений: Рассмотрите возможные проблемы"
                )

        if self.error_analyzer:
            total = self.error_analyzer.stats["total"]
            if total:
                last_error = self.error_analyzer.get_recent(limit=1)[-1]
                err_type = last_error.get("type", "Ошибка")
                recommendations.append(
                    f"{total} критических событий ({err_type}): изучите {self.error_analyzer.log_file.name}"
                )

        if not recommendations:
            safe_print(
                colored(
                    "   Всё работает отлично! Проблем не обнаружено.",
                    Colors.GREEN,
                    bold=True,
                )
            )
        else:
            for i, rec in enumerate(recommendations, 1):
                safe_print(f"   {i}. {rec}")

        safe_print(colored("\n" + "=" * 80 + "\n", Colors.CYAN))


# ============================================================================
# ЭКСПОРТНЫЕ ФУНКЦИИ ДЛЯ APP.PY
# ============================================================================


def analyze_all_logs() -> bool:
    """
    Анализирует все логи - вызывается из app.py

    Returns:
        bool: True если анализ успешен и нет критических проблем
    """
    try:
        analyzer = LogAnalyzer()
        analyzer.run()

        # Проверяем наличие критических проблем
        has_critical_issues = False

        if analyzer.graphics_analyzer:
            sync_rate = analyzer.graphics_analyzer.get_sync_rate()
            if sync_rate < 70:
                has_critical_issues = True

        if analyzer.run_analyzer:
            errors = len(analyzer.run_analyzer.stats["errors"])
            if errors > 10:
                has_critical_issues = True

        if analyzer.error_analyzer:
            if analyzer.error_analyzer.stats["total"] > 0:
                has_critical_issues = True

        return not has_critical_issues

    except Exception as e:
        print(f"❌ Ошибка анализа логов: {e}")
        return False


def analyze_graphics_sync() -> bool:
    """
    Анализирует синхронизацию графики - вызывается из app.py

    Returns:
        bool: True если синхронизация работает нормально
    """
    try:
        logs_dir = Path("logs")
        graphics_dir = logs_dir / "graphics"

        if not graphics_dir.exists():
            print("⚠️  Директория graphics логов не найдена")
            return False

        latest = find_latest_log(graphics_dir, "session_*.jsonl")
        if not latest:
            print("⚠️  Файлы графических логов не найдены")
            return False

        analyzer = GraphicsLogAnalyzer(latest)
        if not analyzer.load_events():
            return False

        analyzer.analyze()
        sync_rate = analyzer.get_sync_rate()

        print(f"📊 Синхронизация графики: {sync_rate:.1f}%")

        if sync_rate >= 95:
            print("✅ Отлично - синхронизация работает идеально")
            return True
        elif sync_rate >= 80:
            print("⚠️  Хорошо - небольшие проблемы синхронизации")
            return True
        else:
            print("❌ Требует внимания - проблемы синхронизации")
            return False

    except Exception as e:
        print(f"❌ Ошибка анализа синхронизации: {e}")
        return False


def analyze_user_session() -> bool:
    """
    Анализирует пользовательскую сессию - вызывается из app.py

    Returns:
        bool: True если сессия прошла без критических проблем
    """
    try:
        logs_dir = Path("logs")
        run_log = logs_dir / "run.log"

        if not run_log.exists():
            print("⚠️  Системный лог не найден")
            return False

        analyzer = RunLogAnalyzer(run_log)
        if not analyzer.analyze():
            return False

        errors = len(analyzer.stats["errors"])
        warnings = len(analyzer.stats["warnings"])

        print(f"📝 Сессия: {errors} ошибок, {warnings} предупреждений")

        if errors == 0:
            print("✅ Отлично - сессия без ошибок")
            return True
        elif errors <= 3:
            print("⚠️  Хорошо - несколько незначительных ошибок")
            return True
        else:
            print("❌ Требует внимания - множественные ошибки")
            return False

    except Exception as e:
        print(f"❌ Ошибка анализа сессии: {e}")
        return False


def main():
    """Главная функция"""
    analyzer = LogAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()
