# 🚀 REFACTORING PHASE 2: MAINWINDOW

## Статус: 📋 ГОТОВ К ВЫПОЛНЕНИЮ

---

## 🎯 ЦЕЛЬ ФАЗЫ 2

Разделить монолитный `main_window.py` (~1200 строк) на модули:

```
src/ui/main_window/
├── __init__.py                     # Export MainWindow
├── main_window.py                  # Coordinator (~300 строк)
├── ui_setup.py                     # UI construction (~400 строк)
├── qml_bridge.py                   # Python↔QML (~300 строк)
├── signals_router.py               # Signal routing (~200 строк)
├── state_sync.py                   # State sync (~250 строк)
└── menu_actions.py                 # Menu/toolbar (~150 строк)
```

---

## 📋 ПЛАН ДЕЙСТВИЙ

### Шаг 1: Создать структуру
```bash
mkdir src/ui/main_window
touch src/ui/main_window/__init__.py
touch src/ui/main_window/README.md
```

### Шаг 2: Выделить UI Setup (~400 строк)
**Файл:** `src/ui/main_window/ui_setup.py`

**Содержимое:**
```python
"""UI Setup Module - MainWindow UI construction"""

class UISetup:
    """Построение UI элементов MainWindow"""
    
    @staticmethod
    def setup_central(window):
        """Создать центральный вид (3D сцена + графики)"""
        # _setup_central() logic
    
    @staticmethod
    def setup_tabs(window):
        """Создать панели с вкладками"""
        # _setup_tabs() logic
    
    @staticmethod
    def setup_menus(window):
        """Создать меню"""
        # _setup_menus() logic
    
    @staticmethod
    def setup_toolbar(window):
        """Создать панель инструментов"""
        # _setup_toolbar() logic
    
    @staticmethod
    def setup_status_bar(window):
        """Создать строку состояния"""
        # _setup_status_bar() logic
```

### Шаг 3: Выделить QML Bridge (~300 строк)
**Файл:** `src/ui/main_window/qml_bridge.py`

**Содержимое:**
```python
"""QML Bridge Module - Python↔QML integration"""

class QMLBridge:
    """Интеграция Python с Qt Quick 3D"""
    
    @staticmethod
    def setup_qml_view(window):
        """Создать QQuickWidget и загрузить QML"""
        # _setup_qml_3d_view() logic
    
    @staticmethod
    def invoke_qml_function(qml_object, function_name, *args):
        """Вызвать QML функцию из Python"""
        # _invoke_qml_function() logic
    
    @staticmethod
    def set_qml_property(qml_object, property_name, value):
        """Установить свойство QML"""
        # Direct property access
    
    @staticmethod
    def batch_update(qml_object, updates: dict):
        """Групповое обновление QML"""
        # applyBatchedUpdates logic
```

### Шаг 4: Выделить Signals Router (~200 строк)
**Файл:** `src/ui/main_window/signals_router.py`

**Содержимое:**
```python
"""Signals Router Module - Signal connections"""

class SignalsRouter:
    """Роутинг сигналов между компонентами"""
    
    @staticmethod
    def connect_panel_signals(window):
        """Подключить сигналы панелей"""
        # _wire_panel_signals() logic
    
    @staticmethod
    def connect_simulation_signals(window):
        """Подключить сигналы симуляции"""
        # _connect_simulation_signals() logic
    
    @staticmethod
    def connect_qml_signals(window):
        """Подключить сигналы QML"""
        # QML signal connections
```

### Шаг 5: Выделить State Sync (~250 строк)
**Файл:** `src/ui/main_window/state_sync.py`

**Содержимое:**
```python
"""State Sync Module - State synchronization"""

class StateSync:
    """Синхронизация состояния между Python и QML"""
    
    @staticmethod
    def update_from_snapshot(window, snapshot):
        """Обновить UI из состояния физики"""
        # _update_3d_scene_from_snapshot() logic
    
    @staticmethod
    def update_geometry(window, params):
        """Обновить геометрию в QML"""
        # _on_geometry_changed() logic
    
    @staticmethod
    def update_animation(window, params):
        """Обновить анимацию в QML"""
        # _on_animation_changed() logic
    
    @staticmethod
    def sync_graphics(window, params):
        """Синхронизировать настройки графики"""
        # Graphics sync logic
```

### Шаг 6: Выделить Menu Actions (~150 строк)
**Файл:** `src/ui/main_window/menu_actions.py`

**Содержимое:**
```python
"""Menu Actions Module - Menu/toolbar handlers"""

class MenuActions:
    """Обработчики действий меню и панели инструментов"""
    
    @staticmethod
    def show_about(window):
        """Диалог О программе"""
        # _show_about() logic
    
    @staticmethod
    def open_file(window):
        """Открыть файл конфигурации"""
        # File open logic
    
    @staticmethod
    def save_file(window):
        """Сохранить конфигурацию"""
        # File save logic
    
    @staticmethod
    def export_data(window):
        """Экспортировать данные"""
        # Export logic
```

### Шаг 7: Рефакторить main_window.py как координатор (~300 строк)
**Файл:** `src/ui/main_window/main_window.py`

