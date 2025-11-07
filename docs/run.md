# Запуск и окружение

## Зависимости

- Python 3.11–3.13 (рекомендуется 3.13.x)
- PySide6 6.5–6.10 (основной профиль 6.10.x)
- numpy 1.24.4 / 1.26.4 / 2.0.1 (в зависимости от профиля)

Установить зависимости: `pip install -r requirements.txt -c requirements-compatible.txt`

## Переменные окружения Qt

`app.py` вызывает `src/bootstrap/environment.configure_qt_environment`, поэтому
следующие значения задаются автоматически (если отсутствуют в `.env`):

- `QSG_RHI_BACKEND=opengl` — единый RHI backend для Windows, Linux и macOS.
- `QT_QUICK_CONTROLS_STYLE=Fusion` — согласованный стиль контролов во всех ОС.
- `QSG_OPENGL_VERSION=3.3` и `QT_OPENGL=desktop` — минимальные требования для OpenGL.
- `QSG_INFO=0`, `QT_LOGGING_RULES=*.debug=false;*.info=false` — ограничение шумных логов.
- `QT_AUTO_SCREEN_SCALE_FACTOR=1`, `QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough`,
  `QT_ENABLE_HIGHDPI_SCALING=1`, `QT_ASSUME_STDERR_HAS_CONSOLE=1` — стабильное
  масштабирование и вывод в консоль.
- `PSS_DIAG=1` — включает диагностический канал симулятора.

### Windows vs Linux

- **Windows / macOS**: используются нативные Qt-плагины (`windows`, `cocoa`),
  поэтому дополнительные переменные платформы не задаются.
- **Linux (desktop)**: значения выше работают без изменений при наличии `DISPLAY`.
- **Linux (CI/headless)**: при отсутствии `DISPLAY` автоматически
  активируется `QT_QPA_PLATFORM=offscreen` и `QT_QUICK_BACKEND=software`.

### Переключение режимов

- Vulkan-тесты: установите `QSG_RHI_BACKEND=vulkan` и добавьте `VK_ICD_FILENAMES`
  для вашего драйвера (например, Lavapipe).
- Безопасный режим: вызовите `configure_qt_environment(safe_mode=True)` или
  удалите `QSG_RHI_BACKEND` из окружения — Qt выберет backend автоматически.
- Возврат к "настольному" запуску из headless профиля: очистите значения
  `QT_QPA_PLATFORM` и `QT_QUICK_BACKEND` (оставьте пустыми в `.env`).

## Режимы запуска

- Обычный: `python app.py`
- Тестовый: `python app.py --test-mode` (окно закрывается через 5 секунд)
