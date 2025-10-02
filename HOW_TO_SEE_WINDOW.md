# ? ИНСТРУКЦИЯ: КАК УВИДЕТЬ ОКНО ПРИЛОЖЕНИЯ

**Проблема:** Окно создается, но не видно на экране  
**Решение:** ? Окно РАБОТАЕТ! Нужно найти его

---

## ?? ГДЕ ИСКАТЬ ОКНО

### 1. ? Панель задач Windows
- Найдите значок **Python** или **PneumoStabSim** на панели задач
- Кликните на него

### 2. ? Alt+Tab
- Нажмите **Alt+Tab** для переключения между окнами
- Найдите окно "PneumoStabSim - Pneumatic Stabilizer Simulator"

### 3. ? Второй монитор
- Если у вас несколько мониторов, проверьте все экраны
- Окно может открыться на другом мониторе

### 4. ? Диспетчер задач
```powershell
# Проверьте, запущен ли процесс
Get-Process python | Where-Object {$_.MainWindowTitle -like "*Pneumo*"}
```

---

## ?? ЗАПУСК ПРИЛОЖЕНИЯ

### Способ 1: Из Visual Studio
```powershell
# 1. Откройте терминал PowerShell
# 2. Активируйте виртуальную среду
.\.venv\Scripts\Activate.ps1

# 3. Запустите приложение
python app.py
```

### Способ 2: Двойной клик
```powershell
# Создайте ярлык (создан ниже)
# Затем двойной клик по run_app.bat
```

---

## ?? ПРОВЕРКА РАБОТЫ

**После запуска вы должны увидеть:**
```
=== PNEUMOSTABSIM STARTING ===
Step 1: Setting High DPI policy...
Step 2: Creating QApplication...
Step 3: Installing Qt message handler...
Step 4: Setting application properties...
Step 5: Creating MainWindow...
Step 6: MainWindow created - Size: 1500x950
         Window title: PneumoStabSim - Pneumatic Stabilizer Simulator
Step 7: Window shown - Visible: True

============================================================
APPLICATION READY - Close window to exit
Check taskbar or press Alt+Tab if window is not visible
============================================================
```

? **Если видите это - окно создано и работает!**

---

## ?? ЧТО ДОЛЖНО БЫТЬ В ОКНЕ

Главное окно **PneumoStabSim** содержит:

### Центр
- **OpenGL 3D Viewport** (тёмно-синий фон)

### Панели
- **Geometry** (слева) - геометрические параметры
- **Pneumatics** (справа вверху) - пневматика
- **Charts** (справа внизу, вкладка) - графики
- **Modes** (плавающая) - режимы симуляции
- **Road Profiles** (плавающая) - профили дороги

### Меню
- File ? Save/Load Preset, Export
- Road ? Load CSV, Clear Profiles
- Parameters ? Reset UI Layout
- View ? Show/Hide panels

### Toolbar
- Start, Stop, Pause, Reset

### Statusbar
- Sim Time, Steps, FPS, Queue stats

---

## ?? ЕСЛИ ОКНО ВСЁ ЕЩЁ НЕ ВИДНО

### Проблема: Окно за пределами экрана

**Решение:**
1. Нажмите **Alt+Space** когда окно в фокусе
2. Выберите **Move** (M)
3. Используйте стрелки клавиатуры для перемещения
4. Нажмите **Enter**

### Проблема: Окно минимизировано

**Решение:**
- Найдите на панели задач
- Кликните правой кнопкой ? **Maximize** или **Restore**

### Проблема: Окно прозрачное/невидимое

**Решение:**
- Это ошибка драйвера видеокарты
- Обновите драйверы OpenGL
- Или измените настройки в Windows Settings ? Display ? Graphics

---

## ? ПОДТВЕРЖДЕНИЕ РАБОТЫ

**Приложение работает, если:**
- ? В консоли появился "Step 7: Window shown"
- ? Процесс python.exe запущен
- ? Окно есть в Alt+Tab
- ? Логи пишутся в `logs/run.log`

**Для закрытия:**
- Закройте окно приложения (крестик)
- Или нажмите **Ctrl+C** в консоли

---

## ?? ПРИЛОЖЕНИЕ ГОТОВО К РАБОТЕ!

Если вы видите окно - всё работает корректно!
