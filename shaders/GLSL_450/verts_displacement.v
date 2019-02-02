#version 450 core
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in float blend_alpha;
layout(location = 2) in vec2 vertex_uv;
layout(location = 4) in vec3 editor_colour;

uniform mat4 gl_ModelViewProjectionMatrix;

out vec3 position;
out float blend;
out vec2 uv;
out vec3 colour;

void main()
{
    position = vertex_position;
    blend = blend_alpha;
    uv = vec2(vertex_uv.x, -vertex_uv.y);
	colour = editor_colour;

	gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex_position, 1);
}
