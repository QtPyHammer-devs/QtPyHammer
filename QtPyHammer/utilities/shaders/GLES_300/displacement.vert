#version 300 es
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in float blend_alpha;
layout(location = 2) in vec2 vertex_uv;
layout(location = 3) in vec3 editor_colour;

uniform mat4 ModelViewProjectionMatrix;

out vec3 position;
out vec3 normal;
out vec2 uv;
out float blend;

out vec3 colour;
out float Kd;

void main()
{
    position = vertex_position;
    normal = vertex_normal;
    uv = vec2(vertex_uv.x, -vertex_uv.y);
	blend = blend_alpha;
	
	colour = mix(vec3(.15, .5, .15), vec3(.25, .25, .30), blend_alpha);
	Kd = abs(normal.z / 3.0 + 1.0/3.0 * normal.y / 3.0 + 2.0/3.0 * normal.x / 3.0);

	gl_Position = ModelViewProjectionMatrix * vec4(vertex_position, 1);
}
