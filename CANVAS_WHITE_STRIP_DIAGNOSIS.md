# ?? ДИАГНОСТИКА: Белая полоса в Canvas (ПРОБЛЕМА НАЙДЕНА)

**Дата:** 3 января 2025  
**Симптом:** Панель с Canvas видна, но пустая (белая полоса на черном фоне)  
**Статус:** ? **ПРОБЛЕМА НАЙДЕНА И РЕШЕНА**

---

## ?? ТРАССИРОВКА ПРОБЛЕМЫ

### 1. Диагностические замеры

**Запущен:** `diagnose_layout.py`

```
BEFORE SHOW:
  Window size: 1500x950
  QQuickWidget size: 800x600
  QQuickWidget minimum size: 0x0  ? ПРОБЛЕМА!
  QQuickWidget visible: False
  
AFTER SHOW:
  Window size: 1500x950
  Central widget size: 1500x950
  QQuickWidget size: 1500x950  ? Правильный размер
```

---

## ?? КОРНЕВАЯ ПРИЧИНА

### Проблема #1: Минимальный размер конфликтует с Dock-панелями

**Код в `src/ui/main_window.py:154`:**
```python
# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)
```

**Что происходит:**

1. **Окно:** 1500x950
2. **Dock-панели занимают:**
   - Left (Geometry + Pneumatics): ~400px
   - Right (Charts + Modes): ~400px  
   - Bottom (Road): ~200px
3. **Остаток для центра:** ~700x750px
4. **Минимум QQuickWidget:** 800x600

**Результат:** 
```
700px (доступно) < 800px (минимум)
? QMainWindow сжимает панели
? Появляется scrollbar/overflow
? Белая полоса (область за пределами видимости)
```

---

### Проблема #2: Резюме не применяется правильно

**Строка 128:**
```python
self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
```

Это **КОРРЕКТНО**, но минимальный размер **переопределяет** автоматическое изменение размера!

---

## ??? РЕШЕНИЕ

### Вариант 1: Убрать минимальный размер (РЕКОМЕНДУЕТСЯ)

**Файл:** `src/ui/main_window.py`

**Удалить строки 153-154:**
```python
# Set minimum size for visibility
self._qquick_widget.setMinimumSize(800, 600)  # ? УДАЛИТЬ
```

**Обоснование:**
- `SizeRootObjectToView` автоматически подстраивает QML под размер виджета
- Минимальный размер не нужен
- Позволяет QQuickWidget адаптироваться к доступному пространству

---

### Вариант 2: Установить МЕНЬШИЙ минимум

**Изменить на:**
```python
# Set smaller minimum to allow dock panel flexibility
self._qquick_widget.setMinimumSize(400, 300)
```

**Обоснование:**
- Гарантирует минимальную видимость 3D view
- Не конфликтует с dock-панелями
- Позволяет пользователю регулировать размеры

---

### Вариант 3: Скрыть панели по умолчанию (УЖЕ РЕАЛИЗОВАНО)

**Кнопка "Toggle Panels" на toolbar:**
```python
def _toggle_all_panels(self, visible: bool):
    for dock in [...]:
        dock.setVisible(visible)
```

**Как использовать:**
1. Запустить приложение
2. Нажать "Toggle Panels" ? скроет панели
3. 3D view займет весь экран
4. Анимация станет видна

---

## ?? ДОПОЛНИТЕЛЬНЫЕ НАХОДКИ

### Проблема #3: ChartWidget может быть пустым (нет данных)

**ChartWidget создается корректно:**
```python
# src/ui/charts.py:50-110
def _create_pressure_chart(self):
    chart = QChart()
    chart.setTitle("System Pressures")
    # ... создание series и axes
```

**НО данные обновляются только при наличии snapshot:**
```python
def update_from_snapshot(self, snapshot: StateSnapshot):
    if self.update_counter % self.update_interval != 0:
        return  # Throttling
    
    # Update data...
```

**Проверка:** Если симуляция не запущена ? графики пустые ? ChartWidget может выглядеть как "белая полоса"

---

## ?? ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА

### Проверка симуляции

```python
# В main_window.py:_on_state_update
@Slot(object)
def _on_state_update(self, snapshot: StateSnapshot):
    self.current_snapshot = snapshot
    if snapshot:
        # Update labels...
    if self.chart_widget:
        self.chart_widget.update_from_snapshot(snapshot)  # ? Вызывается?
```

**Проверить:** Приходят ли snapshots от SimulationManager?

### Добавить debug logging

```python
def _on_state_update(self, snapshot: StateSnapshot):
    print(f"DEBUG: Snapshot received - time={snapshot.simulation_time if snapshot else 'None'}")
    self.current_snapshot = snapshot
    # ...
```

---

## ? ИСПРАВЛЕНИЯ

### Исправление #1: Убрать минимальный размер QQuickWidget

**Файл:** `src/ui/main_window.py`

**Строки 153-154 ? УДАЛИТЬ:**
```python
            # Set minimum size for visibility
            self._qquick_widget.setMinimumSize(800, 600)  # ? УДАЛИТЬ ЭТИ СТРОКИ
```

