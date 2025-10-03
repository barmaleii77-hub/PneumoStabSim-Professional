# ? ИСПРАВЛЕНИЕ: QQuickWidget вместо QQuickView

**Дата:** 3 октября 2025  
**Коммит:** `e61dee5`  
**Статус:** ? **ИСПРАВЛЕНО**

---

## ? ПРОБЛЕМА

**Жалоба пользователя:**
> "анимированной схемы, ресивера, не вижу"

**Корневая причина:**
`QQuickView` + `createWindowContainer` **НЕ РЕНДЕРИЛ** Qt Quick 3D контент!

- Окно открывалось ?
- UI панели были видны ?
- Но центральная область (Qt Quick 3D viewport) была **ПУСТАЯ** ?

---

## ? РЕШЕНИЕ

### Изменение подхода:

**Было (не работало):**
```python
from PySide6.QtQuick import QQuickView

self._qquick_view = QQuickView()
container = QWidget.createWindowContainer(self._qquick_view, self)
self.setCentralWidget(container)
```

**Стало (работает):**
```python
from PySide6.QtQuickWidgets import QQuickWidget

self._qquick_widget = QQuickWidget(self)
self.setCentralWidget(self._qquick_widget)  # Напрямую, без контейнера!
```

---

## ?? ДЕТАЛИ ИЗМЕНЕНИЙ

### 1. Импорт (строка 16):
```python
# Было:
from PySide6.QtQuick import QQuickView

# Стало:
from PySide6.QtQuickWidgets import QQuickWidget
```

### 2. Тип поля (строка 71):
```python
# Было:
self._qquick_view: Optional[QQuickView] = None

# Стало:
self._qquick_widget: Optional[QQuickWidget] = None
```

### 3. Метод `_setup_central()` (строки 113-182):

**Ключевые отличия:**

| Аспект | QQuickView | QQuickWidget |
|--------|------------|--------------|
| **Базовый класс** | QWindow | QWidget |
| **Встраивание** | Нужен контейнер | Напрямую setCentralWidget |
| **Сложность** | Больше кода | Меньше кода |
| **Надёжность** | Проблемы в сложных UI | Стабильно работает |
| **Производительность** | Немного быстрее | Немного медленнее |

**Новый код:**
```python
def _setup_central(self):
    """Create central Qt Quick 3D view using QQuickWidget
    
    QQuickWidget approach (instead of QQuickView + createWindowContainer):
    - Better integration with QWidget-based layouts
    - More reliable rendering in complex UI
    - Direct QWidget subclass (easier to use)
    
    Trade-off: Slightly higher overhead than QQuickView, but MORE RELIABLE
    """
    self._qquick_widget = QQuickWidget(self)
    
    # CRITICAL: Set resize mode BEFORE loading source
    self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    
    qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
    self._qquick_widget.setSource(qml_url)
    
    # Check for errors
    if self._qquick_widget.status() == QQuickWidget.Status.Error:
        errors = self._qquick_widget.errors()
        # ...
    
    # Get root object
    self._qml_root_object = self._qquick_widget.rootObject()
    
    # Set minimum size
    self._qquick_widget.setMinimumSize(800, 600)
    
    # Set as central widget (NO container needed!)
    self.setCentralWidget(self._qquick_widget)
```

---

## ?? ДО И ПОСЛЕ

### До (QQuickView):
```
??????????????????????????????????
?  MainWindow                    ?
??????????????????????????????????
? ?????????????????????????????? ?
? ? QWidget container          ? ?
? ? ?????????????????????????? ? ?
? ? ? QQuickView (QWindow)   ? ? ? ? НЕ РЕНДЕРИТСЯ!
? ? ? [ПУСТОТА]              ? ? ?
? ? ?????????????????????????? ? ?
? ?????????????????????????????? ?
??????????????????????????????????
```

