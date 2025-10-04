import QtQuick
import QtQuick3D

/*
 * PneumoStabSim - Основной 3D вид
 * U-образная рама с надёжной орбитальной камерой + рычаги подвески
 */
Item {
    id: root
    anchors.fill: parent

    // -------- Состояние камеры/ввода --------
    property real cameraDistance: 4000
    property real minDistance: 150
    property real maxDistance: 30000

    property real yawDeg: 30     // вокруг Y (вправо-влево)
    property real pitchDeg: -20  // вокруг X (вверх-вниз), ограничиваем
    property vector3d target: Qt.vector3d(0, 400, 1000) // центр орбиты

    property bool mouseDown: false
    property int  mouseButton: 0
    property real lastX: 0
    property real lastY: 0

    // скорости
    property real rotateSpeed: 0.35
    property real panSpeedK: 1.0       // множитель панорамирования
    property real wheelZoomK: 0.0016   // чувствительность колеса

    // === СВОЙСТВА АНИМАЦИИ ===
    property real suspensionAngle: 0  // Угол качания рычага (-30° до +30°)

    // утилиты
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function normAngleDeg(a) {
        // нормализуем yaw в [-180..180] для численной стабильности
        var x = a % 360;
        if (x > 180) x -= 360;
        if (x < -180) x += 360;
        return x;
    }

    View3D {
        id: view3d
        anchors.fill: parent

        // --- окружение ---
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        // === ОРБИТАЛЬНАЯ УСТАНОВКА + КАМЕРА ===
        Node {
            id: cameraRig
            // установка стоит в точке цели
            position: root.target
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            PerspectiveCamera {
                id: camera
                // Камера на оси +Z, смотрит вдоль -Z (стандартная ориентация)
                position: Qt.vector3d(0, 0, root.cameraDistance)
                fieldOfView: 45
                clipNear: 1
                clipFar: 100000
            }
        }

        // --- освещение ---
        DirectionalLight { eulerRotation: Qt.vector3d(-30, -45, 0); brightness: 1.5 }
        DirectionalLight { eulerRotation: Qt.vector3d( 30, 135, 0); brightness: 1.0 }

        // === Геометрия (U-образная рама) ===
        readonly property real beamSize: 100
        readonly property real frameHeight: 600
        readonly property real frameLength: 2000

        Node {
            id: frame
            // нижняя балка
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize/2, view3d.frameLength/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.beamSize/100, view3d.frameLength/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
            // первая стойка
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
            // вторая стойка
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.frameLength - view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
        }

        // === РЫЧАГ ПОДВЕСКИ (ТЕСТ) ===
        Node {
            id: suspensionArm
            // Точка крепления на раме (передний левый угол)
            position: Qt.vector3d(-400, view3d.beamSize, view3d.beamSize/2)
            
            // Поворот рычага вокруг точки крепления
            eulerRotation: Qt.vector3d(0, 0, root.suspensionAngle)
            
            // Рычаг (балка)
            Model {
                source: "#Cube"
                position: Qt.vector3d(-200, -100, 0)  // Рычаг направлен вниз и в сторону
                scale: Qt.vector3d(4, 0.6, 0.8)      // Длинный и тонкий
                materials: PrincipledMaterial { 
                    baseColor: "#ff6600"  // Оранжевый для видимости
                    metalness: 0.8
                    roughness: 0.2 
                }
            }
            
            // Шарнир (точка крепления)
            Model {
                source: "#Sphere"
                position: Qt.vector3d(0, 0, 0)
                scale: Qt.vector3d(0.5, 0.5, 0.5)
                materials: PrincipledMaterial { 
                    baseColor: "#ffff00"  // Жёлтый шарнир
                    metalness: 0.9
                    roughness: 0.1 
                }
            }
            
            // Колесо на конце рычага
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(-400, -200, 0)  // На конце рычага
                scale: Qt.vector3d(1.2, 0.4, 1.2)     // Плоский цилиндр = колесо
                eulerRotation: Qt.vector3d(90, 0, 0)  // Поворот для колеса
                materials: PrincipledMaterial { 
                    baseColor: "#333333"  // Чёрное колесо
                    metalness: 0.1
                    roughness: 0.8 
                }
            }
        }

        // координатные оси
        Node {
            id: axes
            // X (красная)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(300, 0, 0); scale: Qt.vector3d(0.2, 0.2, 6); eulerRotation.y: 90
                materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
            }
            // Y (зелёная)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(0, 300, 0); scale: Qt.vector3d(0.2, 6, 0.2)
                materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
            }
            // Z (синяя)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(0, 0, 300); scale: Qt.vector3d(0.2, 0.2, 6)
                materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
            }
            // начало координат
            Model {
                source: "#Sphere"; position: Qt.vector3d(0, 0, 0); scale: Qt.vector3d(0.8, 0.8, 0.8)
                materials: PrincipledMaterial { baseColor: "#ffffff"; lighting: PrincipledMaterial.NoLighting }
            }
        }
    }

    // === АНИМАЦИЯ ===
    SequentialAnimation {
        id: suspensionAnimation
        running: true
        loops: Animation.Infinite
        
        NumberAnimation {
            target: root
            property: "suspensionAngle"
            from: -20
            to: 20
            duration: 2000
            easing.type: Easing.InOutSine
        }
        
        NumberAnimation {
            target: root
            property: "suspensionAngle"
            from: 20
            to: -20
            duration: 2000
            easing.type: Easing.InOutSine
        }
    }

    // === МЫШЬ/КЛАВИАТУРА ===
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onPressed: (mouse) => {
            mouse.accepted = true
            root.mouseDown = true
            root.mouseButton = mouse.button
            root.lastX = mouse.x
            root.lastY = mouse.y
            cursorShape = (mouse.button === Qt.RightButton) ? Qt.ClosedHandCursor : Qt.SizeAllCursor
        }

        onReleased: {
            root.mouseDown = false
            root.mouseButton = 0
            cursorShape = Qt.ArrowCursor
        }

        onPositionChanged: (mouse) => {
            if (!root.mouseDown) return
            const dx = mouse.x - root.lastX
            const dy = mouse.y - root.lastY
            const accel = (mouse.modifiers & Qt.ControlModifier) ? 1.8
                         : (mouse.modifiers & Qt.ShiftModifier) ? 0.5 : 1.0

            if (root.mouseButton === Qt.LeftButton) {
                // --- ВРАЩЕНИЕ (орбита) ---
                root.yawDeg   = root.normAngleDeg(root.yawDeg   + dx * root.rotateSpeed * accel)
                root.pitchDeg = root.clamp(root.pitchDeg - dy * root.rotateSpeed * accel, -85, 85)
            } else if (root.mouseButton === Qt.RightButton) {
                // --- ПАНОРАМИРОВАНИЕ ---
                // 1) сколько мировых метров соответствует 1 пикселю по вертикали
                const fovRad = camera.fieldOfView * Math.PI / 180.0
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height

                // 2) векторы камеры: forward, right, up в МИРЕ по текущему yaw/pitch
                const yaw  = root.yawDeg   * Math.PI / 180.0
                const pit  = root.pitchDeg * Math.PI / 180.0
                const cp = Math.cos(pit), sp = Math.sin(pit)
                const cy = Math.cos(yaw), sy = Math.sin(yaw)

                // forward (нормализован)
                const fx =  sy * cp
                const fy = -sp
                const fz = -cy * cp

                // right = normalize(cross(forward, up(0,1,0))) = (-fz, 0, fx) (нормализован уже)
                const rx = -fz
                const ry =  0
                const rz =  fx
                const rlen = Math.hypot(rx, ry, rz)
                const rnx = rx / (rlen || 1), rny = 0, rnz = rz / (rlen || 1)

                // upCam = normalize(cross(right, forward))
                const ux =  rny * fz - rnz * fy
                const uy =  rnz * fx - rnx * fz
                const uz =  rnx * fy - rny * fx
                const ulen = Math.hypot(ux, uy, uz)
                const unx = ux / (ulen || 1), uny = uy / (ulen || 1), unz = uz / (ulen || 1)

                // 3) смещение цели
                const panScale = worldPerPixel * root.panSpeedK * accel
                const moveX = (-dx * panScale) * rnx + ( dy * panScale) * unx
                const moveY = (-dx * panScale) * rny + ( dy * panScale) * uny
                const moveZ = (-dx * panScale) * rnz + ( dy * panScale) * unz

                root.target = Qt.vector3d(root.target.x + moveX,
                                          root.target.y + moveY,
                                          root.target.z + moveZ)
            }

            root.lastX = mouse.x
            root.lastY = mouse.y
        }

        onWheel: (wheel) => {
            wheel.accepted = true
            // экспоненциальный зум
            const accel = (wheel.modifiers & Qt.ControlModifier) ? 1.8
                         : (wheel.modifiers & Qt.ShiftModifier) ? 0.6 : 1.0
            const factor = Math.exp(-wheel.angleDelta.y * root.wheelZoomK * accel)
            root.cameraDistance = root.clamp(root.cameraDistance * factor, root.minDistance, root.maxDistance)
        }

        onDoubleClicked: {
            // Сброс на удачный вид
            resetView()
        }
    }

    Keys.onPressed: (e) => {
        if (e.key === Qt.Key_R) resetView()
        else if (e.key === Qt.Key_Space) {
            // Пауза/возобновление анимации
            suspensionAnimation.running = !suspensionAnimation.running
        }
    }

    function resetView() {
        // центр по раме: середина между стойками
        root.target = Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.frameLength/2)
        root.cameraDistance = 4000
        root.yawDeg = 30
        root.pitchDeg = -20
    }

    focus: true

    // информационная панель
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 380; height: 112
        color: "#aa000000"; border.color: "#60ffffff"; radius: 6

        Column {
            anchors.centerIn: parent; spacing: 4
            Text { text: "ПневмоСтабСим | U-рама + Подвеска"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "?? Анимированный рычаг подвески добавлен"; color: "#ffaa00"; font.pixelSize: 12 }
            Text { text: "ЛКМ — вращение, ПКМ — панорамирование, колесо — зум"; color: "#cccccc"; font.pixelSize: 11 }
            Text { text: "R — сброс | Пробел — пауза анимации | Ctrl — быстрее"; color: "#cccccc"; font.pixelSize: 10 }
        }
    }

    Component.onCompleted: {
        // стартовая позиция по геометрии
        resetView()
        console.log("ПневмоСтабСим 3D сцена загружена с рычагом подвески")
    }
}
