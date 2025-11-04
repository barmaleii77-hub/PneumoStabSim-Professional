#version 300 es
// Requires an OpenGL ES 3.0 context for Qt Quick 3D runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision mediump sampler2D;
#endif

#ifdef QSB_ADD_BINDINGS
#ifndef GL_ES
#extension GL_ARB_shading_language_420pack : enable
#extension GL_ARB_separate_shader_objects : enable
#endif
#endif



#ifndef SAMPLER_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#else
#define SAMPLER_BINDING(index) layout(binding = index)
#endif
#else
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#endif
#endif

#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
in vec2 v_uv;
#else
layout(location = 0) in vec2 v_uv;
#endif
#else
in vec2 v_uv;
#endif

#ifndef UBO_BINDING
#ifdef QSB_ADD_BINDINGS
#ifdef GL_ES
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#else
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#endif
#endif

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifdef MAIN
#undef MAIN
#define MAIN qt_customMain
#define QSB_USES_QT_CUSTOM_MAIN 1
#endif

#ifndef QSB_USES_QT_CUSTOM_MAIN
#define QSB_USES_QT_CUSTOM_MAIN 0
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

SAMPLER_BINDING(0) uniform sampler2D qt_Texture0;

void motionBlurFallbackESMain(inout vec4 fragColor)
{
    fragColor = texture(qt_Texture0, INPUT_UV);
}

#if QSB_USES_QT_CUSTOM_MAIN
void MAIN(inout vec4 fragColor)
{
    motionBlurFallbackESMain(fragColor);
}
#else
void MAIN()
{
    vec4 fragColor = vec4(0.0);
    motionBlurFallbackESMain(fragColor);
    FRAGCOLOR = fragColor;
}
#endif
