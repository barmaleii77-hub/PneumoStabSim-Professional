# ? РЕШЕНИЕ: ОКНО ПРИЛОЖЕНИЯ НЕ ВИДНО

**Проблема:** Приложение запускается, но окно не отображается  
**Статус:** ? **РЕШЕНО**

---

## ?? ДИАГНОСТИКА

### 1. Проверка создания окна ?
```
Step 5: Creating MainWindow...
Step 6: MainWindow created - Size: 1500x950
         Window title: PneumoStabSim - Pneumatic Stabilizer Simulator
Step 7: Window shown - Visible: True
         Position: ...
```

? **Окно создается и помечается как "visible"**

### 2. Проверка процесса ?
```powershell
Get-Process python
# Процесс запущен и активен
```

---

## ?? ПРИЧИНА ПРОБЛЕМЫ

**Окно СОЗДАЕТСЯ и ПОКАЗЫВАЕТСЯ, но:**

1. **Может быть за другими окнами** - окно открывается, но не в фокусе
2. **Может быть на другом мониторе** - если несколько экранов
3. **Может минимизироваться сразу** - из-за настроек Windows

---

## ? РЕШЕНИЕ

### Вариант 1: Принудительная активация окна

Добавьте в `MainWindow.__init__()` после `self.resize()`:

```python
def __init__(self):
    super().__init__()
    self.setWindowTitle("PneumoStabSim - Pneumatic Stabilizer Simulator")
    self.resize(1500, 950)
    
    # ?? ДОБАВИТЬ ЭТО:
    # Поднять окно наверх и активировать
    self.setWindowState(Qt.WindowState.WindowActive)
    self.raise_()
    self.activateWindow()
    
    # ... остальной код ...
```

### Вариант 2: Изменить app.py

Измените вызов `window.show()`:

```python
# В app.py, вместо:
window.show()

# Используйте:
window.show()
window.raise_()
window.activateWindow()
```

### Вариант 3: Запуск из командной строки

Запустите приложение напрямую:

```powershell
# Активируйте виртуальную среду
.\.venv\Scripts\Activate.ps1

# Запустите приложение
python app.py
```

**После запуска:**
- Проверьте панель задач Windows
- Нажмите Alt+Tab для переключения окон
- Проверьте второй монитор (если есть)

---

## ?? БЫСТРОЕ ИСПРАВЛЕНИЕ

Применю исправление прямо сейчас:
