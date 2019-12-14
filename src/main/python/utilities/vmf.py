"""https://github.com/snake-biscuits/vmf_tool"""
#TODO: identify keys that appear more than once and pluralise
#TODO: insure these keys are restored properly when reversing
## e.g. "visgroupid" "7"\n"visgroupid" "8" = {'visgroupid': ['7', '8']}
#TODO: Functions for handling the horrible visgroup system
import io
import textwrap

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
    elif word.endswith('s'): # side <-  sides
        return word[:-1]
    else: # assume word is already singular
        return word # in the face of ambiguity, refuse the temptaion to guess

class scope:
    """Handles a string used to index a multi-dimensional dictionary, correctly reducing nested lists of dictionaries"""
    def __init__(self, strings=[]):
        self.strings = strings

    def __len__(self):
        """Returns depth, ignoring plural indexes"""
        return len(filter(lambda x: isinstance(x, str), self.strings))

    def __repr__(self):
        """Returns scope as a string that can index a deep dictionary"""
        scope_string = ''
        for string in self.strings:
            if isinstance(string, str):
                scope_string += "['{}']".format(string)
            elif isinstance(string, int):
                scope_string += "[{}]".format(string)
        return scope_string

    def add(self, new):
        self.strings.append(new)

    def reduce(self, count):
        for i in range(count):
            try:
                if isinstance(self.strings[-1], int):
                    self.strings = self.strings[:-2]
                else:
                    self.strings = self.strings[:-1]
            except:
                break


def namespace_from(text_file):
    """String or .vmf file to nested namespace"""
    if isinstance(text_file, io.TextIOWrapper):
        file_iter = text_file.readlines()
    elif isinstance(text_file, str):
        file_iter = text_file.split('\n')
    else:
        raise RuntimeError("Cannot construct dictionary from {}!".format(type(text_file)))
    namespace_nest = namespace({})
    current_scope = scope([])
    previous_line = ''
    for line_number, line in enumerate(file_iter):
        try:
            new_namespace = namespace({'_line': line_number})
            line = line.rstrip('\n')
            line = textwrap.shorten(line, width=2000) # cleanup spacing, broke at 200+ chars, not the right tool for the job
            if line == '' or line.startswith('//'): # ignore blank / comments
                continue
            elif line =='{': # START declaration
                current_keys = eval("namespace_nest{}.__dict__.keys()".format(current_scope))
                plural = pluralise(previous_line)
                if previous_line in current_keys: # NEW plural
                    exec("namespace_nest{}[plural] = [namespace_nest{}[previous_line]]".format(current_scope, current_scope))
                    exec("namespace_nest{}.__dict__.pop(previous_line)".format(current_scope))
                    exec("namespace_nest{}[plural].append(new_namespace)".format(current_scope))
                    current_scope = scope([*current_scope.strings, plural, 1]) # why isn't this a method?
                elif plural in current_keys: # APPEND plural
                    current_scope.add(plural)
                    exec("namespace_nest{}.append(new_namespace)".format(current_scope))
                    current_scope.add(len(eval("namespace_nest{}".format(current_scope))) - 1)
                else: # NEW singular
                    current_scope.add(previous_line)
                    exec("namespace_nest{} = new_namespace".format(current_scope))
            elif line == '}': # END declaration
                current_scope.reduce(1)
            elif '" "' in line: # KEY VALUE
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                exec("namespace_nest{}[key] = value".format(current_scope))
            elif line.count(' ') == 1:
                key, value = line.split()
                exec("namespace_nest{}[key] = value".format(current_scope))
            previous_line = line.strip('"')
        except Exception as exc:
            print("error on line {0:04d}:\n{1}\n{2}".format(line_number, line, previous_line))
            raise exc
    return namespace_nest


class namespace: # DUNDER METHODS ONLY!
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
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__.keys())

    def __repr__(self):
        attrs = [a if ' ' not in a else '"{}"'.format(a) for a in self.__dict__.keys()]
        return "namespace([{}])".format(", ".join(attrs))

    def items(self): # fix for lines_from
        for k, v in self.__dict__.items():
            yield (k, v)


def dict_from(namespace_nest):
    out = dict()
    for key, value in namespace_nest.__dict__.items():
        if isinstance(value, namespace):
            out[key] = dict_from(value)
        elif isinstance(value, list):
            out[key] = [dict_from(i) for i in value]
        else:
            out[key] = value
    return out


def lines_from(_dict, tab_depth=0): # rethink & refactor
    '''Takes a nested dictionary (which may also contain lists, but not tuples)
from this a series of strings resembling valve's text format used in .vmf files
are generated approximately one line at a time'''
    tabs = '\t' * tab_depth
    for key, value in _dict.items():
        if isinstance(value, (dict, namespace)): # another layer
            value = (value,)
        elif isinstance(value, list): # collection of plurals
            key = singularise(key)
        else: # key-value pair
            if key == "_line":
                continue
            yield """{}"{}" "{}"\n""".format(tabs, key, value)
            continue
        for item in value:
            yield """{}{}\n{}""".format(tabs, key, tabs) + "{\n" # open into the next layer
            for line in lines_from(item, tab_depth + 1): # recurse down
                yield line
    if tab_depth > 0:
        yield "\t" * (tab_depth - 1) + "}\n" # close the layer


def export(_dict, outfile):
    """Don't forget to close the file afterwards!"""
    print("Exporting {} ... ".format(outfile.name), end="")
    for line in lines_from(_dict): # using a buffer to write in chunks may be wise
        outfile.write(line) # ''.join([line for line in lines_from(_dict)]) also works
    print("Done!")
