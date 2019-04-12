from utilities.vector import dot, vec3, sort_clockwise

## TODO: polygon intersection
## TODO: match intersect to object

def ray_triangle(ray, triangle, length=1024):
    """returns a whether or not ray and triangle intersect, and the point of intersection"""
    point = (0, 0, 0)
    A, B, C = triangle
    ray_origin, ray_dir = ray
    AB = B - A
    AC = C - A
    cross = ray_dir * AC
    proj_AB = dot(AB, cross)
    if proj_AB == 0: # let python handle the epsilon
        return False, point
    snapped_ray = ray_origin - A
    u = (1 / proj_AB) * dot(snapped_ray, cross)
    if u < 0 or u > 1:
        return False, point
    snap_cross = snapped_ray * AB
    v = (1 / proj_AB) * dot(ray_dir, snap_cross) 
    if v < 0 or u + v > 1:
        return False, point
    t = (1 / proj_AB) * dot(AC, snap_cross)
    point = ray_origin + ray_dir * t
    if 0 < t < length:
        return True, point
    else:
        return False, point


def ray_triangle_length(ray, triangle):
    A, B, C = triangle
    ray_origin, ray_dir = ray
    AB = B - A
    AC = C - A
    cross = ray_dir * AC
    proj_AB = dot(AB, cross)
    if proj_AB == 0:
        return 0
    snapped_ray = ray_origin - A
    u = (1 / proj_AB) * dot(snapped_ray, cross)
    if not 0 < u < 1:
        return 0
    snap_cross = snapped_ray * AB
    v = (1 / proj_AB) * dot(ray_dir, snap_cross)
    if v < 0 or u + v > 1:
        return 0
    return (1 / proj_AB) * dot(AC, snap_cross)

def ray_hull(ray, planes):
    '''returns depth of intersection'''
    ray_origin, ray_dir = ray
    intersections = dict()
    for i, plane in enumerate(planes):
        normal, distance = plane
        distance_to_plane = distance - dot(normal, ray_origin)
        parallelity = dot(normal, ray_dir) # can be 0
        t = distance_to_plane / parallelity # ray length at intersection
        if t > 0:
            intersections[i] = t
    ... # entering or leaving?
    # need closest point of entry
    # and point of exit
    return intersections

def ray_hull2(ray, planes):
    ray_origin, ray_dir = ray
    ts = []
    for normal, distance in planes:
        V = normal * distance
        top = dot(V - ray_dir, normal)
        bottom = dot(ray_dir, normal)
        try:
            t = top / bottom
            ts.append(t)
        except:
            pass
    return ts

def determinant(matrix):
    a, b, c, d, e, f, g, h, i = matrix
    # | a b c |
    # | d e f |
    # | g h i |
    # aei + bfg + cdh - afh - bdi - ceg
    return a * (e * i - f * h) - b * (f * g - d * i) + c * (d * h - e * g)

def planes_coincident_point(p1, p2, p3):
    """Expects planes in format: (vec3(*normal), distance)
    does not test to see if an intersection exists"""
    D = determinant([p1[0].x, p1[0].y, p1[0].z,
                     p2[0].x, p2[0].y, p2[0].z,
                     p3[0].x, p3[0].y, p3[0].z])
    D1 = determinant([p1[1], p1[0].y, p1[0].z,
                      p2[1], p2[0].y, p2[0].z,
                      p3[1], p3[0].y, p3[0].z])
    D2 = determinant([p1[0].x, p1[1], p1[0].z,
                      p2[0].x, p2[1], p2[0].z,
                      p3[0].x, p3[1], p3[0].z])
    D3 = determinant([p1[0].x, p1[0].y, p1[1],
                      p2[0].x, p2[0].y, p2[1],
                      p3[0].x, p3[0].y, p3[1]])
    # if D != 0 and single point intersection exists
    print(f'*** {D:.3f} {D1:.3f} {D2:.3f} {D3:.3f}', sep='\t')
    # dot(P1[0], (P2[0] * P3[0])) != 0
    X = D1 / -D
    Y = D2 / -D
    Z = D3 / -D
    # isn't there a simpler way
##    X = p1[0].x * p1[1] + p2[0].x * p2[1] + p3[0].z * p3[1]
##    Y = p1[0].y * p1[1] + p2[0].y * p2[1] + p3[0].z * p3[1]
##    Z = p1[0].z * p1[1] + p2[0].y * p2[1] + p3[0].z * p3[1]
    return vec3(-X, -Y, -Z)


if __name__ == "__main__":
    from utilities.vector import vec3
    ray = (vec3(0, 0, 4), vec3(0, 0, -1))
    make_plane = lambda *args: (vec3(*args), 1)
    cube = tuple(make_plane(*a) for a in [(1, 0, 0), (0, 1, 0), (0, 0, 1),
                                          (-1, 0, 0), (0, -1, 0), (0, 0, -1)])

    print(ray_hull2(ray, cube))
