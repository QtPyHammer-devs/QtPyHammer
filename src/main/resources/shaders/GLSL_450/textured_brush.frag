#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in vec3 normal;
in vec2 uv;
in vec3 colour;

uniform sampler2D texture; /* Texture Atlas or Array */

void main()
{
	vec4 ambient = vec4(0.25, 0.25, 0.25, 1);
	float diffuse = normal.x / 3 + 2/3 * normal.y / 3 + 1/3 * normal.z / 3;

	vec4 albedo = texture2D(texture, uv);

	outColour = albedo * (ambient + diffuse);
}
