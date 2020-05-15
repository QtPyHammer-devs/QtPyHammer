#!/bin/sh
gcc sdl_dynamic_draw.c `sdl2-config --cflags --libs` -lGL -lm -o sdl_dynamic_draw -ggdb3
