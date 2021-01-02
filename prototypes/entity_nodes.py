"""An attempt at Firefox style tabs in Qt"""
import sys

from PyQt5 import QtWidgets


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook  # Python Debug


class entitiy_node(QtWidgets.QGraphicsItem):
    pass


app = QtWidgets.QApplication(sys.argv)
scene = QtWidgets.QGraphicsScene()
scene.addRect(0, 0, 32, 32)
window = QtWidgets.QGraphicsView()
window.setScene(scene)
window.show()
sys.exit(app.exec_())

# C++ Qt 81 - QGraphicsView and QGraphicsScene
# ^ https://www.youtube.com/watch?v=b35JF4LqtBs
# C++ Qt 82 - Custom QGraphicsItem
# ^ https://www.youtube.com/watch?v=hgDd2QspuDg

# Graphics View (part 1/3): Using GraphicsView Classes
# ^ https://www.youtube.com/watch?v=P9VG5LpU1lA
