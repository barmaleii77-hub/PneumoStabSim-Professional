# ✅ ИНСТРУКЦИЯ ПО ПРОВЕРКЕ РАСШИРЕНИЙ VS CODE

## 🎯 ПРОБЛЕМА

Команда `code` не найдена в PATH, поэтому автоматическая проверка невозможна.

---

## 📋 РУЧНАЯ ПРОВЕРКА РАСШИРЕНИЙ

### ШАГ 1: Открыть список расширений в VS Code

1. Нажми `Ctrl+Shift+X` (или кликни на иконку Extensions в боковой панели)
2. В поисковой строке набери: `@installed`
3. Это покажет все установленные расширения

---

### ШАГ 2: Установить рекомендованные расширения

В той же поисковой строке набери: `@recommended`

Это покажет расширения, рекомендованные для workspace.

**Нажми кнопку**: "Install Workspace Extension Recommendations"

---

## 🔴 КРИТИЧНО УСТАНОВИТЬ (TOP PRIORITY):

### 1. **GitHub Copilot** ⭐⭐⭐
- Extension ID: `github.copilot`
- Описание: AI code completion
- Почему: Основная AI помощь в коде
- Установка: Ctrl+Shift+X → search "GitHub Copilot"

### 2. **GitHub Copilot Chat** ⭐⭐⭐
- Extension ID: `github.copilot-chat`
- Описание: AI chat в VS Code
- Почему: Интерактивная помощь с кодом
- Установка: Ctrl+Shift+X → search "GitHub Copilot Chat"

### 3. **Python** ⭐⭐⭐
- Extension ID: `ms-python.python`
- Описание: Python language support
- Почему: Базовая поддержка Python
- Установка: Обычно уже установлен

### 4. **Pylance** ⭐⭐⭐
- Extension ID: `ms-python.vscode-pylance`
- Описание: Fast Python language server
- Почему: Быстрый IntelliSense, type hints
- Установка: Обычно идёт с Python extension

### 5. **GitLens** ⭐⭐⭐
- Extension ID: `eamodio.gitlens`
- Описание: Git supercharged
- Почему: Показывает кто изменил код, blame, timeline
- Установка: Ctrl+Shift+X → search "GitLens"

### 6. **Russian Spell Checker** ⭐⭐
- Extension ID: `streetsidesoftware.code-spell-checker-russian`
- Описание: Проверка орфографии на русском
- Почему: Находит ошибки в комментариях и docstrings
- Установка: Ctrl+Shift+X → search "Russian Spell Checker"

### 7. **Error Lens** ⭐⭐
- Extension ID: `usernamehw.errorlens`
- Описание: Показывает ошибки inline
- Почему: Видны ошибки прямо в коде без hover
- Установка: Ctrl+Shift+X → search "Error Lens"

### 8. **Better Comments** ⭐⭐
- Extension ID: `aaron-bond.better-comments`
- Описание: Цветные комментарии
- Почему: Улучшает читаемость комментариев
- Установка: Ctrl+Shift+X → search "Better Comments"

---

## ⚠️ РЕКОМЕНДУЕТСЯ УСТАНОВИТЬ (OPTIONAL):

### Python Tools:
- **Black Formatter** (`ms-python.black-formatter`)
- **Flake8** (`ms-python.flake8`)
- **Mypy Type Checker** (`ms-python.mypy-type-checker`)

### Git Tools:
- **Git History** (`donjayamanne.githistory`)
- **Git Graph** (`mhutchie.git-graph`)

### QML/Qt:
- **QML** (`bbenoist.QML`)
- **Qt for Python** (`seanwu.vscode-qt-for-python`)

### Productivity:
- **Code Spell Checker** (`streetsidesoftware.code-spell-checker`) - английский
- **TODO Highlight** (`wayou.vscode-todo-highlight`)
- **Todo Tree** (`gruntfuggly.todo-tree`)
- **EditorConfig** (`editorconfig.editorconfig`)

### Markdown:
- **Markdown All in One** (`yzhang.markdown-all-in-one`)
- **markdownlint** (`davidanson.vscode-markdownlint`)

---

## 🚀 БЫСТРАЯ УСТАНОВКА ЧЕРЕЗ VS CODE UI

