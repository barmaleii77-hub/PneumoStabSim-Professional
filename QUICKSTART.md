# ⚡ БЫСТРЫЙ СТАРТ - PneumoStabSim Professional

## ✅ Окружение настроено и готово!

### Текущая конфигурация:

- **Python**: 3.13.8
- **PySide6**: 6.10.0
- **Qt**: 6.10.0
- **NumPy**: 2.3.4
- **SciPy**: 1.16.2
- **Виртуальное окружение**: `venv` (активно)
- **Graphics Backend**: Direct3D 11

---

## 🚀 Запуск приложения

### Метод 1: F5 в VS Code (РЕКОМЕНДУЕТСЯ)

1. Откройте `app.py` в VS Code
2. Нажмите **F5** (или меню Debug → Start Debugging)
3. Выберите конфигурацию:
   - **F5: PneumoStabSim (Главный)** - основной запуск
   - **F5: Verbose (подробные логи)** - с debug выводом
   - **F5: Test Mode (5 сек)** - тестовый режим с авто-закрытием

### Метод 2: PowerShell скрипт

```powershell
# Обычный запуск
.\run.ps1

# С подробными логами
.\run.ps1 -Verbose

# Тестовый режим
.\run.ps1 -Test

# Debug режим Qt
.\run.ps1 -Debug
```

**Примечание**: Если ExecutionPolicy блокирует скрипт:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Метод 3: Batch файл (.bat)

Двойной клик на `run.bat` или из командной строки:
```cmd
run.bat
```

### Метод 4: Прямой запуск Python

```powershell
# Активируйте venv
.\venv\Scripts\Activate.ps1

# Запустите приложение
python app.py

# Или напрямую без активации
.\venv\Scripts\python.exe app.py
```

---

## 🔧 VS Code настроено

### Автоматическая активация терминала

При открытии нового терминала в VS Code автоматически:
- ✅ Активируется виртуальное окружение
- ✅ Устанавливаются переменные окружения Qt
- ✅ Настраивается кодировка UTF-8
- ✅ Показываются полезные команды

### Полезные команды в терминале VS Code

После автоактивации доступны:

```powershell
info             # Показать информацию о проекте
run              # Запустить приложение
run -Verbose     # Запустить с логами
test             # Запустить тесты
fmt              # Форматировать код (black)
typecheck        # Проверить типы (mypy)
clean            # Очистить кэш
install          # Установить зависимости
```

### Задачи (Tasks) - Ctrl+Shift+P

Откройте палитру команд (**Ctrl+Shift+P**) и выберите **Tasks: Run Task**:

- ▶️ Запустить PneumoStabSim
- 🧪 Запустить все тесты (pytest)
- 🔍 Проверка типов (mypy)
- ✨ Форматирование кода (black)
- 📦 Установить зависимости (pip)
- 🧹 Очистка кэша Python
- 🔎 Проверка Qt окружения

---

## 🎯 Быстрая проверка

### Тест запуска

```powershell
# Проверка Python
.\venv\Scripts\python.exe --version

# Проверка PySide6/Qt
.\venv\Scripts\python.exe -c "import PySide6.QtCore as QtCore; print(f'PySide6 {QtCore.__version__} (Qt {QtCore.qVersion()})')"

# Проверка импорта модулей
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from src.diagnostics.warnings import log_warning; print('OK')"
```

### Тестовый запуск (авто-закрытие через 5 сек)

```powershell
.\venv\Scripts\python.exe app.py --test-mode
```

---

## 🐛 Отладка

### Настройки VS Code отладчика

Файл `.vscode/launch.json` содержит готовые конфигурации:

1. **F5: PneumoStabSim (Главный)** - основной запуск с отладчиком
   - `justMyCode: false` - отладка внешних библиотек
   - Переменные окружения из `.env`
   - Integrated Terminal

2. **F5: Verbose** - подробные логи
   - `--verbose` аргумент
   - Qt debug логи включены

3. **F5: Test Mode** - авто-закрытие
   - `--test-mode` аргумент
   - Закрывается через 5 секунд

### Брейкпоинты

- Кликните слева от номера строки в редакторе
- Или нажмите **F9** на нужной строке
- При запуске F5 выполнение остановится на брейкпоинте

---

## 📝 Переменные окружения

Файл `.env` автоматически загружается:

```bash
PYTHONPATH=.;src                              # Пути для импорта
PYTHONIOENCODING=utf-8                        # Кодировка
QSG_RHI_BACKEND=d3d11                         # Direct3D 11 (Windows)
QT_AUTO_SCREEN_SCALE_FACTOR=1                 # Auto HiDPI
QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough   # Scaling
QT_ENABLE_HIGHDPI_SCALING=1                   # HiDPI support
PSS_DIAG=1                                    # Диагностика
```

### Изменение настроек Qt

