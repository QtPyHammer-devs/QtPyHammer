import colorsys
import ctypes
import itertools
import numpy as np # for vertex buffers Numpy is needed (available through pip)
from OpenGL.GL import * # Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import * # PyOpenGL-accelerate 3.1.0 requires MSVC 2015
# get precompiled binaries if you can, it's much less work

import sys
sys.path.insert(0, 'utilities')
# there has to be a better way to load these
import camera
import physics
import vmf_tool
import vector
import solid_tool # must be loaded AFTER vmf_tool (how do dependencies work?)


def loop_fan(vertices):
    out = vertices[:3]
    for vertex in vertices[3:]:
        out += [out[0], out[-1], vertex]
    return out


def loop_fan_indices(vertices, start_index):
    "polygon to triangle fan (indices only) by Exactol"
    indices = []
    for i in range(1, len(vertices) - 1):
        indices += [startIndex, startIndex + i, startIndex + i + 1]
    return indices


def main(vmf_path, width=1024, height=576):

    start_import = time.time()
    imported_vmf = vmf_tool.namespace_from(open(vmf_path))
    if hasattr(imported_vmf.world, 'solid'):
        imported_vmf.world.solids = [imported_vmf.world.solid]
        del imported_vmf.world.solid
    if not hasattr(imported_vmf.world, 'solids'):
        imported_vmf.world['solids'] = []
    if hasattr(imported_vmf, 'entity'):
        imported_vmf.entities = [imported_vmf.entity]
        del imported_vmf.entity
    if not hasattr(imported_vmf, 'entities'):
        imported_vmf['entities'] = []

    for brush in imported_vmf.world.solids:
        # bootleg auto-visgroup
        if not any([face.material == 'TOOLS/SKIP' or face.material == 'TOOLS/HINT' or 'CLIP' in face.material.upper() for face in brush.sides]):
##        if any([hasattr(face, 'dispinfo') for face in brush.sides]):
            string_solids.append(brush)
    for entity in imported_vmf.entities:
        if hasattr(entity, 'solid'):
            if isinstance(entity.solid, vmf_tool.namespace):
                string_solids.append(entity.solid)
        if hasattr(entity, 'solids'):
            if isinstance(entity.solids[0], vmf_tool.namespace):
                string_solids += entity.solids
                
    solids = []
    for brush in string_solids:
        try:
            solids.append(solid_tool.solid(brush))
        except Exception as exc:
            print(f"Invalid solid! (id {brush.id})")
            print(exc, '\n')
##            raise exc

    brush_triangles = list(itertools.chain(*[s.triangles for s in solids]))

    offset_index_map = lambda B, O: [(S + O, L) for S, L in B.index_map]
    
    brush_index_map = [s.index_map for s in solids]

    # vertices, indices & draw_call map ((brush (faces, ...)), ...)
    # [brush[sides], ... ] TO:
    # vertices bytes,
    # indices bytes &
    # [(brush (start, len), side (start, len), ...), ...]
    # use compress sequence to assemble draw calls

##    try: # GLSL 450
##        # Vertex Shaders
##        vert_shader_brush = compileShader(open('shaders/GLSL_450/verts_brush.vert', 'rb'), GL_VERTEX_SHADER)
##        vert_shader_displacement = compileShader(open('shaders/GLSL_450/verts_displacement.vert', 'rb'), GL_VERTEX_SHADER)
##        # Fragment Shaders
##        frag_shader_brush_flat = compileShader(open('shaders/GLSL_450/brush_flat.frag', 'rb'), GL_FRAGMENT_SHADER)
##        frag_shader_displacement_flat = compileShader(open('shaders/GLSL_450/displacement_flat.frag', 'rb'), GL_FRAGMENT_SHADER)
##    except RuntimeError as exc: # GLES 3.00
##        # Vertex Shaders
##        vert_shader_brush = compileShader(open('shaders/GLES_300/verts_brush.vert', 'rb'), GL_VERTEX_SHADER)
##        vert_shader_displacement = compileShader(open('shaders/GLES_300/verts_displacement.vert', 'rb'), GL_VERTEX_SHADER)
##        # Fragment Shaders
##        frag_shader_brush_flat = compileShader(open('shaders/GLES_300/brush_flat.frag', 'rb'), GL_FRAGMENT_SHADER)
##        frag_shader_displacement_flat = compileShader(open('shaders/GLES_300/displacement_flat.frag', 'rb'), GL_FRAGMENT_SHADER)
##    # Programs
##    program_flat_brush = compileProgram(vert_shader_brush, frag_shader_brush_flat)
##    program_flat_displacement = compileProgram(vert_shader_displacement, frag_shader_displacement_flat)
##    glLinkProgram(program_flat_brush)
##    glLinkProgram(program_flat_displacement)
##
##    # Vertex Buffer
##    VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
##    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
##    glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
##    # Index Buffer
##    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
##    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, np.array(indices, dtype=np.uint32), GL_STATIC_DRAW)
##    # Vertex Format
##    glEnableVertexAttribArray(0) # vertex_position
##    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 40, GLvoidp(0))
##    glEnableVertexAttribArray(1) # vertex_normal
##    glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 40, GLvoidp(12))
##    glEnableVertexAttribArray(2) # vertex_uv
##    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 40, GLvoidp(24))
##    glEnableVertexAttribArray(4) # editor_colour
##    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 40, GLvoidp(32))
##    # blend_alpha (displacement)
##    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 40, GLvoidp(12)) # replace vertex_normal
    
    print(f'{len(solids)} brushes loaded succesfully!')   
    print('import took {:.2f} seconds'.format(time.time() - start_import))


