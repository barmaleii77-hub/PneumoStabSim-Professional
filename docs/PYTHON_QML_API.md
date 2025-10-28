# Python ↔ QML API Documentation

## Overview

PneumoStabSim uses a bidirectional communication system between the Python runtime (panels, simulation manager, bridge helpers) and the QML3D scene.

## Граф связей Python ↔ QML

```mermaid
graph TD
 SettingsManager["SettingsManager\n(app_settings.json)"] -->|загружает стартовые состояния| MainWindow
 GraphicsPanel["Qt панели (Geometry/Graphics/...)"] -->|Qt-сигналы| SignalsRouter
 SimulationManager -->|StateSnapshot| SignalsRouter
 SignalsRouter -->|queue_update(...)| QMLBridge
 QMLBridge -->|setProperty('pendingPythonUpdates')| QMLRoot["QML root Item"]
 QMLBridge -->|invokeMethod('apply*Updates')| QMLRoot
 MainWindow -->|context property "window"| QMLRoot
 IblProbeLoader["IblProbeLoader.qml"] -->|window.logIblEvent(...)| MainWindow
 QMLRoot -->|signal batchUpdatesApplied(...)| MainWindow
 QMLRoot -->|window.logQmlEvent(...)| MainWindow
```

## Контекстные свойства

| Имя | Где задаётся | Назначение | Правила изменения |
| --- | --- | --- | --- |
| `window` | `UISetup._setup_qml_3d_view()` при загрузке рефакторенной версии `MainWindow` | Экспортирует экземпляр `MainWindow` в QML для вызова слотов и доступа к вспомогательным объектам (`event_logger`, `ibl_logger` и т.д.) | Контекст должен устанавливаться до `setSource`; при переименовании слотов обновляйте QML, особенно `IblProbeLoader.qml` и места, где проверяется `window.logQmlEvent`. 【F:src/ui/main_window/ui_setup.py†L94-L144】【F:assets/qml/components/IblProbeLoader.qml†L1-L47】

### Дополнительные контексты (legacy fallback)

При аварийном откате на `src/ui/main_window.py` в контекст также пробрасываются:

- `startLightingState`, `startQualityState`, `startCameraState`, `startMaterialsState`, `startEffectsState` — стартовые слепки панелей. 【F:src/ui/main_window.py†L228-L251】
- Набор параметров окружения согласно `ENVIRONMENT_CONTEXT_PROPERTIES`: `startBackgroundMode`, `startBackgroundColor`, `startSkyboxEnabled`, `startIblEnabled`, `startIblIntensity`, `startSkyboxBrightness`, `startProbeHorizon`, `startIblRotation`, `startIblSource`, `startIblFallback`, `startSkyboxBlur`, `startIblOffsetX`, `startIblOffsetY`, `startIblBindToCamera`, `startFogEnabled`, `startFogColor`, `startFogDensity`, `startFogNear`, `startFogFar`, `startFogHeightEnabled`, `startFogLeastY`, `startFogMostY`, `startFogHeightCurve`, `startFogTransmitEnabled`, `startFogTransmitCurve`, `startAoEnabled`, `startAoStrength`, `startAoRadius`, `startAoSoftness`, `startAoDither`, `startAoSampleRate`. 【F:src/ui/environment_schema.py†L298-L335】【F:src/ui/main_window.py†L201-L245】

Изменения: расширяя или переименовывая эти свойства, синхронизируйте `ENVIRONMENT_CONTEXT_PROPERTIES`, unit-тесты (`tests/unit/test_environment_schema.py`) и документацию; убедитесь, что QML использует новые имена.

## Зарегистрированные QML-типы

