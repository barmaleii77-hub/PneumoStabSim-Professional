import QtQuick
import QtQuick3D

/*
 * PneumoStabSim - Main 3D View
 * Complete 4-corner pneumatic suspension system with orbital camera
 */
Item {
    id: root
    anchors.fill: parent

    // Camera state
    property real cameraDistance: 4000
    property real minDistance: 150
    property real maxDistance: 30000
    property real yawDeg: 30
    property real pitchDeg: -20
    property vector3d target: Qt.vector3d(0, 400, 1000)

    // Mouse input
    property bool mouseDown: false
    property int mouseButton: 0
    property real lastX: 0
    property real lastY: 0
    property real rotateSpeed: 0.35
    property real panSpeedK: 1.0
    property real wheelZoomK: 0.0016

    // Animation properties
    property real animationTime: 0.0
    property real animationSpeed: 0.8  // DEPRECATED - use userFrequency instead
    property bool isRunning: false  // NEW: Control animation from Python

    // USER-CONTROLLED ANIMATION PARAMETERS (from Python)
    property real userAmplitude: 8.0       // degrees
    property real userFrequency: 1.0       // Hz
    property real userPhaseGlobal: 0.0     // degrees
    property real userPhaseFL: 0.0         // degrees (per-wheel offset)
    property real userPhaseFR: 0.0
    property real userPhaseRL: 0.0
    property real userPhaseRR: 0.0

    // NEW: USER-CONTROLLED PISTON POSITIONS (from Python Physics Engine!)
    property real userPistonPositionFL: 125.0  // mm - piston position in FL cylinder (from physics)
    property real userPistonPositionFR: 125.0  // mm - piston position in FR cylinder (from physics)
    property real userPistonPositionRL: 125.0  // mm - piston position in RL cylinder (from physics)
    property real userPistonPositionRR: 125.0  // mm - piston position in RR cylinder (from physics)

    // Angles for each corner - CONTROLLED FROM PYTHON ONLY!
    // Do NOT use formula - Python will set these directly via setProperty()
    property real fl_angle: 0.0  // Set by Python via setProperty()
    property real fr_angle: 0.0  // Set by Python via setProperty()
    property real rl_angle: 0.0  // Set by Python via setProperty()
    property real rr_angle: 0.0  // Set by Python via setProperty()
    
    // DEBUG: Watch for angle changes
    onFl_angleChanged: {
        if (Math.abs(fl_angle) > 0.1) {  // Only log significant changes
            console.log("?? QML: fl_angle changed to", fl_angle.toFixed(2), "°")
        }
    }
    onFr_angleChanged: {
        if (Math.abs(fr_angle) > 0.1) {
            console.log("?? QML: fr_angle changed to", fr_angle.toFixed(2), "°")
        }
    }
    onRl_angleChanged: {
        if (Math.abs(rl_angle) > 0.1) {
            console.log("?? QML: rl_angle changed to", rl_angle.toFixed(2), "°")
        }
    }
    onRr_angleChanged: {
        if (Math.abs(rr_angle) > 0.1) {
            console.log("?? QML: rr_angle changed to", rr_angle.toFixed(2), "°")
        }
    }

    // UI parameters (controlled externally)
    property real userBeamSize: 120
    property real userFrameHeight: 650
    property real userFrameLength: 2000
    property real userLeverLength: 315
    property real userCylinderLength: 250

    // NEW: Additional geometry parameters from GeometryPanel
    property real userTrackWidth: 300        // Distance between left/right corners (mm)
    property real userFrameToPivot: 150      // Distance from frame centerline to lever pivot (mm)
    property real userRodPosition: 0.6       // Rod attachment position (fraction 0-1)
    property real userBoreHead: 80           // Head bore diameter (mm)
    property real userBoreRod: 80            // Rod bore diameter (mm)
    property real userRodDiameter: 35        // Piston rod diameter (mm)
    property real userPistonThickness: 25    // Piston thickness (mm)

    // Update geometry from UI
    function updateGeometry(params) {
        console.log("???????????????????????????????????????????????")
        console.log("?? main.qml: updateGeometry() called")
        console.log("?? Received params:", JSON.stringify(params))
        console.log("???????????????????????????????????????????????")
        
        if (params.frameLength !== undefined) {
            console.log("  ? Setting userFrameLength:", params.frameLength)
            userFrameLength = params.frameLength
        }
        if (params.frameHeight !== undefined) {
            console.log("  ? Setting userFrameHeight:", params.frameHeight)
            userFrameHeight = params.frameHeight
        }
        if (params.frameBeamSize !== undefined) {
            console.log("  ? Setting userBeamSize:", params.frameBeamSize)
            userBeamSize = params.frameBeamSize
        }
        if (params.leverLength !== undefined) {
            console.log("  ? Setting userLeverLength:", params.leverLength)
            userLeverLength = params.leverLength
        }
        if (params.cylinderBodyLength !== undefined) {
            console.log("  ? Setting userCylinderLength:", params.cylinderBodyLength)
            userCylinderLength = params.cylinderBodyLength
        }
        
        // NEW: Additional parameters
        if (params.trackWidth !== undefined) {
            console.log("  ? Setting userTrackWidth:", params.trackWidth)
            userTrackWidth = params.trackWidth
        }
        if (params.frameToPivot !== undefined) {
            console.log("  ? Setting userFrameToPivot:", params.frameToPivot)
            userFrameToPivot = params.frameToPivot
        }
        if (params.rodPosition !== undefined) {
            console.log("  ? Setting userRodPosition:", params.rodPosition)
            userRodPosition = params.rodPosition
        }
        if (params.boreHead !== undefined) {
            console.log("  ? Setting userBoreHead:", params.boreHead)
            userBoreHead = params.boreHead
        }
        if (params.boreRod !== undefined) {
            console.log("  ? Setting userBoreRod:", params.boreRod)
            userBoreRod = params.boreRod
        }
        if (params.rodDiameter !== undefined) {
            console.log("  ? Setting userRodDiameter:", params.rodDiameter)
            userRodDiameter = params.rodDiameter
        }
        if (params.pistonThickness !== undefined) {
            console.log("  ? Setting userPistonThickness:", params.pistonThickness)
            userPistonThickness = params.pistonThickness
        }
        
        console.log("???????????????????????????????????????????????")
        console.log("?? Current values after update:")
        console.log("   userFrameLength:", userFrameLength)
        console.log("   userFrameHeight:", userFrameHeight)
        console.log("   userBeamSize:", userBeamSize)
        console.log("   userLeverLength:", userLeverLength)
        console.log("   userCylinderLength:", userCylinderLength)
        console.log("   userTrackWidth:", userTrackWidth)
        console.log("   userFrameToPivot:", userFrameToPivot)
        console.log("   userRodPosition:", userRodPosition)
        console.log("   userBoreHead:", userBoreHead)
        console.log("   userBoreRod:", userBoreRod)
        console.log("   userRodDiameter:", userRodDiameter)
        console.log("   userPistonThickness:", userPistonThickness)
        console.log("???????????????????????????????????????????????")
        
        resetView()
        console.log("   Updated:", userFrameLength + "x" + userFrameHeight + "x" + userBeamSize + "mm")
    }
    
    // NEW: Update piston positions from Python physics engine
    function updatePistonPositions(positions) {
        // DEBUG: Show FIRST update with full details
        if (typeof updatePistonPositions.callCount === 'undefined') {
            updatePistonPositions.callCount = 0
        }
        
        if (updatePistonPositions.callCount === 0) {
            console.log("???????????????????????????????????????????????")
            console.log("?? main.qml: FIRST updatePistonPositions() call!")
            console.log("?? Received positions:", JSON.stringify(positions))
            console.log("???????????????????????????????????????????????")
        }
        
        updatePistonPositions.callCount++
        
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
        
        // DEBUG: Show values every 60 frames (~1 second at 60Hz)
        if (updatePistonPositions.callCount % 60 === 1) {
            console.log("?? Piston positions (frame " + updatePistonPositions.callCount + "):")
            console.log("   FL:", userPistonPositionFL.toFixed(2), "mm")
            console.log("   FR:", userPistonPositionFR.toFixed(2), "mm")
            console.log("   RL:", userPistonPositionRL.toFixed(2), "mm")
            console.log("   RR:", userPistonPositionRR.toFixed(2), "mm")
        }
    }
    
    function updateAnimation(angles) {
        console.log("?? updateAnimation() called:", JSON.stringify(angles))
        if (angles.fl !== undefined) fl_angle = Number(angles.fl)
        if (angles.fr !== undefined) fr_angle = Number(angles.fr)
        if (angles.rl !== undefined) rl_angle = Number(angles.rl)
        if (angles.rr !== undefined) rr_angle = Number(angles.rr)
        console.log("   ? Angles set: FL=" + fl_angle + ", FR=" + fr_angle + ", RL=" + rl_angle + ", RR=" + rr_angle)
    }

    // Utilities
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function normAngleDeg(a) {
        var x = a % 360;
        if (x > 180) x -= 360;
        if (x < -180) x += 360;
        return x;
    }

    // Animation timer (CONTROLLED BY isRunning)
    Timer {
        running: isRunning  // CHANGED: Now controlled by Python
        interval: 16  // 60 FPS for smooth animation
        repeat: true
        onTriggered: {
            animationTime += 0.016  // Fixed timestep in seconds
        }
    }

    View3D {
        id: view3d
        anchors.fill: parent

        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        // Orbital camera rig
        Node {
            id: cameraRig
            position: root.target
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            PerspectiveCamera {
                id: camera
                position: Qt.vector3d(0, 0, root.cameraDistance)
                fieldOfView: 45
                clipNear: 1
                clipFar: 100000
            }
        }

        // Lighting
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -45
            brightness: 2.5
        }

        // U-FRAME (3 beams)
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { baseColor: "#cc0000"; metalness: 0.8; roughness: 0.4 }
        }

        // SUSPENSION COMPONENT (with all parts)
        component SuspensionCorner: Node {
            property vector3d j_arm
            property vector3d j_tail  
            property real leverAngle
            property real pistonPositionFromPython: 125.0  // NEW: Piston position from Python (mm)
            
            // CALCULATE j_rod INTERNALLY from leverAngle!
            property real baseAngle: (j_arm.x < 0) ? 180 : 0  // Left=180°, Right=0°
            property real totalAngle: baseAngle + leverAngle
            
            // j_rod position calculated from lever rotation
            property vector3d j_rod: Qt.vector3d(
                j_arm.x + userLeverLength * Math.cos(totalAngle * Math.PI / 180),
                j_arm.y + userLeverLength * Math.sin(totalAngle * Math.PI / 180),
                j_arm.z
            )
            
            // LEVER (animated)
            Model {
                source: "#Cube"
                
                position: Qt.vector3d(j_arm.x + (userLeverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                                     j_arm.y + (userLeverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                                     j_arm.z)
                scale: Qt.vector3d(userLeverLength/100, 0.8, 0.8)
                eulerRotation: Qt.vector3d(0, 0, totalAngle)
                materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
            }
            
            // === PNEUMATIC CYLINDER ASSEMBLY ===
            // Direction from tail to rod attachment
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
            property vector3d cylDirectionNorm: Qt.vector3d(
                cylDirection.x / cylDirectionLength,
                cylDirection.y / cylDirectionLength,
                0
            )
            
            // FIXED dimensions
            property real lTailRod: 100           // Tail rod: 100mm (CONSTANT)
            property real lCylinder: userCylinderLength  // Cylinder body (CONSTANT)
            
            // Tail rod end (where cylinder starts)
            property vector3d tailRodEnd: Qt.vector3d(
                j_tail.x + cylDirectionNorm.x * lTailRod,
                j_tail.y + cylDirectionNorm.y * lTailRod,
                j_tail.z
            )
            
            // Cylinder end (where rod exits cylinder)
            property vector3d cylinderEnd: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * lCylinder,
                tailRodEnd.y + cylDirectionNorm.y * lCylinder,
                tailRodEnd.z
            )
            
            // PISTON POSITION - FROM PYTHON (absolute position inside cylinder, mm from tailRodEnd)
            property vector3d pistonCenter: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * pistonPositionFromPython,
                tailRodEnd.y + cylDirectionNorm.y * pistonPositionFromPython,
                tailRodEnd.z
            )
            
            // TAIL ROD (FIXED: from j_tail to cylinder start)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, lTailRod/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
            }
            
            // CYLINDER BODY (FIXED LENGTH, transparent to see piston and rod inside)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
                scale: Qt.vector3d(userBoreHead/100, lCylinder/100, userBoreHead/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { 
                    baseColor: "#ffffff"; 
                    metalness: 0.0; 
                    roughness: 0.05; 
                    opacity: 0.15; 
                    alphaMode: PrincipledMaterial.Blend 
                }
            }
            
            // PISTON (moves INSIDE cylinder, visible through transparent cylinder)
            // Position from PYTHON PHYSICS ENGINE!
            Model {
                source: "#Cylinder"
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }
            }
            
            // PISTON ROD - VARIABLE LENGTH (connects piston to j_rod)
            // Piston moves INSIDE cylinder (from Python physics)
            // Rod extends/retracts to connect piston to j_rod
            Model {
                source: "#Cylinder"
                
                // Current rod length = distance from piston to j_rod
                // This CHANGES as piston moves inside cylinder!
                property real rodLength: Math.hypot(j_rod.x - pistonCenter.x, j_rod.y - pistonCenter.y)
                
                // Rod center position (halfway from piston to j_rod)
                position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, j_rod.z)
                
                // Scale: diameter is constant, length CHANGES
                scale: Qt.vector3d(userRodDiameter/100, rodLength/100, userRodDiameter/100)
                
                // Rotation to align with direction from piston to j_rod
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                
                materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
            }
            
            // JOINTS (cylinders along Z-axis)
            
            // Cylinder joint (blue)
            Model {
                source: "#Cylinder"
                position: j_tail
                scale: Qt.vector3d(1.2, 2.4, 1.2)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { baseColor: "#0088ff"; metalness: 0.8; roughness: 0.2 }
            }
            
            // Lever joint (orange)
            Model {
                source: "#Cylinder"
                position: j_arm
                scale: Qt.vector3d(1.0, 2.0, 1.0)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { baseColor: "#ff8800"; metalness: 0.8; roughness: 0.2 }
            }
            
            // Rod joint (green)
            Model {
                source: "#Cylinder" 
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, 0)
                materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
            }
        }

        // FOUR SUSPENSION CORNERS (parametric coordinates with user parameters)
        SuspensionCorner { 
            id: flCorner
            // Front left - j_rod calculated internally!
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fl_angle  // Python controls this!
            pistonPositionFromPython: root.userPistonPositionFL
        }
        
        SuspensionCorner { 
            id: frCorner
            // Front right
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fr_angle  // Python controls this!
            pistonPositionFromPython: root.userPistonPositionFR
        }
        
        SuspensionCorner { 
            id: rlCorner
            // Rear left
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rl_angle  // Python controls this!
            pistonPositionFromPython: root.userPistonPositionRL
        }
        
        SuspensionCorner { 
            id: rrCorner
            // Rear right
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rr_angle  // Python controls this!
            pistonPositionFromPython: root.userPistonPositionRR
        }

        // Coordinate axes
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(300, 0, 0)
            scale: Qt.vector3d(0.2, 0.2, 6)
            eulerRotation.y: 90
            materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
        }
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(0, 300, 0)
            scale: Qt.vector3d(0.2, 6, 0.2)
            materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
        }
        Model {
            source: "#Cylinder"
            position: Qt.vector3d(0, 0, 300)
            scale: Qt.vector3d(0.2, 0.2, 6)
            materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
        }
    }

    // Mouse control
    MouseArea {
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
                // Rotation
                root.yawDeg = root.normAngleDeg(root.yawDeg + dx * root.rotateSpeed)
                root.pitchDeg = root.clamp(root.pitchDeg - dy * root.rotateSpeed, -85, 85)
            } else if (root.mouseButton === Qt.RightButton) {
                // Panning
                const fovRad = camera.fieldOfView * Math.PI / 180.0
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height
                const panScale = worldPerPixel * root.panSpeedK
                
                const yaw = root.yawDeg * Math.PI / 180.0
                const pit = root.pitchDeg * Math.PI / 180.0
                const cp = Math.cos(pit), sp = Math.sin(pit)
                const cy = Math.cos(yaw), sy = Math.sin(yaw)
                
                const fx = sy * cp, fy = -sp, fz = -cy * cp
                const rx = -fz, rz = fx
                const rlen = Math.hypot(rx, 0, rz)
                const rnx = rx / (rlen || 1), rnz = rz / (rlen || 1)
                
                const ux = 0 * fz - rnz * fy
                const uy = rnz * fx - rnx * fz
                const uz = rnx * fy - 0 * fx
                const ulen = Math.hypot(ux, uy, uz)
                const unx = ux / (ulen || 1), uny = uy / (ulen || 1), unz = uz / (ulen || 1)
                
                const moveX = (-dx * panScale) * rnx + (dy * panScale) * unx
                const moveY = (dy * panScale) * uny
                const moveZ = (-dx * panScale) * rnz + (dy * panScale) * unz
                                
                root.target = Qt.vector3d(root.target.x + moveX, root.target.y + moveY, root.target.z + moveZ)
            }

            root.lastX = mouse.x
            root.lastY = mouse.y
        }

        onWheel: (wheel) => {
            wheel.accepted = true
            const factor = Math.exp(-wheel.angleDelta.y * root.wheelZoomK)
            root.cameraDistance = root.clamp(root.cameraDistance * factor, root.minDistance, root.maxDistance)
        }

        onDoubleClicked: {
            resetView()
        }
    }

    Keys.onPressed: (e) => {
        if (e.key === Qt.Key_R) resetView()
        else if (e.key === Qt.Key_Space) {
            // Toggle animation (future feature)
        }
    }

    function resetView() {
        root.target = Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength/2)
        root.cameraDistance = 4000
        root.yawDeg = 30
        root.pitchDeg = -20
    }

    focus: true

    // Info panel
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 450
        height: 140
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 6

        Column {
            anchors.centerIn: parent
            spacing: 4
            Text { text: "PneumoStabSim | 4-Corner Pneumatic Suspension"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "? All components: levers, cylinders, pistons, rods, tail rods, joints"; color: "#ffaa00"; font.pixelSize: 11 }
            Text { text: "? Animated pistons (pink) move inside transparent cylinders"; color: "#cccccc"; font.pixelSize: 10 }
            Text { text: "LMB - rotate | RMB - pan | Wheel - zoom | R - reset | DblClick - fit"; color: "#cccccc"; font.pixelSize: 10 }
        }
    }

    Component.onCompleted: {
        resetView()
        console.log("???????????????????????????????????????????????")
        console.log("?? PneumoStabSim 4-Corner Suspension LOADED")
        console.log("???????????????????????????????????????????????")
        console.log("? All 4 corners: FL, FR, RL, RR")
        console.log("? All components: levers, cylinders, pistons, rods, tail rods, joints")
        console.log("? PYTHON PHYSICS INTEGRATION: Piston positions from physics engine!")
        console.log("???????????????????????????????????????????????")
        console.log("?? Initial geometry:")
        console.log("   Frame:", userFrameLength + "x" + userFrameHeight + "x" + userBeamSize + "mm")
        console.log("   Lever:", userLeverLength + "mm")
        console.log("   Cylinder:", userCylinderLength + "mm")
        console.log("   Track width:", userTrackWidth + "mm")
        console.log("   Frame to pivot:", userFrameToPivot + "mm")
        console.log("   Rod position:", userRodPosition)
        console.log("   Bore head:", userBoreHead + "mm")
        console.log("   Bore rod:", userBoreRod + "mm")
        console.log("   Rod diameter:", userRodDiameter + "mm")
        console.log("   Piston thickness:", userPistonThickness + "mm")
        console.log("???????????????????????????????????????????????")
        console.log("?? Animation:")
        console.log("   Amplitude:", userAmplitude + "deg")
        console.log("   Frequency:", userFrequency + "Hz")
        console.log("   Phase global:", userPhaseGlobal + "deg")
        console.log("   Phase FL/FR/RL/RR:", userPhaseFL + "/" + userPhaseFR + "/" + userPhaseRL + "/" + userPhaseRR + "deg")
        console.log("   isRunning:", isRunning)
        console.log("???????????????????????????????????????????????")
        console.log("?? PISTON POSITIONS (from Python Physics):")
        console.log("   FL:", userPistonPositionFL + "mm")
        console.log("   FR:", userPistonPositionFR + "mm")
        console.log("   RL:", userPistonPositionRL + "mm")
        console.log("   RR:", userPistonPositionRR + "mm")
        console.log("???????????????????????????????????????????????")
        console.log("? updateGeometry() function ready for UI integration")
        console.log("? updatePistonPositions() function ready for physics integration")
        console.log("???????????????????????????????????????????????")
        view3d.forceActiveFocus()
    }
}
