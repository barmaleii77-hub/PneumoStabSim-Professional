#version 300 es
precision highp float;
precision highp int;
precision mediump sampler2D;

#ifndef INPUT_UV
#define INPUT_UV v_uv
#endif

#ifndef FRAGCOLOR
layout(location = 0) out vec4 qt_FragColor;
#define FRAGCOLOR qt_FragColor
#endif

layout(binding = 0) uniform sampler2D qt_Texture0;

void MAIN()
{
    FRAGCOLOR = texture(qt_Texture0, INPUT_UV);
}
