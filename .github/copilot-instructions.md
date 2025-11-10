---
applicable_to: "**/*"
version: "1.2"
last_updated: "2026-06-07"
---

# GitHub Copilot Instructions for PneumoStabSim Professional

## Overview

PneumoStabSim Professional is a professional pneumatic suspension simulator built with Python 3.13, PySide6 6.10, and Qt Quick 3D. This document provides comprehensive guidance for GitHub Copilot coding agent to work effectively with this codebase.

## Quick Reference

### Essential Commands
```bash
# Quality checks
make check                    # Run all checks (lint, typecheck, qml-lint, test)
make autonomous-check         # Full autonomous quality check
make verify                   # Extended verification including smoke tests

# Individual checks
make lint                     # Run Python linters (ruff)
make typecheck               # Run mypy type checking
make qml-lint                # Run QML linters
make test                    # Run pytest suite

# Utilities
make sanitize                # Clean temporary files
make cipilot-env             # Prepare environment for Copilot
python app.py                # Launch the application
```

> 🔗 Полный перечень Qt-переменных и headless/Vulkan сценариев теперь поддерживается
> в [`docs/ENVIRONMENT_SETUP.md`](../docs/ENVIRONMENT_SETUP.md). Используйте его как
> единую точку правды и не дублируйте значения в новых инструкциях.

### Build and Test Workflow
1. **Before starting work**: Run `make autonomous-check` or `make sanitize && make check`
2. **During development**: Run specific checks (`make lint`, `make test`)
3. **Before committing**: Run `make verify` (full validation)
4. **Environment issues**: Run `python app.py --env-check` for diagnostics

## Project Configuration

### Language & Localization
- **Primary Language**: Russian (Русский)
- **Code Comments**: Russian with English technical terms
- **Documentation**: Russian
- **Variable Names**: English (snake_case for Python, camelCase for QML)

### Technology Stack

#### Python Environment
- **Python Version**: 3.13.x
- **Coding Style**: PEP 8 compliant
- **Type Hints**: Required for all functions
- **Async**: asyncio when needed
- **Dependencies Management**: `uv` (`dependency-groups`: dev/docs/release) + экспорт в `requirements*.txt`

#### Qt Framework
- **Qt Version**: 6.10.x
- **Qt Binding**: PySide6 6.10+
- **QML Engine**: Qt Quick 3D (QtQuick3D 6.10)
- **Graphics Backend**: Direct3D 11 (Windows), OpenGL (Linux/macOS)
- **High DPI**: Enabled with PassThrough scaling

#### Key Qt Features Used
- **Qt Quick 3D**: For 3D visualization
- **ExtendedSceneEnvironment**: Advanced rendering features
- **Fog Object**: Qt 6.10+ API
- **Dithering**: Qt 6.10+ feature
- **PrincipledMaterial**: PBR materials
- **IBL (Image-Based Lighting)**: HDR environment maps
- **SLERP Interpolation**: Automatic angle handling

### Project Structure

```
PneumoStabSim-Professional/
├── app.py                          # Main entry point
├── src/
│   ├── common/                     # Common utilities
│   ├── core/                       # Core geometry & physics
│   │   ├── geometry.py            # 2D geometry primitives
│   │   └── kinematics.py          # Suspension kinematics
│   ├── simulation/                 # Physics simulation
│   │   ├── pneumatic_cylinder.py  # Pneumatic model
│   │   └── manager.py             # Simulation coordinator
│   └── ui/
│       ├── main_window.py         # Main window (Qt/QML bridge)
│       ├── panels/                # Control panels
│       │   ├── panel_geometry.py  # Geometry controls
│       │   ├── panel_graphics.py  # Graphics controls
│       │   └── panel_animation.py # Animation controls
│       └── custom_geometry.py     # Custom 3D geometries
├── assets/
│   ├── qml/
│   │   ├── main.qml               # Main 3D scene (v4.9.8)
│   │   └── components/
│   │       └── IblProbeLoader.qml # IBL loader component
│   └── hdr/                       # HDR environment maps
└── tests/                         # Unit, integration и manual-сценарии (см. tests/README.md)
```

### Автономная проверка и трассировка
- **Обязательный запуск**: перед любой разработкой запускай `make autonomous-check`.
  - Используй параметры `--sanitize --launch-trace` для полной подготовки: `python -m tools.autonomous_check --sanitize --launch-trace`.
  - Скрипт автоматически очищает временные артефакты, выполняет линтеры, mypy, pytest и qmllint, а также сохраняет краткий отчёт в консоль и лог-файлы в `reports/quality/`.
