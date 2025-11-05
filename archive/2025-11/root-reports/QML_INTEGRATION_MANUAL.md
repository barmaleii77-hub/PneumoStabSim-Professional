# 🚀 INTEGRATION STEP-BY-STEP GUIDE

## ШАГ 1: Добавьте импорты (строки 1-12)

```qml
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick.Controls
import Qt.labs.folderlistmodel
import "components"
import "core"
import "camera"
import "lighting"   // ✅ NEW
import "effects"    // ✅ NEW
import "scene"      // ✅ NEW
import "geometry"   // ✅ NEW
```

---

## ШАГ 2: Замените ExtendedSceneEnvironment (строка ~900)

**Найдите блок:**
```qml
environment: ExtendedSceneEnvironment {
    id: mainEnvironment
    // ... 150+ строк параметров
}
```

**Замените на:**
```qml
import "effects"

environment: SceneEnvironmentController {
    id: mainEnvironment

    // Background & IBL
    iblBackgroundEnabled: root.iblBackgroundEnabled
    iblLightingEnabled: root.iblLightingEnabled
    backgroundColor: root.backgroundColor
    iblProbe: iblLoader.probe
    iblIntensity: root.iblIntensity
    iblRotationDeg: root.iblRotationDeg

    // AA
    aaPrimaryMode: root.aaPrimaryMode
    aaQualityLevel: root.aaQualityLevel
    aaPostMode: root.aaPostMode
    taaEnabled: root.taaEnabled
    taaStrength: root.taaStrength
    taaMotionAdaptive: root.taaMotionAdaptive
    fxaaEnabled: root.fxaaEnabled
    specularAAEnabled: root.specularAAEnabled
    cameraIsMoving: root.cameraIsMoving

    // Dithering
    ditheringEnabled: root.ditheringEnabled
    canUseDithering: root.canUseDithering

    // Fog
    fogEnabled: root.fogEnabled
    fogColor: root.fogColor
    fogDensity: root.fogDensity
    fogNear: root.fogNear
    fogFar: root.fogFar

    // Tonemap
    tonemapEnabled: root.tonemapEnabled
    tonemapModeName: root.tonemapModeName
    tonemapExposure: root.tonemapExposure
    tonemapWhitePoint: root.tonemapWhitePoint

    // Bloom
    bloomEnabled: root.bloomEnabled
    bloomIntensity: root.bloomIntensity
    bloomThreshold: root.bloomThreshold
    bloomSpread: root.bloomSpread

    // SSAO
    ssaoEnabled: root.ssaoEnabled
    ssaoRadius: root.ssaoRadius
    ssaoIntensity: root.ssaoIntensity

    // DOF
    depthOfFieldEnabled: root.depthOfFieldEnabled
    dofFocusDistance: root.dofFocusDistance
    dofBlurAmount: root.dofBlurAmount

    // Vignette
    vignetteEnabled: root.vignetteEnabled
    vignetteStrength: root.vignetteStrength

    // Lens Flare
    lensFlareEnabled: root.lensFlareEnabled

    // OIT
    oitMode: root.oitMode
}
```

---

## ШАГ 3: Добавьте SharedMaterials (после Node { id: worldRoot })

**После строки:**
```qml
Node {
    id: worldRoot
}
```

