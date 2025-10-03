import QtQuick
import QtQuick3D

/*
 * FIXED: Proper layering - Item root with View3D and 2D overlay
 */
Item {
    id: root
    anchors.fill: parent
    
    // 3D View (background layer)
    View3D {
        id: view3d
        anchors.fill: parent
        
        // Темный фон для контраста
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a2e"  // Темно-синий
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        // Камера - смотрит на сферу
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 5)  // 5 метров от центра
            eulerRotation: Qt.vector3d(0, 0, 0)  // Прямо вперед
        }
        
        // Свет - чтобы сферу было видно
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: 30
            brightness: 1.0
        }
        
        // ОКРУЖНОСТЬ (3D СФЕРА)
        Model {
            id: sphere
            source: "#Sphere"  // Встроенная примитивная сфера
            
            // Позиция в центре (0, 0, 0)
            position: Qt.vector3d(0, 0, 0)
            
            // Размер - радиус 1 метр
            scale: Qt.vector3d(1, 1, 1)
            
            // Красный цвет для видимости
            materials: PrincipledMaterial {
                baseColor: "#ff4444"  // Ярко-красный
                metalness: 0.0
                roughness: 0.5
            }
            
            // АНИМАЦИЯ: Вращение вокруг оси Y (вертикально)
            NumberAnimation on eulerRotation.y {
                from: 0      // Начало: 0 градусов
                to: 360      // Конец: 360 градусов (полный оборот)
                duration: 3000  // 3 секунды на оборот
                loops: Animation.Infinite  // Бесконечное повторение
                running: true  // Запустить сразу
            }
        }
    }
    
    // 2D Overlay (foreground layer - ON TOP of 3D)
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 20
        width: 300
        height: 80
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5
        
        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            Text {
                text: "Простая вращающаяся окружность"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }
            
            Text {
                text: "3D сфера с анимацией"
                color: "#aaaaaa"
                font.pixelSize: 12
            }
            
            Text {
                text: "Qt Quick 3D (RHI/D3D11)"
                color: "#888888"
                font.pixelSize: 10
            }
        }
    }
}
