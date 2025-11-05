# 🚀 СЛЕДУЮЩИЙ ШАГ: Рефакторинг panel_graphics.py

**Текущий статус:** 90% GraphicsPanel реструктуризации завершено
**Осталось:** Рефакторинг главного координатора

---

## 📋 ЧТО НУЖНО СДЕЛАТЬ

### Задача: Превратить `panel_graphics.py` в тонкий координатор

**Было:** 2662 строки монолитного кода
**Станет:** ~400 строк координатора + 10 модулей

---

## 🎯 ПЛАН РЕФАКТОРИНГА

### Шаг 1: Сохранить текущий файл как backup
```bash
cp src/ui/panels/panel_graphics.py src/ui/panels/panel_graphics_backup.py
```

### Шаг 2: Создать новый координатор

**Структура нового файла:**

```python
# -*- coding: utf-8 -*-
"""
GraphicsPanel - координатор вкладок графических настроек
Тонкий слой для агрегации сигналов и управления состоянием
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Signal, Slot
import logging
from typing import Dict, Any

# Импорт модулей
from .lighting_tab import LightingTab
from .environment_tab import EnvironmentTab
from .quality_tab import QualityTab
from .camera_tab import CameraTab
from .materials_tab import MaterialsTab
from .effects_tab import EffectsTab
from .state_manager import GraphicsStateManager


class GraphicsPanel(QWidget):
    """Панель настроек графики и визуализации

    Координирует 6 вкладок:
    - Lighting: Освещение
    - Environment: Окружение (фон, IBL, туман)
    - Quality: Качество (тени, AA)
    - Camera: Камера (FOV, clipping)
    - Materials: Материалы (PBR)
    - Effects: Эффекты (Bloom, SSAO, DoF)

    Signals:
        lighting_changed: Dict - параметры освещения
        environment_changed: Dict - параметры окружения
        quality_changed: Dict - параметры качества
        camera_changed: Dict - параметры камеры
        materials_changed: Dict - параметры материалов
        effects_changed: Dict - параметры эффектов
    """

    # Агрегированные сигналы для MainWindow
    lighting_changed = Signal(dict)
    environment_changed = Signal(dict)
    quality_changed = Signal(dict)
    camera_changed = Signal(dict)
    materials_changed = Signal(dict)
    effects_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Менеджер состояния
        self.state_manager = GraphicsStateManager()

        # Создаём вкладки
        self._create_tabs()

        # Настраиваем UI
        self._setup_ui()

        # Подключаем сигналы
        self._connect_signals()

        # Загружаем сохранённое состояние
        self._load_saved_state()

    def _create_tabs(self):
        """Создать все вкладки"""
        self.lighting_tab = LightingTab()
        self.environment_tab = EnvironmentTab()
        self.quality_tab = QualityTab()
        self.camera_tab = CameraTab()
        self.materials_tab = MaterialsTab()
        self.effects_tab = EffectsTab()

    def _setup_ui(self):
        """Построить UI панели"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.lighting_tab, "💡 Освещение")
        self.tab_widget.addTab(self.environment_tab, "🌍 Окружение")
        self.tab_widget.addTab(self.quality_tab, "⚙️ Качество")
        self.tab_widget.addTab(self.camera_tab, "📷 Камера")
        self.tab_widget.addTab(self.materials_tab, "🎨 Материалы")
        self.tab_widget.addTab(self.effects_tab, "✨ Эффекты")

        layout.addWidget(self.tab_widget)

    def _connect_signals(self):
        """Подключить сигналы от всех вкладок"""
        # Lighting
        self.lighting_tab.lighting_changed.connect(self._on_lighting_changed)

        # Environment
        self.environment_tab.environment_changed.connect(self._on_environment_changed)

        # Quality
        self.quality_tab.quality_changed.connect(self._on_quality_changed)

        # Camera
        self.camera_tab.camera_changed.connect(self._on_camera_changed)

        # Materials
        self.materials_tab.materials_changed.connect(self._on_materials_changed)

        # Effects
        self.effects_tab.effects_changed.connect(self._on_effects_changed)

    @Slot(dict)
    def _on_lighting_changed(self, params: Dict[str, Any]):
        """Обработчик изменения освещения"""
        # Сохранить в QSettings
        self.state_manager.save_state('lighting', params)

        # Испустить агрегированный сигнал
        self.lighting_changed.emit(params)

    # ... аналогично для остальных категорий

    def _load_saved_state(self):
        """Загрузить сохранённое состояние"""
        # Загрузить все категории
        full_state = self.state_manager.load_all()

        # Применить к вкладкам
        if 'lighting' in full_state:
            self.lighting_tab.set_state(full_state['lighting'])

        if 'environment' in full_state:
            self.environment_tab.set_state(full_state['environment'])

        # ... и т.д.

    def get_full_state(self) -> Dict[str, Dict[str, Any]]:
        """Получить полное состояние всех настроек"""
        return {
            'lighting': self.lighting_tab.get_state(),
            'environment': self.environment_tab.get_state(),
            'quality': self.quality_tab.get_state(),
            'camera': self.camera_tab.get_state(),
            'materials': self.materials_tab.get_state(),
            'effects': self.effects_tab.get_state()
        }

    def set_full_state(self, full_state: Dict[str, Dict[str, Any]]):
        """Установить полное состояние"""
        for category, state in full_state.items():
            if category == 'lighting':
                self.lighting_tab.set_state(state)
            # ... и т.д.
```