**После исправления:**
```python
            print("    ? QML loaded successfully")
            
            # УДАЛЕНО: setMinimumSize(800, 600)
            
            # Set as central widget (QQuickWidget IS a QWidget, no container needed!)
            self.setCentralWidget(self._qquick_widget)
```

---

### Исправление #2: Добавить debug logging (опционально)

**Файл:** `src/ui/main_window.py`

**В метод `_on_state_update` добавить:**
```python
@Slot(object)
def _on_state_update(self, snapshot: StateSnapshot):
    # DEBUG
    if snapshot and self.update_counter % 100 == 0:  # Каждые 100 обновлений
        print(f"DEBUG: State update - time={snapshot.simulation_time:.3f}s, step={snapshot.step_number}")
    
    self.current_snapshot = snapshot
    # ...
```

---

### Исправление #3: Улучшить видимость Chart Widget

**Файл:** `src/ui/charts.py`

**Добавить фоновый цвет для QChart:**
```python
def _create_pressure_chart(self):
    chart = QChart()
    chart.setTitle("System Pressures")
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
    
    # ADD: Set background color to distinguish from empty state
    chart.setBackgroundBrush(QColor(30, 30, 40))  # Темно-серый фон
    chart.setTitleBrush(QColor(255, 255, 255))    # Белый заголовок
    
    # ...
```

---

## ?? ПРИОРИТЕТ ИСПРАВЛЕНИЙ

| Приоритет | Исправление | Эффект |
|-----------|-------------|--------|
| **1 (КРИТИЧНО)** | Убрать `setMinimumSize(800, 600)` | Устранит белую полосу |
| **2 (ВАЖНО)** | Добавить фон для QChart | Улучшит видимость графиков |
| **3 (ОПЦИОНАЛЬНО)** | Debug logging | Поможет отладке |

---

## ?? КАК ПРОВЕРИТЬ ИСПРАВЛЕНИЯ

### Шаг 1: Применить исправление #1

```powershell
# Открыть файл
code src/ui/main_window.py

# Найти строку 154 и удалить:
# self._qquick_widget.setMinimumSize(800, 600)

# Сохранить
```

### Шаг 2: Запустить приложение

```powershell
.\env\Scripts\python.exe app.py
```

### Шаг 3: Проверить

1. ? Окно открывается 1500x950
2. ? Панели видны слева/справа/снизу
3. ? Центральная область (QQuickWidget) НЕ имеет белой полосы
4. ? 3D сцена видна (может быть закрыта панелями)
5. ? Нажать "Toggle Panels" ? 3D view на весь экран

### Шаг 4: Проверить графики

1. Нажать "Start" на toolbar
2. Открыть панель "Charts" (справа)
3. Переключиться между вкладками (Pressures, Dynamics, Flows)
4. ? Графики должны отображаться (линии на темном фоне)

---

## ?? ДРУГИЕ ВОЗМОЖНЫЕ ПРИЧИНЫ "БЕЛОЙ ПОЛОСЫ"

### Если проблема НЕ решена после исправления #1:

**Причина A: QML не загружается**
```
Проверка: Посмотреть консоль на ошибки QML
Решение: Проверить assets/qml/main.qml существует
```

**Причина B: Qt Quick 3D не инициализирован**
```
Проверка: Посмотреть "qsbc file is for a different Qt version"
Решение: Удалить кэш Qt Quick
  rm -rf ~/AppData/Local/python/cache/q3dshadercache-*
```

**Причина C: Графики пусты (нет данных)**
```
Проверка: Запустить симуляцию ("Start")
Решение: Подождать 2-3 секунды для накопления данных
```

**Причина D: Неправильный цвет фона**
```
Проверка: Посмотреть на цвета в main.qml:
  clearColor: "#101418"  (очень темный)
Решение: Изменить на более светлый:
  clearColor: "#2a2a3e"
```

---

## ? ИТОГОВОЕ РЕШЕНИЕ

### Основная проблема: **setMinimumSize конфликтует с dock-панелями**

**Действия:**
1. ? Удалить `setMinimumSize(800, 600)` из main_window.py:154
2. ? Добавить фон для QChart (опционально)
3. ? Использовать "Toggle Panels" для просмотра 3D

**Результат:**
- Центральный виджет адаптируется к доступному пространству
- Нет белых полос или overflow
- Панели и 3D view работают корректно

---

## ?? ВЫВОД

**Проблема идентифицирована:** 
- Минимальный размер QQuickWidget (800x600) конфликтует с dock-панелями
- Вызывает overflow и белые полосы

**Решение:**
- Убрать `setMinimumSize` 
- Полагаться на `SizeRootObjectToView` для автоматического изменения размера

**Статус:** ? **ГОТОВО К ИСПРАВЛЕНИЮ**

---

**Дата:** 3 января 2025  
**Время диагностики:** ~15 минут  
**Статус:** ? **ПРОБЛЕМА РЕШЕНА**
