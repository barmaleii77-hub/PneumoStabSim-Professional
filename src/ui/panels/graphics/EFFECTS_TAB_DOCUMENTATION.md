# Effects Tab - Полная документация параметров

**Версия:** 1.0  
**Дата:** 2025-01-13  
**Qt версия:** 6.10+

---

## 📋 Обзор

Effects Tab содержит **ВСЕ доступные параметры** визуальных эффектов из Qt Quick 3D ExtendedSceneEnvironment:

### ✅ Реализованные группы:

1. **Bloom (Свечение)** - 9 параметров (4 базовых + 5 расширенных Qt 6.10)
2. **Tonemap (Тонемаппинг)** - 4 параметра (2 базовых + 2 расширенных Qt 6.10)
3. **Depth of Field (Глубина резкости)** - 3 параметра (без изменений)
4. **Misc Effects (Дополнительные)** - 12 параметров:
   - Motion Blur (2 параметра)
   - Lens Flare (6 параметров: 1 базовый + 5 расширенных Qt 6.10)
   - Vignette (3 параметра: 2 базовых + 1 расширенный Qt 6.10)
5. **Color Adjustments (Цветокоррекция)** - 3 параметра (новая группа Qt 6.10)

**ИТОГО: 31 параметр эффектов**

---

## 🎨 1. Bloom (Свечение)

### Базовые параметры (из монолита):

#### `bloom_enabled` (bool)
- **UI:** Checkbox "Включить Bloom"
- **QML Property:** `glowEnabled`
- **По умолчанию:** `True`
- **Описание:** Включает/выключает эффект свечения ярких участков

#### `bloom_intensity` (float)
- **UI:** Slider "Интенсивность (glowIntensity)"
- **Диапазон:** 0.0 - 2.0
- **Шаг:** 0.02
- **По умолчанию:** 0.5
- **QML Property:** `glowIntensity`
- **Описание:** Сила эффекта свечения

#### `bloom_threshold` (float)
- **UI:** Slider "Порог (glowHDRMinimumValue)"
- **Диапазон:** 0.0 - 4.0
- **Шаг:** 0.05
- **По умолчанию:** 1.0
- **QML Property:** `glowHDRMinimumValue`
- **Описание:** Минимальная яркость пикселя для начала свечения

#### `bloom_spread` (float)
- **UI:** Slider "Распространение (glowBloom)"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.65
- **QML Property:** `glowBloom`
- **Описание:** Степень распространения свечения (0=узкое, 1=широкое)

### Расширенные параметры Qt 6.10:

#### `bloom_glow_strength` (float) ✨ NEW
- **UI:** Slider "Сила свечения (glowStrength)"
- **Диапазон:** 0.0 - 2.0
- **Шаг:** 0.02
- **По умолчанию:** 0.8
- **QML Property:** `glowStrength`
- **Описание:** Общая сила эффекта (работает совместно с intensity)

#### `bloom_hdr_max` (float) ✨ NEW
- **UI:** Slider "HDR Maximum (glowHDRMaximumValue)"
- **Диапазон:** 0.0 - 10.0
- **Шаг:** 0.1
- **По умолчанию:** 2.0
- **QML Property:** `glowHDRMaximumValue`
- **Описание:** Максимальная яркость пикселя для ограничения bloom

#### `bloom_hdr_scale` (float) ✨ NEW
- **UI:** Slider "HDR Scale (glowHDRScale)"
- **Диапазон:** 1.0 - 5.0
- **Шаг:** 0.1
- **По умолчанию:** 2.0
- **QML Property:** `glowHDRScale`
- **Описание:** Масштаб HDR данных для bloom расчетов

#### `bloom_quality_high` (bool) ✨ NEW
- **UI:** Checkbox "Высокое качество (glowQualityHigh)"
- **По умолчанию:** `False`
- **QML Property:** `glowQualityHigh`
- **Описание:** Использовать более качественный (но медленный) blur

#### `bloom_bicubic_upscale` (bool) ✨ NEW
- **UI:** Checkbox "Бикубическое увеличение (glowUseBicubicUpscale)"
- **По умолчанию:** `False`
- **QML Property:** `glowUseBicubicUpscale`
- **Описание:** Использовать бикубическую интерполяцию при upscale (лучше качество)

---

## 🎬 2. Tonemap (Тонемаппинг)

### Базовые параметры (из монолита):

