import fgdtools
from itertools import chain
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QTabWidget()
window.setWindowTitle('Entity Browser')
window.setGeometry(640, 400, 640, 480)

# Monkey Patches
def fgd_repr(fgd):
    entity_counts_by_type = {}
    for entity in fgd.entities:
        if entity.class_type in entity_counts_by_type:
            entity_counts_by_type[entity.class_type] += 1
        else:
            entity_counts_by_type[entity.class_type] = 1
    ent_list = ', '.join([f'{c} {ct}es' for ct, c in entity_counts_by_type.items()])
    return f"<{fgd.__class__.__name__} containing {ent_list}>"

fgdtools.parser.Fgd.__repr__ = fgd_repr
fgdtools.parser.FgdEntity.__repr__ = lambda e: f"<{e.__class__.__name__} {e.class_type}: {e.name}>"
fgdtools.parser.FgdEntityProperty.__repr__ = lambda p: f"<{p.__class__.__name__} '{p.display_name}'>"
fgdtools.parser.FgdEntityInput.__repr__ = lambda i: f"<{i.__class__.__name__} '{i.name}'>"
fgdtools.parser.FgdEntityOutput.__repr__ = lambda o: f"<{o.__class__.__name__} '{o.name}'>"
# End Monkey Patches

tf_fgd = fgdtools.parser.FgdParse('tf.fgd')
entities = [e for e in chain(tf_fgd.entities, *[f.entities for f in tf_fgd.includes]) if e.class_type in ('PointClass', 'SolidClass')]
entities = sorted(entities, key = lambda e: e.name) # sort alphabetically
default_ent = entities.index(tf_fgd.entity_by_name('prop_static'))

core_tab = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout()
ent_selector = QtWidgets.QComboBox()
ent_selector.addItems([e.name for e in entities])
ent_selector.setCurrentIndex(default_ent)
layout.addWidget(ent_selector)
label = QtWidgets.QLabel('No Entity Selected')
layout.addWidget(label)
table = QtWidgets.QScrollArea()
layout.addWidget(table)


def load_entity(index):
    global label, table, window
    # find and remove flags tab if it exists
    label.setText(entities[index].description)
    widget = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()
    for i, p in enumerate(filter(lambda e: isinstance(e, fgdtools.parser.FgdEntityProperty), entities[index].properties)):
        if p.name == 'spawnflags':
            window.addTab(QtWidgets.QWidget(), 'Flags')
            continue
        layout.addWidget(QtWidgets.QLabel(p.name), i, 0)
        # look at type
        # spinbox? file browser?
        # remember shown value != saved value in .vmf
        layout.addWidget(QtWidgets.QLineEdit(str(p.default_value)), i, 1)
    widget.setLayout(layout)
    table.setWidget(widget)
    
        # make a class from a FgdEntity object
##class BasicEntitiy:
##    def __init__(self, base):
##        for property in base.properties:
        # consider type
        # property subclasses from BaseClass?
##            setattr(self, property.name, property.default_value)


ent_selector.currentIndexChanged.connect(load_entity)
load_entity(default_ent)


core_tab.setLayout(layout)
window.addTab(core_tab, 'Core')
window.addTab(QtWidgets.QWidget(), 'Logic')
window.show()
app.exec_()
