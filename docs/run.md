# Запуск и окружение

Зависимости
- Python 3.13+
- PySide6 >= 6.10.0
- numpy >= 1.24.0

Установка
- `pip install -r requirements.txt`

Переменные окружения Qt (автоматически настраиваются в `app.py`)
- `QML2_IMPORT_PATH`, `QML_IMPORT_PATH`, `QT_PLUGIN_PATH`, `QT_QML_IMPORT_PATH`

Режимы запуска
- Обычный `python app.py`
- Тестовый `python app.py --test-mode` (окно закроется через 5 сек)

Графический backend
- Windows: Direct3D 11 (`QSG_RHI_BACKEND=d3d11`)
- Linux/macOS: OpenGL
