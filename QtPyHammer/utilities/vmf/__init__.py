"""https://github.com/snake-biscuits/vmf_tool"""
# TODO: Functions for handling the horrible visgroup system
# e.g. "visgroupid" "7"\n"visgroupid" "8" = {"visgroupid": ["7", "8"]}


def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    elif word.endswith('ex'): # vertex -> vertices
        return word[:-2] + 'ices'
    else: # side -> sides
        return word + 's'


def singularise(word):
    if word.endswith('ves'): # self <- selves
        return word[:-3] + 'f'
    elif word.endswith('ies'): # body <- bodies
        return word[:-3] + 'y'
    elif word.endswith('ices'): # vertex <- vertices
        return word[:-4] + 'ex'
    # in the face of ambiguity, refuse the temptation to guess
    elif word.endswith('s'): # side <- sides
        return word[:-1]
    else:
        return word # assume word is already singular


class namespace: # VMF COULD OVERLOAD METHODS
    """Nested Dicts -> Nested Objects"""
    def __init__(self, nested_dict=dict()):
        for key, value in nested_dict.items() if isinstance(nested_dict, dict) else nested_dict.__dict__.items():
            if isinstance(value, dict):
                self[key] = namespace(value)
            elif isinstance(value, list):
                self[key] = [namespace(i) for i in value]
            else:
                self[key] = value

    def __setitem__(self, index, value):
        setattr(self, str(index), value)

    def __getitem__(self, index):
        return self.__dict__[str(index)]

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __len__(self):
        return len(self.__dict__.keys())

    def __repr__(self):
        attrs = []
        for attr_name, attr in self.items():
            if " " in attr_name:
                attr_name = "{}".format(attr_name)
            attr_string = "{}: {}".format(attr_name, attr.__class__.__name__)
            attrs.append(attr_string)
        return "<namespace({})>".format(", ".join(attrs))

    def items(self):
        for k, v in self.__dict__.items():
            yield (k, v)


class scope:
    """Array of indices into a nested array"""
    def __init__(self, tiers=[]):
        self.tiers = tiers

    def __repr__(self):
        repr_strings = []
        for tier in self.tiers:
            if isinstance(tier, str):
                if " " in tier or tier[0].lower() not in "abcdefghijklmnopqrstuvwxyz":
                    repr_strings.append("['{}']".format(tier))
                else:
                    repr_strings.append(".{}".format(tier))
            else:
                repr_strings.append("[{}]".format(tier))
        return "".join(repr_strings)

    def add(self, tier):
        """Go a layer deeper"""
        self.tiers.append(tier)

    def increment(self): # does not check if tiers[-1] is an integer
        self.tiers[-1] += 1

    def get_from(self, nest):
        """Gets the item stored in nest which this scope points at"""
        target = nest
        for tier in self.tiers:
            target = target[tier]
        return target

    def retreat(self):
        """Retreat up 1 tier (2 tiers for plurals)"""
        popped = self.tiers.pop(-1)
        if isinstance(popped, int):
            self.tiers.pop(-1)

    def remove_from(self, nest): # used for changing singulars into plurals
        """Delete the item stored in nest which this scope points at"""
        target = nest
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1: # must set from tier above
                target.pop(tier)
            else:
                target = target[tier]
        # stop pointing at deleted index
        self.retreat()
        # unsure what will happen when deleting an item from a plural
        # also unsre what SHOULD happen when deleting an item from a plural

    def set_in(self, nest, value):
        """Sets the item stored in nest which this scope points at to value"""
        target = nest
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1: # must set from tier above
                target[tier] = value # could be creating this value
            else:
                target = target[tier]

# LOADING BAR IMPLEMENTATION
# every X (kwarg) lines call progress function (kwarg)
# -- likely lambda p: loading_bar.setProgress(p)
# def parse(lines, loading_func=loading_bar.set_progress, update_freq=100,
#           log=vmf_interface.log, extra_tasks={"solid": ...})

# on close ("}"):
# completed object = current.scope.tiers[-1]
# if completed_object in loading_funcs:
#       loading_funcs[completed_object].__call__(complete_object)
# where: loading_funcs = {"solid": load_brush,
#                        "entity": load_entitiy}
# and:
# load_brush = lambda b: vmf_interface.add_brushes(utilities.solids.import(b))
# load_entity = lambda e: vmf_interface.add_entities(utilities.entities.import(e))

def parse_lines(iterable):
    """String or .vmf file to nested namespace"""
    nest = namespace({})
    current_scope = scope([])
    previous_line = ''
    for line_number, line in enumerate(iterable):
        try:
            new_namespace = namespace({'_line': line_number})
            current_target = current_scope.get_from(nest)
            line = line.strip()  # cleanup spacing
            if line == "" or line.startswith("//"): # ignore blank / comments
                continue
            elif line =="{": # START declaration
                current_keys = current_target.__dict__.keys()
                plural = pluralise(previous_line)
                if previous_line in current_keys: # NEW plural
                    current_target[plural] = [current_target[previous_line]] # create plural from old singular
                    current_target.__dict__.pop(previous_line) # delete singular
                    current_target[plural].append(new_namespace) # second entry
                    current_scope.add(plural)
                    current_scope.add(1) # point at new_namespace
                elif plural in current_keys: # APPEND plural
                    current_scope.add(plural) # point at plural
                    current_scope.get_from(nest).append(new_namespace)
                    current_scope.add(len(current_scope.get_from(nest)) - 1) # current index in plural
                else: # NEW singular
                    current_scope.add(previous_line)
                    current_scope.set_in(nest, new_namespace)
            elif line == '}': # END declaration
                current_scope.retreat()
            elif '" "' in line: # KEY VALUE
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                current_target[key] = value
            elif line.count(' ') == 1:
                key, value = line.split()
                current_target[key] = value
            previous_line = line.strip('"')
        except Exception as exc:
            print("error on line {0:04d}:\n{1}\n{2}".format(line_number, previous_line, line))
            raise exc
    return nest


def lines_from(_dict, tab_depth=0): # rethink & refactor
    """Takes a nested dictionary (which may also contain lists, but not tuples)
from this a series of strings resembling valve's text format used in .vmf files
are generated approximately one line at a time"""
    tabs = '\t' * tab_depth
    for key, value in _dict.items():
        if isinstance(value, (dict, namespace)): # another nest
            value = (value,)
        elif isinstance(value, list): # collection of plurals
            key = singularise(key)
        else: # key-value pair
            if key == "_line":
                continue
            yield """{}"{}" "{}"\n""".format(tabs, key, value)
            continue
        for item in value:
            yield """{}{}\n{}""".format(tabs, key, tabs) + "{\n" # go deeper
            for line in lines_from(item, tab_depth + 1): # recurse down
                yield line
    if tab_depth > 0:
        yield "\t" * (tab_depth - 1) + "}\n" # close the plural index / namespace


def export(nest, outfile):
    """Don't forget to close the file afterwards!"""
    print("Exporting {} ... ".format(outfile.name), end="")
    for line in lines_from(nest):
        outfile.write(line) # writing one line at a time seems wasteful
        # ''.join([line for line in lines_from(_dict)]) also works
    print("Done!")
