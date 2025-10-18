# Qt 6.10 PrincipledMaterial - ПОЛНЫЙ СПИСОК СВОЙСТВ

**Дата:** 2025-01-18  
**Версия:** Qt 6.10.0  
**Источник:** Qt Quick 3D Documentation

---

## 📋 ДОСТУПНЫЕ СВОЙСТВА PrincipledMaterial (Qt 6.10)

### **1. ОСНОВНЫЕ ЦВЕТА**

| Свойство | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `baseColor` | color | Базовый цвет материала | `#ffffff` |
| `emissiveFactor` | vector3d | Множитель эмиссии (излучение) | `Qt.vector3d(0,0,0)` |
| `emissiveMap` | Texture | Карта эмиссии | `null` |

### **2. МЕТАЛЛИЧНОСТЬ И ШЕРОХОВАТОСТЬ**

| Свойство | Тип | Описание | Диапазон | По умолчанию |
|----------|-----|----------|----------|--------------|
| `metalness` | real | Металличность (0=диэлектрик, 1=металл) | `0.0 - 1.0` | `0.0` |
| `roughness` | real | Шероховатость (0=гладкий, 1=шероховатый) | `0.0 - 1.0` | `0.0` |
| `metalnessMap` | Texture | Карта металличности | - | `null` |
| `roughnessMap` | Texture | Карта шероховатости | - | `null` |
| `metalnessChannel` | enumeration | Канал карты металличности | R, G, B, A | `Material.B` |
| `roughnessChannel` | enumeration | Канал карты шероховатости | R, G, B, A | `Material.G` |

### **3. ПРОЗРАЧНОСТЬ**

| Свойство | Тип | Описание | Диапазон | По умолчанию |
|----------|-----|----------|----------|--------------|
| `opacity` | real | Непрозрачность | `0.0 - 1.0` | `1.0` |
| `opacityMap` | Texture | Карта прозрачности | - | `null` |
| `opacityChannel` | enumeration | Канал карты прозрачности | R, G, B, A | `Material.A` |
| `alphaMode` | enumeration | Режим альфа-смешивания | Opaque, Mask, Blend | `Material.Default` |
| `alphaCutoff` | real | Порог для режима Mask | `0.0 - 1.0` | `0.5` |

### **4. НОРМАЛИ И БАМПЫ**

| Свойство | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `normalMap` | Texture | Карта нормалей | `null` |
| `normalStrength` | real | Сила эффекта карты нормалей | `1.0` |
| `bumpMap` | Texture | Карта высот (bump mapping) | `null` |
| `bumpAmount` | real | Сила эффекта bump mapping | `0.0` |

### **5. AMBIENT OCCLUSION (AO)**

| Свойство | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `occlusionMap` | Texture | Карта ambient occlusion | `null` |
| `occlusionAmount` | real | Сила эффекта AO | `1.0` |
| `occlusionChannel` | enumeration | Канал карты AO | R, G, B, A | `Material.R` |

### **6. ОТРАЖЕНИЯ И SPECULAR**

| Свойство | Тип | Описание | Диапазон | По умолчанию |
|----------|-----|----------|----------|--------------|
| `specularAmount` | real | Множитель specular отражений | `0.0 - 1.0` | `0.5` |
| `specularMap` | Texture | Карта specular | - | `null` |
| `specularReflectionMap` | Texture | Карта отражений | - | `null` |
| `specularTint` | color | Оттенок specular отражений | - | `#ffffff` |

### **7. LIGHTING MODEL**

| Свойство | Тип | Описание | Значения |
|----------|-----|----------|----------|
| `lighting` | enumeration | Модель освещения | `NoLighting`, `FragmentLighting` |

### **8. CULLING**

| Свойство | Тип | Описание | Значения |
|----------|-----|----------|----------|
| `cullMode` | enumeration | Режим отсечения граней | `BackFaceCulling`, `FrontFaceCulling`, `NoCulling` |

### **9. ТЕКСТУРНЫЕ КООРДИНАТЫ**

