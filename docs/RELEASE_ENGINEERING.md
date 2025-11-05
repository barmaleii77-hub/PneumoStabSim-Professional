# Release Engineering Guide

Этот документ описывает последовательность действий для подготовки и
публикации дистрибутивов PneumoStabSim Professional на основных платформах.
Процесс синхронизирован с автоматизированным конвейером GitHub Actions
(`.github/workflows/release.yml`) и унифицированным скриптом упаковки
(`tools/packaging/build_packages.py`).

## 1. Предварительные требования

1. **Python 3.13** — соответствует целевому интерпретатору приложения.
2. **Зависимости проекта** — синхронизируются через `uv`:
   ```bash
   uv sync --all-extras
   ```
   Команда установит базовые зависимости, dev-инструменты и
   дополнительные пакеты для упаковки (`pyinstaller`, `cx-Freeze`).
3. **Qt Runtime** — при локальной сборке убедитесь, что выполнен скрипт
   `python tools/setup_qt.py`, чтобы PyInstaller и cx_Freeze корректно
   обнаружили плагины Qt.

## 2. Унифицированная упаковка

Для любой ОС теперь используется команда:

```bash
make package-all
```

Скрипт автоматически подбирает конфигурацию по текущей платформе и
запускает PyInstaller (Linux/Windows) или cx_Freeze (macOS). Артефакты
располагаются в каталоге `dist/packages` и включают:

- архив (`.tar.gz` для Linux, `.zip` для Windows и macOS);
- файл контрольной суммы SHA-256 (`.sha256`);
- манифест с метаданными (`.json`).

Дополнительные параметры можно передать через переменную `PACKAGE_ARGS`,
например `make package-all PACKAGE_ARGS="--output-dir dist/releases --no-clean"`.

## 3. Проверка контрольных сумм

Каждый архив сопровождается файлом `<имя>.sha256` со строкой вида
`<SHA-256>  <имя файла>`. Проверка выполняется стандартными утилитами.

### Linux/macOS

```bash
cd dist/packages
shasum -a 256 --check *.sha256
```

### Windows (PowerShell)

```powershell
Set-Location dist\packages
Get-ChildItem -Filter '*.sha256' | ForEach-Object {
  $content = (Get-Content $_.FullName).Trim()
  $parts = $content -split '\s+' | Where-Object { $_ }
  $expected = $parts[0]
  $fileName = $parts[-1]
  $actual = (Get-FileHash $fileName -Algorithm SHA256).Hash
  if ($expected.ToLower() -ne $actual.ToLower()) {
    throw "Checksum mismatch for $fileName"
  }
}
```

## 4. Автоматический релиз

Workflow `release.yml` запускается при пуше тега `v*` или вручную.
Каждый раннер (Ubuntu, Windows, macOS) выполняет:

1. `uv sync --frozen --extra release` — установка зависимостей.
2. `make package-all` — сборка платформенного пакета.
3. Проверка контрольных сумм на раннере.
4. Публикация артефактов через `actions/upload-artifact`.

После успешного завершения матрицы job `publish` повторно проверяет
контрольные суммы и загружает архивы, манифесты и подписи в GitHub
Release (`softprops/action-gh-release`).

## 5. Ручная валидация пакетов

Перед публикацией релиза рекомендуется дополнительно:

- Развернуть архив на целевой ОС и запустить приложение с ключом
  `--env-check`, чтобы убедиться в корректности окружения.
- Проверить наличие директорий `assets/`, `config/` и `docs/` рядом с
  исполняемым файлом.
- Убедиться, что `LICENSE` и `README.md` присутствуют в архиве.

## 6. Распространённые проблемы

| Симптом | Причина | Решение |
| --- | --- | --- |
| PyInstaller пропускает Qt плагины | Не установлен Qt runtime | Выполнить `python tools/setup_qt.py` перед упаковкой |
| Ошибка `cx_Freeze` на macOS | Не собран wheel `lief` | Запустить `uv sync --extra release` повторно; при необходимости
  установить Xcode Command Line Tools |
| Несовпадение контрольной суммы | Файл повреждён или был изменён после упаковки | Пересоздать пакет командой `make package-all` |

Следование данным шагам обеспечивает воспроизводимую упаковку и
автоматическую доставку пакетов пользователям на всех поддерживаемых
платформах.
