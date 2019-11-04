import fgdtools
from itertools import chain
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class browser(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(browser, self).__init__(parent)
        ctx = parent.ctx # get ApplicationContext from MainWindow

        # should really load in the ApplicationContext as a @cached_property
        tf_fgd = fgdtools.parser.FgdParse(ctx.get_resource("fgds/tf.fgd")) # cannot load base.fgd
        entities = [e for e in chain(tf_fgd.entities, *[f.entities for f in tf_fgd.includes]) if e.class_type in ('PointClass', 'SolidClass')]
        entities = sorted(entities, key = lambda e: e.name) # sort alphabetically
        default_entity = entities.index(tf_fgd.entity_by_name('prop_static'))
        # prop_dynamic for flags and logic
        # team_control_point for more field types
        current_entity = entities[default_entity]

        base_widget = QtWidgets.QTabWidget()
        base_layout = QtWidgets.QVBoxLayout()
        base_layout.addWidget(base_widget)
        self.setLayout(base_layout)

        core_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        ent_select = QtWidgets.QComboBox()
        ent_select.addItems([e.name for e in entities])
        ent_select.setCurrentIndex(default_entity)
        ent_select.currentIndexChanged.connect(load_entity)
        load_entity(default_entity)
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
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addStretch(1)
        bottom_row.addWidget(QtWidgets.QPushButton('Cancel'))
        bottom_row.addWidget(QtWidgets.QPushButton('Apply'))
        layout.addLayout(bottom_row)
        core_tab.setLayout(layout)
        base_widget.addTab(core_tab, 'Core')
        comments_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(entity_label)
        layout.addWidget(QtWidgets.QTextEdit())
        layout.addLayout(bottom_row)
        comments_tab.setLayout(layout)
        base_widget.addTab(comments_tab, 'Comments')


    def load_entity(self, index): #SmartEdit toggle & owo what's this?
        global desc_label, table, entity_label, current_entity, bottom_row
        entity = entities[index]
        current_entity = entity
        entity_label = QtWidgets.QLabel(current_entity.name) # also entity's name property (if it has one), or 'Unnamed'
        try: # remove logic & flags tabs (if used)
            self.removeTab(2)
            self.removeTab(2)
        except:
            pass
        desc_label.setText(entity.description.split('.')[0]) # paragraph in fgd amendment
        properties = [*filter(lambda p: isinstance(p, fgdtools.parser.FgdEntityProperty), entity.properties)]
        inputs = [*filter(lambda i: isinstance(i, fgdtools.parser.FgdEntityInput), entity.properties)]
        outputs = [*filter(lambda o: isinstance(o, fgdtools.parser.FgdEntityOutput), entity.properties)]
        if len(inputs) > 0 or len(outputs) > 0: # AND no inputs recieved
            self.addTab(QtWidgets.QWidget(), 'Logic')
        entity_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout()
        # fill scroll area horizontally
        for i, p in enumerate(properties):
            if p.value_type == 'flags':
                flags_tab = QtWidgets.QWidget()
                flags_layout = QtWidgets.QVBoxLayout()
                flags_scroll = QtWidgets.QScrollArea()
                flags_list = QtWidgets.QVBoxLayout()
                flags_layout.addWidget(entity_label)
                for o in p.options:
                    flags_list.addWidget(QtWidgets.QCheckBox(o.display_name))
                flags_list.addStretch(1)
                flags_scroll.setLayout(flags_list)
                flags_layout.addWidget(flags_scroll)
                flags_layout.addLayout(bottom_row)
                flags_tab.setLayout(flags_layout)
                self.addTab(flags_tab, 'Flags')
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
    # need to be able to create / edit an entity with the browser
