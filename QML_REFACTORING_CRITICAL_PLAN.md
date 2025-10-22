# 🚨 КРИТИЧЕСКИЙ ПЛАН: QML РЕФАКТОРИНГ MAIN.QML

**Дата:** 2025-01-05
**Проблема:** `main.qml` = **6200+ строк МОНОЛИТ**
**Решение:** Разбить на модули используя УЖЕ СОЗДАННУЮ структуру

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ ЧТО УЖЕ СОЗДАНО:

```
assets/qml/
├── core/           ✅ СОЗДАНЫ, но НЕ используются полностью!
│   ├── MathUtils.qml
│   ├── GeometryCalculations.qml
│   ├── StateCache.qml
│   └── qmldir
├── camera/         ✅ СОЗДАНЫ, НО main.qml использует частично!
│   ├── CameraState.qml
│   ├── CameraRig.qml
│   ├── MouseControls.qml
│   ├── CameraController.qml
│   └── qmldir
└── main.qml        ❌ 6200+ СТРОК МОНОЛИТ!!!
```

### ❌ ЧТО НЕ СОЗДАНО:

```
assets/qml/
├── lighting/       ❌ НЕТ! Освещение ВСЁ ЕЩЁ В МОНОЛИТЕ
├── materials/      ❌ НЕТ! Материалы ВСЁ ЕЩЁ В МОНОЛИТЕ
├── effects/        ❌ НЕТ! Эффекты ВСЁ ЕЩЁ В МОНОЛИТЕ
├── geometry/       ❌ НЕТ! Геометрия подвески ВСЁ ЕЩЁ В МОНОЛИТЕ
└── environment/    ❌ НЕТ! IBL/Fog/Environment ВСЁ ЕЩЁ В МОНОЛИТЕ
```

---

## 🎯 ПЛАН ДЕЙСТВИЙ (СРОЧНО!)

### ФАЗА 1: LIGHTING MODULE (1 час)

**Создать:** `assets/qml/lighting/`

```qml
// lighting/DirectionalLights.qml
import QtQuick
import QtQuick3D

Node {
    id: root

    // Properties
    property real keyLightBrightness: 1.2
    property color keyLightColor: "#ffffff"
    property real keyLightAngleX: -35
    property real keyLightAngleY: -40
    // ... все остальные свойства освещения

    // 3 DirectionalLight компонента
    DirectionalLight { id: keyLight; ... }
    DirectionalLight { id: fillLight; ... }
    DirectionalLight { id: rimLight; ... }
}

// lighting/PointLights.qml
import QtQuick
import QtQuick3D

Node {
    // PointLight компоненты
}

// lighting/qmldir
module lighting
DirectionalLights 1.0 DirectionalLights.qml
PointLights 1.0 PointLights.qml
```

**Вырезать из main.qml:** строки ~780-900 (DirectionalLight × 3 + PointLight)

---

### ФАЗА 2: MATERIALS MODULE (1 час)

**Создать:** `assets/qml/materials/`

```qml
// materials/FrameMaterial.qml
import QtQuick
import QtQuick3D

PrincipledMaterial {
    baseColor: parent.frameBaseColor
    metalness: parent.frameMetalness
    // ... все свойства
}

// materials/Materials.qml (уже есть singleton!)
pragma Singleton
import QtQuick

QtObject {
    // Все material properties централизованно
    property color frameBaseColor: "#c53030"
    property real frameMetalness: 0.85
    // ... остальные
}

// materials/qmldir
module materials
singleton Materials 1.0 Materials.qml
FrameMaterial 1.0 FrameMaterial.qml
LeverMaterial 1.0 LeverMaterial.qml
CylinderMaterial 1.0 CylinderMaterial.qml
// ... остальные материалы
```

**Вырезать из main.qml:** строки ~1050-1250 (PrincipledMaterial × 6)

---

### ФАЗА 3: GEOMETRY MODULE (1.5 часа)

**Создать:** `assets/qml/geometry/`

```qml
// geometry/SuspensionCorner.qml
import QtQuick
import QtQuick3D
import "../core"
import "../materials"

Node {
    id: root

    property vector3d j_arm
    property vector3d j_tail
    property real leverAngle
    property real pistonPositionFromPython: 250.0

    // ✅ Используем GeometryCalculations из core/
    readonly property vector3d j_rod: GeometryCalculations.calculateJRodPosition(...)

    // Model компоненты для lever, cylinder, piston, joints
}

// geometry/Frame.qml
import QtQuick
import QtQuick3D
import "../materials"

Node {
    // U-образная рама (3 балки)
}

// geometry/qmldir
module geometry
SuspensionCorner 1.0 SuspensionCorner.qml
Frame 1.0 Frame.qml
```

**Вырезать из main.qml:** строки ~1500-2200 (OptimizedSuspensionCorner + Frame)

---

### ФАЗА 4: EFFECTS MODULE (1 час)

**Создать:** `assets/qml/effects/`

```qml
// effects/ExtendedEnvironment.qml
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

ExtendedSceneEnvironment {
    // Все effects properties
    property bool bloomEnabled: true
    property real bloomIntensity: 0.5
    // ... все остальные эффекты

    // Bind свойства к ExtendedSceneEnvironment
    glowEnabled: bloomEnabled
    glowIntensity: bloomIntensity
    // ... и так далее
}

// effects/qmldir
module effects
ExtendedEnvironment 1.0 ExtendedEnvironment.qml
```