- **Быстрый повтор**: для отдельных стадий можно выполнять `python -m tools.autonomous_check --task lint` или `--task test` с дополнительными аргументами.
- **Трассировка запуска**: `python -m tools.trace_launch` создаёт OpenGL/Qt отчёт в `reports/quality/launch_traces/` и выводит краткую сводку по результатам.
- **Контроль чистоты**: `python -m tools.project_sanitize --verbose` удаляет `__pycache__`, `*.pyc`, временные файлы решений и старые отчёты, чтобы репозиторий оставался чистым.
- **Pre-commit**: перед пушем выполняй `pre-commit run ruff-format-check-all --all-files` — хук запускает `ruff format` и `ruff check` подряд и предотвращает форматные регрессии.

### Visual Studio (Insiders) и F5
> ⚠️ Visual Studio Insiders и F5-профили больше не поддерживаются. Используй VS Code или `make uv-run` для запуска приложения и тестов.

### Агент GitHub Copilot VS
- Перед запуском Copilot GPT обязательно подготовь Qt окружение:
  - Выполни `make cipilot-env` (генерирует `.env.cipilot` и отчёт `reports/quality/cipilot_environment.json`).
  - Подгрузи переменные окружения командой `source ./.env.cipilot` (PowerShell: `Get-Content .env.cipilot | ForEach-Object { $_ -replace '^export ', 'set ' }`).
- При каждом открытии решения агент обязан:
  1. Запустить `python -m tools.project_sanitize --report-history 5`.
  2. Проверить готовность окружения командой `python -m tools.autonomous_check --task verify --launch-trace` и проанализировать
свежие логи в `reports/quality/`.
  3. Применить найденные предупреждения, сформировав TODO в исходниках или в `docs/RENOVATION_MASTER_PLAN.md`.
- Перед генерацией кода агент сверяется с данным документом и файлами `docs/RENOVATION_PHASE_*.md`.
- Все рекомендации по настройке графики, физики и тестов должны оформляться в `reports/` (подпапки `quality/`, `performance/`).
- Если приложение завершилось аварийно, агент обязан повторно вызвать `python -m tools.trace_launch --history-limit 10` и прилож
ить краткий вывод к отчёту.
### Coding Standards

#### Python Code Style
```python
# Type hints обязательны
def calculate_position(angle: float, length: float) -> tuple[float, float]:
    """
    Вычисляет позицию точки по углу и длине.

    Args:
        angle: Угол в градусах
        length: Длина в миллиметрах

    Returns:
        Кортеж (x, y) координат в мм
    """
    rad = math.radians(angle)
    return length * math.cos(rad), length * math.sin(rad)

# Docstrings на русском языке
# Комментарии на русском с английскими терминами
```

#### QML Code Style
```qml
// Свойства группируются логически
property real userBeamSize: 120        // мм - размер балки
property real userFrameHeight: 650     // мм - высота рамы

// Комментарии на русском
// ✅ ПРАВИЛЬНО: используем прямое присваивание
property real angle: 0

// ❌ НЕПРАВИЛЬНО: не нормализуем углы вручную
// Qt сам знает как интерполировать через SLERP
```

### Critical Design Patterns

#### 1. **НИКОГДА не нормализуй углы вручную в QML**
```qml
// ❌ НЕПРАВИЛЬНО - вызывает flip на 180°
onAngleChanged: {
    angle = angle % 360
}

// ✅ ПРАВИЛЬНО - Qt использует SLERP
property real angle: 0  // Qt сам обрабатывает любые значения
```

#### 2. **Python ↔ QML Bridge**
```python
# Используем QMetaObject.invokeMethod для вызова QML функций
QMetaObject.invokeMethod(
    self._qml_root_object,
    "applyGeometryUpdates",
    Qt.ConnectionType.DirectConnection,
    Q_ARG("QVariant", geometry_params)
)
```

#### 3. **Batch Updates для производительности**
```python
# Группируй обновления в батчи
updates = {
    "geometry": {...},
    "lighting": {...},
    "materials": {...}
}
self._qml_root_object.applyBatchedUpdates(updates)
```

#### 4. **QML State Management**
```qml
// ✅ ПРАВИЛЬНО: Используй Component.onCompleted для инициализации
Component.onCompleted: {
    if (typeof startLightingState !== "undefined") {
        applyLightingUpdates(startLightingState)
    }
}

// ❌ НЕПРАВИЛЬНО: Прямой доступ к undefined свойствам
property var intensity: startLightIntensity // может быть undefined
```

#### 5. **Settings Persistence Strategy**
- **SettingsManager**: Централизованное хранилище (config/app_settings.json)
- **НЕ ИСПОЛЬЗОВАТЬ**: QSettings для Python-side конфигураций
- **Panel State**: Собирается через `collect_state()` методы
- **Save Strategy**: Батч-сохранение при closeEvent() основного окна