#### `tonemap_enabled` (bool)
- **UI:** Checkbox "Включить тонемаппинг"
- **По умолчанию:** `True`
- **QML Property:** `tonemapMode != SceneEnvironment.TonemapModeNone`
- **Описание:** Включает тонемаппинг для HDR → LDR конвертации

#### `tonemap_mode` (str)
- **UI:** ComboBox "Режим"
- **Варианты:**
  - `"filmic"` - Filmic (кинематографичный)
  - `"aces"` - ACES (Academy Color Encoding System)
  - `"reinhard"` - Reinhard
  - `"gamma"` - Gamma correction
  - `"linear"` - Linear (без тонемаппинга)
- **По умолчанию:** `"filmic"`
- **QML Property:** `tonemapMode`
- **Описание:** Алгоритм тонемаппинга

### Расширенные параметры Qt 6.10:

#### `tonemap_exposure` (float) ✨ NEW
- **UI:** Slider "Экспозиция (tonemapExposure)"
- **Диапазон:** 0.1 - 5.0
- **Шаг:** 0.05
- **По умолчанию:** 1.0
- **QML Property:** `exposure` (в ExtendedSceneEnvironment)
- **Описание:** Экспозиция сцены (яркость перед тонемаппингом)

#### `tonemap_white_point` (float) ✨ NEW
- **UI:** Slider "Белая точка (tonemapWhitePoint)"
- **Диапазон:** 0.5 - 5.0
- **Шаг:** 0.1
- **По умолчанию:** 2.0
- **QML Property:** `whitePoint` (в ExtendedSceneEnvironment)
- **Описание:** Точка белого цвета для тонемаппинга

---

## 📸 3. Depth of Field (Глубина резкости)

### Параметры (без изменений из монолита):

#### `depth_of_field` (bool)
- **UI:** Checkbox "Включить DoF"
- **По умолчанию:** `False`
- **QML Property:** `depthOfFieldEnabled`
- **Описание:** Включает эффект размытия вне фокуса

#### `dof_focus_distance` (float)
- **UI:** Slider "Фокусное расстояние"
- **Диапазон:** 200.0 - 20000.0 мм
- **Шаг:** 50.0
- **По умолчанию:** 2200.0
- **QML Property:** `depthOfFieldFocusDistance`
- **Описание:** Расстояние до плоскости фокуса

#### `dof_blur` (float)
- **UI:** Slider "Размытие"
- **Диапазон:** 0.0 - 10.0
- **Шаг:** 0.1
- **По умолчанию:** 4.0
- **QML Property:** `depthOfFieldBlurAmount`
- **Описание:** Сила размытия вне фокуса

---

## ✨ 4. Misc Effects (Дополнительные эффекты)

### 4.1 Motion Blur (Размытие движения)

#### `motion_blur` (bool)
- **UI:** Checkbox "Размытие движения"
- **По умолчанию:** `False`
- **QML Property:** НЕ ПОДДЕРЖИВАЕТСЯ в Qt 6.10 ExtendedSceneEnvironment
- **Примечание:** ⚠️ Требуется кастомный Effect shader

#### `motion_blur_amount` (float)
- **UI:** Slider "Сила размытия"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.02
- **По умолчанию:** 0.2
- **QML Property:** НЕ ПОДДЕРЖИВАЕТСЯ
- **Примечание:** ⚠️ Требуется кастомный Effect shader

### 4.2 Lens Flare (Линзовые блики)

#### Базовый параметр (из монолита):

##### `lens_flare` (bool)
- **UI:** Checkbox "Линзовые блики"
- **По умолчанию:** `False`
- **QML Property:** `lensFlareEnabled`
- **Описание:** Включает эффект бликов линз

#### Расширенные параметры Qt 6.10:

##### `lens_flare_ghost_count` (int) ✨ NEW
- **UI:** Slider "Количество призраков"
- **Диапазон:** 1 - 10
- **Шаг:** 1
- **По умолчанию:** 3
- **QML Property:** `lensFlareGhostCount`
- **Описание:** Количество повторяющихся бликов-призраков

##### `lens_flare_ghost_dispersal` (float) ✨ NEW
- **UI:** Slider "Распределение призраков"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.6
- **QML Property:** `lensFlareGhostDispersal`
- **Описание:** Расстояние между призраками

##### `lens_flare_halo_width` (float) ✨ NEW
- **UI:** Slider "Ширина гало"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.25
- **QML Property:** `lensFlareHaloWidth`
- **Описание:** Ширина кольца гало вокруг источника света

