import os
import sys

from cx_Freeze import setup, Executable


current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"

build_exe_options = {"excludes": ["tkinter"],
                     "includes": ["ctypes", "itertools", "struct", "sys", "time",
                                  "numpy", "PyQt5", "sdl2"],
                     "packages": ["OpenGL"]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name = "qt_gl_render_manager",
      version = "1.0",
      description = "cx_Freeze build test",
      options = {"build_exe": build_exe_options},
      executables = [Executable("qt_gl_render_manager.py",
                                targetName="qt_gl_render_manager.exe",
                                icon="../../QtPyHammer/icons/QtPy.ico",
                                base=base)])
