#include "gl3.h"
//#include <GL/gl.h> // try GLEW
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
    int major, minor;
    SDL_GL_GetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, &major);
    SDL_GL_GetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, &minor);
    printf("Using OpenGL %d.%d (SDL)\n", major, minor);
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

    glGetIntegerv(GL_MAJOR_VERSION, &major);
    glGetIntegerv(GL_MINOR_VERSION, &minor);
    printf("Using OpenGL %d.%d (GL)\n", major, minor);

    // GL SETUP
    glClearColor(0.0, 0.75, 0.5, 0.0);
    glOrtho(-4.0, 4.0, -4.0, 4.0, 0.0, 1024.0);
    glEnableClientState(GL_VERTEX_ARRAY);
    glPointSize(8);

    // VERTEX BUFFER
    GLuint VERTEX_BUFFER;
    glGenBuffers(1, &VERTEX_BUFFER);
    glBindBuffer(GL_ARRAY_BUFFER, VERTEX_BUFFER);

    float vertices[24] = {-1,  1,  1,   1,  1,  1,   1, -1,  1,
                          -1, -1,  1,  -1,  1, -1,   1,  1, -1,
                           1, -1, -1,  -1, -1, -1}; // 8 * XYZ

    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 24, vertices, GL_STATIC_DRAW);
    //glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(float) * 24, vertices);

    // INDEX BUFFER
    GLuint INDEX_BUFFER;
    glGenBuffers(1, &INDEX_BUFFER);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER);
    
    unsigned int indices[8] = {0, 1, 2, 3, 4, 5, 6, 7};

    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(int) * 8, indices, GL_STATIC_DRAW);
    //glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, sizeof(int) * 8, indices);

    //float data[32]; 
    //glGetBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(float) * 24, vertices, &data);
    //glGetBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, sizeof(int) * 8, vertices, &data + 24);
    //printf("(%f %f %f)", data[0], data[1], data[2]);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, (GLvoid*)0);
    
    // SHADERS
    const char* vert_source[] = {"#version 300 es\nlayout(location = 0) in vec3 vpos;\nuniform mat4 MVP;\nvoid main()\n{\nglPosition = MVP * vpos;\n}\n"};

    const char* frag_source[] = {"#version 300 es\nlayout(location = 0) out mediump vec4 RGBA;\nvoid main()\n{\nRGBA = vec4(1, 1, 1, 1);\n}\n"};
    
    GLuint vert_shader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vert_shader, 1, vert_source, NULL);
    glCompileShader(vert_shader);

    GLuint frag_shader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(frag_shader, 1, frag_source, NULL);
    glCompileShader(frag_shader);
    
    GLuint shader_program = glCreateProgram();
    glAttachShader(shader_program, vert_shader);
    glAttachShader(shader_program, frag_shader);
    glLinkProgram(shader_program);
    glDetachShader(shader_program, vert_shader);
    glDetachShader(shader_program, frag_shader);

    glUseProgram(shader_program);
    float mvp[16];
    glGetFloatv(GL_PROJECTION_MATRIX, mvp);
    glUniform4fv(glGetUniformLocation(shader_program, "MVP"), 4, mvp);   

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

        glUseProgram(shader_program);
        glDrawArrays(GL_POINTS, 0, 8 * 4);
        glDrawElements(GL_POINTS, 8 * 4, GL_UNSIGNED_INT, (GLvoid*)0);

        glUseProgram(0);
        glBegin(GL_TRIANGLES);
          glVertex2i(1, -1.5);
          glVertex2i(0, 1.5);
          glVertex2i(-1, -1.5);
        glEnd();

        SDL_GL_SwapWindow(window); // PRESENT FRAME
    }
    // QUIT
    glDeleteBuffers(1, &VERTEX_BUFFER);
    glDeleteBuffers(1, &INDEX_BUFFER);
    SDL_DestroyWindow(window);
    SDL_Quit();    
    return 0;
}