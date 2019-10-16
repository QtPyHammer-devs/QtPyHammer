"""Bunch of OpenGL heavy code for rendering vmfs"""
import colorsys
import ctypes
import itertools

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import *

import camera
import vmf_tool
import vector
import solids


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


def main(vmf_path):
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
        # hacky visgroups
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
    # matching <solid>s to index ranges will be quite helpful later
    print(f'{len(solids)} brushes loaded succesfully!')   
    print('import took {:.2f} seconds'.format(time.time() - start_import))

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
################################################################################
####=====================    EXAMPLE DRAW CALLS    ==========================####
################################################################################
### BRUSHES
##glBegin(GL_TRIANGLES)
##for solid in render_solids:
##    if not solid.is_displacement:
##        glColor(*solid.colour) # Flat Colour Unshaded
##        for side_index, index_range in enumerate(solid.face_tri_map):
##            normal = solid.planes[side_index][0]
##            Kd = (vector.dot(normal, (1, 1, 1)) / 16) + .75
##            glColor(*[Kd * x for x in solid.colour])
##            start, end = index_range
##            for vertex in solid.triangles[start:end]:
##                glVertex(*vertex)
##glEnd()
##
### DISPLACEMENTS
##glBegin(GL_TRIANGLES)
##glColor(.5, .5, .5)
##for solid in render_solids:
##    if solid.is_displacement:
##        glColor(1, 1, 1) # Hammer Default
##        for i, points in solid.displacement_triangles.items():
##            for point, alpha, normal in points:
##                Kd = (vector.dot(normal, (1, 1, 1)) / 16) + .75
##                # clamped from 0.75 to 0.75 + 1/32
##                blend = vector.lerp(solid.colour, solid.sides[i].blend_colour, alpha / 255)
##                glColor(*[Kd * x for x in blend])
##                glVertex(*point)
##glEnd()
##
### DISPLACEMENT NORMALS
##glColor(1, .75, 0)
##glBegin(GL_LINES)
##for solid in render_solids:
##    if solid.is_displacement:
##        for side_index, points in solid.displacement_vertices.items():
##            for point, alpha, normal in points:
##                glVertex(*point)
##                glVertex(*point + normal * 32)
##glEnd()
