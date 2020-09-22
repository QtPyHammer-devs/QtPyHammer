import subprocess
import sys
import time

from PyQt5 import QtCore, QtWidgets

sys.path.insert(0, "../../")  # run this script from prototypes/
from QtPyHammer.ui.viewport import MapViewport3D  # noqa: E402


# Qt needs the system exception handler remapped
# without this your python code will break silently, with no errors to trace
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
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
    ...  # pass the demo to the viewport
    window.statusBar().showMessage(filename)


open_file = file_menu.addAction("&Open", open_stv_demo, "Ctrl+O")
window.setMenuBar(menu)

# main_widget
main_widget = QtWidgets.QWidget()
main_widget.setLayout(QtWidgets.QHBoxLayout())
window.setCentralWidget(main_widget)

viewport = MapViewport3D()
viewport.setMinimumSize(512, 512)
# we need to update the render manager
# viewport.render_manager.add_renderable("obj". scout_model)
main_widget.layout().addWidget(viewport)

# terminal interface
console_widget = QtWidgets.QWidget()
console_widget.setLayout(QtWidgets.QVBoxLayout())
console_out = QtWidgets.QTextEdit()
console_out.setMinimumSize(80 * 5, 25 * 12)
console_out.setReadOnly(True)
console_out.append("This is a terminal.  Please type a command:")
console_widget.layout().addWidget(console_out)
console_in = QtWidgets.QLineEdit()
demo_REPL = subprocess.Popen("Tails_demo_reader.exe", stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True)


def send_command(process, command):  # This function by Tails8521
    console_out.append(command)
    console_in.clear()
    # by Tails8521:
    process.stdin.write(command + '\n')
    process.stdin.flush()
    time_before = time.perf_counter()
    output = process.stdout.readline()
    time_after = time.perf_counter()
    return output, time_after - time_before
    # process stdout with .json, give data to viewport


console_in.returnPressed.connect(lambda: send_command(demo_REPL, console_in.text()))
console_widget.layout().addWidget(console_in)
# PIPE a virtual terminal in here
# stdin_widget.add(console_widget)
main_widget.layout().addWidget(console_widget)

# run the app
window.show()
app.exec_()