**Добавьте:**
```qml
// ✅ SHARED MATERIALS (replaces 200+ lines of inline PrincipledMaterial)
SharedMaterials {
    id: sharedMaterials

    // Bind все root properties
    frameBaseColor: root.frameBaseColor
    frameMetalness: root.frameMetalness
    frameRoughness: root.frameRoughness
    frameSpecularAmount: root.frameSpecularAmount
    frameSpecularTint: root.frameSpecularTint
    frameClearcoat: root.frameClearcoat
    frameClearcoatRoughness: root.frameClearcoatRoughness
    frameTransmission: root.frameTransmission
    frameOpacity: root.frameOpacity
    frameIor: root.frameIor
    frameAttenuationDistance: root.frameAttenuationDistance
    frameAttenuationColor: root.frameAttenuationColor
    frameEmissiveColor: root.frameEmissiveColor
    frameEmissiveIntensity: root.frameEmissiveIntensity

    // Lever
    leverBaseColor: root.leverBaseColor
    leverMetalness: root.leverMetalness
    leverRoughness: root.leverRoughness
    leverSpecularAmount: root.leverSpecularAmount
    leverSpecularTint: root.leverSpecularTint
    leverClearcoat: root.leverClearcoat
    leverClearcoatRoughness: root.leverClearcoatRoughness
    leverTransmission: root.leverTransmission
    leverOpacity: root.leverOpacity
    leverIor: root.leverIor
    leverAttenuationDistance: root.leverAttenuationDistance
    leverAttenuationColor: root.leverAttenuationColor
    leverEmissiveColor: root.leverEmissiveColor
    leverEmissiveIntensity: root.leverEmissiveIntensity

    // TailRod
    tailRodBaseColor: root.tailRodBaseColor
    tailRodMetalness: root.tailRodMetalness
    tailRodRoughness: root.tailRodRoughness
    tailRodSpecularAmount: root.tailRodSpecularAmount
    tailRodSpecularTint: root.tailRodSpecularTint
    tailRodClearcoat: root.tailRodClearcoat
    tailRodClearcoatRoughness: root.tailRodClearcoatRoughness
    tailRodTransmission: root.tailRodTransmission
    tailRodOpacity: root.tailRodOpacity
    tailRodIor: root.tailRodIor
    tailRodAttenuationDistance: root.tailRodAttenuationDistance
    tailRodAttenuationColor: root.tailRodAttenuationColor
    tailRodEmissiveColor: root.tailRodEmissiveColor
    tailRodEmissiveIntensity: root.tailRodEmissiveIntensity

    // Cylinder
    cylinderBaseColor: root.cylinderBaseColor
    cylinderMetalness: root.cylinderMetalness
    cylinderRoughness: root.cylinderRoughness
    cylinderSpecularAmount: root.cylinderSpecularAmount
    cylinderSpecularTint: root.cylinderSpecularTint
    cylinderClearcoat: root.cylinderClearcoat
    cylinderClearcoatRoughness: root.cylinderClearcoatRoughness
    cylinderTransmission: root.cylinderTransmission
    cylinderOpacity: root.cylinderOpacity
    cylinderIor: root.cylinderIor
    cylinderAttenuationDistance: root.cylinderAttenuationDistance
    cylinderAttenuationColor: root.cylinderAttenuationColor
    cylinderEmissiveColor: root.cylinderEmissiveColor
    cylinderEmissiveIntensity: root.cylinderEmissiveIntensity

    // JointTail
    jointTailBaseColor: root.jointTailBaseColor
    jointTailMetalness: root.jointTailMetalness
    jointTailRoughness: root.jointTailRoughness
    jointTailSpecularAmount: root.jointTailSpecularAmount
    jointTailSpecularTint: root.jointTailSpecularTint
    jointTailClearcoat: root.jointTailClearcoat
    jointTailClearcoatRoughness: root.jointTailClearcoatRoughness
    jointTailTransmission: root.jointTailTransmission
    jointTailOpacity: root.jointTailOpacity
    jointTailIor: root.jointTailIor
    jointTailAttenuationDistance: root.jointTailAttenuationDistance
    jointTailAttenuationColor: root.jointTailAttenuationColor
    jointTailEmissiveColor: root.jointTailEmissiveColor
    jointTailEmissiveIntensity: root.jointTailEmissiveIntensity

    // JointArm
    jointArmBaseColor: root.jointArmBaseColor
    jointArmMetalness: root.jointArmMetalness
    jointArmRoughness: root.jointArmRoughness
    jointArmSpecularAmount: root.jointArmSpecularAmount
    jointArmSpecularTint: root.jointArmSpecularTint
    jointArmClearcoat: root.jointArmClearcoat
    jointArmClearcoatRoughness: root.jointArmClearcoatRoughness
    jointArmTransmission: root.jointArmTransmission
    jointArmOpacity: root.jointArmOpacity
    jointArmIor: root.jointArmIor
    jointArmAttenuationDistance: root.jointArmAttenuationDistance
    jointArmAttenuationColor: root.jointArmAttenuationColor
    jointArmEmissiveColor: root.jointArmEmissiveColor
    jointArmEmissiveIntensity: root.jointArmEmissiveIntensity
}
```

---

## ШАГ 4: УДАЛИТЕ старые inline PrincipledMaterial (строки ~1100-1300)

**Удалите весь блок:**
```qml
PrincipledMaterial {
    id: frameMaterial
    // ... 15 строк
}

PrincipledMaterial {
    id: leverMaterial
    // ... 15 строк
}

// + ещё 4 материала
```

**Они больше не нужны** - используем `sharedMaterials`!

---

## ШАГ 5: Замените освещение (строки ~1400-1500)

**Найдите блок:**
```qml
DirectionalLight {
    id: keyLight
    // ... 15 параметров
}
DirectionalLight {
    id: fillLight
    // ... 10 параметров
}
DirectionalLight {
    id: rimLight
    // ... 10 параметров
}
PointLight {
    id: accentLight
    // ... 8 параметров
}
```

