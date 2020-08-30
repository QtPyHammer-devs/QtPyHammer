#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump vec3 colour;

in mediump float Kd;

void main()
{
    mediump vec4 Ka = vec4(0.75, 0.75, 0.75, 1);

    outColour = vec4(colour, 1) * (Kd + Ka);
}
