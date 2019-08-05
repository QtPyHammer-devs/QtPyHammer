import fgdtools
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
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
    return ', '.join([f'{c} {ct}es' for ct, c in entity_counts_by_type.items()])
fgdtools.parser.Fgd.__repr__ = fgd_repr
fgdtools.parser.FgdEntity.__repr__ = lambda e: f'{e.class_type}: {e.name}'
fgdtools.parser.FgdEntityProperty.__repr__ = lambda p: f'{p.display_name}'
# End Monkey Patches

tf_fgd = fgdtools.parser.FgdParse('tf.fgd')
entities = [e for e in tf_fgd.entities if e.class_type in ('SolidClass', 'PointClass')]


layout = QtWidgets.QGridLayout()
# drop down list to choose entity
ent_selector = QtWidgets.QComboBox()
ent_index_map = {e.name: i for i, e in enumerate(entities)}
ent_selector.addItems(sorted(ent_index_map.keys()))
ent_selector.currentIndexChanged()
layout.addWidget(ent_selector, 0, 0)
# key | value fields for entities
...
# hints per entry
window.setLayout(layout)

# look at hammer screenies

window.show()

app.exec_()