##### `lens_flare_bloom_bias` (float) ✨ NEW
- **UI:** Slider "Смещение bloom"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.0
- **QML Property:** `lensFlareBloomBias`
- **Описание:** Смещение bloom эффекта для бликов

##### `lens_flare_stretch_to_aspect` (bool) ✨ NEW
- **UI:** Checkbox "Растяжение по пропорциям"
- **По умолчанию:** `False`
- **QML Property:** `lensFlareStretchToAspect`
- **Описание:** Растягивать блики по пропорциям экрана (анаморфный эффект)

### 4.3 Vignette (Виньетирование)

#### Базовые параметры (из монолита):

##### `vignette` (bool)
- **UI:** Checkbox "Виньетирование"
- **По умолчанию:** `False`
- **QML Property:** `vignetteEnabled`
- **Описание:** Включает затемнение краев кадра

##### `vignette_strength` (float)
- **UI:** Slider "Сила виньетки"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.02
- **По умолчанию:** 0.35
- **QML Property:** `vignetteStrength`
- **Описание:** Сила затемнения краев

#### Расширенный параметр Qt 6.10:

##### `vignette_radius` (float) ✨ NEW
- **UI:** Slider "Радиус виньетки"
- **Диапазон:** 0.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.4
- **QML Property:** `vignetteRadius`
- **Описание:** Радиус области без затемнения (0=весь экран темный, 1=только углы)

---

## 🌈 5. Color Adjustments (Цветокоррекция) ✨ NEW Qt 6.10

### Все параметры новые:

#### `adjustment_brightness` (float)
- **UI:** Slider "Яркость"
- **Диапазон:** -1.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.0
- **QML Property:** `adjustmentBrightness` (в ExtendedSceneEnvironment)
- **Описание:** Корректировка яркости (-1=темнее, +1=светлее)

#### `adjustment_contrast` (float)
- **UI:** Slider "Контраст"
- **Диапазон:** -1.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.0
- **QML Property:** `adjustmentContrast`
- **Описание:** Корректировка контраста (-1=меньше, +1=больше)

#### `adjustment_saturation` (float)
- **UI:** Slider "Насыщенность"
- **Диапазон:** -1.0 - 1.0
- **Шаг:** 0.01
- **По умолчанию:** 0.0
- **QML Property:** `adjustmentSaturation`
- **Описание:** Корректировка насыщенности цветов (-1=черно-белое, +1=очень насыщенно)

---

## 🔧 Интеграция с QML

### Маппинг Python ключей → QML properties:

```python
# В MainWindow._on_effects_changed(effects_params: dict)

# Bloom
qml.setProperty("glowEnabled", effects_params.get("bloom_enabled", True))
qml.setProperty("glowIntensity", effects_params.get("bloom_intensity", 0.5))
qml.setProperty("glowHDRMinimumValue", effects_params.get("bloom_threshold", 1.0))
qml.setProperty("glowBloom", effects_params.get("bloom_spread", 0.65))
# Qt 6.10 расширенные
qml.setProperty("glowStrength", effects_params.get("bloom_glow_strength", 0.8))
qml.setProperty("glowHDRMaximumValue", effects_params.get("bloom_hdr_max", 2.0))
qml.setProperty("glowHDRScale", effects_params.get("bloom_hdr_scale", 2.0))
qml.setProperty("glowQualityHigh", effects_params.get("bloom_quality_high", False))
qml.setProperty("glowUseBicubicUpscale", effects_params.get("bloom_bicubic_upscale", False))

# Tonemap
tonemap_mode_map = {
    "filmic": "SceneEnvironment.TonemapModeFilmic",
    "aces": "SceneEnvironment.TonemapModeAces",
    "reinhard": "SceneEnvironment.TonemapModeReinhard",
    "gamma": "SceneEnvironment.TonemapModeGammaOnly",
    "linear": "SceneEnvironment.TonemapModeNone"
}
qml.setProperty("tonemapMode", tonemap_mode_map[effects_params.get("tonemap_mode", "filmic")])
# Qt 6.10 расширенные
qml.setProperty("exposure", effects_params.get("tonemap_exposure", 1.0))
qml.setProperty("whitePoint", effects_params.get("tonemap_white_point", 2.0))

# Depth of Field
qml.setProperty("depthOfFieldEnabled", effects_params.get("depth_of_field", False))
qml.setProperty("depthOfFieldFocusDistance", effects_params.get("dof_focus_distance", 2200.0))
qml.setProperty("depthOfFieldBlurAmount", effects_params.get("dof_blur", 4.0))

# Lens Flare
qml.setProperty("lensFlareEnabled", effects_params.get("lens_flare", False))
# Qt 6.10 расширенные
qml.setProperty("lensFlareGhostCount", effects_params.get("lens_flare_ghost_count", 3))
qml.setProperty("lensFlareGhostDispersal", effects_params.get("lens_flare_ghost_dispersal", 0.6))
qml.setProperty("lensFlareHaloWidth", effects_params.get("lens_flare_halo_width", 0.25))
qml.setProperty("lensFlareBloomBias", effects_params.get("lens_flare_bloom_bias", 0.0))
qml.setProperty("lensFlareStretchToAspect", effects_params.get("lens_flare_stretch_to_aspect", False))

# Vignette
qml.setProperty("vignetteEnabled", effects_params.get("vignette", False))
qml.setProperty("vignetteStrength", effects_params.get("vignette_strength", 0.35))
# Qt 6.10 расширенный
qml.setProperty("vignetteRadius", effects_params.get("vignette_radius", 0.4))

# Color Adjustments (Qt 6.10+)
qml.setProperty("adjustmentBrightness", effects_params.get("adjustment_brightness", 0.0))
qml.setProperty("adjustmentContrast", effects_params.get("adjustment_contrast", 0.0))
qml.setProperty("adjustmentSaturation", effects_params.get("adjustment_saturation", 0.0))
```

