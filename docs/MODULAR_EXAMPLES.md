# 💡 Примеры использования модульной архитектуры

## 📦 Примеры импорта

### Bootstrap модули

```python
# Настройка QtQuick3D окружения
from src.bootstrap.environment import setup_qtquick3d_environment

def my_log_error(msg: str):
    print(f"ERROR: {msg}")

success = setup_qtquick3d_environment(my_log_error)
if success:
    print("QtQuick3D настроен успешно")
```

```python
# Настройка Qt переменных среды
from src.bootstrap.environment import configure_qt_environment
import os

configure_qt_environment()

print(f"QSG_RHI_BACKEND: {os.environ.get('QSG_RHI_BACKEND')}")
# Windows: d3d11, Linux/macOS: opengl
```

```python
# Настройка терминала
from src.bootstrap.terminal import configure_terminal_encoding

def my_log_warning(msg: str):
    print(f"WARNING: {msg}")

configure_terminal_encoding(my_log_warning)
print("Терминал настроен на UTF-8 ✅")
```

```python
# Проверка версии Python
from src.bootstrap.version_check import check_python_compatibility
import sys

def my_log_warning(msg: str):
    print(f"WARNING: {msg}")

def my_log_error(msg: str):
    print(f"ERROR: {msg}")

try:
    check_python_compatibility(my_log_warning, my_log_error)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} OK ✅")
except SystemExit:
    print("Python версия не подходит ❌")
```

```python
# Безопасный импорт Qt
from src.bootstrap.qt_imports import safe_import_qt

QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(
    log_warning=lambda msg: print(f"WARNING: {msg}"),
    log_error=lambda msg: print(f"ERROR: {msg}")
)

print("Qt компоненты импортированы ✅")
```

---

## 🎮 CLI модули

```python
# Парсинг аргументов
from src.cli.arguments import parse_arguments

args = parse_arguments()

if args.test_mode:
    print("🧪 Тестовый режим активен")

if args.verbose:
    print("📢 Verbose режим активен")

if args.diag:
    print("🔍 Диагностика будет запущена после закрытия")
```

```python
# Кастомный парсер на основе существующего
import argparse
from src.cli.arguments import parse_arguments

# Базовые аргументы
base_args = parse_arguments()

# Добавляем свои аргументы
parser = argparse.ArgumentParser(parents=[])
parser.add_argument('--my-custom-arg', action='store_true')

custom_args = parser.parse_args()
print(f"Custom arg: {custom_args.my_custom_arg}")
```

---

## 🩺 Diagnostics модули

### Накопление warnings/errors

```python
from src.diagnostics.warnings import log_warning, log_error, print_warnings_errors

# Накапливаем предупреждения в процессе работы
log_warning("Не найден файл конфигурации, используем defaults")
log_warning("High DPI scaling может не работать")

# Накапливаем ошибки
log_error("PySide6 не установлен!")
log_error("Python версия < 3.13")

# В конце работы выводим всё разом
print_warnings_errors()
```

**Вывод**:
```
============================================================
⚠️  WARNINGS & ERRORS:
============================================================

⚠️  Warnings:
  • Не найден файл конфигурации, используем defaults
  • High DPI scaling может не работать

❌ Errors:
  • PySide6 не установлен!
  • Python версия < 3.13
============================================================
```

### Кастомный коллектор

```python
from src.diagnostics.warnings import WarningErrorCollector

# Создаём свой коллектор
my_collector = WarningErrorCollector()

my_collector.log_warning("Test warning")
my_collector.log_error("Test error")

# Выводим
my_collector.print_all()
```

### Диагностика логов

```python
from src.diagnostics.logs import run_log_diagnostics

# Запускаем полную диагностику
run_log_diagnostics()
```

---

## 🚀 ApplicationRunner

### Базовое использование

```python
from src.app_runner import ApplicationRunner
from src.cli.arguments import parse_arguments
from src.bootstrap.qt_imports import safe_import_qt
from src.diagnostics.warnings import log_warning, log_error

# Импортируем Qt компоненты
QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(
    log_warning, log_error
)

# Парсим аргументы
args = parse_arguments()

# Создаём runner
runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)

# Запускаем приложение
exit_code = runner.run(args)

print(f"Приложение завершено с кодом: {exit_code}")
```

### Кастомизация runner

```python
from src.app_runner import ApplicationRunner

class MyCustomRunner(ApplicationRunner):
    """Кастомный runner с дополнительной логикой."""

    def setup_logging(self, verbose_console: bool = False):
        """Переопределяем логирование."""
        logger = super().setup_logging(verbose_console)

        if logger:
            logger.info("🎨 Custom runner initialized")

        return logger

    def _print_header(self):
        """Кастомный заголовок."""
        print("=" * 60)
        print("🎨 MY CUSTOM APP v2.1.0")
        print("=" * 60)
        print("⏳ Starting...")

# Используем кастомный runner
runner = MyCustomRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
exit_code = runner.run(args)
```