| QML импорт | Класс | Назначение | Правила изменения |
| --- | --- | --- | --- |
| `TestGeometry1.0` | `SimpleTriangle` | Минимальный треугольник для тестов загрузки геометрии. | Поддерживайте формат вершин и `setStride`; при смене имени обновляйте импорты QML. 【F:src/ui/triangle_geometry.py†L1-L59】
| `CustomGeometry1.0` | `SphereGeometry` | Процедурная сфера с нормалями. | Храните обновление через `updateData`; при добавлении параметров следите за сигналом `geometryNodeDirty`. 【F:src/ui/custom_geometry.py†L1-L118】
| `CustomGeometry1.0` | `CubeGeometry` | Процедурный куб с UV/нормалями. | Не меняйте порядок атрибутов без обновления QML-материалов. 【F:src/ui/custom_geometry.py†L118-L236】
| `StableGeometry1.0` | `StableTriangleGeometry` | Треугольник с контролем времени жизни буферов. | Любые правки должны сохранять вызовы `componentComplete()` и приватное хранение буферов. 【F:src/ui/stable_geometry.py†L1-L82】
| `StableGeometry1.0` | `GeometryProvider` | QObject, отдающий стабильную геометрию через `Property`. | При изменениях обновляйте сигнал `geometryChanged` и связанный QML код. 【F:src/ui/stable_geometry.py†L84-L122】
| `CorrectGeometry1.0` | `DocumentationBasedTriangle` | Пример точного следования API Qt. | Сохраняйте последовательность вызовов API; лог выводится в консоль для отладки. 【F:src/ui/correct_geometry.py†L1-L78】
| `SimpleGeometry1.0` | `SimpleSphere` | Упрощённая сфера без нормалей. | При добавлении нормалей скорректируйте `setStride` и атрибуты. 【F:src/ui/simple_geometry.py†L1-L76】
| `DirectGeometry1.0` | `DirectTriangle` | Демонстрация прямой генерации треугольника. | Сохраняйте минимализм (позиции только); QML импорт ожидает именно этот контракт. 【F:src/ui/direct_geometry.py†L1-L54】
| `GeometryExample1.0` | `ExampleTriangleGeometry` | Документированный пример с нормалями. | Следите за соответствием `updateData()` и поддержкой нормалей. 【F:src/ui/example_geometry.py†L1-L82】
| `GeometryExample1.0` | `ExampleGeometryModel` | QObject-обёртка, отдающая `ExampleTriangleGeometry`. | Поддерживайте свойство `geometry` как `constant=True`. 【F:src/ui/example_geometry.py†L82-L124】

## Сигналы и слоты

### QML → Python

| Источник | Сигнал/вызов | Обработчик Python | Правила изменения |
| --- | --- | --- | --- |
| `main.qml` | `batchUpdatesApplied(summary)` | `MainWindow._on_qml_batch_ack` → `QMLBridge.handle_qml_ack` | Поддерживайте подключение в `SignalsRouter._connect_qml_signals`; при изменении сигнатуры обновляйте `QMLBridge.handle_qml_ack` и логику подтверждений. 【F:assets/qml/main.qml†L16-L166】【F:src/ui/main_window/signals_router.py†L215-L233】【F:src/ui/main_window/qml_bridge.py†L360-L434】
| `IblProbeLoader.qml` | `window.logIblEvent(logEntry)` | Делегируется на `MainWindow.ibl_logger.logIblEvent` (через доступ к атрибуту) | При переименовании метода добавьте прокси-слот в `MainWindow`; убедитесь, что логгер остаётся `QObject` со `@Slot(str)`. 【F:assets/qml/components/IblProbeLoader.qml†L1-L47】【F:src/ui/ibl_logger.py†L7-L75】
| QML utility calls | `window.logQmlEvent(event_type, name)` | `MainWindow.logQmlEvent` | Сигнатура должна оставаться `(str, str)`; при расширении перечня типов обновите нормализацию `EventType`. 【F:src/ui/main_window/main_window_refactored.py†L205-L244】

### Python → QML

| Категория | Точка вызова | QML обработчик | Правила изменения |
| --- | --- | --- | --- |
| Батч-обновления | `QMLBridge.queue_update`/`flush_updates` → `setProperty("pendingPythonUpdates")` | `main.qml` → `onPendingPythonUpdatesChanged` + `applyBatchedUpdates` | При добавлении категории обновите `QMLBridge._prepare_for_qml` при необходимости сериализации и убедитесь, что QML обрабатывает ключ. 【F:src/ui/main_window/qml_bridge.py†L107-L193】【F:assets/qml/main.qml†L18-L74】
| Индивидуальные методы | `QMLBridge.QML_UPDATE_METHODS` (из `config/qml_bridge.yaml`) + `invoke_qml_function` | `apply*Updates` функции в QML | Поддерживайте список методов в YAML и убедитесь, что новые QML-функции отражены в документе и модуле `src/ui/qml_bridge.py`. 【F:config/qml_bridge.yaml†L1-L35】【F:src/ui/qml_bridge.py†L1-L147】【F:assets/qml/main.qml†L90-L166】
| Симуляция | `QMLBridge.set_simulation_state` | `applyBatchedUpdates` → `apply3DUpdates`/`applySimulationUpdates` | Изменяя структуру `StateSnapshot`, актуализируйте `_snapshot_to_payload` и QML обработчики. 【F:src/ui/main_window/qml_bridge.py†L195-L279】【F:assets/qml/main.qml†L90-L166】

---

## ?? Python ↔ QML Communication

###1. Geometry Parameters (Static)

**Function:** `updateGeometry(params)`

**Called from:** `MainWindow._on_geometry_changed()`

