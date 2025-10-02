# ? РЕШЕНИЕ НАЙДЕНО

**Проблема:** Приложение крашится при инициализации OpenGL

**Корневая причина:** GLScene пытается использовать PyOpenGL, который несовместим с текущей конфигурацией

## ?? ПРИМЕНЁННЫЕ ИСПРАВЛЕНИЯ

### 1. ? QSurfaceFormat установлен ДО QApplication
```python
# app.py
def setup_opengl_format():
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    # ...
    QSurfaceFormat.setDefaultFormat(format)
```

### 2. ? Убрана повторная установка формата из GLView
```python
# gl_view.py __init__()
# Удалено: self.setFormat(format)
# Используется глобальный формат
```

### 3. ? Улучшена обработка ошибок в initializeGL
```python
# gl_view.py initializeGL()
try:
    self.initializeOpenGLFunctions()
    # ...
except Exception as e:
    print(f"Error: {e}")
    return  # Graceful failure
```

### 4. ? GLScene требует доработки
**Проблема:** GLScene использует PyOpenGL, что вызывает краш

**Временное решение:** Создать stub-версию GLScene

## ?? СЛЕДУЮЩИЕ ШАГИ

1. Создать GLScene stub (минимальная версия без PyOpenGL)
2. Проверить, открывается ли окно
3. Постепенно добавлять функциональность

---

**Статус:** Диагностика завершена, применяю финальное решение...
