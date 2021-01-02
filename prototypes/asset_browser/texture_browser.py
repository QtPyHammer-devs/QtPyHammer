import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class TextureBrowser(QtWidgets.QDialog):
    # https://doc.qt.io/qt-5/qdialog.html
    def __init__(self):
        super(TextureBrowser, self).__init__(parent=None)
        # pick a layout for the core widget
        # top has a scrolling page of texture thumbnails
        # bottom has filters, searchbar, OK & Cancel buttons

        outerQV = QtWidgets.QVBoxLayout()

        # now this has scroll bar but it doesnt have flow layout
        scroll = QtWidgets.QScrollArea()
        groupbox = QtWidgets.QGroupBox("Textures")
        flow_layout = FlowLayout(margin=10)

        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout()

        # configure flow layout
        flow_layout.heightChanged.connect(container.setMinimumHeight)
        for i in range(400):
            self.addTextureSquare(flow_layout)

        # set configured layout to the groupbox
        groupbox.setLayout(flow_layout)

        container_layout.addWidget(groupbox)
        container_layout.addStretch()
        container.setLayout(container_layout)

        # configure scrollarea
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # set configured groupbox as widget of the scrollarea
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        # finally add scrollarea widget to the outer QVBoxLayout
        outerQV.addWidget(scroll)
        outerQV.addWidget(QtWidgets.QLabel("Search Options"))  # placeholder

        searchbar = QtWidgets.QLineEdit()
        outerQV.addWidget(searchbar)

        searchButton = QtWidgets.QPushButton("Search")
        searchButton.clicked.connect(lambda: self.search(searchbar.text()))
        searchButton.setDefault(1)

        outerQV.addWidget(searchButton)

        buttonbox = QtWidgets.QDialogButtonBox
        buttons = buttonbox(buttonbox.Ok | buttonbox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outerQV.addWidget(buttons)
        self.setLayout(outerQV)

    def addTextureSquare(self, layout):
        imagelabel = QtWidgets.QLabel()
        # Placeholder Image
        magenta = b"\xFF\x00\xFF"
        black = b"\x00\x00\x00"
        data = magenta + black + black + magenta

        # Parse data into image
        image = QtGui.QImage(data, 2, 2, QtGui.QImage.Format_RGB888)
        image.setDevicePixelRatio(1 / 32)  # scale *32
        imagelabel.setPixmap(QtGui.QPixmap.fromImage(image))

        layout.addWidget(imagelabel)

    def search(self, keyword):
        print(f"Trying to Search {keyword}!")


class FlowLayout(QtWidgets.QLayout):
    """A ``QLayout`` that aranges its child widgets horizontally and
    vertically.

    If enough horizontal space is available, it looks like an ``HBoxLayout``,
    but if enough space is lacking, it automatically wraps its children into
    multiple rows."""
    heightChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

        self._item_list = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):  # pylint: disable=invalid-name
        self._item_list.append(item)

    def addSpacing(self, size):  # pylint: disable=invalid-name
        self.addItem(QtWidgets.QSpacerItem(size, 0, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum))

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):  # pylint: disable=invalid-name
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):  # pylint: disable=invalid-name
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):  # pylint: disable=invalid-name,no-self-use
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):  # pylint: disable=invalid-name,no-self-use
        return True

    def heightForWidth(self, width):  # pylint: disable=invalid-name
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):  # pylint: disable=invalid-name
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):  # pylint: disable=invalid-name
        return self.minimumSize()

    def minimumSize(self):  # pylint: disable=invalid-name
        size = QtCore.QSize()

        for item in self._item_list:
            minsize = item.minimumSize()
            extent = item.geometry().bottomRight()
            size = size.expandedTo(QtCore.QSize(minsize.width(), extent.y()))

        margin = self.contentsMargins().left()
        size += QtCore.QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only=False):
        m = self.contentsMargins()
        effective_rect = rect.adjusted(+m.left(), +m.top(), -m.right(), -m.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            wid = item.widget()

            space_x = self.spacing()
            space_y = self.spacing()
            if wid is not None:
                space_x += wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
                space_y += wid.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton, QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical)

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        new_height = y + line_height - rect.y()
        self.heightChanged.emit(new_height)
        return new_height


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook  # For debugging python inside Qt Classes

app = QtWidgets.QApplication(sys.argv)
window = TextureBrowser()
window.setGeometry(128, 64, 576, 576)
window.show()

app.exec_()