**Parameters:**
```javascript
{
 frameLength: float, // mm - Frame longitudinal length
 frameHeight: float, // mm - Horn height
 frameBeamSize: float, // mm - Beam cross-section size
 leverLength: float, // mm - Lever arm length
 cylinderBodyLength: float, // mm - Cylinder working length
 trackWidth: float, // mm - Distance between left/right corners
 frameToPivot: float, // mm - Distance from frame centerline to pivot
 rodPosition: float, //0..1 - Rod attachment position on lever
 boreHead: float, // mm - Head bore diameter
 boreRod: float, // mm - Rod bore diameter
 rodDiameter: float, // mm - Piston rod diameter
 pistonThickness: float // mm - Piston thickness
}
```

**Example (Python):**
```python
geometry_params = {
 'frameLength':2500.0,
 'frameHeight':650.0,
 'frameBeamSize':120.0,
 'leverLength':400.0,
 'cylinderBodyLength':570.0,
 # ... other parameters
}

QMetaObject.invokeMethod(
 self._qml_root_object,
 "updateGeometry",
 Qt.ConnectionType.DirectConnection,
 Q_ARG("QVariant", geometry_params)
)
```

---

###2. Piston Positions (Dynamic - Real-time Physics!)

**Function:** `updatePistonPositions(positions)`

**Called from:** `MainWindow._update_3d_scene_from_snapshot()`

**Parameters:**
```javascript
{
 fl: float, // mm - Front Left piston position (from cylinder start)
 fr: float, // mm - Front Right piston position
 rl: float, // mm - Rear Left piston position
 rr: float // mm - Rear Right piston position
}
```

**Calculation (Python - GeometryBridge):**
```python
# From CylinderState
stroke_mm = cylinder_state.stroke *1000.0 # m to mm
max_stroke_mm = cylinder_body_length *0.8 #80% of cylinder
piston_ratio =0.5 + (stroke_mm / (2 * max_stroke_mm)) #0..1
piston_ratio = np.clip(piston_ratio,0.1,0.9)
piston_position_mm = piston_ratio * cylinder_body_length
```

**Example (Python):**
```python
piston_positions = {
 'fl':125.5, # mm
 'fr':132.8,
 'rl':118.3,
 'rr':140.1
}

QMetaObject.invokeMethod(
 self._qml_root_object,
 "updatePistonPositions",
 Qt.ConnectionType.DirectConnection,
 Q_ARG("QVariant", piston_positions)
)
```

---

###3. Animation Parameters

**Function:** `updateAnimation(angles)`

**Parameters:**
```javascript
{
 fl: float, // degrees - Front Left lever angle
 fr: float, // degrees - Front Right lever angle
 rl: float, // degrees - Rear Left lever angle
 rr: float // degrees - Rear Right lever angle
}
```

**Example (Python):**
```python
angles = {'fl':5.2, 'fr': -3.1, 'rl':2.8, 'rr': -1.5}

QMetaObject.invokeMethod(
 self._qml_root_object,
 "updateAnimation",
 Qt.ConnectionType.DirectConnection,
 Q_ARG("QVariant", angles)
)
```

---

## ?? QML ↔ Python Communication

### Signals (Future Implementation)

**Planned:**
- `cameraPositionChanged(x, y, z)` - Camera moved by user
- `cornerSelected(corner_id)` - User clicked on a corner
- `visualizationModeChanged(mode)` - User changed view mode

---

## ?? QML Properties (Read/Write from Python)

### Geometry Properties
```javascript
property real userFrameLength:2000.0 // mm
property real userFrameHeight:650.0 // mm
property real userBeamSize:120.0 // mm
property real userLeverLength:315.0 // mm
property real userCylinderLength:250.0 // mm
property real userTrackWidth:300.0 // mm
property real userFrameToPivot:150.0 // mm
property real userRodPosition:0.6 //0..1
property real userBoreHead:80.0 // mm
property real userBoreRod:80.0 // mm
property real userRodDiameter:35.0 // mm
property real userPistonThickness:25.0 // mm
```

### Animation Properties
```javascript
property real userAmplitude:8.0 // degrees
property real userFrequency:1.0 // Hz
property real userPhaseGlobal:0.0 // degrees
property real userPhaseFL:0.0 // degrees
property real userPhaseFR:0.0 // degrees
property real userPhaseRL:0.0 // degrees
property real userPhaseRR:0.0 // degrees
property bool isRunning: false // Animation on/off
```

### Physics Properties (NEW!)
```javascript
property real userPistonPositionFL:125.0 // mm - FROM PYTHON PHYSICS!
property real userPistonPositionFR:125.0 // mm
property real userPistonPositionRL:125.0 // mm
property real userPistonPositionRR:125.0 // mm
```

