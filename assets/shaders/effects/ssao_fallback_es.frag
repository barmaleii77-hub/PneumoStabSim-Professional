#version 300 es
// Qt Quick 3D post-processing shader.
// Shader logic executes directly inside main() for Qt 6.10 compatibility.
// Requires an OpenGL ES 3.0 context for Qt Quick 3D runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision highp sampler2D;
#endif

#ifdef QSB_ADD_BINDINGS
#ifndef GL_ES
#extension GL_ARB_shading_language_420pack : enable
#extension GL_ARB_separate_shader_objects : enable
#endif
#endif

#ifndef VARYING_UV
#define VARYING_UV v_uv
#endif

#ifndef SAMPLER_BINDING
#if defined(GL_ES)
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define SAMPLER_BINDING(index)
#else
#define SAMPLER_BINDING(index) layout(binding = index)
#endif
#endif

#ifndef DECLARE_INPUT_UV
#if defined(GL_ES)
#define DECLARE_INPUT_UV in vec2 VARYING_UV;
#else
#define DECLARE_INPUT_UV layout(location = 0) in vec2 VARYING_UV;
#endif
#endif
DECLARE_INPUT_UV

#ifndef UBO_BINDING
#if defined(GL_ES)
// GLSL ES 3.00 does not support explicit binding qualifiers; Qt assigns bindings automatically.
#define UBO_BINDING(index)
#else
#define UBO_BINDING(index) layout(binding = index)
#endif
#endif

#ifndef INPUT_UV
#define INPUT_UV VARYING_UV
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

SAMPLER_BINDING(0) uniform sampler2D qt_Texture0;

void ssaoFallbackESMain(inout vec4 fragColor)
{
    fragColor = texture(qt_Texture0, INPUT_UV);
}

void main()
{
    vec4 fragColor = vec4(0.0);
    ssaoFallbackESMain(fragColor);
    FRAGCOLOR = fragColor;
}
