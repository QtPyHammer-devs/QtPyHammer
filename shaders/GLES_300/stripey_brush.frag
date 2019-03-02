#version 300 es
layout(location = 0) out mediump vec4 outColour;

in mediump vec3 position;
in mediump vec3 normal;
in mediump vec2 uv;
in mediump vec3 colour;

void main()
{
	mediump vec4 ambient = vec4(0.35, 0.35, 0.35, 1);
    mediump vec4 diffuse = vec4(1, 1, 1, 1) * dot(normal, vec3(1, 1, 1));
    diffuse = clamp(diffuse, 0.25, 0.75);

    // mathematical pattern
    // could use uniforms (time) to animate
    mediump vec4 stripe = vec4(1, 1, 1, 1) * (abs(uv.x) - abs(uv.y));
    stripe = mod(stripe, 64.0) / 64.0;

    outColour = stripe * vec4(colour, 1) * diffuse + ambient;
}