### Direct Property Access (Python)
```python
# Set property
self._qml_root_object.setProperty("isRunning", True)

# Get property
is_running = self._qml_root_object.property("isRunning")
```

---

## ?? Data Flow Examples

### Example1: Start Simulation
```python
# Python (MainWindow._on_sim_control)
def _on_sim_control(self, command: str):
 if command == "start":
 bus.start_simulation.emit()
 self.is_simulation_running = True

 # Update QML
 if self._qml_root_object:
 self._qml_root_object.setProperty("isRunning", True)
```

### Example2: Update from Physics Snapshot
```python
# Python (MainWindow._update_3d_scene_from_snapshot)
def _update_3d_scene_from_snapshot(self, snapshot):
 # Extract data from physics engine
 piston_positions = {}
 for corner in ['fl', 'fr', 'rl', 'rr']:
 corner_data = snapshot.corners[corner]
 cylinder_state = corner_data.cylinder_state

 # Use GeometryBridge to calculate3D position
 corner_3d = self.geometry_converter.get_corner_3d_coords(
 corner,
 corner_data.lever_angle,
 cylinder_state # Physics data!
 )

 piston_positions[corner] = corner_3d['pistonPositionMm']

 # Send to QML
 QMetaObject.invokeMethod(
 self._qml_root_object,
 "updatePistonPositions",
 Qt.ConnectionType.DirectConnection,
 Q_ARG("QVariant", piston_positions)
 )
```

### Example3: User Changes Geometry in UI
```python
# Python (GeometryPanel.geometry_changed signal)
geometry_params = {
 'frameLength': self.wheelbase_spin.value() *1000, # m to mm
 'leverLength': self.lever_length_spin.value() *1000,
 # ... other parameters
}

# Send to QML
QMetaObject.invokeMethod(
 main_window._qml_root_object,
 "updateGeometry",
 Qt.ConnectionType.DirectConnection,
 Q_ARG("QVariant", geometry_params)
)
```

---

## ?? Visualization Details

### Coordinate System
- X-axis: Transverse (left/right) - Red
- Y-axis: Vertical (up/down) - Green
- Z-axis: Longitudinal (front/rear) - Blue
- Origin: Frame center, beam bottom

### Piston Position Convention
-0 mm: Cylinder start (near tail rod)
- pistonPositionMm: Absolute position from cylinder start
- lCylinder: Cylinder end (where rod exits)
- Valid range:10% to90% of cylinder length (safety limits)

### Example Calculation
```
Cylinder length:250mm
Piston position:125mm (center)
Ratio:0.5

Stroke +50mm (extension):
 Position:125 +50 =175mm
 Ratio:0.7

Stroke -50mm (retraction):
 Position:125 -50 =75mm
 Ratio:0.3
```

---

## ? Performance Considerations

### Update Frequency
- Geometry: ~1 Hz (user changes)
- Piston positions: ~60 Hz (physics simulation)
- Animation: ~60 Hz (smooth visualization)

### Optimization
- Use `DirectConnection` for synchronous updates
- Batch multiple property updates in single function call
- Avoid property updates if value hasn't changed

---

## ?? Debugging

### Enable QML Console Logging
```python
os.environ["QT_LOGGING_RULES"] = "js.debug=true;qt.qml.debug=true"
```

### Check Function Calls
```javascript
// In QML function
function updatePistonPositions(positions) {
 console.log("✅ Received:", JSON.stringify(positions))
 // ... update logic
}
```

### Verify from Python
```python
# Check if function exists
from PySide6.QtCore import QMetaObject
meta = self._qml_root_object.metaObject()
for i in range(meta.methodCount()):
 method = meta.method(i)
 name = method.name().data().decode('utf-8')
 if 'updatePiston' in name:
 print(f"Found method: {name}")
```

---

## ?? References

- GeometryBridge: `src/ui/geometry_bridge.py`
- MainWindow: `src/ui/main_window.py`
- QML Scene: `assets/qml/main.qml`
- CylinderKinematics: `src/mechanics/kinematics.py`

---

## ? Integration Checklist

- [x] QML receives geometry parameters from Python
- [x] QML receives piston positions from Python physics
- [x] QML receives animation parameters from Python
- [x] Python can start/stop animation
- [x] Python can update real-time physics data
- [x] GeometryBridge converts2D kinematics to3D
- [x] Piston positions calculated from CylinderState.stroke
- [ ] QML signals back to Python (future)
- [ ] User interaction events (future)

---

**Status:** ✅ **FULLY INTEGRATED**

Python physics engine ↔ QML3D visualization working!
