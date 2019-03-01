class namespace:
    def __init__(self):
        self._comments = list()
    
    def __setitem__(self, index, value):
        setattr(self, str(index), value)
    
    def __getitem__(self, index):
        return self.__dict__[str(index)]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__.keys())

    def __repr__(self):
        # Auto Vis-Group "Ai, Choreo" gets misinterpreted in this format
        # ", " implies 2 seperate atrributes, rather than 1
        # all strings with spaces do this, actually
        attrs = [a if ' ' not in a else f'"{a}"' for a in self.__dict__.keys()]
        return f"namespace([{', '.join(attrs)}])"


def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    elif word.endswith('ex'): # vertex -> vertices
        return word[:-2] + 'ices'
    else: # horse -> horses
        return word + 's'


def singularise(word):
    if word.endswith('ves'): # self <- selves
        return word[:-3] + 'f'
    elif word.endswith('ies'): # body <- bodies
        return word[:-3] + 'y'
    elif word.endswith('s'): # horse <- horses
        return word[:-1]
    elif word.endswith('ices'): # vertex <- vertices
        return word[:-4] + 'ex'
    else: # assume word is already singular
        return word


def print_keys(nest, indent=0):
    for key, value in nest.__dict__.items():
        print('  ' * indent, key, sep='')
        if isinstance(value, namespace):
            print_keys(value, indent + 1)

brackets = {'[': ']', '(': ')', '{': '}', '/*': '*/'}

# TODOS:
# class definitions
# inheritance

import textwrap

def read_fgd(filename):
    data_tree = namespace() # storing it all in here

    file = open(filename, 'r', errors='replace') # crash on special characters in comments
    current_scope = 'data_tree'
    scope_nest = ''
    previous_line = ''
    stitching = False

    for line_number, line in enumerate(file.readlines()):
        if line_number == 25: # for debugging
            break
        line = line.rstrip('\n')
        print(f'{line_number:3}|{line}')
        line = textwrap.shorten(line, width=1024) # trimming tabs
        if line == '':
            continue
        if line.startswith('//'):
            if previous_line.startswith('//'):
                last_comment = eval(f'{current_scope}._comments[-1]')
                new_comment = '\n'.join((last_comment[0], line))
                exec(f"""{current_scope}._comments[-1][0] = '''{new_comment}'''""")
            else:
                exec(f"{current_scope}._comments.append(['''{line}''', {line_number}])")
        elif line.startswith("@include"):
            filename = line.lstrip("@include").strip().strip('"').rstrip('.fgd')
            if not hasattr(data_tree, 'included'):
                data_tree.included = namespace()
            print(f'data_tree.included.{filename} = read_fgd("{filename}.fgd")')
            exec(f'data_tree.included.{filename} = read_fgd("{filename}.fgd")')
        elif line.startswith('@') and '=' in line:
            ...
        elif line in brackets.keys(): # is an opening bracket
            old_scope = current_scope # needed to reverse a double downshift
            ...
    ##        print(f'UPSHIFTING: {old_scope} >>> {current_scope}')
            scope_nest += line
        elif line in brackets.values(): # is a closing brackets
            old_scope = current_scope
            if line == brackets[scope_nest[-1]]: # is a closing bracket
                times = 1 if len(scope_nest) == 1 else 2 if scope_nest[-2] == '@' else 1
                current_scope = "[".join(current_scope.split("[")[:-times])
                scope_nest = scope_nest[:-times]
            else:
                raise RuntimeError(f'{file.name} ln{line_number}: Unexpected closing bracket ({line})!')
    ##        print(f'DOWNSHIFTING: {old_scope} >>> {current_scope}')
        elif False: # something, don't know what yet
            if 'Class' in current_scope:
                ...
                # properly establish elements
                # muti-line string stitching
        else: # ordinary line
            # e.g. @PointClass base(Targetname) = point_entity_name : "Description"
            # >>> data_tree.PointClasses.point_entity_name
            # _.description, _.base_classes, _.elements, _.editor_name, \
            # _.inputs, _.outputs
            # [
            #     element(type) : "SmartEdit name" : default : "Description"
            #     [ # example of "choice" type (Enum)
            #         0 : "Desc"
            #         1 : "Desc"
            #     ]
            # >>> ...entity_name.elements[0].namespace()
            # >>> _.type = type
            # >>> _.name = "SmartEdit name"
            # >>> _.description = "Description"
            # >>> _.dict = {0: "Value", 1: "Value"}
            # >>> _.default = default
            #
            #     input InputName(type) : "Description"

            # line format:
            # element(type) : "string" : anytype : "string"
            # strings may be stitched across lines

            # special namespace prep
            if previous_line.startswith('@'):
                if '=' in previous_line:
                    scope_nest += '@'
                    type_, object_ = previous_line.split(' = ')
                    type_ = pluralise(type_.rstrip('@'))
                    if not hasattr(eval(current_scope), type_):
                        exec(f'{current_scope}["{type_}"] = namespace()')
                    current_scope += f"""["{type_}"]['{object_.strip('"')}']"""
                    exec(f"{current_scope} = namespace()")
                else:
                    current_scope = f'{current_scope}["{previous_line.rstrip("@")}"]'
                    exec(f'{current_scope} = namespace()')
            # END special namespace prep
            
            line_value = namespace()
            line_value._line_number = line_number
            index = line.strip('"')
            if '//' in line:
                line_value._comment = line[line.index('//'):]
                index = line[:line.index('//')].strip(' ').strip('"')
            exec(f'{current_scope}["{index}"] = line_value')
        if line.endswith('+'):
            # what do we stitch to?
            stitching = True
            # when do we know to stop stitching?
            # IF previous line ended with '+' AND this one doesn't
            # THEN we're done stitching
            # hold onto the line(s) until we have a full one
        previous_line = line
    file.close()
    return data_tree

if __name__ == "__main__":
    data_tree = read_fgd('../tests/fgds/tf.fgd')
