# ExtendedSceneEnvironment - Правильное использование

**Дата:** Декабрь 2024  
**Версия проекта:** PneumoStabSim Professional v4.9  
**Статус:** ✅ КОРРЕКТНАЯ КОНФИГУРАЦИЯ

---

## 🎯 Краткое резюме

**PneumoStabSim использует ВСТРОЕННЫЙ `ExtendedSceneEnvironment` из `QtQuick3D.Helpers`**

- ✅ **НЕТ** кастомного компонента ExtendedSceneEnvironment
- ✅ **НЕТ** конфликтов имен
- ✅ **ВСЕ** визуальные эффекты работают корректно
- ✅ **Правильный импорт**: `import QtQuick3D.Helpers`

---

## 📋 Правильная конфигурация

### 1. Импорт модулей (main.qml)

```qml
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers  // ✅ Правильно - для ExtendedSceneEnvironment
import "components"
```

**❌ НЕ ИСПОЛЬЗУЙТЕ:**
```qml
import QtQuick3D.Effects  // Устарел с Qt 6.5
```

---

### 2. Использование ExtendedSceneEnvironment

```qml
View3D {
    id: view3d
    anchors.fill: parent
    camera: camera

    environment: ExtendedSceneEnvironment {
        id: mainEnvironment
        
        // Фон и IBL
        backgroundMode: root.backgroundMode === "skybox" && root.iblReady ? 
                       SceneEnvironment.SkyBox : SceneEnvironment.Color
        clearColor: root.backgroundColor
        lightProbe: root.iblEnabled && root.iblReady ? iblLoader.probe : null
        probeExposure: root.iblIntensity
        probeHorizon: 0.08
        skyBoxBlurAmount: root.skyboxBlur

        // Тонемаппинг
        tonemapMode: root.tonemapEnabled ?
            (root.tonemapModeName === "filmic" ? SceneEnvironment.TonemapModeFilmic :
             root.tonemapModeName === "aces" ? SceneEnvironment.TonemapModeAces :
             root.tonemapModeName === "reinhard" ? SceneEnvironment.TonemapModeReinhard :
             root.tonemapModeName === "gamma" ? SceneEnvironment.TonemapModeGamma :
             SceneEnvironment.TonemapModeLinear) : SceneEnvironment.TonemapModeNone
        exposure: 1.0
        whitePoint: 2.0

        // Антиалиасинг
        antialiasingMode: root.aaPrimaryMode === "msaa" ? SceneEnvironment.MSAA :
                         root.aaPrimaryMode === "ssaa" ? SceneEnvironment.SSAA :
                         SceneEnvironment.NoAA
        antialiasingQuality: root.aaQualityLevel === "high" ? SceneEnvironment.High :
                           root.aaQualityLevel === "medium" ? SceneEnvironment.Medium :
                           SceneEnvironment.Low
        fxaaEnabled: root.aaPostMode === "fxaa" && root.fxaaEnabled
        temporalAAEnabled: (root.aaPostMode === "taa" && root.taaEnabled)
        temporalAAStrength: root.taaStrength
        specularAAEnabled: root.specularAAEnabled

        // SSAO (Ambient Occlusion)
        aoEnabled: root.aoEnabled
        aoStrength: root.aoStrength
        aoDistance: Math.max(1.0, root.aoRadius)
        aoSoftness: 20
        aoDither: true
        aoSampleRate: 3

        // Bloom/Glow
        glowEnabled: root.bloomEnabled
        glowIntensity: root.bloomIntensity
        glowBloom: root.bloomSpread
        glowStrength: 0.9
        glowQualityHigh: true
        glowUseBicubicUpscale: true
        glowHDRMinimumValue: root.bloomThreshold
        glowHDRMaximumValue: 6.0
        glowHDRScale: 1.5

        // Lens Flare
        lensFlareEnabled: root.lensFlareEnabled
        lensFlareGhostCount: 3
        lensFlareGhostDispersal: 0.6
        lensFlareHaloWidth: 0.25
        lensFlareBloomBias: 0.35
        lensFlareStretchToAspect: 1.0

        // Depth of Field
        depthOfFieldEnabled: root.depthOfFieldEnabled
        depthOfFieldFocusDistance: root.dofFocusDistance
        depthOfFieldBlurAmount: root.dofBlurAmount

        // Vignette
        vignetteEnabled: root.vignetteEnabled
        vignetteRadius: 0.4
        vignetteStrength: root.vignetteStrength

        // OIT (Order Independent Transparency)
        oitMethod: root.oitMode === "weighted" ? 
                  SceneEnvironment.OITWeightedBlended : 
                  SceneEnvironment.OITNone

        // Цветокоррекция
        colorAdjustmentsEnabled: true
        adjustmentBrightness: 1.0
        adjustmentContrast: 1.05
        adjustmentSaturation: 1.05
        
        // ✅ Условная поддержка Dithering (Qt 6.10+)
        Component.onCompleted: {
            if (root.canUseDithering) {
                console.log("✅ Qt 6.10+ - enabling dithering")
                mainEnvironment.ditheringEnabled = Qt.binding(function() { 
                    return root.ditheringEnabled 
                })
            } else {
                console.log("⚠️ Qt < 6.10 - dithering not available")
            }
        }
    }
}
```

