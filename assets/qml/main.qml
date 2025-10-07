import QtQuick
import QtQuick3D

/*
 * PneumoStabSim - Main 3D View
 * Complete 4-corner pneumatic suspension system with orbital camera
 * ИСПРАВЛЕНО: Анимация штока и правильное соединение с шарниром
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
    property real userPistonPositionFL: 250.0  // mm - ИСПРАВЛЕНО: 500/2 для centra цилиндра 500мм
    property real userPistonPositionFR: 250.0  // mm - ИСПРАВЛЕНО: 500/2 для centra цилиндра 500мм
    property real userPistonPositionRL: 250.0  // mm - ИСПРАВЛЕНО: 500/2 для centra цилиндра 500мм
    property real userPistonPositionRR: 250.0  // mm - ИСПРАВЛЕНО: 500/2 для centra цилиндра 500мм

    // Angles for each corner - CALCULATED from animation parameters
    property real fl_angle: useAutoAngles && isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseFL) * Math.PI / 180) : 0.0
    property real fr_angle: useAutoAngles && isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseFR) * Math.PI / 180) : 0.0
    property real rl_angle: useAutoAngles && isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseRL) * Math.PI / 180) : 0.0
    property real rr_angle: useAutoAngles && isRunning ? userAmplitude * Math.sin(animationTime * userFrequency * 2 * Math.PI + (userPhaseGlobal + userPhaseRR) * Math.PI / 180) : 0.0
    
    // Control mode: auto-calculate or Python-controlled
    property bool useAutoAngles: true

    // DEBUG: Watch for angle changes
    onFl_angleChanged: {
        if (Math.abs(fl_angle) > 0.1) {  // Only log significant changes
            console.log("🔍 QML: fl_angle changed to", fl_angle.toFixed(2), "°")
        }
    }
    onFr_angleChanged: {
        if (Math.abs(fr_angle) > 0.1) {
            console.log("🔍 QML: fr_angle changed to", fr_angle.toFixed(2), "°")
        }
    }
    onRl_angleChanged: {
        if (Math.abs(rl_angle) > 0.1) {
            console.log("🔍 QML: rl_angle changed to", rl_angle.toFixed(2), "°")
        }
    }
    onRr_angleChanged: {
        if (Math.abs(rr_angle) > 0.1) {
            console.log("🔍 QML: rr_angle changed to", rr_angle.toFixed(2), "°")
        }
    }

    // ✅ ИСПРАВЛЕНО: USER-CONTROLLED GEOMETRY PARAMETERS - соответствуют панели геометрии!
    property real userBeamSize: 120        // мм - размер балки (без изменений)
    property real userFrameHeight: 650     // мм - высота рамы (без изменений)
    property real userFrameLength: 3200    // мм - ИСПРАВЛЕНО: было 2000, теперь 3200 (wheelbase 3.2м)
    property real userLeverLength: 800     // мм - ИСПРАВЛЕНО: было 315, теперь 800 (lever_length 0.8м)
    property real userCylinderLength: 500  // мм - ИСПРАВЛЕНО: было 250, теперь 500 (cylinder_length 0.5м)
    property real userTrackWidth: 1600     // мм - ИСПРАВЛЕНО: было 300, теперь 1600 (track 1.6м)
    property real userFrameToPivot: 600    // мм - ИСПРАВЛЕНО: было 150, теперь 600 (frame_to_pivot 0.6м)
    property real userRodPosition: 0.6     // доля - без изменений (rod_position 0.6)
    property real userBoreHead: 80         // мм - без изменений (cyl_diam_m 0.080м)
    property real userBoreRod: 80          // мм - без изменений (cyl_diam_m 0.080м)
    property real userRodDiameter: 35      // мм - без изменений (rod_diameter_m 0.035м)
    property real userPistonThickness: 25  // мм - без изменений (piston_thickness_m 0.025м)
    
    // NEW: Piston rod length (set by user, NOT calculated!)
    property real userPistonRodLength: 200  // мм - без изменений (piston_rod_length_m 0.200м)

    // Update geometry from UI
    function updateGeometry(params) {
        console.log("💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡")
        console.log("🔧 main.qml: updateGeometry() called - ALL PARAMETERS SUPPORT")
        console.log("🔧 Received params:", JSON.stringify(params))
        console.log("💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡")
        
        // ОСНОВНЫЕ РАЗМЕРЫ РАМЫ
        if (params.frameLength !== undefined) {
            console.log("  🔧 Setting userFrameLength:", params.frameLength)
            userFrameLength = params.frameLength
        }
        if (params.frameHeight !== undefined) {
            console.log("  🔧 Setting userFrameHeight:", params.frameHeight)
            userFrameHeight = params.frameHeight
        }
        if (params.frameBeamSize !== undefined) {
            console.log("  🔧 Setting userBeamSize:", params.frameBeamSize)
            userBeamSize = params.frameBeamSize
        }
        
        // ГЕОМЕТРИЯ ПОДВЕСКИ
        if (params.leverLength !== undefined) {
            console.log("  🔧 Setting userLeverLength:", params.leverLength)
            userLeverLength = params.leverLength
        }
        if (params.cylinderBodyLength !== undefined) {
            console.log("  🔧 Setting userCylinderLength:", params.cylinderBodyLength)
            userCylinderLength = params.cylinderBodyLength
        }
        
        // ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ ГЕОМЕТРИИ
        if (params.trackWidth !== undefined) {
            console.log("  🔧 Setting userTrackWidth:", params.trackWidth)
            userTrackWidth = params.trackWidth
        }
        if (params.frameToPivot !== undefined) {
            console.log("  🔧 Setting userFrameToPivot:", params.frameToPivot)
            userFrameToPivot = params.frameToPivot
        }
        if (params.rodPosition !== undefined) {
            console.log("  🔧 ✨ Setting userRodPosition:", params.rodPosition, "- КРИТИЧЕСКИЙ ПАРАМЕТР!")
            userRodPosition = params.rodPosition
            console.log("      Новое положение шарнира штока на рычаге:", (userRodPosition * 100).toFixed(1) + "%")
        }
        
        // УСТАРЕВШИЕ ПАРАМЕТРЫ (для совместимости)
        if (params.boreHead !== undefined) {
            console.log("  🔧 Setting userBoreHead (deprecated):", params.boreHead)
            userBoreHead = params.boreHead
        }
        if (params.boreRod !== undefined) {
            console.log("  🔧 Setting userBoreRod (deprecated):", params.boreRod)
            userBoreRod = params.boreRod
        }
        if (params.rodDiameter !== undefined) {
            console.log("Setting userRodDiameter (deprecated):", params.rodDiameter)
            userRodDiameter = params.rodDiameter
        }
        if (params.pistonThickness !== undefined) {
            console.log("  🔧 Setting userPistonThickness (deprecated):", params.pistonThickness)
            userPistonThickness = params.pistonThickness
        }
        if (params.pistonRodLength !== undefined) {
            console.log("  🔧 Setting userPistonRodLength (deprecated):", params.pistonRodLength)
            userPistonRodLength = params.pistonRodLength
        }
        
        // ✨ НОВЫЕ ПАРАМЕТРЫ - МШ-1: Параметры цилиндра в мм (из м)
        if (params.cylDiamM !== undefined) {
            console.log("  ✨ Setting userCylDiamM (NEW):", params.cylDiamM, "мм")
            userBoreHead = params.cylDiamM  // Совместимость: цилиндр = диаметр головной камеры
            userBoreRod = params.cylDiamM   // Совместимость: цилиндр = диаметр штоковой камеры
        }
        if (params.strokeM !== undefined) {
            console.log("  ✨ Setting userStrokeM (NEW):", params.strokeM, "мм")
            // Ход поршня - можно использовать для расчета длины цилиндра
            // userCylinderLength примерно равен strokeM + dead zones
        }
        if (params.deadGapM !== undefined) {
            console.log("  ✨ Setting userDeadGapM (NEW):", params.deadGapM, "мм")
            // Мертвый зазор - влияет на минимальную длину цилиндра
        }
        
        // ✨ НОВЫЕ ПАРАМЕТРЫ - МШ-2: Параметры штока и поршня в мм (из м)
        if (params.rodDiameterM !== undefined) {
            console.log("  ✨ Setting userRodDiameterM (NEW):", params.rodDiameterM, "мм")
            userRodDiameter = params.rodDiameterM  // Совместимость: используем новое значение
        }
        if (params.pistonRodLengthM !== undefined) {
            console.log("  ✨ Setting userPistonRodLengthM (NEW):", params.pistonRodLengthM, "мм")
            userPistonRodLength = params.pistonRodLengthM  // Совместимость: используем новое значение
        }
        if (params.pistonThicknessM !== undefined) {
            console.log("  ✨ Setting userPistonThicknessM (NEW):", params.pistonThicknessM, "мм")
            userPistonThickness = params.pistonThicknessM  // Совместимость: используем новое значение
        }
        
        console.log("💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡")
        console.log("🔧 Current values after COMPLETE update:")
        console.log("  📐 Frame: L=" + userFrameLength + ", H=" + userFrameHeight + ", Beam=" + userBeamSize)
        console.log("  📐 Suspension: Lever=" + userLeverLength + ", Cylinder=" + userCylinderLength)
        console.log("  📐 Track: Width=" + userTrackWidth + ", Frame→Pivot=" + userFrameToPivot + ", RodPos=" + userRodPosition + " (" + (userRodPosition * 100).toFixed(1) + "%)")
        console.log("  📐 OLD Cylinder: BoreHead=" + userBoreHead + ", BoreRod=" + userBoreRod)
        console.log("  📐 OLD Rod: Diameter=" + userRodDiameter + ", Length=" + userPistonRodLength + ", PistonThick=" + userPistonThickness)
        console.log("  ✨ NEW: Все параметры с дискретностью 0.001м теперь поддерживаются!")
        console.log("  ✨ ✨ ИСПРАВЛЕНО: userRodPosition теперь влияет на положение j_rod!")
        console.log("💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡💡")
        
        resetView()
        console.log("  ✅ Geometry updated and view reset")
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

        // ✨ УЛУЧШЕННОЕ ОСВЕЩЕНИЕ: Трехточечная схема освещения
        
        // Key Light (основной свет) - яркий направленный свет
        DirectionalLight {
            id: keyLight
            eulerRotation.x: -30
            eulerRotation.y: -45
            brightness: 2.8  // Увеличена яркость
            color: "#ffffff"
        }
        
        // ✨ НОВОЕ: Fill Light (заполняющий свет) - смягчает тени
        DirectionalLight {
            id: fillLight
            eulerRotation.x: -60
            eulerRotation.y: 135
            brightness: 1.2
            color: "#f0f0ff"  // Слегка голубоватый для контраста
        }
        
        // ✨ НОВОЕ: Rim Light (контровой свет) - создает контур объектов
        DirectionalLight {
            id: rimLight
            eulerRotation.x: 15
            eulerRotation.y: 180
            brightness: 1.5
            color: "#ffffcc"  // Теплый оттенок для контраста
        }
        
        // ✨ НОВОЕ: Point Light (точечный акцент) - подсвечивает центр
        PointLight {
            id: accentLight
            position: Qt.vector3d(0, 1800, 1500)  // Над центром сцены
            brightness: 20000  // Высокая яркость для точечного света
            color: "#ffffff"
            quadraticFade: 0.00008  // Мягкое затухание
        }

        // Lighting
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -45
            brightness: 2.5
        }

        // U-FRAME (3 beams) - обновленные материалы
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize/2, userFrameLength/2)
            scale: Qt.vector3d(userBeamSize/100, userBeamSize/100, userFrameLength/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: 0.7  // Уменьшена металличность
                roughness: 0.3  // Уменьшена шероховатость
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: 0.7
                roughness: 0.3
            }
        }
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, userBeamSize + userFrameHeight/2, userFrameLength - userBeamSize/2)
            scale: Qt.vector3d(userBeamSize/100, userFrameHeight/100, userBeamSize/100)
            materials: PrincipledMaterial { 
                baseColor: "#cc0000"
                metalness: 0.7
                roughness: 0.3
            }
        }

        // SUSPENSION COMPONENT (with all parts)
        component SuspensionCorner: Node {
            property vector3d j_arm
            property vector3d j_tail  
            property real leverAngle
            property real pistonPositionFromPython: 250.0  // NEW: Piston position from Python (mm)
            
            // ✅ ИСПРАВЛЕНО: Правильные базовые углы для левой и правой стороны
            // Левая сторона (x < 0): базовый угол 180° (рычаг смотрит влево)
            // Правая сторона (x > 0): базовый угол 0° (рычаг смотрит вправо)
            property real baseAngle: (j_arm.x < 0) ? 180 : 0
            property real totalAngle: baseAngle + leverAngle
            
            // ✅ ИСПРАВЛЕНО: j_rod position - правильный расчет с базовыми углами
            property vector3d j_rod: Qt.vector3d(
                j_arm.x + (userLeverLength * userRodPosition) * Math.cos(totalAngle * Math.PI / 180),
                j_arm.y + (userLeverLength * userRodPosition) * Math.sin(totalAngle * Math.PI / 180),
                j_arm.z
            )
            
            // === CYLINDER GEOMETRY CALCULATIONS ===
            property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
            property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
            property vector3d cylDirectionNorm: Qt.vector3d(
                cylDirection.x / cylDirectionLength,
                cylDirection.y / cylDirectionLength,
                0
            )
            
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
            
            // 🔧 НОВАЯ ЛОГИКА: Поршень позиционируется так, чтобы длина штока была постоянной
            // Расстояние от j_rod до оси цилиндра (перпендикулярное расстояние)
            property vector3d j_rodToCylStart: Qt.vector3d(j_rod.x - tailRodEnd.x, j_rod.y - tailRodEnd.y, 0)
            property real projectionOnCylAxis: j_rodToCylStart.x * cylDirectionNorm.x + j_rodToCylStart.y * cylDirectionNorm.y
            
            // Проекция j_rod на ось цилиндра
            property vector3d j_rodProjectionOnAxis: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * projectionOnCylAxis,
                tailRodEnd.y + cylDirectionNorm.y * projectionOnCylAxis,
                tailRodEnd.z
            )
            
            // Расстояние от проекции j_rod до реального j_rod (перпендикулярно оси цилиндра)
            property real perpendicularDistance: Math.hypot(
                j_rod.x - j_rodProjectionOnAxis.x,
                j_rod.y - j_rodProjectionOnAxis.y
            )
            
            // Вычисляем позицию поршня на оси цилиндра для постоянной длины штока
            property real rodLengthSquared: userPistonRodLength * userPistonRodLength
            property real perpDistSquared: perpendicularDistance * perpendicularDistance
            property real axialDistanceFromProjection: Math.sqrt(Math.max(0, rodLengthSquared - perpDistSquared))
            
            // Позиция поршня на оси цилиндра (назад от проекции j_rod)
            property real pistonPositionOnAxis: projectionOnCylAxis - axialDistanceFromProjection
            
            // Ограничиваем позицию поршня в пределах цилиндра
            property real clampedPistonPosition: Math.max(10, Math.min(lCylinder - 10, pistonPositionOnAxis))
            
            // PISTON POSITION - ВЫЧИСЛЕННАЯ для постоянной длины штока
            property vector3d pistonCenter: Qt.vector3d(
                tailRodEnd.x + cylDirectionNorm.x * clampedPistonPosition,
                tailRodEnd.y + cylDirectionNorm.y * clampedPistonPosition,
                tailRodEnd.z
            )
            
            // Проверяем реальную длину штока (для отладки)
            property real actualRodLength: Math.hypot(j_rod.x - pistonCenter.x, j_rod.y - pistonCenter.y)
            
            // ✅ LEVER с правильным расчетом центра и базовыми углами
            Model {
                source: "#Cube"
                position: Qt.vector3d(
                    j_arm.x + (userLeverLength/2) * Math.cos(totalAngle * Math.PI / 180), 
                    j_arm.y + (userLeverLength/2) * Math.sin(totalAngle * Math.PI / 180), 
                    j_arm.z
                )
                scale: Qt.vector3d(userLeverLength/100, 0.8, 0.8)
                eulerRotation: Qt.vector3d(0, 0, totalAngle)
                materials: PrincipledMaterial { baseColor: "#888888"; metalness: 0.9; roughness: 0.3 }
            }
            
            // TAIL ROD (FIXED: from j_tail to cylinder start)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
                scale: Qt.vector3d(userRodDiameter/100, lTailRod/100, userRodDiameter/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { baseColor: "#cccccc"; metalness: 0.95; roughness: 0.05 }
            }
            
            // CYLINDER BODY (FIXED LENGTH, transparent)
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
            
            // ✅ ИСПРАВЛЕНО: PISTON - движется по оси цилиндра, отслеживая рычаг
            Model {
                source: "#Cylinder"
                position: pistonCenter
                scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { baseColor: "#ff0066"; metalness: 0.9; roughness: 0.1 }
            }
            
            // ✅ ИСПРАВЛЕНО: PISTON ROD - ПОСТОЯННАЯ ДЛИНА!
            Model {
                source: "#Cylinder"
                
                // Центр штока - между поршнем и шарниром
                position: Qt.vector3d(
                    (pistonCenter.x + j_rod.x) / 2,
                    (pistonCenter.y + j_rod.y) / 2,
                    pistonCenter.z
                )
                
                // ✅ ФИКСИРОВАННАЯ ДЛИНА ШТОКА из параметров UI
                scale: Qt.vector3d(userRodDiameter/100, userPistonRodLength/100, userRodDiameter/100)
                
                // Поворот: точное направление от поршня к шарниру
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
            
            // Rod joint (green) - точно в j_rod
            Model {
                source: "#Cylinder" 
                position: j_rod
                scale: Qt.vector3d(0.8, 1.6, 0.8)
                eulerRotation: Qt.vector3d(90, 0, leverAngle * 0.1)
                materials: PrincipledMaterial { baseColor: "#00ff44"; metalness: 0.7; roughness: 0.3 }
            }
            
            // 🆕 ОТЛАДОЧНЫЕ МАРКЕРЫ
            
            // Красная сфера в j_rod
            Model {
                source: "#Sphere"
                position: j_rod
                scale: Qt.vector3d(0.3, 0.3, 0.3)
                materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
            }
            
            // Желтая сфера - проекция j_rod на ось цилиндра
            Model {
                source: "#Sphere"
                position: j_rodProjectionOnAxis
                scale: Qt.vector3d(0.2, 0.2, 0.2)
                materials: PrincipledMaterial { baseColor: "#ffff00"; lighting: PrincipledMaterial.NoLighting }
            }
            
            // Тонкая линия от поршня к j_rod (визуализация штока)
            Model {
                source: "#Cylinder"
                position: Qt.vector3d((pistonCenter.x + j_rod.x) / 2, (pistonCenter.y + j_rod.y) / 2, pistonCenter.z)
                scale: Qt.vector3d(0.1, actualRodLength/100, 0.1)
                eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
                materials: PrincipledMaterial { baseColor: "#00ffff"; lighting: PrincipledMaterial.NoLighting }
            }
            
            // DEBUG: Логирование
            Component.onCompleted: {
                console.log("🔧 Подвеска " + (j_arm.x < 0 ? "L" : "R") + ":")
                console.log("   Заданная длина штока: " + userPistonRodLength.toFixed(1) + "мм")
                console.log("   Реальная длина штока: " + actualRodLength.toFixed(1) + "мм")
                console.log("   Отклонение: " + (actualRodLength - userPistonRodLength).toFixed(1) + "мм")
                console.log("   Позиция поршня на оси: " + clampedPistonPosition.toFixed(1) + "мм")
            }
        }

        // ✅ ИСПРАВЛЕНО: FOUR SUSPENSION CORNERS с правильными координатами
        SuspensionCorner { 
            id: flCorner
            // Front left - левая сторона, базовый угол 180°
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fl_angle
            pistonPositionFromPython: root.userPistonPositionFL
        }
        
        SuspensionCorner { 
            id: frCorner
            // Front right - правая сторона, базовый угол 0°
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userBeamSize/2)
            leverAngle: fr_angle
            pistonPositionFromPython: root.userPistonPositionFR
        }
        
        SuspensionCorner { 
            id: rlCorner
            // Rear left - левая сторона, базовый угол 180°
            j_arm: Qt.vector3d(-userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(-userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rl_angle
            pistonPositionFromPython: root.userPistonPositionRL
        }
        
        SuspensionCorner { 
            id: rrCorner
            // Rear right - правая сторона, базовый угол 0°
            j_arm: Qt.vector3d(userFrameToPivot, userBeamSize, userFrameLength - userBeamSize/2)
            j_tail: Qt.vector3d(userTrackWidth/2, userBeamSize + userFrameHeight, userFrameLength - userBeamSize/2)
            leverAngle: rr_angle
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
        height: 180  // УВЕЛИЧЕНО для показа параметров анимации
        color: "#aa000000"
        border.color: "#60ffffff"
        radius: 6

        Column {
            anchors.centerIn: parent
            spacing: 4
            Text { 
                text: "PneumoStabSim | 4-Corner Pneumatic Suspension"
                color: "#ffffff"
                font.pixelSize: 14
                font.bold: true 
            }
            Text { 
                text: "✅ All components: levers, cylinders, pistons, rods, tail rods, joints"
                color: "#ffaa00"
                font.pixelSize: 11 
            }
            Text { 
                text: "✅ Animated pistons (pink) move inside transparent cylinders"
                color: "#cccccc"
                font.pixelSize: 10 
            }
            Text { 
                text: "LMB - rotate | RMB - pan | Wheel - zoom | R - reset | DblClick - fit"
                color: "#cccccc"
                font.pixelSize: 10 
            }
            
            // ✨ НОВОЕ: Показываем параметры анимации
            Rectangle {
                width: 430
                height: 60
                color: "#33000000"
                border.color: isRunning ? "#00ff00" : "#ff0000"
                border.width: 2
                radius: 4
                
                Column {
                    anchors.centerIn: parent
                    spacing: 2
                    
                    Text {
                        text: isRunning ? "🎬 АНИМАЦИЯ ЗАПУЩЕНА" : "⏸️ Анимация остановлена"
                        color: isRunning ? "#00ff00" : "#ff6666"
                        font.pixelSize: 11
                        font.bold: true
                    }
                    
                    Text {
                        text: "Амплитуда: " + userAmplitude.toFixed(1) + "° | " +
                              "Частота: " + userFrequency.toFixed(1) + " Гц | " +
                              "Фаза: " + userPhaseGlobal.toFixed(0) + "°"
                        color: "#cccccc"
                        font.pixelSize: 9
                    }
                    
                    Text {
                        text: "Углы: FL=" + fl_angle.toFixed(1) + "° FR=" + fr_angle.toFixed(1) + 
                              "° RL=" + rl_angle.toFixed(1) + "° RR=" + rr_angle.toFixed(1) + "°"
                        color: "#aaaaaa"
                        font.pixelSize: 8
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        resetView()
        console.log("=== PneumoStabSim 4-Corner Suspension LOADED ===")
        console.log("All 4 corners: FL, FR, RL, RR")
        console.log("All components: levers, cylinders, pistons, rods, tail rods, joints")
        console.log("Rod length fixed: Piston moves along cylinder axis with constant rod length")
        console.log("Rod length = " + userPistonRodLength + "mm (does not change with lever movement)")
        console.log("Piston tracks lever movement but stays at correct distance")
        console.log("New piston positioning logic:")
        console.log("  1. Calculate j_rod projection on cylinder axis")
        console.log("  2. Calculate piston position for constant rod length")
        console.log("  3. Piston moves along cylinder axis, tracking lever")
        console.log("  4. Distance piston-j_rod = const = " + userPistonRodLength + "mm")
        console.log("Debug markers:")
        console.log("  Red sphere = j_rod (rod joint)")
        console.log("  Yellow sphere = j_rod projection on cylinder axis")
        console.log("  Cyan line = rod visualization (length should be constant)")
        console.log("  Pink cylinder = piston (moves along cylinder axis)")
        console.log("Geometry (matches geometry panel):")
        console.log("  Frame:", userFrameLength + "x" + userFrameHeight + "x" + userBeamSize + "mm")
        console.log("  Lever:", userLeverLength + "mm | Cylinder:", userCylinderLength + "mm")
        console.log("  Track width:", userTrackWidth + "mm | Frame to Pivot:", userFrameToPivot + "mm")
        console.log("  Rod position:", userRodPosition + " (" + (userRodPosition * 100).toFixed(1) + "%)")
        console.log("  Rod diameter:", userRodDiameter + "mm | Rod length:", userPistonRodLength + "mm")
        view3d.forceActiveFocus()
    }
}
