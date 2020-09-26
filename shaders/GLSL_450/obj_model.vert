#version 450 core
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 vertex_normal;
layout(location = 2) in vec2 vertex_uv;
layout(location = 3) in vec3 vertex_colour;

uniform mat4 MVP_matrix;

out vec3 position;
out smooth vec3 normal;
out vec2 uv;
out vec3 colour;

out float Kd;

void main()
{
    position = vertex_position;
    normal = vertex_normal;
    uv = vec2(vertex_uv.x, -vertex_uv.y);
    colour = vertex_colour;

    Kd = dot(normal, vec3(.05, .35, .60)) / 3.0 + 0.5;

    gl_Position = MVP_matrix * vec4(vertex_position, 1);
}
