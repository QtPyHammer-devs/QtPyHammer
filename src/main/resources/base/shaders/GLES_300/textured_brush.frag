#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump vec3 colour;

uniform sampler2D texture; /* Texture Atlas or Array */

void main()
{
	mediump vec4 ambient = vec4(0.75, 0.75, 0.75, 1);
    mediump float diffuse = normal.x / 3 + 2/3 * normal.y / 3 + 1/3 * normal.z / 3;

	mediump vec4 albedo = texture2D(texture, uv);

	outColour = albedo * (ambient + diffuse);
}