| Свойство | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `baseColorMap` | Texture | Карта базового цвета | `null` |
| `heightMap` | Texture | Карта высот (parallax) | `null` |
| `heightAmount` | real | Сила эффекта parallax | `0.0` |

### **10. INDEX OF REFRACTION (IOR)** ❌ НЕ ПОДДЕРЖИВАЕТСЯ

**ВАЖНО:** Свойства `ior` и `transmission` **НЕ СУЩЕСТВУЮТ** в базовом `PrincipledMaterial` Qt 6.10!

Для стекла используйте:
```qml
PrincipledMaterial {
    baseColor: "#e1f5ff"
    opacity: 0.3
    alphaMode: PrincipledMaterial.Blend
    metalness: 0.0
    roughness: 0.1
    specularAmount: 1.0
}
```

---

## 🎨 РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ ПО ТИПАМ МАТЕРИАЛОВ

### **1. МЕТАЛЛ (рама, рычаги)**
```qml
PrincipledMaterial {
    baseColor: "#c53030"
    metalness: 0.85
    roughness: 0.35
    specularAmount: 0.8
    // Опционально:
    normalMap: Texture { source: "metal_normal.png" }
    occlusionMap: Texture { source: "metal_ao.png" }
}
```

### **2. ПОЛИРОВАННЫЙ МЕТАЛЛ (поршневой шток)**
```qml
PrincipledMaterial {
    baseColor: "#ececec"
    metalness: 1.0
    roughness: 0.18
    specularAmount: 1.0
}
```

### **3. ПРОЗРАЧНЫЙ ПЛАСТИК (цилиндр)**
```qml
PrincipledMaterial {
    baseColor: "#e1f5ff"
    opacity: 0.3
    alphaMode: PrincipledMaterial.Blend
    metalness: 0.0
    roughness: 0.2
    specularAmount: 0.6
}
```

### **4. ЦВЕТНОЙ МЕТАЛЛ (шарниры)**
```qml
PrincipledMaterial {
    baseColor: "#2a82ff"  // Синий
    metalness: 0.9
    roughness: 0.35
    specularAmount: 0.7
}
```

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ МАТЕРИАЛОВ В ПРОЕКТЕ

### **ЧТО ИСПОЛЬЗУЕТСЯ СЕЙЧАС:**

```qml
// leverMat
baseColor: ✅
metalness: ✅
roughness: ✅

// cylinderMat
baseColor: ✅
opacity: ✅
alphaMode: ✅

// pistonBodyMat
baseColor: ✅
metalness: ✅
roughness: ✅
```

### **ЧТО МОЖНО ДОБАВИТЬ:**

| Материал | Доп. свойства | Улучшение |
|----------|---------------|-----------|
| **leverMat** | `specularAmount: 0.8` | Более яркие блики на металле |
| **leverMat** | `normalMap` | Текстура поверхности |
| **cylinderMat** | `specularAmount: 0.6` | Блики на прозрачном пластике |
| **cylinderMat** | `roughness: 0.2` | Полуматовая поверхность |
| **pistonBodyMat** | `specularAmount: 0.9` | Яркие блики на окрашенном металле |
| **jointTailMat** | `specularAmount: 0.7` | Блики на цветных шарнирах |
| **frameMat** | `occlusionMap` | Затенение в углах рамы |

---

## 🚀 ПЛАН РАСШИРЕНИЯ МАТЕРИАЛОВ

### **ШАГ 1: Добавить specularAmount ко всем металлам**
```qml
PrincipledMaterial {
    id: leverMat
    baseColor: root.leverBaseColor
    metalness: root.leverMetalness
    roughness: root.leverRoughness
    specularAmount: root.leverSpecular  // НОВОЕ
}
```

### **ШАГ 2: Добавить roughness к прозрачным материалам**
```qml
PrincipledMaterial {
    id: cylinderMat
    baseColor: root.cylinderBaseColor
    opacity: root.cylinderOpacity
    alphaMode: PrincipledMaterial.Blend
    roughness: root.cylinderRoughness  // НОВОЕ
    specularAmount: root.cylinderSpecular  // НОВОЕ
}
```

