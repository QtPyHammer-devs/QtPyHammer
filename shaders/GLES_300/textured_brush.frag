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
	mediump vec4 diffuse = vec4(1, 1, 1, 1) * dot(normal, vec3(1, 1, 1));
    diffuse = clamp(diffuse, 0.25, 1.0);
	mediump vec4 albedo = texture2D(texture, uv);

	outColour = albedo * (ambient + diffuse);
}
