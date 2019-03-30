from utilities.vector import dot

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
