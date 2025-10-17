# План рефакторинга QML - PneumoStabSim Professional

## 📊 Текущее состояние

### Главный файл: `assets/qml/main.qml` (1400+ строк)

**Структура:**
- Properties (параметры геометрии, анимации, графики, материалов)
- Utility functions (математика, углы, URL)
- Camera system (орбитальная камера)
- Animation system (кэширование вычислений)
- Lighting (4 источника света)
- Materials library (8 материалов PBR)
- Suspension geometry (4 угла подвески)
- Environment (IBL, fog, SSAO)
- Effects (bloom, DOF, tonemap)
- Mouse controls
- Batch update system

### Существующие компоненты:
- `IblProbeLoader.qml` - загрузчик IBL
- `CorrectedSuspensionCorner.qml` - геометрия угла подвески
- `Materials.qml` - библиотека материалов
- Различные backup/fallback файлы

---

## 🎯 Цели рефакторинга

### 1. **Модульность** (по примеру Python-панелей)
- Разделить на логические компоненты
- Каждый компонент отвечает за свою область
- Четкое API взаимодействия

### 2. **Читаемость**
- Файлы до 300-400 строк
- Ясная структура каждого компонента
- Документированные интерфейсы

### 3. **Поддерживаемость**
- Легко найти нужный функционал
- Изолированное тестирование компонентов
- Переиспользование кода

---

## 📁 Предлагаемая структура

```
assets/qml/
├── main_refactored.qml           # Главный файл-композитор (200-300 строк)
│
├── core/                         # Ядро системы
│   ├── Properties.qml            # Все root properties
│   ├── StateManager.qml          # Управление состоянием
│   └── UpdateBridge.qml          # Python↔QML батч-обновления
│
├── camera/                       # Система камеры
│   ├── OrbitalCamera.qml         # Орбитальная камера
│   ├── CameraControls.qml        # Mouse/keyboard контроллы
│   └── CameraDefaults.qml        # Дефолтные значения
│
├── environment/                  # Окружение и эффекты
│   ├── SceneEnvironment.qml      # ExtendedSceneEnvironment настройка
│   ├── IblProbeLoader.qml        # ✅ Уже существует
│   ├── Fog.qml                   # Туман (Qt 6.10+)
│   └── PostEffects.qml           # Bloom, SSAO, DOF, Vignette
│
├── lighting/                     # Система освещения
│   ├── LightingRig.qml           # Композитор всех источников
│   ├── KeyLight.qml              # Главный свет
│   ├── FillLight.qml             # Заполняющий свет
│   ├── RimLight.qml              # Контровой свет
│   └── PointLight.qml            # Акцентный точечный свет
│
├── materials/                    # Библиотека материалов
│   ├── MaterialsLibrary.qml      # ✅ Адаптировать существующий Materials.qml
│   ├── FrameMaterial.qml         # Материал рамы
│   ├── LeverMaterial.qml         # Материал рычагов
│   ├── CylinderMaterial.qml      # Материал цилиндров (glass)
│   └── PistonMaterial.qml        # Материал поршней
│
├── geometry/                     # 3D геометрия подвески
│   ├── SuspensionSystem.qml      # Композитор 4 углов
│   ├── SuspensionCorner.qml      # ✅ Рефакторинг CorrectedSuspensionCorner.qml
│   ├── Frame.qml                 # U-образная рама (3 балки)
│   ├── Lever.qml                 # Рычаг
│   ├── Cylinder.qml              # Цилиндр + поршень
│   └── Joints.qml                # Шарниры
│
├── utils/                        # Утилиты
│   ├── MathUtils.qml             # Математические функции
│   ├── GeometryCache.qml         # Кэш геометрических вычислений
│   ├── AnimationCache.qml        # Кэш анимационных вычислений
│   └── ColorUtils.qml            # Работа с цветами
│
└── ui/                           # UI элементы (опционально)
    └── InfoPanel.qml             # Информационная панель
```

---

## 🔄 Фазы рефакторинга

### **ФАЗА 1: Подготовка и Core** (день 1)

#### Шаги:
1. ✅ Создать структуру каталогов
2. ✅ Создать `core/Properties.qml` - вынести все root properties
3. ✅ Создать `core/StateManager.qml` - управление состоянием
4. ✅ Создать `core/UpdateBridge.qml` - батч-обновления Python↔QML
5. ✅ Создать `utils/MathUtils.qml` - математические функции