**Вырезать из main.qml:** строки ~880-1000 (ExtendedSceneEnvironment configuration)

---

### ФАЗА 5: ENVIRONMENT MODULE (1 час)

**Создать:** `assets/qml/environment/`

```qml
// environment/IBL.qml
import QtQuick
import QtQuick3D
import "../components"  // IblProbeLoader

Node {
    id: root

    property url iblPrimarySource
    property url iblFallbackSource
    property bool iblEnabled
    property bool iblLightingEnabled
    property bool iblBackgroundEnabled
    property real iblRotationDeg
    property real iblIntensity

    IblProbeLoader {
        id: iblLoader
        primarySource: root.iblPrimarySource
        fallbackSource: root.iblFallbackSource
    }
}

// environment/Fog.qml
import QtQuick
import QtQuick3D

Fog {
    enabled: parent.fogEnabled
    color: parent.fogColor
    // ...
}

// environment/qmldir
module environment
IBL 1.0 IBL.qml
Fog 1.0 Fog.qml
```

**Вырезать из main.qml:** строки ~110-130 (IblProbeLoader) + ~950-970 (Fog)

---

## 📐 НОВАЯ СТРУКТУРА MAIN.QML (ПОСЛЕ РЕФАКТОРИНГА)

```qml
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import "core"
import "camera"
import "lighting"        // ✅ НОВЫЙ MODULE
import "materials"       // ✅ НОВЫЙ MODULE
import "geometry"        // ✅ НОВЫЙ MODULE
import "effects"         // ✅ НОВЫЙ MODULE
import "environment"     // ✅ НОВЫЙ MODULE

Item {
    id: root

    // ✅ ТОЛЬКО root properties (флаги, координаты)
    // ✅ StateCache для кэширования
    // ✅ Python integration functions (applyBatchedUpdates, etc.)

    View3D {
        id: view3d

        // ✅ ИСПОЛЬЗУЕМ МОДУЛИ:
        environment: ExtendedEnvironment {
            // ✅ Делегируем в effects/ExtendedEnvironment.qml
        }

        // ✅ Camera system
        CameraController { id: cameraController; ... }

        // ✅ Lighting system
        DirectionalLights { id: dirLights; ... }
        PointLights { id: pointLights; ... }

        // ✅ Environment system
        IBL { id: ibl; ... }

        // ✅ Geometry system
        Frame { id: frame; ... }

        SuspensionCorner { id: flCorner; ... }
        SuspensionCorner { id: frCorner; ... }
        SuspensionCorner { id: rlCorner; ... }
        SuspensionCorner { id: rrCorner; ... }
    }
}
```

**Результат:** `main.qml` = **~1500 строк** вместо 6200!

---

## 🔥 КРИТИЧЕСКИЕ ПРАВИЛА

### ✅ ПРАВИЛО #1: НЕ ТРОГАТЬ РАБОТАЮЩИЙ КОД

- Создавать **НОВЫЕ модули** рядом с main.qml
- Проверять каждый модуль **ОТДЕЛЬНО** через test_app.py
- Только после проверки **ВЫРЕЗАТЬ** из main.qml

### ✅ ПРАВИЛО #2: СОХРАНИТЬ ОБРАТНУЮ СОВМЕСТИМОСТЬ

- Все properties main.qml **ДОЛЖНЫ ОСТАТЬСЯ**
- Python integration functions **НЕ ТРОГАТЬ**
- Только **ДЕЛЕГИРОВАТЬ** в модули

### ✅ ПРАВИЛО #3: ТЕСТИРОВАТЬ КАЖДЫЙ ШАГ

```bash
# После создания каждого модуля:
python test_qml_module.py lighting
python test_qml_module.py materials
python test_qml_module.py geometry
# ... и так далее

# Финальный тест всего приложения:
python app.py
```

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ДО РЕФАКТОРИНГА:
- **main.qml:** 6200+ строк
- **Модули:** 2 (core, camera)
- **Читаемость:** ❌ МОНОЛИТ
- **Поддержка:** ❌ СЛОЖНО

### ПОСЛЕ РЕФАКТОРИНГА:
- **main.qml:** ~1500 строк
- **Модули:** 7 (core, camera, lighting, materials, geometry, effects, environment)
- **Читаемость:** ✅ МОДУЛЬНО
- **Поддержка:** ✅ ЛЕГКО

---

## 🚀 СЛЕДУЮЩИЙ ШАГ: НАЧАТЬ РЕФАКТОРИНГ!

**Приоритет:** **КРИТИЧЕСКИЙ**
**Срок:** **1 рабочий день** (5-6 часов чистой работы)

**Команда для начала:**
```bash
# 1. Создать структуру каталогов
mkdir assets/qml/lighting
mkdir assets/qml/materials
mkdir assets/qml/geometry
mkdir assets/qml/effects
mkdir assets/qml/environment

# 2. Создать qmldir файлы
touch assets/qml/lighting/qmldir
touch assets/qml/materials/qmldir
touch assets/qml/geometry/qmldir
touch assets/qml/effects/qmldir
touch assets/qml/environment/qmldir

# 3. Начать с lighting module (самый простой)
code assets/qml/lighting/DirectionalLights.qml
```

---

**СТАТУС:** 🚨 ТРЕБУЕТ НЕМЕДЛЕННОГО ВНИМАНИЯ
**АВТОР:** GitHub Copilot
**ДАТА:** 2025-01-05
