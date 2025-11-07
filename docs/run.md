# Запуск и окружение

## Зависимости

- Python 3.11–3.13 (рекомендуется 3.13.x)
- PySide6 6.5–6.10 (основной профиль 6.10.x)
- numpy 1.24.4 / 1.26.4 / 2.0.1 (в зависимости от профиля)

Установить зависимости: `pip install -r requirements.txt -c requirements-compatible.txt`

## Переменные окружения Qt

`app.py` вызывает `src/bootstrap/environment.configure_qt_environment`, поэтому
следующие значения задаются автоматически (если отсутствуют в `.env`). Эти же
значения прописаны в `env.sample`, чтобы ручной запуск и автоконфигурация были
идентичными:

- `QSG_RHI_BACKEND=opengl` — единый RHI backend для Windows, Linux и macOS.
- `QT_QUICK_CONTROLS_STYLE=Fusion` — согласованный стиль контролов во всех ОС.
- `QSG_OPENGL_VERSION=3.3` и `QT_OPENGL=desktop` — минимальные требования для OpenGL.
- `QSG_INFO=0`, `QT_LOGGING_RULES=*.debug=false;*.info=false` — ограничение шумных логов.
- `QT_AUTO_SCREEN_SCALE_FACTOR=1`, `QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough`,
  `QT_ENABLE_HIGHDPI_SCALING=1`, `QT_ASSUME_STDERR_HAS_CONSOLE=1` — стабильное
  масштабирование и вывод в консоль.
- `PSS_DIAG=1` — включает диагностический канал симулятора.

### Windows vs Linux

- **Windows / macOS**: используются нативные Qt-плагины (`windows`, `cocoa`).
  Платформа не переопределяется, а OpenGL по умолчанию работает через
  `QT_OPENGL=desktop` (ANGLE включается вручную при необходимости).
- **Linux (desktop)**: значения выше работают без изменений при наличии `DISPLAY`.
- **Linux (CI/headless)**: при отсутствии `DISPLAY` автоматически
  активируется `QT_QPA_PLATFORM=offscreen` и `QT_QUICK_BACKEND=software`, так что
  в `.env` их можно оставлять пустыми.

### Переключение режимов

- Vulkan-тесты: установите `QSG_RHI_BACKEND=vulkan` и добавьте `VK_ICD_FILENAMES`
  для вашего драйвера (например, Lavapipe).
- Безопасный режим: вызовите `configure_qt_environment(safe_mode=True)` или
  удалите `QSG_RHI_BACKEND` из окружения — Qt выберет backend автоматически.
- Возврат к "настольному" запуску из headless профиля: очистите значения
  `QT_QPA_PLATFORM` и `QT_QUICK_BACKEND` (оставьте пустыми в `.env`).

## Linux headless / Windows fallback

| Профиль | Переменные | Назначение |
|---------|------------|------------|
| Linux headless | `QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software`, `LIBGL_ALWAYS_SOFTWARE=1` | Работает в контейнерах и CI без `DISPLAY`, задействует софтварный рендерер Mesa. |
| Vulkan (headless) | `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json` <br>*(путь может отличаться, см. ниже)* | Принудительное использование Lavapipe или другого ICD для тестов Vulkan. |
| Windows fallback | `QT_QPA_PLATFORM=windows`, `QT_OPENGL=angle`, (опционально) `LIBGL_ALWAYS_SOFTWARE=0` | Заставляет Qt переключиться на ANGLE/Direct3D, полезно при отсутствии нативного OpenGL. |

> **Внимание:** Путь к ICD-файлу Lavapipe (`lvp_icd.x86_64.json`) может отличаться в зависимости от дистрибутива Linux.  
> - **Debian/Ubuntu:** обычно `/usr/share/vulkan/icd.d/lvp_icd.json`  
> - **Arch Linux:** может быть `/usr/share/vulkan/icd.d/lvp_icd.x86_64.json`  
> - **Fedora:** часто `/usr/share/vulkan/icd.d/lvp_icd.x86_64.json`  
> Проверьте наличие файла командой:  
> ```bash
> ls /usr/share/vulkan/icd.d/
> ```
> и укажите актуальный путь для вашей системы в переменной `VK_ICD_FILENAMES`.
### Сценарии Safe / Legacy

- **Safe (software-only):** вызовите `configure_qt_environment(safe_mode=True)` и
  дополнительно зафиксируйте `LIBGL_ALWAYS_SOFTWARE=1`. Qt отключит принудительный
  `QSG_RHI_BACKEND`, перейдёт на софтварный OpenGL и гарантированно загрузит сцену
  даже без GPU.
- **Legacy (ANGLE/Direct3D):** на Windows сохраните стандартное значение
  `QSG_RHI_BACKEND=opengl`, но добавьте `QT_OPENGL=angle`. Qt Quick Scene Graph
  задействует ANGLE для совместимости со старыми драйверами; при возврате к
  современным драйверам удалите переменную или установите `QT_OPENGL=desktop`.

## Режимы запуска

- Обычный: `python app.py`
- Тестовый: `python app.py --test-mode` (окно закрывается через 5 секунд)

## FAQ: типовые ошибки

### OpenGL недоступен ("Failed to create OpenGL context")

- Убедитесь, что драйвер доступен: на Linux задайте `LIBGL_ALWAYS_SOFTWARE=1`
  для Mesa или установите проприетарные драйверы и уберите переменную.
- В headless среде активируйте профиль из раздела «Linux headless / Windows
  fallback» и проверьте, что `QT_QPA_PLATFORM` соответствует окружению.
- На Windows переключитесь на ANGLE (`QT_OPENGL=angle`) или установите
  актуальные драйверы GPU.

### Отсутствуют шейдеры или QML-компоненты

- Проверьте, что выполнен `configure_qt_environment()` — он добавляет пути к
  `assets/qml` и встроенным модулям Qt Quick 3D.
- При ручном запуске из IDE убедитесь, что рабочая директория — корень проекта,
  иначе Qt не найдёт `assets/qml/components`.
- Если используются кастомные шейдеры, проверьте наличие `assets/qml/scene`
  и прав доступа; при повреждённых артефактах переустановите пакет из архива
  `assets/`.
