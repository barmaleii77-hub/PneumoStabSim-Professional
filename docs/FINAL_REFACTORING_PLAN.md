# 🎯 ФИНАЛЬНЫЙ ПЛАН ЗАВЕРШЕНИЯ РЕФАКТОРИНГА

> **Дата:** 2025-01-18
> **Версия:** PneumoStabSim Professional v4.9.5
> **Приоритет:** 🔴 КРИТИЧНО

---

## 🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ (ИСПРАВЛЕНЫ)

### ✅ **ЧТО УЖЕ ИСПРАВЛЕНО:**

1. ✅ Создан `config/app_settings.json` (единый источник настроек)
2. ✅ Реализован `src/common/settings_manager.py` (централизованный API)

### ❌ **ЧТО ОСТАЛОСЬ СДЕЛАТЬ:**

1. ❌ Мигрировать GraphicsPanel на SettingsManager
2. ❌ Удалить `defaults.py` (дефолты в коде)
3. ❌ Обновить все табы для работы с JSON
4. ❌ Завершить QML интеграцию (SharedMaterials, Lighting, Geometry)
5. ❌ Тестирование end-to-end

---

## 📋 ПОШАГОВЫЙ ПЛАН ДЕЙСТВИЙ

### **ЭТАП 1: МИГРАЦИЯ GRAPHICSPANEL НА SETTINGSMANAGER** (⏱️ 2 часа)

#### **Шаг 1.1: Обновить panel_graphics_refactored.py** (45 мин)

**Файл:** `src/ui/panels/graphics/panel_graphics_refactored.py`

**Изменения:**

```python
# ❌ СТАРОЕ (удалить)
from .defaults import build_defaults, GRAPHICS_DEFAULTS
self._defaults = build_defaults()
self.state: Dict[str, Any] = copy.deepcopy(self._defaults)

# ✅ НОВОЕ (добавить)
from src.common.settings_manager import get_settings_manager
self.settings_manager = get_settings_manager()
self.state: Dict[str, Any] = self.settings_manager.get_category("graphics")
```

**Методы для обновления:**

1. **`__init__()`:**
```python
def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)

    self.logger = logging.getLogger(__name__)

    # ✅ НОВОЕ: Используем SettingsManager
    self.settings_manager = get_settings_manager()
    self.state = self.settings_manager.get_category("graphics")

    # Логгеры
    self.graphics_logger = get_graphics_logger()
    self.event_logger = get_event_logger()

    self._create_ui()
    self._apply_state_to_ui()

    QTimer.singleShot(0, self._emit_all)
```

2. **`save_settings()`:**
```python
@Slot()
def save_settings(self) -> None:
    """Сохранить текущие настройки"""
    try:
        # ✅ НОВОЕ: Сохранение через SettingsManager
        self.settings_manager.set_category("graphics", self.state, auto_save=True)
        self.logger.info("Graphics settings saved")
    except Exception as e:
        self.logger.error(f"Failed to save settings: {e}")
```

3. **`load_settings()`:**
```python
@Slot()
def load_settings(self) -> None:
    """Загрузить настройки"""
    try:
        # ✅ НОВОЕ: Загрузка через SettingsManager
        self.state = self.settings_manager.get_category("graphics")
        self._apply_state_to_ui()
        self.logger.info("Graphics settings loaded")
    except Exception as e:
        self.logger.error(f"Failed to load settings: {e}")
```

4. **`reset_to_defaults()`:**
```python
@Slot()
def reset_to_defaults(self) -> None:
    """Сброс к дефолтам (из JSON!)"""
    self.logger.info("🔄 Resetting graphics settings to defaults (from JSON)")

    try:
        # ✅ НОВОЕ: Сброс через SettingsManager
        self.settings_manager.reset_to_defaults(category="graphics")
        self.state = self.settings_manager.get_category("graphics")

        self._apply_state_to_ui()
        self._emit_all()

        self.preset_applied.emit("Сброс к значениям из config/app_settings.json")
    except Exception as e:
        self.logger.error(f"Reset failed: {e}")
```