---

## ✅ КРИТЕРИИ УСПЕХА

### 1. Размер файла
- ✅ panel_graphics.py < 500 строк
- ✅ Вся логика вкладок в отдельных модулях

### 2. Функциональность
- ✅ Все вкладки работают
- ✅ Сигналы правильно агрегируются
- ✅ Состояние сохраняется/загружается
- ✅ Обратная совместимость с MainWindow

### 3. Чистота кода
- ✅ Нет дублирования
- ✅ Понятная структура
- ✅ Docstrings везде
- ✅ Type hints

---

## 🧪 ТЕСТИРОВАНИЕ

### Тест 1: Импорт
```python
from src.ui.panels.graphics import GraphicsPanel
panel = GraphicsPanel()
# Должно работать без ошибок
```

### Тест 2: Создание вкладок
```python
panel = GraphicsPanel()
assert panel.lighting_tab is not None
assert panel.environment_tab is not None
# ... и т.д.
```

### Тест 3: Сигналы
```python
panel = GraphicsPanel()
signal_received = False

def on_lighting_changed(params):
    global signal_received
    signal_received = True

panel.lighting_changed.connect(on_lighting_changed)
panel.lighting_tab.key_brightness_slider.set_value(5.0)

assert signal_received
```

### Тест 4: Сохранение/загрузка
```python
panel = GraphicsPanel()

# Изменить параметр
panel.lighting_tab.key_brightness_slider.set_value(5.0)

# Получить состояние
state = panel.get_full_state()
assert state['lighting']['key_brightness'] == 5.0

# Создать новую панель
panel2 = GraphicsPanel()

# Состояние должно загрузиться из QSettings
loaded_state = panel2.get_full_state()
assert loaded_state['lighting']['key_brightness'] == 5.0
```

---

## 📝 ЧЕКЛИСТ

- [ ] Сохранить backup старого файла
- [ ] Создать новый panel_graphics.py (~400 строк)
- [ ] Реализовать _create_tabs()
- [ ] Реализовать _setup_ui()
- [ ] Реализовать _connect_signals()
- [ ] Реализовать обработчики (_on_lighting_changed и т.д.)
- [ ] Реализовать _load_saved_state()
- [ ] Реализовать get_full_state()
- [ ] Реализовать set_full_state()
- [ ] Проверить импорт в MainWindow
- [ ] Запустить приложение и протестировать все вкладки
- [ ] Убедиться что сигналы доходят до MainWindow
- [ ] Проверить сохранение/загрузку состояния
- [ ] Удалить backup файл

---

## 🎉 ПОСЛЕ ЗАВЕРШЕНИЯ

**GraphicsPanel будет 100% готов!**

- ✅ 11 модулей вместо 1 монолита
- ✅ ~3077 строк в 11 файлах (средний размер: 280 строк)
- ✅ Легко тестировать, поддерживать, расширять
- ✅ Обратная совместимость

**Следующий шаг:** Применить этот же подход к другим большим файлам:
- MainWindow (1152 строки)
- SimLoop (730 строк)
- PanelGeometry (805 строк)
- PanelPneumo (771 строка)

---

**Статус:** 🔨 READY TO START
**Приоритет:** 🔥 ВЫСОКИЙ
**Время:** ~2-3 часа

**Удачи!** 🚀
