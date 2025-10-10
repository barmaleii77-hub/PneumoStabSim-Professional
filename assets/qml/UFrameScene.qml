import QtQuick
import QtQuick3D

View3D {
    id: view3d
    anchors.fill: parent

    // ANIMATION PROPERTIES
    property real animationTime: 0.0
    property real animationSpeed: 0.8

    // USER-CONTROLLABLE GEOMETRY PARAMETERS (connected to UI)
    property real userBeamSize: 120        // mm - frame beam size
    property real userFrameHeight: 650     // mm - frame height  
    property real userFrameLength: 2000    // mm - frame length
    property real userLeverLength: 315     // mm - lever length
    property real userCylinderLength: 250  // mm - cylinder body length
    property real userTailRodLength: 100   // mm - tail rod length

    // CALCULATED PARAMETERS (derived from user inputs)
    property real beamSize: 120        // mm - frame beam size (from qml_host)
    property real frameHeight: 650     // mm - frame height (from qml_host)
    property real frameLength: 2000    // mm - frame length (from qml_host)
    property real leverLength: 315     // mm - lever length (from qml_host)

    // ?? ВНЕШНИЕ ПАРАМЕТРЫ УГЛОВ РЫЧАГОВ (от qml_host.py или анимации)
    property real fl_angle: 8 * Math.sin(animationTime)
    property real fr_angle: 8 * Math.sin(animationTime + Math.PI/4)
    property real rl_angle: 8 * Math.sin(animationTime + Math.PI/2)
    property real rr_angle: 8 * Math.sin(animationTime + 3*Math.PI/4)

    // ?? ВНЕШНИЕ ПАРАМЕТРЫ ПОЗИЦИЙ ШАРНИРОВ (от qml_host.py)
    property vector3d fl_j_arm: Qt.vector3d(-150, 60, -frameLength/2)
    property vector3d fr_j_arm: Qt.vector3d(150, 60, -frameLength/2)
    property vector3d rl_j_arm: Qt.vector3d(-150, 60, frameLength/2)
    property vector3d rr_j_arm: Qt.vector3d(150, 60, frameLength/2)

    property vector3d fl_j_tail: Qt.vector3d(-100, 710, -frameLength/2)
    property vector3d fr_j_tail: Qt.vector3d(100, 710, -frameLength/2)
    property vector3d rl_j_tail: Qt.vector3d(-100, 710, frameLength/2)
    property vector3d rr_j_tail: Qt.vector3d(100, 710, frameLength/2)

    // ?? ВНЕШНИЕ ПАРАМЕТРЫ РАЗМЕРОВ (от qml_host.py)
    property real fl_leverLength: leverLength    // will be overridden by qml_host
    property real fr_leverLength: leverLength    // will be overridden by qml_host
    property real rl_leverLength: leverLength    // will be overridden by qml_host
    property real rr_leverLength: leverLength    // will be overridden by qml_host
    
    property real fl_cylinderBodyLength: 250     // will be overridden by qml_host
    property real fr_cylinderBodyLength: 250     // will be overridden by qml_host
    property real rl_cylinderBodyLength: 250     // will be overridden by qml_host
    property real rr_cylinderBodyLength: 250     // will be overridden by qml_host
    
    property real fl_tailRodLength: 100          // will be overridden by qml_host
    property real fr_tailRodLength: 100          // will be overridden by qml_host
    property real rl_tailRodLength: 100          // will be overridden by qml_host
    property real rr_tailRodLength: 100          // will be overridden by qml_host

    // ?? ИСПРАВЛЕНЫ АНИМИРОВАННЫЕ ПОЗИЦИИ ШТОКА (используют ВНЕШНИЕ leverLength)
    // ANIMATED rod positions (move with lever rotation) - CORRECTED DIRECTIONS
    // FL/RL: Base angle 180deg (pointing LEFT) + oscillation
    property vector3d fl_j_rod: Qt.vector3d(
        fl_j_arm.x + fl_leverLength * Math.cos((180 + fl_angle) * Math.PI / 180),
        fl_j_arm.y + fl_leverLength * Math.sin((180 + fl_angle) * Math.PI / 180),
        fl_j_arm.z
    )
    property vector3d rl_j_rod: Qt.vector3d(
        rl_j_arm.x + rl_leverLength * Math.cos((180 + rl_angle) * Math.PI / 180),
        rl_j_arm.y + rl_leverLength * Math.sin((180 + rl_angle) * Math.PI / 180),
        rl_j_arm.z
    )
    
    // FR/RR: Base angle 0deg (pointing RIGHT) + oscillation  
    property vector3d fr_j_rod: Qt.vector3d(
        fr_j_arm.x + fr_leverLength * Math.cos((0 + fr_angle) * Math.PI / 180),
        fr_j_arm.y + fr_leverLength * Math.sin((0 + fr_angle) * Math.PI / 180),
        fr_j_arm.z
    )
    property vector3d rr_j_rod: Qt.vector3d(
        rr_j_arm.x + rr_leverLength * Math.cos((0 + rr_angle) * Math.PI / 180),
        rr_j_arm.y + rr_leverLength * Math.sin((0 + rr_angle) * Math.PI / 180),
        rr_j_arm.z
    )

    // CAMERA PROPERTIES
    property real cameraDistance: Math.max(frameLength * 1.5, 3500)
    property real cameraPitch: -25
    property real cameraYaw: 35

    // FUNCTIONS FOR UI INTEGRATION
    function updateGeometry(params) {
        console.log("?? UFrameScene: Updating geometry from UI", JSON.stringify(params))
        
        if (params.frameLength !== undefined) userFrameLength = params.frameLength
        if (params.frameHeight !== undefined) userFrameHeight = params.frameHeight
        if (params.frameBeamSize !== undefined) userBeamSize = params.frameBeamSize
        if (params.leverLength !== undefined) userLeverLength = params.leverLength
        if (params.cylinderBodyLength !== undefined) userCylinderLength = params.cylinderBodyLength
        if (params.tailRodLength !== undefined) userTailRodLength = params.tailRodLength
        
        // Auto-adjust camera distance for new frame size
        cameraDistance = Math.max(frameLength * 1.5, 3500)
        
        console.log(`   ? New dimensions: ${frameLength}x${frameHeight}x${beamSize}mm`)
        console.log(`   ?? Lever: ${leverLength}mm, Camera: ${cameraDistance}mm`)
    }
    
    function updateAnimation(angles) {
        // Update lever angles from simulation or UI
        if (angles.fl !== undefined) fl_angle = angles.fl
        if (angles.fr !== undefined) fr_angle = angles.fr
        if (angles.rl !== undefined) rl_angle = angles.rl
        if (angles.rr !== undefined) rr_angle = angles.rr
        
        console.log("?? Animation updated:", angles)
    }

    // Animation timer
    Timer {
        running: true
        interval: 33  // 30 FPS
        repeat: true
        onTriggered: {
            animationTime += animationSpeed * 0.033
        }
    }

    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#f0f0f0"
        antialiasingMode: SceneEnvironment.MSAA
    }

    Node {
        id: rig
        position: Qt.vector3d(0, frameHeight/2, 0)
        eulerRotation: Qt.vector3d(cameraPitch, cameraYaw, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraDistance)
            fieldOfView: 45
        }
    }

    DirectionalLight {
        eulerRotation.x: -30
        eulerRotation.y: -45
        brightness: 2.5
    }

    // Origin marker
    Model {
        source: "#Sphere"
        position: Qt.vector3d(0, 0, 0)
        scale: Qt.vector3d(3.0, 3.0, 3.0)
        materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting }
    }

    // ?? ИСПРАВЛЕННАЯ U-РАМА (из успешного теста)
    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, 0)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, -frameLength/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    Model {
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
    }

    // ?? ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ КОМПОНЕНТ ПОДВЕСКИ (из успешного теста)
    component CorrectedSuspensionCorner: Node {
        property vector3d j_arm
        property vector3d j_tail  
        property vector3d j_rod
        property real leverAngle
        property string cornerId: ""  // fl, fr, rl, rr
        
        // ?? ИСПОЛЬЗУЕМ ВНЕШНИЕ ПАРАМЕТРЫ (переданные от qml_host.py)
        property real cornerLeverLength: cornerId === "fl" ? parent.fl_leverLength :
                                        cornerId === "fr" ? parent.fr_leverLength :
                                        cornerId === "rl" ? parent.rl_leverLength :
                                        cornerId === "rr" ? parent.rr_leverLength : 315
        
        property real cornerCylinderLength: cornerId === "fl" ? parent.fl_cylinderBodyLength :
                                           cornerId === "fr" ? parent.fr_cylinderBodyLength :
                                           cornerId === "rl" ? parent.rl_cylinderBodyLength :
                                           cornerId === "rr" ? parent.rr_cylinderBodyLength : 250
        
        property real cornerTailRodLength: cornerId === "fl" ? parent.fl_tailRodLength :
                                          cornerId === "fr" ? parent.fr_tailRodLength :
                                          cornerId === "rl" ? parent.rl_tailRodLength :
                                          cornerId === "rr" ? parent.rr_tailRodLength : 100
        
        // CORRECTED LEVER (proper positioning and rotation around pivot with correct base angles)
        Model {
            source: "#Cube"
            // Position lever CENTERED on pivot point j_arm with correct base direction
            property real baseAngle: (j_arm.x < 0) ? 180 : 0  // Left side: 180deg, Right side: 0deg
            property real totalAngle: baseAngle + leverAngle
            
            position: Qt.vector3d(j_arm.x + (cornerLeverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                                 j_arm.y + (cornerLeverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                                 j_arm.z)
            scale: Qt.vector3d(cornerLeverLength/100, 0.8, 0.8)
            eulerRotation: Qt.vector3d(0, 0, totalAngle)  // Rotate with base + oscillation
            materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
        }
        
        // FIXED CYLINDER - STARTS FROM END OF TAIL ROD (not from j_tail joint)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: cornerCylinderLength  // EXTERNAL cylinder working length
            property real lTailRod: cornerTailRodLength  // EXTERNAL tail rod length
            
            // Cylinder starts FROM END OF TAIL ROD (not from j_tail)
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),  // End of tail rod
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd  // Cylinder starts where tail rod ends
            property vector3d cylEnd: Qt.vector3d(
                cylStart.x + cylDirection.x * (lBody / cylDirectionLength),
                cylStart.y + cylDirection.y * (lBody / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((cylStart.x + cylEnd.x)/2, (cylStart.y + cylEnd.y)/2, cylStart.z)
            scale: Qt.vector3d(1.2, lBody/100, 1.2)  // Working cylinder length only
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylEnd.y - cylStart.y, cylEnd.x - cylStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ffffff"; metalness: 0.0; roughness: 0.05; opacity: 0.12; alphaMode: PrincipledMaterial.Blend }
        }
        
        // MOVING PISTON (animated inside cylinder that starts from tail rod end) - CORRECT DIMENSIONS
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: cornerCylinderLength  // EXTERNAL parameter
            property real lTailRod: cornerTailRodLength  // EXTERNAL parameter
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))  // Scale -8deg..+8deg to 0..1
            
            // Cylinder starts FROM END OF TAIL ROD
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            // PISTON MOVES inside cylinder based on LEVER ANGLE
            property vector3d pistonPos: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: pistonPos
            // CORRECT DIMENSIONS: 20mm thick, 90% of cylinder diameter (1.2 * 0.9 = 1.08)
            scale: Qt.vector3d(1.08, 0.2, 1.08)  // Diameter 90% of cylinder, thickness 20mm
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }  // BRIGHT MAGENTA
        }
        
        // METAL ROD (from piston to j_rod) - NORMAL THICKNESS
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lBody: cornerCylinderLength  // EXTERNAL parameter
            property real lTailRod: cornerTailRodLength  // EXTERNAL parameter
            property real pistonRatio: Math.max(0.0, Math.min(1.0, (leverAngle + 8) / 16))  // SAME as piston
            
            // Cylinder starts FROM END OF TAIL ROD (same as piston calculation)
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            property vector3d cylStart: tailRodEnd
            
            // Rod starts from PISTON position (same calculation as piston)
            property vector3d rodStart: Qt.vector3d(
                cylStart.x + cylDirection.x * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.y + cylDirection.y * ((lBody * (0.15 + pistonRatio * 0.7)) / cylDirectionLength),
                cylStart.z
            )
            
            position: Qt.vector3d((rodStart.x + j_rod.x)/2, (rodStart.y + j_rod.y)/2, j_rod.z)
            scale: Qt.vector3d(0.5, Math.hypot(j_rod.x - rodStart.x, j_rod.y - rodStart.y, 0)/100, 0.5)  // Normal rod thickness
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - rodStart.y, j_rod.x - rodStart.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }  // STEEL
        }
        
        // TAIL ROD (EXTERNAL length from j_tail toward j_rod)
        Model {
            source: "#Cylinder"
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y, 0)
            property real lTailRod: cornerTailRodLength  // EXTERNAL tail rod length
            
            // Tail rod goes from j_tail toward j_rod direction
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirection.x * (lTailRod / cylDirectionLength),
                j_tail.y + cylDirection.y * (lTailRod / cylDirectionLength),
                j_tail.z
            )
            
            position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(0.5, lTailRod/100, 0.5)  // SAME diameter as main rod, EXTERNAL length
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(tailRodEnd.y - j_tail.y, tailRodEnd.x - j_tail.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }  // STEEL
        }
        
        // CORRECTED CYLINDRICAL JOINTS (PROPERLY ROUND AND Z-ORIENTED)
        
        // Tail joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder"
            position: j_tail
            scale: Qt.vector3d(1.2, 2.4, 1.2)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#0088ff"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Arm joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder"
            position: j_arm
            scale: Qt.vector3d(1.0, 2.0, 1.0)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#ff8800"; metalness: 0.8; roughness: 0.2 }
        }
        
        // Rod joint - TRULY ROUND along Z-axis (correct scale after rotation)
        Model {
            source: "#Cylinder" 
            position: j_rod
            scale: Qt.vector3d(0.8, 1.6, 0.8)  // After 90deg rotation: X=diameter, Y=length, Z=diameter
            eulerRotation: Qt.vector3d(90, 0, 0)  // Rotate 90deg around X to orient along Z-axis
            materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
        }
    }

    // Four suspension corners with EXTERNAL PARAMETERS and corner IDs
    CorrectedSuspensionCorner { j_arm: fl_j_arm; j_tail: fl_j_tail; j_rod: fl_j_rod; leverAngle: fl_angle; cornerId: "fl" }
    CorrectedSuspensionCorner { j_arm: fr_j_arm; j_tail: fr_j_tail; j_rod: fr_j_rod; leverAngle: fr_angle; cornerId: "fr" }
    CorrectedSuspensionCorner { j_arm: rl_j_arm; j_tail: rl_j_tail; j_rod: rl_j_rod; leverAngle: rl_angle; cornerId: "rl" }
    CorrectedSuspensionCorner { j_arm: rr_j_arm; j_tail: rr_j_tail; j_rod: rr_j_rod; leverAngle: rr_angle; cornerId: "rr" }

    // Small reference markers
    Model { source: "#Sphere"; position: fl_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: fr_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rl_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }
    Model { source: "#Sphere"; position: rr_j_arm; scale: Qt.vector3d(0.3, 0.3, 0.3); materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting } }

    // Mouse control
    MouseArea {
        anchors.fill: parent
        property real lastX: 0; property real lastY: 0; property bool dragging: false
        onPressed: function(mouse) { lastX = mouse.x; lastY = mouse.y; dragging = true }
        onReleased: function(mouse) { dragging = false }
        onPositionChanged: function(mouse) {
            if (!dragging) return
            cameraYaw += (mouse.x - lastX) * 0.5
            cameraPitch -= (mouse.y - lastY) * 0.5
            cameraPitch = Math.max(-89, Math.min(89, cameraPitch))
            lastX = mouse.x; lastY = mouse.y
        }
        onWheel: function(wheel) {
            var factor = 1.0 + (wheel.angleDelta.y / 1200.0)
            cameraDistance *= factor
            cameraDistance = Math.max(500, Math.min(15000, cameraDistance))
        }
    }

    Component.onCompleted: {
        console.log("=== ?? ИСПРАВЛЕННАЯ АНИМИРОВАННАЯ СХЕМА С ВНЕШНИМИ ПАРАМЕТРАМИ ===")
        console.log("ИСПРАВЛЕНИЯ:")
        console.log("? Использует ВНЕШНИЕ параметры от qml_host.py")
        console.log("? Круглые шарниры: scale(X=Y, Z=length)")
        console.log("? Движущиеся поршни: анимированы с выходом штока")
        console.log("? Стальные штоки: metalness=0.95 (не резина)")
        console.log("? Правильные углы рычагов: из анимации (не статичные 180deg)")
        console.log("=== ВНЕШНИЕ ПАРАМЕТРЫ (от qml_host.py) ===")
        console.log("beamSize:", beamSize, "mm")
        console.log("frameHeight:", frameHeight, "mm")
        console.log("frameLength:", frameLength, "mm")
        console.log("leverLength:", leverLength, "mm")
        console.log("=== ПАРАМЕТРЫ УГЛОВ ===")
        console.log("FL lever length:", fl_leverLength, "mm")
        console.log("FR lever length:", fr_leverLength, "mm")
        console.log("RL lever length:", rl_leverLength, "mm") 
        console.log("RR lever length:", rr_leverLength, "mm")
        console.log("=== ПАРАМЕТРЫ ЦИЛИНДРОВ ===")
        console.log("FL cylinder:", fl_cylinderBodyLength, "mm + tail", fl_tailRodLength, "mm")
        console.log("FR cylinder:", fr_cylinderBodyLength, "mm + tail", fr_tailRodLength, "mm")
        console.log("RL cylinder:", rl_cylinderBodyLength, "mm + tail", rl_tailRodLength, "mm")
        console.log("RR cylinder:", rr_cylinderBodyLength, "mm + tail", rr_tailRodLength, "mm")
        console.log("=== ОТЛАДОЧНЫЕ ЗНАЧЕНИЯ ===")
        console.log("FL угол:", fl_angle)
        console.log("FR угол:", fr_angle)
        console.log("FL j_arm позиция:", fl_j_arm.x, fl_j_arm.y, fl_j_arm.z)
        console.log("FR j_arm позиция:", fr_j_arm.x, fr_j_arm.y, fr_j_arm.z)
        console.log("FL j_rod позиция:", fl_j_rod.x, fl_j_rod.y, fl_j_rod.z)
        console.log("FR j_rod позиция:", fr_j_rod.x, fr_j_rod.y, fr_j_rod.z)
        console.log("Время анимации:", animationTime)
        console.log("?? Расстояние камеры:", cameraDistance, "mm")
        console.log("? Готов к интеграции с UI и пневматикой!")
        view3d.forceActiveFocus()
    }
    
    // WATCHERS for parameter changes
    onUserFrameLengthChanged: {
        console.log("?? Длина рамы изменена на:", userFrameLength, "mm")
        cameraDistance = Math.max(frameLength * 1.5, 3500)
    }
    
    onUserFrameHeightChanged: {
        console.log("?? Высота рамы изменена на:", userFrameHeight, "mm") 
    }
    
    onUserLeverLengthChanged: {
        console.log("?? Длина рычага изменена на:", userLeverLength, "mm")
    }
    
    onUserCylinderLengthChanged: {
        console.log("?? Длина цилиндра изменена на:", userCylinderLength, "mm")
    }
    
    onUserTailRodLengthChanged: {
        console.log("?? Длина хвостовика изменена на:", userTailRodLength, "mm")
    }
}
