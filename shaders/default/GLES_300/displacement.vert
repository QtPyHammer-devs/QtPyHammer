#version 300 es
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec3 vertex_normal;
layout(location = 2) in vec2 vertex_uv;
layout(location = 4) in float blend_alpha;

uniform mat4 MVP_matrix;

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

    colour = mix(vec3(.0, .4, .75), vec3(.65, .0, .45), blend_alpha);
    Kd = dot(normal, vec3(.05, .35, .60)) / 3.0 + 0.5;

    gl_Position = MVP_matrix * vec4(vertex_position, 1);
}
