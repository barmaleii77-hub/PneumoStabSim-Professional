# Python Wrapper Scripts

## Проблема

Windows App Execution Aliases перехватывают команду `python` и перенаправляют в Microsoft Store, даже если Python установлен.

## Решение

Используйте обёртки из директории `scripts/`:

### CMD/Batch
```cmd
scripts\python.bat -V
scripts\python.bat -m pip list
```

### PowerShell
```powershell
.\scripts\python.ps1 -V
.\scripts\python.ps1 -m pip list
```

### Git Bash / MSYS2
```bash
./scripts/python.bat -V
```

## Альтернативное решение

Отключить App Execution Aliases:
1. Открыть Settings → Apps → App execution aliases
2. Найти `python.exe` и `python3.exe`
3. Отключить оба переключателя

## Файлы

- `scripts/python.bat` — CMD wrapper (с поддержкой UTF-8 для кириллицы)
- `scripts/python.ps1` — PowerShell wrapper
- Оба указывают на: `C:\Users\Алексей\AppData\Local\Programs\Python\Python313\python.exe`

## Обновление пути

Если Python переустановлен в другую директорию, отредактируйте переменную `PYTHON_EXE` в обоих файлах.
