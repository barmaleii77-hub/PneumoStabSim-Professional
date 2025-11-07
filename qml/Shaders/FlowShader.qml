import QtQuick 6.10
import "."

ManagedShaderEffect {
    id: root
    objectName: "FlowShader"
    effectId: "flow_shader"

    property color baseColor: Qt.rgba(0.25, 0.73, 1.0, 1.0)
    property real intensity: 1.0
    property real glowStrength: 0.6
    property real pulseSpeed: 1.0
    property real time: 0.0

    width: 256
    height: 64

    vertexShader: "uniform highp mat4 qt_Matrix;\n"
            + "attribute highp vec4 qt_Vertex;\n"
            + "attribute highp vec2 qt_MultiTexCoord0;\n"
            + "varying highp vec2 texCoord;\n"
            + "void main() {\n"
            + "    texCoord = qt_MultiTexCoord0;\n"
            + "    gl_Position = qt_Matrix * qt_Vertex;\n"
            + "}\n"

    fragmentShader: "uniform lowp float intensity;\n"
            + "uniform lowp float glowStrength;\n"
            + "uniform lowp float pulseSpeed;\n"
            + "uniform lowp float time;\n"
            + "uniform lowp vec4 baseColor;\n"
            + "varying highp vec2 texCoord;\n"
            + "lowp float wave = sin((texCoord.x + time * pulseSpeed) * 6.28318530718);\n"
            + "lowp float flowRamp = smoothstep(0.1, 0.9, texCoord.y);\n"
            + "lowp float pulse = 0.5 + 0.5 * wave;\n"
            + "lowp float alpha = clamp(intensity * (0.35 + glowStrength * pulse) * flowRamp, 0.0, 1.0);\n"
            + "lowp vec3 colour = baseColor.rgb * (0.4 + 0.6 * flowRamp);\n"
            + "gl_FragColor = vec4(colour, baseColor.a * alpha);\n"

    NumberAnimation on time {
        id: timeAnimation
        from: 0.0
        to: 1.0
        duration: Math.max(250, 1600 / Math.max(0.2, root.pulseSpeed))
        loops: Animation.Infinite
        running: root.visible
        easing.type: Easing.Linear
    }
}
