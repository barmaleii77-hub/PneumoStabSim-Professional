# PROMPT #1 EXECUTION PLAN

## STATUS: AUDIT COMPLETE ?

### ШАГ 0: ПРЕДПОЛЁТНАЯ ПРОВЕРКА ?
- ? Созданы папки: reports/ui/, artifacts/ui/
- ? Отчёт: reports/ui/ui_audit_pre.md
- ? JSON дерево: artifacts/ui/widget_tree_pre.json
- ? Логирование: reports/ui/ui_prompt1.log

### НАЙДЕННЫЕ ПРОБЛЕМЫ:
1. **ЯЗЫК:** Все тексты на английском ? нужен русский
2. **LAYOUT:** Charts в правом доке ? должны быть внизу на всю ширину
3. **SCROLL:** Нет QScrollArea в вкладках
4. **COMBOBOXES:** Мало выпадающих списков
5. **ACCORDIONS:** ? Нет (хорошо!)

### СЛЕДУЮЩИЕ ШАГИ (по приоритету):

## ШАГ 1: РЕСТРУКТУРИЗАЦИЯ ГЛАВНОГО ОКНА
**Файл:** `src/ui/main_window.py`

### 1.1 Создать вертикальный сплиттер
```python
# БЫЛО: docks слева/справа
# СТАЛО: QSplitter(Qt.Vertical)
#   - Верх: 3D сцена
#   - Низ: Графики (на всю ширину)
```

### 1.2 Переместить panels в QTabWidget
```python
# Создать QTabWidget справа (вместо доков):
tab_widget = QTabWidget()
tab_widget.addTab(scroll_geometry, "Геометрия")
tab_widget.addTab(scroll_pneumo, "Пневмосистема")
tab_widget.addTab(scroll_modes, "Режимы стабилизатора")
tab_widget.addTab(scroll_viz, "Визуализация")
tab_widget.addTab(scroll_road, "Динамика движения")
```

### 1.3 Обернуть каждую панель в QScrollArea
```python
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setWidget(panel)
```

## ШАГ 2: ПОЛНАЯ РУСИФИКАЦИЯ
**Файлы:** Все панели + main_window.py

### 2.1 Заголовки окон/доков
- "Geometry" ? "Геометрия"
- "Pneumatics" ? "Пневмосистема"
- "Charts" ? "Графики"
- "Simulation & Modes" ? "Режимы стабилизатора"
- "Road Profiles" ? "Динамика движения"

### 2.2 Меню
- "File" ? "Файл"
- "Road" ? "Дорога" (скрыть или переименовать)
- "Parameters" ? "Параметры"
- "View" ? "Вид"

### 2.3 Toolbar
- "Start" ? "Старт"
- "Stop" ? "Стоп"
- "Pause" ? "Пауза"
- "Reset" ? "Сброс"

### 2.4 Status Bar
- "Sim Time" ? "Время"
- "Steps" ? "Шаги"
- "Physics FPS" ? "FPS физики"
- "RT" ? "РВ" (реальное время)
- "Queue" ? "Очередь"

### 2.5 Единицы измерения
- mm (миллиметры)
- m (метры)
- bar (бары)
- ° (градусы)
- см? (кубические сантиметры)

## ШАГ 3: ГРАФИКИ ВНИЗУ НА ВСЮ ШИРИНУ
**Файл:** `src/ui/main_window.py`

```python
# Создать вертикальный сплиттер:
splitter = QSplitter(Qt.Vertical)
splitter.addWidget(qquick_widget)  # 3D сцена
splitter.addWidget(chart_widget)   # Графики
splitter.setStretchFactor(0, 3)    # Сцена 60%
splitter.setStretchFactor(1, 2)    # Графики 40%
```

## ШАГ 4: СКРЫТЬ ROAD PANEL
**Файлы:** `src/ui/main_window.py`, `src/ui/panels/panel_road.py`

- Не добавлять RoadPanel в вкладки
- Создать заглушку "Динамика движения" (пустая вкладка)
- Скрыть меню "Road" или переименовать

## ШАГ 5: ЛОГИРОВАНИЕ И ТРЕЙСИНГ
**Новый файл:** `src/ui/ui_logger.py`

```python
# Логировать каждое изменение контрола:
# timestamp | widget_path | objectName | label | old_value | new_value
```

## ШАГ 6: АВТОТЕСТЫ
**Файл:** `tests/ui/test_ui_layout.py`

```python
def test_tabs_exist(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    # Проверить наличие вкладок
    tab_widget = window.findChild(QTabWidget)
    assert tab_widget is not None
    assert tab_widget.count() == 5
    assert tab_widget.tabText(0) == "Геометрия"
    # ...
```

## ШАГ 7: ПОСЛЕИЗМЕНЕНЧЕСКИЙ АУДИТ
- Повторить аудит ? `ui_audit_post.md`
- Дамп дерева ? `widget_tree_post.json`
- Сводный отчёт ? `summary_prompt1.md`

## ШАГ 8: СОХРАНЕНИЕ
```bash
git checkout -b feature/ui-rus-tabs-layout
git add .
git commit -m "UI: Russian labels, tabs layout, charts bottom; no accordions; scroll areas; value tracing (PROMPT #1)"
git push origin feature/ui-rus-tabs-layout
```

## КРИТЕРИИ ГОТОВНОСТИ:
? Все панели в вкладках (QTabWidget)
? Графики внизу на всю ширину (вертикальный splitter)
? Нет аккордеонов
? Весь UI на русском
? Крутилки/слайдеры сохранены
? Скроллбары при переполнении
? Автотесты прошли
? Отчёты и логи собраны
? Коммит/пуш выполнены

## ТЕКУЩИЙ СТАТУС:
**STEP:** 0 (Audit) COMPLETE ?
**NEXT:** Step 1 (Restructure main window) ? READY TO START

---
**Время начала:** 2025-10-05 19:00
**Аудит завершён:** 2025-10-05 19:05