```python
# ✅ ПРАВИЛЬНО: Централизованное сохранение в MainWindow.closeEvent()
def closeEvent(self, event):
    # 1) Собираем состояние всех панелей
    if self.graphics_panel:
        state = self.graphics_panel.collect_state()
        self.settings_manager.set_category("graphics", state, auto_save=False)

    # 2) Пишем на диск ОДИН РАЗ
    self.settings_manager.save()
```

#### 6. **Critical IBL/HDR Path Handling**
```python
# ✅ ПРАВИЛЬНО: Нормализация путей относительно QML директории
def _normalize_hdr_path(candidate: Any, qml_dir: Path) -> str:
    """Преобразует любой путь к HDR в POSIX формат относительно qml_dir"""
    if not candidate:
        return ""

    path_obj = Path(str(candidate).replace("\\", "/"))
    resolved = path_obj.resolve(strict=False)

    # Относительный путь предпочтительнее
    if not path_obj.is_absolute():
        return path_obj.as_posix()

    try:
        return resolved.relative_to(qml_dir).as_posix()
    except ValueError:
        return resolved.as_posix()

# ❌ НЕПРАВИЛЬНО: Смешанные разделители или абсолютные пути
ibl_source = "C:\\Users\\...\\assets\\hdr\\file.hdr"  # Windows path
ibl_source = "../hdr/file.hdr"  # Может не работать из QML
```

### Performance Optimizations

1. **Кэширование вычислений**:
   ```qml
   QtObject {
       id: animationCache
       property real basePhase: animationTime * userFrequency * 2 * Math.PI
       property real flSin: Math.sin(basePhase + flPhaseRad)
   }
   ```

2. **Ленивая загрузка модулей** в Python

3. **Батч обновления** вместо множественных вызовов

4. **Shared материалы** вместо дублирования

### Testing Requirements

- **Unit Tests**: pytest для Python кода
- **Integration Tests**: QML + Python взаимодействие
- **Visual Tests**: Проверка 3D рендеринга
- **Performance Tests**: FPS, memory usage
- `pytest.ini` уже активирует `pytestqt.plugin`, поэтому фикстура `qtbot` доступна без ручных импортов или изменения `PYTEST_DISABLE_PLUGIN_AUTOLOAD`.

### Documentation Style

```python
"""
Модуль управления пневматическими цилиндрами.

Этот модуль реализует физическую модель пневматического цилиндра
с учетом сжимаемости воздуха, трения и динамики.

Classes:
    PneumaticCylinder: Модель одиночного цилиндра
    CylinderManager: Управление множественными цилиндрами

Example:
    >>> cylinder = PneumaticCylinder(bore=80, rod_diameter=35)
    >>> cylinder.update(dt=0.016, force=1000)
    >>> position = cylinder.get_position()
"""
```

### Git Commit Message Format

```
CATEGORY: Brief description in Russian

Detailed description in Russian with technical terms in English.

CHANGES:
1. Added/Fixed/Removed feature X
2. Updated component Y

RESULT:
✅ Expected behavior
✅ Test coverage

Files changed:
- path/to/file.py
- path/to/file.qml
```

### Error Handling

```python
# Всегда логируй ошибки на русском
try:
    result = calculate_kinematics(angle)
except ValueError as e:
    logger.error(f"Ошибка расчета кинематики: {e}")
    raise
except Exception as e:
    logger.critical(f"Критическая ошибка: {e}")
    # Graceful degradation
    return default_value
```

### Dependencies

**Core Requirements**:
- PySide6 >= 6.10.0
- numpy >= 1.24.0
- scipy >= 1.10.0

**Development Requirements**:
- pytest >= 7.0.0
- black (code formatting)
- mypy (type checking)
- pylint (linting)

### IDE Configuration

**VS Code Settings** (recommended):
```json
{
    "python.defaultInterpreterPath": "python3.13",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.encoding": "utf8"
}
```

---

## Copilot Behavior Instructions

When generating code for this project:

1. **Always use Russian** for:
   - Comments explaining logic
   - Docstrings
   - Error messages
   - User-facing strings

2. **Always use English** for:
   - Variable names
   - Function names
   - Technical terms
   - Git commits titles

3. **Follow Qt 6.10 best practices**:
   - Use ExtendedSceneEnvironment features
   - Leverage SLERP for angle interpolation
   - Never normalize angles manually
   - Use PrincipledMaterial for PBR

4. **Python 3.13 features**:
   - Use type hints with `|` syntax: `str | None`
   - Use `match/case` when appropriate
   - Leverage improved error messages

5. **Performance-first**:
   - Cache calculations
   - Batch updates
   - Lazy loading
   - Avoid redundant operations

6. **Testing mindset**:
   - Every function needs tests
   - Edge cases matter
   - Visual testing for 3D

