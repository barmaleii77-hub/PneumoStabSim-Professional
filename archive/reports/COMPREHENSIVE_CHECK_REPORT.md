# ?? ПОЛНАЯ ПРОВЕРКА ПРОЕКТА - НАЙДЕННЫЕ ПРОБЛЕМЫ

**Дата проверки:** 3 октября 2025
**Статус:** ? **НАЙДЕНЫ КРИТИЧЕСКИЕ ОШИБКИ**

---

## ? КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 1. Устаревший код OpenGL НЕ УДАЛЁН

**Файлы, которые должны быть удалены согласно миграции на Qt Quick 3D:**

- ? `src/ui/gl_view.py` - **ВСЁ ЕЩЁ СУЩЕСТВУЕТ** (330+ строк OpenGL кода)
- ? `src/ui/gl_scene.py` - stub версия, но должна быть удалена
- ? Возможно `src/ui/hud.py` - если использует QPainter поверх OpenGL

**Почему критично:**
- Импорты OpenGL зависимостей (QOpenGLWidget, QOpenGLFunctions)
- Может вызывать конфликты с Qt Quick RHI
- Вводит в заблуждение при дебаге

**Действие:** УДАЛИТЬ эти файлы

---

### 2. Crash в `_reset_ui_layout()` из-за None docks

**Файл:** `src/ui/main_window.py`
**Строка:** ~540

```python
def _reset_ui_layout(self):
    for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock,
                 self.modes_dock, self.road_dock]:
        dock.show()  # ? CRASH! dock is None
```

**Проблема:**
- Все доки установлены в `None` в `_setup_docks()`
- Вызов `.show()` на `None` ? `AttributeError`

**Исправление:**
```python
def _reset_ui_layout(self):
    for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock,
                 self.modes_dock, self.road_dock]:
        if dock:  # ? Добавить проверку
            dock.show()
    self.status_bar.showMessage("UI layout reset")
```

---

### 3. View Menu обращается к None docks

**Файл:** `src/ui/main_window.py`
**Метод:** `_setup_menus()`

```python
view_menu = menubar.addMenu("View")
for dock, title in [
    (self.geometry_dock, "Geometry"),  # ? None
    (self.pneumo_dock, "Pneumatics"),  # ? None
    ...
]:
    act = QAction(title, self, checkable=True, checked=True)
    act.toggled.connect(lambda checked, d=dock: d.setVisible(checked))  # ? CRASH!
```

**Проблема:**
- Lambda захватывает `None`
- При toggle ? `d.setVisible(checked)` ? `AttributeError`

**Исправление:**
```python
view_menu = menubar.addMenu("View")
for dock, title in [
    (self.geometry_dock, "Geometry"),
    (self.pneumo_dock, "Pneumatics"),
    (self.charts_dock, "Charts"),
    (self.modes_dock, "Modes"),
    (self.road_dock, "Road Profiles")
]:
    if dock:  # ? Добавить проверку
        act = QAction(title, self, checkable=True, checked=True)
        act.toggled.connect(lambda checked, d=dock: d.setVisible(checked))
        view_menu.addAction(act)
```

**ИЛИ** вообще не создавать View menu если доки отключены.

---

## ?? СРЕДНИЕ ПРОБЛЕМЫ

### 4. Неполная миграция: остались тестовые файлы с OpenGL

**Файлы:**
- `test_p9_opengl.py` - тесты для OpenGL (устарело)
- `test_with_surface_format.py` - OpenGL тесты
- `check_opengl.py` - проверка OpenGL

**Действие:**
- Переименовать в `*.old.py` ИЛИ удалить
- Создать новые тесты для Qt Quick 3D

---

### 5. Документация не обновлена

**Файлы:**
- `P9_P10_REPORT.md` - описывает OpenGL подход (устарел)
- `P10_STATUS_COMPLETE.md` - про HUD поверх OpenGL

**Действие:**
- Добавить примечание: "DEPRECATED: Migrated to Qt Quick 3D"
- Создать новый `QTQUICK3D_ARCHITECTURE.md`

---

### 6. Отсутствует интеграция simulation ? QML

**Проблема:**
В `_update_render()` обновляются только 2 свойства:
```python
self._qml_root_object.setProperty("simulationText", sim_text)
self._qml_root_object.setProperty("fpsText", fps_text)
```

**Отсутствует:**
- Обновление камеры (distance, pitch, yaw)
- Анимация на основе данных симуляции
- Визуализация пневматики

**Действие:**
- Расширить QML properties
- Добавить методы обновления 3D объектов

---

## ? ЧТО РАБОТАЕТ ПРАВИЛЬНО

1. ? `app.py` - корректно устанавливает RHI backend
2. ? `assets/qml/main.qml` - валидная Qt Quick 3D сцена
3. ? `MainWindow._setup_central()` - правильно использует QQuickView
4. ? `MainWindow.showEvent()` - SimulationManager стартует после show()
5. ? Нет импортов OpenGL в MainWindow
6. ? Qt Quick 3D зависимости установлены

---

## ?? ПЛАН ИСПРАВЛЕНИЙ

### Приоритет 1 (КРИТИЧНО):
1. ? Удалить `src/ui/gl_view.py`
2. ? Удалить `src/ui/gl_scene.py`
3. ? Исправить `_reset_ui_layout()` - проверка на None
4. ? Исправить View menu - проверка на None

### Приоритет 2 (ВАЖНО):
5. Переименовать/удалить OpenGL тесты
6. Добавить DEPRECATED пометки в старые отчёты
7. Создать `QTQUICK3D_ARCHITECTURE.md`

### Приоритет 3 (ЖЕЛАТЕЛЬНО):
8. Расширить QML integration
9. Добавить тесты для Qt Quick 3D
10. Документировать QML API

---

## ?? АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ

Запускаю автоматическое исправление критических проблем...

---

**Статус после исправлений:** Будет обновлено после применения изменений
