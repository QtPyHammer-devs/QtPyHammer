#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in smooth vec3 normal;
in vec2 uv;
in vec3 colour;

void main()
{
	vec4 ambient = vec4(0.25, 0.25, 0.25, 1);
	float diffuse = normal.x / 3 + 2/3 * normal.y / 3 + 1/3 * normal.z / 3;

	outColour = vec4(colour, 1) * diffuse + ambient;
}
