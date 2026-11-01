from cx_Freeze import setup, Executable


base = None
# if sys.platform == "win32":
#     base = "Win32GUI" # no console

build_exe_options = {
    "excludes": [
        "tkinter"],
    "includes": [
        "itertools",
        "numpy",
        "PyQt5"],
    "include_files": [
        "configs/",
        "shaders/"],
    "packages": [
        "OpenGL"]}

setup(
    name="QtPyHammer",
    version="0.0.6",
    description="QtPyHammer Map Editor",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "hammer.py",
            targetName="QtPyHammer.exe",
            icon="icons/QtPy.ico",
            base=base)])