---

## 🔧 Структура файлов

### Файлы QML компонентов

**`assets/qml/components/qmldir`:**
```qml
singleton Materials Materials.qml
IblProbeLoader IblProbeLoader.qml
```

**✅ ПРАВИЛЬНО:**
- НЕТ кастомного `ExtendedSceneEnvironment` в qmldir
- Используется только встроенный из QtQuick3D.Helpers

**❌ НЕПРАВИЛЬНО (старый подход):**
```qml
// НЕ ДЕЛАЙТЕ ТАК:
ExtendedSceneEnvironment ExtendedSceneEnvironment.qml  // Конфликт!
```

---

## 🎨 Доступные эффекты

### ExtendedSceneEnvironment поддерживает:

| Эффект | Свойство | Описание |
|--------|----------|----------|
| **Bloom/Glow** | `glowEnabled` | Свечение ярких областей |
| **SSAO** | `aoEnabled` | Объемное затенение |
| **Tonemap** | `tonemapMode` | Кинематографическая цветопередача |
| **Lens Flare** | `lensFlareEnabled` | Блики от источников света |
| **Vignette** | `vignetteEnabled` | Затемнение краев |
| **Depth of Field** | `depthOfFieldEnabled` | Размытие по глубине |
| **Fog** | Через Fog объект | Атмосферная дымка |
| **IBL** | `lightProbe` | HDR окружение |
| **Dithering** | `ditheringEnabled` | Устранение полос (Qt 6.10+) |
| **TAA** | `temporalAAEnabled` | Temporal антиалиасинг |
| **FXAA** | `fxaaEnabled` | Быстрый антиалиасинг |

---

## ⚙️ Qt версии и поддержка

### Qt 6.9.3 (текущая версия)

✅ **Поддерживаемые функции:**
- ExtendedSceneEnvironment (полностью)
- Bloom, SSAO, Vignette, Lens Flare
- Tonemap (Filmic, ACES, Reinhard, Gamma, Linear)
- Depth of Field
- TAA, FXAA, MSAA, SSAA
- IBL с HDR текстурами
- Fog (через Fog объект)

⚠️ **Ограниченные функции:**
- `ditheringEnabled` - доступно только в Qt 6.10+

### Qt 6.10+ (будущие версии)

✅ **Дополнительно:**
- Полная поддержка `ditheringEnabled`
- Улучшенное качество dithering для градиентов

---

## 🚀 Лучшие практики

### 1. Проверка версии Qt

```qml
readonly property var qtVersionParts: Qt.version.split('.')
readonly property int qtMajor: parseInt(qtVersionParts[0])
readonly property int qtMinor: parseInt(qtVersionParts[1])
readonly property bool supportsQtQuick3D610Features: qtMajor === 6 && qtMinor >= 10
```

### 2. Условная активация функций

```qml
Component.onCompleted: {
    if (root.canUseDithering) {
        mainEnvironment.ditheringEnabled = Qt.binding(function() { 
            return root.ditheringEnabled 
        })
    }
}
```

