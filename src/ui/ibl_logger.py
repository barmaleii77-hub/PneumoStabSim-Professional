"""
IBL Signal Logger - Система записи логов сигналов IBL в файл для анализа.

Этот модуль принимает события из QML IblProbeLoader и записывает их в файл
для последующего анализа прохождения сигналов через систему.
"""

import os
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Slot


class IblSignalLogger(QObject):
    """
    Логгер для записи событий IBL loader в файл.
    
    Записывает все события загрузки HDR текстур, смены источников,
    fallback переключений и ошибок в timestamped лог-файл.
    """
    
    def __init__(self, log_dir: str = "logs/ibl"):
        super().__init__()
        
        # Создаем директорию для логов
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"ibl_signals_{timestamp}.log"
        
        # Инициализируем файл
        self._init_log_file()
        
    def _init_log_file(self):
        """Создает файл и записывает заголовок."""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("IBL SIGNAL LOGGER - Signal Flow Analysis\n")
            f.write(f"Log started: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            f.write("FORMAT: timestamp | level | source | message\n")
            f.write("-" * 80 + "\n\n")
        
        print(f"📝 IBL Logger: Writing to {self.log_file}")
    
    @Slot(str)
    def logIblEvent(self, message: str):
        """
        Принимает событие из QML и записывает в файл.
        
        Args:
            message: Сообщение с форматом "timestamp | level | source | message"
        """
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
                f.flush()  # Немедленная запись
        except Exception as e:
            print(f"❌ IBL Logger ERROR: {e}")
    
    def log_python_event(self, level: str, source: str, message: str):
        """
        Записывает событие из Python кода.
        
        Args:
            level: Уровень (INFO, WARN, ERROR, SUCCESS)
            source: Источник события (например, "MainWindow", "GraphicsPanel")
            message: Описание события
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {level} | {source} | {message}"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
                f.flush()
        except Exception as e:
            print(f"❌ IBL Logger ERROR: {e}")
    
    def close(self):
        """Закрывает лог-файл с финальной записью."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write("\n" + "-" * 80 + "\n")
                f.write(f"Log closed: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")
            
            print(f"✅ IBL Logger: Closed {self.log_file}")
        except Exception as e:
            print(f"❌ IBL Logger close ERROR: {e}")


# Глобальный экземпляр для использования
_ibl_logger_instance = None


def get_ibl_logger() -> IblSignalLogger:
    """Получить глобальный экземпляр логгера (singleton)."""
    global _ibl_logger_instance
    if _ibl_logger_instance is None:
        _ibl_logger_instance = IblSignalLogger()
    return _ibl_logger_instance


def log_ibl_event(level: str, source: str, message: str):
    """
    Удобная функция для логирования из Python кода.
    
    Args:
        level: INFO, WARN, ERROR, SUCCESS
        source: Источник события
        message: Описание
    """
    logger = get_ibl_logger()
    logger.log_python_event(level, source, message)
