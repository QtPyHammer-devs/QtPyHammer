#include "gl3.h"
#include <SDL.h>
#include <SDL_opengl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

int main()//int argument_count, char *argument_value[])
{
    //int width = atoi(argument_value[1]);
    //int height = atoi(argument_value[2]);

    SDL_Init(SDL_INIT_VIDEO);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
    int maj, min;
    SDL_GL_GetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, &maj);
    SDL_GL_GetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, &min);
    printf("Using OpenGL %d.%d (SDL)\n", maj, min);
    SDL_Window *window = SDL_CreateWindow("OpenGL window",
                  SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                  720, 576, SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS);
    if (window == NULL) {
        printf("Couldn't make a window: %s\n", SDL_GetError());
        return 1;
    }

    SDL_GLContext context = SDL_GL_CreateContext(window);
    if (context == NULL) {
        printf("Couldn't Initialise GL context: %s\n", SDL_GetError());
        return 1;
    }

    glGetIntegerv(GL_MAJOR_VERSION, &maj);
    glGetIntegerv(GL_MINOR_VERSION, &min);
    printf("Using OpenGL %d.%d (GL)\n", maj, min);

    // GL SETUP
    glClearColor(0.0, 0.75, 0.5, 0.0);
    glOrtho(-2.0, 2.0, -2.0, 2.0, 0.0, 1024.0);
    glEnableClientState(GL_VERTEX_ARRAY);
    glPointSize(8);

    // VERTEX BUFFER
    GLuint VERTEX_BUFFER;
    glGenBuffers(1, &VERTEX_BUFFER);
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER);
    glBufferData(GL_ARRAY_BUFFER, 256, NULL, GL_DYNAMIC_DRAW);

    float vertices[24] = {-1,  1,  1,   1,  1,  1,   1, -1,  1,
                          -1, -1,  1,  -1,  1, -1,   1,  1, -1,
                           1, -1, -1,  -1, -1, -1}; // 8 * XYZ

    glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(float) * 24, vertices);

    // INDEX BUFFER
    GLuint INDEX_BUFFER;
    glGenBuffers(1, &INDEX_BUFFER);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 256, NULL, GL_DYNAMIC_DRAW);
    
    GLubyte indices[8] = {0, 1, 2, 3, 4, 5, 6, 7};

    glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, sizeof(GLubyte) * 8, indices);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, (GLvoid*)0);
    
    // SHADERS
    const GLchar *vert_source = "#version 300 es\nlayout(location = 0) in vec3 vpos;\nuniform mat4 MVP;\nvoid main()\n{\nglPosition = MVP * vpos;\n}\n";

    const GLchar *frag_source = "#version 300 es\nlayout(location = 0) out mediump vec4 RGBA;\nvoid main()\n{\nRGBA = vec4(1, 1, 1, 1);\n}\n";
    
    GLuint vert_shader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vert_shader, &vert_source);
    glCompileShader(vert_shader);

    GLuint frag_shader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(frag_shader, &frag_source);
    glCompileShader(frag_shader);
    
    GLuint shader_program = glCreateProgram();
    glAttachShader(shader_program, vert_shader);
    glAttachShader(shader_program, frag_shader);
    glLinkProgram(shader_program);
    glDetachShader(shader_program, vert_shader);
    glDetachShader(shader_program, frag_shader);

    glUseProgram(shader_progam);
    float mvp[16];
    glGetFloatv(GL_PROJECTION_MATRIX, &mvp);
    glUniform4fv(glGetUniformLocation(shader_program, "MVP"), mvp);   

    bool running = true;
    SDL_Event event;
    while(running)
    {
        while(SDL_PollEvent(&event) != 0)
        {
            switch (event.type)
            {
                case SDL_QUIT:
                    running = false;
                    break; // GOTO QUIT
                case SDL_KEYDOWN:
                    switch (event.key.keysym.sym)
                    {
                        case SDLK_ESCAPE:
                            running = false;
                            break; // GOTO QUIT
                    }
            }
        }

        // DRAW LOOP
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        glDrawArrays(GL_POINTS, 0, 8);
        glDrawElements(GL_POINTS, 8, GL_UNSIGNED_BYTE, (GLvoid*)0);

        /*
        glBegin(GL_TRIANGLES);
          glVertex2i(1, -1.5);
          glVertex2i(0, 1.5);
          glVertex2i(-1, -1.5);
        glEnd();
        */
        
        SDL_GL_SwapWindow(window); // PRESENT FRAME
    }
    // QUIT
    glDeleteBuffers(1, &VERTEX_BUFFER);
    glDeleteBuffers(1, &INDEX_BUFFER);
    SDL_DestroyWindow(window);
    SDL_Quit();    
    return 0;
}
