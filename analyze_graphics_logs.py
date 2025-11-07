#!/usr/bin/env python
"""
Утилита анализа логов графических изменений
Позволяет анализировать сохраненные сессии логирования
"""

import json
import sys
from pathlib import Path
from typing import Any
from collections import defaultdict


class LogAnalyzer:
    """Анализатор логов графических изменений"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events: list[dict[str, Any]] = []
        self.session_info: dict[str, Any] = {}
        self.load_log()

    def load_log(self):
        """Загрузить лог из файла"""
        if not self.log_file.exists():
            print(f"❌ Файл не найден: {self.log_file}")
            return

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())

                    if event.get("event_type") == "session_start":
                        self.session_info = event
                    elif event.get("event_type") in (
                        "parameter_change",
                        "parameter_update",
                    ):
                        self.events.append(event)
                    elif event.get("event_type") == "session_end":
                        self.session_info.update(event.get("stats", {}))
                except json.JSONDecodeError as e:
                    print(f"⚠️ Ошибка парсинга строки: {e}")

        print(f"✅ Загружено {len(self.events)} событий из {self.log_file.name}")

    def print_summary(self):
        """Вывести краткую статистику"""
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        if "session_id" in self.session_info:
            print(f"Session ID: {self.session_info['session_id']}")
        if "timestamp" in self.session_info:
            print(f"Started: {self.session_info['timestamp']}")

        print(f"Total events: {len(self.events)}")

        # Группируем по категориям
        by_category = defaultdict(int)
        for event in self.events:
            category = event.get("category", "unknown")
            by_category[category] += 1

        print("\nBy category:")
        for cat, count in sorted(by_category.items()):
            print(f"  {cat}: {count} events")

        # QML sync
        with_qml = sum(1 for e in self.events if e.get("qml_state"))
        successful = sum(1 for e in self.events if e.get("applied_to_qml"))
        failed = sum(1 for e in self.events if e.get("error"))

        print("\nQML Synchronization:")
        print(f"  With QML update: {with_qml}/{len(self.events)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        if len(self.events) > 0:
            print(f"  Sync rate: {(successful / len(self.events) * 100):.1f}%")

        print("=" * 60 + "\n")

    def print_timeline(self, limit: int = 20):
        """Вывести временную шкалу изменений"""
        print(f"⏱️  TIMELINE (последние {min(limit, len(self.events))})")
        print("-" * 60)

        for event in self.events[-limit:]:
            ts = event.get("timestamp", "N/A")
            param = event.get("parameter_name", "N/A")
            old = event.get("old_value")
            new = event.get("new_value")
            category = event.get("category", "N/A")
            applied = event.get("applied_to_qml", False)
            error = event.get("error")

            status = "✅" if applied else ("❌" if error else "⏳")

            print(f"{status} [{ts}] {category}.{param}")
            print(f"   {old} → {new}")
            if error:
                print(f"   ⚠️ Error: {error}")
            print()

        print("-" * 60 + "\n")

    def analyze_errors(self):
        """Анализ ошибок"""
        errors = [e for e in self.events if e.get("error")]

        if not errors:
            print("✅ Ошибок не обнаружено\n")
            return

        print(f"⚠️  ERRORS ANALYSIS ({len(errors)} errors)")
        print("-" * 60)

        # Группируем по параметрам
        by_param = defaultdict(list)
        for event in errors:
            param = event.get("parameter_name")
            error = event.get("error")
            by_param[param].append(error)

        for param, error_list in sorted(by_param.items()):
            print(f"\n{param}:")
            for i, error in enumerate(error_list, 1):
                print(f"  {i}. {error}")

        print("-" * 60 + "\n")

    def analyze_patterns(self):
        """Анализ паттернов изменений"""
        print("🔍 PATTERN ANALYSIS")
        print("-" * 60)

        # Самые часто меняемые параметры
        param_counts = defaultdict(int)
        for event in self.events:
            param = event.get("parameter_name")
            param_counts[param] += 1

        print("\nМост frequently changed parameters:")
        for param, count in sorted(
            param_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {param}: {count} changes")

        # Параметры без QML синхронизации
        no_sync = []
        for event in self.events:
            if not event.get("qml_state") and not event.get("applied_to_qml"):
                no_sync.append(event.get("parameter_name"))

        if no_sync:
            print(f"\n⚠️ Parameters without QML sync ({len(set(no_sync))} unique):")
            for param in sorted(set(no_sync)):
                count = no_sync.count(param)
                print(f"  {param}: {count} times")

        print("-" * 60 + "\n")

    def export_csv(self, output_file: Path):
        """Экспортировать в CSV для анализа в Excel"""
        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "timestamp",
                "category",
                "parameter_name",
                "old_value",
                "new_value",
                "applied_to_qml",
                "error",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for event in self.events:
                row = {k: event.get(k, "") for k in fieldnames}
                writer.writerow(row)

        print(f"📄 Экспортировано в CSV: {output_file}\n")

    def compare_panel_qml_states(self):
        """Сравнить состояния панели и QML"""
        print("🔄 PANEL ↔ QML STATE COMPARISON")
        print("-" * 60)

        # Берем последнее событие с QML состоянием
        last_with_qml = None
        for event in reversed(self.events):
            if event.get("qml_state"):
                last_with_qml = event
                break

        if not last_with_qml:
            print("⚠️ Нет событий с QML состоянием\n")
            return

        panel_state = last_with_qml.get("panel_state", {})
        qml_state = last_with_qml.get("qml_state", {})

        print(f"Last event with QML state: {last_with_qml.get('timestamp')}")
        print(f"Parameter: {last_with_qml.get('parameter_name')}")
        print(f"\nPanel state keys: {len(panel_state)}")
        print(f"QML state keys: {len(qml_state)}")
        print("-" * 60 + "\n")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_graphics_logs.py <log_file.jsonl>")
        print("\nДоступные логи:")

        log_dir = Path("logs/graphics")
        if log_dir.exists():
            for log_file in sorted(log_dir.glob("session_*.jsonl")):
                print(f"  {log_file}")
        else:
            print("  (нет логов в logs/graphics/)")

        return

    log_file = Path(sys.argv[1])
    analyzer = LogAnalyzer(log_file)

    if not analyzer.events:
        print("❌ Нет событий для анализа")
        return

    # Выполняем все анализы
    analyzer.print_summary()
    analyzer.print_timeline(limit=15)
    analyzer.analyze_errors()
    analyzer.analyze_patterns()
    analyzer.compare_panel_qml_states()

    # Экспорт в CSV
    if "--csv" in sys.argv or "-c" in sys.argv:
        csv_file = log_file.with_suffix(".csv")
        analyzer.export_csv(csv_file)

    print("💡 Tip: используйте --csv для экспорта в CSV")


if __name__ == "__main__":
    main()
