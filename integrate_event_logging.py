"""
Автоматическая интеграция event logging в panel_graphics.py
Заменяет слайдеры, чекбоксы и комбобоксы на версии с логированием
"""

import re
import sys
from pathlib import Path


def backup_file(file_path: Path) -> Path:
    """Создает бэкап файла"""
    backup_path = file_path.with_suffix(".py.backup")
    backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"✅ Бэкап создан: {backup_path}")
    return backup_path


def add_imports(content: str) -> str:
    """Добавляет необходимые импорты"""
    # Проверяем, есть ли уже импорт
    if "from src.common.event_logger import" in content:
        print("ℹ️  Импорты уже добавлены")
        return content

    # Находим место для вставки (после существующих импортов)
    import_pattern = r"(from \.graphics_logger import get_graphics_logger\n)"

    new_imports = """
# ✅ НОВОЕ: Импорты для event logging
from src.common.event_logger import get_event_logger
from src.common.logging_slider_wrapper import create_logging_slider, LoggingColorButton

"""

    content = re.sub(import_pattern, r"\1" + new_imports, content)
    print("✅ Импорты добавлены")
    return content


def add_event_logger_init(content: str) -> str:
    """Добавляет инициализацию event_logger в __init__"""
    # Проверяем, есть ли уже
    if "self.event_logger = get_event_logger()" in content:
        print("ℹ️  event_logger уже инициализирован")
        return content

    # Ищем инициализацию graphics_logger
    pattern = r'(self\.graphics_logger = get_graphics_logger\(\)\n\s+self\.logger\.info\("📊 Graphics logger initialized"\))'

    replacement = r"""\1

        # ✅ НОВОЕ: Инициализируем event logger
        self.event_logger = get_event_logger()
        self.logger.info("🔗 Event logger initialized")"""

    content = re.sub(pattern, replacement, content)
    print("✅ event_logger инициализирован")
    return content


def wrap_labeled_slider(content: str) -> str:
    """Заменяет LabeledSlider на версию с логированием"""
    # Паттерн для поиска создания LabeledSlider
    pattern = r"""(\w+)\s*=\s*LabeledSlider\(
        \s*"([^"]+)",\s*           # title
        ([\d.]+),\s*                # minimum
        ([\d.]+),\s*                # maximum
        ([\d.]+),\s*                # step
        (?:decimals=(\d+))?         # decimals (optional)
        (?:,?\s*unit="([^"]+)")?    # unit (optional)
        \s*\)"""

    def replace_slider(match):
        var_name = match.group(1)
        title = match.group(2)
        minimum = match.group(3)
        maximum = match.group(4)
        step = match.group(5)
        decimals = match.group(6) or "2"
        unit = match.group(7)

        # Генерируем уникальное имя для логирования на основе переменной
        widget_name = var_name.replace("_", ".")

        # Формируем замену
        replacement = f"""{var_name}_slider, {var_name}_logging = create_logging_slider(
            title="{title}",
            minimum={minimum},
            maximum={maximum},
            step={step},
            widget_name="{widget_name}",
            decimals={decimals}"""

        if unit:
            replacement += f',\n            unit="{unit}"'

        replacement += ",\n            parent=self\n        )"

        return replacement

    new_content = re.sub(pattern, replace_slider, content, flags=re.VERBOSE)

    if new_content != content:
        print("✅ LabeledSlider'ы заменены на версию с логированием")

    return new_content


def update_slider_connections(content: str) -> str:
    """Обновляет подключения слайдеров"""
    # Паттерн для поиска connect с LabeledSlider
    pattern = r'(\w+)\.valueChanged\.connect\(lambda v: self\._update_(\w+)\("(\w+)", "(\w+)", v\)\)'

    def replace_connection(match):
        var_name = match.group(1)
        update_func = match.group(2)
        group = match.group(3)
        key = match.group(4)

        # Если уже используется logging версия
        if "_logging" in var_name:
            return match.group(0)

        # Заменяем на logging версию
        return f'{var_name}_logging.valueChanged.connect(lambda v: self._update_{update_func}("{group}", "{key}", v))'

    new_content = re.sub(pattern, replace_connection, content)

    if new_content != content:
        print("✅ Подключения слайдеров обновлены")

    return new_content


def update_control_storage(content: str) -> str:
    """Обновляет сохранение контролов в словарях"""
    # Паттерн для поиска сохранения в _controls
    pattern = r'self\._(\w+)_controls\["([^"]+)"\] = (\w+)'

    def replace_storage(match):
        category = match.group(1)
        key = match.group(2)
        var_name = match.group(3)

        # Если переменная - это slider с logging
        if "_slider" in var_name or "_logging" in var_name:
            # Сохраняем базовый слайдер (без _logging)
            base_var = var_name.replace("_logging", "_slider")
            return f'self._{category}_controls["{key}"] = {base_var}'

        return match.group(0)

    new_content = re.sub(pattern, replace_storage, content)

    return new_content


def add_checkbox_wrappers(content: str) -> str:
    """Добавляет wrapper'ы для QCheckBox"""
    # Это сложнее автоматизировать, выведем список для ручной доработки
    checkbox_pattern = r'(\w+)\s*=\s*QCheckBox\("([^"]+)", self\)\s*\n\s*\1\.stateChanged\.connect\(lambda state: self\._update_(\w+)\("(\w+)", state == Qt\.Checked\)\)'

    checkboxes = re.findall(checkbox_pattern, content)

    if checkboxes:
        print("\n⚠️  Найдены QCheckBox, требующие ручной доработки:")
        for var_name, text, update_func, key in checkboxes:
            print(f"   • {var_name} ('{text}')")

        print("\n💡 Используйте паттерн из FULL_UI_EVENT_LOGGING_GUIDE.md")

    return content


def main():
    """Main entry point"""
    panel_file = Path("src/ui/panels/panel_graphics.py")

    if not panel_file.exists():
        print(f"❌ Файл не найден: {panel_file}")
        return 1

    print("=" * 60)
    print("🔧 АВТОМАТИЧЕСКАЯ ИНТЕГРАЦИЯ EVENT LOGGING")
    print("=" * 60)

    # Создаем бэкап
    backup_file(panel_file)

    # Читаем файл
    content = panel_file.read_text(encoding="utf-8")

    # Применяем трансформации
    content = add_imports(content)
    content = add_event_logger_init(content)
    content = wrap_labeled_slider(content)
    content = update_slider_connections(content)
    content = update_control_storage(content)
    content = add_checkbox_wrappers(content)

    # Записываем результат
    panel_file.write_text(content, encoding="utf-8")

    print("\n" + "=" * 60)
    print("✅ Интеграция завершена!")
    print("=" * 60)

    print("\n📋 Следующие шаги:")
    print("1. Проверьте изменения в panel_graphics.py")
    print("2. Вручную добавьте wrapper'ы для QCheckBox (см. список выше)")
    print("3. Добавьте MouseEventLogger в main.qml")
    print("4. Запустите приложение для тестирования")
    print("5. Проверьте logs/events_*.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
