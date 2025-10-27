# ✅ VS Code Extensions – Setup Status

## 📋 Summary

`python setup_vscode.py` подготовил каталоги `.vscode/`, проверил конфигурацию и
обновил список рекомендуемых расширений. Для завершения требуется установить VS
Code и применить рекомендации.

## 🎯 Current Status

- ❌ **VS Code**: not installed (manual installation still required)
- ⚠️ **Extensions**: recommendations ready, waiting for installation via VS Code
- ✅ **Documentation**: refreshed with automated workflow details
- ✅ **Automation**: `setup_vscode.py`, `install_extensions.ps1`

## 📦 Prepared Assets

- **Documentation** – [VSCODE_EXTENSIONS_GUIDE.md](VSCODE_EXTENSIONS_GUIDE.md)
  описывает установку VS Code, сценарии автоматизации и проверку конфигурации.
- **Scripts** – `setup_vscode.py` актуализирует `.vscode/*`, а
  `install_extensions.ps1` ставит расширения с помощью CLI.

## 🚀 Next Steps

1. **Install VS Code**
   - Download: https://code.visualstudio.com/download
   - During setup enable «Add to PATH» и «Register Code as an editor».
2. **Bootstrap the workspace**
   ```powershell
   python setup_vscode.py
   .\install_extensions.ps1
   ```
   Команды синхронизируют `.venv`, обновят `extensions.json` и установят 12
   рекомендованных расширений.
3. **Finalise configuration**
   - `Ctrl+Shift+P` → `GitHub Copilot: Sign In`
   - `Ctrl+Shift+P` → `Python: Select Interpreter` → `.venv`
   - Убедитесь, что форматирование Ruff срабатывает при сохранении.

## 📚 Recommended extensions

| Extension | ID | Purpose |
|-----------|-----|---------|
| Python | `ms-python.python` | Core Python tooling |
| Pylance | `ms-python.vscode-pylance` | Language server |
| Debugpy | `ms-python.debugpy` | Debugger backend |
| Ruff | `charliermarsh.ruff` | Formatting + linting |
| Jupyter | `ms-toolsai.jupyter` | Notebook support |
| C/C++ | `ms-vscode.cpptools` | Native tooling |
| CMake Tools | `ms-vscode.cmake-tools` | Build integration |
| PowerShell | `ms-vscode.powershell` | PowerShell terminal |
| Qt Tools | `qt.io.qt-vscode` | Qt/QML authoring |
| Even Better TOML | `tamasfe.even-better-toml` | TOML editing |
| GitHub Copilot | `github.copilot` | AI assistance |
| Copilot Chat | `github.copilot-chat` | Chat-based workflows |

## ✅ Verification checklist

- [ ] VS Code установлен и открывает `PneumoStabSim.code-workspace`
- [ ] Все 12 расширений из таблицы установлены (`Ctrl+Shift+X`)
- [ ] Copilot активен (иконка в статус-баре + предложения при вводе)
- [ ] `Tasks: Run Task` показывает команды Ruff, pytest и qmllint
- [ ] Форматирование на сохранение (`ruff`) работает

## 📖 Reference commands

```powershell
# Проверка версии VS Code
code --version

# Установка отдельного расширения
code --install-extension <extension-id>

# Просмотр установленного списка
code --list-extensions
```

---

**Status:** ⚠️ Waiting for VS Code installation
**Action Required:** Install VS Code → run `python setup_vscode.py` → execute `.\install_extensions.ps1`
**Last Updated:** 2025-02-15
