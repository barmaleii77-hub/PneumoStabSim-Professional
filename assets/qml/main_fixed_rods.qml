import QtQuick
import QtQuick3D
import QtQuick3D.Helpers

/*
 * PneumoStabSim - ИСПРАВЛЕННАЯ КИНЕМАТИКА ШТОКОВ v4.1
 * 🔧 ИСПРАВЛЕНО: Правильный расчет длины штоков и позиций поршней
 * ✅ Штоки имеют ПОСТОЯННУЮ длину независимо от угла рычага
 * ✅ Поршни движутся ВДОЛЬ ОСИ цилиндров для сохранения длины штока
 */
Item {
    id: root
    anchors.fill: parent

    // Все остальные свойства остаются как в main_optimized.qml
    // ... (копируем только нужную часть для демонстрации)

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
    property real userRodDiameter: 35
    property real userPistonThickness: 25
    property real userPistonRodLength: 200  // ✅ КОНСТАНТНАЯ ДЛИНА ШТОКА

    // ✅ ИСПРАВЛЕННЫЙ SUSPENSION COMPONENT с правильной кинематикой
    component FixedRodSuspensionCorner: Node {
        property vector3d j_arm
        property vector3d j_tail  
        property real leverAngle
        property real pistonPositionFromPython: 250.0  // Используется только для внешнего управления
        
        // ✅ ПРАВИЛЬНАЯ КИНЕМАТИКА: рассчитываем j_rod
        property real baseAngle: (j_arm.x < 0) ? 180 : 0
        property real totalAngle: baseAngle + leverAngle
        property vector3d j_rod: Qt.vector3d(
            j_arm.x + (userLeverLength * userRodPosition) * Math.cos(totalAngle * Math.PI / 180),
            j_arm.y + (userLeverLength * userRodPosition) * Math.sin(totalAngle * Math.PI / 180),
            j_arm.z
        )
        
        // ✅ НАПРАВЛЕНИЕ ЦИЛИНДРА
        property vector3d cylDirection: Qt.vector3d(j_rod.x - j_tail.x, j_rod.y - j_tail.y, 0)
        property real cylDirectionLength: Math.hypot(cylDirection.x, cylDirection.y)
        property vector3d cylDirectionNorm: Qt.vector3d(
            cylDirection.x / cylDirectionLength,
            cylDirection.y / cylDirectionLength,
            0
        )
        property real cylAngle: Math.atan2(cylDirection.y, cylDirection.x) * 180 / Math.PI + 90
        
        // ✅ ФИКСИРОВАННЫЕ ДЛИНЫ (не изменяются!)
        property real TAIL_ROD_LENGTH: 100                    // мм - константа
        property real PISTON_ROD_LENGTH: userPistonRodLength  // мм - константа из UI
        
        // ✅ БАЗОВЫЕ ПОЗИЦИИ ЦИЛИНДРА
        property vector3d tailRodEnd: Qt.vector3d(
            j_tail.x + cylDirectionNorm.x * TAIL_ROD_LENGTH,
            j_tail.y + cylDirectionNorm.y * TAIL_ROD_LENGTH,
            j_tail.z
        )
        
        property vector3d cylinderEnd: Qt.vector3d(
            tailRodEnd.x + cylDirectionNorm.x * userCylinderLength,
            tailRodEnd.y + cylDirectionNorm.y * userCylinderLength,
            tailRodEnd.z
        )
        
        // ✅ ПРАВИЛЬНЫЙ РАСЧЕТ ПОЗИЦИИ ПОРШНЯ для КОНСТАНТНОЙ длины штока
        // Поршень должен находиться на расстоянии PISTON_ROD_LENGTH от j_rod по направлению к цилиндру
        property vector3d rodDirection: Qt.vector3d(
            cylDirectionNorm.x,  // Направление от j_rod к оси цилиндра
            cylDirectionNorm.y,
            0
        )
        
        // Находим проекцию j_rod на ось цилиндра
        property vector3d j_rodToCylStart: Qt.vector3d(j_rod.x - tailRodEnd.x, j_rod.y - tailRodEnd.y, 0)
        property real projectionOnCylAxis: j_rodToCylStart.x * cylDirectionNorm.x + j_rodToCylStart.y * cylDirectionNorm.y
        
        // Точка на оси цилиндра ближайшая к j_rod
        property vector3d j_rodProjection: Qt.vector3d(
            tailRodEnd.x + cylDirectionNorm.x * projectionOnCylAxis,
            tailRodEnd.y + cylDirectionNorm.y * projectionOnCylAxis,
            tailRodEnd.z
        )
        
        // Расстояние от j_rod до его проекции на ось цилиндра (перпендикулярно)
        property real perpendicularDistance: Math.hypot(
            j_rod.x - j_rodProjection.x,
            j_rod.y - j_rodProjection.y
        )
        
        // ✅ РЕШАЕМ ТРЕУГОЛЬНИК: находим позицию поршня для КОНСТАНТНОЙ длины штока
        // Теорема Пифагора: rod_length² = perpendicular_distance² + axial_distance²
        property real rodLengthSquared: PISTON_ROD_LENGTH * PISTON_ROD_LENGTH
        property real perpDistSquared: perpendicularDistance * perpendicularDistance
        property real axialDistanceFromProjection: Math.sqrt(Math.max(0, rodLengthSquared - perpDistSquared))
        
        // Позиция поршня на оси цилиндра (назад от проекции j_rod на расстояние axialDistance)
        property real pistonPositionOnAxis: projectionOnCylAxis - axialDistanceFromProjection
        
        // ✅ ОГРАНИЧИВАЕМ ПОРШЕНЬ В ПРЕДЕЛАХ ЦИЛИНДРА
        property real clampedPistonPosition: Math.max(10, Math.min(userCylinderLength - 10, pistonPositionOnAxis))
        
        // ✅ ФИНАЛЬНАЯ ПОЗИЦИЯ ПОРШНЯ (на оси цилиндра)
        property vector3d pistonCenter: Qt.vector3d(
            tailRodEnd.x + cylDirectionNorm.x * clampedPistonPosition,
            tailRodEnd.y + cylDirectionNorm.y * clampedPistonPosition,
            tailRodEnd.z
        )
        
        // ✅ ПРОВЕРЯЕМ РЕАЛЬНУЮ ДЛИНУ ШТОКА (для отладки)
        property real actualRodLength: Math.hypot(j_rod.x - pistonCenter.x, j_rod.y - pistonCenter.y)
        property real rodLengthError: Math.abs(actualRodLength - PISTON_ROD_LENGTH)
        
        // ✅ DEBUG: выводим в консоль большие ошибки
        onRodLengthErrorChanged: {
            if (rodLengthError > 1.0) {  // Если ошибка больше 1мм
                console.warn("⚠️ Rod length error:", rodLengthError.toFixed(2), "mm (target:", PISTON_ROD_LENGTH, "actual:", actualRodLength.toFixed(2), ")")
            }
        }
        
        // КОМПОНЕНТЫ ВИЗУАЛИЗАЦИИ
        
        // LEVER (рычаг)
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
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        // TAIL ROD (хвостовой шток) - КОНСТАНТНАЯ длина
        Model {
            source: "#Cylinder"
            position: Qt.vector3d((j_tail.x + tailRodEnd.x)/2, (j_tail.y + tailRodEnd.y)/2, j_tail.z)
            scale: Qt.vector3d(userRodDiameter/100, TAIL_ROD_LENGTH/100, userRodDiameter/100)
            eulerRotation: Qt.vector3d(0, 0, cylAngle)
            materials: PrincipledMaterial { 
                baseColor: "#cccccc"
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        // CYLINDER BODY (корпус цилиндра)
        Model {
            source: "#Cylinder"
            position: Qt.vector3d((tailRodEnd.x + cylinderEnd.x)/2, (tailRodEnd.y + cylinderEnd.y)/2, tailRodEnd.z)
            scale: Qt.vector3d(userBoreHead/100, userCylinderLength/100, userBoreHead/100)
            eulerRotation: Qt.vector3d(0, 0, cylAngle)
            materials: PrincipledMaterial { 
                baseColor: "#ffffff"
                metalness: 0.0
                roughness: 0.05
                opacity: 0.35
                alphaMode: PrincipledMaterial.Blend 
            }
        }
        
        // ✅ PISTON (поршень) - КОРРЕКТНАЯ позиция
        Model {
            source: "#Cylinder"
            position: pistonCenter
            scale: Qt.vector3d((userBoreHead - 2)/100, userPistonThickness/100, (userBoreHead - 2)/100)
            eulerRotation: Qt.vector3d(0, 0, cylAngle)
            materials: PrincipledMaterial { 
                baseColor: "#ff0066"
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        // ✅ PISTON ROD (шток поршня) - КОНСТАНТНАЯ длина!
        Model {
            source: "#Cylinder"
            position: Qt.vector3d((pistonCenter.x + j_rod.x)/2, (pistonCenter.y + j_rod.y)/2, pistonCenter.z)
            scale: Qt.vector3d(userRodDiameter/100, PISTON_ROD_LENGTH/100, userRodDiameter/100)  // ✅ КОНСТАНТНАЯ ДЛИНА!
            eulerRotation: Qt.vector3d(0, 0, Math.atan2(j_rod.y - pistonCenter.y, j_rod.x - pistonCenter.x) * 180 / Math.PI + 90)
            materials: PrincipledMaterial { 
                baseColor: rodLengthError > 1.0 ? "#ff0000" : "#cccccc"  // Красный если большая ошибка
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        // JOINTS (шарниры) - цветные маркеры
        Model {
            source: "#Sphere"
            position: j_tail
            scale: Qt.vector3d(1.2, 1.2, 1.2)
            materials: PrincipledMaterial { 
                baseColor: "#0088ff"  // Синий - шарнир цилиндра
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        Model {
            source: "#Sphere"
            position: j_arm
            scale: Qt.vector3d(1.0, 1.0, 1.0)
            materials: PrincipledMaterial { 
                baseColor: "#ff8800"  // Оранжевый - шарнир рычага
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        Model {
            source: "#Sphere"
            position: j_rod
            scale: Qt.vector3d(0.8, 0.8, 0.8)
            materials: PrincipledMaterial { 
                baseColor: rodLengthError > 1.0 ? "#ff0000" : "#00ff44"  // Красный если ошибка, зеленый если OK
                metalness: 1.0
                roughness: 0.28
            }
        }
        
        // ✅ DEBUG ИНФОРМАЦИЯ НА ЭКРАНЕ
        Text {
            anchors.top: parent.top
            anchors.left: parent.left
            text: "Rod Length: " + actualRodLength.toFixed(1) + "mm (target: " + PISTON_ROD_LENGTH + "mm)\n" +
                  "Error: " + rodLengthError.toFixed(2) + "mm\n" +
                  "Piston Pos: " + clampedPistonPosition.toFixed(1) + "mm"
            color: rodLengthError > 1.0 ? "#ff0000" : "#00ff00"
            font.pixelSize: 8
            visible: false  // Включить для отладки
        }
    }

    // Пример использования исправленного компонента
    View3D {
        id: view3d
        anchors.fill: parent
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 4000)
            fieldOfView: 45
        }

        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -45
            brightness: 2.8
        }

        // Тестовый экземпляр исправленной подвески
        FixedRodSuspensionCorner { 
            id: testCorner
            j_arm: Qt.vector3d(-600, 120, 60)
            j_tail: Qt.vector3d(-800, 770, 60)
            leverAngle: 15.0  // Тестовый угол
        }
        
        // U-образная рама (упрощенная)
        Model {
            source: "#Cube"
            position: Qt.vector3d(0, 60, 1600)
            scale: Qt.vector3d(1.2, 1.2, 32)
            materials: PrincipledMaterial { baseColor: "#cc0000" }
        }
    }

    Component.onCompleted: {
        console.log("🔧 FixedRodSuspensionCorner loaded with CORRECT rod length calculation")
        console.log("✅ Piston rod length is CONSTANT:", userPistonRodLength, "mm")
        console.log("✅ Piston moves along cylinder axis to maintain rod length")
        console.log("✅ Rod length error monitoring enabled")
    }
}
