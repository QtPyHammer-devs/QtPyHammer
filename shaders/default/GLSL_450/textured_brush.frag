#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in vec3 normal;
in vec2 uv;
in vec3 colour;

in float Kd;

uniform sampler2D texture; /* Texture Atlas or Array */

void main()
{
    vec4 albedo = texture2D(texture, uv);

    outColour = albedo;
}