### **ШАГ 3: Добавить normalMap для текстурирования**
```qml
PrincipledMaterial {
    id: frameMat
    baseColor: root.frameBaseColor
    metalness: root.frameMetalness
    roughness: root.frameRoughness
    normalMap: Texture {  // НОВОЕ
        source: root.frameNormalMapEnabled ? root.frameNormalMapPath : ""
    }
    normalStrength: root.frameNormalStrength  // НОВОЕ
}
```

### **ШАГ 4: Добавить emissive для светящихся элементов**
```qml
PrincipledMaterial {
    id: jointRodMat
    baseColor: "#00ff55"
    metalness: 0.9
    roughness: 0.3
    emissiveFactor: Qt.vector3d(  // НОВОЕ - подсветка
        root.jointRodEmissive * 0.0,
        root.jointRodEmissive * 1.0,
        root.jointRodEmissive * 0.3
    )
}
```

---

## 📋 СПИСОК НОВЫХ СВОЙСТВ ДЛЯ UI

### **GraphicsPanel → Materials Tab:**

**Для каждого материала добавить:**

1. **Specular Amount** (слайдер 0.0 - 1.0)
   - `leverSpecular`, `frameSpecular`, `pistonBodySpecular`, и т.д.

2. **Normal Map** (checkbox + file picker)
   - `frameNormalMapEnabled`, `frameNormalMapPath`
   - `leverNormalMapEnabled`, `leverNormalMapPath`

3. **Normal Strength** (слайдер 0.0 - 2.0)
   - `frameNormalStrength`, `leverNormalStrength`

4. **Occlusion Map** (checkbox + file picker)
   - `frameOcclusionMapEnabled`, `frameOcclusionMapPath`

5. **Emissive Factor** (RGB слайдеры 0.0 - 1.0)
   - `jointRodEmissiveR`, `jointRodEmissiveG`, `jointRodEmissiveB`

6. **Alpha Mode** (комбобокс для прозрачных материалов)
   - Opaque, Mask, Blend

7. **Alpha Cutoff** (слайдер 0.0 - 1.0, для режима Mask)

---

## 🎯 ИТОГОВЫЕ СВОЙСТВА МАТЕРИАЛОВ (ПОЛНЫЙ СПИСОК)

### **Frame Material:**
- baseColor ✅
- metalness ✅
- roughness ✅
- specularAmount ⏳ ДОБАВИТЬ
- normalMap ⏳ ДОБАВИТЬ
- normalStrength ⏳ ДОБАВИТЬ
- occlusionMap ⏳ ДОБАВИТЬ

### **Lever Material:**
- baseColor ✅
- metalness ✅
- roughness ✅
- specularAmount ⏳ ДОБАВИТЬ
- normalMap ⏳ ДОБАВИТЬ

### **Cylinder Material:**
- baseColor ✅
- opacity ✅
- alphaMode ✅
- roughness ⏳ ДОБАВИТЬ
- specularAmount ⏳ ДОБАВИТЬ

### **Piston Body Material:**
- baseColor ✅
- metalness ✅
- roughness ✅
- specularAmount ⏳ ДОБАВИТЬ
- emissiveFactor ⏳ ДОБАВИТЬ (для "горячего" поршня)

### **Joint Materials (Tail, Arm, Rod):**
- baseColor ✅
- metalness ✅
- roughness ✅
- specularAmount ⏳ ДОБАВИТЬ
- emissiveFactor ⏳ ДОБАВИТЬ (для подсветки)

---

## 💡 СЛЕДУЮЩИЕ ШАГИ

1. **Добавить свойства в `main.qml`** (root properties)
2. **Обновить материалы** (добавить новые свойства)
3. **Создать UI в Materials Tab** (слайдеры, checkboxes)
4. **Обновить `defaults.py`** (значения по умолчанию)
5. **Добавить в `app_settings.json`** (сохранение настроек)

---

**Готовы начать?** 🚀