Для debug режима измените в `.env`:
```bash
QSG_INFO=1                                    # Включить Qt логи
QT_LOGGING_RULES=qt.qml.connections=true      # QML debug
```

---

## 🧪 Тестирование

### Запуск тестов

```powershell
# Все тесты
.\venv\Scripts\python.exe -m pytest tests/ -v

# С покрытием
.\venv\Scripts\python.exe -m pytest --cov=src --cov-report=html tests/

# Конкретный файл
.\venv\Scripts\python.exe -m pytest tests/test_geometry.py -v
```

### Через VS Code

- **F5** → выберите **F5: Run Tests (pytest)**
- Или используйте Testing панель (колба слева)

---

## 🔄 Обновление зависимостей

```powershell
# Обновить pip
.\venv\Scripts\python.exe -m pip install --upgrade pip

# Установить/обновить зависимости
.\venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade

# Проверить установленные пакеты
.\venv\Scripts\python.exe -m pip list
```

---

## 📂 Структура проекта

```
PneumoStabSim-Professional/
├── app.py                          # ⚡ ГЛАВНЫЙ ФАЙЛ - точка входа
├── run.ps1                         # 🚀 PowerShell запуск
├── run.bat                         # 🚀 Batch запуск
├── quick_setup.ps1                 # 🔧 Быстрая настройка
├── requirements.txt                # 📦 Зависимости
├── pyproject.toml                 # ⚙️ Конфигурация
├── .env                           # 🌍 Переменные окружения
│
├── venv/                          # 🐍 Виртуальное окружение Python 3.13
│   └── Scripts/
│       └── python.exe             # Python интерпретатор
│
├── src/                           # 📁 Исходный код
│   ├── bootstrap/                # Инициализация Qt/Python
│   ├── core/                     # Геометрия, кинематика
│   ├── simulation/               # Физическая модель
│   ├── ui/                       # Qt/QML мост
│   ├── diagnostics/              # Логирование
│   └── cli/                      # Аргументы командной строки
│
├── assets/                        # 🎨 Ресурсы
│   ├── qml/                      # QML компоненты (3D сцена)
│   │   └── main.qml             # Главная 3D сцена
│   └── hdr/                      # HDR окружение (IBL)
│
├── tests/                         # 🧪 Тесты
│
└── .vscode/                      # 🔧 Конфигурация VS Code
    ├── settings.json             # Настройки редактора
    ├── launch.json               # ⚡ F5 конфигурации
    ├── tasks.json                # Задачи (Ctrl+Shift+P)
    └── profile.ps1               # PowerShell профиль терминала
```

---

## ⚙️ Горячие клавиши VS Code

| Клавиша | Действие |
|---------|----------|
| **F5** | Запуск с отладчиком |
| **Ctrl+F5** | Запуск без отладчика |
| **Shift+F5** | Остановить отладку |
| **F9** | Установить/удалить брейкпоинт |
| **F10** | Step Over (следующая строка) |
| **F11** | Step Into (войти в функцию) |
| **Shift+F11** | Step Out (выйти из функции) |
| **Ctrl+Shift+P** | Палитра команд |
| **Ctrl+`** | Открыть/закрыть терминал |

---

## ❓ Troubleshooting

### Проблема: "python" не распознается

**Решение**: Добавьте Python в PATH или используйте полный путь:
```powershell
.\venv\Scripts\python.exe app.py
```

### Проблема: ExecutionPolicy блокирует .ps1 скрипты

**Решение**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Или используйте `.bat` файлы вместо `.ps1`

### Проблема: Ошибки импорта модулей

**Решение**: Проверьте PYTHONPATH:
```powershell
$env:PYTHONPATH = "$PWD;$PWD\src"
```

### Проблема: Qt не запускается / черный экран

**Решение**: Попробуйте другой graphics backend:
```powershell
$env:QSG_RHI_BACKEND = "opengl"
```

### Проблема: Кракозябры в консоли (кодировка)

**Решение**:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
```

---

## 📚 Дополнительная документация

- `SETUP_GUIDE.md` - Подробное руководство по настройке
- `README.md` - Общая информация о проекте
- `.github/copilot-instructions.md` - Инструкции для разработки

---

## ✅ Чек-лист готовности

- [x] Python 3.13.8 установлен
- [x] Виртуальное окружение `venv` создано
- [x] PySide6 6.10.0 установлен
- [x] NumPy 2.3.4 установлен
- [x] SciPy 1.16.2 установлен
- [x] VS Code настроен (settings.json, launch.json, tasks.json)
- [x] PowerShell профиль настроен (profile.ps1)
- [x] Переменные окружения настроены (.env)
- [x] F5 готов к использованию

---

## 🎉 Готово к работе!

Просто нажмите **F5** в VS Code и начните работу!

Или запустите:
```powershell
.\run.ps1
```

Удачной разработки! 🚀
