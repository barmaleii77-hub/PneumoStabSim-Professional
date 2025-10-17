# 🚀 QML PHASE 2: CAMERA SYSTEM REFACTORING PLAN

## 📋 ЦЕЛЬ

Рефакторинг системы управления камерой из `main.qml` в модульные компоненты.

---

## 📊 ТЕКУЩАЯ РЕАЛИЗАЦИЯ

### Местоположение в main.qml:
- **Строки 331-363**: Camera properties (21 property)
- **Строки 467-480**: Smooth camera behaviors (5 Behavior)
- **Строки 634-685**: Camera functions (4 функции)
- **Строки 1230-1249**: Camera rig Node structure
- **Строки 1455-1513**: Mouse controls (MouseArea)
- **Строки 1532-1543**: Auto-rotation timer

### Компоненты для извлечения:

1. **CameraState.qml** - Управление состоянием камеры
2. **CameraRig.qml** - 3D структура камеры (Node → PerspectiveCamera)
3. **MouseControls.qml** - Обработка мыши
4. **CameraController.qml** - Главный контроллер

---

## 🎯 СТРУКТУРА МОДУЛЕЙ

```
assets/qml/camera/
├── qmldir                      # Registration
├── CameraState.qml             # State management
├── CameraRig.qml               # 3D camera rig
├── MouseControls.qml           # Mouse input handler
└── CameraController.qml        # Main controller (combines all)
```

---

## 📝 ДЕТАЛЬНЫЙ ПЛАН

### 1. **CameraState.qml** - State Management

**Ответственность:**
- Хранение camera properties (distance, yaw, pitch, pan, etc.)
- Smooth behaviors (Behavior on properties)
- Auto-rotation logic
- Camera limits (min/max distance, pitch clamping)

**Properties:**
```qml
// Position
property vector3d pivot
property real distance
property real minDistance: 150
property real maxDistance: 30000

// Rotation
property real yawDeg: 225
property real pitchDeg: -25

// Pan
property real panX: 0
property real panY: 0

// Camera settings
property real fov: 60.0
property real nearPlane: 10.0
property real farPlane: 50000.0
property real speed: 1.0

// Auto-rotation
property bool autoRotate: false
property real autoRotateSpeed: 0.5

// Motion tracking (for TAA)
property bool isMoving: false
property real rotateSpeed: 0.35
```

**Functions:**
```qml
function resetView()
function fullResetView()
function autoFitFrame(frameLength, trackWidth, frameHeight, fov)
function flagMotion()
```

---

### 2. **CameraRig.qml** - 3D Structure

**Ответственность:**
- Node hierarchy (cameraRig → panNode → PerspectiveCamera)
- Binding to CameraState properties
- Parent binding (worldRoot)

**Structure:**
```qml
Node {
    id: cameraRig
    // parent: worldRoot (set by main.qml)
    
    position: cameraState.pivot
    eulerRotation: Qt.vector3d(cameraState.pitchDeg, cameraState.yawDeg, 0)
    
    Node {
        id: panNode
        position: Qt.vector3d(cameraState.panX, cameraState.panY, 0)
        
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraState.distance)
            fieldOfView: cameraState.fov
            clipNear: cameraState.nearPlane
            clipFar: cameraState.farPlane
        }
    }
}
```

---

### 3. **MouseControls.qml** - Input Handler

**Ответственность:**
- MouseArea для всего экрана
- Обработка ЛКМ (rotation), ПКМ (pan), колеса (zoom)
- Delta validation (избежание рывков)
- Keyboard shortcuts (R, F, Space)

**Properties:**
```qml
property var cameraState  // Reference to CameraState
property real viewHeight  // For pan calculation
property bool taaMotionAdaptive: false
property bool mouseDown: false
property int mouseButton: 0
property real lastX: 0
property real lastY: 0
```

**Handlers:**
```qml
onPressed: (mouse) => { /* rotation/pan start */ }
onReleased: (mouse) => { /* end motion */ }
onPositionChanged: (mouse) => { /* update rotation/pan */ }
onWheel: (wheel) => { /* zoom */ }
onDoubleClicked: () => { /* reset view */ }
Keys.onPressed: (e) => { /* R, F, Space */ }
```

---

### 4. **CameraController.qml** - Main Controller

**Ответственность:**
- Объединение всех компонентов
- Public API для main.qml
- Signals для Python↔QML