**Замените на:**
```qml
// ✅ MODULAR LIGHTING (replaces 4 inline Light components)
DirectionalLights {
    worldRoot: worldRoot
    cameraRig: cameraController.rig
    shadowsEnabled: root.shadowsEnabled
    shadowResolution: root.shadowResolution
    shadowFilterSamples: root.shadowFilterSamples
    shadowBias: root.shadowBias
    shadowFactor: root.shadowFactor
    keyLightBrightness: root.keyLightBrightness
    keyLightColor: root.keyLightColor
    keyLightAngleX: root.keyLightAngleX
    keyLightAngleY: root.keyLightAngleY
    keyLightCastsShadow: root.keyLightCastsShadow
    keyLightBindToCamera: root.keyLightBindToCamera
    keyLightPosX: root.keyLightPosX
    keyLightPosY: root.keyLightPosY
    fillLightBrightness: root.fillLightBrightness
    fillLightColor: root.fillLightColor
    fillLightCastsShadow: root.fillLightCastsShadow
    fillLightBindToCamera: root.fillLightBindToCamera
    fillLightPosX: root.fillLightPosX
    fillLightPosY: root.fillLightPosY
    rimLightBrightness: root.rimLightBrightness
    rimLightColor: root.rimLightColor
    rimLightCastsShadow: root.rimLightCastsShadow
    rimLightBindToCamera: root.rimLightBindToCamera
    rimLightPosX: root.rimLightPosX
    rimLightPosY: root.rimLightPosY
}

PointLights {
    worldRoot: worldRoot
    cameraRig: cameraController.rig
    pointLightBrightness: root.pointLightBrightness
    pointLightColor: root.pointLightColor
    pointLightX: root.pointLightX
    pointLightY: root.pointLightY
    pointLightRange: root.pointLightRange
    pointLightCastsShadow: root.pointLightCastsShadow
    pointLightBindToCamera: root.pointLightBindToCamera
}
```

---

## ШАГ 6: Замените U-Frame (строки ~1550-1570)

**Найдите блок:**
```qml
// U-FRAME (3 beams) with controlled materials
Model {
    parent: worldRoot
    source: "#Cube"
    position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
    scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
    materials: [frameMaterial]
}
Model {
    parent: worldRoot
    source: "#Cube"
    position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
    scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
    materials: [frameMaterial]
}
Model {
    parent: worldRoot
    source: "#Cube"
    position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
    scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
    materials: [frameMaterial]
}
```

**Замените на:**
```qml
// ✅ MODULAR FRAME (replaces 3 inline Model components)
Frame {
    worldRoot: worldRoot
    beamSize: root.userBeamSize
    frameHeight: root.userFrameHeight
    frameLength: root.userFrameLength
    frameMaterial: sharedMaterials.frameMaterial
}
```

---

## ШАГ 7: Замените подвеску (строки ~1580-1800)

**Найдите блок:**
```qml
component OptimizedSuspensionCorner: Node {
    // ... 100+ строк кинематики
    // ... 15 Model компонентов
}

OptimizedSuspensionCorner {
    id: flCorner
    // ...
}
// + ещё 3 угла
```

