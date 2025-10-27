# VS Code Extensions – Installation Guide

## ✅ Repository-provided configuration

- Запустите `python setup_vscode.py`, чтобы автоматически создать каталог
  `.vscode/`, проверить JSON-файлы и обновить список рекомендуемых расширений.
- Скрипт одновременно выполняет `uv sync`, поэтому рабочее окружение и
  интерпретатор `.venv` всегда готовы к использованию из VS Code.
- После запуска откройте `PneumoStabSim.code-workspace` — все настройки
  (интерпретатор, задачи, конфигурации F5) уже подключены.

## 📥 Установка VS Code (если ещё не установлен)

**Download:** https://code.visualstudio.com/download

**Windows Installation:**
1. Скачайте User Installer (64-bit).
2. Запустите установщик.
3. ✅ Отметьте «Add to PATH».
4. ✅ Отметьте «Register Code as an editor for supported file types».
5. Завершите установку и перезапустите терминал.

## 📦 Рекомендуемые расширения

Эти 12 расширений зафиксированы в `.vscode/extensions.json` и синхронизируются
скриптом `setup_vscode.py`.

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension charliermarsh.ruff
code --install-extension ms-toolsai.jupyter
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cmake-tools
code --install-extension ms-vscode.powershell
code --install-extension qt.io.qt-vscode
code --install-extension tamasfe.even-better-toml
code --install-extension github.copilot
code --install-extension github.copilot-chat
```

## 🚀 Быстрый старт после установки VS Code

1. Выполните `python setup_vscode.py` (повторно, если уже запускали до установки
   VS Code) — файл `extensions.json` гарантированно актуален.
2. Запустите `.\install_extensions.ps1` для пакетной установки расширений или
   выполните приведённые выше команды `code --install-extension`.
3. Перезапустите VS Code и откройте рабочую область `PneumoStabSim.code-workspace`.

## ⚙️ Настройка после установки расширений

### 1. GitHub Copilot
- `Ctrl+Shift+P` → `GitHub Copilot: Sign In` и выполните вход.
- Убедитесь, что иконка Copilot отображается в статус-баре.

### 2. Интерпретатор Python
- `Ctrl+Shift+P` → `Python: Select Interpreter`.
- Выберите `${workspaceFolder}/.venv/bin/python`
  (или `${workspaceFolder}\\.venv\\Scripts\\python.exe` на Windows).

### 3. Проверка ключевых настроек
Файл `.vscode/settings.json` уже включает необходимые параметры, в том числе
привязку интерпретатора и Python path:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/src",
    "${workspaceFolder}/tests",
    "${workspaceFolder}/tools"
  ],
  "editor.formatOnSave": true,
  "files.encoding": "utf8"
}
```

Дополнительно терминал в VS Code автоматически активирует `.venv`, подставляет
Qt-переменные (`QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`) и включает UTF-8.

## 📋 Чек-лист проверки

- [ ] Запускается VS Code и открывается рабочая область.
- [ ] Все 12 расширений установлены (`Ctrl+Shift+X`).
- [ ] При открытии `.py` и `.qml` файлов активна подсветка синтаксиса.
- [ ] Copilot предлагает подсказки и доступен чат.
- [ ] Команда `Tasks: Run Task` показывает задачи Ruff, pytest и qmllint.
- [ ] Форматирование на сохранение (`ruff`) работает из коробки.

## 🔍 Если возникли проблемы

- **VS Code не в PATH:** выполните установку с опцией «Add to PATH» и перезапустите
  терминал.
- **Расширения не устанавливаются:** убедитесь в наличии сети, затем перезапустите
  VS Code и повторите команды `code --install-extension`.
- **Copilot неактивен:** выполните повторный вход через палитру команд, проверьте
  наличие действующей подписки на GitHub Copilot.

## 📚 Связанные файлы

- `.vscode/extensions.json` — список рекомендаций, обновляемый скриптом.
- `.vscode/settings.json` — фиксация интерпретатора, Qt-переменных и форматирования.
- `.vscode/launch.json` — конфигурации F5 для запуска приложения и тестов.
- `setup_vscode.py` и `install_extensions.ps1` — автоматизация настройки IDE.

---

**Status:** ✅ Конфигурация подготовлена. Установите VS Code, выполните
`python setup_vscode.py`, затем установите рекомендованные расширения.
**Last Updated:** 2025-02-15
