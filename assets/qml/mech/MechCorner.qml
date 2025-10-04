# ���������������� MECHCORNER.QML - ������ � ������������ �������� ����������� �������� �� ���
// MechCorner.qml - ���� ���� �������� (����� + ������� + ������� + �����)
import QtQuick
import QtQuick3D
import "../components"

Node {
    id: corner

    // ========== ������� ��������� (�� Python) ==========
    // �����
    property vector3d j_arm: Qt.vector3d(0, 0, 0)
    property real armLength: 500
    property real armAngleDeg: 0
    property real attachFrac: 0.7

    // �������
    property vector3d j_tail: Qt.vector3d(0, 0, 0)  // C
    property vector3d j_rod: Qt.vector3d(0, 0, 0)   // E
    property real bore_d: 80
    property real rod_d: 40
    property real L_body: 300
    property real piston_thickness: 20
    property real dead_bo_vol: 0.0001
    property real dead_sh_vol: 0.0001
    property real s_min: 50

    // �����
    property real mass_unsprung: 50

    // ========== ��������������� ���������� ==========
    readonly property real A_bore: Math.PI * (bore_d * bore_d) / 4.0
    readonly property real A_ann: A_bore - Math.PI * (rod_d * rod_d) / 4.0
    readonly property real L_dead_sh: dead_sh_vol / (A_ann || 1e-9)
    readonly property real L_dead_bo: dead_bo_vol / (A_bore || 1e-9)
    readonly property real L_eff: Math.max(0, L_body - piston_thickness)

    // �������� ���� ������ � ������ ������ ���
    readonly property real x_min: L_dead_sh
    readonly property real x_max: Math.max(x_min, L_eff - L_dead_bo)

    // ========== ����� ==========
    readonly property vector3d lever_end: Qt.vector3d(
        j_arm.x + armLength * Math.cos(armAngleDeg * Math.PI / 180),
        j_arm.y + armLength * Math.sin(armAngleDeg * Math.PI / 180),
        j_arm.z
    )

    readonly property vector3d j_attach: Qt.vector3d(
        j_arm.x + armLength * attachFrac * Math.cos(armAngleDeg * Math.PI / 180),
        j_arm.y + armLength * attachFrac * Math.sin(armAngleDeg * Math.PI / 180),
        j_arm.z
    )

    // ========== ������� ��������� ==========
    
            // ��������������� ����������
            readonly property vector3d v_CE: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, j_rod.z - j_tail.z)
            readonly property real lPin: Math.hypot(v_CE.x, v_CE.y, v_CE.z)
            readonly property vector3d u: Qt.vector3d(v_CE.x / (lPin || 1e-9), v_CE.y / (lPin || 1e-9), v_CE.z / (lPin || 1e-9))

            // ���������: �������� �������� C -> R
            readonly property real lTail: Math.min(0.15 * lBody, 0.2 * bore_d)
            readonly property vector3d rPoint: Qt.vector3d(j_tail.x + u.x * lTail, j_tail.y + u.y * lTail, j_tail.z + u.z * lTail)
            readonly property vector3d fPoint: Qt.vector3d(rPoint.x + u.x * lBody, rPoint.y + u.y * lBody, rPoint.z + u.z * lBody)

            // ������������ ������ ������ - ������� ������ �������
            readonly property real x: lBody * 0.5  // 50% ���� �� ������ ������ (��������)
            readonly property vector3d pBack: Qt.vector3d(rPoint.x + u.x * x, rPoint.y + u.y * x, rPoint.z + u.z * x)
            readonly property vector3d pFront: Qt.vector3d(pBack.x + u.x * piston_thickness, pBack.y + u.y * piston_thickness, pBack.z + u.z * piston_thickness)

            // ��������: ����� ������ ������ ��������� � ������� �����
            readonly property vector3d piston_center: Qt.vector3d((pBack.x + pFront.x) / 2, (pBack.y + pFront.y) / 2, (pBack.z + pFront.z) / 2)
            readonly property vector3d rod_start: fPoint  // ���� ���������� �� �������� ������
            
            Component.onCompleted: {
                console.log(`=== ${corner || "?"} CYLINDER GEOMETRY ===`)
                console.log(`j_tail: (${j_tail.x.toFixed(0)}, ${j_tail.y.toFixed(0)}, ${j_tail.z.toFixed(0)})`)
                console.log(`rPoint: (${rPoint.x.toFixed(0)}, ${rPoint.y.toFixed(0)}, ${rPoint.z.toFixed(0)})`)
                console.log(`fPoint: (${fPoint.x.toFixed(0)}, ${fPoint.y.toFixed(0)}, ${fPoint.z.toFixed(0)})`)
                console.log(`piston_center: (${piston_center.x.toFixed(0)}, ${piston_center.y.toFixed(0)}, ${piston_center.z.toFixed(0)})`)
                console.log(`j_rod: (${j_rod.x.toFixed(0)}, ${j_rod.y.toFixed(0)}, ${j_rod.z.toFixed(0)})`)
                console.log(`rod_length: ${Math.hypot(j_rod.x - fPoint.x, j_rod.y - fPoint.y, j_rod.z - fPoint.z).toFixed(1)}`)
            }

    // ========== ������� ������������ ==========
    function alignYToVector(node, v) {
        const Y = Qt.vector3d(0, 1, 0)
        const len = Math.hypot(v.x, v.y, v.z)
        if (len < 1e-9) return

        const vn = Qt.vector3d(v.x / len, v.y / len, v.z / len)
        const ax = Qt.vector3d(
            Y.y * vn.z - Y.z * vn.y,
            Y.z * vn.x - Y.x * vn.z,
            Y.x * vn.y - Y.y * vn.x
        )
        const axLen = Math.hypot(ax.x, ax.y, ax.z)

        if (axLen < 1e-9) {
            // Parallel or antiparallel to Y
            if (vn.y < 0) {
                node.eulerRotation = Qt.vector3d(180, 0, 0)
            } else {
                node.eulerRotation = Qt.vector3d(0, 0, 0)
            }
            return
        }

        const axis = Qt.vector3d(ax.x / axLen, ax.y / axLen, ax.z / axLen)
        const dot = Math.max(-1, Math.min(1, Y.x * vn.x + Y.y * vn.y + Y.z * vn.z))
        const angle = Math.acos(dot) * 180 / Math.PI
        
        // Use eulerRotation instead of quaternion for simplicity
        // Convert axis-angle to euler (simplified: assume rotation around single axis)
        node.eulerRotation.x = axis.x * angle
        node.eulerRotation.y = axis.y * angle
        node.eulerRotation.z = axis.z * angle
    }

    function placeYBetween(node, A, B, radius, unit) {
        const v = Qt.vector3d(B.x - A.x, B.y - A.y, B.z - A.z)
        const L = Math.hypot(v.x, v.y, v.z)

        node.position = Qt.vector3d(
            (A.x + B.x) / 2,
            (A.y + B.y) / 2,
            (A.z + B.z) / 2
        )

        alignYToVector(node, v)

        node.scale = Qt.vector3d(
            (radius * 2) / unit,
            L / unit,
            (radius * 2) / unit
        )
    }

            // ������� ���������� �������� �� ��� - ������������ ������
            function placeAlongAxis(node, A, B, radius) {
                const v = Qt.vector3d(B.x - A.x, B.y - A.y, B.z - A.z)
                const L = Math.hypot(v.x, v.y, v.z)
                
                if (L < 1e-6) {
                    node.scale = Qt.vector3d(0.01, 0.01, 0.01)
                    return
                }
                
                // ����� �������� - �������� ����� A � B
                node.position = Qt.vector3d((A.x + B.x) / 2, (A.y + B.y) / 2, (A.z + B.z) / 2)
                
                // ����������� �� A � B (���������������)
                const vn = Qt.vector3d(v.x / L, v.y / L, v.z / L)
                
                // ������������: ������� ������������ �������� (��� Y) � ����������� vn
                const yaw = Math.atan2(vn.x, vn.z) * 180 / Math.PI
                const pitch = -Math.asin(vn.y) * 180 / Math.PI
                
                node.eulerRotation = Qt.vector3d(pitch, yaw, 0)
                
                // �������: ������� � XZ, ����� � Y
                const scale_factor = 100.0
                node.scale = Qt.vector3d(
                    (radius * 2) / scale_factor,  // ������� X
                    L / scale_factor,             // ����� Y
                    (radius * 2) / scale_factor   // ������� Z
                )
                
                console.log(`placeAlongAxis: A=(${A.x.toFixed(0)},${A.y.toFixed(0)},${A.z.toFixed(0)}), B=(${B.x.toFixed(0)},${B.y.toFixed(0)},${B.z.toFixed(0)}), L=${L.toFixed(1)}`)
            }

            // ===== ���������� ������� =====
            // ������ j_arm (������) - ��������� ������ � ����
            Model {
                source: "#Sphere"
                position: j_arm
                scale: Qt.vector3d(0.3, 0.3, 0.3)
                materials: PrincipledMaterial {
                    baseColor: "#00ff00"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // ������ j_tail (�����) - ��������� �������� � ����
            Model {
                source: "#Sphere"
                position: j_tail
                scale: Qt.vector3d(0.3, 0.3, 0.3)
                materials: PrincipledMaterial {
                    baseColor: "#0000ff"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // ������ j_rod (�������) - ��������� ����� � ������
            Model {
                source: "#Sphere"
                position: j_rod
                scale: Qt.vector3d(0.3, 0.3, 0.3)
                materials: PrincipledMaterial {
                    baseColor: "#ff0000"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            
            // ������ lever_end (�����) - ����� ������ (�����)
            Model {
                source: "#Sphere"
                position: lever_end
                scale: Qt.vector3d(0.3, 0.3, 0.3)
                materials: PrincipledMaterial {
                    baseColor: "#ffff00"
                    lighting: PrincipledMaterial.NoLighting
                }
            }

            // ===== ����� =====
            Model {
                id: lever
                source: "#Cube"
                materials: steel
                Component.onCompleted: placeAlongAxis(lever, j_arm, lever_end, 0.3 * bore_d)
            }

            // ������ ������ (������� �� Z) - ���������
            Model {
                source: "#Cylinder"
                materials: steel
                position: j_arm
                scale: Qt.vector3d((bore_d * 0.6) / 100, 0.15, (bore_d * 0.6) / 100)
                // ��� �������� - ��� Z �� ���������
            }

            // ===== ������� - ���������� ��������� =====
            
            // ��������� (�������� C -> R)
            Model {
                id: tail
                source: "#Cylinder"
                materials: steel
                Component.onCompleted: placeAlongAxis(tail, j_tail, rPoint, 0.35 * bore_d)
            }

            // ������ �������� (������, R -> F) - ���������
            Model {
                id: barrel
                source: "#Cylinder" 
                materials: glass
                Component.onCompleted: placeAlongAxis(barrel, rPoint, fPoint, 0.55 * bore_d)
            }

            // ������ ������ (R) - ������� �� Z
            Model {
                source: "#Cylinder"
                materials: steelThin
                position: rPoint
                scale: Qt.vector3d((bore_d * 0.56) / 100, 0.05, (bore_d * 0.56) / 100)
                // ��� �������� - ������� ������
            }

            // ������ �������� (F) - ������� �� Z  
            Model {
                source: "#Cylinder"
                materials: steelThin
                position: fPoint
                scale: Qt.vector3d((bore_d * 0.56) / 100, 0.05, (bore_d * 0.56) / 100)
                // ��� �������� - ������� ������
            }

            // ������� (���� � ��������) - ���������
            Model {
                id: piston
                source: "#Cylinder"
                materials: steel
                Component.onCompleted: placeAlongAxis(piston, pBack, pFront, 0.54 * bore_d)
            }

            // ���� (������� ����� F -> E) - ���������
            Model {
                id: rod
                source: "#Cylinder"
                materials: chrome
                Component.onCompleted: placeAlongAxis(rod, fPoint, j_rod, 0.5 * rod_d)
            }

            // ������ ���������� (C) - ������� �� Z
            Model {
                source: "#Cylinder"
                materials: steel
                position: j_tail
                scale: Qt.vector3d((bore_d * 0.6) / 100, 0.15, (bore_d * 0.6) / 100)
                // ��� �������� - ��� Z
            }

            // ������ ����� (E) - ������� �� Z
            Model {
                source: "#Cylinder"
                materials: steel
                position: j_rod
                scale: Qt.vector3d((bore_d * 0.5) / 100, 0.15, (bore_d * 0.5) / 100)
                // ��� �������� - ��� Z
            }
