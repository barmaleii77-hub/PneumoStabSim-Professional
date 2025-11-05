# PneumoStabSim - VS Code Configuration README

## Настройки Visual Studio Code для кроссплатформенного `.venv`

Рабочая область настроена на автоматический выбор интерпретатора из виртуального окружения `.venv` (Windows: `.venv\\Scripts\\python.exe`, Linux/macOS: `.venv/bin/python`). Если папка окружения отсутствует, VS Code Insiders откатится к системному `python3.13`.

### Созданные файлы конфигурации:

#### `.vscode/settings.json`
- Кроссплатформенный выбор интерпретатора через ключи `[windows]`, `[linux]`, `[mac]`
- Fallback на системный `python3.13`, если `.venv` не создан
- Настройки форматирования и анализа кода
- Автоматическое определение путей проекта

#### `.vscode/launch.json`
- Конфигурации отладки для различных режимов запуска
- `PYTHONPATH` формируется через `${pathSeparator}` и указывает на корень и `src`
- Qt переменные подхватываются из `.env`
- Профили для отладки, тестирования и безопасного режима

#### `.vscode/tasks.json`
- Задачи для сборки и запуска приложения
- Команды автоматически используют `${config:python.defaultInterpreterPath}`
- Qt переменные подгружаются из `.env`, в задачах оставлен только `PYTHONPATH`
- Задачи тестирования и проверки качества

#### `.vscode/extensions.json`
- Рекомендуемые расширения для работы с проектом

### Быстрый запуск в VS Code:

1. **Запуск приложения**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run PneumoStabSim"
2. **Отладка**: `F5` или выберите конфигурацию в панели Debug
3. **Запуск текущего файла**: `Ctrl+F5`

### Доступные команды запуска:

- **Обычный режим**: `./.venv/bin/python app.py` (Linux/macOS) или `.venv\Scripts\python.exe app.py` (Windows)
- **Режим отладки**: `./.venv/bin/python app.py --debug`
- **Тестовый режим**: `./.venv/bin/python app.py --test-mode`
- **Безопасный режим**: `./.venv/bin/python app.py --safe-mode`
- **Устаревший OpenGL**: `./.venv/bin/python app.py --legacy`

### Альтернативные bat-файлы:

- **`run.bat`** – стандартный запуск, который активирует `.venv`
- **`run_py.bat`** – резервный сценарий для систем, где используется Python Launcher (`py`) без предварительно созданного `.venv`

### Проверка готовности интерпретаторов:

- `python3.13 --version` – убедитесь, что системный fallback доступен
- `./.venv/bin/python --version` или `.venv\Scripts\python.exe --version` – проверьте виртуальное окружение

### Проверка конфигурации:

```cmd
# Проверить текущий интерпретатор VS Code
code --status | find "python"

# Запуск тестового режима из виртуального окружения (Linux/macOS)
./.venv/bin/python app.py --test-mode

# Запуск тестового режима в Windows PowerShell
.\.venv\Scripts\python.exe app.py --test-mode
```

### Troubleshooting:

1. **Если `.venv` отсутствует**:
   - Выполните `python3.13 -m venv .venv`
   - Активируйте окружение и установите зависимости `pip install -r requirements.txt`

2. **Проблемы с путями**:
   - Убедитесь, что `PYTHONPATH` содержит `${workspaceFolder}` и `${workspaceFolder}/src`
   - Перезапустите окно VS Code (`Developer: Reload Window`), чтобы перечитать `.env`

3. **Проблемы с кодировкой**:
   - Все файлы настроены на UTF-8
   - Настройки терминала автоматически используют UTF-8

### VS Code Insiders + Copilot Chat

- Используйте последнюю версию VS Code Insiders — она быстрее обновляет поддержку GitHub Copilot Chat и Qt QML Language Server.
- Открыв `PneumoStabSim.code-workspace`, примите рекомендации расширений: `github.copilot`, `github.copilot-chat`, `ms-qttools.qt-language-server`, `ms-python.black-formatter`, `ms-python.mypy-type-checker`.
- После установки войдите в GitHub Copilot, откройте панель *Chat* и протестируйте подсказку `@workspace status` для проверки контекста проекта.
- Изменили `.env` или виртуальное окружение? Выполните `Developer: Reload Window`, чтобы Insiders перечитал Qt переменные и обновил интерпретатор.

### Дополнительные возможности:

- **Code Runner**: Запуск Python-файлов кнопкой "Run Code" (▷)
- **Автоформатирование**: Black formatter при сохранении
- **Линтинг**: Flake8 для проверки кода
- **Автоимпорт**: isort для организации импортов
