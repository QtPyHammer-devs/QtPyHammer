// reverse engineered from:
// https://github.com/ValveSoftware/source-sdk-2013/blob/master/mp/src/materialsystem/stdshaders/WorldVertexTransition_ps14.psh
// with the help of Tumby#5171, Crowbar#3063 & yoshimario2000#3972

//Tumby:
// Thingy = clamp(DisplacementAlpha - BlendGreen + 0.5)
// Alpha = -2 * Thingy^3 + 3 * Thingy^2

vec4 albedo1 = texture2D(texture0, uv) /* blend from */
vec4 albedo2 = texture2D(texture1, uv) /* blend into */
float blend_factor;

if (blendmodulate)
    {
    modulate = texture2D(texture2, uv);
    blend_factor = clamp(blend_alpha - modulate.g + 0.5, 0, 1);
    float curve = ((-2.0 * blend_factor) + 3.0) * blend_factor;
    blend_factor = blend_factor * curve;
    }
else
    { blend_factor = clamp(blend_alpha, 0, 1); }
outColour = mix(albedo1, albedo2, blend_factor);