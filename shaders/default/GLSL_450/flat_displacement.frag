#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in vec3 normal;
in vec2 uv;
in float blend;

in vec3 colour;
in float Kd;

void main()
{
    vec4 Ka = vec4(0.25, 0.25, 0.25, 1);

    outColour = vec4(colour, 1) * (Kd + Ka);
}
