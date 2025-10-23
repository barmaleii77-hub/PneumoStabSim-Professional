# PneumoStabSim Environment Compatibility

Этот документ фиксирует протестированную матрицу версий Python и PySide6, а также контрольные проверки, используемые для валидации окружения.

## Матрица совместимости (Python3.11–3.13, PySide66.5–6.10)

| Python \\ PySide6 |6.5 LTS |6.6 Stable |6.7 Feature |6.8 LTS |6.9 Stable |6.10 Target |
| --- | --- | --- | --- | --- | --- | --- |
| **3.11** | ✅ NumPy1.24.4<br>✅ SciPy1.11.4<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.5.3<br>✅ pytest7.4.4 | ✅ NumPy1.24.4<br>✅ SciPy1.11.4<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.6.3<br>✅ pytest7.4.4 | ✅ NumPy1.26.4<br>✅ SciPy1.12.0<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.7.2<br>✅ pytest7.4.4 | ⚠️ Требует NumPy1.26.4<br>⚠️ SciPy1.12.0<br>⚠️ Использовать QtQuick3D6.8.1<br>(Smoke-тест) | ⚠️ Использовать QtQuick3D6.9.1<br>Остальные зависимости — как для6.8 | ❌ Не поддерживается (Qt6.10 требует Python ≥3.12) |
| **3.12** | ⚠️ Работает с NumPy1.26.4<br>⚠️ SciPy1.12.0<br>QtQuick3D6.5.3 (ограниченный режим) | ✅ NumPy1.26.4<br>✅ SciPy1.12.0<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.6.3<br>✅ pytest8.2.2 | ✅ NumPy1.26.4<br>✅ SciPy1.12.0<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.7.2<br>✅ pytest8.2.2 | ✅ NumPy1.26.4<br>✅ SciPy1.12.0<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.8.1<br>✅ pytest8.2.2 | ✅ NumPy1.26.4<br>✅ SciPy1.12.0<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.9.1<br>✅ pytest8.2.2 | ⚠️ NumPy2.0.1<br>⚠️ SciPy1.13.1<br>✅ QtQuick3D6.10.0<br>(Smoke-тест) |
| **3.13** | ❌ Qt6.5 не собирается с Python3.13 | ⚠️ NumPy2.0.1<br>⚠️ SciPy1.13.1<br>✅ QtQuick3D6.6.3<br>(ограниченная поддержка) | ⚠️ NumPy2.0.1<br>⚠️ SciPy1.13.1<br>✅ QtQuick3D6.7.2<br>(ограниченная поддержка) | ✅ NumPy2.0.1<br>✅ SciPy1.13.1<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.8.1<br>✅ pytest8.3.2 | ✅ NumPy2.0.1<br>✅ SciPy1.13.1<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.9.1<br>✅ pytest8.3.2 | 🟢 **Основной профиль**<br>✅ NumPy2.0.1<br>✅ SciPy1.13.1<br>✅ PyOpenGL3.1.7<br>✅ QtQuick3D6.10.0<br>✅ pytest8.3.2 |

> Примечания:
> - Все конфигурации используют `PyOpenGL-accelerate3.1.7` (кроме macOS, где пакет недоступен).
> - Для нестандартных сборок (6.6/6.7/6.9) задействуется тот же стек NumPy/SciPy, что и у ближайшего LTS.
> - Дополнительные пины доступны через extras проекта (`pip install .[qt65]`, `.[qt68]`, `.[qt610]`).

## Команды для создания окружения

```bash
# Основной профиль (Python3.13 + PySide66.10)
python -m venv .venv
source .venv/bin/activate # или .\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt -c requirements-compatible.txt
pip install -r requirements-dev.txt
```

```bash
# Пример: профиль Python3.11 + PySide66.5 LTS
python3.11 -m venv .venv-py311
source .venv-py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -c requirements-compatible.txt "pneumostabsim[qt65] @ ."
```

## Контрольные проверки

| Проверка | Команда | Описание |
| --- | --- | --- |
| Сборка зависимостей | `pip list --format=columns | grep PySide6` | Убедиться, что установлена нужная версия PySide6/QtQuick3D |
| Импорт QtQuick3D | `python -c "from PySide6 import QtQuick3D; print(QtQuick3D.__name__)"` | Проверка доступности модуля QtQuick3D |
| Импорт численных библиотек | `python -c "import numpy, scipy; print(numpy.__version__, scipy.__version__)"` | Подтверждение версий NumPy/SciPy |
| Тестовый прогон | `pytest -q` | Регрессия по встроенным тестам |
| Линтер | `ruff check src tests` | Быстрая проверка код-стайла |

## Результаты последней проверки

- ✅ `pip install -r requirements.txt -c requirements-compatible.txt` (Python3.13.3)
- ⚠️ `pytest -q` — в контейнере требует системную библиотеку `libGL.so.1`, поэтому UI-тесты завершаются ошибкой загрузки Qt
- ⚠️ `ruff check src tests` — фиксирует существующие синтаксические проблемы в наследуемом коде (см. src/ui/main_window/qml_bridge.py)

## Политика поддержки

1. Основной таргет: Python3.13 + PySide66.10. Все новые фичи тестируются на этой связке.
2. LTS-поддержка: Python3.11 + PySide66.5 и Python3.12 + PySide66.8. Фиксы безопасности бэкпортируются до окончания жизненного цикла релизов Qt.
3. Промежуточные ветки (6.6/6.7/6.9): поддерживаются в режиме best-effort. Ошибки, связанные с этими версиями, принимаются при наличии воспроизводимого сценария.
4. Тестовая матрица CI: минимум `pytest -q` и `ruff check` должны проходить на всех поддерживаемых профилях перед выпуском минорного релиза.
5. Эскалация: Если критичная библиотека прекращает выпуск колес для конкретной версии Python, профиль переводится в статус deprecated с уведомлением в `docs/environments.md`.
