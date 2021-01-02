import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class TextureBrowser(QtWidgets.QDialog):
    # https://doc.qt.io/qt-5/qdialog.html
    def __init__(self, parent=None):
        super().__init__(parent)
        # pick a layout for the core widget
        # top has a scrolling page of texture thumbnails
        # bottom has filters, self.searchbar, OK & Cancel buttons

        main_layout = QtWidgets.QVBoxLayout()

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
        main_layout.addWidget(scroll)
        main_layout.addWidget(QtWidgets.QLabel("Search Options"))
        # list of checkboxes?
        # colour-range (hue) slider (.vtf reflectivity value)

        self.searchbar = QtWidgets.QLineEdit()
        main_layout.addWidget(self.searchbar)

        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(lambda: self.search(self.searchbar.text()))
        search_button.setDefault(1)

        main_layout.addWidget(search_button)

        buttonbox = QtWidgets.QDialogButtonBox
        buttons = buttonbox(buttonbox.Ok | buttonbox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def addTextureSquare(self, layout):
        image_label = QtWidgets.QLabel()
        # Placeholder Image
        magenta = b"\xFF\x00\xFF"
        black = b"\x00\x00\x00"
        data = magenta + black + black + magenta

        # Parse data into image
        image = QtGui.QImage(data, 2, 2, QtGui.QImage.Format_RGB888)
        image.setDevicePixelRatio(1 / 32)  # scale *32
        image_label.setPixmap(QtGui.QPixmap.fromImage(image))

        layout.addWidget(image_label)

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

    def addItem(self, item):
        self._item_list.append(item)

    def addSpacing(self, size):
        self.addItem(QtWidgets.QSpacerItem(size, 0, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum))

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
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
                space_x += wid.style().layoutSpacing(QtWidgets.QSizePolicy.PushButton,
                                                     QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
                space_y += wid.style().layoutSpacing(QtWidgets.QSizePolicy.PushButton,
                                                     QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical)

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


if __name__ == "__main__":
    def except_hook(cls, exception, traceback):
        """Get tracebacks for python called by Qt functions & classes"""
        sys.__excepthook__(cls, exception, traceback)

    sys.excepthook = except_hook
    app = QtWidgets.QApplication(sys.argv)
    browser = TextureBrowser()
    browser.setGeometry(128, 64, 576, 576)
    browser.show()

    app.exec_()