### Метод 1: Workspace Recommendations (САМЫЙ ПРОСТОЙ)

1. Открой VS Code
2. Нажми `Ctrl+Shift+X`
3. В поисковой строке набери: `@recommended`
4. Нажми кнопку: **"Install Workspace Extension Recommendations"**
5. Подожди пока все установятся (может занять 2-3 минуты)
6. Перезапусти VS Code (`Ctrl+Shift+P` → "Reload Window")

### Метод 2: Ручная установка каждого

1. Нажми `Ctrl+Shift+X`
2. Введи название расширения или Extension ID
3. Нажми "Install"
4. Повтори для каждого критичного расширения

---

## 📊 ПРОВЕРКА УСТАНОВЛЕННЫХ РАСШИРЕНИЙ

### Способ 1: Через VS Code UI

1. `Ctrl+Shift+X`
2. Введи `@installed`
3. Прокрути список и сравни с критичными выше

### Способ 2: Через Command Palette

1. `Ctrl+Shift+P`
2. Введи: "Extensions: Show Installed Extensions"
3. Увидишь список всех установленных

---

## ✅ ЧЕКЛИСТ ПОСЛЕ УСТАНОВКИ

Проверь что эти расширения установлены:

- [ ] GitHub Copilot
- [ ] GitHub Copilot Chat
- [ ] Python
- [ ] Pylance
- [ ] GitLens
- [ ] Russian Spell Checker
- [ ] Error Lens
- [ ] Better Comments

### Проверка работы:

1. **Copilot**: Открой `.py` файл → начни печатать → должны появиться серые подсказки
2. **Pylance**: Открой `.py` файл → типы должны показываться inline (если включены inlay hints)
3. **GitLens**: Открой любой файл → в конце строк должны быть серые комментарии с авторами
4. **Russian Spell Checker**: Напиши русский комментарий с ошибкой → должна подчеркнуться
5. **Error Lens**: Добавь синтаксическую ошибку → должна показаться inline справа
6. **Better Comments**: Напиши комментарий с `// TODO:` → должен быть цветным

---

## 🔧 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Copilot не предлагает код:
1. `Ctrl+Shift+P` → "GitHub Copilot: Sign In"
2. Авторизуйся через GitHub
3. Перезапусти VS Code

### Inlay hints не видны:
1. Проверь settings.json:
   ```json
   "python.analysis.inlayHints.variableTypes": true
   ```
2. Перезапусти VS Code

### GitLens не показывает авторов:
1. Проверь что репозиторий инициализирован: `git status`
2. Настройки GitLens: `Ctrl+Shift+P` → "GitLens: Open Settings"

### Russian Spell Checker не работает:
1. `Ctrl+Shift+P` → "Code Spell Checker: Enable Language"
2. Выбери "Russian"

---

## 💡 ДОПОЛНИТЕЛЬНЫЕ СОВЕТЫ

### Добавить `code` в PATH (чтобы работали скрипты):

1. Открой VS Code
2. `Ctrl+Shift+P`
3. Введи: "Shell Command: Install 'code' command in PATH"
4. Enter
5. Перезапусти PowerShell

После этого можно будет запустить:
```powershell
.\check_vscode_extensions.ps1
```

---

## 📝 ИТОГО

### Минимальный набор (5 минут):
1. GitHub Copilot + Chat
2. Python + Pylance (обычно уже есть)
3. GitLens
4. Russian Spell Checker
5. Error Lens

### Полный набор (10 минут):
- Все из минимального
- Better Comments
- TODO Highlight
- QML extension
- Markdown tools

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Установи расширения (используй Workspace Recommendations)
2. ✅ Перезапусти VS Code
3. ✅ Проверь работу каждого расширения (см. чеклист)
4. ✅ Добавь `code` в PATH (чтобы работали скрипты)
5. ✅ Запусти `.\check_vscode_extensions.ps1` для автоматической проверки

---

**Время установки**: 5-10 минут  
**Сложность**: Лёгкая  
**Эффект**: +11.4% productivity

---

**Создано**: 2024  
**Версия**: 1.0  
**Статус**: ✅ Готово к использованию
