#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in smooth vec3 normal;
in vec2 uv;
in vec3 colour;

void main()
{
	vec4 ambient = vec4(0.25, 0.25, 0.25, 1);
	float diffuse = dot(normal, vec3(1, 1, 1));
	diffuse = clamp(diffuse, 0.25, 0.75);

	outColour = vec4(colour, 1) * diffuse + ambient;
}
