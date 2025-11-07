# Запуск и окружение

Зависимости
- Python3.11–3.13 (рекомендуется3.13.x)
- PySide66.5–6.10 (основной профиль6.10.x)
- numpy1.24.4 /1.26.4 /2.0.1 (в зависимости от профиля)

Установка
- `pip install -r requirements.txt -c requirements-compatible.txt`

Переменные окружения Qt (автоматически настраиваются в `app.py`)
- `QML2_IMPORT_PATH`, `QML_IMPORT_PATH`, `QT_PLUGIN_PATH`, `QT_QML_IMPORT_PATH`

Режимы запуска
- Обычный `python app.py`
- Тестовый `python app.py --test-mode` (окно закроется через5 сек)

Графический backend
- Все платформы: OpenGL RHI (`QSG_RHI_BACKEND=opengl`, требуется OpenGL 3.3+)

## Linux headless / Windows fallback

### Переменные окружения
- `QT_QPA_PLATFORM` — задаёт платформенный плагин Qt. В headless-сценариях используем `offscreen`, на Windows-фоллбеке оставляем `windows`.
- `LIBGL_ALWAYS_SOFTWARE` — форсирует программный OpenGL (llvmpipe/softpipe), полезно для CI и удалённых агентов. Значение `1` включает режим, `0` — возвращает системный драйвер.
- `VK_ICD_FILENAMES` — явный путь к Vulkan ICD. Для безопасного режима указываем Mesa (`/usr/share/vulkan/icd.d/lvp_icd.x86_64.json`), для Windows-совместимости оставляем пустым, чтобы Qt выбрал ANGLE/D3D.

### Сценарии запуска
- **Safe (CI, headless Linux):** `QT_QPA_PLATFORM=offscreen LIBGL_ALWAYS_SOFTWARE=1 VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json python app.py`. Обеспечивает детерминированный программный рендеринг без зависимости от GPU.
- **Legacy (Windows/устаревшие драйверы):** запуск `python app.py` с предустановленным `QT_QPA_PLATFORM=windows` и пустым `VK_ICD_FILENAMES`. Qt автоматически переключится на ANGLE/Direct3D 11, даже если OpenGL недоступен.

## FAQ: типовые ошибки
- **OpenGL недоступен / `QOpenGLContext::create` failed.** Проверьте наличие драйвера. Для обхода проблемы запустите приложение в Safe-сценарии с программным OpenGL (`LIBGL_ALWAYS_SOFTWARE=1`) или на Windows оставьте Qt в режиме ANGLE.
- **Шейдеры не найдены (`ShaderEffectSource: source is not set`).** Убедитесь, что каталог `assets/qml/` находится в `QML2_IMPORT_PATH` и приложение стартует из корня проекта. Дополнительно выполните `python tools/setup_qt.py`, чтобы обновить кэш QML и перекомпилировать шейдеры.
