#version 450 core
// Qt Quick 3D post-processing shader.
// Shader logic executes in main() with helper functions for readability.
// Requires GLSL 4.50 core for Qt Quick 3D SPIR-V runtime compatibility.

#ifdef GL_ES
precision highp float;
precision highp int;
precision mediump sampler2D;
#endif

#ifndef SAMPLER_BINDING
#define SAMPLER_BINDING(index) layout(binding = index)
#endif

#ifndef VARYING_UV
#define VARYING_UV v_uv
#endif

#ifndef DECLARE_INPUT_UV
#define DECLARE_INPUT_UV layout(location = 0) in vec2 VARYING_UV;
#endif
DECLARE_INPUT_UV

#ifndef UBO_BINDING
#define UBO_BINDING(index) layout(binding = index)
#endif

#ifndef INPUT_UV
#define INPUT_UV VARYING_UV
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

void motionBlurMain(inout vec4 fragColor)
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

void main()
{
    vec4 fragColor = vec4(0.0);
    motionBlurMain(fragColor);
    FRAGCOLOR = fragColor;
}
