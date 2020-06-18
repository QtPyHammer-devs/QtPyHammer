import os
import sys

from cx_Freeze import setup, Executable


current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"

configs = []
config_dir = current_dir + "QtPyHammer/configs/"
for file in os.listdir(config_dir):
    configs.append(os.path.join(config_dir, file))

shaders = []
shader_dir = current_dir + "QtPyHammer/utilities/shaders/"
for version in ("GLES_300", "GLSL_450"):
    for file in os.listdir(os.path.join(shader_dir, version)):
        shaders.append(os.path.join(shader_dir, version, file))

build_exe_options = {"excludes": ["tkinter"],
                     "includes": ["itertools", "numpy", "OpenGL", "PyQt5"],
                     "include_files": [*configs, *shaders], 
                     "packages": ["ops", "ui", "utilities"]}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "QtPyHammer",
        version = "0.0.6",
        description = "QtPyHammer Map Editor",
        options = {"build_exe": build_exe_options},
        executables = [Executable("QtPyHammer/hammer.py",
                                  targetName="QtPyHammer.exe",
                                  icon="icons/QtPy.ico",
                                  base=base)])
