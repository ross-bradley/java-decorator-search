#!/usr/bin/env python3

import argparse
import os
import javalang

from shutil import get_terminal_size

"""
  Search functions by decorators (and function names if you need to!)

"""

"""
Nice for structure and memory use (do we really care? How much Python are we parsing?!) :
{
  "a/b/c/d.py": {
    "class": "name",
    "functions":[
      {
        "name": "func1",
        "line": 123,
        "decorators": [
          {
            "name": "dec_name",
            "value", "123"
        ]
      }
    ]
  }
}

----

Better for easy search (especially for writing the actual lambdas!) :

[
  {"path": "a/b/c/d.py", "class": "name", "function": "func1", "line": 123, "decorators": [ ...] },
  {"path": "a/b/c/d.py", "class": "name2", "function": "func2", "line": 223, "decorators": [ ...] },
  ...
]
"""

# ====================================================================================================

class colors:
    DEC_NAME = '\033[1m' # '\033[38;5;231m'
    DEC_VAL = '\033[38;5;231m'
    PATH = '\033[38;5;101m'
    LINE = '\033[38;5;15m'
    CLS = '\033[38;5;28m'
    FUNC = '\033[38;5;46m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    SEPARATOR = '\033[38;5;213m'

# ====================================================================================================

class DecoratorSearcher(object):
    def __init__(self):
        self.results = []
        self.ignore = []

# ----------------------------------------------------------------------------------------------------
    def start(self, args):
        self.ignore = args.ignore if args.ignore is not None else []
        self.parse_folder(args.folder)

# ----------------------------------------------------------------------------------------------------

    def parse_folder(self, folder):
        with os.scandir(folder) as f:
            for path in f:
                if path.name in self.ignore:
                    continue
                if path.is_dir():
                    self.parse_folder(path.path)
                elif path.is_file() and path.name.endswith('.java'):
                    #print(f'[*] Parsing {path.path}')
                    c = JClass()
                    self.results.extend(c.load(path.path))

# ----------------------------------------------------------------------------------------------------

    def from_results(self, results):
        self.results = results

# ----------------------------------------------------------------------------------------------------

    def add_results(self, results):
        self.results.extend(results)

# ----------------------------------------------------------------------------------------------------

    def pretty(self):
        cols = get_terminal_size((1,1)).columns - 1
        print(f'{colors.SEPARATOR}{"#"*cols}{colors.ENDC}')
        for entry in self.results:
            print(f'{colors.PATH}{entry.path}{colors.ENDC}:{colors.LINE}{entry.line}{colors.ENDC}')
            print('\n'.join([f'@{colors.DEC_NAME}{dec.name}{colors.ENDC}({colors.DEC_VAL}{dec.value}{colors.ENDC})' for dec in entry.decorators]))
            print(f'  {colors.CLS}{entry.class_name}{colors.ENDC}:{colors.FUNC}{entry.function}{colors.ENDC}\n--')

# ----------------------------------------------------------------------------------------------------

    def find(self, callback):
        results = []
        for entry in self.results:
            if callback(entry):
                results.append(entry)
        # build a new object and return it!
        # we can use this to chain queries like "find functions with decorator X then filter those that don't have decorator Y"
        results_object = DecoratorSearcher()
        results_object.from_results(results)
        return results_object

# ----------------------------------------------------------------------------------------------------

    """
    *Only* searches decorators!
    Keeps things simple, but limits our flexibility
    If one decorator matches we add the result to our result set
    """
    def findAny(self, callback):
        results = []
        for entry in self.results:
            for decorator in entry['decorators']:
                if type(decorator) != ObjDict:
                    print('NOT DICT!')
                    print(decorator)
                    continue
                if callback(decorator):
                    results.append(entry)
                    break

        # build a new object and return it!
        # we can use this to chain queries like "find functions with decorator X then filter those that don't have decorator Y"
        results_object = DecoratorSearcher()
        results_object.from_results(results)
        return results_object

# ----------------------------------------------------------------------------------------------------

    """
    *Only* searches decorators!
    Keeps things simple, but limits our flexibility
    If all decorators match we add the result to our result set
    Useful for negative searches
    """
    def findAll(self, callback):
        results = []
        for entry in self.results:
            hit = True
            for decorator in entry['decorators']:
                if not callback(decorator):
                    hit = False
                    break
            if hit:
                results.append(entry)
 
        # build a new object and return it!
        # we can use this to chain queries like "find functions with decorator X then filter those that don't have decorator Y"
        results_object = DecoratorSearcher()
        results_object.from_results(results)
        return results_object

# ----------------------------------------------------------------------------------------------------

    """
    Searches by partial name match:
    name: a_decorator_name

    dec => matches
    a_decorator_name2 => does NOT match
    """
    def find_decorators_by_name(self, name):
        return self.findAny(lambda d: name in d.name)

# ----------------------------------------------------------------------------------------------------

    """
    Searches by partial name match:
    name: a_decorator_name

    dec => matches
    a_decorator_name2 => does NOT match
    """
    def find_decorators_by_exact_name(self, name):
        return self.findAny(lambda d: d.name == name)

# ----------------------------------------------------------------------------------------------------

    """
    Searches by partial value match:
    value: /users/(?P<accountType>\\w+)-(?P<userID>\\d+)/assets/products/$

    users => matches
    /Users => does NOT match
    """
    def find_decorators_by_value(self, value):
        return self.findAny(lambda d: value in d.value)

# ----------------------------------------------------------------------------------------------------

    """
    Searches by partial value match:
    value: /users/(?P<accountType>\\w+)-(?P<userID>\\d+)/assets/products/$

    users => matches
    /Users => does NOT match
    """
    def find_decorators_by_exact_value(self, value):
        return self.findAny(lambda d: d['value'] == value)

# ----------------------------------------------------------------------------------------------------

    """
    Exact match on both decorator and value
    """
    def find_decorators_by_name_and_value(self, name, value):
        return self.find(lambda d: name in d.name and value in d.value)


# ====================================================================================================
# Parses a single Java file
# ====================================================================================================

class JClass(object):
    def __init__(self):
        self.results = []
        self._tree = None

# ----------------------------------------------------------------------------------------------------

    def from_results(self, results):
        self.results = results

# ----------------------------------------------------------------------------------------------------

    def load(self, path):
        with open(path, 'r') as fd:
            try:
                self._tree = javalang.parse.parse(fd.read())
            except:
                print(f'[!] Parse FAILED: {path}')
                pass

        if self._tree is not None:
            self.parse(path)
            return self.results
        else:
            return []

# ----------------------------------------------------------------------------------------------------

    def parse(self, path):
        classes = [n for p, n in self._tree.filter(javalang.tree.ClassDeclaration)]
        for cls in classes:
            self.parse_class(cls, path)

# ----------------------------------------------------------------------------------------------------

    def parse_class(self, cls_node, path):
        functions = []
        for node in cls_node.body:
            match type(node):
                case javalang.tree.MethodDeclaration:
                    parsed_func = self.parse_function(node, class_name=cls_node.name, class_decorators=cls_node.annotations)
                    parsed_func['path'] = path
                    self.results.append(parsed_func)
                    
# ----------------------------------------------------------------------------------------------------

    def parse_function(self, fun_node, class_name="", class_decorators=[]):
        # glue the class and function decorators together to make searching a bit easier
        # the class decorators come first if we do it like this, which feels a bit more natural
        # it's important that we make a copy of the class decorators! Don't just .extend(...) them otherwise we modify the class, which is bad
        decorators = [d for d in class_decorators]
        decorators.extend(fun_node.annotations)

        # Dirty temporary hack to include parameter decorators (allows us to search for injected authN filters)
        # TODO: Break parameter decorators out into a separate part of the object so we can search on them separately (and not have kludgy match/case stuff going on)
        for parameter in fun_node.parameters:
            if len(parameter.annotations) > 0:
                decorators.extend(parameter.annotations)

        # super simple reconstruction of the decorators so we can do a dirty grep
        decorators_parsed = []
        for decorator in decorators:
            arguments = []

            match type(decorator.element):
                case javalang.tree.Literal:
                    decorator_name = decorator.name
                    decorator_value = f'{decorator.element.value}'
                    decorators_parsed.append(ObjDict({'name':decorator_name, 'value': decorator_value}))

                case javalang.tree.MemberReference:
                    decorator_name = decorator.name
                    qualifier = f'{decorator.element.qualifier}.' if len(decorator.element.qualifier) > 0 else ''
                    decorator_value = f'{qualifier}{decorator.element.member}'
                    decorators_parsed.append(ObjDict({'name':decorator_name, 'value': decorator_value}))

                case javalang.tree.ElementArrayValue:
                    decorator_name = decorator.name
                    values = []
                    for value in decorator.element.values:
                        # TODO: let's not expect Literals; it could be anything!
                        if type(value) != javalang.tree.Literal:
                            print(f'UNKNOWN TYPE in ElementArrayValue: {value}')
                        else:
                            values.append(value.value)
                    decorator_value = ','.join(values)
                    decorators_parsed.append(ObjDict({'name':decorator_name, 'value': decorator_value}))
                # TODO: This breaks match/case by acting as a catch-all when we don't want it to. Need a workaround for Parameter decorators like @Auth...

                case NoneType:
                    decorator_name = decorator.name
                    decorators_parsed.append(ObjDict({'name':decorator_name, 'value': ''}))
                #case _:
                #    print('[ERROR] Unknown decorator type: ', type(decorator.element))

        return ObjDict({'class_name':class_name, 'function':fun_node.name, 'line':fun_node.position.line, 'decorators':decorators_parsed})

# ====================================================================================================

class ObjDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


# ====================================================================================================


# ====================================================================================================

def instructions():
    print("""
[Java Decorator Search]

Schema:
=======

Function:   {"path": "a/b/c/d.java", "class_name": "name", "function": "func1", "line": 123, "decorators": [ ...] }
Decorator:  {"name": "decorator_name", "value": "b2b"}

Usage:
======

Start from the `ds` object - the following methods are available:

* findAny(lambda d: ...)
* findAll(lambda d: ...)
* find(lambda f: ...)

findAny(lambda d: ...)

 Likely to be the workhorse - if *any* decorator on a function matches, the function will be added to the result set

findAll(lambda d: ...)

 Useful for negative searches, i.e. where you want *all* decorators to not include something. Functions will only be added to the result set if all decorators match

find(lambda f: ...)

 A bit more powerful, but less useful in an interactive lambda. More useful if you add helper functions into the session. Gives you access to the function record, which has things like function and class name, source file path etc.
 
Chaining Queries
================

You can chain queries by simply appending `.findAny(...)` etc. Each query returns a new DirectorySearcher object with the relevant results in it

Display Results
===============

`.pretty()` will print the matched functions in a reasonably sane way including file path and line number, all decorators on the function etc.

`.results` is just the list of results (each entry is a dict)

Examples
========

Find any functions that have a decorator with 'auth' in the name:
>> ds.findAny(lambda d: 'auth' in d.name).pretty()

Find any functions with 'auth' in a decorator name, and 'admin' in the same decorator's value:
>> ds.findAny(lambda d: 'auth' in d.name and 'admin' in d.value).pretty()

Find any functions with 'admin' in a decorator's name, and do not have 'test' in any decorator's name:
>> ds.findAny(lambda d: 'auth' in d.name).findAll(lambda d: 'test' not in d.name).pretty()

""")


def main():
    parser = argparse.ArgumentParser(description='Search Java code by decorators')
    parser.add_argument('folder', type=str, help='Folder to recursively load and parse .java files from')
    parser.add_argument('--ignore', type=str, action='append', help='ignore files and folders with this exact name')
    parser.add_argument('--quiet', action='store_true', help='Disable instructions on start')

    args = parser.parse_args()

    ds = DecoratorSearcher()
    ds.start(args)

    if not args.quiet:
        instructions()

    # Interactive shell for searching for decorators
    import readline
    import code
    vars = globals().copy()
    vars.update(locals())
    shell = code.InteractiveConsole(vars)
    shell.interact()


if __name__ == '__main__':
    main()


