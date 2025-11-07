#!/usr/bin/env python3
"""
Автоматическое добавление отсутствующих параметров в рефакторенные табы GraphicsPanel
Читает монолит panel_graphics.py и добавляет недостающие LabeledSlider в табы
"""

from pathlib import Path


def extract_slider_definition(
    monolith_path: Path, param_name: str, line_number: int
) -> str:
    """Извлекает полное определение LabeledSlider из монолита"""
    content = monolith_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Начинаем с указанной строки
    start_idx = line_number - 1
    code_lines = []

    # Ищем начало определения
    for i in range(start_idx, min(start_idx + 10, len(lines))):
        code_lines.append(lines[i])
        # Находим закрывающую скобку
        if ")" in lines[i] and "=" in "".join(code_lines):
            break

    return "\n".join(code_lines)


# Карта: параметр монолита → (таб, строка в монолите)
MISSING_PARAMS = {
    # Camera Tab (5 параметров)
    "Поле зрения": ("camera_tab.py", 1379),
    "Ближняя плоскость": ("camera_tab.py", 1384),
    "Дальняя плоскость": ("camera_tab.py", 1389),
    "Скорость камеры": ("camera_tab.py", 1394),
    "Скорость автоповорота": ("camera_tab.py", 1417),
    # Environment Tab (4 параметра)
    "Интенсивность IBL": ("environment_tab.py", 930),
    "Размытие skybox": ("environment_tab.py", 936),
    "Поворот IBL": ("environment_tab.py", 975),
    "Смещение окружения X": ("environment_tab.py", 989),
    "Смещение окружения Y": ("environment_tab.py", 995),
    # Fog в Environment Tab (5 параметров)
    "Плотность": ("environment_tab.py", 1094),
    "Начало": ("environment_tab.py", 1099),
    "Конец": ("environment_tab.py", 1104),
    "Радиус": ("environment_tab.py", 1127),  # AO radius
    # Quality Tab (3 параметра)
    "Shadow Bias": ("quality_tab.py", 1202),
    "Темнота": ("quality_tab.py", 1207),
    "Сила TAA": ("quality_tab.py", 1249),
    "Масштаб рендера": ("quality_tab.py", 1277),
    "Лимит FPS": ("quality_tab.py", 1290),
    # Effects Tab (3 параметра)
    "Порог": ("effects_tab.py", 1616),
    "Распространение": ("effects_tab.py", 1621),
    "Фокусное расстояние": ("effects_tab.py", 1661),
}


def main():
    """Генерирует отчёт с кодом для добавления"""
    monolith = Path("src/ui/panels/panel_graphics.py")

    if not monolith.exists():
        print(f"❌ Монолит не найден: {monolith}")
        return

    print("=" * 80)
    print("📋 ПЛАН ДОБАВЛЕНИЯ ОТСУТСТВУЮЩИХ ПАРАМЕТРОВ")
    print("=" * 80)

    # Группируем по табам
    by_tab = {}
    for param, (tab, line) in MISSING_PARAMS.items():
        if tab not in by_tab:
            by_tab[tab] = []
        by_tab[tab].append((param, line))

    # Генерируем отчёт для каждого таба
    for tab, params in sorted(by_tab.items()):
        print(f"\n{'=' * 80}")
        print(f"📄 {tab} - добавить {len(params)} параметров")
        print(f"{'=' * 80}\n")

        for param, line in params:
            print(f"▶ {param} (строка {line} в монолите)")

            # Извлекаем код из монолита
            code = extract_slider_definition(monolith, param, line)

            print("   Код для добавления:")
            print("   " + "-" * 76)
            for code_line in code.split("\n"):
                if code_line.strip():
                    # Убираем лишние отступы
                    cleaned = code_line.lstrip()
                    print(f"   {cleaned}")
            print("   " + "-" * 76)
            print()

    print("\n" + "=" * 80)
    print("💡 ИНСТРУКЦИЯ ПО ДОБАВЛЕНИЮ")
    print("=" * 80)
    print(
        """
1. Откройте каждый таб из списка выше
2. Найдите соответствующую группу (QGroupBox)
3. Скопируйте код из раздела "Код для добавления"
4. Вставьте в нужное место (перед layout.addStretch())
5. Подключите сигнал к _emit_changes()
6. Добавьте обработку в get_state() и set_state()
7. Запустите python fix_labeled_slider_calls.py для проверки

Пример интеграции:

```python
# В _create_camera_group():
fov_slider = LabeledSlider(
    "Поле зрения:",
    minimum=10.0,
    maximum=120.0,
    value=60.0,
    step=0.5,
    suffix="°"
)
layout.addWidget(fov_slider)
self.fov_slider = fov_slider  # Сохраняем ссылку

# В _connect_signals():
self.fov_slider.value_changed.connect(self._emit_changes)

# В get_state():
return {
    'fov': self.fov_slider.get_value(),
    # ... остальные параметры
}

# В set_state():
if 'fov' in state:
    self.fov_slider.set_value(state['fov'])
```
    """
    )

    print("\n✅ Отчёт сгенерирован!")


if __name__ == "__main__":
    main()