#### Критерий готовности:
- [ ] Все properties вынесены в отдельный файл
- [ ] Batch update система работает
- [ ] Utility функции изолированы

---

### **ФАЗА 2: Camera System** (день 1-2)

#### Шаги:
1. ✅ Создать `camera/OrbitalCamera.qml` - орбитальная камера
2. ✅ Создать `camera/CameraControls.qml` - mouse/keyboard контроллы
3. ✅ Создать `camera/CameraDefaults.qml` - дефолтные значения
4. ✅ Интегрировать в main_refactored.qml

#### Критерий готовности:
- [ ] Орбитальная камера работает независимо
- [ ] Mouse controls (ЛКМ вращение, ПКМ панорама, колесо зум)
- [ ] Клавиши R (reset), F (fit), Space (анимация)

---

### **ФАЗА 3: Environment & Effects** (день 2)

#### Шаги:
1. ✅ Адаптировать `environment/IblProbeLoader.qml` (уже есть)
2. ✅ Создать `environment/SceneEnvironment.qml` - ExtendedSceneEnvironment
3. ✅ Создать `environment/Fog.qml` - туман (Qt 6.10+)
4. ✅ Создать `environment/PostEffects.qml` - Bloom, SSAO, DOF

#### Критерий готовности:
- [ ] IBL загружается корректно
- [ ] ExtendedSceneEnvironment настроен
- [ ] Все эффекты работают (bloom, fog, SSAO, vignette)

---

### **ФАЗА 4: Lighting System** (день 2-3)

#### Шаги:
1. ✅ Создать `lighting/LightingRig.qml` - композитор
2. ✅ Создать `lighting/KeyLight.qml` - главный свет
3. ✅ Создать `lighting/FillLight.qml` - заполняющий
4. ✅ Создать `lighting/RimLight.qml` - контровой
5. ✅ Создать `lighting/PointLight.qml` - точечный акцент

#### Критерий готовности:
- [ ] 3-точечная схема освещения работает
- [ ] Управление из Python (яркость, цвет, углы)
- [ ] Тени настраиваются

---

### **ФАЗА 5: Materials Library** (день 3)

#### Шаги:
1. ✅ Адаптировать `materials/MaterialsLibrary.qml`
2. ✅ Создать `materials/FrameMaterial.qml` - металл рамы
3. ✅ Создать `materials/LeverMaterial.qml` - металл рычагов
4. ✅ Создать `materials/CylinderMaterial.qml` - стекло цилиндров
5. ✅ Создать `materials/PistonMaterial.qml` - поршень с warning цветом

#### Критерий готовности:
- [ ] PBR материалы корректно рендерятся
- [ ] Прозрачность цилиндров работает (IOR, transmission)
- [ ] Warning цвета поршней при ошибке длины штока

---

### **ФАЗА 6: Suspension Geometry** (день 3-4)

#### Шаги:
1. ✅ Создать `geometry/Frame.qml` - U-рама (3 балки)
2. ✅ Рефакторить `geometry/SuspensionCorner.qml` (из CorrectedSuspensionCorner)
3. ✅ Создать `geometry/Lever.qml` - рычаг
4. ✅ Создать `geometry/Cylinder.qml` - цилиндр + поршень
5. ✅ Создать `geometry/Joints.qml` - шарниры
6. ✅ Создать `geometry/SuspensionSystem.qml` - композитор 4 углов

#### Критерий готовности:
- [ ] Все 4 угла подвески работают независимо
- [ ] Длина штока поршня константна (200мм)
- [ ] Визуальный warning при ошибке геометрии

---

### **ФАЗА 7: Integration & Testing** (день 4-5)

#### Шаги:
1. ✅ Создать `main_refactored.qml` - главный композитор
2. ✅ Интегрировать все компоненты
3. ✅ Тестирование Python↔QML коммуникации
4. ✅ Регрессионное тестирование всех функций
5. ✅ Оптимизация производительности
6. ✅ Документация API

#### Критерий готовности:
- [ ] Все функции main.qml работают
- [ ] Python обновления применяются корректно
- [ ] FPS >= 60 при анимации
- [ ] Нет регрессий в функциональности

---

## 📝 Правила рефакторинга

### 1. **Сохранение обратной совместимости**
- Не ломать существующий Python API
- Все QML функции доступны: `applyGeometryUpdates()`, `applyLightingUpdates()` и т.д.
- Сигналы `batchUpdatesApplied` работают