5. **Добавить новый метод `save_current_as_defaults()`:**
```python
@Slot()
def save_current_as_defaults(self) -> None:
    """
    Сохранить текущие настройки как новые дефолты
    (кнопка "Сохранить как дефолт" в UI)
    """
    try:
        self.settings_manager.save_current_as_defaults(category="graphics")
        self.logger.info("✅ Current graphics settings saved as new defaults")
        self.preset_applied.emit("Текущие настройки сохранены как новые дефолты")
    except Exception as e:
        self.logger.error(f"Save as defaults failed: {e}")
```

6. **Обновить кнопки в `_create_ui()`:**
```python
def _create_ui(self) -> None:
    # ...existing code...

    button_row = QHBoxLayout()

    # Кнопка "Сброс к дефолтам"
    reset_btn = QPushButton("↩︎ Сброс к дефолтам", self)
    reset_btn.setToolTip("Загрузить дефолты из config/app_settings.json")
    reset_btn.clicked.connect(self.reset_to_defaults)
    button_row.addWidget(reset_btn)

    # ✅ НОВАЯ кнопка "Сохранить как дефолт"
    save_default_btn = QPushButton("💾 Сохранить как дефолт", self)
    save_default_btn.setToolTip("Сохранить текущие настройки в defaults_snapshot")
    save_default_btn.clicked.connect(self.save_current_as_defaults)
    button_row.addWidget(save_default_btn)

    button_row.addStretch(1)
    main_layout.addLayout(button_row)
```

---

#### **Шаг 1.2: Удалить defaults.py** (5 мин)

**Действие:**
```bash
# После подтверждения что всё работает
rm src/ui/panels/graphics/defaults.py
```

**Обновить импорты** во всех файлах, которые использовали `defaults.py`:
- `panel_graphics_refactored.py` - ✅ уже обновлен
- `test_graphics_panel_integration.py` - нужно обновить

---

#### **Шаг 1.3: Наполнить app_settings.json ПОЛНЫМИ настройками** (30 мин)

**Файл:** `config/app_settings.json`

**Добавить:**
- Все 244 параметра из `defaults.py`
- Структурировать по категориям
- Добавить metadata

**Скрипт для миграции:**

```python
# migrate_defaults_to_json.py
import json
from pathlib import Path
from src.ui.panels.graphics.defaults import build_defaults, build_quality_presets

def migrate():
    """Мигрировать defaults.py → app_settings.json"""

    # Загружаем существующий файл
    settings_file = Path("config/app_settings.json")
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    # Получаем все дефолты из defaults.py
    graphics_defaults = build_defaults()
    quality_presets = build_quality_presets()

    # Обновляем текущие настройки
    settings["current"]["graphics"] = graphics_defaults
    settings["current"]["quality_presets"] = quality_presets

    # Сохраняем как дефолты
    settings["defaults_snapshot"]["graphics"] = graphics_defaults
    settings["defaults_snapshot"]["quality_presets"] = quality_presets

    # Метаданные
    settings["metadata"]["migrated_from_defaults_py"] = True
    settings["metadata"]["migration_date"] = "2025-01-18"

    # Сохраняем
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"✅ Migrated {len(graphics_defaults)} parameters to {settings_file}")

if __name__ == "__main__":
    migrate()
```

**Запуск:**
```bash
python migrate_defaults_to_json.py
```

---

#### **Шаг 1.4: Обновить tests** (20 мин)

**Файл:** `src/ui/panels/graphics/test_graphics_panel_integration.py`

**Изменения:**

```python
# ❌ СТАРОЕ
from .defaults import GRAPHICS_DEFAULTS

# ✅ НОВОЕ
from src.common.settings_manager import get_settings_manager

def test_defaults_from_json():
    """Тест: дефолты загружаются из JSON, не из кода"""
    manager = get_settings_manager()

    # Проверяем что defaults_snapshot существует
    defaults = manager.get_all_defaults()
    assert "graphics" in defaults

    # Проверяем ключевые параметры
    assert defaults["graphics"]["effects"]["bloom_intensity"] == 0.5
    assert defaults["graphics"]["lighting"]["key"]["brightness"] == 1.2

    print("✅ Defaults loaded from JSON successfully")
```

---

