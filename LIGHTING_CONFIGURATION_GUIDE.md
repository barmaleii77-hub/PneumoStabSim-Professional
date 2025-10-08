# 💡 ИСТОЧНИКИ СВЕТА В ПРОЕКТЕ - ПОЛНЫЙ АНАЛИЗ

## 📍 РАСПОЛОЖЕНИЕ ПАРАМЕТРОВ ОСВЕЩЕНИЯ

### 🎯 **ОСНОВНЫЕ ФАЙЛЫ С НАСТРОЙКАМИ ОСВЕЩЕНИЯ:**

---

## 1. 📁 `assets/qml/main.qml` - ГЛАВНЫЙ 3D ФАЙЛ

### 🔥 **ОСНОВНАЯ СХЕМА ОСВЕЩЕНИЯ** (строки 369-404)

```qml
// ✨ УЛУЧШЕННОЕ ОСВЕЩЕНИЕ: Трехточечная схема освещения

// Key Light (основной свет) - яркий направленный свет
DirectionalLight {
    id: keyLight
    eulerRotation.x: -30        // Угол наклона по X
    eulerRotation.y: -45        // Угол поворота по Y
    brightness: 2.8             // ЯРКОСТЬ (основной параметр)
    color: "#ffffff"            // Цвет света
}

// ✨ Fill Light (заполняющий свет) - смягчает тени
DirectionalLight {
    id: fillLight
    eulerRotation.x: -60        // Угол наклона
    eulerRotation.y: 135        // Угол поворота
    brightness: 1.2             // Меньшая яркость
    color: "#f0f0ff"           // Слегка голубоватый
}

// ✨ Rim Light (контровой свет) - создает контур объектов
DirectionalLight {
    id: rimLight
    eulerRotation.x: 15         // Контровое освещение
    eulerRotation.y: 180        // Сзади
    brightness: 1.5             // Средняя яркость
    color: "#ffffcc"           // Теплый оттенок
}

// ✨ Point Light (точечный акцент) - подсвечивает центр
PointLight {
    id: accentLight
    position: Qt.vector3d(0, 1800, 1500)  // Позиция в пространстве
    brightness: 20000           // Высокая яркость
    color: "#ffffff"           // Белый свет
    quadraticFade: 0.00008     // Мягкое затухание
}
```

### 🌍 **ОКРУЖЕНИЕ СЦЕНЫ** (строки 345-351)

```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color  // Тип фона
    clearColor: "#2a2a2a"                   // ЦВЕТ ФОНА
    antialiasingMode: SceneEnvironment.MSAA // Сглаживание
    antialiasingQuality: SceneEnvironment.High // Качество
}
```

### 🔧 **ДОПОЛНИТЕЛЬНЫЙ СВЕТ** (строки 406-411)

```qml
// Дополнительный направленный свет
DirectionalLight {
    eulerRotation.x: -30
    eulerRotation.y: -45
    brightness: 2.5             // Настраиваемая яркость
}
```

---

## 2. 📁 `assets/qml/main_working_builtin.qml` - ПРОСТАЯ СХЕМА

### 💡 **БАЗОВОЕ ОСВЕЩЕНИЕ** (строки 23-28)

```qml
DirectionalLight {
    eulerRotation.x: -30        // Угол по X
    eulerRotation.y: -30        // Угол по Y
    brightness: 1.5             // ЯРКОСТЬ
    color: "#ffffff"            // ЦВЕТ
}
```

### 🌍 **ОКРУЖЕНИЕ** (строки 15-20)

```qml
environment: SceneEnvironment {
    backgroundMode: SceneEnvironment.Color
    clearColor: "#1a1a2e"                   // ТЕМНО-СИНИЙ ФОН
    antialiasingMode: SceneEnvironment.MSAA
    antialiasingQuality: SceneEnvironment.High
}
```

---

## 3. 📁 `assets/qml/components/Materials.qml` - МАТЕРИАЛЫ

### ✨ **СВЕТОВЫЕ СВОЙСТВА МАТЕРИАЛОВ**

```qml
// Красный металл
readonly property PrincipledMaterial redMetal: PrincipledMaterial {
    baseColor: "#d01515"
    metalness: 1.0              // Металличность (влияет на отражение света)
    roughness: 0.28             // Шероховатость (влияет на рассеивание)
    clearcoatAmount: 0.25       // Прозрачное покрытие
    clearcoatRoughnessAmount: 0.1
}

// Стекло (прозрачный материал)
readonly property PrincipledMaterial glass: PrincipledMaterial {
    baseColor: "#ffffff"
    metalness: 0.0
    roughness: 0.05             // Очень гладкое (отражает свет)
    opacity: 0.35               // Прозрачность
    alphaMode: PrincipledMaterial.Blend
}
```

---

## 4. 🔍 **ДРУГИЕ QML ФАЙЛЫ С ОСВЕЩЕНИЕМ:**

### 📁 `assets/qml/main_backup.qml`
### 📁 `assets/qml/main_enhanced_2d.qml`
### 📁 `assets/qml/main_interactive_frame.qml`
### 📁 `assets/qml/diagnostic.qml`

**Все эти файлы содержат похожие настройки DirectionalLight и SceneEnvironment**

---

## 🛠️ **ПАРАМЕТРЫ КОТОРЫЕ МОЖНО НАСТРАИВАТЬ:**

### 🔆 **ПАРАМЕТРЫ НАПРАВЛЕННОГО СВЕТА (DirectionalLight):**

