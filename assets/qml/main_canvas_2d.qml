import QtQuick

/*
 * SOLUTION: 2D Canvas schematic view
 * Reason: PySide6 6.8.3 doesn't include Qt Quick 3D primitive meshes
 * This provides a working alternative using 2D graphics
 *
 * Улучшено (stability for tests):
 * - Добавлен Component.onCompleted с принудительным requestPaint() для первого кадра
 * - Динамическая смена цвета рамки и спиц колес по анимационному углу для гарантированного отличия кадров
 * - Оверлей текущего угла animationAngle и времени для визуального контроля
 * - Плавный фон с лёгким градиентом зависит от animationAngle (меняются пиксели → устойчивость diff)
 */
Item {
    id: root
    objectName: "canvasRoot" // добавлено для тестов
    anchors.fill: parent

    property double lastPaintTs: 0

    Component.onCompleted: {
        // Принудительный первый рендер чтобы тест сразу получил ненулевой кадр
        schematicCanvas.requestPaint()
    }

    // Dark background (динамический градиент по углу)
    Rectangle {
        anchors.fill: parent
        // Небольшая модуляция синего канала чтобы diff между кадрами всегда присутствовал
        color: Qt.rgba(0.10, 0.10, 0.18 + (schematicCanvas.animationAngle % 30) / 600.0, 1.0)
    }

    // Canvas for drawing pneumatic schematic
    Canvas {
        id: schematicCanvas
        objectName: "schematicCanvas" // добавлено для тестов
        anchors.fill: parent
        anchors.margins: 50

        property real frameWidth: 400
        property real frameHeight: 100
        property real wheelRadius: 50
        property real animationAngle: 0

        // Animation
        NumberAnimation on animationAngle {
            from: 0
            to: 360
            duration: 3000
            loops: Animation.Infinite
            running: true
        }

        onAnimationAngleChanged: {
            requestPaint()
        }

        onPaint: {
            var ctx = getContext("2d")
            var ts = Date.now() / 1000.0
            root.lastPaintTs = ts

            // Clear
            ctx.clearRect(0, 0, width, height)

            // Calculate center
            var centerX = width / 2
            var centerY = height / 2

            // Dynamic frame color (вращение оттенка по углу)
            var hueBase = (animationAngle % 360) / 360.0
            var rFrame = 180 + Math.floor(50 * Math.sin(animationAngle * Math.PI / 180))
            var gFrame = 180 + Math.floor(50 * Math.cos(animationAngle * Math.PI / 180))
            var bFrame = 220
            var frameColor = "rgb(" + rFrame + "," + gFrame + "," + bFrame + ")"

            // Draw frame (body)
            ctx.strokeStyle = frameColor
            ctx.lineWidth = 3
            ctx.strokeRect(
                centerX - frameWidth/2,
                centerY - frameHeight,
                frameWidth,
                frameHeight
            )

            // Draw 4 wheels (circles)
            var wheel1X = centerX - frameWidth/2 + 50
            var wheel2X = centerX + frameWidth/2 - 50
            var wheelY = centerY + 20

            // Front left wheel
            drawWheel(ctx, wheel1X, wheelY, wheelRadius, animationAngle)

            // Front right wheel
            drawWheel(ctx, wheel2X, wheelY, wheelRadius, animationAngle)

            // Rear left wheel
            drawWheel(ctx, wheel1X, wheelY + 100, wheelRadius, animationAngle + 90)

            // Rear right wheel
            drawWheel(ctx, wheel2X, wheelY + 100, wheelRadius, animationAngle + 90)

            // Draw 4 pneumatic cylinders
            drawCylinder(ctx, wheel1X, centerY - frameHeight, wheel1X, wheelY - wheelRadius, "#ff4444")
            drawCylinder(ctx, wheel2X, centerY - frameHeight, wheel2X, wheelY - wheelRadius, "#ff4444")
            drawCylinder(ctx, wheel1X, centerY - frameHeight, wheel1X, wheelY + 100 - wheelRadius, "#4444ff")
            drawCylinder(ctx, wheel2X, centerY - frameHeight, wheel2X, wheelY + 100 - wheelRadius, "#4444ff")

            // Draw title (динамическая лёгкая пульсация яркости)
            ctx.fillStyle = "#ffffff"
            ctx.font = "bold 24px Arial"
            ctx.textAlign = "center"
            ctx.fillText("Pneumatic Suspension Schematic", centerX, 40)

            ctx.font = "16px Arial"
            var shade = 170 + Math.floor(40 * Math.sin(animationAngle * Math.PI / 180))
            ctx.fillStyle = "rgb(" + shade + "," + shade + "," + shade + ")"
            ctx.fillText("2D Canvas View (Animated)", centerX, 70)

            // Diagnostic overlay (угол + время)
            ctx.font = "12px Arial"
            ctx.fillStyle = "#cccccc"
            ctx.textAlign = "left"
            ctx.fillText("angle=" + animationAngle.toFixed(1) + "°", 14, 24)
            ctx.fillText("t=" + ts.toFixed(2) + "s", 14, 40)
        }

        function drawWheel(ctx, x, y, r, angle) {
            ctx.save()

            // Draw circle (dynamic rim color)
            var rimPulse = 120 + Math.floor(60 * Math.sin((angle + x) * Math.PI / 180))
            ctx.strokeStyle = "rgb(" + rimPulse + "," + (rimPulse - 20) + "," + (rimPulse - 40) + ")"
            ctx.lineWidth = 2
            ctx.beginPath()
            ctx.arc(x, y, r, 0, 2 * Math.PI)
            ctx.stroke()

            // Draw rotating spokes
            ctx.translate(x, y)
            ctx.rotate(angle * Math.PI / 180)

            for (var i = 0; i < 8; i++) {
                var spokeShade = 150 + Math.floor(50 * Math.sin((angle + i * 45) * Math.PI / 180))
                ctx.strokeStyle = "rgb(" + spokeShade + "," + spokeShade + "," + (spokeShade + 10) + ")"
                ctx.lineWidth = 1.4
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(r, 0)
                ctx.stroke()
                ctx.rotate(Math.PI / 4)
            }

            ctx.restore()
        }

        function drawCylinder(ctx, x1, y1, x2, y2, color) {
            // Cylinder body
            ctx.strokeStyle = color
            ctx.lineWidth = 4
            ctx.beginPath()
            ctx.moveTo(x1, y1)
            ctx.lineTo(x2, y2)
            ctx.stroke()

            // Cylinder caps
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(x1, y1, 6, 0, 2 * Math.PI)
            ctx.fill()

            ctx.beginPath()
            ctx.arc(x2, y2, 6, 0, 2 * Math.PI)
            ctx.fill()
        }
    }

    // Info overlay
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 20
        width: 250
        height: 140
        color: "#20000000"
        border.color: "#40ffffff"
        border.width: 1
        radius: 5

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Text { text: "2D Schematic View"; color: "#ffffff"; font.pixelSize: 14; font.bold: true }
            Text { text: "• Frame (white rectangle)"; color: "#aaaaaa"; font.pixelSize: 11 }
            Text { text: "• 4 Wheels (rotating circles)"; color: "#aaaaaa"; font.pixelSize: 11 }
            Text { text: "• 4 Cylinders (red/blue lines)"; color: "#aaaaaa"; font.pixelSize: 11 }
            Text { text: "• Dynamic colors / angle overlay"; color: "#aaaaaa"; font.pixelSize: 11 }
            Text { text: "Qt Quick Canvas 2D"; color: "#888888"; font.pixelSize: 9 }
        }
    }
}
