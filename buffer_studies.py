import colorsys
import ctypes
import enum
import itertools
import numpy as np # for vertex buffers Numpy is needed (available through pip)
from OpenGL.GL import * # Installed via pip (PyOpenGl 3.1.0)
from OpenGL.GL.shaders import compileShader, compileProgram
from OpenGL.GLU import * # PyOpenGL-accelerate 3.1.0 requires MSVC 2015
# get precompiled binaries if you can, it's much less work
from sdl2 import * #Installed via pip (PySDL2 0.9.5)
# requires SDL2.dll (steam has a copy in it's main directory)
# and an Environment Variable (PYSDL2_DLL_PATH)
# PYSDL2_DLL_PATH must point to the folder containing the DLL
# this makes loading SDL2 addons with their DLLs in the same folders very easy
import time

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
    SDL_Init(SDL_INIT_VIDEO)
    window = SDL_CreateWindow(b'SDL2 OpenGL', SDL_WINDOWPOS_CENTERED,  SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS)
    glContext = SDL_GL_CreateContext(window)
    SDL_GL_SetSwapInterval(0)
    glClearColor(0.1, 0.1, 0.1, 0.0)
    glColor(1, 1, 1)
    gluPerspective(90, width / height, 0.1, 4096 * 4)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_BACK, GL_LINE)
    glFrontFace(GL_CW)
    glPointSize(4)

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

    global solid
    string_solids = []
    for brush in imported_vmf.world.solids:
        # bootleg auto-visgroup
        if not any([face.material == 'TOOLS/SKIP' or face.material == 'TOOLS/HINT' or 'CLIP' in face.material.upper() for face in brush.sides]):
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
        except Exception as exc: # find buggy brushes for testing & recovery
