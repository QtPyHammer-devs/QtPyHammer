import io
import json
import os
import subprocess
import sys

from PyQt5 import QtCore, QtWidgets
import vmf_tool

sys.path.insert(0, "../../")  # run this script from tests/prototypes/
from QtPyHammer.ui.viewport import MapViewport3D  # noqa: E402
from QtPyHammer.utilities.obj import Obj  # noqa: E402


# Qt needs the system exception handler remapped
# without this your python code will break silently, with no errors to trace
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
    sys.exit()
sys.excepthook = except_hook  # noqa: E305


app = QtWidgets.QApplication([])
app.folder = "../../"
app.preferences = QtCore.QSettings("../../configs/preferences.ini", QtCore.QSettings.IniFormat)
# window
window = QtWidgets.QMainWindow()
window.setWindowTitle("Visualise SourceTV (*.dem) file")
window.setStatusBar(QtWidgets.QStatusBar())
menu = QtWidgets.QMenuBar()
# File > Open
file_menu = menu.addMenu("&File")


file_dialog = QtWidgets.QFileDialog()
# ^ using a single QFileDialog helps Qt remember the last folder you browsed
def open_stv_demo():  # noqa: E302
    kwargs = {"parent": window, "caption": "Open...",
              "filter": "SourceTV demo file (*.dem)"}
    if sys.platform == "linux":
        kwargs["options"] = file_dialog.Option.DontUseNativeDialog
    filename, extention = file_dialog.getOpenFileName(**kwargs)
    console_in.setText(f"load {filename}")
    console_in.returnPressed.emit()
    window.statusBar().showMessage(filename)


open_file = file_menu.addAction("&Open", open_stv_demo, "Ctrl+O")
playback_menu = menu.addMenu("&Playback")
current_frame = 0
timer = QtCore.QTimer()
timer.setInterval(15)


def next_frame():
    global current_frame
    console_in.setText(f"frame {current_frame}")
    console_in.returnPressed.emit()
    current_frame += 1


timer.timeout.connect(next_frame)


def play_pause():
    if timer.isActive():
        timer.stop()
    else:
        timer.start()


playback_menu.addAction("&Play", play_pause, "Space")
window.setMenuBar(menu)

# main_widget
splitter = QtWidgets.QSplitter()
window.setCentralWidget(splitter)

viewport = MapViewport3D()
viewport.setMinimumSize(512, 512)
# we need to update the render manager
tf2_scout = Obj.load_from_file("scout.obj")
viewport.render_manager.add_obj_models(tf2_scout)
viewport.render_manager.dynamics[("obj_model", "scout.obj")] = {"position": [0, 128, -64]}
viewport.render_manager.draw_calls["obj_model"] = []
test2_vmf = vmf_tool.Vmf("../../Team Fortress 2/tf/mapsrc/test2.vmf")
viewport.render_manager.add_brushes(*test2_vmf.brushes.values())
splitter.addWidget(viewport)

# terminal interface
console_widget = QtWidgets.QWidget()
console_widget.setLayout(QtWidgets.QVBoxLayout())
console_out = QtWidgets.QTextEdit()
console_out.setMinimumSize(80 * 5, 25 * 12)
console_out.setReadOnly(True)
console_out.append("This is a terminal.  Please type a command:")
console_widget.layout().addWidget(console_out)
console_in = QtWidgets.QLineEdit()
# pointing wine at the coldmaps.exe on linux is hard
demo_REPL = subprocess.Popen("coldmaps_0.2.2.exe --demoplayer", stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True)


def send_command(process, command):  # This function by Tails8521
    console_out.append(command)
    console_in.clear()
    # by Tails8521:
    process.stdin.write(command + '\n')
    process.stdin.flush()
    output = process.stdout.readline()
    console_out.append(output)
    if command.startswith("frame "):
        update_player_models(output)
    elif command.startswith("load "):
        get_tickrate(output)
    return output
    # process stdout with .json, give data to viewport


console_in.returnPressed.connect(lambda: send_command(demo_REPL, console_in.text()))
console_widget.layout().addWidget(console_in)
# PIPE a virtual terminal in here
# stdin_widget.add(console_widget)
splitter.addWidget(console_widget)


def update_player_models(json_text):
    frame = json.load(io.StringIO(json_text))
    position = frame["result"]["player_entities"][0]["position"]
    x, y, z = position["x"], position["y"], position["z"]
    viewport.render_manager.dynamics[("obj_model", "scout.obj")]["position"] = [x, y, z]


def get_tickrate(json_text):
    demo_header = json.load(io.StringIO(json_text))["result"]
    frame_time = demo_header["duration"] / demo_header["frames"]
    timer.setInterval(int(1000 * frame_time))


# run the app
window.show()
app.exec_()
