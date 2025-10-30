"""Инициализация конфигурационного пакета."""

from pathlib import Path

CONFIG_ROOT: Path = Path(__file__).resolve().parent
"""Корневая директория конфигурационных файлов."""

__all__ = ["CONFIG_ROOT"]