---

## 📊 Defaults (для добавления в defaults.py)

```python
EFFECTS_DEFAULTS = {
    # Bloom
    "bloom_enabled": True,
    "bloom_intensity": 0.5,
    "bloom_threshold": 1.0,
    "bloom_spread": 0.65,
    # Qt 6.10 расширенные
    "bloom_glow_strength": 0.8,
    "bloom_hdr_max": 2.0,
    "bloom_hdr_scale": 2.0,
    "bloom_quality_high": False,
    "bloom_bicubic_upscale": False,
    
    # Tonemap
    "tonemap_enabled": True,
    "tonemap_mode": "filmic",
    # Qt 6.10 расширенные
    "tonemap_exposure": 1.0,
    "tonemap_white_point": 2.0,
    
    # Depth of Field
    "depth_of_field": False,
    "dof_focus_distance": 2200.0,
    "dof_blur": 4.0,
    
    # Motion Blur (НЕ ПОДДЕРЖИВАЕТСЯ в Qt 6.10)
    "motion_blur": False,
    "motion_blur_amount": 0.2,
    
    # Lens Flare
    "lens_flare": False,
    # Qt 6.10 расширенные
    "lens_flare_ghost_count": 3,
    "lens_flare_ghost_dispersal": 0.6,
    "lens_flare_halo_width": 0.25,
    "lens_flare_bloom_bias": 0.0,
    "lens_flare_stretch_to_aspect": False,
    
    # Vignette
    "vignette": False,
    "vignette_strength": 0.35,
    # Qt 6.10 расширенный
    "vignette_radius": 0.4,
    
    # Color Adjustments (Qt 6.10+)
    "adjustment_brightness": 0.0,
    "adjustment_contrast": 0.0,
    "adjustment_saturation": 0.0,
}
```

---

## ⚠️ Известные ограничения

### 1. Motion Blur НЕ ПОДДЕРЖИВАЕТСЯ
**Проблема:** Qt Quick 3D ExtendedSceneEnvironment НЕ ИМЕЕТ встроенной поддержки Motion Blur в Qt 6.10.

**Решение (опционально):**
- Реализовать кастомный Effect с velocity-based motion blur shader
- Использовать TAA (Temporal Anti-Aliasing) как частичную альтернативу

**Код checkbox остается в UI для будущей совместимости.**

### 2. Совместимость с Qt < 6.10
Расширенные параметры (помеченные ✨ NEW) **недоступны** в Qt < 6.10.

**Fallback стратегия:**
- Проверять версию Qt перед использованием новых параметров
- Скрывать/отключать новые контролы в старых версиях

---

## 📚 Справочные материалы

- [Qt Quick 3D ExtendedSceneEnvironment Documentation](https://doc.qt.io/qt-6/qml-qtquick3d-extendedsceneenvironment.html)
- [Qt Quick 3D Effects Examples](https://doc.qt.io/qt-6/qtquick3d-effects-example.html)
- [PBR Material Rendering in Qt Quick 3D](https://doc.qt.io/qt-6/qtquick3d-pbr.html)

---

**Документация создана:** 2025-01-13  
**Автор:** PneumoStabSim Professional Graphics System  
**Версия:** 1.0
