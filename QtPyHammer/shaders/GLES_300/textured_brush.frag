#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump vec3 colour;

in mediump float Kd;

uniform sampler2D texture; /* Texture Atlas or Array */

void main()
{
    mediump vec4 albedo = texture2D(texture, uv);

    outColour = albedo;
}
