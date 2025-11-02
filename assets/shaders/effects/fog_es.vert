#version 300 es
precision highp float;
precision highp int;

#ifndef INPUT_POSITION
#define INPUT_POSITION qt_Vertex
#endif

#ifndef INPUT_UV
#define INPUT_UV qt_MultiTexCoord0
#endif

layout(location = 0) out vec2 v_uv;

layout(std140) uniform qt_effectUniforms {
    mat4 qt_ModelMatrix;
    mat4 qt_ModelViewProjectionMatrix;
    mat4 qt_ViewMatrix;
    vec3 qt_CameraPosition;
    float qt_Opacity;
} ubuf;

void MAIN()
{
    vec4 localPosition = vec4(INPUT_POSITION, 1.0);
    v_uv = INPUT_UV;
    POSITION = ubuf.qt_ModelViewProjectionMatrix * localPosition;
}
