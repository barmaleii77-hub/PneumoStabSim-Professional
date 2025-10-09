import QtQuick
import QtQuick3D
import QtQuick3D.Helpers  // ИСПРАВЛЕНО: Правильный импорт для ExtendedSceneEnvironment

/*
 * PneumoStabSim - Main 3D View (Enhanced Realism v2.1)
 * ИСПРАВЛЕНО: ExtendedSceneEnvironment с Qt 6.9.3 совместимостью
 * УЛУЧШЕНО: Орбитальная камера с фиксированным pivot в центре нижней балки
 */
Item {
    id: root
    anchors.fill: parent

    // ===============================================================
    // CAMERA SYSTEM - Improved Orbital Camera with Fixed Pivot
    // ===============================================================
    
    // Фиксированный pivot - всегда центр нижней балки рамы
    property vector3d pivot: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
    
    // Camera orbital parameters
    property real cameraDistance: 3500
    property real minDistance: 150
    property real maxDistance: 30000
    property real yawDeg: 225            // Стартовый вид "сзади-слева-сверху"
    property real pitchDeg: -25
    
    // Camera panning in rig local space (NOT moving pivot)
    property real panX: 0
    property real panY: 0
    
    // Camera properties
    property real cameraFov: 50.0
    property real cameraNear: 2.0
    property real cameraFar: 50000.0
    property real cameraSpeed: 1.0
    
    // Auto rotation
    property bool autoRotate: false
    property real autoRotateSpeed: 0.5

    // Mouse input state
    property bool mouseDown: false
    property int mouseButton: 0
    property real lastX: 0
    property real lastY: 0
    property real rotateSpeed: 0.35

    // ===============================================================
    // ENHANCED GRAPHICS PROPERTIES
    // ===============================================================
    
    // Environment
    property string backgroundColor: "#2a2a2a"
    property bool skyboxEnabled: true
    property bool iblEnabled: true
    property real iblIntensity: 1.0
    
    // Quality settings  
    property int antialiasingMode: 2     // 0=None, 1=SSAA, 2=MSAA, 3=Progressive
    property int antialiasingQuality: 2  // 0=Low, 1=Medium, 2=High
    property bool shadowsEnabled: true
    property int shadowQuality: 2        // 0=Low, 1=Medium, 2=High
    property real shadowSoftness: 0.5
    
    // Post-processing effects
    property bool bloomEnabled: true
    property real bloomThreshold: 1.0
    property real bloomIntensity: 0.8
    property bool ssaoEnabled: true
    property real ssaoRadius: 8.0
    property real ssaoIntensity: 0.6
    property bool tonemapEnabled: true
    property int tonemapMode: 3          // 0=None, 1=Linear, 2=Reinhard, 3=Filmic
    
    // Advanced effects
    property bool depthOfFieldEnabled: false
    property real dofFocusDistance: 2000
    property real dofFocusRange: 900
    property bool lensFlareEnabled: true
    property bool vignetteEnabled: true
    property real vignetteStrength: 0.45
    
    // Lighting control properties
    property real keyLightBrightness: 2.8
    property string keyLightColor: "#ffffff"
    property real keyLightAngleX: -30
    property real keyLightAngleY: -45
    property real fillLightBrightness: 1.2
    property string fillLightColor: "#f0f0ff"
    property real pointLightBrightness: 20000
    property real pointLightY: 1800

    // Material control properties
    property real metalRoughness: 0.28
    property real metalMetalness: 1.0
    property real metalClearcoat: 0.25
    property real glassOpacity: 0.35
    property real glassRoughness: 0.05
    property real frameMetalness: 0.8
    property real frameRoughness: 0.4

    // ===============================================================
    // ANIMATION AND GEOMETRY PROPERTIES
    // ===============================================================
    
    property real animationTime: 0.0
    property bool isRunning: false

    // User-controlled animation parameters
    property real userAmplitude: 8.0
    property real userFrequency: 1.0
    property real userPhaseGlobal: 0.0
    property real userPhaseFL: 0.0
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0

    // Piston positions from Python
    property real userPistonPositionFL: 250.0
    property real userPistonPositionFR: 250.0
    property real userPistonPositionRL: 250.0
    property real userPistonPositionRR: 250.0

    // Calculated angles for each corner
    property real fl_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseFL) * Math.PI / 180) : 0.0
    property real fr_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseFR) * Math.PI / 180) : 0.0
    property real rl_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseRL) * Math.PI / 180) : 0.0
    property real rr_angle: isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseRR) * Math.PI / 180) : 0.0

    // Geometry parameters
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 3200
    property real userLeverLength: 800
    property real userCylinderLength: 500
    property real userTrackWidth: 1600
    property real userFrameToPivot: 600
    property real userRodPosition: 0.6
    property real userBoreHead: 80
    property real userBoreRod: 80
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200

    // ===============================================================
    // SMOOTH CAMERA BEHAVIORS
    // ===============================================================
    
    Behavior on yawDeg         { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on pitchDeg       { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on cameraDistance { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on panX           { NumberAnimation { duration: 60; easing.type: Easing.OutQuad } }
    Behavior on panY           { NumberAnimation { duration: 60; easing.type: Easing.OutQuad } }

    // ===============================================================
    // UTILITY FUNCTIONS
    // ===============================================================
    
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    
    function normAngleDeg(a) {
        var x = a % 360;
        if (x > 180) x -= 360;
        if (x < -180) x += 360;
        return x;
    }
    
    // Auto-fit frame to view with margin
    function autoFitFrame(marginFactor) {
        const L = Math.max(1, userFrameLength)
        const T = Math.max(1, userTrackWidth)  
        const H = Math.max(1, userFrameHeight)
        const margin = marginFactor !== undefined ? marginFactor : 1.15
        const R = 0.5 * Math.sqrt(L*L + T*T + H*H)
        const fov = cameraFov * Math.PI / 180.0
        const dist = (R * margin) / Math.tan(fov * 0.5)
        cameraDistance = Math.max(minDistance, Math.min(maxDistance, dist))
    }
    
    // Reset view to optimal position
    function resetView() {
        // Reset pivot to center of bottom frame beam
        pivot = Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
        
        // Reset camera position
        yawDeg = 225      // "Behind-left-above" view
        pitchDeg = -25
        panX = 0
        panY = 0
        
        // Auto-fit to frame
        autoFitFrame()
        
        console.log("🔄 View reset: pivot =", pivot, "distance =", cameraDistance)
    }

    // ===============================================================
    // UPDATE FUNCTIONS FOR PYTHON INTEGRATION
    // ===============================================================
    
    function updateGeometry(params) {
        console.log("🔧 main.qml: updateGeometry() called")
        console.log("🔧 Received params:", JSON.stringify(params))
        
        // Update frame dimensions
        if (params.frameLength !== undefined) {
            userFrameLength = params.frameLength
        }
        if (params.frameHeight !== undefined) {
            userFrameHeight = params.frameHeight
        }
        if (params.frameBeamSize !== undefined) {
            userBeamSize = params.frameBeamSize
        }
        
        // Update suspension geometry
        if (params.leverLength !== undefined) {
            userLeverLength = params.leverLength
        }
        if (params.cylinderBodyLength !== undefined) {
            userCylinderLength = params.cylinderBodyLength
        }
        if (params.trackWidth !== undefined) {
            userTrackWidth = params.trackWidth
        }
        if (params.frameToPivot !== undefined) {
            userFrameToPivot = params.frameToPivot
        }
        if (params.rodPosition !== undefined) {
            console.log("  🔧 ✨ Setting userRodPosition:", params.rodPosition, "- КРИТИЧЕСКИЙ ПАРАМЕТР!")
            userRodPosition = params.rodPosition
        }
        
        // Update cylinder parameters (compatibility)
        if (params.cylDiamM !== undefined) {
            userBoreHead = params.cylDiamM
            userBoreRod = params.cylDiamM
        }
        if (params.rodDiameterM !== undefined) {
            userRodDiameter = params.rodDiameterM
        }
        if (params.pistonRodLengthM !== undefined) {
            userPistonRodLength = params.pistonRodLengthM
        }
        if (params.pistonThicknessM !== undefined) {
            userPistonThickness = params.pistonThicknessM
        }
        
        // Reset view to new geometry
        resetView()
        console.log("  ✅ Geometry updated and view reset")
    }
    
    // ИСПРАВЛЕНО: Функции обновления графики с правильными параметрами
    function updateLighting(params) {
        console.log("💡 main.qml: updateLighting() called")
        
        if (params.key_light !== undefined) {
            if (params.key_light.brightness !== undefined) {
                keyLightBrightness = params.key_light.brightness
            }
            if (params.key_light.color !== undefined) {
                keyLightColor = params.key_light.color
            }
            if (params.key_light.angle_x !== undefined) {
                keyLightAngleX = params.key_light.angle_x
            }
            if (params.key_light.angle_y !== undefined) {
                keyLightAngleY = params.key_light.angle_y
            }
        }
        
        if (params.fill_light !== undefined) {
            if (params.fill_light.brightness !== undefined) {
                fillLightBrightness = params.fill_light.brightness
            }
            if (params.fill_light.color !== undefined) {
                fillLightColor = params.fill_light.color
            }
        }
        
        if (params.point_light !== undefined) {
            if (params.point_light.brightness !== undefined) {
                pointLightBrightness = params.point_light.brightness
            }
            if (params.point_light.position_y !== undefined) {
                pointLightY = params.point_light.position_y
            }
        }
        
        console.log("  ✅ Lighting updated successfully")
    }
    
    function updateMaterials(params) {
        console.log("🎨 main.qml: updateMaterials() called")
        
        if (params.metal !== undefined) {
            if (params.metal.roughness !== undefined) {
                metalRoughness = params.metal.roughness
            }
            if (params.metal.metalness !== undefined) {
                metalMetalness = params.metal.metalness
            }
            if (params.metal.clearcoat !== undefined) {
                metalClearcoat = params.metal.clearcoat
            }
        }
        
        if (params.glass !== undefined) {
            if (params.glass.opacity !== undefined) {
                glassOpacity = params.glass.opacity
            }
            if (params.glass.roughness !== undefined) {
                glassRoughness = params.glass.roughness
            }
        }
        
        if (params.frame !== undefined) {
            if (params.frame.metalness !== undefined) {
                frameMetalness = params.frame.metalness
            }
            if (params.frame.roughness !== undefined) {
                frameRoughness = params.frame.roughness
            }
        }
        
        console.log("  ✅ Materials updated successfully")
    }
    
    function updateEnvironment(params) {
        console.log("🌍 main.qml: updateEnvironment() called")
        
        if (params.background_color !== undefined) {
            backgroundColor = params.background_color
        }
        if (params.skybox_enabled !== undefined) {
            skyboxEnabled = params.skybox_enabled
        }
        
        console.log("  ✅ Environment updated successfully")
    }
    
    function updateQuality(params) {
        console.log("⚙️ main.qml: updateQuality() called")
        
        if (params.antialiasing !== undefined) {
            antialiasingMode = params.antialiasing
        }
        if (params.aa_quality !== undefined) {
            antialiasingQuality = params.aa_quality
        }
        if (params.shadows_enabled !== undefined) {
            shadowsEnabled = params.shadows_enabled
        }
        
        console.log("  ✅ Quality settings updated successfully")
    }
    
    function updateEffects(params) {
        console.log("✨ main.qml: updateEffects() called")
        
        if (params.bloom_enabled !== undefined) {
            bloomEnabled = params.bloom_enabled
        }
        if (params.bloom_intensity !== undefined) {
            bloomIntensity = params.bloom_intensity
        }
        if (params.ssao_enabled !== undefined) {
            ssaoEnabled = params.ssao_enabled
        }
        if (params.ssao_intensity !== undefined) {
            ssaoIntensity = params.ssao_intensity
        }
        if (params.depth_of_field !== undefined) {
            depthOfFieldEnabled = params.depth_of_field
        }
        
        console.log("  ✅ Visual effects updated successfully")
    }
    
    function updateCamera(params) {
        console.log("📷 main.qml: updateCamera() called")
        
        if (params.fov !== undefined) {
            cameraFov = params.fov
        }
        if (params.near !== undefined) {
            cameraNear = params.near
        }
        if (params.far !== undefined) {
            cameraFar = params.far
        }
        if (params.speed !== undefined) {
            cameraSpeed = params.speed
        }
        if (params.auto_rotate !== undefined) {
            autoRotate = params.auto_rotate
        }
        if (params.auto_rotate_speed !== undefined) {
            autoRotateSpeed = params.auto_rotate_speed
        }
        
        console.log("  ✅ Camera settings updated successfully")
    }
    
    function updatePistonPositions(positions) {
        // Update piston positions from Python physics engine
        if (positions.fl !== undefined) {
            userPistonPositionFL = Number(positions.fl)
        }
        if (positions.fr !== undefined) {
            userPistonPositionFR = Number(positions.fr)
        }
        if (positions.rl !== undefined) {
            userPistonPositionRL = Number(positions.rl)
        }
        if (positions.rr !== undefined) {
            userPistonPositionRR = Number(positions.rr)
        }
    }

    // ===============================================================
    // 3D SCENE
    // ===============================================================

    View3D {
        id: view3d
        anchors.fill: parent

        // ИСПРАВЛЕНО: ExtendedSceneEnvironment с Qt 6.9.3 совместимостью
        environment: ExtendedSceneEnvironment {
            // Background and IBL
            backgroundMode: skyboxEnabled ? SceneEnvironment.SkyBox : SceneEnvironment.Color
            clearColor: backgroundColor
            
            // ИСПРАВЛЕНО: Условное использование lightProbe
            lightProbe: iblEnabled ? null : null  // Пока отключаем IBL для совместимости
            probeExposure: iblIntensity
            
            // ИСПРАВЛЕНО: Правильные enum значения для тонемаппинга
            tonemapMode: tonemapEnabled ? 
                (tonemapMode === 3 ? SceneEnvironment.TonemapModeFilmic :
                 tonemapMode === 2 ? SceneEnvironment.TonemapModeReinhard :
                 tonemapMode === 1 ? SceneEnvironment.TonemapModeLinear :
                 SceneEnvironment.TonemapModeNone) : SceneEnvironment.TonemapModeNone
            exposure: 1.0
            whitePoint: 2.0
            
            // Quality settings
            antialiasingMode: antialiasingMode === 3 ? SceneEnvironment.ProgressiveAA :
                             antialiasingMode === 2 ? SceneEnvironment.MSAA :
                             antialiasingMode === 1 ? SceneEnvironment.SSAA :
                             SceneEnvironment.NoAA
            antialiasingQuality: antialiasingQuality === 2 ? SceneEnvironment.High :
                                antialiasingQuality === 1 ? SceneEnvironment.Medium :
                                SceneEnvironment.Low
            
            specularAAEnabled: true
            ditheringEnabled: true
            fxaaEnabled: true
            temporalAAEnabled: isRunning  // TAA only during animation
            
            // SSAO settings
            aoEnabled: ssaoEnabled
            aoStrength: ssaoIntensity * 100  // Convert to 0-100 range
            aoDistance: ssaoRadius
            aoSoftness: 20
            aoDither: true
            aoSampleRate: 3
            
            // ИСПРАВЛЕНО: Bloom/Glow настройки для ExtendedSceneEnvironment
            glowEnabled: bloomEnabled
            glowIntensity: bloomIntensity
            glowBloom: 0.5
            glowStrength: 0.8
            glowQualityHigh: true
            glowUseBicubicUpscale: true
            glowHDRMinimumValue: bloomThreshold
            glowHDRMaximumValue: 8.0
            glowHDRScale: 2.0
            
            // Lens flare
            lensFlareEnabled: lensFlareEnabled
            lensFlareGhostCount: 3
            lensFlareGhostDispersal: 0.6
            lensFlareHaloWidth: 0.25
            lensFlareBloomBias: 0.35
            lensFlareStretchToAspect: 1.0
            
            // Depth of Field
            depthOfFieldEnabled: depthOfFieldEnabled
            depthOfFieldFocusDistance: dofFocusDistance
            depthOfFieldFocusRange: dofFocusRange
            depthOfFieldBlurAmount: 3.0
            
            // Vignette
            vignetteEnabled: vignetteEnabled
            vignetteRadius: 0.4
            vignetteStrength: vignetteStrength
            
            // Color adjustments
            colorAdjustmentsEnabled: true
            adjustmentBrightness: 1.0
            adjustmentContrast: 1.05
            adjustmentSaturation: 1.05
        }

        // УЛУЧШЕНО: Орбитальная камера с фиксированным pivot
        Node {
            id: cameraRig
            position: root.pivot  // Всегда центр нижней балки рамы
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            // Узел для панорамирования в локальной системе rig
            Node {
                id: panNode
                position: Qt.vector3d(root.panX, root.panY, 0)

                PerspectiveCamera {
                    id: camera
                    position: Qt.vector3d(0, 0, root.cameraDistance)
                    fieldOfView: root.cameraFov
                    clipNear: root.cameraNear
                    clipFar: root.cameraFar
                }
            }
        }

        // УЛУЧШЕНО: Освещение с управляемыми параметрами
        DirectionalLight {
            id: keyLight
            eulerRotation.x: keyLightAngleX
            eulerRotation.y: keyLightAngleY
            brightness: keyLightBrightness
            color: keyLightColor
            castsShadow: shadowsEnabled
            shadowMapQuality: shadowQuality === 2 ? Light.ShadowMapQualityHigh :
                             shadowQuality === 1 ? Light.ShadowMapQualityMedium :
                             Light.ShadowMapQualityLow
            shadowFactor: 75
            shadowBias: shadowSoftness * 0.001
        }
        
        DirectionalLight {
            id: fillLight
            eulerRotation.x: -60
            eulerRotation.y: 135
            brightness: fillLightBrightness
            color: fillLightColor
            castsShadow: false
        }
        
        DirectionalLight {
            id: rimLight
            eulerRotation.x: 15
            eulerRotation.y: 180
            brightness: 1.5
            color: "#ffffcc"
            castsShadow: false
        }
        
        PointLight {
            id: accentLight
            position: Qt.vector3d(0, pointLightY, 1500)
            brightness: pointLightBrightness
            color: "#ffffff"
            quadraticFade: 0.00008
        }

        // ===============================================================
        // SUSPENSION SYSTEM GEOMETRY
        // ===============================================================

        // U-FRAME (3 beams) with controlled materials
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: frameMetalness
                roughness: frameRoughness
            }
        }

        // SUSPENSION COMPONENT
        component SuspensionCorner: Node {
            property vector3d j_arm
            property vector3d j_tail  
            property real leverAngle
            property real pistonPositionFromPython: 250.0
            
            property real baseAngle: (j_arm.x < 0) ? 180 : 0
            property real totalAngle: baseAngle + leverAngle
            
            property vector3d j_rod: Qt.vector3d(
                j_arm.x + (userLeverLength * userRodPosition) * Math.cos(totalAngle * Math.PI / 180),
                j_arm.y + (userLeverLength * userRodPosition) * Math.sin(totalAngle * Math.PI / 180),
                j_arm.z
            )
            
            // Cylinder geometry calculations
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
            property vector3d cylDirectionNorm: Qt.vector3d(
                cylDirection.x / cylDirectionLength,
                cylDirection.y / cylDirectionLength,
                0
            )
            
            property real lTailRod: 100
            property real lCylinder: userCylinderLength
            
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirectionNorm.x * lTailRod,
                j_tail.y + cylDirectionNorm.y * lTailRod,
                j_tail.z
            )
            
            property vector3d cylinderEnd: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * lCylinder,
                tailRodEnd.y + cylDirectionNorm.y * lCylinder,
                tailRodEnd.z
            )
            
            // Piston positioning for constant rod length
            property vector3d j_rodToCylStart: Qt.vector3d(j_rod.x - tailRodEnd.x, j_rod.y - tailRodEnd.y, 0)
            property real projectionOnCylAxis: j_rodToCylStart.x * cylDirectionNorm.x + j_rodToCylStart.y * cylDirectionNorm.y
            
            property vector3d j_rodProjectionOnAxis: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * projectionOnCylAxis,
                tailRodEnd.y + cylDirectionNorm.y * projectionOnCylAxis,
                tailRodEnd.z
            )
            
            property real perpendicularDistance: Math.hypot(
                j_rod.x - j_rodProjectionOnAxis.x,
                j_rod.y - j_rodProjectionOnAxis.y
            )
            
            property real rodLengthSquared: userPistonRodLength * userPistonRodLength
            property real perpDistSquared: perpendicularDistance * perpendicularDistance
            property real axialDistanceFromProjection: Math.sqrt(Math.max(0, rodLengthSquared - perpDistSquared))
            
            property real pistonPositionOnAxis: projectionOnCylAxis - axialDistanceFromProjection
            property real clampedPistonPosition: Math.max(10, Math.min(lCylinder - 10, pistonPositionOnAxis))
            
            property vector3d pistonCenter: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * clampedPistonPosition,
                tailRodEnd.y + cylDirectionNorm.y * clampedPistonPosition,
                tailRodEnd.z
            )
            
            // LEVER with controlled materials
            Model {
                source: "#Cube"
                position: Qt.vector3d(
                    j_arm.x + (userLeverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                    j_arm.y + (userLeverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                    j_arm.z
                )
                scale: Qt.vector3d(userLeverLength/100, 0.8, 0.8)
                eulerRotation: Qt.vector3d(0, 0, totalAngle)
                materials: PrincipledMaterial { 
                    baseColor: "#888888"
                    metalness: metalMetalness
                    roughness: metalRoughness
                    clearcoatAmount: metalClearcoat
                }
            }
            
            // TAIL ROD
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, lTailRod/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: "#cccccc"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // CYLINDER BODY (transparent with controlled materials)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
                scale: Qt.vector3d(userBoreHead/100, lCylinder/100, userBoreHead/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: "#ffffff"
                    metalness: 0.0
                    roughness: glassRoughness
                    opacity: glassOpacity
                    alphaMode: PrincipledMaterial.Blend 
                }
            }
            
            // PISTON
            Model {
                source: "#Cylinder"
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: "#ff0066"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // PISTON ROD (constant length)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(
                    (pistonCenter.x + j_rod.x) / 2,
                    (pistonCenter.y + j_rod.y) / 2,
                    pistonCenter.z
                )
                scale: Qt.vector3d(userRodDiameter/100, userPistonRodLength/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: "#cccccc"
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            // JOINTS - visible colored markers
            Model {
                source: "#Cylinder"
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { 
                    baseColor: "#0088ff"  // Blue - cylinder joint
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            Model {
                source: "#Cylinder"
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { 
                    baseColor: "#ff8800"  // Orange - lever joint
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
            
            Model {
                source: "#Cylinder" 
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial { 
                    baseColor: "#00ff44"  // Green - rod joint
                    metalness: metalMetalness
                    roughness: metalRoughness
                }
            }
        }

        // Four suspension corners
        SuspensionCorner { 
            id: flCorner
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fl_angle
            pistonPositionFromPython: root.userPistonPositionFL
        }
        
        SuspensionCorner { 
            id: frCorner
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fr_angle
            pistonPositionFromPython: root.userPistonPositionFR
        }
        
        SuspensionCorner { 
            id: rlCorner
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rl_angle
            pistonPositionFromPython: root.userPistonPositionRL
        }
        
        SuspensionCorner { 
            id: rrCorner
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rr_angle
            pistonPositionFromPython: root.userPistonPositionRR
        }
    }

    // ===============================================================
    // MOUSE CONTROLS - Fixed Orbital Camera
    // ===============================================================

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onPressed: (mouse) => {
            mouse.accepted = true
            root.mouseDown = true
            root.mouseButton = mouse.button
            root.lastX = mouse.x
            root.lastY = mouse.y
        }

        onReleased: {
            root.mouseDown = false
            root.mouseButton = 0
        }

        onPositionChanged: (mouse) => {
            if (!root.mouseDown) return
            const dx = mouse.x - root.lastX
            const dy = mouse.y - root.lastY

            if (root.mouseButton === Qt.LeftButton) {
                // Orbital rotation around fixed pivot
                root.yawDeg = root.normAngleDeg(root.yawDeg + dx * root.rotateSpeed)
                root.pitchDeg = root.clamp(root.pitchDeg - dy * root.rotateSpeed, -85, 85)
            } else if (root.mouseButton === Qt.RightButton) {
                // Panning in camera rig local space (NOT moving pivot)
                const fovRad = camera.fieldOfView * Math.PI / 180.0
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height
                const s = worldPerPixel * root.cameraSpeed
                
                // Pan in rig local X/Y coordinates
                root.panX -= dx * s
                root.panY += dy * s
            }

            root.lastX = mouse.x
            root.lastY = mouse.y
        }

        onWheel: (wheel) => {
            wheel.accepted = true
            const factor = Math.exp(-wheel.angleDelta.y * 0.0016)
            root.cameraDistance = root.clamp(root.cameraDistance * factor, root.minDistance, root.maxDistance)
        }

        onDoubleClicked: {
            resetView()
        }
    }

    // ===============================================================
    // ANIMATION TIMERS
    // ===============================================================

    Timer {
        running: isRunning
        interval: 16  // 60 FPS
        repeat: true
        onTriggered: {
            animationTime += 0.016
        }
    }
    
    Timer {
        running: autoRotate
        interval: 16
        repeat: true
        onTriggered: {
            yawDeg = normAngleDeg(yawDeg + autoRotateSpeed * 0.016 * 10)
        }
    }

    // ===============================================================
    // KEYBOARD SHORTCUTS
    // ===============================================================

    Keys.onPressed: (e) => {
        if (e.key === Qt.Key_R) {
            resetView()
        } else if (e.key === Qt.Key_Space) {
            isRunning = !isRunning
        } else if (e.key === Qt.Key_F) {
            autoFitFrame()
        }
    }

    focus: true

    // ===============================================================
    // INFO PANEL
    // ===============================================================

    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 480
        height: 200
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 8

        Column {
            anchors.centerIn: parent
            spacing: 6
            
            Text { 
                text: "PneumoStabSim Professional | Enhanced Realism v2.1"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true 
            }
            
            Text { 
                text: "✨ УЛУЧШЕНО: ExtendedSceneEnvironment + Fixed Orbital Camera"
                color: "#00ff88"
                font.pixelSize: 11 
            }
            
            Text { 
                text: "🎨 Эффекты: " + (bloomEnabled ? "Bloom " : "") + 
                      (ssaoEnabled ? "SSAO " : "") + (vignetteEnabled ? "Vignette " : "") +
                      (tonemapEnabled ? "Tonemap " : "")
                color: "#ffaa00"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "📷 Камера: " + cameraDistance.toFixed(0) + "мм | Pivot: (" + 
                      pivot.x.toFixed(0) + ", " + pivot.y.toFixed(0) + ", " + pivot.z.toFixed(0) + ")"
                color: "#cccccc"
                font.pixelSize: 10 
            }
            
            Text { 
                text: "🎮 ЛКМ-вращение | ПКМ-панорама | Колесо-зум | R-сброс | F-автофит | Space-анимация"
                color: "#aaddff"
                font.pixelSize: 9 
            }
            
            // Animation status
            Rectangle {
                width: 450
                height: 70
                color: "#33000000"
                border.color: isRunning ? "#00ff00" : "#ff0000"
                border.width: 2
                radius: 6
                
                Column {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: isRunning ? "🎬 АНИМАЦИЯ АКТИВНА" : "⏸️ Анимация остановлена"
                        color: isRunning ? "#00ff88" : "#ff6666"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    
                    Text {
                        text: "Параметры: A=" + userAmplitude.toFixed(1) + "° | f=" + userFrequency.toFixed(1) + "Гц | φ=" + userPhaseGlobal.toFixed(0) + "°"
                        color: "#cccccc"
                        font.pixelSize: 9
                    }
                    
                    Text {
                        text: "Углы: FL=" + fl_angle.toFixed(1) + "° | FR=" + fr_angle.toFixed(1) + 
                              "° | RL=" + rl_angle.toFixed(1) + "° | RR=" + rr_angle.toFixed(1) + "°"
                        color: "#aaaaaa"
                        font.pixelSize: 8
                    }
                }
            }
        }
    }

    // ===============================================================
    // INITIALIZATION
    // ===============================================================

    Component.onCompleted: {
        console.log("═══════════════════════════════════════════")
        console.log("🚀 PneumoStabSim Enhanced Realism v2.1 LOADED")
        console.log("═══════════════════════════════════════════")
        console.log("✅ ИСПРАВЛЕНО: ExtendedSceneEnvironment с Qt 6.9.3 совместимостью")
        console.log("✅ УЛУЧШЕНО: Орбитальная камера с фиксированным pivot")
        console.log("✅ ДОБАВЛЕНО: Улучшенные пост-эффекты (Bloom, SSAO, Vignette, Tonemap)")
        console.log("✅ ОПТИМИЗИРОВАНО: Плавная анимация камеры и интерфейса")
        console.log("📷 Pivot камеры зафиксирован в центре нижней балки рамы")
        console.log("🎨 Все графические эффекты управляются из Python панели")
        console.log("═══════════════════════════════════════════")
        
        resetView()
        view3d.forceActiveFocus()
    }
}