################################################################################
####========================    DRAW CALLS    ==============================####
################################################################################

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        CAMERA.set()

        # CENTER MARKER
        glLineWidth(1)
        glBegin(GL_LINES)
        glColor(1, 0, 0)
        glVertex(0, 0, 0)
        glVertex(128, 0, 0)
        glColor(0, 1, 0)
        glVertex(0, 0, 0)
        glVertex(0, 128, 0)
        glColor(0, 0, 1)
        glVertex(0, 0, 0)
        glVertex(0, 0, 128)
        glEnd()

        # RAYCAST
        glColor(1, .5, 0)
        glBegin(GL_LINES)
        for point in rendered_ray:
            glVertex(*point)
        glEnd()

        # GRID
##        glLineWidth(2)
##        glBegin(GL_LINES)
##        for x in range(-16, 17):
##            x = x * 64
##            glColor(1, 0 , 0)
##            glVertex(x, -1024, 0)
##            glColor(.25, .25, .25)
##            glVertex(x, 0, 0)
##            glVertex(x, 0, 0)
##            glColor(1, 0 , 0)
##            glVertex(x, 1024, 0)
##        for y in range(-16, 17):
##            y = y * 64
##            glColor(0, 1 , 0)
##            glVertex(-1024, y, 0)
##            glColor(.25, .25, .25)
##            glVertex(0, y, 0)
##            glVertex(0, y, 0)
##            glColor(0, 1 , 0)
##            glVertex(1024, y, 0)
##        glEnd()

        # SOLIDS
##        glColor(1, 1, 1)
##        glBegin(GL_TRIANGLES)
##        for vertex in brush_triangles:
##            glVertex(*vertex)
##        glEnd()

        glBegin(GL_TRIANGLES)
        for solid in render_solids:
            if not solid.is_displacement:
                glColor(*solid.colour) # Flat Colour Unshaded
                for side_index, index_range in enumerate(solid.face_tri_map):
                    normal = solid.planes[side_index][0]
                    Kd = (vector.dot(normal, (1, 1, 1)) / 16) + .75
                    glColor(*[Kd * x for x in solid.colour])
                    start, end = index_range
                    for vertex in solid.triangles[start:end]:
                        glVertex(*vertex)
        glEnd()

        # DISPLACEMENTS
        glBegin(GL_TRIANGLES)
        glColor(.5, .5, .5)
        for solid in render_solids:
            if solid.is_displacement:
                glColor(1, 1, 1) # Hammer Default
                for i, points in solid.displacement_triangles.items():
                    for point, alpha, normal in points:
                        Kd = (vector.dot(normal, (1, 1, 1)) / 16) + .75
                        # clamped from 0.75 to 0.75 + 1/32
                        blend = vector.lerp(solid.colour, solid.sides[i].blend_colour, alpha / 255)
                        glColor(*[Kd * x for x in blend])
                        glVertex(*point)
        glEnd()

        # DISPLACEMENT NORMALS
        glColor(1, .75, 0)
        glBegin(GL_LINES)
        for solid in render_solids:
            if solid.is_displacement:
                for side_index, points in solid.displacement_vertices.items():
                    for point, alpha, normal in points:
                        glVertex(*point)
                        glVertex(*point + normal * 32)
        glEnd()

        # BRUSH BOUNDING BOXES
        # be sure to turn off backface culling
##        glColor(1, 0, 0)
##        glPolygonMode(GL_FRONT, GL_LINE)
##        glBegin(GL_QUADS)
##        for solid in solids:
##            draw_aabb(solid.aabb)
##        glEnd()
##        glPolygonMode(GL_FRONT, GL_FILL)

        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    try:
        main('tests/vmfs/test2.vmf')
##        main('tests/vmfs/sdk_pl_goldrush.vmf')
##        main('tests/vmfs/pl_upward_d.vmf')
    except Exception as exc:
        SDL_Quit()
        raise exc
##    import sys
##    for file in sys.argv[1:]:
##        main(file)