##            print(f"Invalid solid! (id {brush.id})")
##            print(exc, '\n')
            pass

    brush_triangles = list(itertools.chain(*[s.triangles for s in solids]))
    offset_index_map = lambda B, O: [(S + O, L) for S, L in B.index_map] # B? S? O? L?
    brush_index_map = [s.index_map for s in solids]

    GLES_MODE = False
    try: # GLSL 450
        # Vertex Shaders
        vert_shader_brush = compileShader(open('shaders/GLSL_450/brush.vert', 'rb'), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open('shaders/GLSL_450/displacement.vert', 'rb'), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_flat_brush = compileShader(open('shaders/GLSL_450/flat_brush.frag', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_flat_displacement = compileShader(open('shaders/GLSL_450/flat_displacement.frag', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_stripey_brush = compileShader(open('shaders/GLSL_450/stripey_brush.frag', 'rb'), GL_FRAGMENT_SHADER)
    except RuntimeError as exc: # Check supported shader versions instead
        GLES_MODE = True # GLES 3.00
        # Vertex Shaders
        vert_shader_brush = compileShader(open('shaders/GLES_300/brush.vert', 'rb'), GL_VERTEX_SHADER)
        vert_shader_displacement = compileShader(open('shaders/GLES_300/displacement.vert', 'rb'), GL_VERTEX_SHADER)
        # Fragment Shaders
        frag_shader_flat_brush = compileShader(open('shaders/GLES_300/flat_brush.frag', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_flat_displacement = compileShader(open('shaders/GLES_300/flat_displacement.frag', 'rb'), GL_FRAGMENT_SHADER)
        frag_shader_stripey_brush = compileShader(open('shaders/GLES_300/stripey_brush.frag', 'rb'), GL_FRAGMENT_SHADER)
##        raise exc # to debug GLSL 4.5 shaders
    # Programs
    program_flat_brush = compileProgram(vert_shader_brush, frag_shader_flat_brush)
    program_flat_displacement = compileProgram(vert_shader_displacement, frag_shader_flat_displacement)
    program_stripey_brush = compileProgram(vert_shader_brush, frag_shader_stripey_brush)
    glLinkProgram(program_flat_brush)
    glLinkProgram(program_flat_displacement)
    glLinkProgram(program_stripey_brush)

    if GLES_MODE == True: # set uniform locations in the shaders to eliminate the need for this block
        glUseProgram(program_flat_brush)
        uniform_brush_matrix = glGetUniformLocation(program_flat_brush, 'ModelViewProjectionMatrix')
        glUseProgram(program_flat_displacement)
        uniform_displacement_matrix = glGetUniformLocation(program_flat_displacement, 'ModelViewProjectionMatrix')
        glUseProgram(program_stripey_brush)
        uniform_stripey_matrix = glGetUniformLocation(program_flat_brush, 'ModelViewProjectionMatrix')
        glUseProgram(0)

    vertices = []
    indices = []
    solid_map = dict()
    displacement_ids = []
    for solid in solids:
        if solid.is_displacement:
            displacement_ids.append(solid.id)
        solid_map[solid.id] = (len(indices), len(solid.indices))
        vertices += solid.vertices
        indices += [len(vertices) + i for i in solid.indices]
    vertices = tuple(itertools.chain(*vertices))

    # TODO: don't render solids that are also displacements
    # TODO: render displacements from the buffer
    
    ### ====== BUFFER ====== ###
    # solid verts | disp verts #
    ############################

    # Vertex Buffer
    VERTEX_BUFFER, INDEX_BUFFER = glGenBuffers(2)
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER)
    glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
    # Index Buffer
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, np.array(indices, dtype=np.uint32), GL_STATIC_DRAW)
    # Vertex Format
    glEnableVertexAttribArray(0) # vertex_position
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(0))
    glEnableVertexAttribArray(1) # vertex_normal
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(12))
    glEnableVertexAttribArray(2) # vertex_uv
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 44, GLvoidp(24))
    glEnableVertexAttribArray(4) # editor_colour
    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 44, GLvoidp(32))
##    # blend_alpha (displacement)
##    glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 44, GLvoidp(12)) # replace vertex_normal

    print(vmf_path)
    print(f'{len(solids)} brushes loaded succesfully!')
    print(f'{len(vertices) // 33:,} TRIANGLES')
    print(f'{len(vertices) * 4 // 1024:,}KB')
    print('import took {:.2f} seconds'.format(time.time() - start_import))

    # STATIC BUFFER (UTILITIES)
    # Skybox, 3D grid, Origin Point
    # Editor Props (playerspawn, lights, sprite, path_track)

    CAMERA = camera.freecam((160, -160, 160), None, 128)
    render_solids = [s for s in solids if (s.center - CAMERA.position).sqrmagnitude() < 1024]
    rendered_ray = []

    SDL_SetRelativeMouseMode(SDL_TRUE)
    SDL_CaptureMouse(SDL_TRUE)

    mousepos = vector.vec2(-180, 120) # overrides start angle
    keys = []
            
    tickrate = 1 / 0.015
    old_time = time.time()
    event = SDL_Event()
    while True:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT or event.key.keysym.sym == SDLK_ESCAPE and event.type == SDL_KEYDOWN:
                SDL_GL_DeleteContext(glContext)
                SDL_DestroyWindow(window)
                SDL_Quit()
                return False
            if event.type == SDL_KEYDOWN:
                if event.key.keysym.sym not in keys:
                    keys.append(event.key.keysym.sym)
            if event.type == SDL_KEYUP:
                while event.key.keysym.sym in keys:
                    keys.remove(event.key.keysym.sym)
            if event.type == SDL_MOUSEBUTTONDOWN:
                keys.append(event.button.button)
            if event.type == SDL_MOUSEBUTTONUP:
                while event.button.button in keys:
                    keys.remove(event.button.button)
            if event.type == SDL_MOUSEMOTION:
                mousepos += vector.vec2(event.motion.xrel, event.motion.yrel)
                SDL_WarpMouseInWindow(window, width // 2, height // 2)
            if event.type == SDL_MOUSEWHEEL:
                if CAMERA.speed + event.wheel.y * 32 > 0: # speed limits
                    CAMERA.speed += event.wheel.y * 32
            if event.type == SDL_DROPFILE:
                # load event.drop.file
                # .vmf -> new tab
                # .lin / .prt -> match to vmf
                pass

        dt = time.time() - old_time
        while dt >= 1 / tickrate:
            # use KEYTIME to delay input repeat
            # KEYTIME
            # KEYTIME_COOLDOWN (time since key pressed with a limit of X seconds)
            CAMERA.update(mousepos, keys, 1 / tickrate)
            render_solids = [s for s in solids if (s.center - CAMERA.position).magnitude() < 2048]
            if SDLK_r in keys:
                CAMERA = camera.freecam(None, None, 128)
            if SDLK_BACKQUOTE in keys:
                print(f'CAMERA @ {CAMERA.position:.3f} & {CAMERA.rotation:.3f}')
                print(f'Currently rendering {len(render_solids)} brushes')
                
                console_loop = True
                while console_loop:
                    console_input = input('>>> ')
                    if console_input == 'exit':
                        print('Exited Console')
                        console_loop = False
                        break
                    try:
                        print(eval(console_input))
                    except Exception as exc:
                        print(f'{exc.__class__.__name__}: {exc}')
                        
            if SDL_BUTTON_LEFT in keys:
                ray_start = CAMERA.position
                ray_dir = vector.vec3(0, 1, 0).rotate(*-CAMERA.rotation)
                rendered_ray = [ray_start, ray_start + (ray_dir * 4096)]
                # calculate collisions
            dt -= 1 / tickrate
            old_time = time.time()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        CAMERA.set()
        if GLES_MODE:
            MVP_matrix = np.array(glGetFloatv(GL_MODELVIEW_MATRIX), np.float32)
        

        # draw brushes
        glUseProgram(program_stripey_brush)
        if GLES_MODE:
            glUniformMatrix4fv(uniform_stripey_matrix, 1, GL_FALSE, MVP_matrix)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, GLvoidp(0))
        glUseProgram(0)

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
        glLineWidth(2)
        glColor(.25, .25, .25)
        glBegin(GL_LINES)
        for x in range(-32, 33):
            x = x * 64
            glVertex(x, -2048, 0)
            glVertex(x, 0, 0)
            glVertex(x, 0, 0)
            glVertex(x, 2048, 0)
        for y in range(-32, 33):
            y = y * 64
            glVertex(-2048, y, 0)
            glVertex(0, y, 0)
            glVertex(0, y, 0)
            glVertex(2048, y, 0)
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

        glPopMatrix()
        SDL_GL_SwapWindow(window)

if __name__ == '__main__':
    try:
##        main('tests/vmfs/test.vmf')
##        main('tests/vmfs/test2.vmf')
##        main('tests/vmfs/sdk_pl_goldrush.vmf')
        main('tests/vmfs/pl_upward_d.vmf')
    except Exception as exc:
        SDL_Quit()
        raise exc
##    import sys
##    for file in sys.argv[1:]:
##        main(file)
