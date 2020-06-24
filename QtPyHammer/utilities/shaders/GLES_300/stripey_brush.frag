#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump vec3 colour;

in mediump float Kd;

void main()
{
    mediump vec4 Ka = vec4(0.35, 0.35, 0.35, 1);
    mediump float stripe = mod((uv.x + uv.y) / 64.0, 1.0);
    stripe = (stripe > 0.5 ? 1.0 : 0.25);

    outColour = stripe * vec4(colour, 1) * (Kd + Ka);
}