**Содержимое:**
```python
"""MainWindow Coordinator - Refactored Version"""

from .ui_setup import UISetup
from .qml_bridge import QMLBridge
from .signals_router import SignalsRouter
from .state_sync import StateSync
from .menu_actions import MenuActions

class MainWindow(QMainWindow):
    """Главное окно приложения - КООРДИНАТОР"""
    
    def __init__(self, use_qml_3d=True):
        super().__init__()
        
        # Инициализация state
        self._init_state()
        
        # Построение UI (ДЕЛЕГИРОВАНИЕ)
        UISetup.setup_central(self)
        UISetup.setup_tabs(self)
        UISetup.setup_menus(self)
        UISetup.setup_toolbar(self)
        UISetup.setup_status_bar(self)
        
        # QML интеграция (ДЕЛЕГИРОВАНИЕ)
        QMLBridge.setup_qml_view(self)
        
        # Подключение сигналов (ДЕЛЕГИРОВАНИЕ)
        SignalsRouter.connect_panel_signals(self)
        SignalsRouter.connect_simulation_signals(self)
        
        # Таймеры
        self._setup_timers()
    
    def _on_state_update(self, snapshot):
        """Обработка обновления состояния"""
        StateSync.update_from_snapshot(self, snapshot)
    
    def _on_geometry_changed(self, params):
        """Обработка изменения геометрии"""
        StateSync.update_geometry(self, params)
    
    def _show_about(self):
        """Показать диалог О программе"""
        MenuActions.show_about(self)
```

### Шаг 8: Обновить __init__.py
**Файл:** `src/ui/main_window/__init__.py`

```python
"""MainWindow - Modular Structure"""

# Coordinator (REFACTORED)
try:
    from .main_window import MainWindow
    _USING_REFACTORED = True
except ImportError:
    # Fallback к старой версии
    from ..main_window import MainWindow
    _USING_REFACTORED = False

# Export utilities
from .ui_setup import UISetup
from .qml_bridge import QMLBridge
from .signals_router import SignalsRouter
from .state_sync import StateSync
from .menu_actions import MenuActions

__all__ = [
    'MainWindow',
    'UISetup',
    'QMLBridge',
    'SignalsRouter',
    'StateSync',
    'MenuActions',
]
```

---

## ⏱️ ОЦЕНКА ВРЕМЕНИ

| Шаг | Задача | Время | Сложность |
|-----|--------|-------|-----------|
| 1 | Создать структуру | 5 мин | ⭐ |
| 2 | UI Setup | 1 час | ⭐⭐ |
| 3 | QML Bridge | 1.5 часа | ⭐⭐⭐ |
| 4 | Signals Router | 45 мин | ⭐⭐ |
| 5 | State Sync | 1 час | ⭐⭐⭐ |
| 6 | Menu Actions | 30 мин | ⭐ |
| 7 | Координатор | 1 час | ⭐⭐ |
| 8 | __init__.py | 15 мин | ⭐ |
| **ИТОГО** | **Вся фаза** | **~6 часов** | ⭐⭐⭐ |

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit Tests
```python
def test_ui_setup():
    """Тест UISetup"""
    window = QMainWindow()
    UISetup.setup_central(window)
    assert window.centralWidget() is not None

def test_qml_bridge():
    """Тест QMLBridge"""
    window = MainWindow()
    QMLBridge.invoke_qml_function(
        window._qml_root_object,
        "updateGeometry",
        {"frameLength": 2.5}
    )
    # Проверка результата

def test_signals_router():
    """Тест SignalsRouter"""
    window = MainWindow()
    signal_received = False
    
    def on_signal():
        nonlocal signal_received
        signal_received = True
    
    window.geometry_panel.geometry_changed.connect(on_signal)
    window.geometry_panel.geometry_changed.emit({})
    
    assert signal_received
```

### Integration Test
```python
def test_main_window_integration():
    """Интеграционный тест MainWindow"""
    app = QApplication([])
    window = MainWindow()
    
    # Проверка создания всех компонентов
    assert window.geometry_panel is not None
    assert window._qml_root_object is not None
    
    # Проверка сигналов
    window.geometry_panel.geometry_changed.emit({
        'frameLength': 2.5
    })
    
    # QML должен обновиться
    # (требует реальной QML сцены для проверки)
```

---

## ✅ КРИТЕРИИ УСПЕХА

- [ ] Все модули созданы (7/7)
- [ ] Координатор < 400 строк
- [ ] Каждый модуль < 500 строк
- [ ] Обратная совместимость сохранена
- [ ] Unit тесты пройдены
- [ ] Integration тест пройден
- [ ] Приложение запускается без ошибок
- [ ] QML интеграция работает корректно

---

## 🚀 ГОТОВ К ВЫПОЛНЕНИЮ!

**Команда для запуска:**
```bash
# Создать структуру
mkdir src/ui/main_window

# Начать рефакторинг
# (следовать шагам из плана выше)
```

**Следующий файл для редактирования:**
```
src/ui/main_window.py → src/ui/main_window/main_window.py
```

---

**Дата создания:** 2025-01-XX  
**Версия:** v4.9.5  
**Приоритет:** ⭐⭐⭐ ВЫСОКИЙ