### **ЭТАП 2: ЗАВЕРШЕНИЕ QML ИНТЕГРАЦИИ** (⏱️ 2 часа)

#### **Шаг 2.1: Интегрировать SharedMaterials** (30 мин)

**Файл:** `assets/qml/main.qml`

**Действия:**
1. Найти строку `Node { id: worldRoot }`
2. После неё добавить:

```qml
// ✅ SHARED MATERIALS
import "scene"

SharedMaterials {
    id: sharedMaterials

    // Frame
    frameBaseColor: root.frameBaseColor
    frameMetalness: root.frameMetalness
    frameRoughness: root.frameRoughness
    // ... все параметры

    // Lever, Tail, Cylinder, Piston*, Joint*
    // ... все материалы
}
```

3. Удалить старые inline `PrincipledMaterial` (frameMaterial, leverMaterial и т.д.)

4. Заменить `materials: [frameMaterial]` → `materials: [sharedMaterials.frameMaterial]`

---

#### **Шаг 2.2: Интегрировать DirectionalLights + PointLights** (20 мин)

**Файл:** `assets/qml/main.qml`

**Действия:**
1. Найти 3 блока `DirectionalLight { id: keyLight ... }`
2. Заменить на:

```qml
import "lighting"

DirectionalLights {
    worldRoot: worldRoot
    cameraRig: cameraController.rig
    // ...all parameters
}

PointLights {
    worldRoot: worldRoot
    // ...parameters
}
```

---

#### **Шаг 2.3: Интегрировать Frame** (15 мин)

**Файл:** `assets/qml/main.qml`

**Заменить 3 Model на:**

```qml
import "geometry"

Frame {
    worldRoot: worldRoot
    beamSize: root.userBeamSize
    frameHeight: root.userFrameHeight
    frameLength: root.userFrameLength
    frameMaterial: sharedMaterials.frameMaterial
}
```

---

#### **Шаг 2.4: Интегрировать SuspensionCorner** (45 мин)

**Файл:** `assets/qml/main.qml`

**Заменить component + 4 инстанса на:**

```qml
import "geometry"

SuspensionCorner {
    id: flCorner
    parent: worldRoot
    // ...parameters FL
}

SuspensionCorner {
    id: frCorner
    // ...FR
}

SuspensionCorner {
    id: rlCorner
    // ...RL
}

SuspensionCorner {
    id: rrCorner
    // ...RR
}
```

---

#### **Шаг 2.5: Тестирование QML** (10 мин)

```bash
py app.py
```

**Ожидаемый вывод:**
```
💡 DirectionalLights initialized
💡 PointLights initialized
🏗️ Frame initialized
🔧 SuspensionCorner initialized (x4)
```

---

### **ЭТАП 3: ТЕСТИРОВАНИЕ И ВАЛИДАЦИЯ** (⏱️ 1 час)

#### **Шаг 3.1: Unit тесты** (20 мин)

```bash
pytest tests/test_settings_manager.py -v
pytest src/ui/panels/graphics/test_graphics_panel_integration.py -v
```

#### **Шаг 3.2: Integration тест** (20 мин)

1. Запустить приложение
2. Изменить 10+ параметров в GraphicsPanel
3. Закрыть приложение
4. Открыть `config/app_settings.json` - проверить изменения
5. Запустить снова - настройки должны загрузиться

#### **Шаг 3.3: Тест кнопок** (20 мин)

1. **Кнопка "Сброс к дефолтам":**
   - Изменить параметры
   - Нажать "Сброс"
   - Проверить что загрузились значения из `defaults_snapshot`

2. **Кнопка "Сохранить как дефолт":**
   - Изменить параметры
   - Нажать "Сохранить как дефолт"
   - Открыть JSON - проверить что `defaults_snapshot` обновлён

---

### **ЭТАП 4: ФИНАЛИЗАЦИЯ И ДОКУМЕНТАЦИЯ** (⏱️ 30 мин)

#### **Шаг 4.1: Обновить документацию** (15 мин)

**Создать:** `docs/SETTINGS_ARCHITECTURE.md`

