import itertools
import os
import textwrap

import fgdtools
from PyQt5 import QtCore, QtGui, QtWidgets

# from .. import utilities.entity


class browser(QtWidgets.QDialog):
    def __init__(self, entities, parent):
        super(browser, self).__init__(parent, QtCore.Qt.Tool)
        if len(entities) == 0:
            raise RuntimeError("No entites to browse!")
        self.setWindowTitle("Entity Browser")
        # self.setWindowIcon(parent.entity_icon)
        self.setGeometry(780, 220, 360, 640)
        # center with:
        # self.setGeometry(QStyle.alignedRect(QtCore.Qt.LefttoRight,QtCore.Qt.AlignCenter, self.size(), parent.parent.desktop().availableGeometry()))
        point_or_solid = lambda e: e.class_type in ("PointClass", "SolidClass")
        filtered_entities = list(filter(point_or_solid, entities))
        self.entities = sorted(filtered_entities, key=lambda e: e.name)
        default_entity = "prop_dynamic" # set in user config
        # test prop_dynamic for flags and logic
        # test team_control_point for more field types
        entity_names = [e.name for e in self.entities]
        self.current_index = entity_names.index(default_entity)
        self.current_entity = self.entities[self.current_index]

        self.base_widget = QtWidgets.QTabWidget()
        base_layout = QtWidgets.QVBoxLayout()
        base_layout.addWidget(self.base_widget)
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addStretch(1)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_button)
        apply_button = QtWidgets.QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        # TODO: extend self.accept to actually apply changes
        apply_button.setDefault(True)
        bottom_row.addWidget(apply_button)
        base_layout.addLayout(bottom_row)
        self.setLayout(base_layout)

        # the core entity handles (keys & values)
        core_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        ent_select = QtWidgets.QComboBox()
        ent_select.addItems([e.name for e in self.entities])
        ent_select.setCurrentIndex(self.current_index)
        ent_select.currentIndexChanged.connect(self.load_entity)
        ent_select_layout = QtWidgets.QHBoxLayout()
        ent_select_layout.addWidget(ent_select)
        ent_select_layout.addWidget(QtWidgets.QPushButton("Copy"))
        ent_select_layout.addWidget(QtWidgets.QPushButton("Paste"))
        self.smart_edit = QtWidgets.QPushButton("SmartEdit")
        self.smart_edit.setCheckable(True)
        self.smart_edit.setChecked(True)
        self.ent_form_map = {} # row: (name, display_name)
        def toggle_smart_edit():
            form = self.table.widget().layout()
            smartedit_on = self.smart_edit.isChecked()
            for row_index, names in self.ent_form_map.items():
                name, display_name = names
                other_name = display_name if smartedit_on else name
                label = form.itemAt(row_index, QtWidgets.QFormLayout.LabelRole)
                label.widget().setText(other_name)
        self.smart_edit.clicked.connect(toggle_smart_edit)
        ent_select_layout.addWidget(self.smart_edit)
        ent_select_layout.setStretch(0, 2)
        layout.insertLayout(0, ent_select_layout)
        self.desc_label = QtWidgets.QLabel("No Entity Selected")
        self.entity_label = QtWidgets.QLabel(self.current_entity.name)
        self.desc_label.setWordWrap(True) # have a "Read More..." button (link)
        layout.addWidget(self.desc_label)
        self.table = QtWidgets.QScrollArea()
        layout.addWidget(self.table)
        core_tab.setLayout(layout)
        self.base_widget.addTab(core_tab, "Core")
        # A whole tab for comments on the selected entity/entities
        comments_tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.entity_label)
        layout.addWidget(QtWidgets.QTextEdit()) # filter for .vmf breaking characters
        comments_tab.setLayout(layout)
        self.base_widget.addTab(comments_tab, "Comments")
        self.load_entity(self.current_index)

    def load_entity(self, index): # ADD SmartEdit toggle & tooltips
        entity = self.entities[index]
        self.current_entity = entity
        self.entity_label = QtWidgets.QLabel(self.current_entity.name)
        # ^ f"{entitiy.name} {'- ' + selection's targetname (if != '')}"