### 2. **Именование компонентов**
```qml
// ✅ ПРАВИЛЬНО: PascalCase для компонентов
OrbitalCamera { }
KeyLight { }
FrameMaterial { }

// ✅ ПРАВИЛЬНО: camelCase для свойств и функций
property real userBeamSize: 120
function applyGeometryUpdates(params) { }

// ✅ ПРАВИЛЬНО: snake_case для ключей Python↔QML
{
    "frame_length": 3200,
    "track_width": 1600
}
```

### 3. **Документирование**
```qml
/*
 * OrbitalCamera - Orbital camera system
 * 
 * Features:
 *  - Mouse controls (LMB rotate, RMB pan, wheel zoom)
 *  - Auto-rotation mode
 *  - Reset view (R key or double-click)
 * 
 * Properties:
 *  - cameraDistance: Distance from pivot (mm)
 *  - yawDeg: Horizontal rotation (degrees)
 *  - pitchDeg: Vertical rotation (degrees)
 * 
 * Functions:
 *  - resetView(): Reset camera to default position
 *  - autoFitFrame(): Fit frame in view
 */
Node { }
```

### 4. **Комментарии на русском**
```qml
// ✅ ПРАВИЛЬНО: Комментарии на русском
// Вращение камеры вокруг центральной точки

// ✅ ПРАВИЛЬНО: Технические термины на английском
// Используем SLERP для smooth rotation interpolation
```

---

## 🧪 Тестирование

### Unit тесты QML компонентов:
```
tests/qml/
├── test_camera_orbital.qml          # Тест орбитальной камеры
├── test_lighting_rig.qml            # Тест системы освещения
├── test_materials_library.qml       # Тест материалов
├── test_suspension_corner.qml       # Тест угла подвески
└── test_python_qml_bridge.py        # Python↔QML integration
```

### Критерии прохождения:
- [ ] Все компоненты загружаются без ошибок
- [ ] Python обновления применяются корректно
- [ ] FPS >= 60 при анимации
- [ ] Нет утечек памяти
- [ ] Визуальное соответствие оригиналу

---

## 📊 Метрики качества

### До рефакторинга:
- **main.qml**: 1400+ строк
- **Компонентов**: 3
- **Модульность**: Низкая
- **Поддерживаемость**: Средняя

### После рефакторинга (цель):
- **main_refactored.qml**: ~300 строк (композитор)
- **Компонентов**: ~25
- **Модульность**: Высокая
- **Поддерживаемость**: Отличная
- **Производительность**: FPS >= 60

---

## 🚀 Следующие шаги

### 1. **Подтверждение плана**
- [ ] Рассмотреть предложенную структуру
- [ ] Уточнить приоритеты фаз
- [ ] Подтвердить timeline (4-5 дней)

### 2. **Запуск Фазы 1**
- [ ] Создать каталоги `assets/qml/core/`, `utils/`
- [ ] Создать `Properties.qml`
- [ ] Создать `MathUtils.qml`
- [ ] Первые тесты

### 3. **Документация**
- [ ] Создать `QML_API_REFERENCE.md`
- [ ] Документировать каждый компонент
- [ ] Примеры использования

---

## ⚠️ Риски и митигация

### Риск 1: Поломка Python↔QML API
**Митигация:** 
- Сохранить старый `main.qml` как `main_legacy.qml`
- Протестировать все Python функции после каждой фазы
- Использовать integration тесты

### Риск 2: Падение производительности
**Митигация:**
- Профилирование после каждой фазы
- Кэширование вычислений (уже реализовано)
- Lazy loading компонентов

### Риск 3: Визуальные регрессии
**Митигация:**
- Скриншоты до/после рефакторинга
- Визуальное сравнение рендера
- User acceptance testing

---

## 🎯 Ожидаемый результат

### **Чистая модульная архитектура QML:**
```
Main (композитор)
  ├── Core (properties, state)
  ├── Camera (orbital, controls)
  ├── Environment (IBL, fog, effects)
  ├── Lighting (rig, key/fill/rim/point)
  ├── Materials (library, PBR)
  └── Geometry (frame, suspension system)
```

### **Преимущества:**
✅ Читаемый код (файлы <400 строк)
✅ Легкая поддержка и расширение
✅ Изолированное тестирование
✅ Переиспользование компонентов
✅ Соответствие архитектуре Python-кода

---

**Готов начать рефакторинг?** 🚀

Предлагаю начать с **Фазы 1: Core & Utils** - это база для всех остальных компонентов.
