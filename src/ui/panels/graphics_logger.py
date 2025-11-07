"""
Модуль логирования изменений графических параметров
Записывает все изменения на панели графики и их соответствия в QML
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict
from collections import deque


@dataclass
class GraphicsChangeEvent:
    """Событие изменения графического параметра"""

    timestamp: str
    parameter_name: str
    old_value: Any
    new_value: Any
    category: str  # lighting, material, environment, quality, camera, effects
    panel_state: dict[str, Any]
    qml_state: dict[str, Any] | None = None
    applied_to_qml: bool = False
    error: str | None = None


class GraphicsLogger:
    """Логгер для записи изменений графических параметров"""

    def __init__(self, log_dir: Path = Path("logs/graphics")):
        """
        Args:
            log_dir: Директория для сохранения логов
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Буфер событий (последние 1000 изменений)
        self.events_buffer: deque[GraphicsChangeEvent] = deque(maxlen=1000)

        # Текущая сессия
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log_file = self.log_dir / f"session_{self.session_id}.jsonl"

        # Счетчики для статистики
        self.stats = {
            "total_changes": 0,
            "successful_qml_updates": 0,
            "failed_qml_updates": 0,
            "by_category": {},
        }

        self.logger = logging.getLogger(__name__)

        # Создаем заголовок сессии
        self._write_session_header()

    def _write_session_header(self):
        """Записать заголовок сессии логирования"""
        header = {
            "event_type": "session_start",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }

        with open(self.session_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(header, ensure_ascii=False) + "\n")

    def log_change(
        self,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
        category: str,
        panel_state: dict[str, Any],
        qml_state: dict[str, Any] | None = None,
        applied_to_qml: bool = False,
        error: str | None = None,
    ) -> GraphicsChangeEvent:
        """
        Записать изменение параметра на панели

        Args:
            parameter_name: Имя параметра
            old_value: Старое значение
            new_value: Новое значение
            category: Категория (lighting, material и т.д.)
            panel_state: Полное состояние панели графики

        Returns:
            Объект события изменения
        """
        event = GraphicsChangeEvent(
            timestamp=datetime.now().isoformat(),
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            category=category,
            panel_state=panel_state.copy(),
        )
        # Применяем дополнительную информацию о QML при наличии
        if qml_state is not None:
            event.qml_state = qml_state
        event.applied_to_qml = applied_to_qml
        event.error = error

        # Добавляем в буфер
        self.events_buffer.append(event)

        # Обновляем статистику
        self.stats["total_changes"] += 1
        if applied_to_qml:
            self.stats["successful_qml_updates"] += 1
        if error:
            self.stats["failed_qml_updates"] += 1
        if category not in self.stats["by_category"]:
            self.stats["by_category"][category] = 0
        self.stats["by_category"][category] += 1

        # Записываем в файл
        # Если у нас уже есть QML информация — отмечаем как update
        self._write_event_to_file(
            event, update=bool(qml_state or applied_to_qml or error)
        )

        # Раньше здесь был шумный вывод в консоль: "📊 GRAPHICS CHANGE: ..."
        # Удалено по просьбе пользователя. Все изменения пишутся в файл лога.
        # self.logger.debug(f"GRAPHICS CHANGE: {category}.{parameter_name}: {old_value} → {new_value}")

        return event

    def log_qml_update(
        self,
        event: GraphicsChangeEvent,
        qml_state: dict[str, Any] | None = None,
        success: bool = True,
        error: str | None = None,
    ):
        """
        Записать результат применения изменения в QML

        Args:
            event: Событие изменения
            qml_state: Состояние QML после изменения
            success: Успешно ли применено
            error: Сообщение об ошибке
        """
        # Обновляем событие
        event.qml_state = qml_state
        event.applied_to_qml = success
        event.error = error

        # Обновляем статистику
        if success:
            self.stats["successful_qml_updates"] += 1
        else:
            self.stats["failed_qml_updates"] += 1

        # Записываем обновленное событие
        self._write_event_to_file(event, update=True)

        # Сохраняем краткий вывод о результате (оставляем по умолчанию)
        if success:
            print(f"   ✅ QML updated: {event.parameter_name}")
        else:
            print(f"   ❌ QML update failed: {event.parameter_name} - {error}")

    def _write_event_to_file(self, event: GraphicsChangeEvent, update: bool = False):
        """Записать событие в файл лога"""
        event_dict = asdict(event)
        event_dict["event_type"] = "parameter_update" if update else "parameter_change"

        with open(self.session_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, ensure_ascii=False, default=str) + "\n")

    def get_changes_by_category(self, category: str) -> list[GraphicsChangeEvent]:
        """Получить все изменения по категории"""
        return [e for e in self.events_buffer if e.category == category]

    def get_recent_changes(self, count: int = 10) -> list[GraphicsChangeEvent]:
        """Получить последние N изменений"""
        return list(self.events_buffer)[-count:]

    def analyze_qml_sync(self) -> dict[str, Any]:
        """
        Анализировать синхронизацию Python-QML

        Returns:
            Словарь с результатами анализа
        """
        total = len(self.events_buffer)
        if total == 0:
            return {"status": "no_data", "message": "Нет записанных изменений"}

        # Считаем события с QML обновлениями
        with_qml = sum(1 for e in self.events_buffer if e.qml_state is not None)
        successful = sum(1 for e in self.events_buffer if e.applied_to_qml)
        failed = sum(1 for e in self.events_buffer if e.error is not None)

        # Группируем ошибки
        errors_by_param = {}
        for event in self.events_buffer:
            if event.error:
                if event.parameter_name not in errors_by_param:
                    errors_by_param[event.parameter_name] = []
                errors_by_param[event.parameter_name].append(event.error)

        # Группируем по категориям
        by_category = {}
        for event in self.events_buffer:
            cat = event.category
            if cat not in by_category:
                by_category[cat] = {
                    "total": 0,
                    "with_qml": 0,
                    "successful": 0,
                    "failed": 0,
                }

            by_category[cat]["total"] += 1
            if event.qml_state is not None:
                by_category[cat]["with_qml"] += 1
            if event.applied_to_qml:
                by_category[cat]["successful"] += 1
            if event.error:
                by_category[cat]["failed"] += 1

        return {
            "status": "ok",
            "total_events": total,
            "with_qml_update": with_qml,
            "successful_updates": successful,
            "failed_updates": failed,
            "sync_rate": (successful / total * 100) if total > 0 else 0,
            "by_category": by_category,
            "errors_by_parameter": errors_by_param,
            "stats": self.stats,
        }

    def export_analysis_report(self, output_file: Path | None = None) -> Path:
        """
        Экспортировать отчет анализа в JSON

        Args:
            output_file: Путь для сохранения (None - автоматический)

        Returns:
            Путь к сохраненному файлу
        """
        if output_file is None:
            output_file = self.log_dir / f"analysis_{self.session_id}.json"

        analysis = self.analyze_qml_sync()

        # Добавляем примеры изменений
        analysis["recent_changes"] = [
            {
                "timestamp": e.timestamp,
                "parameter": e.parameter_name,
                "category": e.category,
                "old": e.old_value,
                "new": e.new_value,
                "qml_applied": e.applied_to_qml,
                "error": e.error,
            }
            for e in self.get_recent_changes(20)
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        print(f"📄 Отчет анализа сохранен: {output_file}")
        return output_file

    def compare_states(
        self, panel_state: dict[str, Any], qml_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Сравнить состояния панели и QML

        Args:
            panel_state: Состояние панели графики
            qml_state: Состояние QML сцены

        Returns:
            Словарь с различиями
        """
        differences = {
            "matching": [],
            "mismatched": [],
            "only_in_panel": [],
            "only_in_qml": [],
        }

        # Проверяем каждый параметр панели
        for key, panel_value in panel_state.items():
            if key in qml_state:
                qml_value = qml_state[key]
                if panel_value == qml_value:
                    differences["matching"].append(key)
                else:
                    mismatch = {
                        "parameter": key,
                        "panel_value": panel_value,
                        "qml_value": qml_value,
                    }
                    differences["mismatched"].append(mismatch)
            else:
                differences["only_in_panel"].append(key)

        # Параметры только в QML
        for key in qml_state:
            if key not in panel_state:
                differences["only_in_qml"].append(key)

        return differences

    def close_session(self):
        """Завершить текущую сессию логирования"""
        # Записываем финальную статистику
        footer = {
            "event_type": "session_end",
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "analysis": self.analyze_qml_sync(),
        }

        with open(self.session_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(footer, ensure_ascii=False, indent=2) + "\n")

        # Экспортируем финальный отчет
        self.export_analysis_report()

        print(f"📊 Сессия логирования завершена: {self.session_log_file}")
        print(f"   Всего изменений: {self.stats['total_changes']}")
        print(f"   Успешных QML обновлений: {self.stats['successful_qml_updates']}")
        print(f"   Неудачных QML обновлений: {self.stats['failed_qml_updates']}")

    # ------------------------------------------------------------------
    # Помощники для массовой отметки применённых изменений
    # ------------------------------------------------------------------
    def mark_category_changes_applied(
        self, category: str, since_timestamp: str | int | float | None = None
    ) -> int:
        """Отметить все события типа parameter_change в указанной категории как применённые (успешные).

        Args:
            category: Имя категории (lighting/materials/environment/quality/camera/effects/geometry)
            since_timestamp: Необязательный ISO-временной порог (включительно)

        Returns:
            Количество помеченных событий
        """
        marked = 0
        threshold = self._coerce_timestamp(since_timestamp)

        # Идём по копии буфера, чтобы безопасно логировать обновления
        for e in list(self.events_buffer):
            try:
                if e.category != category:
                    continue
                if e.applied_to_qml:
                    continue

                event_timestamp = self._coerce_timestamp(e.timestamp)
                if (
                    threshold is not None
                    and event_timestamp is not None
                    and event_timestamp < threshold
                ):
                    continue

                # Пишем parameter_update и помечаем как success
                self.log_qml_update(e, qml_state={"applied": True}, success=True)
                marked += 1
            except Exception:
                # Не прерываем массовую отметку единичной ошибкой
                continue
        return marked

    def _coerce_timestamp(self, value: str | int | float | None) -> float | None:
        """Преобразовать различные форматы временных отметок к секундам."""

        if value is None:
            return None

        # Числовые значения (миллисекунды или секунды)
        if isinstance(value, (int, float)):
            numeric = float(value)
            # Date.now() возвращает миллисекунды — нормализуем к секундам
            if numeric > 1e11:  # ~ 1973 год в миллисекундах
                return numeric / 1000.0
            return numeric

        # Пытаемся разобрать ISO-строку
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None

            try:
                return datetime.fromisoformat(stripped).timestamp()
            except ValueError:
                # Возможно, строка — число в текстовом виде
                try:
                    numeric = float(stripped)
                except ValueError:
                    return None
                if numeric > 1e11:
                    return numeric / 1000.0
                return numeric

        return None


# Глобальный экземпляр логгера
_graphics_logger: GraphicsLogger | None = None


def get_graphics_logger() -> GraphicsLogger:
    """Получить глобальный экземпляр логгера графики"""
    global _graphics_logger
    if _graphics_logger is None:
        _graphics_logger = GraphicsLogger()
    return _graphics_logger


def close_graphics_logger():
    """Закрыть текущую сессию логирования"""
    global _graphics_logger
    if _graphics_logger is not None:
        _graphics_logger.close_session()
        _graphics_logger = None
