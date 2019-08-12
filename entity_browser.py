import fgdtools
from itertools import chain
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

def except_hook(cls, exception, traceback): #for PyQt debugging
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

tf_fgd = fgdtools.parser.FgdParse('bin/tf.fgd')

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

entities = [e for e in chain(tf_fgd.entities, *[f.entities for f in tf_fgd.includes]) if e.class_type in ('PointClass', 'SolidClass')]
entities = sorted(entities, key = lambda e: e.name) # sort alphabetically
default_entity = entities.index(tf_fgd.entity_by_name('prop_static'))
# prop_dynamic for flags and logic
# team_control_point for more field types
current_entity = entities[default_entity]

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QTabWidget()
window.setWindowTitle('Entity Browser')
window.setGeometry(640, 400, 640, 480)

# make the whole window a class for loading on a button / key in the main program
core_tab = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout()
ent_select = QtWidgets.QComboBox()
ent_select.addItems([e.name for e in entities])
ent_select.setCurrentIndex(default_entity)
ent_select_layout = QtWidgets.QHBoxLayout()
ent_select_layout.addWidget(ent_select)
ent_select_layout.addWidget(QtWidgets.QPushButton('Copy'))
ent_select_layout.addWidget(QtWidgets.QPushButton('Paste'))
ent_select_layout.setStretch(0, 2)
layout.insertLayout(0, ent_select_layout)
desc_label = QtWidgets.QLabel('No Entity Selected')
entity_label = QtWidgets.QLabel(current_entity.name)
desc_label.setWordWrap(True) # have a "Read More..." button (link)
layout.addWidget(desc_label)
table = QtWidgets.QScrollArea()
layout.addWidget(table)


def load_entity(index): #SmartEdit toggle & owo what's this?
    global desc_label, table, window, entity_label, current_entity
    entity = entities[index]
    current_entity = entity
    entity_label = QtWidgets.QLabel(current_entity.name) # also entity's name property (if it has one), or 'Unnamed'
    try: # remove logic & flags tabs (if used)
        window.removeTab(2)
        window.removeTab(2)
    except:
        pass
    desc_label.setText(entity.description.split('.')[0]) # paragraph in fgd amendment
    properties = [*filter(lambda p: isinstance(p, fgdtools.parser.FgdEntityProperty), entity.properties)]
    inputs = [*filter(lambda i: isinstance(i, fgdtools.parser.FgdEntityInput), entity.properties)]
    outputs = [*filter(lambda o: isinstance(o, fgdtools.parser.FgdEntityOutput), entity.properties)]
    if len(inputs) > 0 or len(outputs) > 0: # AND no inputs recieved
        window.addTab(QtWidgets.QWidget(), 'Logic')
    entity_widget = QtWidgets.QWidget()
    form = QtWidgets.QFormLayout()
    form.setAlignment(QtCore.Qt.AlignJustify)
    for i, p in enumerate(properties):
        if p.value_type == 'flags':
            flags_tab = QtWidgets.QWidget()
            flags_layout = QtWidgets.QVBoxLayout()
            flags_scroll = QtWidgets.QScrollArea()
            flags_list = QtWidgets.QVBoxLayout()
            flags_list.setSpacing(0)
            flags_layout.addWidget(entity_label)
            for o in p.options:
                flags_list.addWidget(QtWidgets.QCheckBox(o.display_name))
            flags_scroll.setLayout(flags_list)
            flags_layout.addWidget(flags_scroll)
            flags_tab.setLayout(flags_layout)
            window.addTab(flags_tab, 'Flags')
            print(p, p.options[0].__dict__) # [o.name for o in p.options]
        # use comboboxes informed by model for anims and skins
        # when props change consistency will be difficult
        # having a csv or similar naming skins would be neat
        # matching teams to numbers etc.
        elif p.value_type == 'choices':
            selector = QtWidgets.QComboBox()
            options = {i: o.value for i, o in enumerate(p.options)}
            selector.addItems([str(o.display_name) for o in p.options])
            selector.setCurrentIndex([i for i, v in options.items() if v == p.default_value][0])
            form.addRow(p.display_name, selector)
        elif p.value_type == 'integer':
            # set 'skin' min & max from model (props)
            selector = QtWidgets.QSpinBox()
            selector.setValue(p.default_value)
            form.addRow(p.display_name, selector)
        elif p.value_type == 'studio': # model
            selector = QtWidgets.QHBoxLayout()
            address_bar = QtWidgets.QLineEdit(p.default_value)
            selector.addWidget(address_bar)
            button = QtWidgets.QPushButton('Browse...')
            selector.addWidget(button) # connect to model browser
            model_browser = QtWidgets.QFileDialog() # FAKE FOR TESTS
            def get_file_address():
                address = model_browser.getOpenFileName()[0]
                # {tf_folder}/models/{address_bar.text}.mdl == actual address
                # cleanup accordingly
                stripped_address = address.split('/')[-1].rpartition('.')[0]
                # stripped_address = address.lstrip(f'{tf_folder}/models/')
                address_bar.setText(stripped_address)
            button.clicked.connect(get_file_address)
            form.addRow(p.display_name, selector)
        else:
            form.addRow(p.display_name, QtWidgets.QLineEdit(str(p.default_value)))
    entity_widget.setLayout(form)
    table.setWidget(entity_widget)
    
        # make a class from a FgdEntity object
##class BasicEntitiy:
##    def __init__(self, base):
##        for property in base.properties:
        # consider type
        # property subclasses from BaseClass?
##            setattr(self, property.name, property.default_value)


ent_select.currentIndexChanged.connect(load_entity)
# what we attach here should be contextual
# have a function that checks the context and delegates?
load_entity(default_entity)


core_tab.setLayout(layout)
window.addTab(core_tab, 'Core')
comments_tab = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout()
layout.addWidget(entity_label)
layout.addWidget(QtWidgets.QTextEdit())
comments_tab.setLayout(layout)
window.addTab(comments_tab, 'Comments')
window.show()
app.exec_()

if __name__ == "__main__":
    print('loading prop_static, prop_dynamic...')
    prop_static = tf_fgd.entity_by_name('prop_static')
    prop_dynamic = tf_fgd.entity_by_name('prop_dynamic')
