import OpenGL.GL as gl  # imagine a python binding with gl.Begin not gl.glBegin


def grid_line_generator(limit, scale):  # grid scale selected via the UI
    """ yields lines on a grid (one vertex at a time) centered on [0, 0]
    limit: int, half the width of grid
    step: int, gap between edges"""
    # center axes
    yield 0, -limit
    yield 0, limit  # +NS
    yield -limit, 0
    yield limit, 0  # +EW
    # concentric squares stepping out from center (0, 0) to limit
    for i in range(0, limit + 1, scale):
        yield i, -limit
        yield i, limit  # +NS
        yield -limit, i
        yield limit, i  # +EW
        yield limit, -i
        yield -limit, -i  # -WE
        yield -i, limit
        yield -i, -limit  # -SN
    # ^ the above function is optimised for a line grid
    # another function would be required for a dot grid
    # it's also worth considering adding an offset / origin point


def line_grid(limit=2048, grid_scale=64, colour=(.5, .5, .5)):
    gl.glLineWidth(1)
    gl.glBegin(gl.GL_LINES)
    gl.glColor(*colour)
    for x, y in grid_line_generator(limit, grid_scale):
        # you don't have to generate the grid every frame by the way
        gl.glVertex(x, y)
    gl.glEnd()


def dot_grid_generator(min_x, min_y, max_x, max_y, scale):
    """Takes a x,y boiunds so only the visible points are rendered"""
    def snap(x):
        return x // scale * scale
    min_x = snap(min_x)
    max_x = snap(max_x)
    min_y = snap(min_y)
    max_y = snap(max_y)
    for x in range(min_x, min_y + 1, scale):
        for y in range(min_x, min_y + 1, scale):
            yield x, y


def dot_grid(min_x, min_y, max_x, max_y, scale=64, colour=(.5, .5, .5)):
    gl.glBegin(gl.GL_POINTS)
    gl.glColor(*colour)
    for x, y in dot_grid_generator(min_x, min_y, max_x, max_y, scale):
        # you don't have to generate the grid every frame by the way
        gl.glVertex(x, y)
    gl.glEnd()


def origin_marker(scale=128):
    gl.glLineWidth(2)
    gl.glBegin(gl.GL_LINES)
    gl.glColor(1, 0, 0)
    gl.glVertex(0, 0, 0)
    gl.glVertex(scale, 0, 0)
    gl.glColor(0, 1, 0)
    gl.glVertex(0, 0, 0)
    gl.glVertex(0, scale, 0)
    gl.glColor(0, 0, 1)
    gl.glVertex(0, 0, 0)
    gl.glVertex(0, 0, scale)
    gl.glEnd()


def ray(origin, direction, distance=4096):
    gl.glLineWidth(2)
    gl.glBegin(gl.GL_LINES)
    gl.glColor(1, .75, .25)
    gl.glVertex(*origin)
    gl.glVertex(*(origin + direction * distance))
    gl.glEnd()
