#version 450 core
layout(location = 0) out vec4 outColour;

in vec3 position;
in smooth vec3 normal;
in vec2 uv;
in vec3 colour;

// uniform sampler2D texture; /* Move toward a Texture Atlas / Array */

void main()
{
	vec4 ambient = vec4(0.75, 0.75, 0.75, 1);
	vec4 diffuse = vec4(1, 1, 1, 1) * normal.x / 3 + 2/3 * normal.y / 3 + 1/3 * normal.z / 3;
	// vec4 albedo = texture2D(texture, uv);

	outColour = vec4(colour, 1) * (ambient + diffuse);
	// outColour = vec4(uv.x, uv.y, 1, 1);
	// outColor = albedo * (ambient + diffuse);
}
