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
- Windows: Direct3D11 (`QSG_RHI_BACKEND=d3d11`)
- Linux/macOS: OpenGL
