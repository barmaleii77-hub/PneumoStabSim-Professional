# PneumoStabSim - Pneumatic Stabilizer Simulator

Симулятор пневматической системы стабилизации.

## Требования

- Python 3.13+
- Visual Studio 2022+ с Python workload

## Установка

1. Клонируйте репозиторий
2. Создайте виртуальное окружение:
   ```
   py -3.13 -m venv .venv
   . .\.venv\Scripts\Activate.ps1
   ```
3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

## Запуск

```
python app/app.py
```

## Структура проекта

- `src/common/` - Общие классы и константы
- `src/core/` - Базовые механизмы, геометрия
- `src/pneumo/` - Компоненты пневматической системы
- `src/mechanics/` - Механическая кинематика
- `src/physics/` - Физические симуляции
- `src/ui/` - Пользовательский интерфейс (PySide6)