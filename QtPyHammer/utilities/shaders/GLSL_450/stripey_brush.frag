#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in smooth vec3 normal;
in vec2 uv;
in vec3 colour;

in float Kd;

void main()
{
    vec4 Ka = vec4(0.25, 0.25, 0.25, 1);
    float stripe = mod((uv.x + uv.y) / 64.0, 1.0);
    stripe = (stripe > 0.5 ? 1.0 : 0.25);

    outColour = stripe * vec4(colour, 1) * (Kd + Ka);
}