**Structure:**
```qml
Item {
    id: controller
    
    // Public API
    readonly property alias state: cameraState
    readonly property alias rig: cameraRig
    readonly property alias camera: cameraRig.camera
    
    // Signals
    signal cameraChanged()
    
    // Components
    CameraState { id: cameraState }
    CameraRig { id: cameraRig; cameraState: cameraState }
    MouseControls { id: mouseControls; cameraState: cameraState }
}
```

---

## 🔗 ИНТЕГРАЦИЯ В main.qml

### До (текущее):
```qml
// 21 camera properties
property vector3d pivot: ...
property real cameraDistance: ...
// ...

// Camera rig Node
Node {
    id: cameraRig
    // ...
}

// Mouse controls
MouseArea {
    // ...
}
```

### После (Phase 2):
```qml
import "camera"

// Replace with:
CameraController {
    id: cameraController
    anchors.fill: parent
    
    worldRoot: worldRoot
    taaMotionAdaptive: root.taaMotionAdaptive
    
    onCameraChanged: {
        // Update StateCache
        StateCache.cameraFov = cameraController.state.fov
    }
}

// Access via:
// cameraController.state.distance
// cameraController.camera
```

---

## 📊 МЕТРИКИ

### Code Reduction:
| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Camera properties | 21 lines | 2 lines | -19 lines |
| Camera behaviors | 5 lines | 0 lines | -5 lines |
| Camera functions | 52 lines | 0 lines | -52 lines |
| Camera rig | 20 lines | 2 lines | -18 lines |
| Mouse controls | 59 lines | 0 lines | -59 lines |
| Auto-rotation | 12 lines | 0 lines | -12 lines |
| **TOTAL** | **169 lines** | **4 lines** | **-165 lines** |

### Benefits:
- ✅ **90% code reduction** in main.qml
- ✅ **Reusable** camera system
- ✅ **Testable** modules
- ✅ **Maintainable** structure

---

## 🧪 TESTING PLAN

### Unit Tests:
1. **CameraState**:
   - Property initialization
   - Behaviors (smooth transitions)
   - Limit clamping (pitch, distance)
   - resetView() logic

2. **CameraRig**:
   - Node hierarchy
   - Property bindings
   - Camera frustum

3. **MouseControls**:
   - Mouse input → camera updates
   - Delta validation
   - Keyboard shortcuts

### Integration Tests:
1. **CameraController**:
   - Full camera system workflow
   - Python↔QML integration
   - applyCameraUpdates() function

---

## 📋 IMPLEMENTATION STEPS

### Step 1: Create camera/ directory
```bash
mkdir assets/qml/camera
```

### Step 2: Create qmldir
```qml
module camera
CameraState 1.0 CameraState.qml
CameraRig 1.0 CameraRig.qml
MouseControls 1.0 MouseControls.qml
CameraController 1.0 CameraController.qml
```

### Step 3: Implement modules
1. CameraState.qml (properties + functions)
2. CameraRig.qml (Node hierarchy)
3. MouseControls.qml (input handling)
4. CameraController.qml (integration)

### Step 4: Integrate into main.qml
- Replace camera properties with `CameraController`
- Update references
- Test functionality

### Step 5: Write tests
- Unit tests for each module
- Integration test for full system

---

## 🎯 SUCCESS CRITERIA

- ✅ Camera system fully modular
- ✅ All functionality preserved
- ✅ main.qml reduced by ~165 lines
- ✅ Tests pass (100%)
- ✅ No visual regressions
- ✅ Python↔QML bridge works

---

## 📝 NOTES

### Critical Design Decisions:

1. **CameraState as QtObject (not Item)**
   - Lightweight, pure state management
   - No visual component needed

2. **CameraRig as Node**
   - Must be part of Qt Quick 3D scene graph
   - Parent set by main.qml (worldRoot)

3. **MouseControls as Item**
   - Needs anchors.fill: parent
   - Handles input over entire viewport

4. **CameraController as composite**
   - Public API layer
   - Combines all subcomponents

---

## 🚀 READY TO START

**Current Status:** Plan Complete  
**Next Step:** Implement CameraState.qml

**Estimated Time:**
- Implementation: 2-3 hours
- Testing: 1 hour
- Integration: 30 minutes
- **Total: 3.5-4.5 hours**

---

**Date:** 2025-01-17  
**Phase:** 2 of 5  
**Status:** PLANNING COMPLETE

