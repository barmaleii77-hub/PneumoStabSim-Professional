import QtQuick

/*
 * FALLBACK SOLUTION: Enhanced 2D Canvas with 3D-like effects
 * Reason: Qt Quick 3D custom geometry rendering issues
 * This provides professional-looking 2D visualization
 */
Item {
    id: root
    anchors.fill: parent

    // Dark background with gradient
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#1a1a2e" }
            GradientStop { position: 1.0; color: "#16213e" }
        }
    }

    // Enhanced Canvas for pneumatic schematic with 3D effects
    Canvas {
        id: schematicCanvas
        anchors.fill: parent
        anchors.margins: 50

        property real frameWidth: 400
        property real frameHeight: 120
        property real wheelRadius: 60
        property real animationAngle: 0
        property real breathingFactor: 0

        // Main rotation animation
        NumberAnimation on animationAngle {
            from: 0; to: 360; duration: 4000
            loops: Animation.Infinite; running: true
        }

        // Breathing effect for 3D-like appearance
        NumberAnimation on breathingFactor {
            from: 0; to: 1; duration: 2000
            loops: Animation.Infinite; running: true
            easing.type: Easing.InOutSine
        }

        onAnimationAngleChanged: requestPaint()
        onBreathingFactorChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            var centerX = width / 2
            var centerY = height / 2

            // Enhanced frame with 3D effect
            drawFrame3D(ctx, centerX, centerY)

            // Enhanced wheels with depth
            var wheel1X = centerX - frameWidth/2 + 60
            var wheel2X = centerX + frameWidth/2 - 60
            var wheelY = centerY + 30

            drawWheel3D(ctx, wheel1X, wheelY, wheelRadius, animationAngle)
            drawWheel3D(ctx, wheel2X, wheelY, wheelRadius, animationAngle)
            drawWheel3D(ctx, wheel1X, wheelY + 120, wheelRadius, animationAngle + 90)
            drawWheel3D(ctx, wheel2X, wheelY + 120, wheelRadius, animationAngle + 90)

            // Enhanced cylinders with animation
            drawCylinder3D(ctx, wheel1X, centerY - frameHeight, wheel1X, wheelY - wheelRadius, "#ff4444", breathingFactor)
            drawCylinder3D(ctx, wheel2X, centerY - frameHeight, wheel2X, wheelY - wheelRadius, "#ff4444", breathingFactor)
            drawCylinder3D(ctx, wheel1X, centerY - frameHeight, wheel1X, wheelY + 120 - wheelRadius, "#4444ff", 1 - breathingFactor)
            drawCylinder3D(ctx, wheel2X, centerY - frameHeight, wheel2X, wheelY + 120 - wheelRadius, "#4444ff", 1 - breathingFactor)

            // Enhanced title with glow
            drawTitle(ctx, centerX)
        }

        function drawFrame3D(ctx, centerX, centerY) {
            // Main frame with gradient
            var gradient = ctx.createLinearGradient(
                centerX - frameWidth/2, centerY - frameHeight,
                centerX + frameWidth/2, centerY
            )
            gradient.addColorStop(0, "#ffffff")
            gradient.addColorStop(0.5, "#cccccc")
            gradient.addColorStop(1, "#888888")

            ctx.strokeStyle = gradient
            ctx.lineWidth = 4
            ctx.strokeRect(
                centerX - frameWidth/2, centerY - frameHeight,
                frameWidth, frameHeight
            )

            // Inner shadow effect
            ctx.strokeStyle = "#666666"
            ctx.lineWidth = 1
            ctx.strokeRect(
                centerX - frameWidth/2 + 3, centerY - frameHeight + 3,
                frameWidth - 6, frameHeight - 6
            )
        }

        function drawWheel3D(ctx, x, y, r, angle) {
            ctx.save()

            // Wheel shadow
            ctx.fillStyle = "rgba(0, 0, 0, 0.3)"
            ctx.beginPath()
            ctx.arc(x + 3, y + 3, r, 0, 2 * Math.PI)
            ctx.fill()

            // Main wheel with gradient
            var gradient = ctx.createRadialGradient(x - r/3, y - r/3, 0, x, y, r)
            gradient.addColorStop(0, "#ffffff")
            gradient.addColorStop(0.7, "#dddddd")
            gradient.addColorStop(1, "#999999")

            ctx.fillStyle = gradient
            ctx.beginPath()
            ctx.arc(x, y, r, 0, 2 * Math.PI)
            ctx.fill()

            // Wheel rim
            ctx.strokeStyle = "#666666"
            ctx.lineWidth = 3
            ctx.beginPath()
            ctx.arc(x, y, r, 0, 2 * Math.PI)
            ctx.stroke()

            // Rotating spokes with depth
            ctx.translate(x, y)
            ctx.rotate(angle * Math.PI / 180)

            for (var i = 0; i < 8; i++) {
                // Spoke shadow
                ctx.strokeStyle = "rgba(0, 0, 0, 0.3)"
                ctx.lineWidth = 3
                ctx.beginPath()
                ctx.moveTo(2, 2)
                ctx.lineTo(r - 5, 2)
                ctx.stroke()

                // Main spoke
                ctx.strokeStyle = "#555555"
                ctx.lineWidth = 2
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(r - 5, 0)
                ctx.stroke()

                ctx.rotate(Math.PI / 4)
            }

            ctx.restore()
        }

        function drawCylinder3D(ctx, x1, y1, x2, y2, color, extension) {
            // Calculate extended position for breathing effect
            var dx = x2 - x1
            var dy = y2 - y1
            var length = Math.sqrt(dx * dx + dy * dy)
            var extendedLength = length * (1 + extension * 0.2)

            var newX2 = x1 + (dx / length) * extendedLength
            var newY2 = y1 + (dy / length) * extendedLength

            // Cylinder shadow
            ctx.strokeStyle = "rgba(0, 0, 0, 0.3)"
            ctx.lineWidth = 6
            ctx.beginPath()
            ctx.moveTo(x1 + 2, y1 + 2)
            ctx.lineTo(newX2 + 2, newY2 + 2)
            ctx.stroke()

            // Main cylinder with gradient
            var gradient = ctx.createLinearGradient(x1, y1, newX2, newY2)
            gradient.addColorStop(0, color)
            gradient.addColorStop(0.5, "#ffffff")
            gradient.addColorStop(1, color)

            ctx.strokeStyle = gradient
            ctx.lineWidth = 5
            ctx.beginPath()
            ctx.moveTo(x1, y1)
            ctx.lineTo(newX2, newY2)
            ctx.stroke()

            // Enhanced caps with depth
            drawCylinderCap(ctx, x1, y1, color, 8)
            drawCylinderCap(ctx, newX2, newY2, color, 6)
        }

        function drawCylinderCap(ctx, x, y, color, radius) {
            // Cap shadow
            ctx.fillStyle = "rgba(0, 0, 0, 0.3)"
            ctx.beginPath()
            ctx.arc(x + 1, y + 1, radius, 0, 2 * Math.PI)
            ctx.fill()

            // Main cap with gradient
            var gradient = ctx.createRadialGradient(x - radius/3, y - radius/3, 0, x, y, radius)
            gradient.addColorStop(0, "#ffffff")
            gradient.addColorStop(0.5, color)
            gradient.addColorStop(1, "#000000")

            ctx.fillStyle = gradient
            ctx.beginPath()
            ctx.arc(x, y, radius, 0, 2 * Math.PI)
            ctx.fill()
        }

        function drawTitle(ctx, centerX) {
            // Title shadow
            ctx.fillStyle = "rgba(0, 0, 0, 0.5)"
            ctx.font = "bold 26px Arial"
            ctx.textAlign = "center"
            ctx.fillText("Pneumatic Suspension System", centerX + 2, 42)

            // Main title with gradient
            var gradient = ctx.createLinearGradient(0, 20, 0, 50)
            gradient.addColorStop(0, "#ffffff")
            gradient.addColorStop(1, "#cccccc")

            ctx.fillStyle = gradient
            ctx.font = "bold 26px Arial"
            ctx.fillText("Pneumatic Suspension System", centerX, 40)

            // Subtitle
            ctx.fillStyle = "#aaaaaa"
            ctx.font = "16px Arial"
            ctx.fillText("Enhanced 2D Visualization with 3D Effects", centerX, 70)
        }
    }

    // Enhanced info overlay with glass effect
    Rectangle {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 20
        width: 280
        height: 140
        color: "rgba(32, 32, 64, 0.8)"
        border.color: "rgba(255, 255, 255, 0.3)"
        border.width: 1
        radius: 10

        // Glass effect
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: Math.round(parent.height / 2)
            color: "rgba(255, 255, 255, 0.1)"
            radius: 10
        }

        Column {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 8

            Text {
                text: "Enhanced 2D Schematic"
                color: "#ffffff"
                font.pixelSize: 16
                font.bold: true
            }

            Text {
                text: " Animated frame & cylinders"
                color: "#aaaaaa"
                font.pixelSize: 11
            }

            Text {
                text: " 4 Wheels with depth effect"
                color: "#aaaaaa"
                font.pixelSize: 11
            }

            Text {
                text: " Breathing pneumatic system"
                color: "#aaaaaa"
                font.pixelSize: 11
            }

            Text {
                text: " Gradient & shadow effects"
                color: "#aaaaaa"
                font.pixelSize: 11
            }

            Text {
                text: "Qt Quick Canvas 2D Enhanced"
                color: "#888888"
                font.pixelSize: 9
            }
        }
    }
}
