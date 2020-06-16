#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in float blend;
in vec2 uv;
in vec3 colour;

void main()
{
	vec4 Ka = vec4(0.75, 0.75, 0.75, 1);
	
	vec3 inverse_colour = vec3(1, 1, 1); // will be inverse hue
	vec4 blend_colour = vec4(mix(colour, inverse_colour, blend), 1);

	outColour = vec4(blend_colour, 1) + Ka;
}
