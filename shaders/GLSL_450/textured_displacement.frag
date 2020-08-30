#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in vec3 normal;
in vec2 uv;
in float blend;

in vec3 colour;
in float Kd;

uniform sampler2D blend_texture1;
uniform sampler2D blend_texture2;

void main()
{
    vec4 albedo1 = texture2D(blend_texture1, uv);
    vec4 albedo2 = texture2D(blend_texture2, uv);

    outColour = mix(albedo1, albedo2, blend);
}
