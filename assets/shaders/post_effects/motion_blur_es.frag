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
SAMPLER_BINDING(1) uniform sampler2D qt_VelocityTexture;

#ifndef INPUT
#define INPUT texture(qt_Texture0, INPUT_UV)
#endif

#ifdef QSB_USE_UNIFORM_BLOCK
layout(std140) UBO_BINDING(10) uniform QsbMotionBlurParams {
    float uStrength;
    int uSamples;
};
#else
uniform float uStrength;
uniform int uSamples;
#endif

void motionBlurESMain(inout vec4 fragColor)
{
    vec4 original = INPUT;
    vec2 velocity = texture(qt_VelocityTexture, INPUT_UV).xy;

    vec3 color = original.rgb;
    int sampleCount = max(uSamples, 1);
    vec2 step = velocity * uStrength
        / max(1.0, float(sampleCount));

    for (int i = 1; i < sampleCount; i++) {
        vec2 sampleCoord = INPUT_UV + step * float(i);
        color += texture(qt_Texture0, sampleCoord).rgb;
    }

    color /= max(1.0, float(sampleCount));
    fragColor = vec4(color, original.a);
}

#if QSB_USES_QT_CUSTOM_MAIN
void MAIN(inout vec4 fragColor)
{
    motionBlurESMain(fragColor);
}
#else
void MAIN()
{
    vec4 fragColor = vec4(0.0);
    motionBlurESMain(fragColor);
    FRAGCOLOR = fragColor;
}
#endif
