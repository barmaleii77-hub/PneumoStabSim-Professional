# 🚀 START PHASE 2: MAINWINDOW REFACTORING

## ⚡ БЫСТРЫЙ СТАРТ

Вы готовы начать Фазу 2 реструктуризации проекта PneumoStabSim!

---

## ✅ ПРЕДПОСЫЛКИ

**Фаза 1 завершена:**
- ✅ GraphicsPanel разделён на 12 модулей
- ✅ Координатор уменьшен с 2662 → 300 строк
- ✅ Обратная совместимость сохранена
- ✅ Все компоненты протестированы

**Текущий статус проекта:**
```
┌────────────────────────────────────┐
│  Фаза 1: GraphicsPanel   ✅ 100%  │
│  Фаза 2: MainWindow      ⏳   0%  │
│  Фаза 3: GeometryPanel   📋   0%  │
│  Фаза 4: SimLoop         📋   0%  │
│────────────────────────────────────│
│  ОБЩИЙ ПРОГРЕСС:         █░░░ 25% │
└────────────────────────────────────┘
```

---

## 🎯 ЦЕЛЬ ФАЗЫ 2

Разделить `main_window.py` (~1200 строк) на модули:

```
src/ui/main_window/
├── main_window.py          # Coordinator (~300 строк)
├── ui_setup.py             # UI construction (~400 строк)
├── qml_bridge.py           # Python↔QML (~300 строк)
├── signals_router.py       # Signal routing (~200 строк)
├── state_sync.py           # State sync (~250 строк)
└── menu_actions.py         # Menu/toolbar (~150 строк)
```

---

## 🔧 ШАГИ ВЫПОЛНЕНИЯ

### 1. Создать структуру директории
```bash
mkdir src/ui/main_window
cd src/ui/main_window
```

### 2. Создать базовые файлы
```bash
# Windows PowerShell
New-Item -ItemType File -Path __init__.py
New-Item -ItemType File -Path README.md
New-Item -ItemType File -Path ui_setup.py
New-Item -ItemType File -Path qml_bridge.py
New-Item -ItemType File -Path signals_router.py
New-Item -ItemType File -Path state_sync.py
New-Item -ItemType File -Path menu_actions.py
New-Item -ItemType File -Path main_window.py

# Linux/macOS
touch __init__.py README.md ui_setup.py qml_bridge.py
touch signals_router.py state_sync.py menu_actions.py main_window.py
```

### 3. Следовать детальному плану
```bash
# Откройте детальный план:
code REFACTORING_PHASE2_MAINWINDOW_PLAN.md

# Или просмотрите в консоли:
cat REFACTORING_PHASE2_MAINWINDOW_PLAN.md
```

---

## 📚 ДЕТАЛЬНЫЙ ПЛАН

### Шаг 2.1: Выделить UI Setup (~400 строк)
**Файл:** `ui_setup.py`

**Методы для переноса:**
- `_setup_central()`
- `_setup_tabs()`
- `_setup_menus()`
- `_setup_toolbar()`
- `_setup_status_bar()`

### Шаг 2.2: Выделить QML Bridge (~300 строк)
**Файл:** `qml_bridge.py`

**Методы для переноса:**
- `_setup_qml_3d_view()`
- `_invoke_qml_function()`
- `_set_qml_property()`
- `_batch_update()`

### Шаг 2.3: Выделить Signals Router (~200 строк)
**Файл:** `signals_router.py`

**Методы для переноса:**
- `_wire_panel_signals()`
- `_connect_simulation_signals()`

### Шаг 2.4: Выделить State Sync (~250 строк)
**Файл:** `state_sync.py`

**Методы для переноса:**
- `_update_3d_scene_from_snapshot()`
- `_on_geometry_changed()`
- `_on_animation_changed()`

### Шаг 2.5: Выделить Menu Actions (~150 строк)
**Файл:** `menu_actions.py`

**Методы для переноса:**
- `_show_about()`
- `_open_file()`
- `_save_file()`
- `_export_data()`

### Шаг 2.6: Рефакторить координатор (~300 строк)
**Файл:** `main_window.py`

**Новая структура:**
```python
from .ui_setup import UISetup
from .qml_bridge import QMLBridge
from .signals_router import SignalsRouter
from .state_sync import StateSync
from .menu_actions import MenuActions

class MainWindow(QMainWindow):
    def __init__(self, use_qml_3d=True):
        super().__init__()

        # Делегирование UI построения
        UISetup.setup_central(self)
        UISetup.setup_tabs(self)
        # ...

        # Делегирование QML интеграции
        QMLBridge.setup_qml_view(self)

        # Делегирование сигналов
        SignalsRouter.connect_panel_signals(self)
```

