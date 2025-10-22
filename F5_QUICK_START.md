# 🚀 Руководство по быстрому запуску F5 - PneumoStabSim Professional

## ⚡ Мгновенный запуск в любой IDE

Нажмите **F5** в любой IDE для запуска PneumoStabSim Professional с автоматической настройкой окружения!

---

## 🎯 Инструкции для различных IDE

### 🟦 Visual Studio 2022

1. **Откройте проект**: `PneumoStabSim.sln`
2. **Нажмите F5** для запуска с отладкой
3. **Ctrl+F5** для запуска без отладки

**Доступные конфигурации:**
- `Debug` - полная отладка с Qt логами
- `Release` - оптимизированный запуск
- `SafeMode` - безопасный режим без 3D

### 🟨 VS Code

1. **Откройте папку проекта**
2. **Нажмите F5** или **Ctrl+F5**
3. **Выберите конфигурацию** из выпадающего меню

**Доступные конфигурации:**
- 🚀 **PneumoStabSim: Main** - основной режим (по умолчанию)
- 🐛 **PneumoStabSim: Debug Mode** - полная отладка
- 🛡️ **PneumoStabSim: Safe Mode** - без 3D функций
- ⚡ **PneumoStabSim: Performance Monitor** - с мониторингом
- 🧪 **PneumoStabSim: Test Mode (5s)** - тестовый режим
- 🔧 **Apply Patches** - применение патчей

### 🟩 PyCharm

1. **Откройте папку как проект**
2. **Нажмите Shift+F10** или используйте зеленую стрелку
3. **F5 для отладки** после настройки breakpoints

**Конфигурации создаются автоматически:**
- 🚀 PneumoStabSim - основной режим
- 🐛 PneumoStabSim (Debug) - отладочный режим
- 🛡️ PneumoStabSim (Safe Mode) - безопасный режим
- ⚡ PneumoStabSim (Performance) - с профилированием

### 🟣 Sublime Text

1. **Откройте**: `PneumoStabSim.sublime-project`
2. **Нажмите Ctrl+B** для сборки/запуска
3. **Выберите вариант** из меню

### 🟠 Другие IDE (Atom, Vim, и т.д.)

Используйте универсальный launcher:
```bash
py universal_f5.py          # Обычный запуск
py universal_f5.py --debug  # Отладочный режим
```

---

## 🔥 Быстрые команды

### Windows Batch файлы
```cmd
F5_Launch.bat           # Быстрый запуск (эквивалент F5)
F5_Launch.bat debug     # Быстрый запуск в режиме отладки
run_pneumostabsim.bat   # Полная настройка + запуск
```

### Python скрипты
```bash
py f5_launch.py                # F5 launcher с автонастройкой
py f5_launch.py --debug        # F5 launcher (отладка)
py universal_f5.py             # Универсальный launcher
py setup_f5.py                 # Настройка F5 для всех IDE
```

### Прямой запуск
```bash
py app.py                      # Базовый запуск
py app.py --debug              # Отладочный режим
py app.py --safe-mode          # Безопасный режим
py app.py --monitor-perf       # С мониторингом производительности
py app.py --test-mode          # Тестовый режим (автозакрытие 5с)
```

---

## 🛠️ Автоматическая настройка

### Первый запуск
```bash
# Автоматическая настройка окружения для всех IDE
py setup_f5.py
```

### Если возникли проблемы
```bash
# Полная настройка окружения разработчика
py setup_dev.py

# Проверка и исправление зависимостей
pip install -r requirements.txt

# Применение патчей
py apply_patches.py
```

---

## 🎮 Горячие клавиши во время отладки

| Клавиша | Действие |
|---------|----------|
| **F5** | Продолжить выполнение |
| **F9** | Установить/убрать breakpoint |
| **F10** | Выполнить следующую строку (Step Over) |
| **F11** | Войти в функцию (Step Into) |
| **Shift+F11** | Выйти из функции (Step Out) |
| **Shift+F5** | Остановить отладку |
| **Ctrl+F5** | Запуск без отладки |

---

## 🔧 Переменные окружения для отладки

Автоматически настраиваются при F5 запуске:

### Обычный режим
```
PYTHONPATH=.;./src
QT_DEBUG_PLUGINS=0
QT_LOGGING_RULES=js.debug=false;qt.qml.debug=false
```

### Отладочный режим
```
PYTHONPATH=.;./src
QT_DEBUG_PLUGINS=1
QT_LOGGING_RULES=*.debug=true;js.debug=true;qt.qml.debug=true
PYTHONDEBUG=1
```

---

## 📊 Мониторинг производительности

При запуске с `--monitor-perf`:
- ⏱️ Время кадра и FPS
- 🧠 Использование памяти
- 🔥 Загрузка CPU
- 📈 Статистика Qt рендеринга

---

## 🚨 Решение проблем

### F5 не работает
1. Убедитесь что выбран правильный интерпретатор Python
2. Запустите `py setup_f5.py`
3. Проверьте `py setup_dev.py`

### Ошибки импорта
```bash
# Переустановка зависимостей
pip install --force-reinstall -r requirements.txt
```

### Qt/PySide6 проблемы
```bash
# Переустановка Qt
pip uninstall PySide6 shiboken6
pip install PySide6>=6.5.0
```

### 3D не работает
```bash
# Запуск в безопасном режиме
py app.py --safe-mode
```

---

## 🎯 Рекомендуемые настройки IDE

### VS Code расширения
- Python
- Python Debugger
- Qt for Python
- EditorConfig for VS Code

### Visual Studio компоненты
- Python Tools for Visual Studio (PTVS)
- Qt Visual Studio Tools

### PyCharm плагины
- Qt for Python
- Requirements

---

**🚀 Нажмите F5 и наслаждайтесь разработкой!**

*Все конфигурации настроены автоматически для максимального удобства разработки.*
