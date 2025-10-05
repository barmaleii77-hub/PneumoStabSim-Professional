import QtQuick
import QtQuick3D

/*
 * PneumoStabSim - �������� 3D ���
 * U-�������� ���� � ������� ����������� ������� + ������ ��������
 */
Item {
    id: root
    anchors.fill: parent

    // -------- ��������� ������/����� --------
    property real cameraDistance: 4000
    property real minDistance: 150
    property real maxDistance: 30000

    property real yawDeg: 30     // ������ Y (������-�����)
    property real pitchDeg: -20  // ������ X (�����-����), ������������
    property vector3d target: Qt.vector3d(0, 400, 1000) // ����� ������

    property bool mouseDown: false
    property int  mouseButton: 0
    property real lastX: 0
    property real lastY: 0

    // ��������
    property real rotateSpeed: 0.35
    property real panSpeedK: 1.0       // ��������� ���������������
    property real wheelZoomK: 0.0016   // ���������������� ������

    // === �������� �������� ===
    property real suspensionAngle: 0  // ���� ������� ������ (-30� �� +30�)

    // �������
    function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
    function normAngleDeg(a) {
        // ����������� yaw � [-180..180] ��� ��������� ������������
        var x = a % 360;
        if (x > 180) x -= 360;
        if (x < -180) x += 360;
        return x;
    }

    View3D {
        id: view3d
        anchors.fill: parent

        // --- ��������� ---
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        // === ����������� ��������� + ������ ===
        Node {
            id: cameraRig
            // ��������� ����� � ����� ����
            position: root.target
            eulerRotation: Qt.vector3d(root.pitchDeg, root.yawDeg, 0)

            PerspectiveCamera {
                id: camera
                // ������ �� ��� +Z, ������� ����� -Z (����������� ����������)
                position: Qt.vector3d(0, 0, root.cameraDistance)
                fieldOfView: 45
                clipNear: 1
                clipFar: 100000
            }
        }

        // --- ��������� ---
        DirectionalLight { eulerRotation: Qt.vector3d(-30, -45, 0); brightness: 1.5 }
        DirectionalLight { eulerRotation: Qt.vector3d( 30, 135, 0); brightness: 1.0 }

        // === ��������� (U-�������� ����) ===
        readonly property real beamSize: 100
        readonly property real frameHeight: 600
        readonly property real frameLength: 2000

        Node {
            id: frame
            // ������ �����
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize/2, view3d.frameLength/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.beamSize/100, view3d.frameLength/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
            // ������ ������
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
            // ������ ������
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.frameLength - view3d.beamSize/2)
                scale: Qt.vector3d(view3d.beamSize/100, view3d.frameHeight/100, view3d.beamSize/100)
                materials: PrincipledMaterial { baseColor: "#999999"; metalness: 0.7; roughness: 0.3 }
            }
        }

        // === ����� �������� � ����������� ��������� ===
        Node {
            id: suspensionArm
            // ����� ��������� �� ���� (�������� ����� ����)
            position: Qt.vector3d(-400, view3d.beamSize, view3d.beamSize/2)
            
            // ������� ������ ������ ����� ��������� (������ ��� Z)
            eulerRotation: Qt.vector3d(0, 0, root.suspensionAngle)
            
            // === ������ ������ (��� ��������� � ���� �������� Z) ===
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(0, 0, 0)
                scale: Qt.vector3d(0.8, 0.8, 1.2)  
                // �����: ������� ��� ��������� �� ��� Z (�� ���������), 
                // ��� ��������� � ���� �������� ������
                eulerRotation: Qt.vector3d(0, 0, 0)  // �� ��� Z
                materials: PrincipledMaterial { 
                    baseColor: "#ffff00"  // Ƹ���� ������ ������
                    metalness: 0.9
                    roughness: 0.1 
                }
            }
            
            // === ����� (�������� �����) ===
            Model {
                source: "#Cube"
                position: Qt.vector3d(-200, -100, 0)  // ����� ��������� ���� � � �������
                scale: Qt.vector3d(4, 0.6, 0.8)      // ������� � ������
                materials: PrincipledMaterial { 
                    baseColor: "#ff6600"  // ��������� ��� ���������
                    metalness: 0.8
                    roughness: 0.2 
                }
            }
            
            // === ������ ����� (����� �� ��� Z) ===
            Model {
                source: "#Cylinder"
                position: Qt.vector3d(-400, -200, 0)  // �� ����� ������
                scale: Qt.vector3d(0.6, 0.6, 1.0)     // ������ ������� ������
                // �����: ������ ����� ���� �� ��� Z ��� ���������������
                eulerRotation: Qt.vector3d(0, 0, 0)   // �� ��� Z
                materials: PrincipledMaterial { 
                    baseColor: "#00ff00"  // ������ ������ �����
                    metalness: 0.9
                    roughness: 0.1 
                }
            }
        }

        // ������������ ���
        Node {
            id: axes
            // X (�������)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(300, 0, 0); scale: Qt.vector3d(0.2, 0.2, 6); eulerRotation.y: 90
                materials: PrincipledMaterial { baseColor: "#ff0000"; lighting: PrincipledMaterial.NoLighting }
            }
            // Y (������)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(0, 300, 0); scale: Qt.vector3d(0.2, 6, 0.2)
                materials: PrincipledMaterial { baseColor: "#00ff00"; lighting: PrincipledMaterial.NoLighting }
            }
            // Z (�����)
            Model {
                source: "#Cylinder"; position: Qt.vector3d(0, 0, 300); scale: Qt.vector3d(0.2, 0.2, 6)
                materials: PrincipledMaterial { baseColor: "#0000ff"; lighting: PrincipledMaterial.NoLighting }
            }
            // ������ ���������
            Model {
                source: "#Sphere"; position: Qt.vector3d(0, 0, 0); scale: Qt.vector3d(0.8, 0.8, 0.8)
                materials: PrincipledMaterial { baseColor: "#ffffff"; lighting: PrincipledMaterial.NoLighting }
            }
        }
    }

    // === �������� ===
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

    // === ����/���������� ===
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
                // --- �������� (������) ---
                root.yawDeg   = root.normAngleDeg(root.yawDeg   + dx * root.rotateSpeed * accel)
                root.pitchDeg = root.clamp(root.pitchDeg - dy * root.rotateSpeed * accel, -85, 85)
            } else if (root.mouseButton === Qt.RightButton) {
                // --- ��������������� ---
                // 1) ������� ������� ������ ������������� 1 ������� �� ���������
                const fovRad = camera.fieldOfView * Math.PI / 180.0
                const worldPerPixel = (2 * root.cameraDistance * Math.tan(fovRad / 2)) / view3d.height

                // 2) ������� ������: forward, right, up � ���� �� �������� yaw/pitch
                const yaw  = root.yawDeg   * Math.PI / 180.0
                const pit  = root.pitchDeg * Math.PI / 180.0
                const cp = Math.cos(pit), sp = Math.sin(pit)
                const cy = Math.cos(yaw), sy = Math.sin(yaw)

                // forward (������������)
                const fx =  sy * cp
                const fy = -sp
                const fz = -cy * cp

                // right = normalize(cross(forward, up(0,1,0))) = (-fz, 0, fx) (������������ ���)
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

                // 3) �������� ����
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
            // ���������������� ���
            const accel = (wheel.modifiers & Qt.ControlModifier) ? 1.8
                         : (wheel.modifiers & Qt.ShiftModifier) ? 0.6 : 1.0
            const factor = Math.exp(-wheel.angleDelta.y * root.wheelZoomK * accel)
            root.cameraDistance = root.clamp(root.cameraDistance * factor, root.minDistance, root.maxDistance)
        }

        onDoubleClicked: {
            // ����� �� ������� ���
            resetView()
        }
    }

    Keys.onPressed: (e) => {
        if (e.key === Qt.Key_R) resetView()
        else if (e.key === Qt.Key_Space) {
            // �����/������������� ��������
            suspensionAnimation.running = !suspensionAnimation.running
        }
    }

    function resetView() {
        // ����� �� ����: �������� ����� ��������
        root.target = Qt.vector3d(0, view3d.beamSize + view3d.frameHeight/2, view3d.frameLength/2)
        root.cameraDistance = 4000
        root.yawDeg = 30
        root.pitchDeg = -20
    }

    focus: true

    // �������������� ������
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 15
        width: 420; height: 132
        color: "#aa000000"; border.color: "#60ffffff"; radius: 6

        Column {
            anchors.centerIn: parent; spacing: 4
            Text { text: "������������� | ���������� ��� ��������"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "?? ��� ��������� ��������� � ���� �������� Z"; color: "#ffaa00"; font.pixelSize: 12 }
            Text { text: "?? Ƹ���� ������ ������ | ?? ������ ������ �����"; color: "#cccccc"; font.pixelSize: 11 }
            Text { text: "��� � ��������, ��� � ���������������, ������ � ���"; color: "#cccccc"; font.pixelSize: 10 }
            Text { text: "R � ����� | ������ � ����� �������� | Ctrl � �������"; color: "#cccccc"; font.pixelSize: 9 }
        }
    }

    Component.onCompleted: {
        // ��������� ������� �� ���������
        resetView()
        console.log("������������� 3D: ������� � ���������� ����������� �� ��� Z")
    }
}