### 3. Оптимизация производительности

```qml
// Адаптивный TAA - включается только при движении камеры
temporalAAEnabled: (root.aaPostMode === "taa" && 
                   root.taaEnabled && 
                   (!root.taaMotionAdaptive || !root.cameraIsMoving))
```

### 4. Правильные режимы тонемаппинга

```qml
tonemapMode: root.tonemapEnabled ?
    (root.tonemapModeName === "filmic" ? SceneEnvironment.TonemapModeFilmic :
     root.tonemapModeName === "aces" ? SceneEnvironment.TonemapModeAces :
     root.tonemapModeName === "reinhard" ? SceneEnvironment.TonemapModeReinhard :
     root.tonemapModeName === "gamma" ? SceneEnvironment.TonemapModeGamma :
     SceneEnvironment.TonemapModeLinear) : SceneEnvironment.TonemapModeNone
```

---

## 🔍 Диагностика проблем

### Проблема: ExtendedSceneEnvironment не найден

**Решение:**
1. Проверьте импорт: `import QtQuick3D.Helpers`
2. Убедитесь что PySide6 >= 6.5.0
3. Установите переменные окружения:
   ```python
   os.environ["QML2_IMPORT_PATH"] = str(qml_path)
   os.environ["QML_IMPORT_PATH"] = str(qml_path)
   ```

### Проблема: Конфликт имен

**Решение:**
1. Удалите кастомный ExtendedSceneEnvironment.qml (если есть)
2. Уберите из qmldir: `ExtendedSceneEnvironment ...`
3. Используйте только встроенный: `import QtQuick3D.Helpers`

### Проблема: ditheringEnabled не работает

**Решение:**
1. Проверьте версию Qt: `Qt.version`
2. Если Qt < 6.10, используйте условную активацию:
   ```qml
   Component.onCompleted: {
       if (root.canUseDithering) {
           mainEnvironment.ditheringEnabled = ...
       }
   }
   ```

---

## 📊 Проверка конфигурации

### Python код (app.py)

```python
from PySide6.QtCore import qVersion

qt_version = qVersion()
print(f"Qt version: {qt_version}")

major, minor = qt_version.split('.')[:2]
supports_dithering = int(major) == 6 and int(minor) >= 10

print(f"ExtendedSceneEnvironment: ✅ Built-in from QtQuick3D.Helpers")
print(f"Dithering support: {'✅ YES' if supports_dithering else '⚠️ NO (Qt 6.10+ required)'}")
```

### QML отладка

```qml
Component.onCompleted: {
    console.log("═══════════════════════════════════════════")
    console.log("ExtendedSceneEnvironment Configuration:")
    console.log("  Qt Version:", Qt.version)
    console.log("  Dithering Support:", root.canUseDithering)
    console.log("  IBL Enabled:", root.iblEnabled)
    console.log("  Bloom Enabled:", root.bloomEnabled)
    console.log("  SSAO Enabled:", root.aoEnabled)
    console.log("  Tonemap Mode:", root.tonemapModeName)
    console.log("═══════════════════════════════════════════")
}
```

---

## ✅ Заключение

### Текущий статус PneumoStabSim:

- ✅ **Правильная конфигурация**: Используется встроенный ExtendedSceneEnvironment
- ✅ **Нет конфликтов**: Кастомные компоненты удалены
- ✅ **Все эффекты работают**: Bloom, SSAO, Tonemap, Vignette, Lens Flare, DoF
- ✅ **Совместимость**: Qt 6.9.3 полностью поддержана
- ✅ **Готовность**: Qt 6.10+ features готовы к активации

### Рекомендации:

1. **Не создавайте кастомный ExtendedSceneEnvironment** - используйте встроенный
2. **Всегда импортируйте QtQuick3D.Helpers** для доступа к ExtendedSceneEnvironment
3. **Используйте условную активацию** для функций Qt 6.10+
4. **Проверяйте версию Qt** перед использованием новых функций
5. **Тестируйте на разных версиях Qt** для совместимости

---

**Документ создан:** Декабрь 2024  
**Версия:** 1.0  
**Статус:** ✅ Актуальный и протестированный
