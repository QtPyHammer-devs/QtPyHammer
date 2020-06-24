#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump float blend;

in mediump vec3 colour;
in mediump float Kd;

uniform sampler2D blend_texture1;
uniform sampler2D blend_texture2;

void main()
{
    mediump vec4 albedo1 = texture2D(blend_texture1, uv);
    mediump vec4 albedo2 = texture2D(blend_texture2, uv);

    outColour = mix(albedo1, albedo2, blend);
}
