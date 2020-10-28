from PyQt5 import QtCore, QtGui, QtWidgets


def load_theme(filename):  # shouldn't this be in ops.theme?
    palette_ini = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
    palette = QtGui.QPalette()

    def read(ini_key, colour_group, colour_role):
        string = palette_ini.value(ini_key)
        colour = QtGui.QColor(*map(int, string.split(" ")))
        palette.setColor(colour_group, colour_role, colour)

    for group in ("Active", "Disabled", "Inactive"):
        palette_ini.beginGroup(group)
        group = getattr(palette, group)
        read("window", group, palette.Window)
        read("windowText", group, palette.WindowText)
        read("base", group, palette.Base)
        read("alternateBase", group, palette.AlternateBase)
        read("toolTipBase", group, palette.ToolTipBase)
        read("toolTipText", group, palette.ToolTipText)
        read("placeholderText", group, palette.PlaceholderText)
        read("text", group, palette.Text)
        read("button", group, palette.Button)
        read("buttonText", group, palette.ButtonText)
        read("brightText", group, palette.BrightText)
        read("light", group, palette.Light)
        read("midlight", group, palette.Midlight)
        read("dark", group, palette.Dark)
        read("mid", group, palette.Mid)
        read("shadow", group, palette.Shadow)
        read("highlight", group, palette.Highlight)
        read("highlightedText", group, palette.HighlightedText)
        read("link", group, palette.Link)
        read("linkVisited", group, palette.LinkVisited)
        palette_ini.endGroup()
    return palette


def save_theme(palette, filename):  # also for ops.theme?
    palette_ini = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)

    def write(ini_key, colour_group, colour_role):
        colour = palette.color(colour_group, colour_role)
        ini_value = f"{colour.red()} {colour.blue()} {colour.green()}"
        palette_ini.setValue(ini_key, ini_value)

    for group in ("Active", "Disabled", "Inactive"):
        palette_ini.beginGroup(group)
        group = getattr(palette, group)
        write("window", group, palette.Window)
        write("windowText", group, palette.WindowText)
        write("base", group, palette.Base)
        write("alternateBase", group, palette.AlternateBase)
        write("toolTipBase", group, palette.ToolTipBase)
        write("toolTipText", group, palette.ToolTipText)
        write("placeholderText", group, palette.PlaceholderText)
        write("text", group, palette.Text)
        write("button", group, palette.Button)
        write("buttonText", group, palette.ButtonText)
        write("brightText", group, palette.BrightText)
        write("light", group, palette.Light)
        write("midlight", group, palette.Midlight)
        write("dark", group, palette.Dark)
        write("mid", group, palette.Mid)
        write("shadow", group, palette.Shadow)
        write("highlight", group, palette.Highlight)
        write("highlightedText", group, palette.HighlightedText)
        write("link", group, palette.Link)
        write("linkVisited", group, palette.LinkVisited)
        palette_ini.endGroup()


class ThemeEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ThemeEditor, self).__init__(parent)
        form = QtWidgets.QFormLayout()
        form.addRow("role", ColourPicker())
        self.setLayout(form)
        # have a preview_widget
        # apply & cancel buttons


class ColourPicker(QtWidgets.QLabel):
    """A coloured label with it's own colour wheel"""

    def __init__(self, colour=(255, 255, 255), parent=None):
        super(QtWidgets.QLabel, self).__init__(parent)
        self.picker = QtWidgets.QColorDialog()
        self.picker.setCurrentColor(QtGui.QColor(*colour))
        self.setColour()
        self.picker.accepted.connect(self.setColour)

    def mousePressEvent(self, event):
        super(QtWidgets.QLabel, self).mousePressEvent(self)
        self.picker.exec()

    def setColour(self):
        """sets the label colour to the picker's selected colour"""
        colour = self.picker.selectedColor()
        pixels = colour.rgb().to_bytes(4, "little")
        image = QtGui.QImage(pixels, 1, 1, QtGui.QImage.Format_ARGB32)
        # need to scale the image up somehow, minimum label size?
        self.setPixmap(QtGui.QPixmap.fromImage(image))
