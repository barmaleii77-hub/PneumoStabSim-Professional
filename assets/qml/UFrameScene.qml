import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

View3D {
    id: view3d
    anchors.fill: parent

    // ========== Параметры геометрии (передаются из Python) ==========
    // Рама
    property real beamSize: 100
    property real frameHeight: 600
    property real frameLength: 2000

    // Параметры углов (пример для FL; аналогично FR/RL/RR)
    // FL - Front Left
    property vector3d fl_j_arm: Qt.vector3d(-800, 100, -1600)
    property real fl_armLength: 500
    property real fl_armAngleDeg: 0
    property real fl_attachFrac: 0.7
    property vector3d fl_j_tail: Qt.vector3d(-500, 200, -1400)
    property vector3d fl_j_rod: Qt.vector3d(-750, 150, -1500)
    property real fl_bore_d: 80
    property real fl_rod_d: 40
    property real fl_L_body: 300
    property real fl_piston_thickness: 20
    property real fl_dead_bo_vol: 0.0001
    property real fl_dead_sh_vol: 0.0001
    property real fl_s_min: 50
    property real fl_mass_unsprung: 50

    // FR - Front Right
    property vector3d fr_j_arm: Qt.vector3d(800, 100, -1600)
    property real fr_armLength: 500
    property real fr_armAngleDeg: 0
    property real fr_attachFrac: 0.7
    property vector3d fr_j_tail: Qt.vector3d(500, 200, -1400)
    property vector3d fr_j_rod: Qt.vector3d(750, 150, -1500)
    property real fr_bore_d: 80
    property real fr_rod_d: 40
    property real fr_L_body: 300
    property real fr_piston_thickness: 20
    property real fr_dead_bo_vol: 0.0001
    property real fr_dead_sh_vol: 0.0001
    property real fr_s_min: 50
    property real fr_mass_unsprung: 50

    // RL - Rear Left
    property vector3d rl_j_arm: Qt.vector3d(-800, 100, 1600)
    property real rl_armLength: 500
    property real rl_armAngleDeg: 0
    property real rl_attachFrac: 0.7
    property vector3d rl_j_tail: Qt.vector3d(-500, 200, 1400)
    property vector3d rl_j_rod: Qt.vector3d(-750, 150, 1500)
    property real rl_bore_d: 80
    property real rl_rod_d: 40
    property real rl_L_body: 300
    property real rl_piston_thickness: 20
    property real rl_dead_bo_vol: 0.0001
    property real rl_dead_sh_vol: 0.0001
    property real rl_s_min: 50
    property real rl_mass_unsprung: 50

    // RR - Rear Right
    property vector3d rr_j_arm: Qt.vector3d(800, 100, 1600)
    property real rr_armLength: 500
    property real rr_armAngleDeg: 0
    property real rr_attachFrac: 0.7
    property vector3d rr_j_tail: Qt.vector3d(500, 200, 1400)
    property vector3d rr_j_rod: Qt.vector3d(750, 150, 1500)
    property real rr_bore_d: 80
    property real rr_rod_d: 40
    property real rr_L_body: 300
    property real rr_piston_thickness: 20
    property real rr_dead_bo_vol: 0.0001
    property real rr_dead_sh_vol: 0.0001
    property real rr_s_min: 50
    property real rr_mass_unsprung: 50

    // ========== Внутренние переменные камеры ==========
    property real cameraDistance: 3000
    property real cameraPitch: -25
    property real cameraYaw: 30

    // ========== SceneEnvironment с IBL и MSAA ==========
    environment: SceneEnvironment {
        backgroundMode: SceneEnvironment.Color
        clearColor: "#ffffff"
        // lightProbe: Texture {
        //     source: "assets/studio_small_09_2k.hdr"  // ОТКЛЮЧЕНО: файл не существует
        //     mappingMode: Texture.LightProbe
        // }
        antialiasingMode: SceneEnvironment.MSAA
        antialiasingQuality: SceneEnvironment.High
        tonemapMode: SceneEnvironment.TonemapModeAces
    }

    // ========== Пивот (центр нижней балки) ==========
    Node {
        id: pivot
        position: Qt.vector3d(0, beamSize/2, frameLength/2)
    }

    // ========== Орбит-камера (вращение вокруг пивота) ==========
    Node {
        id: rig
        position: pivot.position
        eulerRotation: Qt.vector3d(cameraPitch, cameraYaw, 0)

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, cameraDistance)
            fieldOfView: 45
            clipNear: 1
            clipFar: 100000

            // Headlight (подсветка от камеры)
            PointLight {
                position: Qt.vector3d(0, 0, 100)
                brightness: 15.0
                castsShadow: false
            }
        }
    }

    // ========== OrbitCameraController ==========
    OrbitCameraController {
        origin: rig
        camera: camera
        panEnabled: false
        mouseEnabled: true
    }

    // ========== Ключевой направленный свет с тенями ==========
    DirectionalLight {
        id: keyLight
        eulerRotation.x: -40
        eulerRotation.y: 135
        brightness: 1.5
        castsShadow: true
        shadowMapQuality: Light.ShadowMapQualityHigh
        shadowBias: 0.002
    }

    // ========== Второй заполняющий свет (fill light) ==========
    DirectionalLight {
        id: fillLight
        eulerRotation.x: -20
        eulerRotation.y: -45
        brightness: 0.6
        castsShadow: false
        color: "#f0f0ff"
    }

    // ========== Третий контровый свет (rim/back light) ==========
    DirectionalLight {
        id: rimLight
        eulerRotation.x: 10
        eulerRotation.y: -120
        brightness: 0.8
        castsShadow: false
        color: "#fffaf0"
    }

    // ========== Мягкий ambient (общий фон) ==========
    DirectionalLight {
        id: ambientLight
        eulerRotation.x: 0
        eulerRotation.y: 0
        brightness: 0.2
        castsShadow: false
    }

    // ========== U-Рама (3 примитива) ==========
    
    // PBR материалы (inline)
    PrincipledMaterial {
        id: redMetal
        baseColor: "#d01515"
        metalness: 1.0
        roughness: 0.28
        clearcoatAmount: 0.25
        clearcoatRoughnessAmount: 0.1
    }
    
    PrincipledMaterial {
        id: steel
        baseColor: "#9fa5ad"
        metalness: 0.9
        roughness: 0.35
    }
    
    PrincipledMaterial {
        id: steelThin
        baseColor: "#b9c0c8"
        metalness: 0.8
        roughness: 0.25
    }
    
    PrincipledMaterial {
        id: chrome
        baseColor: "#e6e6e6"
        metalness: 1.0
        roughness: 0.12
    }
    
    PrincipledMaterial {
        id: glass
        baseColor: "#ffffff"
        metalness: 0.0
        roughness: 0.05
        opacity: 0.35
        alphaMode: PrincipledMaterial.Blend
        cullMode: Material.BackFaceCulling
    }
    
    PrincipledMaterial {
        id: massSphere
        baseColor: "#a0d8ff"
        metalness: 0.2
        roughness: 0.6
        opacity: 0.55
        alphaMode: PrincipledMaterial.Blend
    }
    
    // Нижняя балка
    Model {
        id: bottomBeam
        source: "#Cube"
        position: Qt.vector3d(0, beamSize/2, frameLength/2)
        scale: Qt.vector3d(beamSize/100, beamSize/100, frameLength/100)
        materials: redMetal
        receivesShadows: true
        castsShadows: true
    }

    // Стойка 1 (передняя, Z?0)
    Model {
        id: post1
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: redMetal
        receivesShadows: true
        castsShadows: true
    }

    // Стойка 2 (задняя, Z?frameLength)
    Model {
        id: post2
        source: "#Cube"
        position: Qt.vector3d(0, beamSize + frameHeight/2, frameLength - beamSize/2)
        scale: Qt.vector3d(beamSize/100, frameHeight/100, beamSize/100)
        materials: redMetal
        receivesShadows: true
        castsShadows: true
    }

    // ========== МЕХАНИКА: 4 угла ==========
    Node {
        id: mechanics

        // Компонент MechCorner (inline) - ПОЛНАЯ ВЕРСИЯ
        component MechCorner : Node {
            // Входные параметры
            property vector3d j_arm: Qt.vector3d(0, 0, 0)
            property real armLength: 500
            property real armAngleDeg: 0
            property real attachFrac: 0.7
            property vector3d j_tail: Qt.vector3d(0, 0, 0)  // C
            property vector3d j_rod: Qt.vector3d(0, 0, 0)   // E
            property real bore_d: 80
            property real rod_d: 40
            property real lBody: 300
            property real piston_thickness: 20
            property real mass_unsprung: 50

            // Вспомогательные вычисления
            readonly property vector3d v_CE: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, j_rod.z - j_tail.z)
            readonly property real lPin: Math.hypot(v_CE.x, v_CE.y, v_CE.z)
            readonly property vector3d u: Qt.vector3d(v_CE.x / (lPin || 1e-9), v_CE.y / (lPin || 1e-9), v_CE.z / (lPin || 1e-9))

            // Хвостовик: короткий патрубок C -> R
            readonly property real lTail: Math.min(0.15 * lBody, 0.2 * bore_d)
            readonly property vector3d rPoint: Qt.vector3d(j_tail.x + u.x * lTail, j_tail.y + u.y * lTail, j_tail.z + u.z * lTail)
            readonly property vector3d fPoint: Qt.vector3d(rPoint.x + u.x * lBody, rPoint.y + u.y * lBody, rPoint.z + u.z * lBody)

            // Упрощённый ход поршня (центр корпуса)
            readonly property real x: lBody * 0.3  // 30% хода от задней крышки
            readonly property vector3d pFront: Qt.vector3d(fPoint.x - u.x * x, fPoint.y - u.y * x, fPoint.z - u.z * x)
            readonly property vector3d pBack: Qt.vector3d(pFront.x - u.x * piston_thickness, pFront.y - u.y * piston_thickness, pFront.z - u.z * piston_thickness)

            // Функция размещения цилиндра по оси
            function placeAlongAxis(node, A, B, radius) {
                const v = Qt.vector3d(B.x - A.x, B.y - A.y, B.z - A.z)
                const L = Math.hypot(v.x, v.y, v.z)
                
                node.position = Qt.vector3d((A.x + B.x) / 2, (A.y + B.y) / 2, (A.z + B.z) / 2)
                
                // Простое выравнивание (упрощённое)
                if (Math.abs(v.z) > 0.9 * L) {
                    // Вдоль Z - поворот X
                    node.eulerRotation.x = (v.z > 0) ? 0 : 180
                } else if (Math.abs(v.x) > 0.9 * L) {
                    // Вдоль X - поворот Z
                    node.eulerRotation.z = (v.x > 0) ? 90 : -90
                } else {
                    // Произвольное направление - упрощённое выравнивание
                    const angleY = Math.atan2(v.x, v.z) * 180 / Math.PI
                    const angleX = -Math.atan2(v.y, Math.hypot(v.x, v.z)) * 180 / Math.PI
                    node.eulerRotation.y = angleY
                    node.eulerRotation.x = angleX
                }
                
                node.scale = Qt.vector3d((radius * 2) / 100, L / 100, (radius * 2) / 100)
            }

            // ===== РЫЧАГ =====
            readonly property vector3d lever_end: Qt.vector3d(
                j_arm.x + armLength * Math.cos(armAngleDeg * Math.PI / 180),
                j_arm.y + armLength * Math.sin(armAngleDeg * Math.PI / 180),
                j_arm.z
            )

            Model {
                id: lever
                source: "#Cube"
                materials: steel
                Component.onCompleted: placeAlongAxis(lever, j_arm, lever_end, 0.3 * bore_d)
            }

            // Шарнир рычага (цилиндр по Z)
            Model {
                source: "#Cylinder"
                materials: steel
                eulerRotation.x: 90
                position: j_arm
                scale: Qt.vector3d((bore_d * 0.6) / 100, 0.15, (bore_d * 0.6) / 100)
            }

            // ===== ЦИЛИНДР =====
            
            // Хвостовик (патрубок C -> R)
            Model {
                id: tail
                source: "#Cylinder"
                materials: steel
                Component.onCompleted: placeAlongAxis(tail, j_tail, rPoint, 0.35 * bore_d)
            }

            // Корпус цилиндра (стекло, R -> F)
            Model {
                id: barrel
                source: "#Cylinder" 
                materials: glass
                Component.onCompleted: placeAlongAxis(barrel, rPoint, fPoint, 0.55 * bore_d)
            }

            // Крышка задняя (R)
            Model {
                source: "#Cylinder"
                materials: steelThin
                position: rPoint
                eulerRotation: Qt.vector3d(
                    Math.atan2(u.y, Math.hypot(u.x, u.z)) * 180 / Math.PI,
                    -Math.atan2(u.x, u.z) * 180 / Math.PI,
                    0
                )
                scale: Qt.vector3d((bore_d * 0.56) / 100, 0.05, (bore_d * 0.56) / 100)
            }

            // Крышка передняя (F)
            Model {
                source: "#Cylinder"
                materials: steelThin
                position: fPoint
                eulerRotation: Qt.vector3d(
                    Math.atan2(u.y, Math.hypot(u.x, u.z)) * 180 / Math.PI,
                    -Math.atan2(u.x, u.z) * 180 / Math.PI,
                    0
                )
                scale: Qt.vector3d((bore_d * 0.56) / 100, 0.05, (bore_d * 0.56) / 100)
            }

            // Поршень (диск с толщиной)
            Model {
                id: piston
                source: "#Cylinder"
                materials: steel
                Component.onCompleted: placeAlongAxis(piston, pBack, pFront, 0.54 * bore_d)
            }

            // Шток (видимая часть F -> E)
            Model {
                id: rod
                source: "#Cylinder"
                materials: chrome
                Component.onCompleted: placeAlongAxis(rod, fPoint, j_rod, 0.5 * rod_d)
            }

            // Шарнир хвостовика (C)
            Model {
                source: "#Cylinder"
                materials: steel
                eulerRotation.x: 90
                position: j_tail
                scale: Qt.vector3d((bore_d * 0.6) / 100, 0.15, (bore_d * 0.6) / 100)
            }

            // Шарнир штока (E)  
            Model {
                source: "#Cylinder"
                materials: steel
                eulerRotation.x: 90
                position: j_rod
                scale: Qt.vector3d((bore_d * 0.5) / 100, 0.15, (bore_d * 0.5) / 100)
            }

            // ===== МАССА =====
            Model {
                source: "#Sphere"
                position: lever_end
                scale: Qt.vector3d(1, 1, 1).times(Math.max(0.05, 0.12 * Math.sqrt(Math.max(mass_unsprung, 0))))
                materials: massSphere
            }
        }

        // FL - Front Left
        MechCorner {
            j_arm: fl_j_arm
            armLength: fl_armLength
            armAngleDeg: fl_armAngleDeg
            attachFrac: fl_attachFrac
            j_tail: fl_j_tail
            j_rod: fl_j_rod
            bore_d: fl_bore_d
            rod_d: fl_rod_d
            lBody: fl_L_body  // ИСПРАВЛЕНО: L_body -> lBody
            piston_thickness: fl_piston_thickness
            mass_unsprung: fl_mass_unsprung
        }

        // FR - Front Right
        MechCorner {
            j_arm: fr_j_arm
            armLength: fr_armLength
            armAngleDeg: fr_armAngleDeg
            attachFrac: fr_attachFrac
            j_tail: fr_j_tail
            j_rod: fr_j_rod
            bore_d: fr_bore_d
            rod_d: fr_rod_d
            lBody: fr_L_body  // ИСПРАВЛЕНО
            piston_thickness: fr_piston_thickness
            mass_unsprung: fr_mass_unsprung
        }

        // RL - Rear Left
        MechCorner {
            j_arm: rl_j_arm
            armLength: rl_armLength
            armAngleDeg: rl_armAngleDeg
            attachFrac: rl_attachFrac
            j_tail: rl_j_tail
            j_rod: rl_j_rod
            bore_d: rl_bore_d
            rod_d: rl_rod_d
            lBody: rl_L_body  // ИСПРАВЛЕНО
            piston_thickness: rl_piston_thickness
            mass_unsprung: rl_mass_unsprung
        }

        // RR - Rear Right
        MechCorner {
            j_arm: rr_j_arm
            armLength: rr_armLength
            armAngleDeg: rr_armAngleDeg
            attachFrac: rr_attachFrac
            j_tail: rr_j_tail
            j_rod: rr_j_rod
            bore_d: rr_bore_d
            rod_d: rr_rod_d
            lBody: rr_L_body  // ИСПРАВЛЕНО
            piston_thickness: rr_piston_thickness
            mass_unsprung: rr_mass_unsprung
        }
    }

    // ========== Auto-Fit функция ==========
    function autoFit() {
        var minX = -Math.max(800, beamSize/2)
        var maxX = Math.max(800, beamSize/2)
        var minY = 0
        var maxY = beamSize + frameHeight + 200
        var minZ = -1700
        var maxZ = frameLength + 100

        var cx = (minX + maxX) / 2
        var cy = (minY + maxY) / 2
        var cz = (minZ + maxZ) / 2
        var dx = maxX - minX
        var dy = maxY - minY
        var dz = maxZ - minZ
        var r = 0.5 * Math.sqrt(dx*dx + dy*dy + dz*dz)

        pivot.position = Qt.vector3d(0, beamSize/2, frameLength/2)
        rig.position = pivot.position

        var vFOV = camera.fieldOfView * Math.PI / 180
        var aspect = view3d.width / view3d.height
        var hFOV = 2 * Math.atan(Math.tan(vFOV/2) * aspect)
        var phi = Math.min(vFOV, hFOV)
        var padding = 0.12
        var dist = (r * (1 + padding)) / Math.sin(phi / 2)

        cameraDistance = dist
        camera.clipNear = Math.max(1, dist - r * 2)
        camera.clipFar = dist + r * 3
    }

    function resetView() {
        cameraPitch = -25
        cameraYaw = 30
        autoFit()
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F) {
            autoFit()
            event.accepted = true
        } else if (event.key === Qt.Key_R) {
            resetView()
            event.accepted = true
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onDoubleClicked: {
            autoFit()
        }
    }

    Component.onCompleted: {
        view3d.forceActiveFocus()
        autoFit()
    }

    onWidthChanged: autoFit()
    onHeightChanged: autoFit()
}
