#version 300 es
// Requires an OpenGL ES 3.0 context for Qt Quick 3D runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
#endif

#ifdef QSB_ADD_BINDINGS
#ifndef GL_ES
#extension GL_ARB_shading_language_420pack : enable
#extension GL_ARB_separate_shader_objects : enable
#endif
#endif

#ifndef INPUT_POSITION
#define INPUT_POSITION qt_Vertex
#endif

#ifndef INPUT_UV
#define INPUT_UV qt_MultiTexCoord0
#endif

#ifndef MAIN
#define MAIN qt_customMain
#define QSB_USES_QT_CUSTOM_MAIN 1
#endif

#ifndef QSB_USES_QT_CUSTOM_MAIN
#define QSB_USES_QT_CUSTOM_MAIN 0
#endif

#ifndef UBO_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#else
// GLSL 330 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#endif
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

layout(location = 0) out vec2 v_uv;

layout(std140) UBO_BINDING(0) uniform qt_effectUniforms {
    mat4 qt_ModelMatrix;
    mat4 qt_ModelViewProjectionMatrix;
    mat4 qt_ViewMatrix;
    vec3 qt_CameraPosition;
    float qt_Opacity;
} ubuf;

void fogESVertexMain(out vec4 position)
{
    vec4 localPosition = vec4(INPUT_POSITION, 1.0);
    v_uv = INPUT_UV;
    position = ubuf.qt_ModelViewProjectionMatrix * localPosition;
}

void MAIN()
{
    vec4 position = vec4(0.0);
    fogESVertexMain(position);
    POSITION = position;
}

void MAIN(out vec4 position)
{
    fogESVertexMain(position);
}
