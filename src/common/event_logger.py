"""
Unified Event Logger for Python↔QML sync analysis
Tracks ALL events that should affect scene rendering
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum, auto


class EventType(Enum):
    """Типы событий для трекинга"""
    # Python events
    USER_CLICK = auto()          # Клик пользователя на UI элемент
    USER_SLIDER = auto()         # ✅ НОВОЕ: Изменение слайдера
    USER_COMBO = auto()          # ✅ НОВОЕ: Выбор в комбобоксе
    USER_COLOR = auto()          # ✅ НОВОЕ: Выбор цвета
    STATE_CHANGE = auto()        # Изменение state в Python
    SIGNAL_EMIT = auto()         # Вызов .emit() сигнала
    QML_INVOKE = auto()          # QMetaObject.invokeMethod
    
    # QML events
    SIGNAL_RECEIVED = auto()     # QML получил сигнал (onXxxChanged)
    FUNCTION_CALLED = auto()     # QML функция вызвана
    PROPERTY_CHANGED = auto()    # QML property изменилось
    
    # ✅ НОВОЕ: Mouse events in QML
    MOUSE_PRESS = auto()         # Нажатие мыши на канве
    MOUSE_DRAG = auto()          # Перетаскивание
    MOUSE_WHEEL = auto()         # Прокрутка колесика (zoom)
    MOUSE_RELEASE = auto()       # Отпускание мыши
    
    # Errors
    PYTHON_ERROR = auto()        # Ошибка в Python
    QML_ERROR = auto()           # Ошибка в QML


class EventLogger:
    """Singleton логгер для отслеживания Python↔QML событий"""
    
    _instance: Optional['EventLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EventLogger._initialized:
            return
        
        self.logger = logging.getLogger("EventLogger")
        self.events: list[Dict[str, Any]] = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        EventLogger._initialized = True
    
    def log_event(
        self,
        event_type: EventType,
        component: str,
        action: str,
        *,
        old_value: Any = None,
        new_value: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "python"
    ) -> None:
        """
        Логирование события
        
        Args:
            event_type: Тип события
            component: Компонент (panel_graphics, main.qml, etc.)
            action: Описание действия
            old_value: Старое значение (если применимо)
            new_value: Новое значение (если применимо)
            metadata: Дополнительные данные
            source: Источник ("python" или "qml")
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "event_type": event_type.name,
            "source": source,
            "component": component,
            "action": action,
            "old_value": self._serialize_value(old_value),
            "new_value": self._serialize_value(new_value),
            "metadata": metadata or {}
        }
        
        self.events.append(event)
        
        # Логируем в файл
        self.logger.info(
            f"[{event_type.name}] {component}.{action}: "
            f"{old_value} → {new_value}"
        )
    
    def log_user_click(
        self,
        widget_name: str,
        widget_type: str,
        value: Any,
        **metadata
    ) -> None:
        """Логирование клика пользователя"""
        self.log_event(
            EventType.USER_CLICK,
            component="panel_graphics",
            action=f"click_{widget_name}",
            new_value=value,
            metadata={"widget_type": widget_type, **metadata}
        )
    
    # ✅ НОВОЕ: Логирование слайдера
    def log_user_slider(
        self,
        slider_name: str,
        old_value: float,
        new_value: float,
        **metadata
    ) -> None:
        """Логирование изменения слайдера"""
        self.log_event(
            EventType.USER_SLIDER,
            component="panel_graphics",
            action=f"slider_{slider_name}",
            old_value=old_value,
            new_value=new_value,
            metadata={"widget_type": "LabeledSlider", **metadata}
        )
    
    # ✅ НОВОЕ: Логирование комбобокса
    def log_user_combo(
        self,
        combo_name: str,
        old_value: str,
        new_value: str,
        **metadata
    ) -> None:
        """Логирование выбора в комбобоксе"""
        self.log_event(
            EventType.USER_COMBO,
            component="panel_graphics",
            action=f"combo_{combo_name}",
            old_value=old_value,
            new_value=new_value,
            metadata={"widget_type": "QComboBox", **metadata}
        )
    
    # ✅ НОВОЕ: Логирование выбора цвета
    def log_user_color(
        self,
        color_name: str,
        old_color: str,
        new_color: str,
        **metadata
    ) -> None:
        """Логирование выбора цвета"""
        self.log_event(
            EventType.USER_COLOR,
            component="panel_graphics",
            action=f"color_{color_name}",
            old_value=old_color,
            new_value=new_color,
            metadata={"widget_type": "ColorButton", **metadata}
        )
    
    def log_state_change(
        self,
        category: str,
        parameter: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Логирование изменения state"""
        self.log_event(
            EventType.STATE_CHANGE,
            component=f"state.{category}",
            action=parameter,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_signal_emit(
        self,
        signal_name: str,
        payload: Dict[str, Any]
    ) -> None:
        """Логирование вызова .emit()"""
        self.log_event(
            EventType.SIGNAL_EMIT,
            component="panel_graphics",
            action=f"emit_{signal_name}",
            new_value=payload
        )
    
    def log_qml_invoke(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> None:
        """Логирование QMetaObject.invokeMethod"""
        self.log_event(
            EventType.QML_INVOKE,
            component="qml_bridge",
            action=function_name,
            new_value=arguments
        )
    
    def log_qml_signal_received(
        self,
        signal_name: str,
        qml_component: str
    ) -> None:
        """Логирование получения сигнала в QML"""
        self.log_event(
            EventType.SIGNAL_RECEIVED,
            component=qml_component,
            action=f"on{signal_name}Changed",
            source="qml"
        )
    
    def log_qml_function_called(
        self,
        function_name: str,
        qml_component: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логирование вызова QML функции"""
        self.log_event(
            EventType.FUNCTION_CALLED,
            component=qml_component,
            action=function_name,
            new_value=arguments,
            source="qml"
        )
    
    def log_qml_property_changed(
        self,
        property_name: str,
        qml_component: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Логирование изменения QML property"""
        self.log_event(
            EventType.PROPERTY_CHANGED,
            component=qml_component,
            action=property_name,
            old_value=old_value,
            new_value=new_value,
            source="qml"
        )
    
    # ✅ НОВОЕ: Логирование мыши
    def log_mouse_press(
        self,
        x: float,
        y: float,
        button: str,
        **metadata
    ) -> None:
        """Логирование нажатия мыши на канве"""
        self.log_event(
            EventType.MOUSE_PRESS,
            component="main.qml",
            action="mouse_press",
            new_value={"x": x, "y": y, "button": button},
            metadata=metadata,
            source="qml"
        )
    
    def log_mouse_drag(
        self,
        delta_x: float,
        delta_y: float,
        **metadata
    ) -> None:
        """Логирование перетаскивания"""
        self.log_event(
            EventType.MOUSE_DRAG,
            component="main.qml",
            action="mouse_drag",
            new_value={"delta_x": delta_x, "delta_y": delta_y},
            metadata=metadata,
            source="qml"
        )
    
    def log_mouse_wheel(
        self,
        delta: float,
        **metadata
    ) -> None:
        """Логирование прокрутки колесика (zoom)"""
        self.log_event(
            EventType.MOUSE_WHEEL,
            component="main.qml",
            action="mouse_wheel",
            new_value={"delta": delta},
            metadata=metadata,
            source="qml"
        )
    
    def log_error(
        self,
        error_msg: str,
        source: str = "python",
        **metadata
    ) -> None:
        """Логирование ошибки"""
        event_type = EventType.PYTHON_ERROR if source == "python" else EventType.QML_ERROR
        self.log_event(
            event_type,
            component=metadata.get("component", "unknown"),
            action="error",
            new_value=error_msg,
            metadata=metadata,
            source=source
        )
    
    def export_events(self, output_dir: Path | str = "logs") -> Path:
        """Экспорт событий в JSON"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"events_{self._session_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Events exported to: {output_file}")
        return output_file
    
    def get_python_qml_pairs(self) -> list[Dict[str, Any]]:
        """Найти пары Python→QML событий для анализа синхронизации"""
        pairs = []
        
        # Группируем по timestamp
        for i, event in enumerate(self.events):
            if event["event_type"] == "SIGNAL_EMIT":
                # Ищем соответствующий SIGNAL_RECEIVED в QML
                signal_name = event["action"].replace("emit_", "")
                
                # Ищем в следующих 1000ms
                emit_time = datetime.fromisoformat(event["timestamp"])
                
                for j in range(i+1, len(self.events)):
                    next_event = self.events[j]
                    recv_time = datetime.fromisoformat(next_event["timestamp"])
                    
                    if (recv_time - emit_time).total_seconds() > 1.0:
                        break  # Слишком поздно
                    
                    if (next_event["event_type"] == "SIGNAL_RECEIVED" and
                        signal_name in next_event["action"]):
                        
                        pairs.append({
                            "python_event": event,
                            "qml_event": next_event,
                            "latency_ms": (recv_time - emit_time).total_seconds() * 1000,
                            "status": "synced"
                        })
                        break
                else:
                    # Не нашли соответствующий QML event
                    pairs.append({
                        "python_event": event,
                        "qml_event": None,
                        "latency_ms": None,
                        "status": "missing_qml"
                    })
        
        return pairs
    
    def analyze_sync(self) -> Dict[str, Any]:
        """Анализ синхронизации Python↔QML"""
        pairs = self.get_python_qml_pairs()
        
        total = len(pairs)
        synced = sum(1 for p in pairs if p["status"] == "synced")
        missing = sum(1 for p in pairs if p["status"] == "missing_qml")
        
        latencies = [p["latency_ms"] for p in pairs if p["latency_ms"] is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "total_signals": total,
            "synced": synced,
            "missing_qml": missing,
            "sync_rate": (synced / total * 100) if total > 0 else 0,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max(latencies) if latencies else 0,
            "pairs": pairs
        }
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Сериализация значений для JSON"""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {k: EventLogger._serialize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [EventLogger._serialize_value(v) for v in value]
        return str(value)


# Singleton instance
_event_logger = EventLogger()

def get_event_logger() -> EventLogger:
    """Получить singleton instance EventLogger"""
    return _event_logger
