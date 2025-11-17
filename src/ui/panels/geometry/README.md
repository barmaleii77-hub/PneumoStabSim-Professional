# GeometryPanel - Модульная структура

**Версия:** v2.0.2
**Статус:** ✅ Refactored
**Дата:** 2025-01-XX

---

## 📊 Архитектура

### **Coordinator Pattern**

```
GeometryPanel (Coordinator)
    ├── FrameTab           - Размеры рамы (wheelbase, track)
    ├── SuspensionTab      - Геометрия подвески (lever, pivot)
    ├── CylinderTab        - Параметры цилиндров (diameter, stroke, rod)
    ├── OptionsTab         - Опции и пресеты
    ├── StateManager       - Управление состоянием
    └── Defaults           - Константы и пресеты
```

### **Файлы**

```
geometry/
├── __init__.py                      # Export + Fallback (80 строк)
├── README.md                        # Документация
├── defaults.py                      # Константы (150 строк)
├── state_manager.py                 # State & validation (200 строк)
├── frame_tab.py                     # Вкладка "Рама" (200 строк)
├── suspension_tab.py                # Вкладка "Подвеска" (250 строк)
├── cylinder_tab.py                  # Вкладка "Цилиндры" (300 строк)
├── options_tab.py                   # Вкладка "Опции" (150 строк)
└── panel_geometry_refactored.py     # Coordinator (250 строк)
```

---

## 🎯 Компоненты

### **1. Defaults (defaults.py)**

Хранит все константы и пресеты геометрии:

```python
DEFAULT_GEOMETRY = {
    'wheelbase': 3.2,
    'track': 1.6,
    'lever_length': 0.8,
    # ...
}

GEOMETRY_PRESETS = {
    'standard_truck': {...},
    'light_commercial': {...},
    'heavy_truck': {...}
}
```

### **2. StateManager (state_manager.py)**

Управление состоянием и валидация:

```python
class GeometryStateManager:
    def validate_geometry(self) -> List[str]
    def check_dependencies(self, param, value) -> Dict
    def save_state(self)
    def load_state(self)
```

### **3. FrameTab (frame_tab.py)**

Вкладка размеров рамы:

```python
class FrameTab(QWidget):
    parameter_changed = Signal(str, float)

    # Widgets:
    # - wheelbase_slider
    # - track_slider
```

### **4. SuspensionTab (suspension_tab.py)**

Вкладка геометрии подвески:

```python
class SuspensionTab(QWidget):
    parameter_changed = Signal(str, float)

    # Widgets:
    # - frame_to_pivot_slider
    # - lever_length_slider
    # - rod_position_slider
```

### **5. CylinderTab (cylinder_tab.py)**

Вкладка параметров цилиндров:

```python
class CylinderTab(QWidget):
    parameter_changed = Signal(str, float)

    # Widgets:
    # - cylinder_length_slider
    # - cyl_diam_m_slider
    # - stroke_m_slider
    # - dead_gap_m_slider
    # - rod_diameter_m_slider
    # - piston_rod_length_m_slider
    # - piston_thickness_m_slider
```

### **6. OptionsTab (options_tab.py)**

Вкладка опций:

```python
class OptionsTab(QWidget):
    preset_changed = Signal(int)
    option_changed = Signal(str, bool)

    # Widgets:
    # - preset_combo
    # - interference_check
    # - link_rod_diameters
    # - reset_button
    # - validate_button
```

### **7. GeometryPanel (panel_geometry_refactored.py)**

Координатор панели:

```python
class GeometryPanel(QWidget):
    """Тонкий координатор - делегирует работу вкладкам"""

    parameter_changed = Signal(str, float)
    geometry_updated = Signal(dict)
    geometry_changed = Signal(dict)

    def __init__(self):
        self.state_manager = GeometryStateManager()
        self.frame_tab = FrameTab(self.state_manager)
        self.suspension_tab = SuspensionTab(self.state_manager)
        self.cylinder_tab = CylinderTab(self.state_manager)
        self.options_tab = OptionsTab(self.state_manager)
```

---

## 📊 Метрики

### **Размеры файлов**

| Файл | Строк | Статус |
|------|-------|--------|
| `panel_geometry.py` (старый) | ~850 | ❌ Монолитный |
| `panel_geometry_refactored.py` | ~250 | ✅ Координатор (-70%) |
| `frame_tab.py` | ~200 | ✅ Модуль |
| `suspension_tab.py` | ~250 | ✅ Модуль |
| `cylinder_tab.py` | ~300 | ✅ Модуль |
| `options_tab.py` | ~150 | ✅ Модуль |
| `state_manager.py` | ~200 | ✅ Модуль |
| `defaults.py` | ~150 | ✅ Модуль |

### **Качество**

| Метрика | До | После | Изменение |
|---------|-----|--------|-----------|
| Читаемость | ⭐⭐ | ⭐⭐⭐ | +50% |
| Тестируемость | ⭐ | ⭐⭐⭐ | +200% |
| Поддерживаемость | ⭐⭐ | ⭐⭐⭐ | +50% |

---

## 🚀 Использование

### **Импорт (обратная совместимость)**

```python
from src.ui.panels import GeometryPanel

# Работает независимо от рефакторинга!
panel = GeometryPanel(parent)
panel.parameter_changed.connect(handler)
```

### **Доступ к подкомпонентам**

```python
# Прямой доступ к вкладкам (если нужно)
panel.frame_tab.wheelbase_slider.setValue(3.5)
panel.state_manager.validate_geometry()
```

---

## ✅ Тестирование

### **Unit Tests**

```bash
pytest tests/test_geometry_panel.py -v
```

### **Integration Tests**

```bash
python tests/test_geometry_integration.py
```

### **Manual Testing**

```bash
python app.py
# Проверить панель "Геометрия автомобиля"
# Изменить значения слайдеров
# Проверить сохранение настроек
```

---

## 📝 Changelog

### **v2.0.2 (2025-01-XX)**

- ✅ Создана модульная структура
- ✅ Выделены вкладки (Frame, Suspension, Cylinder, Options)
- ✅ Создан StateManager
- ✅ Создан Defaults
- ✅ Рефакторинг координатора (-70% кода)
- ✅ Сохранена полная обратная совместимость
- ✅ Добавлены тесты

---

**Статус:** ✅ **REFACTORING COMPLETE**