```markdown
# Settings Architecture

## Единая система настроек

### Файлы:
- `config/app_settings.json` - ЕДИНСТВЕННЫЙ источник настроек
- `src/common/settings_manager.py` - API для работы с настройками

### Структура JSON:
```json
{
  "current": { ... текущие настройки ... },
  "defaults_snapshot": { ... сохраненные дефолты ... },
  "metadata": { "version", "last_modified" }
}
```

### Принципы:
1. ❌ Никаких дефолтов в коде
2. ✅ Все настройки в JSON
3. ✅ Сквозная прослеживаемость
4. ✅ Дефолты = snapshot (обновляются по кнопке)
```

#### **Шаг 4.2: Git коммит** (15 мин)

```bash
git add .
git commit -m "feat: Unified settings system + QML integration complete

CRITICAL CHANGES:
1. Settings System Refactoring
   - Created config/app_settings.json (single source of truth)
   - Implemented SettingsManager (no defaults in code!)
   - Removed src/ui/panels/graphics/defaults.py
   - All settings now in JSON (current + defaults_snapshot)

2. QML Integration (100% complete)
   - Integrated SharedMaterials, DirectionalLights, PointLights
   - Integrated Frame, SuspensionCorner components
   - Removed 1050+ lines of inline QML code

3. GraphicsPanel Enhancements
   - Migrated to SettingsManager
   - Added 'Save as Default' button
   - Autosave on every change
   - Reset loads from defaults_snapshot

RESULT:
✅ No defaults in code
✅ Single settings file
✅ Traceable parameters
✅ QML integration: 100%
✅ All tests passing

Files changed:
- config/app_settings.json (NEW - unified settings)
- src/common/settings_manager.py (NEW - settings API)
- src/ui/panels/graphics/panel_graphics_refactored.py (migrated)
- src/ui/panels/graphics/defaults.py (REMOVED)
- assets/qml/main.qml (-1050 lines, modular imports)
"
```

---

## 🎯 КОНТРОЛЬНЫЕ ТОЧКИ

| # | Checkpoint | Статус | ETA |
|---|-----------|--------|-----|
| **1** | SettingsManager реализован | ✅ ГОТОВО | +0h |
| **2** | GraphicsPanel мигрирован | ❌ TODO | +2h |
| **3** | defaults.py удалён | ❌ TODO | +2h |
| **4** | QML интеграция завершена | ❌ TODO | +4h |
| **5** | Тестирование пройдено | ❌ TODO | +5h |
| **6** | Документация готова | ❌ TODO | +5.5h |

**Общее время:** ~5.5 часов (1 рабочий день)

---

## ✅ КРИТЕРИИ ГОТОВНОСТИ (DEFINITION OF DONE)

### **Settings System:**
- [ ] `config/app_settings.json` содержит ВСЕ 244+ параметра
- [ ] `SettingsManager` работает (load/save/reset/save_as_default)
- [ ] `defaults.py` удалён
- [ ] Никаких дефолтов в коде
- [ ] Кнопки "Сброс" и "Сохранить как дефолт" работают

### **QML Integration:**
- [ ] SharedMaterials интегрирован
- [ ] DirectionalLights + PointLights интегрированы
- [ ] Frame интегрирован
- [ ] SuspensionCorner (x4) интегрированы
- [ ] `py app.py` запускается без ошибок
- [ ] Консоль показывает инициализацию модулей

### **Testing:**
- [ ] Unit тесты SettingsManager pass
- [ ] Integration тесты GraphicsPanel pass
- [ ] Smoke тест приложения pass
- [ ] Кнопки UI работают корректно

### **Documentation:**
- [ ] `docs/SETTINGS_ARCHITECTURE.md` создан
- [ ] `docs/FINAL_REFACTORING_COMPLETION.md` создан
- [ ] README обновлён
- [ ] Git коммит создан

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ (IMMEDIATE ACTIONS)

1. **СЕЙЧАС:** Запустить `migrate_defaults_to_json.py` для миграции
2. **ЗАТЕМ:** Обновить `panel_graphics_refactored.py` (Шаг 1.1)
3. **ПАРАЛЛЕЛЬНО:** Начать QML интеграцию (Этап 2)

**Готов начать с миграции дефолтов?**