---

## ⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ

| Задача | Время | Сложность |
|--------|-------|-----------|
| Создание структуры | 5 мин | ⭐ |
| UI Setup | 1 час | ⭐⭐ |
| QML Bridge | 1.5 часа | ⭐⭐⭐ |
| Signals Router | 45 мин | ⭐⭐ |
| State Sync | 1 час | ⭐⭐⭐ |
| Menu Actions | 30 мин | ⭐ |
| Координатор | 1 час | ⭐⭐ |
| **ИТОГО** | **~6 часов** | ⭐⭐⭐ |

---

## 🧪 ТЕСТИРОВАНИЕ

После завершения рефакторинга:

### 1. Проверка синтаксиса
```bash
python -m py_compile src/ui/main_window/*.py
```

### 2. Запуск приложения
```bash
python app.py
```

### 3. Проверка функционала
- ✅ Окно открывается
- ✅ 3D сцена загружается
- ✅ Панели работают
- ✅ Сигналы между панелями проходят
- ✅ QML обновляется при изменениях

### 4. Unit тесты
```bash
python -m pytest tests/ui/test_main_window.py -v
```

### 5. Проверка метрик
```bash
python tools/analyze_file_sizes.py
```

**Ожидаемый результат:**
```
src/ui/main_window/main_window.py: ~300 строк ✅
src/ui/main_window/ui_setup.py: ~400 строк ✅
src/ui/main_window/qml_bridge.py: ~300 строк ✅
```

---

## 📋 ЧЕКЛИСТ ВЫПОЛНЕНИЯ

### Подготовка:
- [ ] Создана директория `src/ui/main_window/`
- [ ] Созданы базовые файлы (8 файлов)
- [ ] Прочитан детальный план

### Реализация:
- [ ] Выделен `ui_setup.py` (~400 строк)
- [ ] Выделен `qml_bridge.py` (~300 строк)
- [ ] Выделен `signals_router.py` (~200 строк)
- [ ] Выделен `state_sync.py` (~250 строк)
- [ ] Выделен `menu_actions.py` (~150 строк)
- [ ] Рефакторен `main_window.py` (~300 строк)
- [ ] Обновлён `__init__.py` (fallback механизм)

### Тестирование:
- [ ] Проверка синтаксиса (py_compile)
- [ ] Приложение запускается
- [ ] 3D сцена работает
- [ ] Панели работают
- [ ] Unit тесты пройдены
- [ ] Метрики проверены

### Документация:
- [ ] Обновлён `README.md`
- [ ] Обновлён `REFACTORING_REPORT.md`
- [ ] Создан отчёт о завершении Фазы 2

---

## 🎯 КРИТЕРИИ УСПЕХА

✅ **Координатор < 400 строк**
✅ **Каждый модуль < 500 строк**
✅ **Обратная совместимость сохранена**
✅ **Приложение запускается без ошибок**
✅ **Все тесты пройдены**

---

## 📞 ПОМОЩЬ

### Документация:
- `REFACTORING_PHASE2_MAINWINDOW_PLAN.md` - Детальный план
- `REFACTORING_STATUS_VISUAL.txt` - Визуальный отчёт
- `src/ui/panels/graphics/README.md` - Пример из Фазы 1

### Инструменты:
- `tools/analyze_file_sizes.py` - Анализ размеров
- `python -m pytest tests/` - Запуск тестов

### Примеры паттернов:
```python
# Coordinator Pattern (из GraphicsPanel)
class MainWindow(QMainWindow):
    def __init__(self):
        # Создание компонентов (делегирование)
        UISetup.setup_central(self)
        QMLBridge.setup_qml_view(self)
        SignalsRouter.connect_signals(self)

# State Manager Pattern
class StateSync:
    @staticmethod
    def update_from_snapshot(window, snapshot):
        # Обновление UI из состояния
        ...
```

---

## 🚀 НАЧАТЬ!

```bash
# 1. Создать структуру
mkdir src/ui/main_window

# 2. Открыть в редакторе
code src/ui/main_window

# 3. Следовать плану
# REFACTORING_PHASE2_MAINWINDOW_PLAN.md

# 4. Тестировать
python app.py
```

---

## ✅ ГОТОВ!

**Фаза 2 запущена! Удачи!** 🚀

---

**Дата:** 2025-01-XX
**Версия:** v4.9.5
**Приоритет:** ⭐⭐⭐ ВЫСОКИЙ