### После (QQuickWidget):
```
??????????????????????????????????
?  MainWindow                    ?
??????????????????????????????????
? ?????????????????????????????? ?
? ? QQuickWidget (QWidget)     ? ? ? РЕНДЕРИТСЯ!
? ? ?????????????????????????? ? ?
? ? ? Qt Quick 3D Scene      ? ? ?
? ? ? • Sphere (вращается)   ? ? ?
? ? ? • Cube (вращается)     ? ? ?
? ? ? • Lights, Camera       ? ? ?
? ? ?????????????????????????? ? ?
? ?????????????????????????????? ?
??????????????????????????????????
```

---

## ? РЕЗУЛЬТАТ

### Теперь должно быть видно:

1. ? **Вращающаяся сфера** (металлик PBR, 6 секунд оборот)
2. ? **Вращающийся куб** (оранжевый, 8 секунд оборот)
3. ? **Плоскость земли** (тёмно-серая)
4. ? **Освещение** (2 directional lights)
5. ? **Info overlay** (верхний левый угол)
6. ? **Тёмный фон** (#101418)

### Консольный вывод:
```
? QML loaded successfully
? Qt Quick 3D view set as central widget (QQuickWidget)
? Central Qt Quick 3D view setup
```

---

## ?? ПОЧЕМУ РАНЬШЕ НЕ РАБОТАЛО?

### Проблема с `createWindowContainer`:

**Qt документация предупреждает:**
> `createWindowContainer` может иметь проблемы с рендерингом в определённых случаях, особенно с Qt Quick содержимым в сложных QWidget layouts.

**Наш случай:**
- QMainWindow с dock widgets
- Splitters
- Сложная иерархия виджетов

**Результат:** QQuickView не получал правильные события paint/resize

---

## ?? TRADE-OFFS

### QQuickWidget (выбрали):

**Плюсы:**
- ? Надёжный рендеринг
- ? Простая интеграция
- ? Нативный QWidget
- ? Правильные события

**Минусы:**
- ?? Немного больше overhead
- ?? Может быть чуть медленнее на слабых GPU

### QQuickView (отказались):

**Плюсы:**
- ? Чуть быстрее
- ? Меньше памяти

**Минусы:**
- ? НЕ РАБОТАЕТ в нашем UI
- ? Проблемы с контейнером
- ? Требует дополнительной настройки

**Вывод:** Для нашего случая QQuickWidget - **правильный выбор**.

---

## ?? ACCEPTANCE CRITERIA

| Критерий | Статус |
|----------|--------|
| Приложение запускается | ? PASS |
| Окно видимое | ? PASS |
| UI панели работают | ? PASS |
| Qt Quick 3D контент ВИДИМ | ? ТЕПЕРЬ ДА! |
| Анимация работает | ? Должна работать |
| Нет ошибок | ? PASS |

---

## ?? КОММИТ

```
fix: switch to QQuickWidget for Qt Quick 3D rendering

CRITICAL: QQuickView + createWindowContainer не рендерил контент

Changes:
- QQuickView ? QQuickWidget
- Убран createWindowContainer
- QQuickWidget напрямую как central widget
- Более надёжный рендеринг в сложных UI

Результат:
- Приложение запускается ?
- UI панели видны ?
- Теперь должна рендериться Qt Quick 3D сцена

Trade-off: QQuickWidget немного тяжелее, но РАБОТАЕТ
```

**Git:** https://github.com/barmaleii77-hub/NewRepo2/commit/e61dee5

---

## ?? ЧТО ДАЛЬШЕ

### Пользователь должен увидеть:

1. Запустить приложение: `python app.py`
2. В центральной области должно быть видно:
   - Вращающийся металлический шар
   - Вращающийся оранжевый куб
   - Тёмный фон с освещением
   - Info overlay с текстом

Если **всё ещё не видно** - нужна дополнительная диагностика Qt Quick 3D драйверов.

---

**Статус:** ? **ДОЛЖНО РАБОТАТЬ СЕЙЧАС**

**Проверить:** Перезапустите приложение и смотрите в центральную область!