**Замените на:**
```qml
// ✅ MODULAR SUSPENSION (replaces component definition + 4 instances)
SuspensionCorner {
    id: flCorner
    parent: worldRoot
    j_arm: Qt.vector3d(-root.userFrameToPivot, root.userBeamSize, root.userBeamSize/2)
    j_tail: Qt.vector3d(-root.userTrackWidth/2, root.userBeamSize + root.userFrameHeight, root.userBeamSize/2)
    leverAngle: root.fl_angle
    pistonPositionFromPython: root.userPistonPositionFL

    // Geometry
    userLeverLength: root.userLeverLength
    userRodPosition: root.userRodPosition
    userCylinderLength: root.userCylinderLength
    userBoreHead: root.userBoreHead
    userRodDiameter: root.userRodDiameter
    userPistonThickness: root.userPistonThickness
    userPistonRodLength: root.userPistonRodLength

    // Quality
    cylinderSegments: root.cylinderSegments
    cylinderRings: root.cylinderRings

    // Materials
    sharedMaterials: sharedMaterials
    pistonBodyBaseColor: root.pistonBodyBaseColor
    pistonBodyWarningColor: root.pistonBodyWarningColor
    pistonRodBaseColor: root.pistonRodBaseColor
    pistonRodWarningColor: root.pistonRodWarningColor
    jointRodOkColor: root.jointRodOkColor
    jointRodErrorColor: root.jointRodErrorColor
}

SuspensionCorner {
    id: frCorner
    parent: worldRoot
    j_arm: Qt.vector3d(root.userFrameToPivot, root.userBeamSize, root.userBeamSize/2)
    j_tail: Qt.vector3d(root.userTrackWidth/2, root.userBeamSize + root.userFrameHeight, root.userBeamSize/2)
    leverAngle: root.fr_angle
    pistonPositionFromPython: root.userPistonPositionFR

    // Same parameters as FL
    userLeverLength: root.userLeverLength
    userRodPosition: root.userRodPosition
    userCylinderLength: root.userCylinderLength
    userBoreHead: root.userBoreHead
    userRodDiameter: root.userRodDiameter
    userPistonThickness: root.userPistonThickness
    userPistonRodLength: root.userPistonRodLength
    cylinderSegments: root.cylinderSegments
    cylinderRings: root.cylinderRings
    sharedMaterials: sharedMaterials
    pistonBodyBaseColor: root.pistonBodyBaseColor
    pistonBodyWarningColor: root.pistonBodyWarningColor
    pistonRodBaseColor: root.pistonRodBaseColor
    pistonRodWarningColor: root.pistonRodWarningColor
    jointRodOkColor: root.jointRodOkColor
    jointRodErrorColor: root.jointRodErrorColor
}

SuspensionCorner {
    id: rlCorner
    parent: worldRoot
    j_arm: Qt.vector3d(-root.userFrameToPivot, root.userBeamSize, root.userFrameLength - root.userBeamSize/2)
    j_tail: Qt.vector3d(-root.userTrackWidth/2, root.userBeamSize + root.userFrameHeight, root.userFrameLength - root.userBeamSize/2)
    leverAngle: root.rl_angle
    pistonPositionFromPython: root.userPistonPositionRL

    userLeverLength: root.userLeverLength
    userRodPosition: root.userRodPosition
    userCylinderLength: root.userCylinderLength
    userBoreHead: root.userBoreHead
    userRodDiameter: root.userRodDiameter
    userPistonThickness: root.userPistonThickness
    userPistonRodLength: root.userPistonRodLength
    cylinderSegments: root.cylinderSegments
    cylinderRings: root.cylinderRings
    sharedMaterials: sharedMaterials
    pistonBodyBaseColor: root.pistonBodyBaseColor
    pistonBodyWarningColor: root.pistonBodyWarningColor
    pistonRodBaseColor: root.pistonRodBaseColor
    pistonRodWarningColor: root.pistonRodWarningColor
    jointRodOkColor: root.jointRodOkColor
    jointRodErrorColor: root.jointRodErrorColor
}

SuspensionCorner {
    id: rrCorner
    parent: worldRoot
    j_arm: Qt.vector3d(root.userFrameToPivot, root.userBeamSize, root.userFrameLength - root.userBeamSize/2)
    j_tail: Qt.vector3d(root.userTrackWidth/2, root.userBeamSize + root.userFrameHeight, root.userFrameLength - root.userBeamSize/2)
    leverAngle: root.rr_angle
    pistonPositionFromPython: root.userPistonPositionRR

    userLeverLength: root.userLeverLength
    userRodPosition: root.userRodPosition
    userCylinderLength: root.userCylinderLength
    userBoreHead: root.userBoreHead
    userRodDiameter: root.userRodDiameter
    userPistonThickness: root.userPistonThickness
    userPistonRodLength: root.userPistonRodLength
    cylinderSegments: root.cylinderSegments
    cylinderRings: root.cylinderRings
    sharedMaterials: sharedMaterials
    pistonBodyBaseColor: root.pistonBodyBaseColor
    pistonBodyWarningColor: root.pistonBodyWarningColor
    pistonRodBaseColor: root.pistonRodBaseColor
    pistonRodWarningColor: root.pistonRodWarningColor
    jointRodOkColor: root.jointRodOkColor
    jointRodErrorColor: root.jointRodErrorColor
}
```

---

## ✅ РЕЗУЛЬТАТ

**После всех изменений:**
- **-1050 строк** удалённого inline кода
- **+600 строк** модульных компонентов
- **Чистый выигрыш:** -450 строк + модульность!

---

## 📝 ТЕСТИРОВАНИЕ

```bash
python app.py
```

**Ожидаем в консоли:**
```
💡 DirectionalLights initialized
💡 PointLights initialized
🏗️ Frame initialized
🔧 SuspensionCorner initialized (x4)
```

---

**Если всё работает - ГОТОВО! 🎉**