##        self.widget(1).layout().itemAt(0).setText(self.current_entity.name)
        # TODO: change comments tab's label to ^ (breaks atm)
        tabs_to_delete = []
        for i in range(self.base_widget.count()):
            tab_name = self.base_widget.tabText(i)
            if tab_name in ("Logic", "Flags"):
                tabs_to_delete.append(i)
        for i in reversed(tabs_to_delete):
            self.base_widget.removeTab(i)
        # ^ maybe recycle the old tabs?
        self.desc_label.setText(entity.description.split(".")[0]) # paragraph in fgd amendment
        properties = [*filter(lambda p: isinstance(p, fgdtools.parser.FgdEntityProperty), entity.properties)]
        inputs = [*filter(lambda i: isinstance(i, fgdtools.parser.FgdEntityInput), entity.properties)]
        outputs = [*filter(lambda o: isinstance(o, fgdtools.parser.FgdEntityOutput), entity.properties)]
        # split properly in some version of fgdtools (prob 1.0.0 but it's broken?)
        if len(inputs) > 0 or len(outputs) > 0: # OR ANY inputs recieved
            logic_widget = QtWidgets.QWidget() # <- make it's own class
            logic_widget.setLayout(QtWidgets.QVBoxLayout())
            logic_widget.layout().addWidget(QtWidgets.QLabel("Inputs"))
            logic_widget.layout().addWidget(QtWidgets.QLabel("Outputs"))
            self.base_widget.addTab(logic_widget, "Logic")
        entity_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout()
        for p in [p for p in properties if p.value_type == "flags"]: # loop once and make flags = p
            # should ask about having this simplified in fgdtools
            flags_tab = QtWidgets.QWidget()
            flags_layout = QtWidgets.QVBoxLayout()
            flags_scroll = QtWidgets.QScrollArea()
            flags_list = QtWidgets.QVBoxLayout()
            flags_layout.addWidget(self.entity_label)
            for o in p.options:
                flags_list.addWidget(QtWidgets.QCheckBox(o.display_name))
            flags_list.addStretch(1)
            flags_scroll.setLayout(flags_list)
            flags_layout.addWidget(flags_scroll)
            flags_tab.setLayout(flags_layout)
            self.base_widget.addTab(flags_tab, "Flags")
        self.ent_form_map = {} # row: (name, display_name)
        # also map property.name to value set in form
        # this will be sent back to the selection and added to the Edit Timeline
        for i, p in enumerate([p for p in properties if p.value_type != "flags"]):
            self.ent_form_map[i] = (p.name, p.display_name)
            # use comboboxes informed by model for anims and skins
            # Default Animation \/ ref, open, close
            # Skin \/ Red, Blue
            # skin naming will require prop catalogues (.csv ?)
            if p.value_type == "color255": # need something similar for lights
                selector = colour_picker(default=p.default_value)
            elif p.value_type == "choices":
                selector = QtWidgets.QComboBox()
                options = {i: o.value for i, o in enumerate(p.options)}
                selector.addItems([str(o.display_name) for o in p.options])
                selector.setCurrentIndex([i for i, v in options.items() if v == p.default_value][0])
            elif p.value_type == "integer":
                # set "skin" min & max from model (props)
                selector = QtWidgets.QSpinBox()
                selector.setMaximum(p.default_value) # fgd doesn't specify a max, a soft / adjustable max like blender would be nice
                selector.setValue(p.default_value)
            elif p.value_type == "studio": # model
                selector = model_picker(default=p.default_value)
            elif p.value_type == "target_destination":
                selector = QtWidgets.QLineEdit()
                # add a 3D / entity picker
                # selector. ??? .connect(highlight_row(i))
            else:
                selector = QtWidgets.QLineEdit(str(p.default_value))
            field_name = p.display_name if self.smart_edit.isChecked() else p.name
            field_label = QtWidgets.QLabel("<{}>".format(p.value_type) + field_name)
            if isinstance(p.description, str):
                description = textwrap.fill(p.description, width=40)
            else:
                description = p.display_name
            field_label.setToolTip(description)
            field_label.setWhatsThis(description)
            # doesn't appear to work
            if isinstance(selector, QtWidgets.QWidget):
                selector.setToolTip(description)
                selector.setWhatsThis(description)
            elif isinstance(selector, QtWidgets.QLayout):
                for i in range(selector.count()):
                    widget = selector.itemAt(i).widget()
                    if not isinstance(widget, QtWidgets.QWidget):
                        continue
                    widget.setToolTip(description)
                    widget.setWhatsThis(description)
            form.addRow(field_name, selector)

        entity_widget.setLayout(form)
        # add keyvalue button?, smartedit only?
        self.table.setWidget(entity_widget)
        # ensure this widget always scales to fit horizontally without scrolling
        # highlight properties that are not default
        # allow reset per-row for changed properties
        # allow re-ordering of properties, with a reset order option


class model_picker(QtWidgets.QHBoxLayout):
    def __init__(self, parent=None, default=""):
        super(QtWidgets.QHBoxLayout, self).__init__(parent)
        self.text_field = QtWidgets.QLineEdit(default)
        self.button = QtWidgets.QPushButton("Browse")
        self.model_browser = QtWidgets.QFileDialog() # FAKE FOR TESTS
        def pick_model(): # real deal should search vpks and grab actual mdls
            address = self.model_browser.getOpenFileName()[0]
            stripped_address = address.split("/")[-1].rpartition(".")[0]
            self.text_field.setText(stripped_address)
        self.button.clicked.connect(pick_model)
        self.addWidget(self.text_field)
        self.addWidget(self.button)


class colour_picker(QtWidgets.QHBoxLayout):
    def __init__(self, parent=None, default=""):
        super(QtWidgets.QHBoxLayout, self).__init__(parent)
        default_len = len(default.split())
        self.text_field = QtWidgets.QLineEdit(default)
        self.button = QtWidgets.QPushButton("Pick")
        self.text = lambda: self.text_field.text()
        self.setText = lambda t: self.text_field.setText(t)
        def pick_colour(): # variables must be locked to this row
            current_colour = QtGui.QColor(*map(int, self.text().split()[:3]))
            picker = QtWidgets.QColorDialog(current_colour)
            new_colour = picker.getColor()
            if new_colour.isValid(): # user did not cancel
                if default_len == 3:
                    self.setText("{} {} {}".format(*new_colour.getRgb()))
                elif default_len == 4:
                    try:
                        strength = self.text().split()[3]
                    except: # cannot get the strength from self.text
                        strength = default.split()[3]
                    self.setText("{} {} {} {}".format(*new_colour.getRgb()[:3], strength))
            # preview the colour, but how?
        self.button.clicked.connect(pick_colour)
        self.addWidget(self.text_field)
        self.addWidget(self.button)

    # make a class from a FgdEntity object
##class BasicEntitiy:
##    def __init__(self, base):
##        for property in base.properties:
    # consider type
    # property subclasses from BaseClass?
##            setattr(self, property.name, property.default_value)
    # need to be able to create / edit an entity with the browser
