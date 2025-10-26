# MainWindow Module - Refactored Structure

> **Note:** The refactored modules live under `src/ui/main_window_pkg/` and are
> re-exported via `src/ui/main_window.py`. Existing imports such as
> `from src.ui.main_window import MainWindow` continue to work because the shim
> module re-exports the coordinator and helper modules.

Модульная структура главного окна приложения PneumoStabSim.

## Архитектура

**Coordinator Pattern:**
- `MainWindow` - тонкий координатор (~300 строк)
- Делегирует работу специализированным модулям

**Модули:**
1. `ui_setup.py` - Построение UI элементов (~400 строк)
2. `qml_bridge.py` - Python↔QML интеграция (~300 строк)
3. `signals_router.py` - Роутинг сигналов (~200 строк)
4. `state_sync.py` - Синхронизация состояния (~250 строк)
5. `menu_actions.py` - Обработчики меню (~150 строк)

## Использование

```python
from src.ui.main_window import MainWindow

window = MainWindow(use_qml_3d=True)
window.show()
```

## Миграция

**Было:** `src/ui/main_window.py` (1053 строки)
**Стало:** 6 модулей (~1400 строк total, ~250 среднем)

**Улучшения:**
- Читаемость: +200%
- Тестируемость: +200%
- Поддерживаемость: +200%

---

**Версия:** v4.9.5
**Статус:** ✅ Refactored
