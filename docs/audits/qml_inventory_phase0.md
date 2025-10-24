# Phase 0 QML Inventory

Diagnostic run performed with `python qml_diagnostic.py --help` to validate the
current entrypoint selection logic.

## Summary

- Optimised QML entry (`assets/qml/main_optimized.qml`) is absent; the launcher
  correctly falls back to `assets/qml/main.qml`.
- Baseline QML file exists (124 bytes) and begins with `import QtQuick` as
  expected for Qt Quick 3 content.
- No additional QML modules were auto-discovered by the helper script; further
  enumeration will be required in Phase 3 when synchronising UI bindings.

## Diagnostic Output

```
🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML ФАЙЛОВ
==================================================
📂 Рабочая директория: /workspace/PneumoStabSim-Professional

📄 assets/qml/main_optimized.qml:
   Существует: False

📄 assets/qml/main.qml:
   Существует: True
   Размер: 124 байт
   Полный путь: /workspace/PneumoStabSim-Professional/assets/qml/main.qml
   Первая строка: import QtQuick

🔄 СИМУЛЯЦИЯ ЛОГИКИ ЗАГРУЗКИ:
1. Проверяем main_optimized.qml: False
   ⚠️ Оптимизированная версия не найдена, переключаемся на main.qml
2. Итоговый файл для загрузки: assets/qml/main.qml
   Существует: True
   ✅ Будет загружен: main.qml
```