### Доступ к экземплярам

```python
runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)

# После runner.run() доступны:
print(f"App instance: {runner.app_instance}")
print(f"Window instance: {runner.window_instance}")
print(f"Logger: {runner.app_logger}")
```

---

## 🔧 Интеграция в существующий код

### Минимальная интеграция

```python
# my_custom_app.py
import sys
from src.diagnostics.warnings import log_warning, log_error
from src.bootstrap.environment import configure_qt_environment
from src.bootstrap.terminal import configure_terminal_encoding

# Настройка окружения
configure_terminal_encoding(log_warning)
configure_qt_environment()

# Ваш код приложения
def main():
    print("Hello from custom app!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Полная интеграция

```python
# my_full_app.py
import sys
from src.diagnostics.warnings import log_warning, log_error, print_warnings_errors
from src.bootstrap import (
    setup_qtquick3d_environment,
    configure_qt_environment,
    configure_terminal_encoding,
    check_python_compatibility,
    safe_import_qt
)
from src.cli import parse_arguments

# Bootstrap
setup_qtquick3d_environment(log_error)
configure_terminal_encoding(log_warning)
check_python_compatibility(log_warning, log_error)
configure_qt_environment()

# Qt import
QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt(log_warning, log_error)

# CLI
args = parse_arguments()

def main():
    try:
        print("🚀 Starting custom app...")

        # Ваша логика

        return 0
    except Exception as e:
        log_error(f"Fatal error: {e}")
        return 1
    finally:
        print_warnings_errors()

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🧪 Тестирование

### Pytest примеры

```python
# tests/test_bootstrap.py
import pytest
import os
from src.bootstrap.environment import configure_qt_environment

def test_configure_qt_environment():
    """Тест настройки Qt переменных среды."""
    configure_qt_environment()

    # Проверяем, что переменные установлены
    assert "QSG_RHI_BACKEND" in os.environ
    assert "QT_LOGGING_RULES" in os.environ
    assert "PSS_DIAG" in os.environ

    # Проверяем значения
    backend = os.environ["QSG_RHI_BACKEND"]
    assert backend in ["d3d11", "opengl"]


def test_version_check():
    """Тест проверки версии Python."""
    import sys
    from src.bootstrap.version_check import check_python_compatibility

    warnings = []
    errors = []

    # Если Python >= 3.13, ошибок быть не должно
    if sys.version_info >= (3, 13):
        check_python_compatibility(warnings.append, errors.append)
        assert len(errors) == 0
```

```python
# tests/test_diagnostics.py
import pytest
from src.diagnostics.warnings import WarningErrorCollector

def test_warning_error_collector():
    """Тест коллектора warnings/errors."""
    collector = WarningErrorCollector()

    # Добавляем warnings и errors
    collector.log_warning("Test warning 1")
    collector.log_warning("Test warning 2")
    collector.log_error("Test error 1")

    # Проверяем накопление
    assert len(collector._items) == 3

    # Проверяем типы
    warnings = [item for item in collector._items if item[0] == "WARNING"]
    errors = [item for item in collector._items if item[0] == "ERROR"]

    assert len(warnings) == 2
    assert len(errors) == 1
```

---

## 📚 Best Practices

### 1. Используйте type hints

```python
from typing import Callable

def my_function(log_error: Callable[[str], None]) -> bool:
    """Функция с type hints."""
    try:
        # Логика
        return True
    except Exception as e:
        log_error(f"Error: {e}")
        return False
```

### 2. Логируйте через коллектор

```python
from src.diagnostics.warnings import log_warning, log_error

# ✅ ПРАВИЛЬНО
log_warning("Configuration file not found, using defaults")

# ❌ НЕПРАВИЛЬНО
print("WARNING: Configuration file not found")
```

### 3. Проверяйте результаты setup функций

```python
from src.bootstrap.environment import setup_qtquick3d_environment
from src.diagnostics.warnings import log_error

success = setup_qtquick3d_environment(log_error)

if not success:
    # Fallback логика
    print("QtQuick3D setup failed, using fallback")
```

### 4. Используйте context managers где возможно

```python
from contextlib import contextmanager
from src.diagnostics.warnings import WarningErrorCollector

@contextmanager
def diagnostic_context():
    """Context manager для диагностики."""
    collector = WarningErrorCollector()

    try:
        yield collector
    finally:
        collector.print_all()

# Использование
with diagnostic_context() as diag:
    diag.log_warning("Test warning")
    # Ваш код
    # В конце автоматически вызовется print_all()
```

---

## 🎯 Заключение

Модульная архитектура позволяет:
- ✅ Переиспользовать код
- ✅ Легко тестировать
- ✅ Расширять функциональность
- ✅ Поддерживать чистый код

Все примеры выше готовы к использованию! 🚀