---

## Architecture Overview

### System Layers
```
┌─────────────────────────────────────┐
│   UI Layer (Qt/QML)                 │
│   - MainWindow (Python)             │
│   - Control Panels (Python)         │
│   - 3D Scene (QML)                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Business Logic (Python)           │
│   - Kinematics                      │
│   - Physics Simulation              │
│   - Settings Management             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Data Layer                        │
│   - JSON Configuration              │
│   - State Persistence               │
│   - Event Logging                   │
└─────────────────────────────────────┘
```

### Key Components
- **MainWindow**: Central Qt/QML bridge, manages panels and 3D scene
- **Panels**: Geometry, Graphics, Animation control panels
- **SettingsManager**: Centralized configuration (config/app_settings.json)
- **PneumaticCylinder**: Physics model for suspension simulation
- **Kinematics**: Geometric calculations for suspension movement
- **Custom Geometries**: 3D models for visualization

### Data Flow
1. User interacts with control panels (Qt widgets)
2. Panels emit signals with parameter changes
3. MainWindow collects updates and batches them
4. Updates sent to QML via `QMetaObject.invokeMethod`
5. QML 3D scene updates geometry and materials
6. Settings persisted via SettingsManager on close

## Contributing Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Checklist
- [ ] Create feature branch from `develop`
- [ ] Run `make autonomous-check` before starting
- [ ] Write tests for new functionality
- [ ] Run `make verify` before committing
- [ ] Follow commit conventions (Conventional Commits)
- [ ] Update documentation if needed
- [ ] Create PR targeting `develop`

### Branch Strategy
- `main`: Production releases only
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

## Troubleshooting

### Common Issues

#### 1. Qt Plugin/QML Import Errors
```bash
# Verify environment
python app.py --env-check

# Setup paths
source activate_environment.sh  # Linux/macOS
.\activate_environment.ps1      # Windows
```

#### 2. Black Screen or Rendering Issues
- Check Qt version: `python -c "from PySide6 import QtCore; print(QtCore.qVersion())"`
- Must be >= 6.10.0 for ExtendedSceneEnvironment features
- Verify HDR files exist in `assets/hdr/`
- Check QML console for errors

#### 3. Test Failures
```bash
# Run specific test
pytest tests/smoke/test_import.py -v

# Debug mode
pytest tests/ -vv --log-cli-level=DEBUG

# Skip slow tests
pytest -m "not slow"
```

#### 4. Type Checking Errors
```bash
# Run mypy on specific file
mypy src/ui/main_window.py

# Update type stubs
pip install --upgrade types-PySide6
```

#### 5. Build/Lint Failures
```bash
# Auto-fix formatting
make format

# Clean and retry
make sanitize
make check
```

### Getting Help
- Check `docs/RENOVATION_MASTER_PLAN.md` for architecture decisions
- Review `reports/quality/` for recent quality reports
- See phase documents in `docs/RENOVATION_PHASE_*.md`
- Consult `DEVELOPER_GUIDE.md` for development workflows

## Task Assignment Guidelines

### Ideal Tasks for Copilot Agent
- ✅ Bug fixes with clear reproduction steps
- ✅ Adding tests for existing functionality
- ✅ Code refactoring with defined scope
- ✅ Documentation updates
- ✅ Configuration changes
- ✅ Performance optimizations with benchmarks
- ✅ Accessibility improvements

### Tasks Requiring Human Oversight
- ⚠️ Architecture changes affecting multiple components
- ⚠️ Security-sensitive modifications
- ⚠️ Qt/QML rendering pipeline changes
- ⚠️ Physics simulation algorithm changes
- ⚠️ Breaking API changes
- ⚠️ Database schema migrations

### Out of Scope
- ❌ Business logic without domain expert input
- ❌ Major UI/UX redesigns
- ❌ Performance-critical real-time code without profiling
- ❌ Changes to CI/CD pipelines without testing

## Security Considerations

### Sensitive Files
- **Never commit**: API keys, credentials, production configs
- **Use environment variables**: For sensitive configuration
- **Validate inputs**: All user-provided data, especially file paths
- **Sanitize paths**: Use `Path.resolve()` and validate with `.is_relative_to()` to prevent directory traversal attacks

### Code Review Checklist
- [ ] No hardcoded credentials or secrets
- [ ] Input validation for all external data
- [ ] Proper error handling (no exposed stack traces)
- [ ] Safe file operations (check paths, permissions)
- [ ] Qt object lifecycle managed correctly
- [ ] Dependencies reviewed for vulnerabilities

---

**Last Updated**: 2026-06-07
**Project Version**: v4.9.8
**Copilot Instructions Version**: 1.2
**Maintainer**: barmaleii77-hub
