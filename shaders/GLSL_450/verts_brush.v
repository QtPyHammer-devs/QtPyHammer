#version 450 core
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 vertex_normal;
layout(location = 2) in vec2 vertex_uv;
layout(location = 4) in vec3 editor_colour;

uniform mat4 gl_ModelViewProjectionMatrix;

out vec3 position;
out smooth vec3 normal;
out vec2 uv;
out vec3 colour;

void main()
{
    position = vertex_position;
    normal = vertex_normal;
    uv = vec2(vertex_uv.x, -vertex_uv.y);
	colour = editor_colour;

	gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex_position, 1);
}
