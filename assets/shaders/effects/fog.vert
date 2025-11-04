#version 450 core
#ifndef MAIN
#define MAIN qt_customMain
#endif

// Requires GLSL 4.50 core for Qt Quick 3D SPIR-V runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
#endif

#ifndef INPUT_POSITION
#define INPUT_POSITION qt_Vertex
#endif

#ifndef INPUT_UV
#define INPUT_UV qt_MultiTexCoord0
#endif

#ifndef UBO_BINDING
#define UBO_BINDING(index) layout(binding = index)
#endif

#ifndef qt_Vertex
layout(location = 0) in vec3 qt_Vertex;
#endif

#ifndef qt_MultiTexCoord0
layout(location = 1) in vec2 qt_MultiTexCoord0;
#endif

#ifndef POSITION
#define POSITION gl_Position
#endif

#ifndef VARYING_UV
#define VARYING_UV v_uv
#endif

#ifndef DECLARE_OUTPUT_UV
#define DECLARE_OUTPUT_UV layout(location = 0) out vec2 VARYING_UV;
#endif
DECLARE_OUTPUT_UV

layout(std140) UBO_BINDING(0) uniform qt_effectUniforms {
    mat4 qt_ModelMatrix;
    mat4 qt_ModelViewProjectionMatrix;
    mat4 qt_ViewMatrix;
    vec3 qt_CameraPosition;
    float qt_Opacity;
} ubuf;

void fogVertexMain(out vec4 position)
{
    vec4 localPosition = vec4(INPUT_POSITION, 1.0);
    VARYING_UV = INPUT_UV;
    position = ubuf.qt_ModelViewProjectionMatrix * localPosition;
}

void MAIN()
{
    vec4 position = vec4(0.0);
    fogVertexMain(position);
    POSITION = position;
}

