# PneumoStabSim - Pneumatic Stabilizer Simulator

Симулятор пневматической системы стабилизации.

## Требования

- Python 3.13+
- Visual Studio 2022+ с Python workload

## Установка

1. Клонируйте репозиторий
2. Создайте виртуальную среду:
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

- `src/common/` - общие утилиты и константы
- `src/core/` - системы координат, геометрия
- `src/pneumo/` - компоненты пневматической системы
- `src/mechanics/` - механические компоненты
- `src/physics/` - физическая симуляция
- `src/ui/` - пользовательский интерфейс (PySide6)