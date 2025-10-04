// MechCorner.qml - Один угол подвески (рычаг + цилиндр + шарниры + масса)
import QtQuick
import QtQuick3D
import "../components"

Node {
    id: corner

    // ========== ВХОДНЫЕ ПАРАМЕТРЫ (из Python) ==========
    // Рычаг
    property vector3d j_arm: Qt.vector3d(0, 0, 0)
    property real armLength: 500
    property real armAngleDeg: 0
    property real attachFrac: 0.7

    // Цилиндр
    property vector3d j_tail: Qt.vector3d(0, 0, 0)  // C
    property vector3d j_rod: Qt.vector3d(0, 0, 0)   // E
    property real bore_d: 80
    property real rod_d: 40
    property real L_body: 300
    property real piston_thickness: 20
    property real dead_bo_vol: 0.0001
    property real dead_sh_vol: 0.0001
    property real s_min: 50

    // Масса
    property real mass_unsprung: 50

    // ========== ВСПОМОГАТЕЛЬНЫЕ ВЫЧИСЛЕНИЯ ==========
    readonly property real A_bore: Math.PI * (bore_d * bore_d) / 4.0
    readonly property real A_ann: A_bore - Math.PI * (rod_d * rod_d) / 4.0
    readonly property real L_dead_sh: dead_sh_vol / (A_ann || 1e-9)
    readonly property real L_dead_bo: dead_bo_vol / (A_bore || 1e-9)
    readonly property real L_eff: Math.max(0, L_body - piston_thickness)

    // Диапазон хода поршня с учётом мёртвых зон
    readonly property real x_min: L_dead_sh
    readonly property real x_max: Math.max(x_min, L_eff - L_dead_bo)

    // ========== РЫЧАГ ==========
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

    // ========== ЦИЛИНДР ГЕОМЕТРИЯ ==========
    readonly property vector3d v_CE: Qt.vector3d(
        j_rod.x - j_tail.x,
        j_rod.y - j_tail.y,
        j_rod.z - j_tail.z
    )
    readonly property real L_pin: Math.hypot(v_CE.x, v_CE.y, v_CE.z)
    readonly property vector3d u: Qt.vector3d(
        v_CE.x / (L_pin || 1e-9),
        v_CE.y / (L_pin || 1e-9),
        v_CE.z / (L_pin || 1e-9)
    )

    // Хвостовик: короткий патрубок C -> R
    readonly property real L_tail: Math.min(0.15 * L_body, 0.2 * bore_d)
    readonly property vector3d R: Qt.vector3d(
        j_tail.x + u.x * L_tail,
        j_tail.y + u.y * L_tail,
        j_tail.z + u.z * L_tail
    )
    readonly property vector3d F: Qt.vector3d(
        R.x + u.x * L_body,
        R.y + u.y * L_body,
        R.z + u.z * L_body
    )

    // Текущий ход поршня (упрощённо: из геометрии pin-to-pin)
    readonly property real x_req: Math.max(x_min, Math.min(x_max, L_pin - L_tail - s_min))
    readonly property real x: x_req

    // Наружный вылет штока
    readonly property real s: s_min + (x - x_min)

    // Позиции поршня
    readonly property vector3d P_front: Qt.vector3d(
        F.x - u.x * x,
        F.y - u.y * x,
        F.z - u.z * x
    )
    readonly property vector3d P_back: Qt.vector3d(
        P_front.x - u.x * piston_thickness,
        P_front.y - u.y * piston_thickness,
        P_front.z - u.z * piston_thickness
    )

    // ========== УТИЛИТЫ ВЫРАВНИВАНИЯ ==========
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

    // ========== ВИЗУАЛИЗАЦИЯ ==========

    // Рычаг
    Model {
        id: lever
        source: "#Cube"
        materials: Materials.steel
        Component.onCompleted: placeYBetween(lever, j_arm, lever_end, 0.5 * bore_d, 100)
    }

    // Шарнир рычага (цилиндр по Z)
    Model {
        source: "#Cylinder"
        materials: Materials.steel
        eulerRotation.x: 90
        position: j_arm
        scale: Qt.vector3d((bore_d * 0.6) / 100, 0.2, (bore_d * 0.6) / 100)
    }

    // Хвостовик цилиндра
    Model {
        id: tail
        source: "#Cylinder"
        materials: Materials.steel
        Component.onCompleted: placeYBetween(tail, j_tail, R, 0.35 * bore_d, 100)
    }

    // Корпус цилиндра (стекло, R -> F)
    Model {
        id: barrel
        source: "#Cylinder"
        materials: Materials.glass
        Component.onCompleted: placeYBetween(barrel, R, F, 0.55 * bore_d, 100)
    }

    // Крышка задняя (R)
    Model {
        id: capRear
        source: "#Cylinder"
        materials: Materials.steelThin
        Component.onCompleted: {
            const R1 = Qt.vector3d(R.x + u.x * 0.001, R.y + u.y * 0.001, R.z + u.z * 0.001)
            placeYBetween(capRear, R, R1, 0.56 * bore_d, 100)
        }
    }

    // Крышка передняя (F)
    Model {
        id: capFront
        source: "#Cylinder"
        materials: Materials.steelThin
        Component.onCompleted: {
            const F1 = Qt.vector3d(F.x + u.x * 0.001, F.y + u.y * 0.001, F.z + u.z * 0.001)
            placeYBetween(capFront, F, F1, 0.56 * bore_d, 100)
        }
    }

    // Поршень (диск с толщиной)
    Model {
        id: piston
        source: "#Cylinder"
        materials: Materials.steel
        Component.onCompleted: placeYBetween(piston, P_back, P_front, 0.54 * bore_d, 100)
    }

    // Шток (видимая часть F -> E)
    Model {
        id: rod
        source: "#Cylinder"
        materials: Materials.chrome
        Component.onCompleted: placeYBetween(rod, F, j_rod, 0.5 * rod_d, 100)
    }

    // Шарнир хвостовика (C)
    Model {
        source: "#Cylinder"
        materials: Materials.steel
        eulerRotation.x: 90
        position: j_tail
        scale: Qt.vector3d((bore_d * 0.6) / 100, 0.2, (bore_d * 0.6) / 100)
    }

    // Шарнир штока (E)
    Model {
        source: "#Cylinder"
        materials: Materials.steel
        eulerRotation.x: 90
        position: j_rod
        scale: Qt.vector3d((bore_d * 0.5) / 100, 0.2, (bore_d * 0.5) / 100)
    }

    // Масса (сфера ? ?m)
    Model {
        source: "#Sphere"
        position: lever_end
        scale: Qt.vector3d(1, 1, 1).times(
            Math.max(0.05, 0.12 * Math.sqrt(Math.max(mass_unsprung, 0)))
        )
        materials: Materials.massSphere
    }
}