```qml
DirectionalLight {
    // 📐 УГЛЫ ОСВЕЩЕНИЯ
    eulerRotation.x: -30    // Наклон вверх/вниз (-90 до 90)
    eulerRotation.y: -45    // Поворот влево/вправо (-180 до 180)
    eulerRotation.z: 0      // Крен (обычно 0)
    
    // 💡 ЯРКОСТЬ И ЦВЕТ
    brightness: 2.8         // Интенсивность (0.0 - 10.0+)
    color: "#ffffff"        // Цвет в hex (#ffffff = белый)
    
    // 🎯 ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ
    castsShadow: true       // Отбрасывает тени
    shadowFactor: 75        // Интенсивность теней (0-100)
    shadowMapQuality: Light.ShadowMapQualityHigh  // Качество теней
}
```

### 💡 **ПАРАМЕТРЫ ТОЧЕЧНОГО СВЕТА (PointLight):**

```qml
PointLight {
    // 📍 ПОЗИЦИЯ В ПРОСТРАНСТВЕ
    position: Qt.vector3d(0, 1800, 1500)  // X, Y, Z координаты
    
    // 💡 ИНТЕНСИВНОСТЬ И ЦВЕТ
    brightness: 20000       // Яркость (больше для точечных источников)
    color: "#ffffff"        // Цвет света
    
    // 🌊 ЗАТУХАНИЕ
    constantFade: 1.0       // Постоянное затухание
    linearFade: 0.0         // Линейное затухание с расстоянием
    quadraticFade: 0.00008  // Квадратичное затухание
}
```

### 🌍 **ПАРАМЕТРЫ ОКРУЖЕНИЯ (SceneEnvironment):**

```qml
environment: SceneEnvironment {
    // 🎨 ФОН
    backgroundMode: SceneEnvironment.Color    // Тип фона
    clearColor: "#2a2a2a"                     // Цвет фона
    
    // 🔧 КАЧЕСТВО РЕНДЕРИНГА
    antialiasingMode: SceneEnvironment.MSAA   // Сглаживание
    antialiasingQuality: SceneEnvironment.High // Качество
    
    // 🌍 ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ
    lightProbe: null        // IBL освещение
    skyboxBlurAmount: 0.0   // Размытие skybox
    tonemapMode: SceneEnvironment.TonemapModeNone  // Тональное отображение
}
```

---

## 🎛️ **КАК ИЗМЕНИТЬ ПАРАМЕТРЫ ОСВЕЩЕНИЯ:**

### 1. **📝 ПРЯМОЕ РЕДАКТИРОВАНИЕ QML:**
- Открыть `assets/qml/main.qml`
- Изменить параметры в блоках DirectionalLight и PointLight
- Сохранить файл - изменения применятся сразу

### 2. **🐍 ЧЕРЕЗ PYTHON КОД:**
```python
# В main_window.py можно добавить методы для управления освещением
def update_lighting(self, key_brightness=2.8, fill_brightness=1.2):
    self.qml_object.setProperty("keyLightBrightness", key_brightness)
    self.qml_object.setProperty("fillLightBrightness", fill_brightness)
```

### 3. **⚙️ ЧЕРЕЗ КОНФИГУРАЦИОННЫЙ ФАЙЛ:**
Создать `config/lighting_config.yaml`:
```yaml
lighting:
  key_light:
    brightness: 2.8
    color: "#ffffff"
    angle_x: -30
    angle_y: -45
  fill_light:
    brightness: 1.2
    color: "#f0f0ff"
  background:
    color: "#2a2a2a"
```

---

## 🎯 **РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ ДЛЯ РАЗНЫХ СЦЕНАРИЕВ:**

### 🌅 **ДНЕВНОЕ ОСВЕЩЕНИЕ:**
```qml
DirectionalLight {
    brightness: 3.2
    color: "#fff8e1"        // Теплый дневной свет
    eulerRotation.x: -25
    eulerRotation.y: -30
}
clearColor: "#87ceeb"       // Небесно-голубой фон
```

### 🌙 **НОЧНОЕ ОСВЕЩЕНИЕ:**
```qml
DirectionalLight {
    brightness: 1.8
    color: "#b3c6ff"        // Холодный лунный свет
    eulerRotation.x: -60
    eulerRotation.y: 45
}
clearColor: "#0f0f23"       // Темно-синий фон
```

### 🏭 **ПРОМЫШЛЕННОЕ ОСВЕЩЕНИЕ:**
```qml
DirectionalLight {
    brightness: 4.0
    color: "#f0f0f0"        // Яркий белый свет
    eulerRotation.x: -20
    eulerRotation.y: 0
}
clearColor: "#404040"       // Серый фон
```

---

## 📍 **РЕЗЮМЕ - ГДЕ НАСТРАИВАТЬ:**

1. **🎯 Основное место**: `assets/qml/main.qml` (строки 369-411)
2. **🔧 Материалы**: `assets/qml/components/Materials.qml`
3. **🌍 Окружение**: В каждом QML файле в блоке `SceneEnvironment`
4. **🐍 Python**: Можно добавить управление через `main_window.py`
5. **⚙️ Конфиг**: Создать файл конфигурации освещения

**💡 Все изменения в QML файлах применяются мгновенно при сохранении!**

---

*Анализ освещения завершен: 2025-01-03*  
*PneumoStabSim Professional - Lighting Configuration Guide*  
*"Свет создает атмосферу и показывает детали" 💡*
